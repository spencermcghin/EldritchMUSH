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
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class AccountAdapter(DefaultAccountAdapter):

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
