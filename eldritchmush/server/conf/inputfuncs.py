"""
Input functions

Custom input handlers loaded via settings.INPUT_FUNC_MODULES. Anything
defined here overrides Evennia's defaults of the same name.

We override the `text` handler to write a diagnostic line to
/data/diag.log before forwarding to the stock handler. That gives us
unconditional visibility into every command frame that reaches the
server — which has been impossible to confirm any other way given
Railway's broken log capture.
"""
from evennia.server.inputfuncs import text as _stock_text


def text(session, *args, **kwargs):
    """
    Wrapper around Evennia's stock `text` inputfunc that:
      1. Logs every non-keepalive text frame to the diag sink.
      2. Dumps the live cmdset chain + account permissions on the
         first frame of any session, so we can see what the dispatcher
         actually has at hand.
      3. Force-dispatches `charcreate <name>` directly to our
         CmdCharCreate.func() if the cmdset chain isn't picking it up
         (workaround for the persistent dispatch bug we've been
         chasing all night). Falls back to the stock text handler for
         everything else.
    """
    try:
        from web.diag import diag_write

        txt = args[0] if args else None

        # Skip keepalive (empty text) frames — they flood the diag log.
        if txt is None or (isinstance(txt, str) and not txt.strip()):
            return _stock_text(session, *args, **kwargs)

        diag_write(
            "inputfunc.text RECEIVED",
            sessid=getattr(session, "sessid", None),
            logged_in=getattr(session, "logged_in", None),
            uid=getattr(session, "uid", None),
            account=repr(getattr(session, "account", None)),
            puppet=repr(getattr(session, "puppet", None)),
            text=txt,
        )

        # Dump cmdset chain + permissions on every command for now,
        # while we're hunting the dispatch bug.
        account = getattr(session, "account", None)
        try:
            session_cmdsets = []
            try:
                if hasattr(session, "cmdset") and session.cmdset:
                    for cs in session.cmdset.all():
                        session_cmdsets.append(getattr(cs, "key", repr(cs)))
            except Exception as exc:
                session_cmdsets = [f"<err: {exc}>"]
            diag_write("  session.cmdset.all()", cmdsets=session_cmdsets)

            if account is not None:
                try:
                    acct_cmdsets = []
                    if hasattr(account, "cmdset") and account.cmdset:
                        for cs in account.cmdset.all():
                            acct_cmdsets.append(getattr(cs, "key", repr(cs)))
                    diag_write("  account.cmdset.all()", cmdsets=acct_cmdsets)
                except Exception as exc:
                    diag_write("  account.cmdset.all() ERROR", exc=str(exc))
                try:
                    diag_write(
                        "  account.cmdset_storage",
                        storage=account.cmdset_storage,
                        db_cmdset_storage=getattr(account, "db_cmdset_storage", None),
                    )
                except Exception as exc:
                    diag_write("  account.cmdset_storage ERROR", exc=str(exc))

                # Dump permissions so we can see if the lock check
                # would even pass.
                try:
                    perms = list(account.permissions.all()) if hasattr(account, "permissions") else []
                    diag_write(
                        "  account.permissions",
                        perms=perms,
                        is_superuser=getattr(account, "is_superuser", None),
                        check_player=account.check_permstring("Player") if hasattr(account, "check_permstring") else None,
                    )
                except Exception as exc:
                    diag_write("  account.permissions ERROR", exc=str(exc))

                # Find charcreate in any account cmdset and report its
                # source class + lock string.
                try:
                    found = []
                    if hasattr(account, "cmdset") and account.cmdset:
                        for cs in account.cmdset.all():
                            for cmd in cs.commands:
                                if cmd.key == "charcreate":
                                    found.append(
                                        f"{cs.key}:{type(cmd).__module__}.{type(cmd).__name__} locks={getattr(cmd, 'locks', None)}"
                                    )
                    diag_write("  charcreate lookup", found=found or "NOT FOUND")
                except Exception as exc:
                    diag_write("  charcreate lookup ERROR", exc=str(exc))
        except Exception as exc:
            diag_write("inputfunc.text cmdset dump FAILED", exc=str(exc))

        # ----------------------------------------------------------------
        # WORKAROUND: directly invoke CmdCharCreate for `charcreate <name>`
        # frames when the session is authenticated to an account.
        #
        # We've confirmed via diag dumps that AccountCmdSet is correctly
        # attached to the account and contains our CmdCharCreate, yet
        # the standard cmdhandler dispatch never reaches func(). Until
        # we figure out why the cmdset merge/parser path isn't matching
        # this command, bypass it: parse the command name ourselves and
        # call CmdCharCreate.func() with the args wired up.
        # ----------------------------------------------------------------
        try:
            stripped = txt.strip()
            if stripped and account is not None:
                # Match `charcreate <args>` (case-insensitive) but not
                # words that just start with charcreate.
                lowered = stripped.lower()
                # __finish_chargen__ — teleport the puppeted character out
                # of the ChargenRoom to the game's START_LOCATION. Sent
                # by the chargen wizard's Finalize button after all set*
                # skill commands have been applied.
                if lowered == "__finish_chargen__":
                    try:
                        from django.conf import settings as dj_settings
                        from evennia.objects.models import ObjectDB
                        puppet = getattr(session, "puppet", None)
                        if puppet and puppet.location:
                            tc_path = puppet.location.typeclass_path or ""
                            if "ChargenRoom" in tc_path:
                                start_id = getattr(dj_settings, "START_LOCATION", 2)
                                start_loc = ObjectDB.objects.get_id(start_id)
                                if start_loc:
                                    puppet.move_to(start_loc, quiet=False)
                                    diag_write("FINISH_CHARGEN moved to start", puppet=repr(puppet), dest=repr(start_loc))
                                else:
                                    diag_write("FINISH_CHARGEN START_LOCATION not found", start_id=start_id)
                            else:
                                diag_write("FINISH_CHARGEN not in ChargenRoom, skipping", location=tc_path)
                        else:
                            diag_write("FINISH_CHARGEN no puppet or no location")
                    except Exception as exc:
                        diag_write("FINISH_CHARGEN FAILED", exc=str(exc))
                    return

                # __charsheet_ui__ — push structured character skill data
                if lowered == "__charsheet_ui__":
                    try:
                        puppet = getattr(session, "puppet", None)
                        if puppet:
                            db = puppet.db
                            def slot_name(s):
                                v = getattr(db, s, None)
                                if not v: return None
                                if isinstance(v, (list, tuple)):
                                    return getattr(v[0], "key", str(v[0])) if v else None
                                return getattr(v, "key", str(v))

                            from world.events import emit_to
                            emit_to(puppet, "charsheet_data", {
                                "name": puppet.key,
                                "status": {
                                    "body": getattr(db, "body", 0),
                                    "totalBody": getattr(db, "total_body", 0),
                                    "weaponBonus": getattr(db, "weapon_level", 0),
                                    "armorValue": getattr(db, "av", 0),
                                    "rightSlot": slot_name("right_slot"),
                                    "leftSlot": slot_name("left_slot"),
                                    "bodySlot": slot_name("body_slot"),
                                },
                                "activeMartial": {
                                    "Disarm": getattr(db, "disarm", 0),
                                    "Stun": getattr(db, "stun", 0),
                                    "Stagger": getattr(db, "stagger", 0),
                                    "Sunder": getattr(db, "sunder", 0),
                                    "Cleave": getattr(db, "cleave", 0),
                                },
                                "passiveMartial": {
                                    "Resist": getattr(db, "resist", 0),
                                    "Tough": getattr(db, "tough", 0),
                                    "Armor": getattr(db, "armor", 0),
                                    "Master of Arms": getattr(db, "master_of_arms", 0),
                                    "Armor Specialist": getattr(db, "armor_specialist", 0),
                                    "Sniper": getattr(db, "sniper", 0),
                                },
                                "proficiencies": {
                                    "Gunner": getattr(db, "gunner", 0),
                                    "Archer": getattr(db, "archer", 0),
                                    "Shields": getattr(db, "shields", 0),
                                    "Melee Weapons": getattr(db, "melee_weapons", 0),
                                    "Armor Proficiency": getattr(db, "armor_proficiency", 0),
                                },
                                "general": {
                                    "Perception": getattr(db, "perception", 0),
                                    "Tracking": getattr(db, "tracking", 0),
                                    "Medicine": getattr(db, "medicine", 0),
                                },
                                "profession": {
                                    "Stabilize": getattr(db, "stabilize", 0),
                                    "Battlefield Medicine": getattr(db, "battlefieldmedicine", 0),
                                    "Chirurgeon": getattr(db, "chirurgeon", 0),
                                    "Rally": getattr(db, "rally", 0),
                                    "Battlefield Commander": getattr(db, "battlefieldcommander", 0),
                                    "Vigil": getattr(db, "vigil", 0),
                                },
                                "crafting": {
                                    "Blacksmith": getattr(db, "blacksmith", 0),
                                    "Artificer": getattr(db, "artificer", 0),
                                    "Bowyer": getattr(db, "bowyer", 0),
                                    "Gunsmith": getattr(db, "gunsmith", 0),
                                    "Alchemist": getattr(db, "alchemist", 0),
                                },
                                "resources": {
                                    "Iron Ingots": getattr(db, "iron_ingots", 0),
                                    "Refined Wood": getattr(db, "refined_wood", 0),
                                    "Leather": getattr(db, "leather", 0),
                                    "Cloth": getattr(db, "cloth", 0),
                                    "Gold": getattr(db, "gold", 0),
                                    "Silver": getattr(db, "silver", 0),
                                    "Copper": getattr(db, "copper", 0),
                                },
                            })
                            diag_write("CHARSHEET_UI sent", puppet=repr(puppet))
                    except Exception as exc:
                        diag_write("CHARSHEET_UI FAILED", exc=str(exc))
                    return

                # __equip_ui__ — the frontend sends this (not a real MUD
                # command) to request structured inventory data for the
                # equip modal. We intercept it here and push the OOB event
                # directly; it never reaches the cmdhandler.
                if lowered == "__equip_ui__":
                    try:
                        from world.inventory_oob import push_inventory
                        puppet = getattr(session, "puppet", None)
                        if puppet:
                            push_inventory(puppet)
                            diag_write("EQUIP_UI push_inventory sent", puppet=repr(puppet))
                        else:
                            diag_write("EQUIP_UI no puppet — can't send inventory")
                    except Exception as exc:
                        diag_write("EQUIP_UI FAILED", exc=str(exc))
                    return

                # Direct-dispatch equip/unequip through the puppet's
                # command classes, bypassing the standard cmdhandler
                # (same dispatch issue as charcreate).
                if lowered.startswith("equip ") or lowered.startswith("unequip "):
                    puppet = getattr(session, "puppet", None)
                    if puppet:
                        try:
                            is_unequip = lowered.startswith("unequip ")
                            cmd_key = "unequip" if is_unequip else "equip"
                            cmdarg = stripped[len(cmd_key):].strip()
                            if is_unequip:
                                from commands.command import CmdUnequip as CmdClass
                            else:
                                from commands.command import CmdEquip as CmdClass
                            cmd = CmdClass()
                            cmd.caller = puppet
                            cmd.account = account
                            cmd.session = session
                            cmd.cmdname = cmd_key
                            cmd.raw_cmdname = cmd_key
                            cmd.cmdstring = cmd_key
                            cmd.args = " " + cmdarg if cmdarg else ""
                            cmd.raw_string = stripped
                            cmd.cmdset = None
                            cmd.cmdset_providers = {}
                            cmd.parse()
                            cmd.func()
                            # Force-push updated stats to the UI in case
                            # CmdEquip's own push_character_stats call
                            # didn't reach the client for some reason.
                            try:
                                from world.character_stats import push_character_stats
                                push_character_stats(puppet)
                            except Exception:
                                pass
                            diag_write(f"DIRECT DISPATCH {cmd_key} DONE", item=cmdarg)
                        except Exception as exc:
                            import traceback
                            diag_write(f"DIRECT DISPATCH {cmd_key} FAILED", exc=str(exc), traceback=traceback.format_exc())
                        return

                if lowered == "charcreate" or lowered.startswith("charcreate "):
                    cmdarg = stripped[len("charcreate"):].lstrip()
                    diag_write(
                        "DIRECT DISPATCH charcreate",
                        cmdarg=cmdarg,
                        account=repr(account),
                    )
                    try:
                        from commands.account import CmdCharCreate
                        cmd = CmdCharCreate()
                        cmd.caller = account
                        cmd.account = account
                        cmd.session = session
                        cmd.cmdname = "charcreate"
                        cmd.raw_cmdname = "charcreate"
                        cmd.cmdstring = "charcreate"
                        cmd.args = " " + cmdarg if cmdarg else ""
                        cmd.raw_string = stripped
                        cmd.cmdset = None
                        cmd.cmdset_providers = {}
                        # parse() splits args by `=` into lhs/rhs
                        cmd.parse()
                        cmd.func()
                        diag_write("DIRECT DISPATCH charcreate DONE")
                    except Exception as exc:
                        import traceback
                        diag_write(
                            "DIRECT DISPATCH charcreate FAILED",
                            exc=str(exc),
                            traceback=traceback.format_exc(),
                        )
                    # Don't forward to the stock handler — we already
                    # ran the command. Avoids double-execution if
                    # cmdhandler ever does pick it up.
                    return
        except Exception as exc:
            diag_write("inputfunc.text direct-dispatch wrapper FAILED", exc=str(exc))

    except Exception as exc:
        # Never break command input over a logging issue.
        try:
            from web.diag import diag_write
            diag_write("inputfunc.text DIAG FAILED", exc=str(exc))
        except Exception:
            pass

    # Forward to Evennia's real text handler — same call signature.
    return _stock_text(session, *args, **kwargs)
