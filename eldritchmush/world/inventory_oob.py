"""
world/inventory_oob.py — Push structured inventory data to the web UI.

Call push_inventory(character) when the frontend requests an equip
screen. Sends an `inventory_list` OOB event containing every item
in the character's inventory with metadata about type, slot, and
current equipped status.
"""
from world.events import emit_to


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


def push_inventory(character):
    """Send an inventory_list OOB event to the character's web client."""
    if character is None:
        return

    db = character.db

    # Build set of currently equipped item ids
    equipped_map = {}  # item_id → slot_name
    for slot_name in _ALL_SLOTS:
        slot_val = getattr(db, slot_name, None)
        if not slot_val:
            continue
        items = slot_val if isinstance(slot_val, (list, tuple)) else [slot_val]
        for it in items:
            if hasattr(it, "id"):
                equipped_map[it.id] = slot_name

    # Build the inventory list
    items = []
    for item in character.contents:
        item_id = item.id
        idb = item.db
        equipped_slot = equipped_map.get(item_id)
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
        })

    # Also send current slot occupancy so the UI can show what's equipped where
    slots = {}
    for slot_name, label in _SLOT_LABELS.items():
        slot_val = getattr(db, slot_name, None)
        if slot_val and isinstance(slot_val, (list, tuple)) and slot_val:
            first = slot_val[0]
            slots[slot_name] = {
                "label": label,
                "item": getattr(first, "key", str(first)),
                "itemId": getattr(first, "id", None),
            }
        else:
            slots[slot_name] = {"label": label, "item": None, "itemId": None}

    emit_to(character, "inventory_list", {
        "items": items,
        "slots": slots,
    })
