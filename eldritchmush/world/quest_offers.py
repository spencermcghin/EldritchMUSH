"""
Quest offer OOB push.

When a character enters a room (or logs in), check whether any
available quests have givers standing in the room. If so, send a
quest_offer OOB event so the frontend can pop a parchment-styled
accept/reject modal. Players can still use `quest accept <title>`
manually — the modal is just a discoverability win.
"""
from world.quest_data import QUESTS


def _prereqs_met(char, qdef):
    quests = char.db.quests or {}
    for prereq in qdef.get("prereqs", []):
        st = quests.get(prereq)
        if not st or st.get("status") != "completed":
            return False
    return True


def _format_reward_parts(qdef):
    rewards = qdef.get("rewards", {}) or {}
    parts = []
    if rewards.get("silver"):
        parts.append(f"{rewards['silver']} silver")
    for proto_key in rewards.get("items", []) or []:
        parts.append(proto_key.replace("_", " ").lower())
    for reagent, qty in (rewards.get("reagents", {}) or {}).items():
        parts.append(f"{qty}x {reagent}")
    return parts


def push_quest_offers_for_room(char):
    """Emit a quest_offer event for each eligible quest the char can
    accept from an NPC present in their current room. Sends at most
    one event per check — if multiple quests are offered in the same
    room, frontend can stack / show one at a time.
    """
    if not char or not char.location:
        return
    if not char.sessions.count():
        return

    # Which NPC keys are in the room?
    room_keys = {
        obj.key.lower() for obj in char.location.contents
        if getattr(obj.db, "is_npc", False)
    }
    if not room_keys:
        return

    existing = char.db.quests or {}
    offers = []
    for key, qdef in QUESTS.items():
        if key in existing:
            continue  # already active, completed, or failed
        giver = (qdef.get("giver") or "").lower()
        if not giver or giver not in room_keys:
            continue
        if not _prereqs_met(char, qdef):
            continue
        offers.append({
            "key": qdef["key"],
            "title": qdef["title"],
            "giver": qdef["giver"],
            "description": qdef["description"],
            "objectives": [
                {"desc": o["desc"].split("(")[0].strip(), "qty": o["qty"]}
                for o in qdef["objectives"]
            ],
            "rewards": _format_reward_parts(qdef),
        })
    if not offers:
        return

    import time as _time
    payload = {
        "type": "quest_offer",
        "_ts": _time.time(),
        "offers": offers,
    }
    try:
        for sess in char.sessions.all():
            sess.msg(event=payload)
    except Exception:
        pass
