"""
Signal handlers wired up by web/apps.py during app load.

When allauth creates a new AccountDB via Google OAuth, we do NOT
auto-create a Character. Instead, the React frontend's CharacterSelect
screen offers the player a choice: pick an existing character or
create a new one with their chosen name. New characters are spawned
in the ChargenRoom (via the custom `charcreate` command override) so
the ChargenWizard fires automatically.

This module is loaded by web/apps.py inside a try/except, so it's
safe to assume django-allauth is installed if we get this far.
"""
from allauth.account.signals import user_signed_up
from django.dispatch import receiver


@receiver(user_signed_up)
def log_new_oauth_signup(sender, request, user, **kwargs):
    """
    Fired once, the first time a user signs up via any allauth flow
    (Google OAuth in our case). `user` is an AccountDB instance because
    Evennia sets AUTH_USER_MODEL = "accounts.AccountDB".

    We don't create a character here — that happens later when the
    player picks a name in the CharacterSelect screen and the frontend
    sends `charcreate <name>`.
    """
    print(f"[web.signals] New OAuth account created: {user.username}")
