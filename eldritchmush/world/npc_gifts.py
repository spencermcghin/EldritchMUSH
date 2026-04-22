"""
NPC gift validation.

When an AI NPC claims to hand the player something — via a structured
marker in its LLM output, e.g. "[GIVE: WOLF_PELT]" — parse the marker,
verify it against the NPC's allow-list, spawn the prototype into the
recipient's inventory, and fire an `item_received` OOB event so the
frontend can toast the transfer. If the NPC has no allow-list or the
marker doesn't match, the marker is stripped but no item is given
(keeps the LLM honest even when it hallucinates generosity).

Usage
-----
Call `process_gift_markers(reply, npc, recipient)` with the raw LLM
text; it returns the cleaned text safe to display.

NPC setup
---------
Set `ai_giftable_items` on the NPC — a list of prototype keys, e.g.:

    npc.attributes.add("ai_giftable_items", ["WOLF_PELT", "WRITS_OF_PASSAGE"])

The LLM's system prompt should tell it to emit `[GIVE: PROTO_KEY]`
(on its own line or inline) whenever it wants to hand over one of
those items. The marker itself is stripped from the visible text.
"""
import re

_GIFT_RE = re.compile(r"\[GIVE:\s*([A-Za-z0-9_ \-]+?)\s*\]", re.IGNORECASE)


def _fire_item_received(recipient, npc, item):
    """Send an item_received OOB event to the recipient's session(s),
    and tick any matching 'gather' quest objectives. Every scripted
    item handoff (duel drops, LLM gifts, future reward flows) routes
    through here, so this is the natural chokepoint to advance quests
    that require receiving a named item."""
    try:
        from commands.quests import quest_gather
        quest_gather(recipient, item.key, qty=1)
    except Exception:
        pass
    try:
        import time as _time
        payload = {
            "type": "item_received",
            "_ts": _time.time(),
            "itemName": item.key,
            "fromNpc": npc.key if npc else "",
            "desc": (item.db.desc or "")[:180],
        }
        for sess in recipient.sessions.all():
            sess.msg(event=payload)
    except Exception:
        pass


def _spawn_into(proto_key, recipient):
    """Spawn *proto_key* and move it into recipient's inventory.
    Returns the created object, or None on failure.
    """
    try:
        from evennia import spawn
        items = spawn(proto_key)
        if not items:
            return None
        item = items[0]
        item.move_to(recipient, quiet=True)
        return item
    except Exception:
        return None


def process_gift_markers(reply, npc, recipient):
    """Strip [GIVE: KEY] markers from *reply*, spawn approved items
    into the recipient, and emit item_received events. Returns the
    cleaned reply text.
    """
    if not reply or "[GIVE" not in reply.upper():
        return reply
    allow_raw = npc.attributes.get("ai_giftable_items", default=None) or []
    allow = {str(k).strip().upper(): str(k).strip() for k in allow_raw}

    def _sub(match):
        claim = match.group(1).strip()
        claim_key = claim.upper().replace(" ", "_").replace("-", "_")
        if claim_key in allow:
            item = _spawn_into(allow[claim_key], recipient)
            if item:
                _fire_item_received(recipient, npc, item)
                try:
                    recipient.msg(
                        f"|y{npc.key} hands you |w{item.key}|y.|n"
                    )
                except Exception:
                    pass
        # Always strip the marker from visible text — if the claim is
        # invalid, the NPC simply talks about giving something without
        # actually giving it, which is fine flavor.
        return ""

    cleaned = _GIFT_RE.sub(_sub, reply)
    # Tidy double-spaces and stray whitespace
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def announce_item_drop(recipient, item, from_source_name=""):
    """Fire an item_received OOB event for any non-LLM item handoff
    (e.g. duel defeat drops). Useful so the UI toast also shows for
    scripted rewards.
    """
    _fire_item_received(recipient, type("N", (), {"key": from_source_name})(), item)
