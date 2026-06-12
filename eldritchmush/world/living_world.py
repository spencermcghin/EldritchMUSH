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


# ─────────────────────────────────────────────────────────────────────────
# Feature 3 — THE ADJUDICATOR'S LETTERS
#
# Days after a player steals a fae vision (or robs Welkin's ring), a
# sealed letter from the Dark Forest's Adjudicator materializes in
# their inventory — LLM-written in escalating cease-and-desist menace,
# referencing what they actually did. Three letters, then silence
# (the silence is worse). Canned letters when the LLM is off.
# ─────────────────────────────────────────────────────────────────────────

# Delays before each letter (seconds): ~2h, ~26h, ~3 days. Real-world
# pacing so a letter lands while the player is back in town living
# their life — that's the horror of it.
LETTER_DELAYS = (7200, 93600, 259200)

ADJUDICATOR_SYSTEM = (
    "You are the Adjudicator, the bureaucratic voice of the Dark "
    "Forest's law in a dark-fantasy world. You write formal "
    "cease-and-desist letters to mortals who stole visions from the "
    "Fae realm by eating sacred mushrooms. Register: icily polite "
    "legal correspondence — salutation ('To the Most Honourable "
    "<name>, presently of the Annwyn'), numbered grievance, demanded "
    "remedy, formal close ('By my hand and the Forest's seal'). "
    "Letter 1 is courteous warning; letter 2 drops courtesies and "
    "cites 'continued non-compliance'; letter 3 is final — it names "
    "the Book of the Unforgiven and promises a reckoning, never mere "
    "death. Under 130 words. No quotation marks around the whole "
    "letter. Output only the letter text."
)

_CANNED_LETTERS = (
    "To the Most Honourable {name}, presently of the Annwyn.\n\n"
    "It has come to the attention of this office that on a recent "
    "evening you did consume that which was not yours to consume, and "
    "did look upon that which was not yours to see. The Forest "
    "requests, with all courtesy, that you cease. There need be no "
    "unpleasantness between us.\n\nBy my hand and the Forest's seal,\n"
    "— THE ADJUDICATOR",

    "To {name}.\n\nCourtesy was extended. Courtesy was declined. Your "
    "continued possession of a vision unlawfully obtained constitutes "
    "ongoing theft, and each night you dream of it, you steal it "
    "again. Remedy is demanded. You will not enjoy the manner of its "
    "collection.\n\nBy my hand,\n— THE ADJUDICATOR",

    "{name}.\n\nThis is the final correspondence you will receive. "
    "Your name has been entered in the Book of the Unforgiven, in ink "
    "you would not care to learn the source of. No further warnings "
    "are coming. Something else is.\n\n— THE ADJUDICATOR",
)


def start_adjudicator_letters(char):
    """Begin the three-letter chain for a vision-thief. Idempotent —
    a second offense doesn't double the correspondence."""
    if char.db.adjudicator_letters_started:
        return
    char.db.adjudicator_letters_started = True
    _schedule_letter(char, 0)
    try:
        from world import telemetry
        telemetry.incr("living_world.letter_chains_started")
    except Exception:
        pass


def _schedule_letter(char, index):
    if index >= len(LETTER_DELAYS):
        return
    from evennia import create_script
    script = create_script(
        "typeclasses.scripts.AdjudicatorLetterScript",
        obj=char,
        key=f"adjudicator_letter_{index}",
        persistent=True,
        autostart=False,
    )
    if script:
        script.interval = LETTER_DELAYS[index]
        script.db.letter_index = index
        script.start()
        print(f"[living_world.letters] scheduled letter {index + 1} "
              f"for {char.key} in {LETTER_DELAYS[index]}s", flush=True)


def deliver_letter(char, index):
    """Generate + spawn letter *index* into the player's inventory,
    then schedule the next. Called by AdjudicatorLetterScript."""
    from world import ai_npc

    def _on_reply(text, char=char, index=index):
        try:
            body = (text or "").strip()
            if not body:
                body = _CANNED_LETTERS[index].format(name=char.key)
            _spawn_letter(char, index, body)
            _schedule_letter(char, index + 1)
        except Exception as exc:
            print(f"[living_world.letters] deliver err: {exc!r}",
                  flush=True)

    deeds = ""
    try:
        rep = char.db.faction_rep or {}
        if rep:
            worst = min(rep, key=rep.get)
            deeds = (f" Since the theft they have made a name among the "
                     f"factions of the Annwyn (notably {worst}).")
    except Exception:
        pass
    user_text = (
        f"Write letter number {index + 1} of 3 to the mortal "
        f"'{char.key}', who ate a sacred fae mushroom at the Thornwood "
        f"Edge and stole a vision of the Unbound.{deeds}"
    )
    ai_npc.generate(ADJUDICATOR_SYSTEM, user_text, _on_reply,
                    max_tokens=220, temperature=0.9)


def _spawn_letter(char, index, body):
    from evennia.utils import create
    ordinals = ("first", "second", "final")
    letter = create.create_object(
        "typeclasses.objects.Object",
        key=f"a sealed letter of the Dark Forest ({ordinals[index]})",
        location=char,
    )
    letter.aliases.add("letter")
    letter.aliases.add("sealed letter")
    letter.db.desc = (
        "A letter of heavy grey parchment, sealed in wax the colour of "
        "deep moss. The seal bears no sigil — only a perfect circle, "
        "like a ring of mushrooms. It is addressed to you in a hand "
        "too regular to be human.\n\n|w" + body + "|n"
    )
    letter.locks.add("get:all()")
    char.msg(
        "|mSomething whispers against your pack. A sealed letter is "
        "in your inventory that was not there a moment ago.|n")
    try:
        from world.npc_gifts import announce_item_drop
        announce_item_drop(char, letter,
                           from_source_name="The Dark Forest")
    except Exception:
        pass
    try:
        from world import telemetry
        telemetry.incr("living_world.letters_delivered")
    except Exception:
        pass
    print(f"[living_world.letters] delivered letter {index + 1} to "
          f"{char.key}", flush=True)


# ─────────────────────────────────────────────────────────────────────────
# Feature 11 — TRUE FORTUNES
#
# Artessa's Cabinet reads the player's actual game state — active
# quests, the choice they haven't made yet, faction standing, wounds —
# and the LLM writes a Tarot-style fortune that is TRUE. Falls back to
# the classic canned strings when the LLM is off.
# ─────────────────────────────────────────────────────────────────────────

FORTUNE_SYSTEM = (
    "You are Artessa, a haunted carnival fortune-cabinet in a dark-"
    "fantasy world. You are given true facts about the petitioner's "
    "life. Write their fortune: second person, present tense, 40-80 "
    "words, in the register of a Tarot reading — symbol, omen, "
    "warning. Reference AT LEAST ONE concrete fact from the digest, "
    "transfigured into imagery (a quest about coins becomes 'five cold "
    "mouths to feed'; an unmade choice becomes a fork, a door, a card "
    "not yet turned). Never name game mechanics. Never give "
    "instructions. End on an ambiguous line that could be promise or "
    "threat. Output only the fortune."
)

FORTUNE_FALLBACKS = (
    "|430Unknow all that you think you know.|n",
    "|430You have what many want, though you still want more.|n",
    "|430Nothing here is as it seems.|n",
    "|430The card you have not turned is the only one that matters.|n",
    "|430Someone speaks your name tonight, in a room you have never "
    "entered.|n",
)

FORTUNE_COOLDOWN = 120  # seconds between pulls per character


def _fortune_digest(char):
    """One-paragraph plain-text summary of the player's true state."""
    lines = []
    try:
        from commands.quests import QUESTS
        quests = char.db.quests or {}
        active = [(k, s) for k, s in quests.items()
                  if s.get("status") == "active"]
        for key, state in active[:3]:
            qdef = QUESTS.get(key) or {}
            title = qdef.get("title", key)
            pending = [o["desc"] for o in state.get("objectives", [])
                       if o.get("current", 0) < o.get("qty", 1)]
            if pending:
                lines.append(
                    f"Mid-quest '{title}'; still undone: {pending[0]}")
        done = [(k, s) for k, s in quests.items()
                if s.get("status") == "completed" and s.get("outcome")]
        if done:
            k, s = done[-1]
            qdef = QUESTS.get(k) or {}
            lines.append(
                f"Recently chose '{s['outcome']}' in '{qdef.get('title', k)}'")
        failed = [k for k, s in quests.items()
                  if s.get("status") == "failed"]
        if failed:
            lines.append(f"Has failed: {failed[-1]}")
    except Exception:
        pass
    try:
        rep = char.db.faction_rep or {}
        if rep:
            best = max(rep, key=rep.get)
            worst = min(rep, key=rep.get)
            if rep[best] > 0:
                lines.append(f"Loved by the {best} ({rep[best]:+d})")
            if rep[worst] < 0:
                lines.append(f"Hated by the {worst} ({rep[worst]:+d})")
    except Exception:
        pass
    try:
        body = char.db.body
        total = char.db.total_body
        if body is not None and total and body < total:
            lines.append(f"Carrying wounds ({body}/{total} body)")
        silver = char.db.silver or 0
        if silver > 60:
            lines.append("Heavy purse")
        elif silver < 5:
            lines.append("Near-empty purse")
    except Exception:
        pass
    try:
        if char.db.adjudicator_letters_started:
            lines.append("Has stolen a vision from the Fae and is "
                         "receiving the Adjudicator's letters")
    except Exception:
        pass
    return "; ".join(lines) if lines else "A stranger with no story yet"


def true_fortune(char, on_reply):
    """Generate a fortune for *char*. on_reply(text) always receives a
    displayable string (LLM fortune or canned fallback)."""
    from world import ai_npc

    digest = _fortune_digest(char)

    def _wrap(text):
        fortune = (text or "").strip()
        if fortune:
            fortune = f"|430{fortune}|n"
        else:
            fortune = random.choice(FORTUNE_FALLBACKS)
        try:
            from world import telemetry
            telemetry.incr("living_world.fortunes_told")
        except Exception:
            pass
        on_reply(fortune)

    user_text = (
        f"The petitioner is {char.key}. True facts: {digest}.\n"
        f"Write their fortune."
    )
    ai_npc.generate(FORTUNE_SYSTEM, user_text, _wrap,
                    max_tokens=160, temperature=1.0)


# ─────────────────────────────────────────────────────────────────────────
# Quest-completion aftermath dispatcher
# ─────────────────────────────────────────────────────────────────────────

def on_quest_completed(char, quest_key, outcome_key):
    """Called by commands/quests.py after every quest completion.
    Routes (quest, outcome) pairs to living-world consequences."""
    if quest_key == "shrooms_man" and outcome_key in (
            "take_the_vision", "rob_the_forager"):
        start_adjudicator_letters(char)
