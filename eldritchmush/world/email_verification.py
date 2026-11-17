"""
Email verification for password accounts.

AI NPC chat and the fortune cabinet need a verified email or a Google
sign-in (world/ai_safety.account_ai_eligible). This module lets a
password player verify their address from inside the game:

    verify                    send a link to the address on the account
    verify you@example.com    set that address on the account, then send

Links are ordinary django-allauth confirmation links
(/accounts/confirm-email/<key>/), sent through the game's Resend setup
(world/email_backend.py). Clicking one marks the allauth EmailAddress
verified, which is what the AI gate checks.

Limits on sending, so the command can't be used to spam an inbox or burn
the Resend quota:
    - one email per account every VERIFY_COOLDOWN seconds (10 minutes)
    - VERIFY_DAILY_MAX emails per account per rolling day (5)
    - VERIFY_GLOBAL_HOURLY_MAX emails per hour for the whole game (60)

send_bulk() is the one-off backfill for existing accounts; run it with
scripts/send_verification_emails.py (dry run unless --send is given).
"""
import os
import re
import threading
import time
from collections import deque

VERIFY_HINT = ("Verify your email to talk with NPCs. "
               "Check your inbox or type `verify`.")

VERIFY_COOLDOWN = 600
VERIFY_DAILY_MAX = 5
VERIFY_GLOBAL_HOURLY_MAX = 60

_SENDS_ATTR = "email_verify_sends"
_BULK_ATTR = "email_verify_bulk_sent"
_GLOBAL_LOCK = threading.Lock()
_GLOBAL_SENDS = deque()

_DEFAULT_BASE_URLS = {
    "production": "https://eldritchmush.com",
    "prod": "https://eldritchmush.com",
    "uat": "https://uat.eldritchmush.com",
}


def site_base_url():
    """Where confirmation links point. SITE_BASE_URL wins; otherwise a
    default for the Railway environment; localhost for local dev."""
    explicit = (os.environ.get("SITE_BASE_URL") or "").strip().rstrip("/")
    if explicit:
        return explicit
    env = (os.environ.get("RAILWAY_ENVIRONMENT_NAME")
           or os.environ.get("DEPLOY_ENV") or "local").lower()
    return _DEFAULT_BASE_URLS.get(env, "http://localhost:4001")


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
    """True when another account already uses *addr*."""
    from django.contrib.auth import get_user_model
    from allauth.account.models import EmailAddress
    User = get_user_model()
    if (User.objects.filter(email__iexact=addr)
            .exclude(id=account.id).exists()):
        return True
    return (EmailAddress.objects.filter(email__iexact=addr)
            .exclude(user_id=account.id).exists())


def _account_limit_message(account, now):
    sends = [t for t in (account.attributes.get(_SENDS_ATTR, default=None)
                         or []) if now - t < 86400]
    if sends and now - sends[-1] < VERIFY_COOLDOWN:
        wait = int((VERIFY_COOLDOWN - (now - sends[-1])) / 60) + 1
        return ("We just sent you a link. Check your inbox (and spam "
                f"folder), or try again in about {wait} minutes.")
    if len(sends) >= VERIFY_DAILY_MAX:
        return ("You've asked for several links today. Check your inbox "
                "(and spam folder), or try again tomorrow.")
    return None


def _take_global_slot(now):
    with _GLOBAL_LOCK:
        while _GLOBAL_SENDS and now - _GLOBAL_SENDS[0] >= 3600:
            _GLOBAL_SENDS.popleft()
        if len(_GLOBAL_SENDS) >= VERIFY_GLOBAL_HOURLY_MAX:
            return False
        _GLOBAL_SENDS.append(now)
        return True


def _record_send(account, now):
    sends = [t for t in (account.attributes.get(_SENDS_ATTR, default=None)
                         or []) if now - t < 86400]
    sends.append(now)
    account.attributes.add(_SENDS_ATTR, sends)


def build_message(account, email_address):
    """Render the confirmation email for an allauth EmailAddress."""
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


def prepare(account, email=None, bulk=False):
    """Validate, rate-limit, attach the address and render the email.

    Returns (message_for_player, email_message_or_None). Sending is left
    to the caller so the HTTP call can run off the reactor thread.
    bulk=True skips the per-account limits (send_bulk has its own).
    """
    from allauth.account.models import EmailAddress

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
        return ("That address is already used by another account. Type "
                "|wverify you@example.com|n with an address only you use, "
                "or sign in with Google.", None)

    now = time.time()
    if not bulk:
        limited = _account_limit_message(account, now)
        if limited:
            return (limited, None)
    if not _take_global_slot(now):
        return ("We can't send more verification emails right now. "
                "Please try again in an hour.", None)

    if (getattr(account, "email", "") or "").lower() != addr:
        account.email = addr
        account.save(update_fields=["email"])
    email_address = EmailAddress.objects.filter(
        user_id=account.id, email__iexact=addr).first()
    if email_address is None:
        has_primary = EmailAddress.objects.filter(
            user_id=account.id, primary=True).exists()
        email_address = EmailAddress.objects.create(
            user=account, email=addr, verified=False,
            primary=not has_primary)

    message = build_message(account, email_address)
    _record_send(account, now)
    return (f"We're sending a verification link to {addr}. Open it within "
            f"3 days to finish. Check your spam folder if it doesn't "
            f"arrive.", message)


def request_verification(account, email=None, reply=None):
    """`verify` command entry point. Prepares synchronously (fast ORM
    work) and sends on a worker thread; reply(text) runs on the reactor
    thread afterwards if the send fails."""
    text, message = prepare(account, email=email)
    if reply:
        reply(text)
    if message is None:
        return False

    def _failed(_result=None):
        if reply:
            reply("|rThe verification email didn't go out. Please try "
                  "again later.|n")

    try:
        from twisted.internet import reactor, threads
        running = reactor.running
    except Exception:
        running = False
    if running:
        # In the game: the Resend HTTP call runs on a worker thread so the
        # reactor never waits on it; the callback returns to the reactor.
        d = threads.deferToThread(message.send)
        d.addCallbacks(lambda sent: None if sent else _failed(),
                       lambda _f: _failed())
        return True
    # No reactor (shell, script, tests): send inline.
    try:
        if not message.send():
            _failed()
    except Exception:
        _failed()
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
    run, *delay* seconds apart (Resend allows about 2 a second; its free
    plan allows 100 a day). Dry run unless send=True. Returns the number
    sent (or that would be sent)."""
    candidates = bulk_candidates()
    out(f"{len(candidates)} unverified account(s) with an email address; "
        f"this run handles up to {limit}.")
    done = 0
    for account in candidates[:limit]:
        if not send:
            out(f"  would send to account #{account.id} ({account.username})")
            done += 1
            continue
        text, message = prepare(account, bulk=True)
        if message is None:
            out(f"  skipped #{account.id}: {text}")
            continue
        try:
            sent = message.send()
        except Exception as exc:
            sent = 0
            out(f"  failed #{account.id}: {type(exc).__name__}")
        if sent:
            account.attributes.add(_BULK_ATTR, time.time())
            done += 1
            out(f"  sent to account #{account.id} ({account.username})")
        time.sleep(delay)
    out(f"{'Sent' if send else 'Would send'}: {done}.")
    return done
