"""
Server startstop hooks

This module contains functions called by Evennia at various
points during its startup, reload and shutdown sequence. It
allows for customizing the server operation as desired.

This module must contain at least these global functions:

at_server_start()
at_server_stop()
at_server_reload_start()
at_server_reload_stop()
at_server_cold_start()
at_server_cold_stop()

"""


def _migrate_oauth_account_typeclasses():
    """
    Repair AccountDB rows whose db_typeclass_path was never set to the
    proper typeclass. This happens when allauth creates an account via
    a raw `AccountDB.save()` call (bypassing Evennia's `create_account`
    helper). The row ends up bound to `evennia.accounts.models.AccountDB`
    — the raw Django model — which has none of the typeclass hook
    methods (at_pre_login, at_post_login, at_disconnect, at_post_puppet),
    so every login crashes in sessionhandler.login().

    Fixed forward in `web/oauth_signals.setup_new_oauth_account` for
    new signups, but pre-existing broken accounts still need to be
    repaired. Runs once on every server start; idempotent.
    """
    try:
        from django.conf import settings as dj_settings
        from evennia.accounts.models import AccountDB

        target = getattr(dj_settings, "BASE_ACCOUNT_TYPECLASS", "typeclasses.accounts.Account")

        # Match anything that isn't the canonical typeclass — covers both
        # the raw-model fallback ("evennia.accounts.models.AccountDB")
        # and any historical typo paths.
        broken = AccountDB.objects.exclude(db_typeclass_path=target)
        count = broken.count()
        if count == 0:
            return

        repaired = 0
        for acct in broken:
            old_path = acct.db_typeclass_path
            try:
                acct.set_class_from_typeclass(typeclass_path=target)
                acct.save()
                repaired += 1
                print(
                    f"[startup_migration] Repaired account {acct.username} "
                    f"(was: {old_path or 'NULL'}) → {target}"
                )
            except Exception as exc:
                print(
                    f"[startup_migration] Failed to repair account "
                    f"{getattr(acct, 'username', '?')}: {exc}"
                )
        print(f"[startup_migration] Account typeclass repair: {repaired}/{count} fixed.")
    except Exception as exc:
        # Never crash boot over this migration.
        print(f"[startup_migration] Account typeclass migration skipped: {exc}")


def at_server_start():
    """
    This is called every time the server starts up, regardless of
    how it was shut down.
    """
    from twisted.internet import task, reactor
    from evennia.server.sessionhandler import SESSIONS

    # Repair any AccountDB rows that allauth created with a missing or
    # wrong typeclass binding. Must run before any login attempts.
    _migrate_oauth_account_typeclasses()

    def _keepalive():
        try:
            for session in SESSIONS.all():
                try:
                    # Send an invisible keepalive that produces real WebSocket bytes
                    session.msg(" ")
                except Exception:
                    pass
        except Exception:
            pass

    lc = task.LoopingCall(_keepalive)
    # Fire immediately at start, then every 5s — Railway idle timeout is ~10s
    reactor.callLater(3, lc.start, 5, True)


def at_server_stop():
    """
    This is called just before the server is shut down, regardless
    of it is for a reload, reset or shutdown.
    """
    pass


def at_server_reload_start():
    """
    This is called only when server starts back up after a reload.
    """
    pass


def at_server_reload_stop():
    """
    This is called only time the server stops before a reload.
    """
    pass


def at_server_cold_start():
    """
    This is called only when the server starts "cold", i.e. after a
    shutdown or a reset.
    """
    pass


def at_server_cold_stop():
    """
    This is called only when the server goes down due to a shutdown or
    reset.
    """
    pass
