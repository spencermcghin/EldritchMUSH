"""
world/email.py — Email sending via Resend API.

Uses the RESEND_API_KEY environment variable. Falls back to printing
the email to the diag log if the key is not configured or sending fails.

All outgoing mail shares one daily cap (EMAIL_DAILY_LIMIT, default 60)
and one hourly burst cap (EMAIL_HOURLY_LIMIT, default 20), saved on the
volume; see "Shared outgoing-mail quota" below.
"""
import os
import json
import html as _html
import threading
import time


def _esc(value):
    """HTML-escape a value for safe interpolation into email templates.

    Character names and rejection reasons are user-controlled strings
    that get embedded in the admin / player approval emails below.
    Without escaping, a character name like `<a href="https://evil">`
    would render as a live link in the recipient's mail client.
    """
    return _html.escape(str(value or ""), quote=True)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL = "EldritchMUSH <noreply@eldritchmush.com>"
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "contact@eldritchmush.com")


# ---------------------------------------------------------------------------
# Shared outgoing-mail quota
# ---------------------------------------------------------------------------
# Every email the game sends (verification links, allauth web mail,
# character approvals, admin alerts) counts against ONE daily cap and one
# hourly burst cap, kept below Resend's free plan (100 a day). The count
# is saved on the Railway volume like the AI spend file, so restarts and
# redeploys keep it, and it FAILS CLOSED: if the file can't be read or
# written (or a deployed environment has no volume), nothing is sent.
# The last MAIL_ADMIN_RESERVE slots of the day are kept for mail to
# ADMIN_EMAIL, and admin mail skips the hourly cap, so a flood of sign-up
# mail can't silence the admin alerts. A flock on mail_quota.lock guards
# the read-modify-write; a corrupt file is rewritten as "today is full".
# Counts recipients (to + cc + bcc), which is how Resend counts.
MAIL_ADMIN_RESERVE = 5
_QUOTA_LOCK = threading.Lock()


class EmailNotSent(RuntimeError):
    """Raised by the Django backend when a message was not sent. reason is
    one of: no_key, daily_cap, hourly_cap, store_error, provider_error."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def _int_env(name, default):
    try:
        return max(0, int(os.environ.get(name, str(default))))
    except ValueError:
        return default


def mail_daily_limit():
    return _int_env("EMAIL_DAILY_LIMIT", 60)


def mail_hourly_limit():
    return _int_env("EMAIL_HOURLY_LIMIT", 20)


def _quota_file():
    vol = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
    if vol:
        return os.path.join(vol, "mail_quota.json")
    if os.environ.get("RAILWAY_ENVIRONMENT_NAME"):
        return None  # deployed with no volume: no durable store
    return "/tmp/mail_quota.json"


class _CorruptQuota(ValueError):
    pass


def _read_quota(path):
    """Today's quota record. Missing file = fresh. Raises _CorruptQuota on
    a file that can't be parsed, OSError on one that can't be read."""
    today = time.strftime("%Y-%m-%d", time.gmtime())
    try:
        with open(path, "r", encoding="utf-8") as fp:
            raw = fp.read()
    except FileNotFoundError:
        raw = ""
    try:
        data = json.loads(raw) if raw.strip() else {}
        if not isinstance(data, dict):
            raise ValueError("not a JSON object")
        now = time.time()
        hour = [float(t) for t in data.get("hour", [])
                if now - float(t) < 3600]
        count = int(data.get("count") or 0)
    except Exception as exc:
        raise _CorruptQuota(str(exc))
    if data.get("day") != today:
        return {"day": today, "count": 0, "hour": hour}
    return {"day": today, "count": count, "hour": hour}


def _write_quota(path, data):
    """Atomic write: a temp file in the same directory, then rename."""
    import tempfile
    fd, tmp = tempfile.mkstemp(prefix=".mail_quota.", suffix=".tmp",
                               dir=os.path.dirname(path) or ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fp:
            json.dump(data, fp)
            fp.flush()
            os.fsync(fp.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


class _QuotaLock:
    """Thread lock plus an flock on mail_quota.lock beside the store, so
    read-modify-write is safe across threads and processes."""

    def __init__(self, path):
        self.lock_path = os.path.join(os.path.dirname(path) or ".",
                                      "mail_quota.lock")
        self.fp = None

    def __enter__(self):
        _QUOTA_LOCK.acquire()
        try:
            import fcntl
            self.fp = open(self.lock_path, "a")
            fcntl.flock(self.fp.fileno(), fcntl.LOCK_EX)
        except Exception:
            if self.fp:
                self.fp.close()
            self.fp = None
            _QUOTA_LOCK.release()
            raise
        return self

    def __exit__(self, *exc):
        try:
            import fcntl
            fcntl.flock(self.fp.fileno(), fcntl.LOCK_UN)
            self.fp.close()
        finally:
            _QUOTA_LOCK.release()
        return False


def _reserve(n, to_admin):
    """Take n slots. Returns None on success, else the refusal reason.

    Mail to ADMIN_EMAIL may use the last MAIL_ADMIN_RESERVE daily slots
    and isn't held to the hourly cap. A corrupt store refuses this send
    and is rewritten as "today is full", so mail resumes next UTC day."""
    path = _quota_file()
    if not path:
        return "store_error"
    try:
        with _QuotaLock(path):
            try:
                data = _read_quota(path)
            except _CorruptQuota as exc:
                print(f"[email] MAIL QUOTA FILE CORRUPT ({exc}); not "
                      f"sending, and treating today as full", flush=True)
                _write_quota(path, {
                    "day": time.strftime("%Y-%m-%d", time.gmtime()),
                    "count": mail_daily_limit(), "hour": []})
                return "store_error"
            limit = mail_daily_limit()
            if not to_admin:
                limit = max(0, limit - MAIL_ADMIN_RESERVE)
            if data["count"] + n > limit:
                return "daily_cap"
            if not to_admin and len(data["hour"]) + n > mail_hourly_limit():
                return "hourly_cap"
            data["count"] += n
            data["hour"].extend([time.time()] * n)
            _write_quota(path, data)
            return None
    except Exception as exc:
        print(f"[email] MAIL QUOTA STORE FAILED, not sending: "
              f"{type(exc).__name__}: {exc}", flush=True)
        return "store_error"


def _release(n):
    """Give back n slots after a send that didn't go out."""
    path = _quota_file()
    if not path:
        return
    try:
        with _QuotaLock(path):
            data = _read_quota(path)
            data["count"] = max(0, data["count"] - n)
            data["hour"] = data["hour"][:-n] if n else data["hour"]
            _write_quota(path, data)
    except Exception:
        pass


def _as_list(value):
    if not value:
        return []
    return [value] if isinstance(value, str) else list(value)


def send_email_result(to, subject, html_body, text_body=None,
                      cc=None, bcc=None):
    """Send an email via Resend's HTTP API, within the shared quota.

    Returns (sent: bool, reason: str | None). reason is set when sent is
    False: no_key, daily_cap, hourly_cap, store_error, provider_error.
    """
    try:
        from web.diag import diag_write
    except Exception:
        diag_write = lambda msg, **kw: None

    to_l, cc_l, bcc_l = _as_list(to), _as_list(cc), _as_list(bcc)
    recipients = to_l + cc_l + bcc_l
    if not recipients:
        return False, "provider_error"

    if not RESEND_API_KEY:
        diag_write("EMAIL SKIPPED — no RESEND_API_KEY", subject=subject, to=to)
        return False, "no_key"

    to_admin = all(r.lower() == ADMIN_EMAIL.lower() for r in recipients)
    refused = _reserve(len(recipients), to_admin)
    if refused:
        diag_write("EMAIL BLOCKED", reason=refused, subject=subject)
        print(f"[email] not sent ({refused}): {subject}", flush=True)
        if refused in ("daily_cap", "hourly_cap") and not to_admin:
            try:
                from world import telemetry
                if refused == "daily_cap":
                    telemetry.alert(
                        "email_daily_cap",
                        f"Daily email cap reached ({mail_daily_limit()})",
                        "Verification and other player emails stop until "
                        "UTC midnight. Raise EMAIL_DAILY_LIMIT only if the "
                        "Resend plan allows it.")
                else:
                    telemetry.alert(
                        "email_hourly_cap",
                        f"Hourly email cap reached ({mail_hourly_limit()})",
                        "Player emails pause until the rolling hour frees "
                        "up. A burst like this can mean someone is "
                        "triggering emails on purpose.")
            except Exception:
                pass
        return False, refused

    try:
        import urllib.request
        import urllib.error

        payload = {
            "from": FROM_EMAIL,
            "to": to_l,
            "subject": subject,
            "html": html_body,
        }
        if cc_l:
            payload["cc"] = cc_l
        if bcc_l:
            payload["bcc"] = bcc_l
        if text_body:
            payload["text"] = text_body

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=data,
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "EldritchMUSH/1.0",
            },
        )
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read().decode("utf-8"))
        diag_write("EMAIL SENT", to=to, subject=subject, id=result.get("id"))
        return True, None

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        diag_write("EMAIL FAILED", to=to, subject=subject, status=exc.code, body=body)
    except Exception as exc:
        diag_write("EMAIL FAILED", to=to, subject=subject, exc=str(exc))
    _release(len(recipients))
    return False, "provider_error"


def send_email(to, subject, html_body, text_body=None, cc=None, bcc=None):
    """Send an email via Resend's HTTP API (shared quota applies).

    Args:
        to: recipient email (string or list of strings)
        subject: email subject line
        html_body: HTML content
        text_body: plain text fallback (optional)
        cc, bcc: optional recipients (string or list)

    Returns:
        True on success, False on failure.
    """
    sent, _reason = send_email_result(to, subject, html_body,
                                      text_body=text_body, cc=cc, bcc=bcc)
    return sent


def send_approval_request(character_name, account_name, account_email, skills_summary):
    """Notify admin that a character needs approval."""
    c_name = _esc(character_name)
    a_name = _esc(account_name)
    a_email = _esc(account_email)
    skills = _esc(skills_summary)
    # Subject goes through mail transport as-is; Resend encodes it, but
    # it's still user-controlled so keep it plain ASCII-friendly.
    subject = f"[EldritchMUSH] Character Approval Request: {character_name}"
    html = f"""
    <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; background: #1a1610; color: #e8e4d0; padding: 30px; border: 1px solid #4a3828;">
        <h1 style="color: #d4af37; font-size: 24px; margin-bottom: 5px;">Character Approval Request</h1>
        <hr style="border: none; border-top: 1px solid #4a3828; margin: 15px 0;">
        <p><strong>Character:</strong> {c_name}</p>
        <p><strong>Account:</strong> {a_name} ({a_email})</p>
        <h3 style="color: #d4af37; margin-top: 20px;">Skills</h3>
        <p style="font-family: monospace; font-size: 12px; white-space: pre-line;">{skills}</p>
        <hr style="border: none; border-top: 1px solid #4a3828; margin: 15px 0;">
        <p style="color: #9a8266; font-size: 12px;">
            Log in to the <a href="https://eldritchmush.com" style="color: #d4af37;">Admin Dashboard</a>
            to approve or reject this character.
        </p>
    </div>
    """
    return send_email(ADMIN_EMAIL, subject, html)


def send_approval_notification(player_email, character_name, approved, reason=""):
    """Notify a player that their character was approved or rejected."""
    c_name = _esc(character_name)
    r = _esc(reason)
    if approved:
        subject = f"[EldritchMUSH] {character_name} has been approved!"
        html = f"""
        <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; background: #1a1610; color: #e8e4d0; padding: 30px; border: 1px solid #4a3828;">
            <h1 style="color: #00e5a0; font-size: 24px;">Character Approved</h1>
            <hr style="border: none; border-top: 1px solid #4a3828; margin: 15px 0;">
            <p>Your character <strong style="color: #d4af37;">{c_name}</strong> has been approved by the game masters.</p>
            <p>You may now enter the world. Log in at <a href="https://eldritchmush.com" style="color: #d4af37;">eldritchmush.com</a> and select your character to begin your journey.</p>
            <hr style="border: none; border-top: 1px solid #4a3828; margin: 15px 0;">
            <p style="color: #9a8266; font-size: 12px;">The dark awaits. Choose wisely.</p>
        </div>
        """
    else:
        subject = f"[EldritchMUSH] {character_name} — changes requested"
        html = f"""
        <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; background: #1a1610; color: #e8e4d0; padding: 30px; border: 1px solid #4a3828;">
            <h1 style="color: #cc2211; font-size: 24px;">Changes Requested</h1>
            <hr style="border: none; border-top: 1px solid #4a3828; margin: 15px 0;">
            <p>Your character <strong style="color: #d4af37;">{c_name}</strong> needs some changes before it can be approved.</p>
            {f'<p><strong>Reason:</strong> {r}</p>' if reason else ''}
            <p>Log in at <a href="https://eldritchmush.com" style="color: #d4af37;">eldritchmush.com</a> to update your character build.</p>
            <hr style="border: none; border-top: 1px solid #4a3828; margin: 15px 0;">
            <p style="color: #9a8266; font-size: 12px;">The game masters await your revised submission.</p>
        </div>
        """
    return send_email(player_email, subject, html)
