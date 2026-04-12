"""
world/inventory_oob.py — Push structured inventory data to the web UI.

Call push_inventory(character) when the frontend requests an equip
screen. Sends an `inventory_list` OOB event containing every item
in the character's inventory with metadata about type, slot, and
current equipped status.
"""
from world.events import emit_to

# Skill check mapping — mirrors the logic in CmdEquip.func()
_SKILL_LABELS = {
    "gunner": "Firearms",
    "archer": "Archery",
    "shields": "Shields",
    "melee_weapons": "Melee Weapons",
    "armor_proficiency": "Armor",
}


# Map of slot attribute name → human-readable label
_SLOT_LABELS = {
    "right_slot": "Right Hand",
    "left_slot": "Left Hand",
    "body_slot": "Body",
    "hand_slot": "Hands",
    "foot_slot": "Feet",
    "clothing_slot": "Clothing",
    "cloak_slot": "Cloak",
    "kit_slot": "Kit",
    "arrow_slot": "Arrows",
    "bullet_slot": "Bullets",
}

_ALL_SLOTS = list(_SLOT_LABELS.keys())


def _item_type(item):
    """Determine a display type string for an item."""
    db = item.db
    if getattr(db, "is_armor", False):
        return "armor"
    if getattr(db, "is_shield", False):
        return "shield"
    if getattr(db, "is_bow", False):
        return "bow"
    if getattr(db, "damage", 0):
        return "weapon"
    if getattr(db, "hand_slot", False):
        return "gloves"
    if getattr(db, "foot_slot", False):
        return "boots"
    if getattr(db, "clothing_slot", False):
        return "clothing"
    if getattr(db, "cloak_slot", False):
        return "cloak"
    if getattr(db, "kit_slot", False):
        return "kit"
    if getattr(db, "arrow_slot", False):
        return "arrows"
    if getattr(db, "bullet_slot", False):
        return "bullets"
    if getattr(db, "craft_source", None):
        return "consumable"
    return "misc"


def _target_slot(item):
    """Determine which equipment slot this item fits into."""
    db = item.db
    if getattr(db, "is_armor", False):
        return "body_slot"
    if getattr(db, "hand_slot", False):
        return "hand_slot"
    if getattr(db, "foot_slot", False):
        return "foot_slot"
    if getattr(db, "clothing_slot", False):
        return "clothing_slot"
    if getattr(db, "cloak_slot", False):
        return "cloak_slot"
    if getattr(db, "kit_slot", False):
        return "kit_slot"
    if getattr(db, "arrow_slot", False):
        return "arrow_slot"
    if getattr(db, "bullet_slot", False):
        return "bullet_slot"
    # Weapons/shields go to hand slots
    if getattr(db, "damage", 0) or getattr(db, "is_shield", False) or getattr(db, "is_bow", False):
        return "right_slot"
    return None


def _check_can_use(item, character):
    """Check if the character has the required skill to equip this item.

    Returns (can_use: bool, required_skill_label: str or None).
    Mirrors the skill check logic in CmdEquip.func().
    """
    try:
        from evennia.prototypes import prototypes as proto_module
        item_lower = item.key.lower().replace(" ", "_")
        try:
            prototype = proto_module.search_prototype(item_lower, require_single=True)
        except (KeyError, ValueError):
            return True, None  # no prototype found — allow equip

        prototype_data = prototype[0]
        item_data = prototype_data.get("attrs", [])

        idx = next((i for i, v in enumerate(item_data) if v[0] == "required_skill"), None)
        if idx is None:
            return True, None  # no skill requirement

        required_skill = item_data[idx][1]
        label = _SKILL_LABELS.get(required_skill, required_skill)
        has_skill = bool(getattr(character.db, required_skill, 0))
        return has_skill, label
    except Exception:
        return True, None  # on error, allow equip


def push_inventory(character, session=None):
    """Send an inventory_list OOB event.

    If session is provided, sends directly via session.msg(event=...) which
    bypasses character.msg() routing — more reliable from inputfunc context.
    Otherwise falls back to emit_to(character, ...) for backward compat.
    """
    if character is None:
        return

    db = character.db

    # Build set of currently equipped item ids.
    # Evennia 5.x db attribute reads may return copies of mutable values,
    # so we also cross-reference with character.contents to find items
    # that are physically in the character but match known equipment
    # patterns (have damage, is_armor, is_shield, etc.).
    equipped_map = {}  # item_id → slot_name

    # First pass: read from db slots directly
    for slot_name in _ALL_SLOTS:
        slot_val = character.attributes.get(slot_name, default=[])
        if not slot_val:
            continue
        slot_items = slot_val if isinstance(slot_val, (list, tuple)) else [slot_val]
        for it in slot_items:
            if hasattr(it, "id"):
                equipped_map[it.id] = slot_name

    try:
        from web.diag import diag_write
        diag_write(
            "push_inventory debug",
            equipped_map={k: v for k, v in equipped_map.items()},
            contents_count=len(list(character.contents)),
            contents_ids=[c.id for c in character.contents],
        )
    except Exception:
        pass

    # Build the inventory list
    items = []
    for item in character.contents:
        item_id = item.id
        idb = item.db
        equipped_slot = equipped_map.get(item_id)
        can_use, required_skill_label = _check_can_use(item, character)
        items.append({
            "id": item_id,
            "name": item.key,
            "desc": getattr(idb, "desc", "") or item.db.desc if hasattr(idb, "desc") else "",
            "type": _item_type(item),
            "targetSlot": _target_slot(item),
            "targetSlotLabel": _SLOT_LABELS.get(_target_slot(item), ""),
            "equipped": bool(equipped_slot),
            "equippedSlot": _SLOT_LABELS.get(equipped_slot, "") if equipped_slot else "",
            "damage": getattr(idb, "damage", 0) or 0,
            "materialValue": getattr(idb, "material_value", 0) or 0,
            "level": getattr(idb, "level", 0) or 0,
            "broken": bool(getattr(idb, "broken", False)),
            "twohanded": bool(getattr(idb, "twohanded", False)),
            "canUse": can_use,
            "requiredSkill": required_skill_label,
        })

    # Also send current slot occupancy so the UI can show what's equipped where
    slots = {}
    for slot_name, label in _SLOT_LABELS.items():
        slot_val = character.attributes.get(slot_name, default=[])
        if slot_val and isinstance(slot_val, (list, tuple)) and slot_val:
            first = slot_val[0]
            slots[slot_name] = {
                "label": label,
                "item": getattr(first, "key", str(first)),
                "itemId": getattr(first, "id", None),
            }
        else:
            slots[slot_name] = {"label": label, "item": None, "itemId": None}

    import time
    payload = {
        "type": "inventory_list",
        "_ts": time.time(),
        "items": items,
        "slots": slots,
    }
    if session:
        session.msg(event=payload)
    else:
        emit_to(character, "inventory_list", {
            "items": items,
            "slots": slots,
        })
