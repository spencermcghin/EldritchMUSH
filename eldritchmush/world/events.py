"""
world/events.py — Structured JSON event emitter for the EldritchMUSH web UI.

Usage
-----
Import and call emit() anywhere in the combat/game logic:

    from world.events import emit

    emit(room, "combat_hit", {
        "attacker": attacker.key,
        "target": target.key,
        "damage": 2,
        "location": "torso",
        "weapon": weapon.key if weapon else "fists",
    })

The call simultaneously:
  1. Does nothing extra for MUD-protocol (telnet) clients — they get text via
     the normal msg_contents() calls that already exist throughout the codebase.
  2. Sends a JSON OOB frame to every *web* client currently in the room so the
     UI can update panels, animations, health bars, etc. without parsing text.

OOB wire format (Evennia webclient):
    ["event", [], {"type": "combat_hit", "attacker": ..., ...}]

Frontend receives it via:
    Evennia.emitter.on("event", function(args, kwargs) {
        const data = kwargs;
        if (data.type === "combat_hit") { ... }
    });

Event types catalogue
---------------------
combat_start        room, combatants (list of names), turn_order (list)
combat_end          room
turn_change         character (name of whose turn it now is)
combat_hit          attacker, target, damage, location, weapon
combat_miss         attacker, target, reason (e.g. "blocked", "missed")
combat_stun         attacker, target
combat_disarm       attacker, target
combat_stagger      attacker, target
combat_cleave       attacker, targets (list)
combat_sunder       attacker, target, item_sundered
combat_skip         character
combat_disengage    character
character_bleed     character (entered bleeding state)
character_dying     character (entered dying state)
character_dead      character
heal                healer, target, amount, new_bleed, new_body
available_commands  character, commands (list of {key, label, args_hint})

All events also carry:
    _ts     Unix timestamp (float, seconds)
    _room   Room dbref string (#nn)
"""

import time


def _send_event(target, payload):
    """Wire-format helper.

    The Evennia webclient protocol dispatches output by *kwarg name* on
    msg(), looking up `send_<key>` on the portal session. There is no
    `send_oob` handler anywhere in Evennia, so calls like
    `obj.msg(oob=(...))` fall through to `send_default("oob", ...)` and
    hit the wire as `["oob", ...]` — which the React frontend doesn't
    recognize as a structured event.

    The correct call is `obj.msg(event=<dict>)`. clean_senddata
    normalizes that to `[[], dict]`, the portal calls
    `send_default("event", **dict)`, and the wire format becomes
    `["event", [], dict]` — which the frontend's `cmd === 'event'`
    branch picks up and dispatches by `kwargs.type`.
    """
    try:
        target.msg(event=payload)
    except Exception:
        pass  # never crash game logic over a UI notification


def emit(room, event_type, data=None):
    """Send a structured JSON OOB event to all web-connected players in *room*.

    Parameters
    ----------
    room : Room
        The Evennia Room object whose occupants should receive the event.
    event_type : str
        One of the event type strings listed in the module docstring.
    data : dict or None
        Arbitrary payload merged into the OOB frame along with the standard
        fields (_ts, _room, type).
    """
    if data is None:
        data = {}

    payload = {
        "type": event_type,
        "_ts": time.time(),
        "_room": room.dbref if room else None,
    }
    payload.update(data)

    for obj in room.contents:
        # Only send OOB to objects that have an active web session.
        # has_account covers both Characters and NPCs that happen to be
        # puppeted; NPCs without accounts are silently skipped.
        if hasattr(obj, "has_account") and obj.has_account:
            _send_event(obj, payload)


def emit_to(character, event_type, data=None):
    """Send a structured JSON OOB event to a single character (private).

    Useful for events only the recipient should see, e.g. available_commands.
    """
    if data is None:
        data = {}

    payload = {
        "type": event_type,
        "_ts": time.time(),
    }
    payload.update(data)

    if hasattr(character, "has_account") and character.has_account:
        _send_event(character, payload)
