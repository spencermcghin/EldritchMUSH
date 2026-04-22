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

import re as _re

_TOPIC_PREFIXES = (
    "if pressed about ",
    "if asked about ",
    "if the player admits to ",
    "if the player seems ",
    "if the player has a ",
    "if the player has ",
    "if the player ",
    "has heard ",
    "will ",
    "can ",
    "may ",
)


def _shorten_topic(hook):
    """Boil a full AI-instruction hook down to a 2-4 word topic label
    suitable for both the chip and `ask <npc> <topic>`.

    Returns "" when the hook doesn't shorten to anything useful.
    """
    s = (str(hook) or "").strip()
    if not s:
        return ""
    low = s.lower()
    # Strip leading boilerplate instruction prefixes
    for pre in _TOPIC_PREFIXES:
        if low.startswith(pre):
            s = s[len(pre):]
            low = s.lower()
            break
    # If the hook contains "about X", pull X as the topic
    m = _re.search(r"\babout ([^,.;:]+)", s, _re.IGNORECASE)
    if m:
        s = m.group(1).strip()
    # Drop everything after first comma/period/semicolon
    s = _re.split(r"[.,;:]", s, 1)[0].strip()
    # Collapse whitespace, cap to first 4 words
    words = s.split()
    # Trim a trailing conjunction/preposition if present
    while words and words[-1].lower() in {
        "and", "or", "with", "for", "to", "the", "a", "an", "of", "in", "on", "at",
    }:
        words.pop()
    words = words[:4]
    label = " ".join(words).strip(" -—.,;:")
    # Skip trivially useless labels
    if not label or len(label) < 3:
        return ""
    return label[:40]


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
                                # Check if this account is admin
                                is_admin = bool(
                                    account and (
                                        account.is_superuser
                                        or account.check_permstring("Admin")
                                        or account.check_permstring("Builder")
                                    )
                                )

                                # Build skills summary for email
                                db = puppet.db
                                skill_lines = []
                                for attr, label in [
                                    ("melee_weapons", "Melee Weapons"), ("archer", "Archer"),
                                    ("shields", "Shields"), ("gunner", "Gunner"),
                                    ("armor_proficiency", "Armor Prof"),
                                    ("tough", "Tough"), ("master_of_arms", "Master of Arms"),
                                    ("disarm", "Disarm"), ("stun", "Stun"),
                                    ("stagger", "Stagger"), ("sunder", "Sunder"),
                                    ("cleave", "Cleave"), ("perception", "Perception"),
                                    ("tracking", "Tracking"), ("medicine", "Medicine"),
                                    ("blacksmith", "Blacksmith"), ("artificer", "Artificer"),
                                    ("bowyer", "Bowyer"), ("gunsmith", "Gunsmith"),
                                    ("alchemist", "Alchemist"), ("vigil", "Vigil"),
                                ]:
                                    val = getattr(db, attr, 0) or 0
                                    if val > 0:
                                        skill_lines.append(f"  {label}: {val}")
                                skills_summary = "\n".join(skill_lines) if skill_lines else "  (no skills set)"

                                start_id = getattr(dj_settings, "START_LOCATION", 2)
                                start_loc = ObjectDB.objects.get_id(start_id)

                                # Look up Gateway Tent City — the canonical
                                # arrival point for players emerging from chargen.
                                # Players land here pending approval and can
                                # wander Gateway (talk to NPCs, collect a Writ)
                                # until a game master approves their crossing.
                                gateway_tents = ObjectDB.objects.filter(
                                    db_key="Gateway — The Tent City"
                                ).first()

                                # Look up Mistgate — the far side of the Mists,
                                # where approved admins land directly.
                                mistgate = ObjectDB.objects.filter(
                                    db_key="The Mistgate"
                                ).first()

                                if is_admin:
                                    # Admins are auto-approved and walk straight
                                    # into the Annwyn. Skip the Gateway rigmarole.
                                    puppet.attributes.add("approval_status", "approved")
                                    target = mistgate or start_loc
                                    if target:
                                        puppet.move_to(target, quiet=False)
                                    session.msg(text="|gCharacter approved automatically (admin). Welcome to the world.|n")
                                    diag_write("FINISH_CHARGEN admin auto-approved", puppet=repr(puppet))
                                else:
                                    # Regular players: mark pending, issue a
                                    # Writ, and deposit them at Gateway Tent
                                    # City so they can meet the Mistwalker
                                    # Compact and wait for approval.
                                    puppet.attributes.add("approval_status", "pending")

                                    # Move puppet to Gateway Tent City (the
                                    # Arnesse-side arrival point). Falls back
                                    # to START_LOCATION if Gateway isn't built.
                                    arrival = gateway_tents or start_loc
                                    if arrival:
                                        puppet.move_to(arrival, quiet=True)

                                    # Spawn a Writ of Safe Conduct into the
                                    # player's inventory, bearer pre-filled.
                                    # This is their ticket once approved.
                                    try:
                                        from evennia.utils import create as _create_obj
                                        writ = _create_obj.create_object(
                                            "typeclasses.objects.WritOfSafeConduct",
                                            key="writ of safe conduct",
                                            location=puppet,
                                        )
                                        writ.aliases.add("writ")
                                        writ.db.bearer = puppet.key
                                        writ.db.crossings = 1
                                        diag_write("FINISH_CHARGEN writ issued", bearer=puppet.key)
                                    except Exception as exc:
                                        diag_write("FINISH_CHARGEN writ spawn failed", exc=str(exc))

                                    # Grant a Compact-issued starter purse so
                                    # the bearer can practice shopping with
                                    # Matron Hegga before crossing. 25 silver
                                    # is enough for a basic weapon + one kit.
                                    try:
                                        current_silver = puppet.db.silver or 0
                                        if current_silver < 25:
                                            puppet.db.silver = 25
                                            diag_write("FINISH_CHARGEN starter purse", silver=25)
                                    except Exception as exc:
                                        diag_write("FINISH_CHARGEN purse failed", exc=str(exc))

                                    # Send approval email to admin
                                    try:
                                        from world.email import send_approval_request
                                        acct_email = getattr(account, "email", "") or ""
                                        send_approval_request(
                                            puppet.key, account.username,
                                            acct_email, skills_summary
                                        )
                                    except Exception as exc:
                                        diag_write("FINISH_CHARGEN email failed", exc=str(exc))

                                    session.msg(text=(
                                        "|gYou stand at the tent city of Gateway, damp earth "
                                        "underfoot, the palisade looming westward. Your papers "
                                        "are submitted to the Mistwalker Compact — Crane will "
                                        "register you in due course.|n\n\n"
                                        "|xWhile you wait: |wlook|x around, |wask|x the "
                                        "Mistguard or the other travelers about their business, "
                                        "and |wlook writ|x to read the terms you have agreed to. "
                                        "A game master will approve your crossing when they have "
                                        "reviewed your build. You will receive an email.|n"
                                    ))
                                    diag_write("FINISH_CHARGEN pending approval at Gateway", puppet=repr(puppet))
                            else:
                                diag_write("FINISH_CHARGEN not in ChargenRoom, skipping", location=tc_path)
                        else:
                            diag_write("FINISH_CHARGEN no puppet or no location")
                    except Exception as exc:
                        diag_write("FINISH_CHARGEN FAILED", exc=str(exc))
                    return

                # __test_email__ — admin-only test to verify Resend works
                if lowered == "__test_email__":
                    is_admin = bool(
                        account and (account.is_superuser or account.check_permstring("Admin"))
                    )
                    if is_admin:
                        try:
                            from world.email import send_email
                            result = send_email(
                                "contact@eldritchmush.com",
                                "[EldritchMUSH] Test Email",
                                "<h1 style='color: #d4af37;'>Email is working!</h1><p>This is a test from EldritchMUSH.</p>"
                            )
                            session.msg(text=f"|g{'Email sent successfully!' if result else 'Email failed — check diag log.'}|n")
                        except Exception as exc:
                            session.msg(text=f"|400Email test failed: {exc}|n")
                    else:
                        session.msg(text="|400Admin only.|n")
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

                            # Send via session.msg (not character.msg via emit_to)
                            # because character.msg OOB events don't reliably
                            # reach the frontend from the inputfunc context.
                            import time
                            payload = {
                                "type": "charsheet_data",
                                "_ts": time.time(),
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
                            }
                            session.msg(event=payload)
                            diag_write("CHARSHEET_UI sent via session.msg", puppet=repr(puppet))
                    except Exception as exc:
                        diag_write("CHARSHEET_UI FAILED", exc=str(exc))
                    return

                # __map_ui__ — send the room graph for the interactive map
                if lowered == "__map_ui__":
                    try:
                        puppet = getattr(session, "puppet", None)
                        if puppet:
                            from evennia.objects.models import ObjectDB
                            import time
                            import re as _re

                            def _zone_for(room):
                                """Determine which zone a room belongs to.

                                Zones correspond to canonical settlements.
                                Preference order:
                                  1. Explicit room.db.zone attribute (set in populate scripts)
                                  2. Keyword-based inference from room key
                                  3. Default 'The Annwyn' (catch-all for travel/road rooms)
                                """
                                z = room.attributes.get("zone", default=None)
                                if z:
                                    return z
                                name = (room.key or "").lower()
                                tc = room.typeclass_path or ""
                                if "ChargenRoom" in tc:
                                    return "Arrival"
                                # Canonical settlements — match by name
                                if "ironhaven" in name or "hardinger" in name:
                                    return "Ironhaven"
                                if "arcton" in name or "falconer" in name:
                                    return "Arcton"
                                if "carran" in name:
                                    return "Carran"
                                if "harrowgate" in name or "coldhill" in name:
                                    return "Harrowgate"
                                if "goldleaf" in name:
                                    return "Goldleaf"
                                if "moonfall" in name:
                                    return "Moonfall"
                                if "tamris" in name or "barrow" in name:
                                    return "Tamris"
                                if "cirque" in name or "carnival" in name or "circus" in name:
                                    return "The Cirque"
                                # Gateway — Arnesse-side border town / Mistwall
                                if any(w in name for w in [
                                    "gateway", "mistwalker", "mistwall", "broken oar",
                                    "palisade", "tent city",
                                ]):
                                    return "Gateway"
                                # Mystvale and its sub-locations (Stag Hall is inside Mystvale)
                                if any(w in name for w in [
                                    "mystvale", "mistvale", "aentact", "songbird", "tavern", "raven", "marketplace",
                                    "crafter", "maker", "forge", "workbench", "hollow",
                                    "stag hall", "hart hall", "manor row", "chantry",
                                    "herbalist", "town hall", "back alley",
                                ]):
                                    return "Mystvale"
                                # Everything else (roads, mists, wilderness) → The Annwyn
                                return "The Annwyn"

                            # Get all rooms
                            room_classes = [
                                "typeclasses.rooms.Room",
                                "typeclasses.rooms.WeatherRoom",
                                "typeclasses.rooms.MarketRoom",
                                "typeclasses.rooms.ChargenRoom",
                            ]
                            rooms = ObjectDB.objects.filter(
                                db_typeclass_path__in=room_classes
                            )
                            # Also grab Limbo (#2)
                            limbo = ObjectDB.objects.filter(id=2).first()

                            nodes = {}
                            edges = []
                            zone_counts = {}

                            for room in list(rooms) + ([limbo] if limbo and limbo not in rooms else []):
                                if not room:
                                    continue
                                room_id = room.id
                                tc = room.typeclass_path or ""
                                room_type = "chargen" if "ChargenRoom" in tc else \
                                            "market" if "MarketRoom" in tc else \
                                            "weather" if "WeatherRoom" in tc else "room"
                                has_merchant = any(
                                    getattr(obj.db, "shop_inventory", None) is not None
                                    for obj in room.contents if obj != puppet
                                )
                                has_crafting = any(
                                    "Forge" in (getattr(obj, "typeclass_path", "") or "") or
                                    "Workbench" in (getattr(obj, "typeclass_path", "") or "")
                                    for obj in room.contents
                                )
                                zone = _zone_for(room)
                                zone_counts[zone] = zone_counts.get(zone, 0) + 1
                                nodes[room_id] = {
                                    "id": room_id,
                                    "name": _re.sub(r'\|[a-zA-Z]|\|\d{3}|\|\[?\d+', '', room.key or '').strip(),
                                    "type": room_type,
                                    "zone": zone,
                                    "hasMerchant": has_merchant,
                                    "hasCrafting": has_crafting,
                                    "current": room_id == (puppet.location.id if puppet.location else None),
                                }

                                for obj in room.contents:
                                    if hasattr(obj, "destination") and obj.destination:
                                        dest_id = obj.destination.id
                                        edges.append({
                                            "from": room_id,
                                            "to": dest_id,
                                            "dir": obj.key,
                                        })

                            # Build zone list sorted by node count (biggest first)
                            zones = [
                                {"name": z, "count": c}
                                for z, c in sorted(zone_counts.items(), key=lambda x: -x[1])
                            ]

                            # Current zone (for auto-select)
                            current_zone = None
                            if puppet.location:
                                for n in nodes.values():
                                    if n["current"]:
                                        current_zone = n["zone"]
                                        break

                            payload = {
                                "type": "map_data",
                                "_ts": time.time(),
                                "nodes": list(nodes.values()),
                                "edges": edges,
                                "zones": zones,
                                "currentRoom": puppet.location.id if puppet.location else None,
                                "currentZone": current_zone,
                            }
                            session.msg(event=payload)
                            diag_write("MAP_UI sent", rooms=len(nodes), zones=len(zones))
                    except Exception as exc:
                        import traceback
                        diag_write("MAP_UI FAILED", exc=str(exc), tb=traceback.format_exc())
                    return

                # __primer_ui__ — push the Traveler's Primer content as
                # a structured OOB event so the frontend renders a
                # parchment-styled modal instead of (or alongside) the
                # text return_appearance. Triggered by clicking a
                # primer item or via the synthetic command.
                if lowered == "__primer_ui__":
                    try:
                        import time as _time
                        session.msg(event={
                            "type": "primer_data",
                            "_ts": _time.time(),
                            "title": "A Traveler's Primer — Gateway Edition",
                            "subtitle": (
                                "Published by the Mistwalker Compact for "
                                "the use of bearers awaiting passage "
                                "through the Mists."
                            ),
                            "sections": [
                                {
                                    "header": "Getting Around",
                                    "rows": [
                                        ("look", "describe where you stand"),
                                        ("look <thing>", "study an object or person"),
                                        ("north / south / east / west", "walk through an exit"),
                                        ("out / in / up / down", "other directions"),
                                    ],
                                },
                                {
                                    "header": "Speaking with Others",
                                    "rows": [
                                        ("say <words>", "speak aloud to the room"),
                                        ("emote <action>", "perform a gesture or action"),
                                        ("ask <npc> <question>", "ask an NPC a question"),
                                        ("farewell <npc>", "end a conversation"),
                                        ("whisper <target>=<msg>", "private speech"),
                                    ],
                                },
                                {
                                    "header": "Your Things",
                                    "rows": [
                                        ("inventory", "list what you carry"),
                                        ("get <item>", "pick something up"),
                                        ("drop <item>", "put it down"),
                                        ("give <item> to <whom>", "hand something over"),
                                        ("equip <item>", "wear or wield"),
                                        ("unequip <item>", "take it off"),
                                    ],
                                },
                                {
                                    "header": "Buying and Selling",
                                    "rows": [
                                        ("browse <merchant>", "see wares with prices"),
                                        ("buy <item> from <merchant>", "purchase for silver"),
                                        ("sell <item> to <merchant>", "sell for half value"),
                                    ],
                                    "note": "Try this at Matron Hegga's stall in Gateway Square.",
                                },
                                {
                                    "header": "Understanding Yourself",
                                    "rows": [
                                        ("sheet", "see your character sheet"),
                                        ("status", "quick health check"),
                                        ("who", "who's currently playing"),
                                        ("help <topic>", "game help on any subject"),
                                    ],
                                },
                                {
                                    "header": "Diversions",
                                    "rows": [
                                        ("tavyl sit <dealer>", "join a card game"),
                                        ("tavyl hand", "see your cards"),
                                        ("tavyl play <card>", "play a card"),
                                    ],
                                    "note": "Mab the Gambler runs a Tavyl table at the Broken Oar.",
                                },
                                {
                                    "header": "When You Cross",
                                    "rows": [],
                                    "note": (
                                        "The Mistwalker Soap guides bearers through at the "
                                        "Mistwall. Your Writ of Safe Conduct must be lit "
                                        "before she will let you through — a game master "
                                        "will approve your passage when they have reviewed "
                                        "your build. Until then, wander, practice, and prepare."
                                    ),
                                },
                            ],
                            "signature": (
                                "Signed, Crane, Registrar of the Gateway Crossing Office"
                            ),
                        })
                    except Exception as exc:
                        diag_write("PRIMER_UI failed", exc=str(exc))
                    return

                # __room_meta__ — send per-NPC flags for the current room.
                # Used by the frontend DetailPanel to decide which contextual
                # action buttons to show (Play Tavyl for dealers, Browse for
                # merchants with shop_inventory, etc.).
                if lowered == "__room_meta__":
                    try:
                        puppet = getattr(session, "puppet", None)
                        if puppet and puppet.location:
                            import time as _time
                            npcs = []
                            for obj in puppet.location.contents:
                                if obj == puppet:
                                    continue
                                # Only include NPCs / merchants — anything that
                                # isn't a player character. Cheap filter: must
                                # have a key and not be an exit.
                                if hasattr(obj, "destination") and obj.destination:
                                    continue
                                # Must be a Character subclass (covers Npc and
                                # Merchant which extends Npc).
                                tcp = obj.typeclass_path or ""
                                if not (
                                    "Npc" in tcp
                                    or "Merchant" in tcp
                                    or "Character" in tcp
                                ):
                                    continue
                                # Skip puppeted player characters
                                if getattr(obj, "db_account_id", None) and getattr(obj, "has_account", False):
                                    continue
                                aliases = []
                                try:
                                    aliases = [a for a in obj.aliases.all()]
                                except Exception:
                                    pass
                                # Topic chips: only show when the NPC has
                                # explicit ai_quest_topics set. The old
                                # heuristic that tried to auto-shorten
                                # quest_hooks produced garbage fragments
                                # like "Needs a runner to". Curated labels
                                # only — no label is better than a bad one.
                                explicit = obj.attributes.get("ai_quest_topics", default=None) or []
                                topics = [str(t).strip() for t in explicit if str(t).strip()]
                                npcs.append({
                                    "name": obj.key,
                                    "dbref": obj.id,
                                    "aliases": aliases,
                                    "isTavylDealer": bool(obj.attributes.get("tavyl_dealer", default=False)),
                                    "tavylStake": int(obj.attributes.get("tavyl_stake", default=1) or 1),
                                    "isMerchant": getattr(obj.db, "shop_inventory", None) is not None,
                                    "hasAi": bool(obj.attributes.get("ai_personality", default=None)),
                                    "topics": topics[:4],
                                })
                            session.msg(event={
                                "type": "room_meta",
                                "_ts": _time.time(),
                                "roomKey": puppet.location.key,
                                "roomId": puppet.location.id,
                                "npcs": npcs,
                            })
                    except Exception as exc:
                        diag_write("ROOM_META FAILED", exc=str(exc))
                    return

                # __shop_ui__ — send structured merchant shop data
                if lowered == "__shop_ui__":
                    try:
                        puppet = getattr(session, "puppet", None)
                        if puppet and puppet.location:
                            merchants = [
                                obj for obj in puppet.location.contents
                                if obj != puppet and getattr(obj.db, "shop_inventory", None) is not None
                            ]
                            if merchants:
                                from evennia.prototypes import prototypes as proto_utils
                                import time
                                merchant_data = []
                                for m in merchants:
                                    items = []
                                    for proto_key in (m.db.shop_inventory or []):
                                        try:
                                            results = proto_utils.search_prototype(proto_key.lower())
                                            if not results:
                                                results = proto_utils.search_prototype(proto_key.upper())
                                            if results:
                                                proto = results[0]
                                                price = int(proto.get("value_silver", 0)) or max(1, int(proto.get("value_copper", 0)) // 10)
                                                proto_name = proto.get("key", proto_key)
                                                # Enrich with Item Effect text from the
                                                # Schematics master (CSV), since prototypes
                                                # don't carry effect descriptions.
                                                try:
                                                    from world import items_data
                                                    effect_text = items_data.get_effect(proto_name)
                                                except Exception:
                                                    effect_text = ""
                                                items.append({
                                                    "key": proto_key,
                                                    "name": proto_name,
                                                    "desc": proto.get("desc", ""),
                                                    "effect": effect_text,
                                                    "price": price,
                                                    "damage": proto.get("damage", 0),
                                                    "materialValue": proto.get("material_value", 0),
                                                    "level": proto.get("level", 0),
                                                    "type": proto.get("craft_source", ""),
                                                    "materials": {
                                                        "iron": proto.get("iron_ingots", 0),
                                                        "cloth": proto.get("cloth", 0),
                                                        "wood": proto.get("refined_wood", 0),
                                                        "leather": proto.get("leather", 0),
                                                    },
                                                })
                                        except Exception:
                                            pass
                                    merchant_data.append({
                                        "name": m.key,
                                        "desc": getattr(m.db, "desc", "") or "",
                                        "items": items,
                                    })
                                # Player's sellable inventory
                                sell_items = []
                                for item in puppet.contents:
                                    val = getattr(item.db, "value_silver", 0) or 0
                                    if not val:
                                        val = (getattr(item.db, "value_copper", 0) or 0) // 10
                                    sell_price = max(1, int(val) // 2) if val else 0
                                    sell_items.append({
                                        "name": item.key,
                                        "sellPrice": sell_price,
                                        "type": getattr(item.db, "craft_source", "") or "",
                                    })
                                payload = {
                                    "type": "shop_data",
                                    "_ts": time.time(),
                                    "merchants": merchant_data,
                                    "playerSilver": getattr(puppet.db, "silver", 0) or 0,
                                    "sellInventory": sell_items,
                                }
                                session.msg(event=payload)
                                diag_write("SHOP_UI sent", merchants=len(merchant_data))
                            else:
                                session.msg(text="|430There are no merchants here.|n")
                        else:
                            session.msg(text="|430You need to be in a room to shop.|n")
                    except Exception as exc:
                        diag_write("SHOP_UI FAILED", exc=str(exc))
                    return

                # __buy__ <item> from <merchant> — direct buy handler
                if lowered.startswith("__buy__ "):
                    try:
                        puppet = getattr(session, "puppet", None)
                        if puppet:
                            args = stripped[len("__buy__ "):].strip()
                            # Parse "item from merchant"
                            if " from " in args.lower():
                                parts = args.lower().split(" from ", 1)
                                item_name = parts[0].strip()
                                merchant_name = parts[1].strip()
                            else:
                                item_name = args.strip()
                                merchant_name = ""

                            # Find merchant
                            merchants = [
                                obj for obj in puppet.location.contents
                                if obj != puppet and getattr(obj.db, "shop_inventory", None) is not None
                            ]
                            if merchant_name:
                                merchants = [m for m in merchants if merchant_name in m.key.lower()]
                            if not merchants:
                                session.msg(text="|430No merchant found.|n")
                                return
                            merchant = merchants[0]

                            # Find proto in merchant inventory
                            from evennia.prototypes import prototypes as proto_utils
                            from evennia import spawn as ev_spawn
                            matched_proto = None
                            for proto_key in (merchant.db.shop_inventory or []):
                                results = proto_utils.search_prototype(proto_key.lower()) or proto_utils.search_prototype(proto_key.upper())
                                if results and item_name in results[0].get("key", "").lower():
                                    matched_proto = results[0]
                                    break

                            if not matched_proto:
                                session.msg(text=f"|430{merchant.key} doesn't sell '{item_name}'.|n")
                                return

                            price = int(matched_proto.get("value_silver", 0)) or max(1, int(matched_proto.get("value_copper", 0)) // 10)
                            silver = getattr(puppet.db, "silver", 0) or 0

                            if silver < price:
                                session.msg(text=f"|400You can't afford {matched_proto['key']}. It costs {price} silver; you have {silver}.|n")
                                return

                            spawned = ev_spawn(matched_proto, location=puppet)
                            if spawned:
                                puppet.db.silver = silver - price
                                session.msg(text=f"|gYou pay {price} silver and receive |w{matched_proto['key']}|g.|n")
                                diag_write("BUY DONE", item=matched_proto['key'], price=price)
                            else:
                                session.msg(text="|400Failed to create item.|n")
                    except Exception as exc:
                        diag_write("BUY FAILED", exc=str(exc))
                    return

                # __sell__ <item> — direct sell handler
                if lowered.startswith("__sell__ "):
                    try:
                        puppet = getattr(session, "puppet", None)
                        if puppet:
                            item_name = stripped[len("__sell__ "):].strip()
                            item = puppet.search(item_name, location=puppet)
                            if not item:
                                session.msg(text=f"|430You don't have '{item_name}'.|n")
                                return
                            # Check merchant exists
                            merchants = [
                                obj for obj in puppet.location.contents
                                if obj != puppet and getattr(obj.db, "shop_inventory", None) is not None
                            ]
                            if not merchants:
                                session.msg(text="|430There are no merchants here.|n")
                                return
                            merchant = merchants[0]
                            val = getattr(item.db, "value_silver", 0) or 0
                            if not val:
                                val = (getattr(item.db, "value_copper", 0) or 0) // 10
                            sell_price = max(1, int(val) // 2) if val else 0
                            if sell_price == 0:
                                session.msg(text=f"|430{merchant.key} has no interest in {item.key}.|n")
                                return
                            item_key = item.key
                            item.delete()
                            puppet.db.silver = (getattr(puppet.db, "silver", 0) or 0) + sell_price
                            session.msg(text=f"|gYou sell |w{item_key}|g to {merchant.key} for {sell_price} silver.|n")
                            diag_write("SELL DONE", item=item_key, price=sell_price)
                    except Exception as exc:
                        diag_write("SELL FAILED", exc=str(exc))
                    return

                # __alchemy_ui__ — push structured alchemy data for the
                # frontend AlchemyModal. Sends known recipes, reagent
                # inventory, kit status, and per-recipe canBrew flags.
                if lowered == "__alchemy_ui__":
                    try:
                        puppet = getattr(session, "puppet", None)
                        if puppet:
                            import time as _time
                            from world import alchemy_prototypes as _apmod
                            import inspect as _inspect

                            alchemist_level = getattr(puppet.db, "alchemist", 0) or 0
                            reagents = puppet.db.reagents or {}

                            # Kit check
                            kit_slot = getattr(puppet.db, "kit_slot", []) or []
                            kit = kit_slot[0] if kit_slot else None
                            has_kit = False
                            if kit and getattr(kit.db, "type", None) == "apothecary":
                                has_kit = (getattr(kit.db, "uses", 0) or 0) > 0

                            # Collect all apothecary prototypes from the module
                            all_protos = {}
                            for name, obj in _inspect.getmembers(_apmod):
                                if isinstance(obj, dict) and obj.get("craft_source") == "apothecary":
                                    proto_key = name.upper()
                                    all_protos[proto_key] = obj

                            # Get known recipes
                            known = puppet.db.known_recipes
                            if not isinstance(known, set):
                                known = set()
                            # Superusers see all recipes
                            is_su = getattr(puppet, "account", None) and getattr(puppet.account, "is_superuser", False)
                            if is_su:
                                recipe_keys = set(all_protos.keys())
                            else:
                                recipe_keys = set()
                                for k in known:
                                    ku = k.upper()
                                    if ku in all_protos:
                                        recipe_keys.add(ku)
                                    else:
                                        # Try matching by name
                                        for pk, pv in all_protos.items():
                                            if pv.get("key", "").lower() == k.lower():
                                                recipe_keys.add(pk)

                            recipes = []
                            for proto_key in sorted(recipe_keys):
                                proto = all_protos.get(proto_key)
                                if not proto:
                                    continue
                                level = proto.get("level", 1)
                                # Gather reagents
                                recipe_reagents = []
                                for i in range(1, 6):
                                    r_name = proto.get(f"reagent_{i}")
                                    r_qty = proto.get(f"reagent_{i}_qty", 0) or 0
                                    if r_name and r_qty > 0:
                                        have = reagents.get(r_name, 0)
                                        recipe_reagents.append({
                                            "name": r_name,
                                            "qty": r_qty,
                                            "have": have,
                                        })
                                # Check canBrew
                                can_brew = (
                                    alchemist_level >= level
                                    and has_kit
                                    and all(r["have"] >= r["qty"] for r in recipe_reagents)
                                )
                                recipes.append({
                                    "key": proto_key,
                                    "name": proto.get("key", proto_key),
                                    "level": level,
                                    "type": (proto.get("substance_type") or "").capitalize(),
                                    "effect": proto.get("effect", ""),
                                    "qty_produced": proto.get("qty_produced", 1),
                                    "reagents": recipe_reagents,
                                    "canBrew": can_brew,
                                })

                            payload = {
                                "type": "alchemy_data",
                                "_ts": _time.time(),
                                "alchemistLevel": alchemist_level,
                                "knownRecipes": recipes,
                                "reagents": {k: v for k, v in reagents.items() if v > 0},
                                "hasKit": has_kit,
                            }
                            session.msg(event=payload)
                            diag_write("ALCHEMY_UI sent", recipes=len(recipes))
                    except Exception as exc:
                        diag_write("ALCHEMY_UI FAILED", exc=str(exc))
                    return

                # __alchemy_brew__ <RECIPE_KEY> — brew a recipe via OOB,
                # bypassing the text `brew` command. Validates everything
                # server-side and pushes updated alchemy_data on success.
                if lowered.startswith("__alchemy_brew__ "):
                    try:
                        puppet = getattr(session, "puppet", None)
                        if puppet:
                            recipe_key = stripped[len("__alchemy_brew__ "):].strip().upper()
                            import time as _time
                            from world import alchemy_prototypes as _apmod
                            import inspect as _inspect
                            from evennia import spawn as ev_spawn

                            alchemist_level = getattr(puppet.db, "alchemist", 0) or 0
                            if not alchemist_level:
                                session.msg(text="|400You do not have the Alchemist skill.|n")
                                return

                            # Look up the prototype
                            all_protos = {}
                            for name, obj in _inspect.getmembers(_apmod):
                                if isinstance(obj, dict) and obj.get("craft_source") == "apothecary":
                                    all_protos[name.upper()] = obj

                            proto = all_protos.get(recipe_key)
                            if not proto:
                                session.msg(text=f"|400Unknown recipe: {recipe_key}|n")
                                return

                            # Recipe known check
                            is_su = getattr(puppet, "account", None) and getattr(puppet.account, "is_superuser", False)
                            if not is_su:
                                known = puppet.db.known_recipes
                                if not isinstance(known, set):
                                    known = set()
                                substance_name = proto.get("key", "")
                                if recipe_key not in known and substance_name.lower() not in {r.lower() for r in known}:
                                    session.msg(text=f"|400You don't know this recipe.|n")
                                    return

                            level = proto.get("level", 1)
                            substance_name = proto.get("key", recipe_key)
                            qty_produced = proto.get("qty_produced", 1)

                            # Skill level check
                            if alchemist_level < level:
                                session.msg(text=f"|400Your Alchemist skill (level {alchemist_level}) is too low for {substance_name} (level {level}).|n")
                                return

                            # Kit check
                            kit_slot = getattr(puppet.db, "kit_slot", []) or []
                            kit = kit_slot[0] if kit_slot else None
                            if not kit or getattr(kit.db, "type", None) != "apothecary":
                                session.msg(text="|430You need an Apothecary Kit equipped.|n")
                                return
                            if (getattr(kit.db, "uses", 0) or 0) <= 0:
                                session.msg(text=f"|400Your {kit.key} is out of uses.|n")
                                return

                            # Reagent checks
                            reagents = puppet.db.reagents or {}
                            required = {}
                            for i in range(1, 6):
                                r_name = proto.get(f"reagent_{i}")
                                r_qty = proto.get(f"reagent_{i}_qty", 0) or 0
                                if r_name and r_qty > 0:
                                    required[r_name] = required.get(r_name, 0) + r_qty

                            missing = []
                            for r_name, r_qty in required.items():
                                have = reagents.get(r_name, 0)
                                if have < r_qty:
                                    missing.append(f"{r_name} (need {r_qty}, have {have})")

                            if missing and not is_su:
                                session.msg(text="|400Missing reagents: " + ", ".join(missing) + "|n")
                                return

                            # All checks passed — consume reagents, use kit, spawn
                            if not is_su:
                                for r_name, r_qty in required.items():
                                    reagents[r_name] = reagents.get(r_name, 0) - r_qty
                                puppet.db.reagents = reagents

                            kit.db.uses -= 1

                            for _ in range(qty_produced):
                                item = ev_spawn(proto)
                                item[0].move_to(puppet, quiet=True)

                            dose_word = "dose" if qty_produced == 1 else "doses"
                            session.msg(text=f"|230You carefully brew {qty_produced} {dose_word} of |430{substance_name}|n|230.|n")
                            if puppet.location:
                                puppet.location.msg_contents(
                                    f"|230{puppet.key} works carefully over their apothecary kit, "
                                    f"producing a batch of {substance_name}.|n",
                                    exclude=puppet,
                                )

                            diag_write("ALCHEMY_BREW done", recipe=recipe_key, qty=qty_produced)

                            # Push updated alchemy data so the modal refreshes
                            # Re-run the same logic as __alchemy_ui__
                            try:
                                reagents = puppet.db.reagents or {}
                                kit_slot2 = getattr(puppet.db, "kit_slot", []) or []
                                kit2 = kit_slot2[0] if kit_slot2 else None
                                has_kit2 = False
                                if kit2 and getattr(kit2.db, "type", None) == "apothecary":
                                    has_kit2 = (getattr(kit2.db, "uses", 0) or 0) > 0

                                known2 = puppet.db.known_recipes
                                if not isinstance(known2, set):
                                    known2 = set()
                                if is_su:
                                    recipe_keys2 = set(all_protos.keys())
                                else:
                                    recipe_keys2 = set()
                                    for k in known2:
                                        ku = k.upper()
                                        if ku in all_protos:
                                            recipe_keys2.add(ku)
                                        else:
                                            for pk, pv in all_protos.items():
                                                if pv.get("key", "").lower() == k.lower():
                                                    recipe_keys2.add(pk)

                                recipes2 = []
                                for pk2 in sorted(recipe_keys2):
                                    p2 = all_protos.get(pk2)
                                    if not p2:
                                        continue
                                    lvl2 = p2.get("level", 1)
                                    rr2 = []
                                    for i in range(1, 6):
                                        rn = p2.get(f"reagent_{i}")
                                        rq = p2.get(f"reagent_{i}_qty", 0) or 0
                                        if rn and rq > 0:
                                            rr2.append({"name": rn, "qty": rq, "have": reagents.get(rn, 0)})
                                    cb2 = alchemist_level >= lvl2 and has_kit2 and all(r["have"] >= r["qty"] for r in rr2)
                                    recipes2.append({
                                        "key": pk2,
                                        "name": p2.get("key", pk2),
                                        "level": lvl2,
                                        "type": (p2.get("substance_type") or "").capitalize(),
                                        "effect": p2.get("effect", ""),
                                        "qty_produced": p2.get("qty_produced", 1),
                                        "reagents": rr2,
                                        "canBrew": cb2,
                                    })
                                session.msg(event={
                                    "type": "alchemy_data",
                                    "_ts": _time.time(),
                                    "alchemistLevel": alchemist_level,
                                    "knownRecipes": recipes2,
                                    "reagents": {k: v for k, v in reagents.items() if v > 0},
                                    "hasKit": has_kit2,
                                })
                            except Exception as exc2:
                                diag_write("ALCHEMY_BREW refresh failed", exc=str(exc2))
                    except Exception as exc:
                        import traceback
                        diag_write("ALCHEMY_BREW FAILED", exc=str(exc), tb=traceback.format_exc())
                        session.msg(text=f"|400Brew error: {exc}|n")
                    return

                # __crafting_ui__ — unified crafting modal. Pushes one
                # crafting_data OOB with a tab per craft_source the player
                # has the skill for (blacksmith/artificer/bowyer/gunsmith/
                # alchemy). Station and kit readiness are reported per tab.
                if lowered == "__crafting_ui__":
                    try:
                        puppet = getattr(session, "puppet", None)
                        if puppet:
                            from world.crafting_ui import build_payload as _cui_build
                            payload = _cui_build(puppet)
                            session.msg(event=payload)
                            diag_write(
                                "CRAFTING_UI sent",
                                tabs=[t["id"] for t in payload.get("tabs", [])],
                            )
                    except Exception as exc:
                        import traceback as _tb
                        diag_write(
                            "CRAFTING_UI FAILED",
                            exc=str(exc),
                            tb=_tb.format_exc(),
                        )
                    return

                # __craft_item__ <PROTO_KEY> — execute a chosen recipe.
                # Re-pushes crafting_data on success so the modal refreshes.
                if lowered.startswith("__craft_item__ "):
                    try:
                        puppet = getattr(session, "puppet", None)
                        if puppet:
                            recipe_key = stripped[len("__craft_item__ "):].strip()
                            from world.crafting_ui import (
                                craft_item as _cui_craft,
                                build_payload as _cui_build,
                            )
                            ok, msg, bcast = _cui_craft(puppet, recipe_key)
                            if msg:
                                session.msg(text=msg)
                            if ok and bcast and puppet.location:
                                puppet.location.msg_contents(bcast, exclude=puppet)
                            # Always refresh the modal so counts update
                            # whether success or failure.
                            session.msg(event=_cui_build(puppet))
                            diag_write("CRAFT_ITEM", recipe=recipe_key, ok=ok)
                    except Exception as exc:
                        import traceback as _tb
                        diag_write(
                            "CRAFT_ITEM FAILED",
                            exc=str(exc),
                            tb=_tb.format_exc(),
                        )
                        session.msg(text=f"|400Craft error: {exc}|n")
                    return

                # `brew`, `forge`, `craft` with no args — open the unified
                # crafting modal if the player is at a matching station.
                # With args, fall through to the stock text command.
                if lowered in ("brew", "forge", "craft"):
                    try:
                        puppet = getattr(session, "puppet", None)
                        if puppet:
                            from world.crafting_ui import (
                                build_payload as _cui_build,
                                CRAFT_SOURCES as _CS,
                            )
                            is_su = bool(
                                getattr(puppet, "account", None)
                                and getattr(puppet.account, "is_superuser", False)
                            )
                            # Check that any matching station exists.
                            # meta[2] is a tuple of typeclass class names.
                            _station_names = set()
                            for meta in _CS.values():
                                _station_names.update(meta[2])
                            has_any = is_su or (
                                puppet.location is not None
                                and any(
                                    (getattr(o, "typeclass_path", "") or "").rsplit(".", 1)[-1] in _station_names
                                    for o in puppet.location.contents
                                )
                            )
                            if has_any:
                                session.msg(event=_cui_build(puppet))
                                return
                            # No station — fall through to stock handler
                    except Exception as exc:
                        diag_write("UNIFIED CRAFT OPEN FAILED", exc=str(exc))
                    # Fall through to legacy per-command handling below.

                # `brew` without args — open the alchemy modal
                if lowered == "brew":
                    try:
                        puppet = getattr(session, "puppet", None)
                        if puppet:
                            # Check for workbench in room
                            has_workbench = False
                            if puppet.location:
                                for obj in puppet.location.contents:
                                    tcp = getattr(obj, "typeclass_path", "") or ""
                                    if "ApothecaryWorkbench" in tcp or "Apothecary" in tcp:
                                        has_workbench = True
                                        break
                            if has_workbench or (getattr(puppet, "account", None) and getattr(puppet.account, "is_superuser", False)):
                                # Re-use __alchemy_ui__ by recursing through text handler
                                session.msg(text="|430Opening the alchemy workbench...|n")
                                # Inline push of alchemy data (same as __alchemy_ui__)
                                import time as _time
                                from world import alchemy_prototypes as _apmod
                                import inspect as _inspect

                                alchemist_level = getattr(puppet.db, "alchemist", 0) or 0
                                reagents = puppet.db.reagents or {}
                                kit_slot = getattr(puppet.db, "kit_slot", []) or []
                                kit = kit_slot[0] if kit_slot else None
                                has_kit = False
                                if kit and getattr(kit.db, "type", None) == "apothecary":
                                    has_kit = (getattr(kit.db, "uses", 0) or 0) > 0

                                all_protos = {}
                                for name, obj in _inspect.getmembers(_apmod):
                                    if isinstance(obj, dict) and obj.get("craft_source") == "apothecary":
                                        all_protos[name.upper()] = obj

                                known = puppet.db.known_recipes
                                if not isinstance(known, set):
                                    known = set()
                                is_su = getattr(puppet, "account", None) and getattr(puppet.account, "is_superuser", False)
                                if is_su:
                                    recipe_keys = set(all_protos.keys())
                                else:
                                    recipe_keys = set()
                                    for k in known:
                                        ku = k.upper()
                                        if ku in all_protos:
                                            recipe_keys.add(ku)
                                        else:
                                            for pk, pv in all_protos.items():
                                                if pv.get("key", "").lower() == k.lower():
                                                    recipe_keys.add(pk)

                                recipes = []
                                for proto_key in sorted(recipe_keys):
                                    proto = all_protos.get(proto_key)
                                    if not proto:
                                        continue
                                    level = proto.get("level", 1)
                                    recipe_reagents = []
                                    for i in range(1, 6):
                                        r_name = proto.get(f"reagent_{i}")
                                        r_qty = proto.get(f"reagent_{i}_qty", 0) or 0
                                        if r_name and r_qty > 0:
                                            recipe_reagents.append({
                                                "name": r_name,
                                                "qty": r_qty,
                                                "have": reagents.get(r_name, 0),
                                            })
                                    can_brew = (
                                        alchemist_level >= level
                                        and has_kit
                                        and all(r["have"] >= r["qty"] for r in recipe_reagents)
                                    )
                                    recipes.append({
                                        "key": proto_key,
                                        "name": proto.get("key", proto_key),
                                        "level": level,
                                        "type": (proto.get("substance_type") or "").capitalize(),
                                        "effect": proto.get("effect", ""),
                                        "qty_produced": proto.get("qty_produced", 1),
                                        "reagents": recipe_reagents,
                                        "canBrew": can_brew,
                                    })

                                session.msg(event={
                                    "type": "alchemy_data",
                                    "_ts": _time.time(),
                                    "alchemistLevel": alchemist_level,
                                    "knownRecipes": recipes,
                                    "reagents": {k: v for k, v in reagents.items() if v > 0},
                                    "hasKit": has_kit,
                                })
                            else:
                                # No workbench — fall through to stock handler
                                # which will run CmdBrew (it'll show usage text)
                                return _stock_text(session, *args, **kwargs)
                    except Exception as exc:
                        diag_write("BREW UI FAILED", exc=str(exc))
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
                            push_inventory(puppet, session=session)
                            diag_write("EQUIP_UI push_inventory sent via session", puppet=repr(puppet))
                        else:
                            diag_write("EQUIP_UI no puppet — can't send inventory")
                    except Exception as exc:
                        diag_write("EQUIP_UI FAILED", exc=str(exc))
                    return

                # `inventory` / `inv` / `i` — push inventory_list AND emit
                # an inventory_open signal so the frontend auto-opens the
                # modal. This is a parallel path to the Equip sidebar
                # button, giving players a keyboard-driven way in.
                if lowered in ("inventory", "inv", "i"):
                    try:
                        import time as _time
                        from world.inventory_oob import push_inventory
                        puppet = getattr(session, "puppet", None)
                        if puppet:
                            push_inventory(puppet, session=session)
                            session.msg(event={
                                "type": "inventory_open",
                                "_ts": _time.time(),
                            })
                    except Exception as exc:
                        diag_write("INVENTORY CMD FAILED", exc=str(exc))
                    return

                # ── Equip / Unequip ──
                # Custom handler that bypasses CmdEquip/CmdUnequip entirely.
                # Handles auto-swap (equipping replaces existing item in slot)
                # and slot choice via syntax: equip <item> [to right|left]
                # Also: unequip <item> or unequip right|left|body|...
                if lowered.startswith("equip ") or lowered.startswith("unequip "):
                    puppet = getattr(session, "puppet", None)
                    if not puppet:
                        return
                    try:
                        is_unequip = lowered.startswith("unequip ")
                        cmdarg = stripped[len("unequip " if is_unequip else "equip "):].strip()

                        # Helper: persist a slot and notify
                        def _save_slot(slot_name, val):
                            puppet.attributes.add(slot_name, val)

                        def _get_slot(slot_name):
                            return puppet.attributes.get(slot_name, default=[])

                        def _push_updates():
                            try:
                                from world.character_stats import push_character_stats
                                from world.available_commands import push_available_commands
                                push_character_stats(puppet)
                                push_available_commands(puppet)
                            except Exception:
                                pass

                        if is_unequip:
                            # unequip <item> or unequip <slot_name>
                            # Try slot name first (right, left, body, etc.)
                            slot_map = {
                                "right": "right_slot", "right hand": "right_slot",
                                "left": "left_slot", "left hand": "left_slot",
                                "body": "body_slot", "armor": "body_slot",
                                "hands": "hand_slot", "gloves": "hand_slot",
                                "feet": "foot_slot", "boots": "foot_slot",
                                "clothing": "clothing_slot", "cloak": "cloak_slot",
                                "kit": "kit_slot", "arrows": "arrow_slot",
                                "bullets": "bullet_slot",
                            }
                            target_slot = slot_map.get(cmdarg.lower())
                            if target_slot:
                                slot_val = _get_slot(target_slot)
                                if slot_val:
                                    old_item = slot_val[0] if isinstance(slot_val, list) and slot_val else slot_val
                                    _save_slot(target_slot, [])
                                    # Two-handed: clear both slots
                                    if hasattr(old_item, "db") and getattr(old_item.db, "twohanded", False):
                                        _save_slot("right_slot", [])
                                        _save_slot("left_slot", [])
                                        puppet.db.weapon_level = 0
                                    elif hasattr(old_item, "db") and getattr(old_item.db, "damage", 0):
                                        puppet.db.weapon_level = 0
                                    if hasattr(old_item, "db") and getattr(old_item.db, "is_armor", False):
                                        puppet.db.armor = 0
                                        tough = getattr(puppet.db, "tough", 0) or 0
                                        armor_specialist = 1 if getattr(puppet.db, "armor_specialist", False) else 0
                                        puppet.db.av = tough + armor_specialist
                                    session.msg(text=f"You unequip {getattr(old_item, 'key', str(old_item))}.")
                                else:
                                    session.msg(text=f"Nothing equipped in that slot.")
                            else:
                                # Search by item name
                                item = puppet.search(cmdarg, location=puppet)
                                if item:
                                    removed = False
                                    for sn in ("right_slot", "left_slot", "body_slot", "hand_slot",
                                               "foot_slot", "clothing_slot", "cloak_slot",
                                               "kit_slot", "arrow_slot", "bullet_slot"):
                                        sv = _get_slot(sn)
                                        if sv and item in sv:
                                            sv.remove(item)
                                            _save_slot(sn, sv)
                                            removed = True
                                            # Two-handed
                                            if getattr(item.db, "twohanded", False):
                                                for other in ("right_slot", "left_slot"):
                                                    ov = _get_slot(other)
                                                    if item in ov:
                                                        ov.remove(item)
                                                        _save_slot(other, ov)
                                            if getattr(item.db, "damage", 0):
                                                puppet.db.weapon_level = 0
                                            if getattr(item.db, "is_armor", False):
                                                puppet.db.armor = 0
                                                tough = getattr(puppet.db, "tough", 0) or 0
                                                armor_specialist = 1 if getattr(puppet.db, "armor_specialist", False) else 0
                                                puppet.db.av = tough + armor_specialist
                                            break
                                    if removed:
                                        session.msg(text=f"You unequip {item.key}.")
                                    else:
                                        session.msg(text=f"{item.key} is not equipped.")
                            _push_updates()
                            diag_write(f"UNEQUIP DONE", item=cmdarg)

                        else:
                            # equip <item> [to right|left]
                            # Parse optional slot target
                            target_hand = None
                            parts = cmdarg.rsplit(" to ", 1)
                            if len(parts) == 2:
                                item_name = parts[0].strip()
                                hand_choice = parts[1].strip().lower()
                                if hand_choice in ("right", "right hand", "r"):
                                    target_hand = "right_slot"
                                elif hand_choice in ("left", "left hand", "l"):
                                    target_hand = "left_slot"
                                else:
                                    item_name = cmdarg  # "to" was part of name
                            else:
                                item_name = cmdarg

                            item = puppet.search(item_name, location=puppet)
                            if not item:
                                return

                            if getattr(item.db, "broken", False):
                                session.msg(text=f"|400{item.key} is broken and cannot be equipped.|n")
                                return

                            # Determine target slot
                            idb = item.db
                            if getattr(idb, "is_armor", False):
                                slot = "body_slot"
                            elif getattr(idb, "hand_slot", False):
                                slot = "hand_slot"
                            elif getattr(idb, "foot_slot", False):
                                slot = "foot_slot"
                            elif getattr(idb, "clothing_slot", False):
                                slot = "clothing_slot"
                            elif getattr(idb, "cloak_slot", False):
                                slot = "cloak_slot"
                            elif getattr(idb, "kit_slot", False):
                                slot = "kit_slot"
                            elif getattr(idb, "arrow_slot", False):
                                slot = "arrow_slot"
                            elif getattr(idb, "bullet_slot", False):
                                slot = "bullet_slot"
                            elif getattr(idb, "damage", 0) or getattr(idb, "is_shield", False) or getattr(idb, "is_bow", False):
                                # Weapon/shield — use target_hand or default to right
                                if target_hand:
                                    slot = target_hand
                                elif getattr(idb, "twohanded", False):
                                    slot = "right_slot"  # will also fill left
                                else:
                                    # Pick the first empty hand, or default right
                                    r = _get_slot("right_slot")
                                    l = _get_slot("left_slot")
                                    if not r:
                                        slot = "right_slot"
                                    elif not l:
                                        slot = "left_slot"
                                    else:
                                        slot = "right_slot"  # auto-replace right
                            else:
                                session.msg(text=f"Don't know how to equip {item.key}.")
                                return

                            # Auto-unequip whatever is in the target slot
                            old_items = _get_slot(slot)
                            if old_items:
                                old = old_items[0] if isinstance(old_items, list) else old_items
                                session.msg(text=f"You unequip {getattr(old, 'key', str(old))}.")
                                if getattr(old, "db", None) and getattr(old.db, "twohanded", False):
                                    _save_slot("right_slot", [])
                                    _save_slot("left_slot", [])
                                else:
                                    _save_slot(slot, [])
                                if hasattr(old, "db") and getattr(old.db, "damage", 0):
                                    puppet.db.weapon_level = 0
                                if hasattr(old, "db") and getattr(old.db, "is_armor", False):
                                    puppet.db.armor = 0

                            # Equip the new item
                            if getattr(idb, "twohanded", False):
                                # Two-handed: clear both, equip both
                                r_old = _get_slot("right_slot")
                                l_old = _get_slot("left_slot")
                                if r_old:
                                    session.msg(text=f"You unequip {getattr(r_old[0], 'key', str(r_old[0]))}.")
                                if l_old and l_old != r_old:
                                    session.msg(text=f"You unequip {getattr(l_old[0], 'key', str(l_old[0]))}.")
                                _save_slot("right_slot", [item])
                                _save_slot("left_slot", [item])
                            else:
                                _save_slot(slot, [item])

                            # Update derived stats
                            if getattr(idb, "damage", 0):
                                from commands import combat
                                h = combat.Helper(puppet)
                                puppet.db.weapon_level = h.weaponValue(idb.level)
                            if getattr(idb, "is_armor", False):
                                puppet.db.armor = getattr(idb, "material_value", 0) or 0
                                armor = puppet.db.armor
                                tough = getattr(puppet.db, "tough", 0) or 0
                                armor_specialist = 1 if getattr(puppet.db, "armor_specialist", False) else 0
                                indomitable = getattr(puppet.db, "indomitable", 0) or 0
                                puppet.db.av = armor + tough + armor_specialist + indomitable

                            session.msg(text=f"You equip {item.key}.")
                            if puppet.location:
                                puppet.location.msg_contents(
                                    f"|025{puppet.key} equips their {item.key}.|n",
                                    exclude=[puppet]
                                )
                            _push_updates()
                            diag_write(f"EQUIP DONE", item=item_name, slot=slot)
                    except Exception as exc:
                        import traceback
                        diag_write(f"EQUIP/UNEQUIP FAILED", exc=str(exc), tb=traceback.format_exc())
                        session.msg(text=f"|400Error: {exc}|n")
                    return

                # Direct-dispatch workaround for `ic <name>` and bare
                # `ooc`, same pattern as the charcreate workaround below.
                # Evennia's cmdhandler doesn't route to the account-level
                # CmdIC/CmdOOC funcs for our WS sessions, so we do it
                # ourselves via account.puppet_object / unpuppet_object.
                if (lowered == "ic" or lowered.startswith("ic ")) and account is not None:
                    try:
                        from evennia.objects.models import ObjectDB
                        arg = stripped[2:].strip() if len(stripped) > 2 else ""
                        target = None
                        playable = account.db._playable_characters or []
                        if arg:
                            for pc in playable:
                                if pc and pc.key.lower() == arg.lower():
                                    target = pc
                                    break
                            if target is None:
                                # Fallback: global lookup (superuser convenience)
                                hits = ObjectDB.objects.filter(
                                    db_key__iexact=arg,
                                    db_typeclass_path__endswith=".Character",
                                )
                                if hits.count() == 1:
                                    target = hits.first()
                        else:
                            # Bare `ic` — puppet the latest controlled
                            last = account.db._last_puppet
                            if last and last in playable:
                                target = last
                            elif playable:
                                target = playable[0]
                        if target is None:
                            session.msg(text="|400No such character to puppet.|n")
                            return
                        try:
                            account.puppet_object(session, target)
                            account.db._last_puppet = target
                            diag_write("DIRECT DISPATCH ic DONE", target=target.key)
                        except Exception as exc:
                            import traceback
                            diag_write(
                                "DIRECT DISPATCH ic FAILED",
                                target=repr(target),
                                exc=str(exc),
                                tb=traceback.format_exc(),
                            )
                            session.msg(text=f"|400Puppet failed: {exc}|n")
                    except Exception as exc:
                        import traceback
                        diag_write(
                            "DIRECT DISPATCH ic ERROR",
                            exc=str(exc),
                            tb=traceback.format_exc(),
                        )
                    return

                if lowered == "ooc" and account is not None:
                    try:
                        puppet = getattr(session, "puppet", None)
                        if puppet:
                            account.db._last_puppet = puppet
                            account.unpuppet_object(session)
                        # Re-show the OOC look so the client lands on the
                        # character-select screen.
                        session.msg(text="You go OOC.")
                        diag_write("DIRECT DISPATCH ooc DONE")
                    except Exception as exc:
                        import traceback
                        diag_write(
                            "DIRECT DISPATCH ooc FAILED",
                            exc=str(exc),
                            tb=traceback.format_exc(),
                        )
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
