"""
world/quest_journal_oob.py — Push structured quest journal data to the web UI.

The journal modal shows three sections (active, available-here, completed)
with click-to-track / click-to-abandon actions per row. The companion
sentinel `__quest_ui__` (handled in server/conf/inputfuncs.py) calls
push_quest_journal(session) on demand from the modal mount.
"""
import time

from world.quest_data import QUESTS


def _objectives_payload(state_objectives):
    """Convert in-progress state objectives into UI-ready dicts."""
    out = []
    for obj in state_objectives or []:
        desc = obj.get("desc", "") or ""
        # Strip trailing parenthetical hints like "(0/3)" — UI renders its own count.
        short = desc.split("(")[0].strip()
        out.append({
            "desc": short,
            "current": int(obj.get("current", 0) or 0),
            "qty": int(obj.get("qty", 0) or 0),
            "done": int(obj.get("current", 0) or 0) >= int(obj.get("qty", 0) or 0),
        })
    return out


def _outcome_objectives_payload(qdef, outcome_key):
    """For not-yet-accepted branching quests, surface each branch's objectives."""
    odef = (qdef.get("outcomes") or {}).get(outcome_key) or {}
    return [
        {
            "desc": (o.get("desc", "") or "").split("(")[0].strip(),
            "current": 0,
            "qty": int(o.get("qty", 0) or 0),
            "done": False,
        }
        for o in odef.get("objectives", [])
    ]


def _rewards_payload(qdef, outcome_key=None):
    """Flatten rewards (items / silver / reagents) into a single list of strings."""
    if outcome_key:
        odef = (qdef.get("outcomes") or {}).get(outcome_key) or {}
        rewards = odef.get("rewards") or {}
    else:
        rewards = qdef.get("rewards") or {}
    parts = []
    silver = rewards.get("silver", 0)
    if silver:
        parts.append(f"{silver} silver")
    for item_key in rewards.get("items", []) or []:
        parts.append(item_key.replace("_", " ").lower())
    for reagent, qty in (rewards.get("reagents") or {}).items():
        parts.append(f"{qty}x {reagent}")
    return parts


def push_quest_journal(character, session=None):
    """Send a `quest_log` OOB event with active / available / completed quests.

    Each entry carries enough context for the UI to render objectives,
    rewards, and an Abandon button — without needing a follow-up text
    fetch. Call from the `__quest_ui__` sentinel handler.
    """
    if character is None:
        return

    quests = character.db.quests or {}

    active = []
    completed = []
    for key, state in quests.items():
        qdef = QUESTS.get(key)
        if not qdef:
            continue
        outcome_key = state.get("outcome")
        outcome_label = ""
        if outcome_key:
            odef = (qdef.get("outcomes") or {}).get(outcome_key) or {}
            outcome_label = odef.get("label", outcome_key)
        entry = {
            "key": key,
            "title": qdef.get("title", key),
            "giver": qdef.get("giver", ""),
            "description": qdef.get("description", ""),
            "outcomeKey": outcome_key,
            "outcomeLabel": outcome_label,
            "objectives": _objectives_payload(state.get("objectives")),
            "rewards": _rewards_payload(qdef, outcome_key),
        }
        if state.get("status") == "active":
            active.append(entry)
        elif state.get("status") == "completed":
            completed.append(entry)

    # "Available here" — quest givers in the current room with quests
    # the player hasn't started. We surface this so the UI can show a
    # one-click accept button right inside the journal modal.
    available_here = []
    if character.location:
        room_npc_keys = {
            (getattr(o.db, "is_npc", False) and (o.key or "").lower()) or None
            for o in character.location.contents
        }
        room_npc_keys.discard(None)
        room_npc_keys.discard("")
        for key, qdef in QUESTS.items():
            if key in quests:
                continue
            giver = (qdef.get("giver") or "").lower()
            if giver and giver in room_npc_keys:
                # If branching, surface each outcome as its own pickable row
                # so the player can pick a path right inside the journal.
                outcomes = qdef.get("outcomes") or {}
                if outcomes:
                    for okey, odef in outcomes.items():
                        available_here.append({
                            "key": key,
                            "title": qdef.get("title", key),
                            "giver": qdef.get("giver", ""),
                            "description": qdef.get("description", ""),
                            "outcomeKey": okey,
                            "outcomeLabel": odef.get("label", okey),
                            "outcomeDescription": odef.get("description", ""),
                            "objectives": _outcome_objectives_payload(qdef, okey),
                            "rewards": _rewards_payload(qdef, okey),
                        })
                else:
                    available_here.append({
                        "key": key,
                        "title": qdef.get("title", key),
                        "giver": qdef.get("giver", ""),
                        "description": qdef.get("description", ""),
                        "outcomeKey": None,
                        "outcomeLabel": "",
                        "outcomeDescription": "",
                        "objectives": [
                            {
                                "desc": (o.get("desc", "") or "").split("(")[0].strip(),
                                "current": 0,
                                "qty": int(o.get("qty", 0) or 0),
                                "done": False,
                            }
                            for o in qdef.get("objectives", [])
                        ],
                        "rewards": _rewards_payload(qdef),
                    })

    payload = {
        "type": "quest_log",
        "_ts": time.time(),
        "active": active,
        "availableHere": available_here,
        "completed": completed,
    }

    try:
        if session is not None:
            session.msg(event=payload)
        else:
            character.msg(event=payload)
    except Exception:
        try:
            from web.diag import diag_write
            diag_write("push_quest_journal FAILED", char=repr(character))
        except Exception:
            pass
