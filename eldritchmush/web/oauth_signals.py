"""
OAuth signal handlers, loaded as a side-effect import from web/urls.py.

We can't put this in a Django AppConfig because twistd's portal
subprocess fails to import any local Django app from INSTALLED_APPS
(see notes in server/conf/settings.py). web/urls.py is loaded via
ROOT_URLCONF AFTER django.setup() succeeds, so a side-effect import
here runs in a fully-initialized Django environment.

The OAuth callback URL (/accounts/google/login/callback/) is handled
by allauth, which goes through Django's URL routing, which loads
web/urls.py, which loads this module. So by the time the
user_signed_up signal could possibly fire, this handler is already
connected.
"""
try:
    from allauth.account.signals import user_signed_up
    from django.dispatch import receiver

    @receiver(user_signed_up)
    def log_new_oauth_signup(sender, request, user, **kwargs):
        """
        Fired once, the first time a user signs up via any allauth
        flow (Google OAuth in our case). `user` is an AccountDB
        instance because Evennia sets AUTH_USER_MODEL =
        "accounts.AccountDB".

        We don't create a character here — that happens later when
        the player picks a name in the CharacterSelect screen and
        the frontend sends `charcreate <name>`.
        """
        print(f"[oauth_signals] New OAuth account created: {user.username}")

    print("[oauth_signals] OAuth signal handlers connected.")
except ImportError:
    # django-allauth not installed — silently skip. The web/urls.py
    # also guards its allauth.urls include behind a try/except.
    pass
