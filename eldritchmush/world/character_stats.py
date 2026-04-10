"""
world/character_stats.py — Push character vitals to the web UI sidebar.

Call push_character_stats(character) any time the character's body / armor /
status changes (combat hits, healing, equipment changes, login).
"""
from world.events import emit_to


def push_character_stats(character):
    """Send a character_stats OOB event with the character's current vitals."""
    if character is None:
        return
    db = character.db

    # Equipment slots store either an object or [name] list — extract names
    def slot_name(slot):
        val = getattr(db, slot, None)
        if not val:
            return None
        if isinstance(val, (list, tuple)):
            if not val:
                return None
            first = val[0]
            return getattr(first, "key", None) or str(first)
        return getattr(val, "key", None) or str(val)

    payload = {
        "character": character.key,
        "body": getattr(db, "body", None),
        "total_body": getattr(db, "total_body", None),
        "bleed_points": getattr(db, "bleed_points", None),
        "death_points": getattr(db, "death_points", None),
        "av": getattr(db, "av", 0) or 0,
        "status": {
            "bleeding": bool(getattr(db, "bleeding", False)),
            "dying": bool(getattr(db, "dying", False)),
            "unconscious": bool(getattr(db, "sleep", False)),
        },
        "equipment": {
            "rightHand": slot_name("right_slot"),
            "leftHand": slot_name("left_slot"),
            "body": slot_name("body_slot"),
        },
    }
    emit_to(character, "character_stats", payload)
