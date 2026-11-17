"""
Email verification for password accounts.

AI NPC chat and the fortune cabinet need a verified email or a Google
sign-in (world/ai_safety.account_ai_eligible). This module lets a
password player verify their address from inside the game:

    verify                    send a link to the address on the account
    verify you@example.com    switch the account to that address, then send

Links are ordinary django-allauth confirmation links
(/accounts/confirm-email/<key>/), sent through the game's Resend setup
(world/email_backend.py). Clicking one marks the allauth EmailAddress
verified, which is what the AI gate checks. On confirmation, the address
is removed from every OTHER account's unverified rows
(web/allauth_adapters.AccountAdapter.confirm_email), so nobody can park
on someone else's address.

Limits on sending, so the command can't be used to spam an inbox or burn
the Resend quota:
    - the account must be at least VERIFY_MIN_ACCOUNT_AGE seconds old
      (10 minutes) or already have a character
    - one email per account every VERIFY_COOLDOWN seconds (10 minutes)
    - VERIFY_DAILY_MAX emails per account per rolling day (5)
    - the shared daily and hourly caps on ALL game mail (world/email.py)
A send that fails gives the account's slot back.

send_bulk() is the one-off backfill for existing accounts; run it with
scripts/send_verification_emails.py (dry run unless --send is given).
"""
import os
import re
import time
from urllib.parse import urlsplit

VERIFY_HINT = ("Verify your email to talk with NPCs. "
               "Check your inbox or type `verify`.")

VERIFY_COOLDOWN = 600
VERIFY_DAILY_MAX = 5
VERIFY_MIN_ACCOUNT_AGE = 600

_SENDS_ATTR = "email_verify_sends"
_BULK_ATTR = "email_verify_bulk_sent"

_DEFAULT_BASE_URLS = {
    "production": "https://eldritchmush.com",
    "prod": "https://eldritchmush.com",
    "uat": "https://uat.eldritchmush.com",
}
_LOCAL_BASE_URL = "http://localhost:4001"


class SiteURLNotConfigured(RuntimeError):
    """A deployed environment has no known public URL for links."""


def site_base_url():
    """Where confirmation links point.

    SITE_BASE_URL wins. Otherwise production and uat use their public
    hosts, and local dev (no RAILWAY_ENVIRONMENT_NAME) uses localhost.
    Any other deployed environment without SITE_BASE_URL raises
    SiteURLNotConfigured (logged loudly) instead of mailing localhost
    links."""
    explicit = (os.environ.get("SITE_BASE_URL") or "").strip().rstrip("/")
    if explicit:
        return explicit
    railway_env = (os.environ.get("RAILWAY_ENVIRONMENT_NAME") or "").lower()
    if railway_env:
        if railway_env in _DEFAULT_BASE_URLS:
            return _DEFAULT_BASE_URLS[railway_env]
        print(f"[email_verification] SITE_BASE_URL is not set on deployed "
              f"environment {railway_env!r}; refusing to send "
              f"verification links.", flush=True)
        raise SiteURLNotConfigured(railway_env)
    env = (os.environ.get("DEPLOY_ENV") or "local").lower()
    return _DEFAULT_BASE_URLS.get(env, _LOCAL_BASE_URL)


def sync_site():
    """Point the Django Site (used by allauth's emails and pages) at this
    environment: name "Eldritch MUSH", domain from site_base_url(). Run at
    server start. Never raises."""
    try:
        from django.conf import settings
        from django.contrib.sites.models import Site
        domain = urlsplit(site_base_url()).netloc
        if not domain:
            return
        site, _ = Site.objects.get_or_create(
            id=getattr(settings, "SITE_ID", 1),
            defaults={"domain": domain, "name": "Eldritch MUSH"})
        if site.domain != domain or site.name != "Eldritch MUSH":
            site.domain, site.name = domain, "Eldritch MUSH"
            site.save()
        Site.objects.clear_cache()
    except Exception as exc:
        print(f"[email_verification] could not set the Django Site: "
              f"{exc!r}", flush=True)


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------
def email_status(account):
    """One of "verified", "google", "unverified", "no_email", "no_account"."""
    if account is None:
        return "no_account"
    uid = getattr(account, "id", None)
    try:
        from allauth.account.models import EmailAddress
        if EmailAddress.objects.filter(user_id=uid, verified=True).exists():
            return "verified"
    except Exception:
        pass
    try:
        from allauth.socialaccount.models import SocialAccount
        if SocialAccount.objects.filter(user_id=uid,
                                        provider="google").exists():
            return "google"
    except Exception:
        pass
    if (getattr(account, "email", "") or "").strip():
        return "unverified"
    return "no_email"


def needs_verification(account):
    """True when the AI gate is on and this account doesn't pass it."""
    from world import ai_safety
    return (ai_safety._require_verified()
            and not ai_safety.account_ai_eligible(account))


def send_hint(char):
    """The one-line hint after a canned NPC line or fortune."""
    try:
        char.msg(f"|y{VERIFY_HINT}|n")
    except Exception:
        pass


def login_note(account):
    """Short note for an unverified password player at login, or None."""
    if not needs_verification(account):
        return None
    if email_status(account) == "no_email":
        return ("|yNPCs only give short stock replies until you add and "
                "verify an email address. Type |wverify you@example.com|y "
                "and we'll send you a link.|n")
    return ("|yYour email address isn't verified yet, so NPCs only give "
            "short stock replies. Type |wverify|y and we'll send you a "
            "link.|n")


# ---------------------------------------------------------------------------
# Sending
# ---------------------------------------------------------------------------
_EMAIL_RX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _valid_email(addr):
    if not addr or len(addr) > 254 or not _EMAIL_RX.match(addr):
        return False
    try:
        from django.core.validators import validate_email
        validate_email(addr)
        return True
    except Exception:
        return False


def _address_taken(addr, account):
    """True when another account has *addr* VERIFIED, or is a Google
    account using it. Unverified claims by other accounts don't count:
    whoever verifies first owns the address (see confirm_email cleanup)."""
    from django.contrib.auth import get_user_model
    from allauth.account.models import EmailAddress
    User = get_user_model()
    if (EmailAddress.objects.filter(email__iexact=addr, verified=True)
            .exclude(user_id=account.id).exists()):
        return True
    return (User.objects.filter(email__iexact=addr,
                                socialaccount__provider="google")
            .exclude(id=account.id).exists())


def _account_old_enough(account):
    """New accounts must wait VERIFY_MIN_ACCOUNT_AGE, unless they have
    already made a character."""
    try:
        chars = account.characters.all()
    except Exception:
        chars = account.db._playable_characters or []
    if chars:
        return True
    created = getattr(account, "date_created", None) \
        or getattr(account, "db_date_created", None)
    if created is None:
        return False
    try:
        return time.time() - created.timestamp() >= VERIFY_MIN_ACCOUNT_AGE
    except Exception:
        return False


def _recent_sends(account, now):
    return [t for t in (account.attributes.get(_SENDS_ATTR, default=None)
                        or []) if now - t < 86400]


def _account_limit_message(account, now):
    sends = _recent_sends(account, now)
    if sends and now - sends[-1] < VERIFY_COOLDOWN:
        wait = int((VERIFY_COOLDOWN - (now - sends[-1])) / 60) + 1
        return ("We just sent you a link. Check your inbox (and spam "
                f"folder), or try again in about {wait} minutes.")
    if len(sends) >= VERIFY_DAILY_MAX:
        return ("You've asked for several links today. Check your inbox "
                "(and spam folder), or try again tomorrow.")
    return None


def _record_send(account, now):
    sends = _recent_sends(account, now)
    sends.append(now)
    account.attributes.add(_SENDS_ATTR, sends)


def _release_send(account, stamp):
    """Give back the per-account slot taken for a send that failed."""
    sends = [t for t in (account.attributes.get(_SENDS_ATTR, default=None)
                         or []) if t != stamp]
    account.attributes.add(_SENDS_ATTR, sends)


def _switch_address(account, addr):
    """Make *addr* the account's primary address: drop the account's other
    UNVERIFIED rows, create the row if needed, set it primary and keep
    User.email in sync. Returns the EmailAddress."""
    from allauth.account.models import EmailAddress
    (EmailAddress.objects.filter(user_id=account.id, verified=False)
     .exclude(email__iexact=addr).delete())
    email_address = EmailAddress.objects.filter(
        user_id=account.id, email__iexact=addr).first()
    if email_address is None:
        email_address = EmailAddress.objects.create(
            user=account, email=addr, verified=False, primary=False)
    email_address.set_as_primary()  # unsets others, writes User.email
    if (account.email or "").lower() != addr:
        account.email = addr
        account.save(update_fields=["email"])
    return email_address


def build_message(account, email_address):
    """Render the confirmation email for an allauth EmailAddress.
    Raises SiteURLNotConfigured when links can't be built."""
    from allauth.account.adapter import get_adapter
    from allauth.account.models import EmailConfirmationHMAC
    adapter = get_adapter()
    confirmation = EmailConfirmationHMAC(email_address)
    ctx = {
        "user": account,
        "key": confirmation.key,
        "activate_url": adapter.get_email_confirmation_url(
            None, confirmation),
        "email": email_address.email,
        "account_name": account.username,
    }
    return adapter.render_mail(
        "account/email/email_confirmation", email_address.email, ctx)


class Prepared:
    """A verification email ready to send, plus what to say afterwards."""

    def __init__(self, account, addr, message, stamp):
        self.account = account
        self.addr = addr
        self.message = message
        self.stamp = stamp

    def sent_text(self):
        return (f"We sent a verification link to {self.addr}. Open it "
                f"within 3 days to finish. Check your spam folder if it "
                f"doesn't arrive.")


def prepare(account, email=None, bulk=False):
    """Validate, rate-limit, attach the address and render the email.

    Returns (refusal_text, None) when nothing should be sent, or
    (None, Prepared) when an email is ready. Sending is left to the caller
    so the HTTP call can run off the reactor thread. bulk=True skips the
    per-account limits and age gate (send_bulk has its own rules).
    """
    status = email_status(account)
    if status in ("verified", "google"):
        return ("Your email is already verified. NPCs will talk with "
                "you.", None)
    if status == "no_account":
        return ("Log in first.", None)

    addr = (email or getattr(account, "email", "") or "").strip().lower()
    if not addr:
        return ("There's no email address on your account. Type "
                "|wverify you@example.com|n to add one.", None)
    if not _valid_email(addr):
        return (f"That doesn't look like an email address: {addr}", None)
    if _address_taken(addr, account):
        return ("That address is already verified on another account. "
                "Type |wverify you@example.com|n with an address only you "
                "use.", None)

    now = time.time()
    if not bulk:
        if not _account_old_enough(account):
            return ("New accounts can ask for a verification link after "
                    "10 minutes, or as soon as you've made a character.",
                    None)
        limited = _account_limit_message(account, now)
        if limited:
            return (limited, None)

    try:
        site_base_url()
    except SiteURLNotConfigured:
        return ("Verification emails aren't set up on this server yet. "
                "Please tell a game admin.", None)

    email_address = _switch_address(account, addr)
    message = build_message(account, email_address)
    if not bulk:
        _record_send(account, now)
    return (None, Prepared(account, addr, message, now))


def _failure_text(exc):
    reason = getattr(exc, "reason", None)
    if reason in ("daily_cap", "hourly_cap"):
        return ("|rThe game has sent all the email it can for now. Please "
                "type |wverify|r again later.|n")
    return ("|rThe verification email didn't go out. Please try again "
            "later.|n")


def request_verification(account, email=None, reply=None):
    """`verify` command entry point. Prepares synchronously (fast ORM
    work), sends on a worker thread, and replies only once the send
    result is known. A failed send gives the account's slot back."""
    say = reply or (lambda _t: None)
    refusal, prepared = prepare(account, email=email)
    if prepared is None:
        say(refusal)
        return False

    def _done(_count):
        say(prepared.sent_text())

    def _failed(exc):
        _release_send(account, prepared.stamp)
        say(_failure_text(exc))

    try:
        from twisted.internet import reactor, threads
        running = reactor.running
    except Exception:
        running = False
    if running:
        # In the game: the Resend HTTP call runs on a worker thread so the
        # reactor never waits on it; callbacks come back to the reactor.
        d = threads.deferToThread(prepared.message.send)
        d.addCallbacks(_done, lambda failure: _failed(failure.value))
        return True
    # No reactor (shell, script, tests): send inline.
    try:
        count = prepared.message.send()
    except Exception as exc:
        _failed(exc)
        return False
    _done(count)
    return True


# ---------------------------------------------------------------------------
# One-off backfill for existing accounts
# ---------------------------------------------------------------------------
def bulk_candidates():
    """Accounts that have an email address, aren't verified, have no
    Google sign-in, share their address with no other account, and
    haven't had a backfill email yet."""
    from django.contrib.auth import get_user_model
    from django.db.models import Count
    from django.db.models.functions import Lower
    User = get_user_model()
    dup = set(
        User.objects.exclude(email="")
        .annotate(addr=Lower("email")).values("addr")
        .annotate(n=Count("id")).filter(n__gt=1)
        .values_list("addr", flat=True))
    out = []
    for account in User.objects.exclude(email="").order_by("id"):
        if (account.email or "").lower() in dup:
            continue
        if email_status(account) != "unverified":
            continue
        if account.attributes.get(_BULK_ATTR, default=None):
            continue
        out.append(account)
    return out


def send_bulk(limit=50, delay=1.0, send=False, out=print):
    """Send one verification email to each candidate, at most *limit* per
    run, *delay* seconds apart. Every email also counts against the shared
    daily mail cap (world/email.py), so a run stops sending once that is
    used up. Dry run unless send=True. Returns the number sent (or that
    would be sent)."""
    candidates = bulk_candidates()
    out(f"{len(candidates)} unverified account(s) with an email address; "
        f"this run handles up to {limit}.")
    done = 0
    for account in candidates[:limit]:
        if not send:
            out(f"  would send to account #{account.id} ({account.username})")
            done += 1
            continue
        refusal, prepared = prepare(account, bulk=True)
        if prepared is None:
            out(f"  skipped #{account.id}: {refusal}")
            continue
        try:
            sent = prepared.message.send()
        except Exception as exc:
            sent = 0
            reason = getattr(exc, "reason", None) or type(exc).__name__
            out(f"  failed #{account.id}: {reason}")
            if reason in ("daily_cap", "hourly_cap"):
                out("  stopping: the shared mail cap is used up")
                break
        else:
            if not sent:
                out(f"  failed #{account.id}: not sent")
        if sent:
            account.attributes.add(_BULK_ATTR, time.time())
            done += 1
            out(f"  sent to account #{account.id} ({account.username})")
        time.sleep(delay)
    out(f"{'Sent' if send else 'Would send'}: {done}.")
    return done
