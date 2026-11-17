"""
django-allauth adapters (wired up in server/conf/settings.py).

AccountAdapter
    Builds email confirmation links from SITE_BASE_URL (see
    world/email_verification.site_base_url), so links sent from inside
    the game, where there is no HTTP request, still point at the right
    host instead of the Django Sites default ("example.com").
    confirm_email() also removes the newly verified address from every
    OTHER account's unverified rows (and their User.email), so an address
    can't be squatted by someone who never verified it.
    send_mail() catches world.email.EmailNotSent (mail cap reached, Resend
    down, no key): the page carries on (the sign-up still completes) with
    a warning instead of a 500, and allauth's "we sent you an email" note
    is suppressed for that request.
    get_client_ip() can log the client-IP headers once, for checking the
    proxy setup (LOG_CLIENT_IP_HEADERS=1).

SocialAccountAdapter
    Google sign-in may log into an existing local account that has the
    same email address (SOCIALACCOUNT_EMAIL_AUTHENTICATION), and connect
    to it (..._AUTO_CONNECT). That is only safe when the LOCAL address is
    verified: otherwise anyone could register a password account with a
    victim's Gmail address and wait for the victim to sign in with Google.
    can_authenticate_by_email() therefore requires that EVERY local account
    allauth would match for that address (filter_users_by_email, the same
    lookup the login uses) holds it as a verified EmailAddress.
"""
import os
import threading

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

MAIL_FAILED_TEXT = "We couldn't send the email right now. Please try again later."
_MAIL_FAILED_FLAG = "_eldritch_mail_failed"
# allauth notices that claim an email went out.
_SENT_NOTICES = (
    "account/messages/email_confirmation_sent.txt",
)

_IP_LOG_LOCK = threading.Lock()
_IP_LOGGED = {"done": False}


def _log_client_ip_headers(request):
    """One log line with the headers allauth's client IP comes from, the
    first time it's asked. Off unless LOG_CLIENT_IP_HEADERS=1."""
    if os.environ.get("LOG_CLIENT_IP_HEADERS", "0") != "1":
        return
    with _IP_LOG_LOCK:
        if _IP_LOGGED["done"]:
            return
        _IP_LOGGED["done"] = True
    meta = getattr(request, "META", {}) or {}
    print(f"[client_ip] X-Real-IP={meta.get('HTTP_X_REAL_IP')!r} "
          f"X-Forwarded-For={meta.get('HTTP_X_FORWARDED_FOR')!r} "
          f"REMOTE_ADDR={meta.get('REMOTE_ADDR')!r}", flush=True)


class AccountAdapter(DefaultAccountAdapter):

    @staticmethod
    def _mail_failed(reason, what):
        print(f"[allauth] email not sent ({reason}): {what}", flush=True)
        from allauth.core import context as allauth_context
        request = allauth_context.request
        if request is None or getattr(request, _MAIL_FAILED_FLAG, False):
            return
        setattr(request, _MAIL_FAILED_FLAG, True)
        try:
            from django.contrib import messages
            messages.warning(request, MAIL_FAILED_TEXT)
        except Exception:
            pass

    def send_mail(self, template_prefix, email, context):
        from world.email import EmailNotSent
        try:
            return super().send_mail(template_prefix, email, context)
        except EmailNotSent as exc:
            self._mail_failed(exc.reason, template_prefix)
            return None

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        from world.email_verification import SiteURLNotConfigured
        try:
            return super().send_confirmation_mail(
                request, emailconfirmation, signup)
        except SiteURLNotConfigured:
            self._mail_failed("no SITE_BASE_URL", "email confirmation")
            return None

    def add_message(self, request, level, message_template=None,
                    message_context=None, extra_tags="", message=None):
        if (getattr(request, _MAIL_FAILED_FLAG, False)
                and message_template in _SENT_NOTICES):
            return None
        return super().add_message(
            request, level, message_template=message_template,
            message_context=message_context, extra_tags=extra_tags,
            message=message)

    def get_client_ip(self, request):
        """allauth's client IP, falling back to REMOTE_ADDR when the
        trusted header (X-Real-IP on Railway) is missing, so a proxy
        change degrades the per-IP limits instead of failing every
        sign-in with a 403."""
        _log_client_ip_headers(request)
        from allauth.core.internal.httpkit import get_client_ip
        ip = get_client_ip(request)
        if not ip:
            ip = (getattr(request, "META", {}) or {}).get("REMOTE_ADDR")
            if ip:
                print("[client_ip] trusted client-IP header missing; "
                      "using REMOTE_ADDR", flush=True)
        if not ip:
            return super().get_client_ip(request)
        return ip

    def get_email_confirmation_url(self, request, emailconfirmation):
        from django.urls import reverse
        from world.email_verification import site_base_url
        path = reverse("account_confirm_email", args=[emailconfirmation.key])
        return f"{site_base_url()}{path}"

    def confirm_email(self, request, email_address):
        confirmed = super().confirm_email(request, email_address)
        if confirmed:
            _drop_unverified_claims(email_address)
        return confirmed


def _drop_unverified_claims(email_address):
    """Remove a just-verified address from other accounts' unverified
    EmailAddress rows, and clear it from their User.email."""
    from django.contrib.auth import get_user_model
    from allauth.account.models import EmailAddress
    addr = email_address.email.lower()
    owner_id = email_address.user_id
    (EmailAddress.objects.filter(email__iexact=addr, verified=False)
     .exclude(user_id=owner_id).delete())
    User = get_user_model()
    for user in User.objects.filter(email__iexact=addr).exclude(id=owner_id):
        user.email = ""
        user.save(update_fields=["email"])


class SocialAccountAdapter(DefaultSocialAccountAdapter):

    def can_authenticate_by_email(self, login, email):
        if not super().can_authenticate_by_email(login, email):
            return False
        from allauth.account.models import EmailAddress
        from allauth.account.utils import filter_users_by_email
        addr = (email or "").lower()
        users = filter_users_by_email(addr, prefer_verified=True)
        if not users:
            return False
        return all(
            EmailAddress.objects.filter(
                user_id=u.id, email=addr, verified=True).exists()
            for u in users)
