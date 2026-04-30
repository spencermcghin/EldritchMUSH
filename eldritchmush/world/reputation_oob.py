"""
world/reputation_oob.py — Push faction + per-NPC reputation to the web UI.

Backs the ReputationModal. The companion sentinel `__rep_ui__` (handled
in server/conf/inputfuncs.py) calls push_reputation(session) on demand.
"""
import time


_FACTION_ORDER = ["crown", "cirque", "rangers", "crows", "outlaws", "outsider"]

_FACTION_BLURB = {
    "crown": "Loyalty to House Aenarion and the courts of Highcourt.",
    "cirque": "Standing among the Cirque's tribes and their kin.",
    "rangers": "Trust earned with the wardens of the wild road.",
    "crows": "Bargains struck with the murder beyond the veil.",
    "outlaws": "Word among the smugglers, fences, and scarred corners.",
    "outsider": "Reputation among wanderers, mercs, and walk-ins.",
}


def _label_for_score(score):
    """Adjective bucket — mirrors commands/reputation.py._rep_label
    but in plain text so the frontend can colour it independently."""
    if score >= 10:
        return "heroic"
    if score >= 5:
        return "friend"
    if score >= 1:
        return "known"
    if score == 0:
        return "stranger"
    if score >= -4:
        return "suspect"
    if score >= -9:
        return "enemy"
    return "marked"


def push_reputation(character, session=None):
    """Send a `reputation_data` OOB event."""
    if character is None:
        return

    faction_rep = character.db.faction_rep or {}
    npc_rep = character.db.npc_rep or {}

    factions = []
    for f in _FACTION_ORDER:
        score = int(faction_rep.get(f, 0) or 0)
        factions.append({
            "key": f,
            "name": f.title(),
            "score": score,
            "label": _label_for_score(score),
            "blurb": _FACTION_BLURB.get(f, ""),
        })

    npcs = []
    for npc_key, entry in (npc_rep or {}).items():
        if not entry:
            continue
        score = int(entry.get("rep", 0) or 0)
        memories = list(entry.get("memories") or [])
        npcs.append({
            "key": npc_key,
            "name": npc_key.title(),
            "score": score,
            "label": _label_for_score(score),
            "lastInteracted": entry.get("last_interacted") or "",
            "memories": memories,
        })
    # Most-charged relationships first (largest |rep| value bubbles up)
    npcs.sort(key=lambda n: abs(n["score"]), reverse=True)

    payload = {
        "type": "reputation_data",
        "_ts": time.time(),
        "factions": factions,
        "npcs": npcs,
    }

    try:
        if session is not None:
            session.msg(event=payload)
        else:
            character.msg(event=payload)
    except Exception:
        try:
            from web.diag import diag_write
            diag_write("push_reputation FAILED", char=repr(character))
        except Exception:
            pass
