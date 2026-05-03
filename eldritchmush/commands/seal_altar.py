"""
Seals of Power puzzle — `place` command + OOB state events.

Players gather four broken seal fragments (each marked with an
Elder Futhark protection rune) scattered across the Thornwood and
Mystvale, then bring them to the rune altar in the ruined barn
beside the Field of Witching Fire. Each placement weakens the
Oblivion Coil protecting the nethermancer; when the fourth is set,
the Coil collapses and the boss fight begins.

The altar emits a `seal_altar_state` OOB event whenever the puzzle
state changes, driving the visual SealAltarModal on the web client.

Canon: Eldritch Monster Manual / Event 4 — Doom Comes to Mystvale.
"""
from evennia import Command
from world.events import emit_to


# Canon order — these four protection runes form the warding
# circle. Drawn from Elder Futhark / Telyrian (per Monster Manual:
# "language of death and the dead, but also of protection and
# sanctification"). Kept in canonical order so the altar fills the
# correct slot regardless of which fragment is placed first.
SEAL_RUNES = [
    {"name": "algiz",   "symbol": "ᛉ", "meaning": "warding"},     # ᛉ
    {"name": "tiwaz",   "symbol": "ᛏ", "meaning": "binding"},     # ᛏ
    {"name": "eihwaz",  "symbol": "ᛇ", "meaning": "yew-gate"},    # ᛇ
    {"name": "ingwaz",  "symbol": "ᛜ", "meaning": "sealing"},     # ᛜ
]


def _carried_rune_names(character):
    """Return lowercase rune names the character is carrying."""
    if not character:
        return set()
    carried = set()
    try:
        for obj in character.contents:
            if obj.attributes.get("is_seal_fragment", default=False):
                name = (obj.attributes.get("rune_name", default="") or "").lower()
                if name:
                    carried.add(name)
    except Exception:
        pass
    return carried


def _altar_state_payload(altar, character=None):
    """Build the SealAltarModal payload describing current state."""
    placed_names = list(altar.db.placed_runes or [])
    carried = _carried_rune_names(character)
    slots = []
    for rune in SEAL_RUNES:
        is_filled = rune["name"] in placed_names
        slots.append({
            "name": rune["name"],
            "symbol": rune["symbol"],
            "meaning": rune["meaning"],
            "filled": is_filled,
            "carried": rune["name"] in carried,
        })
    return {
        "room": altar.location.key if altar.location else "",
        "slots": slots,
        "placed": len(placed_names),
        "total": len(SEAL_RUNES),
        "complete": len(placed_names) >= len(SEAL_RUNES),
    }


def emit_altar_state(altar, character=None):
    """Push the current altar state to one player (or all players in
    the altar's room if `character` is None)."""
    if not altar or not altar.location:
        return
    if character is not None:
        targets = [character]
    else:
        targets = [
            obj for obj in altar.location.contents
            if hasattr(obj, "has_account") and obj.has_account
        ]
    for char in targets:
        try:
            payload = _altar_state_payload(altar, character=char)
            emit_to(char, "seal_altar_state", payload)
        except Exception as exc:
            print(f"[seal_altar] emit_to failed: {exc!r}", flush=True)


class CmdPlaceSeal(Command):
    """
    Place a broken seal fragment on the rune altar.

    Usage:
      place <fragment>
      place <fragment> on altar

    Each placement weakens the Oblivion Coil shielding the
    nethermancer in the field beyond. When all four seals are
    set, the Coil collapses.
    """
    key = "place"
    aliases = ["set", "lay"]
    locks = "cmd:all()"
    help_category = "Combat"

    def func(self):
        caller = self.caller
        room = caller.location
        if not room:
            return

        # Find the altar in this room — there should be exactly one.
        altar = None
        for obj in room.contents:
            if obj.attributes.get("is_seal_altar", default=False):
                altar = obj
                break
        if not altar:
            caller.msg("There is no altar here to place anything on.")
            return

        args = (self.args or "").strip()
        # Strip the "on altar" / "at altar" / "on the altar" suffix.
        for tail in (" on the altar", " on altar", " at the altar",
                     " at altar", " on the rune altar", " at the rune altar"):
            if args.lower().endswith(tail):
                args = args[: -len(tail)].strip()
                break
        if not args:
            caller.msg(
                "Place what? You'll need a |wbroken seal|n fragment "
                "from somewhere in the Thornwood."
            )
            return

        # Look in the caller's inventory only — the fragment must be
        # carried, not scenery in the room.
        fragment = caller.search(
            args, location=caller, quiet=True,
        )
        if isinstance(fragment, list):
            fragment = fragment[0] if fragment else None
        if not fragment:
            caller.msg(
                f"You aren't carrying any '{args}'. The seal fragments "
                "are scattered through the Thornwood and Mystvale."
            )
            return
        if not fragment.attributes.get("is_seal_fragment", default=False):
            caller.msg(
                f"{fragment.key} is not one of the broken seals. "
                "The altar would not accept it."
            )
            return

        placed_runes = list(altar.db.placed_runes or [])
        target_room = altar.db.coil_target_room
        rune_name = (fragment.attributes.get("rune_name", default="") or "").lower()
        rune_symbol = fragment.attributes.get("rune_symbol", default="?")

        if rune_name in placed_runes:
            caller.msg(
                f"The {rune_name} rune is already set upon the altar. "
                "Find the others."
            )
            return
        if len(placed_runes) >= len(SEAL_RUNES):
            caller.msg(
                "All four seals have already been set. The Coil "
                "has fallen; the nethermancer is exposed."
            )
            return

        # Consume the fragment.
        fragment.delete()
        placed_runes.append(rune_name)
        altar.db.placed_runes = placed_runes
        # Backwards-compat counter (older code paths read seals_placed).
        altar.db.seals_placed = len(placed_runes)

        seals_left = len(SEAL_RUNES) - len(placed_runes)
        room.msg_contents(
            f"|y{caller.key} sets the |w{rune_symbol}|y rune ({rune_name}) "
            f"upon the altar. The lines flare amethyst, then settle. "
            f"({len(placed_runes)}/{len(SEAL_RUNES)} placed.)|n"
        )

        # Push fresh visual state to the modal.
        emit_altar_state(altar)

        if len(placed_runes) >= len(SEAL_RUNES):
            room.msg_contents(
                "|MA shudder runs through the air. From the field beyond, "
                "a sound like cracking ice — the amethyst barrier shatters "
                "and falls.|n"
            )
            if target_room:
                _drop_oblivion_coil(target_room)
        else:
            room.msg_contents(
                f"|x({seals_left} seal{'s' if seals_left != 1 else ''} "
                f"remain.)|n"
            )


def _drop_oblivion_coil(target_room):
    """Disable the Oblivion Coil on every NPC in the target room and
    broadcast the collapse to anyone present."""
    if not target_room:
        return
    for obj in target_room.contents:
        if obj.attributes.get("oblivion_coil_active", default=False):
            obj.db.oblivion_coil_active = False
    target_room.msg_contents(
        "|MThe amethyst circles ringing the field flicker once and "
        "die. The shimmering barrier falls. The nethermancer turns, "
        "and for the first time looks up from the tome.|n"
    )
