"""
Equip-bonus helper — apply and remove item stat bonuses on equip/unequip.

Each prototype in world/prototypes.py may carry an `equip_bonus` dict
mapping character db-stat name to delta:

    LIGHT_BOOTS = {
        ...,
        "equip_bonus": {"resist": 1},
    }

When the player equips the item, those deltas are added to the
character's matching db attributes. The applied modifiers are recorded
on the character (db.equip_modifiers[item_id]) so unequip can reverse
exactly what was applied — even if the item was changed between
equip and unequip.

Usage in the equip command:
    from world import equip_bonuses
    equip_bonuses.apply(character, item)

In the unequip command:
    equip_bonuses.remove(character, item)

The functions are idempotent and silent on items without bonuses.
Push character_stats after to refresh the UI.
"""


# Stat names that exist as db attributes on Character. Anything not in
# this set is rejected to prevent typos from creating mystery attrs.
KNOWN_STATS = {
    "av", "resist", "tough", "weakness",
    "stagger", "stun", "sunder", "disarm", "cleave",
    "espionage", "influence",
    "shield", "shield_value", "weapon_level",
    "material_value",
    # Skills (rare equip-bonuses to skills, but legal):
    "melee", "melee_weapons", "archer", "shields", "gunner",
    "armor_proficiency", "armor_specialist", "master_of_arms",
    "stabilize", "medicine", "battlefieldmedicine", "chirurgeon",
    "perception", "tracking",
}


def _ensure_modifier_store(character):
    """Lazily initialize the character's equip-modifier ledger."""
    store = character.attributes.get("equip_modifiers", default=None)
    if store is None:
        store = {}
        character.attributes.add("equip_modifiers", store)
    # Always return a plain dict (not _SaverDict) for safe mutation.
    return dict(store)


def _save_modifiers(character, store):
    character.attributes.add("equip_modifiers", store)


_SLOT_NAMES = (
    "right_slot", "left_slot", "body_slot",
    "hand_slot", "foot_slot",
    "clothing_slot", "cloak_slot",
    "kit_slot", "arrow_slot", "bullet_slot",
)


def _is_equipped(character, item):
    """True if the item is currently held in any of character's slots."""
    for slot in _SLOT_NAMES:
        contents = getattr(character.db, slot, None) or []
        if item in contents:
            return True
    return False


def apply(character, item):
    """Apply the item's equip_bonus dict to the character.

    Safe to call from CmdEquip's success path — verifies the item is
    actually in one of the character's slots before applying. If the
    item has no bonus or isn't equipped, this is a no-op.

    Records the applied deltas under character.db.equip_modifiers[item.id]
    so they can be reversed exactly on unequip. Returns the dict of
    applied stats (or empty dict if nothing was applied).
    """
    if not character or not item:
        return {}
    bonus = item.db.equip_bonus
    if not bonus:
        return {}
    if not _is_equipped(character, item):
        return {}

    store = _ensure_modifier_store(character)
    item_key = str(item.id)

    # If somehow already applied, remove first so we don't double-stack.
    if item_key in store:
        _undo(character, store[item_key])
        del store[item_key]

    applied = {}
    for stat, delta in dict(bonus).items():
        if stat not in KNOWN_STATS:
            continue
        try:
            d = int(delta)
        except (TypeError, ValueError):
            continue
        if d == 0:
            continue
        cur = getattr(character.db, stat, 0) or 0
        try:
            cur = int(cur)
        except (TypeError, ValueError):
            cur = 0
        setattr(character.db, stat, cur + d)
        applied[stat] = d

    if applied:
        store[item_key] = applied
        _save_modifiers(character, store)
    return applied


def remove(character, item):
    """Reverse the deltas previously applied for this item.

    Returns the dict of stats reversed, or empty dict if nothing was
    on record. Tolerates double-removal (no-op the second time).
    """
    if not character or not item:
        return {}
    store = _ensure_modifier_store(character)
    item_key = str(item.id)
    applied = store.get(item_key)
    if not applied:
        return {}
    reversed_ = _undo(character, applied)
    del store[item_key]
    _save_modifiers(character, store)
    return reversed_


def _undo(character, applied):
    """Subtract previously-applied deltas from the character's stats."""
    out = {}
    for stat, delta in dict(applied).items():
        if stat not in KNOWN_STATS:
            continue
        try:
            d = int(delta)
        except (TypeError, ValueError):
            continue
        cur = getattr(character.db, stat, 0) or 0
        try:
            cur = int(cur)
        except (TypeError, ValueError):
            cur = 0
        setattr(character.db, stat, cur - d)
        out[stat] = d
    return out


def summary_for(character):
    """Return a copy of the character's current equip-modifier ledger.

    Useful for the character sheet / debug display.
    """
    store = character.attributes.get("equip_modifiers", default=None) or {}
    return {k: dict(v) for k, v in dict(store).items()}
