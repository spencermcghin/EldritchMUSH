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
    def setup_new_oauth_account(sender, request, user, **kwargs):
        """
        Fired once, the first time a user signs up via any allauth
        flow (Google OAuth in our case). `user` is an AccountDB
        instance because Evennia sets AUTH_USER_MODEL =
        "accounts.AccountDB".

        Evennia's normal account creation path calls
        `create.create_account()` which adds the default account
        permissions (typically "Player"). Allauth bypasses that and
        just creates the AccountDB row directly, so OAuth users end
        up with NO permissions and `cmd:pperm(Player)` locks reject
        them silently — including charcreate. We add the defaults
        here so OAuth users can use the same commands as everyone
        else.
        """
        from django.conf import settings as dj_settings

        try:
            default_perms = dj_settings.PERMISSION_ACCOUNT_DEFAULT
            if isinstance(default_perms, str):
                # Comma-separated string → list of perm names
                perms = [p.strip() for p in default_perms.split(",") if p.strip()]
            else:
                perms = list(default_perms)
            for perm in perms:
                user.permissions.add(perm)
            user.save()
            print(f"[oauth_signals] New OAuth account: {user.username} (perms={perms})")
        except Exception as exc:
            print(f"[oauth_signals] Could not grant default perms to {user.username}: {exc}")

    print("[oauth_signals] OAuth signal handlers connected.")
except ImportError:
    # django-allauth not installed — silently skip. The web/urls.py
    # also guards its allauth.urls include behind a try/except.
    pass
