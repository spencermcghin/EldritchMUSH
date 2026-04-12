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

                            for room in list(rooms) + ([limbo] if limbo and limbo not in rooms else []):
                                if not room:
                                    continue
                                room_id = room.id
                                tc = room.typeclass_path or ""
                                room_type = "chargen" if "ChargenRoom" in tc else \
                                            "market" if "MarketRoom" in tc else \
                                            "weather" if "WeatherRoom" in tc else "room"
                                # Check for merchants/crafting stations
                                has_merchant = any(
                                    getattr(obj.db, "shop_inventory", None) is not None
                                    for obj in room.contents if obj != puppet
                                )
                                has_crafting = any(
                                    "Forge" in (getattr(obj, "typeclass_path", "") or "") or
                                    "Workbench" in (getattr(obj, "typeclass_path", "") or "")
                                    for obj in room.contents
                                )
                                nodes[room_id] = {
                                    "id": room_id,
                                    "name": __import__('re').sub(r'\|[a-zA-Z]|\|\d{3}|\|\[?\d+', '', room.key or '').strip(),
                                    "type": room_type,
                                    "hasMerchant": has_merchant,
                                    "hasCrafting": has_crafting,
                                    "current": room_id == (puppet.location.id if puppet.location else None),
                                }

                                # Find exits from this room
                                for obj in room.contents:
                                    if hasattr(obj, "destination") and obj.destination:
                                        dest_id = obj.destination.id
                                        edges.append({
                                            "from": room_id,
                                            "to": dest_id,
                                            "dir": obj.key,
                                        })

                            payload = {
                                "type": "map_data",
                                "_ts": time.time(),
                                "nodes": list(nodes.values()),
                                "edges": edges,
                                "currentRoom": puppet.location.id if puppet.location else None,
                            }
                            session.msg(event=payload)
                            diag_write("MAP_UI sent", rooms=len(nodes), edges=len(edges))
                    except Exception as exc:
                        import traceback
                        diag_write("MAP_UI FAILED", exc=str(exc), tb=traceback.format_exc())
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
                                                items.append({
                                                    "key": proto_key,
                                                    "name": proto.get("key", proto_key),
                                                    "desc": proto.get("desc", ""),
                                                    "price": price,
                                                    "damage": proto.get("damage", 0),
                                                    "materialValue": proto.get("material_value", 0),
                                                    "level": proto.get("level", 0),
                                                    "type": proto.get("craft_source", ""),
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
