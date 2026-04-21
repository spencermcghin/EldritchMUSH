"""
world/available_commands.py — Context-aware command list for the web UI sidebar.

Call push_available_commands(character) whenever the character's available
actions might have changed:
  - After they move to a new room
  - After combat state changes (enter/leave combat loop)
  - After equipment changes
  - After taking damage that changes their state

The function builds a list of command descriptors and pushes them to the
character's web client via an OOB "available_commands" event. The frontend
can render these as a scrollable sidebar of clickable/typeable commands.

Command descriptor format
-------------------------
{
    "key":       "strike",           # the actual command to type
    "label":     "Strike",           # display name
    "args_hint": "<target>",         # placeholder shown in the UI
    "category":  "Combat",
    "enabled":   true,               # false = grayed out with reason shown
    "reason":    "",                 # why it's disabled (empty when enabled)
}
"""

from world.events import emit_to


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _cmd(key, label, args_hint="", category="General", enabled=True, reason=""):
    return {
        "key": key,
        "label": label,
        "args_hint": args_hint,
        "category": category,
        "enabled": enabled,
        "reason": reason,
    }


def _is_in_combat(character):
    room = character.location
    if not room:
        return False
    loop = getattr(room.db, "combat_loop", None)
    return loop is not None and character in loop


def _has_weapon(character):
    right = (character.db.right_slot or [None])[0]
    left = (character.db.left_slot or [None])[0]

    def has_damage(slot_obj):
        if not slot_obj:
            return False
        obj = character.search(slot_obj, location=character, quiet=True)
        if not obj:
            return False
        item = obj[0] if isinstance(obj, list) else obj
        return bool(item.db.damage and item.db.damage > 0)

    return has_damage(right) or has_damage(left)


def _has_bow(character):
    right = (character.db.right_slot or [None])[0]
    left = (character.db.left_slot or [None])[0]
    for slot in (right, left):
        if slot:
            obj = character.search(slot, location=character, quiet=True)
            if obj:
                item = obj[0] if isinstance(obj, list) else obj
                if item.db.is_bow:
                    return True
    return False


def _has_arrows(character):
    return bool(character.db.arrow_slot)


def _has_bullets(character):
    return bool(character.db.bullet_slot)


def _can_fight(character):
    return bool(character.db.bleed_points and character.db.bleed_points > 0)


def _is_bleeding(character):
    bp = character.db.bleed_points or 0
    return bp == 0 and bool(character.db.death_points and character.db.death_points > 0)


def _has_chirurgeons_kit(character):
    kit_slot = character.db.kit_slot
    if not kit_slot:
        return False
    kit = kit_slot[0] if isinstance(kit_slot, list) else kit_slot
    obj = character.search(kit, location=character, quiet=True)
    if not obj:
        return False
    item = obj[0] if isinstance(obj, list) else obj
    return getattr(item.db, "type", None) == "chirurgeon" and (item.db.uses or 0) > 0


def _has_apothecary_kit(character):
    kit_slot = character.db.kit_slot
    if not kit_slot:
        return False
    kit = kit_slot[0] if isinstance(kit_slot, list) else kit_slot
    obj = character.search(kit, location=character, quiet=True)
    if not obj:
        return False
    item = obj[0] if isinstance(obj, list) else obj
    return getattr(item.db, "type", None) == "apothecary" and (item.db.uses or 0) > 0


def _room_has_merchant(character):
    if not character.location:
        return False
    for obj in character.location.contents:
        if obj.db.shop_inventory is not None:
            return True
    return False


def _room_has_forge(character):
    if not character.location:
        return False
    for obj in character.location.contents:
        if obj.__class__.__name__ in ("Forge", "BlacksmithStation"):
            return True
        cmdsets = [cs.key for cs in obj.cmdset.all()]
        if "BlacksmithCmdSet" in cmdsets:
            return True
    return False


def _room_has_workbench(character):
    if not character.location:
        return False
    for obj in character.location.contents:
        cmdsets = [cs.key for cs in obj.cmdset.all()]
        if "CrafterCmdSet" in cmdsets or "ApothecaryWorkbenchCmdSet" in cmdsets:
            return True
    return False


def _room_has_apothecary_workbench(character):
    if not character.location:
        return False
    for obj in character.location.contents:
        cmdsets = [cs.key for cs in obj.cmdset.all()]
        if "ApothecaryWorkbenchCmdSet" in cmdsets:
            return True
    return False


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_available_commands(character):
    """Return a list of command descriptors appropriate for *character* right now."""
    commands = []
    in_combat = _is_in_combat(character)
    can_fight = _can_fight(character)
    bleeding = _is_bleeding(character)
    has_turn = bool(character.db.combat_turn)
    has_weapon = _has_weapon(character)
    has_bow = _has_bow(character)
    has_arrows = _has_arrows(character)
    has_bullets = _has_bullets(character)

    # --- Always-available general commands ---
    commands.append(_cmd("look", "Look", "[<target>]", "General"))
    commands.append(_cmd("inventory", "Inventory", "", "General"))
    commands.append(_cmd("equipment", "Equipment", "", "General"))
    commands.append(_cmd("charsheet", "Character Sheet", "", "General"))
    commands.append(_cmd("score", "Score", "", "General"))

    # --- Combat commands ---
    if in_combat:
        # Disengage is always available in combat (even while bleeding)
        commands.append(_cmd("disengage", "Disengage", "", "Combat"))

        if bleeding:
            # Can only disengage when bleeding
            pass
        elif can_fight:
            if has_turn:
                if has_weapon:
                    commands.append(_cmd("strike", "Strike", "<target>", "Combat"))
                    if character.db.cleave:
                        commands.append(_cmd("cleave", "Cleave", "<target>", "Combat"))
                    if character.db.disarm:
                        commands.append(_cmd("disarm", "Disarm", "<target>", "Combat"))
                    if character.db.stagger:
                        commands.append(_cmd("stagger", "Stagger", "<target>", "Combat"))
                    if character.db.stun:
                        commands.append(_cmd("stun", "Stun", "<target>", "Combat"))
                    if character.db.sunder:
                        commands.append(_cmd("sunder", "Sunder", "<target>", "Combat"))
                else:
                    commands.append(_cmd(
                        "strike", "Strike", "<target>", "Combat",
                        enabled=False, reason="No weapon equipped"
                    ))

                if has_bow and has_arrows:
                    commands.append(_cmd("shoot", "Shoot", "<target>", "Combat"))
                elif has_bow:
                    commands.append(_cmd(
                        "shoot", "Shoot", "<target>", "Combat",
                        enabled=False, reason="No arrows equipped"
                    ))

                if character.db.resist:
                    commands.append(_cmd("resist", "Resist", "", "Combat"))

                # Healing in combat
                if character.db.medicine or character.db.stabilize or character.db.battlefieldmedicine:
                    kit_ok = _has_chirurgeons_kit(character)
                    commands.append(_cmd(
                        "heal", "Heal", "<target>", "Combat",
                        enabled=kit_ok,
                        reason="" if kit_ok else "No chirurgeon's kit equipped"
                    ))
                if character.db.chirurgeon:
                    kit_ok = _has_chirurgeons_kit(character)
                    commands.append(_cmd(
                        "chirurgery", "Chirurgery", "<target>", "Combat",
                        enabled=kit_ok,
                        reason="" if kit_ok else "No chirurgeon's kit equipped"
                    ))

                commands.append(_cmd("skip", "Skip Turn", "", "Combat"))

            else:
                # Not my turn — show grayed-out combat commands so player knows what's coming
                commands.append(_cmd(
                    "strike", "Strike", "<target>", "Combat",
                    enabled=False, reason="Waiting for your turn"
                ))

    else:
        # Out of combat — show entry options
        commands.append(_cmd("strike", "Strike", "<target>", "Combat"))
        if has_bow and has_arrows:
            commands.append(_cmd("shoot", "Shoot", "<target>", "Combat"))
        elif has_bow:
            commands.append(_cmd(
                "shoot", "Shoot", "<target>", "Combat",
                enabled=False, reason="No arrows equipped"
            ))

    # --- Healing (out of combat) ---
    if not in_combat:
        if character.db.medicine or character.db.stabilize or character.db.battlefieldmedicine:
            kit_ok = _has_chirurgeons_kit(character)
            commands.append(_cmd(
                "heal", "Heal", "<target>", "Healing",
                enabled=kit_ok,
                reason="" if kit_ok else "No chirurgeon's kit equipped"
            ))
        if character.db.chirurgeon:
            kit_ok = _has_chirurgeons_kit(character)
            commands.append(_cmd(
                "chirurgery", "Chirurgery", "<target>", "Healing",
                enabled=kit_ok,
                reason="" if kit_ok else "No chirurgeon's kit equipped"
            ))

    # --- Crafting (location-dependent) ---
    # One unified "Crafting" entry. The frontend opens the multi-tab
    # CraftingModal; the server's __crafting_ui__ OOB handler enumerates
    # per-skill tabs. Show the entry if the player has any crafting skill
    # AND is standing at a matching station — that way the button only
    # appears in contexts where at least one tab will be usable.
    at_forge = _room_has_forge(character)
    at_workbench = _room_has_workbench(character)
    at_apoth = _room_has_apothecary_workbench(character)
    has_any_craft_skill = any(
        getattr(character.db, s, 0)
        for s in ("blacksmith", "bowyer", "artificer", "gunsmith", "alchemist")
    )
    if has_any_craft_skill and (at_forge or at_workbench or at_apoth):
        commands.append(_cmd(
            "__crafting_ui__", "Crafting", "", "Crafting"
        ))

    # Repair stays text-based — it's a single targeted action, not a menu.
    if at_workbench or at_forge:
        if character.db.blacksmith or character.db.artificer or character.db.bowyer or character.db.gunsmith:
            commands.append(_cmd("repair", "Repair", "<item>", "Crafting"))

    # Reagents list is a text dump, not part of the modal.
    if at_apoth and character.db.alchemist:
        commands.append(_cmd("reagents", "Reagents", "", "Alchemy"))

    # --- Shop (location-dependent) ---
    if _room_has_merchant(character):
        commands.append(_cmd("browse", "Browse", "[<merchant>]", "Shop"))
        commands.append(_cmd("buy", "Buy", "<item> from <merchant>", "Shop"))
        commands.append(_cmd("sell", "Sell", "<item> to <merchant>", "Shop"))

    # --- Tracking / Perception ---
    if character.db.tracking:
        commands.append(_cmd("track", "Track", "", "Exploration"))
    if character.db.perception:
        commands.append(_cmd("perception", "Perception", "", "Exploration"))

    return commands


# ---------------------------------------------------------------------------
# Push helper
# ---------------------------------------------------------------------------

def push_available_commands(character):
    """Compute and push the available-commands sidebar list to *character*'s web client."""
    commands = build_available_commands(character)
    emit_to(character, "available_commands", {"commands": commands})
