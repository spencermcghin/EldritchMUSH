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
import sys

# Module-level diagnostic — fires the moment Evennia imports this file.
# Lets us tell from the logs whether the file is being loaded at all
# (separate from whether the hook functions are actually called).
print("[at_server_startstop] module imported", flush=True)
sys.stdout.flush()


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
    print(f"[startup_migration] Checking AccountDB rows for typeclass binding...")
    try:
        from django.conf import settings as dj_settings
        from evennia.accounts.models import AccountDB

        target = getattr(dj_settings, "BASE_ACCOUNT_TYPECLASS", "typeclasses.accounts.Account")
        total = AccountDB.objects.count()

        # Match anything that isn't the canonical typeclass — covers both
        # the raw-model fallback ("evennia.accounts.models.AccountDB")
        # and any historical typo paths.
        broken = list(AccountDB.objects.exclude(db_typeclass_path=target))
        if not broken:
            print(
                f"[startup_migration] All {total} account(s) already bound to {target}; nothing to do."
            )
            return

        print(f"[startup_migration] Found {len(broken)}/{total} account(s) needing repair.")
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
        print(f"[startup_migration] Account typeclass repair: {repaired}/{len(broken)} fixed.")
    except Exception as exc:
        # Never crash boot over this migration.
        import traceback
        print(f"[startup_migration] Account typeclass migration ERROR: {exc}")
        traceback.print_exc()


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

    # Backfill subscription state on existing accounts. Accounts that
    # existed before the billing feature shipped have no
    # trial_started_at attribute — without it, is_in_trial() returns
    # False and the account shows as paywalled the moment it logs in.
    # This grants every pre-existing account a fresh 30-day trial
    # starting from the first boot after the billing feature lands.
    # Idempotent: skips accounts that already have trial_started_at.
    try:
        import datetime
        from evennia.accounts.models import AccountDB
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        backfilled = 0
        for acct in AccountDB.objects.all():
            try:
                if acct.attributes.get("trial_started_at", default=None):
                    continue
                acct.attributes.add("trial_started_at", now_iso)
                if not acct.attributes.get("subscription_status", default=None):
                    acct.attributes.add("subscription_status", "trialing")
                backfilled += 1
            except Exception as exc:
                print(f"[trial_backfill] failed for {getattr(acct, 'username', '?')}: {exc!r}", flush=True)
        if backfilled:
            print(f"[trial_backfill] granted 30-day trial to {backfilled} existing account(s)")
        else:
            print("[trial_backfill] all accounts already have trial state")
    except Exception as exc:
        print(f"[trial_backfill] outer error: {exc!r}", flush=True)

    # Bootstrap the global AmbientNpcScript if it's not already running.
    # Idempotent: if a previous boot already created it, this no-ops.
    try:
        from evennia.scripts.models import ScriptDB
        from evennia import create_script
        if not ScriptDB.objects.filter(db_key="ambient_npc_speech").exists():
            create_script(
                "typeclasses.scripts.AmbientNpcScript",
                key="ambient_npc_speech",
                persistent=True,
                autostart=True,
            )
            print("[at_server_start] AmbientNpcScript bootstrapped")
        else:
            print("[at_server_start] AmbientNpcScript already present")
    except Exception as exc:
        print(f"[at_server_start] AmbientNpcScript bootstrap FAILED: {exc!r}")

    # Bootstrap the telemetry heartbeat (operational logging + cost
    # alerts — see world/telemetry.py). Idempotent.
    try:
        from evennia.scripts.models import ScriptDB
        from evennia import create_script
        if not ScriptDB.objects.filter(db_key="telemetry_heartbeat").exists():
            create_script(
                "typeclasses.scripts.TelemetryHeartbeatScript",
                key="telemetry_heartbeat",
                persistent=True,
                autostart=True,
            )
            print("[at_server_start] TelemetryHeartbeatScript bootstrapped")
    except Exception as exc:
        print(f"[at_server_start] telemetry bootstrap FAILED: {exc!r}")

    # Bootstrap the gossip ticker (world/living_world.py). Idempotent.
    try:
        from evennia.scripts.models import ScriptDB
        from evennia import create_script
        if not ScriptDB.objects.filter(db_key="living_world_gossip").exists():
            create_script(
                "typeclasses.scripts.GossipScript",
                key="living_world_gossip",
                persistent=True,
                autostart=True,
            )
            print("[at_server_start] GossipScript bootstrapped")
    except Exception as exc:
        print(f"[at_server_start] gossip bootstrap FAILED: {exc!r}")

    # Bootstrap Dierdra's weekly dream. Idempotent.
    try:
        from evennia.scripts.models import ScriptDB
        from evennia import create_script
        if not ScriptDB.objects.filter(db_key="living_world_dream").exists():
            create_script(
                "typeclasses.scripts.DreamScript",
                key="living_world_dream",
                persistent=True,
                autostart=True,
            )
            print("[at_server_start] DreamScript bootstrapped")
    except Exception as exc:
        print(f"[at_server_start] dream bootstrap FAILED: {exc!r}")

    # Bootstrap the weekly Chronicle. Idempotent.
    try:
        from evennia.scripts.models import ScriptDB
        from evennia import create_script
        if not ScriptDB.objects.filter(
                db_key="living_world_chronicle").exists():
            create_script(
                "typeclasses.scripts.ChronicleScript",
                key="living_world_chronicle",
                persistent=True,
                autostart=True,
            )
            print("[at_server_start] ChronicleScript bootstrapped")
    except Exception as exc:
        print(f"[at_server_start] chronicle bootstrap FAILED: {exc!r}")

    # Bootstrap the moving Mists. Idempotent.
    try:
        from evennia.scripts.models import ScriptDB
        from evennia import create_script
        if not ScriptDB.objects.filter(db_key="living_world_mists").exists():
            create_script(
                "typeclasses.scripts.MistPassageScript",
                key="living_world_mists",
                persistent=True,
                autostart=True,
            )
            print("[at_server_start] MistPassageScript bootstrapped")
    except Exception as exc:
        print(f"[at_server_start] mists bootstrap FAILED: {exc!r}")

    # Bootstrap the Withering Maw's heartbeat. Idempotent.
    try:
        from evennia.scripts.models import ScriptDB
        from evennia import create_script
        if not ScriptDB.objects.filter(db_key="living_world_maw").exists():
            create_script(
                "typeclasses.scripts.WitheringMawScript",
                key="living_world_maw",
                persistent=True,
                autostart=True,
            )
            print("[at_server_start] WitheringMawScript bootstrapped")
    except Exception as exc:
        print(f"[at_server_start] maw bootstrap FAILED: {exc!r}")

    # Bootstrap moonstorms + revert any storm buff stranded by a crash.
    try:
        from evennia.scripts.models import ScriptDB
        from evennia import create_script
        if not ScriptDB.objects.filter(
                db_key="living_world_moonstorm").exists():
            create_script(
                "typeclasses.scripts.MoonstormScript",
                key="living_world_moonstorm",
                persistent=True,
                autostart=True,
            )
            print("[at_server_start] MoonstormScript bootstrapped")
        from world import living_world
        living_world.end_moonstorm(announce=False)
    except Exception as exc:
        print(f"[at_server_start] moonstorm bootstrap FAILED: {exc!r}")

    # Bootstrap NPC wound recovery. Idempotent.
    try:
        from evennia.scripts.models import ScriptDB
        from evennia import create_script
        if not ScriptDB.objects.filter(
                db_key="living_world_recovery").exists():
            create_script(
                "typeclasses.scripts.NpcRecoveryScript",
                key="living_world_recovery",
                persistent=True,
                autostart=True,
            )
            print("[at_server_start] NpcRecoveryScript bootstrapped")
    except Exception as exc:
        print(f"[at_server_start] recovery bootstrap FAILED: {exc!r}")

    # Cross-check quest content against the live world. Quest targets
    # bind by substring match, so a renamed room/NPC/item silently
    # strands quests — this surfaces those as boot-time log errors
    # instead of player-reported bugs. Never blocks startup.
    try:
        from world.quest_validation import run_and_report
        run_and_report(check_world=True,
                       out=lambda m: print(m, flush=True))
    except Exception as exc:
        print(f"[at_server_start] quest validation FAILED: {exc!r}")

    # Loud one-time notice if AI input moderation is disabled — the
    # regex banned-phrase filter alone is a noise filter, not a
    # defense. Set NPC_LLM_MODERATE=1 in production.
    try:
        import os as _os
        if _os.environ.get("NPC_LLM_MODERATE", "0") != "1":
            print(
                "[ai_safety] WARNING: NPC_LLM_MODERATE is disabled — "
                "AI NPC input moderation is OFF. Set NPC_LLM_MODERATE=1 "
                "in production.",
                flush=True,
            )
    except Exception:
        pass


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
