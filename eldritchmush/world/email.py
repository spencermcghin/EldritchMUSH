"""
world/email.py — Email sending via Resend API.

Uses the RESEND_API_KEY environment variable. Falls back to printing
the email to the diag log if the key is not configured or sending fails.
"""
import os
import json
import html as _html


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


def send_email(to, subject, html_body, text_body=None):
    """Send an email via Resend's HTTP API.

    Args:
        to: recipient email (string or list of strings)
        subject: email subject line
        html_body: HTML content
        text_body: plain text fallback (optional)

    Returns:
        True on success, False on failure.
    """
    try:
        from web.diag import diag_write
    except Exception:
        diag_write = lambda msg, **kw: None

    if not RESEND_API_KEY:
        diag_write("EMAIL SKIPPED — no RESEND_API_KEY", subject=subject, to=to)
        return False

    try:
        import urllib.request
        import urllib.error

        payload = {
            "from": FROM_EMAIL,
            "to": [to] if isinstance(to, str) else to,
            "subject": subject,
            "html": html_body,
        }
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
        return True

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        diag_write("EMAIL FAILED", to=to, subject=subject, status=exc.code, body=body)
        return False
    except Exception as exc:
        diag_write("EMAIL FAILED", to=to, subject=subject, exc=str(exc))
        return False


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
