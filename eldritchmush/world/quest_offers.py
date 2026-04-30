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
        if isinstance(prereq, dict):
            q_key = prereq["quest"]
            want_outcome = prereq.get("outcome")
            st = quests.get(q_key)
            if not st or st.get("status") != "completed":
                return False
            if want_outcome and st.get("outcome") != want_outcome:
                return False
        else:
            st = quests.get(prereq)
            if not st or st.get("status") != "completed":
                return False
    return True


def _format_reward_parts(rewards):
    """Format a rewards dict into a list of short human-readable strings."""
    rewards = rewards or {}
    parts = []
    if rewards.get("silver"):
        parts.append(f"{rewards['silver']} silver")
    for proto_key in rewards.get("items", []) or []:
        parts.append(proto_key.replace("_", " ").lower())
    for reagent, qty in (rewards.get("reagents", {}) or {}).items():
        parts.append(f"{qty}x {reagent}")
    return parts


def _format_objectives(objectives):
    return [
        {"desc": o["desc"].split("(")[0].strip(), "qty": o["qty"]}
        for o in (objectives or [])
    ]


def push_quest_offers_for_room(char):
    """Emit a quest_offer event for each eligible quest the char can
    accept from an NPC present in their current room. Sends at most
    one event per check — if multiple quests are offered in the same
    room, frontend can stack / show one at a time.

    Note: as of 2026-04-30 the room-entry auto-trigger was removed in
    favor of fire-on-ask via push_quest_offers_for_npc — popping the
    modal the moment a player walks into a room felt overbearing.
    This function remains for any future flow that wants the broad
    "all offers from NPCs in this room" behavior (e.g. a "look for
    work" command or an admin tool).
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

        offer = {
            "key": qdef["key"],
            "title": qdef["title"],
            "giver": qdef["giver"],
            "description": qdef["description"],
        }
        if qdef.get("outcomes"):
            # Branching quest — surface each outcome so the modal can
            # render picker buttons. The modal sends
            # `quest accept <title> / <outcome_key>` when one is chosen.
            offer["outcomes"] = [
                {
                    "key": okey,
                    "label": odef.get("label", okey),
                    "description": odef.get("description", ""),
                    "objectives": _format_objectives(odef.get("objectives", [])),
                    "rewards": _format_reward_parts(odef.get("rewards", {})),
                    "factionRep": odef.get("faction_rep", {}),
                }
                for okey, odef in qdef["outcomes"].items()
            ]
        else:
            offer["objectives"] = _format_objectives(qdef.get("objectives", []))
            offer["rewards"] = _format_reward_parts(qdef.get("rewards", {}))
        offers.append(offer)
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


def push_quest_offers_for_npc(char, npc):
    """Emit a quest_offer event for each eligible quest the char can
    accept from a SPECIFIC npc. Used by CmdAsk so quest offers fire
    when the player engages an NPC in conversation, rather than on
    every room entry.

    No-op if the NPC has no quests to offer that the char hasn't
    already started (or that they don't yet meet the prereqs for).
    """
    if not char or not npc:
        return
    if not char.sessions.count():
        return

    npc_key = (getattr(npc, "key", "") or "").lower()
    if not npc_key:
        return

    existing = char.db.quests or {}
    offers = []
    for key, qdef in QUESTS.items():
        if key in existing:
            continue
        giver = (qdef.get("giver") or "").lower()
        if not giver or giver != npc_key:
            continue
        if not _prereqs_met(char, qdef):
            continue

        offer = {
            "key": qdef["key"],
            "title": qdef["title"],
            "giver": qdef["giver"],
            "description": qdef["description"],
        }
        if qdef.get("outcomes"):
            offer["outcomes"] = [
                {
                    "key": okey,
                    "label": odef.get("label", okey),
                    "description": odef.get("description", ""),
                    "objectives": _format_objectives(odef.get("objectives", [])),
                    "rewards": _format_reward_parts(odef.get("rewards", {})),
                    "factionRep": odef.get("faction_rep", {}),
                }
                for okey, odef in qdef["outcomes"].items()
            ]
        else:
            offer["objectives"] = _format_objectives(qdef.get("objectives", []))
            offer["rewards"] = _format_reward_parts(qdef.get("rewards", {}))
        offers.append(offer)
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
