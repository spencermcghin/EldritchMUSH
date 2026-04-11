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

        Allauth creates AccountDB rows directly via `user.save()`,
        which bypasses Evennia's `create.create_account()` helper.
        That helper does TWO things we have to replicate manually:

        1. Grants default Player permissions. Without these,
           `cmd:pperm(Player)` locks reject every command silently
           (including charcreate).
        2. Sets `db_typeclass_path` to the configured BASE_ACCOUNT_TYPECLASS
           ("typeclasses.accounts.Account"). Without this, the row
           defaults to the raw AccountDB model class on next load,
           which has *none* of the typeclass hook methods Evennia
           expects (`at_pre_login`, `at_post_login`, `at_disconnect`,
           `at_post_puppet`, etc.). Every login then crashes inside
           sessionhandler.login(), which means our `account_info` OOB
           event never fires and the React CharacterSelect screen
           hangs forever after the user clicks Begin.
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

            # Re-bind the row to the proper Evennia typeclass so all
            # the at_* hooks resolve. set_class_from_typeclass swaps
            # __class__ on the instance AND writes db_typeclass_path,
            # but does not call save() — we save explicitly.
            target_typeclass = getattr(
                dj_settings, "BASE_ACCOUNT_TYPECLASS", "typeclasses.accounts.Account"
            )
            try:
                user.set_class_from_typeclass(typeclass_path=target_typeclass)
            except Exception as exc:
                print(f"[oauth_signals] Could not bind typeclass {target_typeclass} to {user.username}: {exc}")

            user.save()
            print(
                f"[oauth_signals] New OAuth account: {user.username} "
                f"(perms={perms}, typeclass={user.db_typeclass_path})"
            )
        except Exception as exc:
            print(f"[oauth_signals] Could not finalize OAuth account {user.username}: {exc}")

    print("[oauth_signals] OAuth signal handlers connected.")
except ImportError:
    # django-allauth not installed — silently skip. The web/urls.py
    # also guards its allauth.urls include behind a try/except.
    pass
