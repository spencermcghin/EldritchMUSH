"""
django-allauth adapters (wired up in server/conf/settings.py).

AccountAdapter
    Builds email confirmation links from SITE_BASE_URL (see
    world/email_verification.site_base_url), so links sent from inside
    the game, where there is no HTTP request, still point at the right
    host instead of the Django Sites default ("example.com").

SocialAccountAdapter
    Google sign-in may log into an existing local account that has the
    same email address (SOCIALACCOUNT_EMAIL_AUTHENTICATION), and connect
    to it (..._AUTO_CONNECT). That is only safe when the LOCAL address is
    verified: otherwise anyone could register a password account with a
    victim's Gmail address and wait for the victim to sign in with Google.
    can_authenticate_by_email() therefore requires a verified local
    EmailAddress for that address.
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class AccountAdapter(DefaultAccountAdapter):

    def get_email_confirmation_url(self, request, emailconfirmation):
        from django.urls import reverse
        from world.email_verification import site_base_url
        path = reverse("account_confirm_email", args=[emailconfirmation.key])
        return f"{site_base_url()}{path}"


class SocialAccountAdapter(DefaultSocialAccountAdapter):

    def can_authenticate_by_email(self, login, email):
        if not super().can_authenticate_by_email(login, email):
            return False
        from allauth.account.models import EmailAddress
        return EmailAddress.objects.filter(
            email__iexact=email, verified=True).exists()
