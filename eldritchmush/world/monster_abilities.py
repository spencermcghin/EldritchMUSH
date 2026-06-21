"""
world/monster_abilities.py — combat mechanics for bestiary ``db.special`` flags.

The bestiary prototypes (``world/bestiary_prototypes.py``) carry each monster's
special abilities as a list of NAME strings on ``db.special`` (e.g.
``immune_ranged``, ``lesser_regeneration``, ``target_fear_2``). Those strings
were previously data-only — see docs/bestiary-build.md §5.2. This module turns
the safe, well-defined ones into real combat mechanics.

Design rules (so existing combat is never altered for un-flagged NPCs/players):

* Every helper is **flag-gated**. An NPC whose ``db.special`` lacks a given
  flag returns the same answer as today (not immune, no regen, no fear).
* Players have no ``db.special`` list of these flags, so they are unaffected.
* Helpers are pure-ish and defensive: they tolerate ``None``/missing attrs and
  non-NPC objects, returning the inert default rather than raising.

Hook points (kept minimal & commented in the call sites):

* ``is_immune(target, maneuver)`` — called at the top of each combat maneuver
  command (strike/shoot/stun/stagger/disarm/sunder/cleave) to fizzle a
  maneuver the target is immune to, with a flavour message.
* ``apply_regen(npc)`` — called from ``Npc.take_combat_turn`` so a regenerating
  monster knits a little durability back each of its own turns.
* ``apply_fear(attacker, target, room)`` — called after a flagged monster lands
  a hit, setting the existing ``db.fear`` status on one target or the room.

Deferred flags (documented in docs/monster-abilities.md, NOT wired here):
    raise_dead, summon_necrophage, thrall, nether_ward, unhallowed_resurrection,
    killable_only_by_hallowed, paralyze_N, lycanthropic_infection,
    decomposition_x2, no_vitals, no_dexterity, and the pure-flavour names
    (music_of_the_dark_forest, staring_into_the_void, chill_of_the_grave,
    fresh_meat, dextrous, dexterous).
"""

# ---------------------------------------------------------------------------
# Flag tables
# ---------------------------------------------------------------------------

# Maneuver name -> the db.special flag that makes a target immune to it.
# These are the *status / control* maneuvers; raw-damage attacks (strike,
# cleave) are only blocked via immune_ranged (shoot) / immune_all (see below).
_MANEUVER_IMMUNITY = {
    "stun": "immune_stun",
    "stagger": "immune_stagger",
    "disarm": "immune_disarm",
    "sunder": "immune_sunder",
}

# Regeneration flags -> how much durability the monster knits back per turn.
# We heal the *tough* stat (the bestiary's chosen durability pool; see
# docs/bestiary-build.md "HP/body mapping decision") up to the monster's
# original tough, and also top body back toward total_body. Conservative
# amounts so regen is a grind-tax, not an invincibility wall.
_REGEN_AMOUNT = {
    "lesser_regeneration": 1,
    "lycan_regeneration": 2,
    "undead_resilience": 1,
}

# Fear flags -> (scope, magnitude). scope "target" = the struck target only;
# scope "room" = every player in the room. Magnitude is carried for future
# tuning (duration/severity); the current db.fear status is a boolean, so all
# magnitudes simply set the flag.
_FEAR_FLAGS = {
    "target_fear_1": ("target", 1),
    "target_fear_2": ("target", 2),
    "target_fear_3": ("target", 3),
    "mass_fear_1": ("room", 1),
    "mass_fear_2": ("room", 2),
    "sphere_of_terror": ("room", 3),
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _specials(obj):
    """Return the object's db.special list as a real list (never None)."""
    try:
        sp = obj.db.special
    except Exception:
        return []
    return list(sp) if sp else []


def has_flag(obj, flag):
    """True if `obj` carries `flag` in its db.special list."""
    return flag in _specials(obj)


# ---------------------------------------------------------------------------
# Immunities
# ---------------------------------------------------------------------------

def is_immune(target, maneuver):
    """Is `target` immune to combat action `maneuver`?

    `maneuver` is the command key: "strike", "shoot", "stun", "stagger",
    "disarm", "sunder", "cleave".

    Rules:
      * immune_all (Netherphage): immune to every *martial maneuver* — only
        raw damage that goes through AV applies. So strike/shoot/cleave still
        land (they are damage), but stun/stagger/disarm/sunder fizzle.
      * immune_ranged: shoot has no effect.
      * immune_<maneuver>: that specific control maneuver fizzles.

    Returns True if the maneuver should be blocked. Un-flagged targets and
    non-special objects always return False (today's behaviour).
    """
    flags = _specials(target)
    if not flags:
        return False

    # immune_ranged blocks the ranged attack entirely.
    if maneuver == "shoot" and "immune_ranged" in flags:
        return True

    # immune_all: martial maneuvers (the control verbs) fizzle. Raw-damage
    # verbs (strike/shoot/cleave) are NOT blocked here — they resolve through
    # AV as normal, which is the faithful "only damage via AV applies" rule.
    if "immune_all" in flags and maneuver in _MANEUVER_IMMUNITY:
        return True

    # Per-maneuver immunity.
    flag = _MANEUVER_IMMUNITY.get(maneuver)
    return bool(flag and flag in flags)


def immunity_message(target, maneuver):
    """Flavour line broadcast when `is_immune` blocks a maneuver."""
    name = getattr(target, "key", "the creature")
    flags = _specials(target)
    if maneuver == "shoot" and "immune_ranged" in flags:
        return (f"|MArrows and shot pass through |c{name}|M as though it "
                "were smoke — ranged attacks have no purchase here.|n")
    if "immune_all" in flags and maneuver in _MANEUVER_IMMUNITY:
        return (f"|M{name} cannot be {_past(maneuver)} — no maneuver finds "
                "a hold on it. Only raw force, ground through its armor, "
                "will do.|n")
    return (f"|M{name} shrugs off the attempt — it cannot be "
            f"{_past(maneuver)}.|n")


def _past(maneuver):
    """Crude past-participle for the fizzle message."""
    return {
        "stun": "stunned",
        "stagger": "staggered",
        "disarm": "disarmed",
        "sunder": "sundered",
        "shoot": "shot",
    }.get(maneuver, maneuver + "ed")


# ---------------------------------------------------------------------------
# Regeneration
# ---------------------------------------------------------------------------

def apply_regen(npc):
    """Heal a regenerating monster a little on its own combat turn.

    Called from ``Npc.take_combat_turn`` BEFORE it acts. No-op unless the NPC
    carries a regeneration flag. Heals tough back toward its starting value
    and tops body back toward total_body. Does nothing once the monster is
    already dying (bleed_points == 0) — being knocked out of the fight is the
    "killing condition" these regens respect; a downed monster does not knit
    itself back up mid-bleed-out.

    Returns the amount of tough restored (0 if none), for testability.
    """
    flags = _specials(npc)
    amount = 0
    for flag, value in _REGEN_AMOUNT.items():
        if flag in flags:
            amount = max(amount, value)
    if amount <= 0:
        return 0

    # Killing condition: a monster already bleeding out doesn't regenerate.
    try:
        if not npc.db.bleed_points:
            return 0
    except Exception:
        return 0

    healed = 0

    # Regen cap = the highest tough this monster has ever had (its origin
    # durability). We track the running maximum so a monster can never
    # regenerate above where it started, even across repeated sunders.
    # Tracking the max (rather than caching once) is robust to *when* this
    # first runs relative to the monster taking armor damage.
    try:
        cur = npc.db.tough or 0
        cap = npc.db.regen_tough_cap
        if cap is None or cur > cap:
            cap = cur
            npc.db.regen_tough_cap = cap
    except Exception:
        cap = npc.db.tough or 0

    try:
        cur_tough = npc.db.tough or 0
        if cur_tough < cap:
            new_tough = min(cap, cur_tough + amount)
            healed = new_tough - cur_tough
            npc.db.tough = new_tough
            # Keep displayed AV consistent with the restored natural armor.
            npc.db.av = (npc.db.av or 0) + healed
    except Exception:
        healed = 0

    # Top body back toward total_body with any leftover regen.
    try:
        leftover = amount - healed
        max_body = npc.db.total_body or npc.db.body or 0
        cur_body = npc.db.body or 0
        if leftover > 0 and cur_body < max_body:
            npc.db.body = min(max_body, cur_body + leftover)
    except Exception:
        pass

    if healed > 0 and npc.location:
        try:
            npc.location.msg_contents(
                f"|g{npc.key}'s wounds knit shut before your eyes "
                f"(+{healed} armor).|n"
            )
        except Exception:
            pass
    return healed


# ---------------------------------------------------------------------------
# Fear
# ---------------------------------------------------------------------------

def fear_scope(npc):
    """Return (scope, magnitude) for an NPC's strongest fear flag, or None.

    "room" beats "target"; higher magnitude wins within a scope.
    """
    best = None
    for flag in _specials(npc):
        spec = _FEAR_FLAGS.get(flag)
        if not spec:
            continue
        if best is None:
            best = spec
            continue
        scope, mag = spec
        b_scope, b_mag = best
        # room scope dominates; otherwise higher magnitude.
        if (scope == "room" and b_scope != "room") or (
                scope == b_scope and mag > b_mag):
            best = spec
    return best


def apply_fear(attacker, target, room=None):
    """Inflict the existing ``db.fear`` status if `attacker` carries a fear flag.

    Single-target flags fear only `target`; mass/sphere flags fear every
    player in the room. Reuses the same ``db.fear = True`` status that Rally
    (`commands/combat.py`) and healing (`commands/heal.py`) clear, so existing
    plumbing handles recovery. No-op for un-flagged attackers.

    Returns the list of characters newly feared (for testability).
    """
    spec = fear_scope(attacker)
    if not spec:
        return []
    scope, _mag = spec
    room = room or getattr(attacker, "location", None)

    feared = []
    if scope == "target":
        victims = [target] if target is not None else []
    else:  # room
        if not room:
            return []
        victims = [
            o for o in room.contents
            if getattr(o, "has_account", False) and o.has_account
            and o is not attacker
        ]

    for v in victims:
        if v is None:
            continue
        try:
            if not v.db.fear:
                v.db.fear = True
                feared.append(v)
                v.msg("|MA cold dread grips you — you are |rafraid|M. "
                      "(A |wrally|M from an ally can steady you.)|n")
        except Exception:
            continue

    if feared and room:
        try:
            room.msg_contents(
                f"|M{attacker.key} radiates terror.|n"
            )
        except Exception:
            pass
    return feared
