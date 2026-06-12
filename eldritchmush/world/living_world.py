"""
living_world.py — systems that make the Annwyn feel haunted by intelligence.

Each feature here is an offline "world tick" that uses the spend-capped
ai_npc.generate() API (with non-LLM fallbacks, so everything works with
the LLM disabled). All ticks are driven by scripts in
typeclasses/scripts.py and bootstrapped from at_server_startstop.

Feature 1 — GOSSIP: NPC memories about a player propagate to other NPCs
the player knows, distorted slightly in the retelling. Memories live on
the character (char.db.npc_rep[npc_key]["memories"]), so a rumor is a
new memory string written under ANOTHER npc's key on the same character.
The LLM dialogue prompt already surfaces npc_rep memories, so the
receiving NPC will spontaneously know (a warped version of) what the
player did — and players can chase a rumor back to who started it.
"""

import random

# Rumor memories are prefixed so they are never re-gossiped (no
# infinite telephone) and so the dialogue LLM knows it's secondhand.
RUMOR_PREFIX = "heard a rumor"

# At most this many rumors held about a player per receiving NPC —
# keeps memory lists from silting up with hearsay.
MAX_RUMORS_PER_NPC = 2

GOSSIP_SYSTEM = (
    "You are the rumor-mill of a dark-fantasy frontier town. You retell "
    "one NPC's firsthand memory of a traveler as the SECONDHAND rumor "
    "another NPC heard. Rules: exactly one sentence, third person, "
    "past tense, dark-fantasy register, no quotation marks. Distort "
    "exactly ONE vivid detail — exaggerate it, get a name slightly "
    "wrong, or shift the motive — but keep the core deed recognizable. "
    "Never invent a new crime. Output only the rumor sentence."
)


def _player_characters():
    """All account-backed player characters."""
    from evennia.objects.models import ObjectDB
    return list(ObjectDB.objects.filter(
        db_account__isnull=False,
        db_typeclass_path="typeclasses.characters.Character",
    ))


def _gossip_candidates(char):
    """Return (source_key, memory, target_key) options for one player.

    Source: any firsthand (non-rumor) memory an NPC holds about the
    player. Target: a DIFFERENT NPC the player has also interacted
    with (gossip travels the player's own social graph, so the payoff
    is guaranteed to be an NPC they'll meet again) who isn't already
    full of hearsay about them.
    """
    rep = char.db.npc_rep or {}
    if len(rep) < 2:
        return []
    sources = []
    for npc_key, entry in rep.items():
        for mem in (entry or {}).get("memories") or []:
            if mem and not mem.startswith(RUMOR_PREFIX):
                sources.append((npc_key, mem))
    if not sources:
        return []
    out = []
    for source_key, mem in sources:
        for target_key, target_entry in rep.items():
            if target_key == source_key:
                continue
            t_mems = (target_entry or {}).get("memories") or []
            rumor_count = sum(
                1 for m in t_mems if m.startswith(RUMOR_PREFIX))
            if rumor_count >= MAX_RUMORS_PER_NPC:
                continue
            # Don't re-spread a deed the target already heard about.
            if any(mem[:40].lower() in m.lower() for m in t_mems):
                continue
            out.append((source_key, mem, target_key))
    return out


def _fallback_distort(source_key, memory):
    """Non-LLM rumor: still secondhand, still flags the teller."""
    templates = [
        f"that you {memory} — or so the telling goes, and tellings twist",
        f"from {source_key}'s corner of the world that you {memory}, "
        f"though the details had grown teeth by the time it arrived",
        f"that you {memory}; whoever carried the tale added a shadow to it",
    ]
    return random.choice(templates)


def _write_rumor(char, source_key, target_key, rumor_text):
    from commands.quests import _adjust_npc_rep
    memory = f"{RUMOR_PREFIX} (by way of {source_key}): {rumor_text}"
    _adjust_npc_rep(char, target_key, 0, memory_tag=memory)
    try:
        from world import telemetry
        telemetry.incr("living_world.rumors_spread")
    except Exception:
        pass
    print(
        f"[living_world.gossip] {char.key}: {source_key} -> {target_key}: "
        f"{rumor_text[:80]}", flush=True)


def gossip_tick(max_events=4):
    """Spread at most one new rumor per player, max_events total.

    Called from GossipScript on the reactor thread; LLM distortion is
    dispatched async per rumor, with a template fallback when the LLM
    is disabled or over budget.
    """
    from world import ai_npc
    events = 0
    chars = _player_characters()
    random.shuffle(chars)
    for char in chars:
        if events >= max_events:
            break
        try:
            options = _gossip_candidates(char)
        except Exception as exc:
            print(f"[living_world.gossip] candidates err for "
                  f"{getattr(char, 'key', '?')}: {exc!r}", flush=True)
            continue
        if not options:
            continue
        source_key, memory, target_key = random.choice(options)
        events += 1

        def _on_reply(text, char=char, source_key=source_key,
                      memory=memory, target_key=target_key):
            try:
                rumor = (text or "").strip()
                if not rumor:
                    rumor = _fallback_distort(source_key, memory)
                # One sentence max — clip runaway generations.
                if len(rumor) > 300:
                    rumor = rumor[:300]
                _write_rumor(char, source_key, target_key, rumor)
            except Exception as exc:
                print(f"[living_world.gossip] write err: {exc!r}",
                      flush=True)

        user_text = (
            f"NPC '{source_key}' has this firsthand memory of the "
            f"traveler {char.key}: \"{memory}\".\n"
            f"Retell it as the rumor NPC '{target_key}' heard."
        )
        ai_npc.generate(GOSSIP_SYSTEM, user_text, _on_reply,
                        max_tokens=90, temperature=1.0)
    if events:
        print(f"[living_world.gossip] tick spread {events} rumor(s)",
              flush=True)
    return events
