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


# ---------------------------------------------------------------------------
# Armor durability
# ---------------------------------------------------------------------------
# Combat subtracts absorbed damage from the *character's* db.armor pool
# (Combatant.takeArmorDamage -> alternateDamage("armor")), while equip used
# to reset that pool to the item's pristine db.material_value. Unequipping
# and re-equipping the same breastplate therefore refilled it for free, with
# no turn cost and no in-combat check — repeatable every round.
#
# These helpers keep the worn-down state on the item itself, in
# db.armor_remaining, so the pool a player gets back is whatever their armor
# had left. Repair restores it (see reset_armor).

def _int(value, default=0):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _is_armor(item):
    idb = getattr(item, "db", None)
    return bool(idb is not None and getattr(idb, "is_armor", False))


def current_armor_value(item):
    """Absorption this armor piece has left, never above its material_value.

    Falls back to the item's material_value for armor that predates
    armor_remaining, so existing gear keeps working unchanged.
    """
    if not item or not getattr(item, "db", None):
        return 0

    full = max(0, _int(getattr(item.db, "material_value", 0)))
    remaining = item.attributes.get("armor_remaining", default=None)
    if remaining is None:
        return full
    return max(0, min(full, _int(remaining)))


def store_armor_value(item, value):
    """Persist an armor pool back onto the item, capped at material_value.

    The cap means indomitable (or anything else above the piece's own
    material_value) is never banked on the item. That also covers legacy
    characters whose db.armor already had indomitable folded in.
    """
    if not item or not getattr(item, "db", None):
        return
    full = max(0, _int(getattr(item.db, "material_value", 0)))
    value = max(0, min(full, _int(value)))
    item.attributes.add("armor_remaining", value)


def recompute_av(character):
    """Set and return db.av from the absorbable pools.

    AV = armor + tough + armor_specialist. Indomitable is not a separate
    term: while armor is worn it is folded into db.armor (see don_armor),
    so it absorbs hits and drains with the armor, and it does nothing with
    no armor on. Every equip/unequip path (text, web, give, sell, drop)
    and Combatant.updateAv go through here so AV never depends on which
    client was used.
    """
    cdb = character.db
    armor = _int(getattr(cdb, "armor", 0))
    tough = _int(getattr(cdb, "tough", 0))
    armor_specialist = 1 if getattr(cdb, "armor_specialist", 0) else 0
    av = armor + tough + armor_specialist
    cdb.av = av
    return av


def don_armor(character, item):
    """Load the character's armor pool from `item` as it goes on.

    The pool is whatever absorption the piece has left plus the wearer's
    indomitable, which only applies while the armor still has absorption
    (the pre-durability rule was "only if material_value > 0"). The amount
    of indomitable added is recorded so doff_armor can bank only the
    piece's own share.
    """
    remaining = current_armor_value(item)
    indomitable = _int(getattr(character.db, "indomitable", 0)) if remaining > 0 else 0
    character.db.armor = remaining + indomitable
    character.db.armor_indomitable = indomitable
    return recompute_av(character)


def worn_armor_remaining(character, item):
    """What `item` has left right now, reading the live pool if it is worn."""
    if character is not None and is_equipped(character, item):
        pool = _int(getattr(character.db, "armor", 0))
        indomitable = _int(getattr(character.db, "armor_indomitable", 0))
        full = max(0, _int(getattr(item.db, "material_value", 0)))
        return max(0, min(full, pool - indomitable))
    return current_armor_value(item)


def doff_armor(character, item):
    """Bank the pool back onto `item` and clear it from the character.

    Hits drain the piece's own share first; the indomitable share is what
    is left last. So the item keeps pool - indomitable, capped at its
    material_value. Re-equipping then gives back exactly what was banked
    plus indomitable (if anything is left), never a free refill.
    """
    pool = _int(getattr(character.db, "armor", 0))
    indomitable = _int(getattr(character.db, "armor_indomitable", 0))
    store_armor_value(item, pool - indomitable)
    character.db.armor = 0
    character.db.armor_indomitable = 0
    return recompute_av(character)


def reset_armor(item, wearer=None):
    """Restore an armor piece to full absorption (repair and patch kit).

    Only armor is touched: repairing a sword or shield must not write
    armor_remaining or the wearer's pool. Pass `wearer` when the piece may
    currently be worn, so the live pool is refreshed too.
    """
    if not item or not getattr(item, "db", None) or not _is_armor(item):
        return

    full = max(0, _int(getattr(item.db, "material_value", 0)))
    item.attributes.add("armor_remaining", full)

    if wearer is not None and is_equipped(wearer, item):
        don_armor(wearer, item)


# ---------------------------------------------------------------------------
# Force-unequip
# ---------------------------------------------------------------------------
# Selling, giving or dropping an item never went through the unequip path, so
# a worn breastplate could leave the character's inventory with its AV still
# applied and a stale reference sitting in db.body_slot. The recipient could
# then equip the same piece for a second copy of the bonus, while the original
# owner kept theirs and could no longer unequip (the search is scoped to their
# own inventory, and the item is gone).
#
# Call this before any transfer that removes an item from a character.

SLOT_NAMES = (
    "right_slot", "left_slot", "body_slot", "hand_slot", "foot_slot",
    "clothing_slot", "cloak_slot", "kit_slot", "arrow_slot", "bullet_slot",
)


def is_equipped(character, item):
    """True if `item` currently occupies any of the character's slots."""
    if character is None or item is None:
        return False
    for slot in SLOT_NAMES:
        contents = character.attributes.get(slot, default=None)
        if contents and item in contents:
            return True
    return False


def force_unequip(character, item):
    """Remove `item` from every slot and reverse the stats it granted.

    Safe to call on an item that is not equipped (returns False). Returns
    True if the item was removed from at least one slot.
    """
    if character is None or item is None:
        return False

    removed = False
    for slot in SLOT_NAMES:
        contents = character.attributes.get(slot, default=None)
        if not contents or item not in contents:
            continue
        while item in contents:
            contents.remove(item)
        removed = True

    if not removed:
        return False

    idb = getattr(item, "db", None)

    # Weapon bonus is derived from whatever is left in hand.
    if idb is not None and (getattr(idb, "damage", 0) or getattr(idb, "twohanded", False)):
        character.db.weapon_level = 0

    # Armor: bank remaining absorption on the piece, then clear the pool.
    if _is_armor(item):
        doff_armor(character, item)

    # Gloves / boots carry a flat resist that the equip path added directly.
    if idb is not None and getattr(idb, "resist", 0):
        current = getattr(character.db, "resist", 0) or 0
        character.db.resist = max(0, current - (getattr(idb, "resist", 0) or 0))

    # Clothing / cloak influence and espionage, same pattern.
    if idb is not None and getattr(idb, "influential", 0):
        current = getattr(character.db, "influential", 0) or 0
        character.db.influential = max(0, current - (getattr(idb, "influential", 0) or 0))
    if idb is not None and getattr(idb, "espionage", 0):
        current = getattr(character.db, "espionage", 0) or 0
        character.db.espionage = max(0, current - (getattr(idb, "espionage", 0) or 0))

    # Reverse any prototype-declared equip_bonus deltas.
    try:
        remove(character, item)
    except Exception:
        pass

    # Recompute armor value from what is still worn.
    try:
        recompute_av(character)
    except Exception:
        pass

    return True


def release_from_holder(item, notify=True):
    """Force-unequip `item` from whoever holds it, if it is equipped.

    Used by the leave/delete hooks so any path that takes an equipped item
    away (stock drop, put, quest sweeps, item.delete()) reverses its stats.
    Explicit force_unequip calls made earlier in give/sell leave nothing
    in the slots, so this is a no-op for them and nothing is reversed twice.
    """
    holder = getattr(item, "location", None)
    if holder is None or not is_equipped(holder, item):
        return False
    if not force_unequip(holder, item):
        return False
    if notify:
        try:
            holder.msg(f"|430You are no longer using {item.key}.|n")
        except Exception:
            pass
    try:
        from world.character_stats import push_character_stats
        push_character_stats(holder)
    except Exception:
        pass
    return True
