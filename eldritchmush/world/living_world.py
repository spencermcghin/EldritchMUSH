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
    ledger_add("rumor", char=char.key, source=source_key,
               target=target_key)
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
    ledger_add("letter", char=char.key, index=index)
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
# THE WORLD LEDGER — a rolling log of notable player deeds. Dreams,
# the chronicle, and future features all read from it. Stored on a
# singleton storage script so it survives reboots.
# ─────────────────────────────────────────────────────────────────────────

LEDGER_CAP = 200


def _ledger_script():
    from evennia.scripts.models import ScriptDB
    from evennia import create_script
    script = ScriptDB.objects.filter(db_key="living_world_ledger").first()
    if not script:
        script = create_script(
            "typeclasses.scripts.LedgerStorageScript",
            key="living_world_ledger",
            persistent=True, autostart=False,
        )
    return script


def ledger_add(kind, **fields):
    """Append one event to the world ledger (capped ring)."""
    import time as _time
    try:
        script = _ledger_script()
        events = list(script.db.events or [])
        fields["kind"] = kind
        fields["ts"] = _time.time()
        events.append(fields)
        if len(events) > LEDGER_CAP:
            events = events[-LEDGER_CAP:]
        script.db.events = events
    except Exception as exc:
        print(f"[living_world.ledger] add err: {exc!r}", flush=True)


def ledger_recent(days=7, kinds=None):
    import time as _time
    try:
        script = _ledger_script()
        cutoff = _time.time() - days * 86400
        out = [e for e in (script.db.events or [])
               if e.get("ts", 0) >= cutoff
               and (kinds is None or e.get("kind") in kinds)]
        return out
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────
# Feature 2 — DIERDRA DREAMS
#
# Once a week, Dierdra the Wisewoman dreams. The LLM stitches the
# week's real player deeds (from the ledger) into a surreal prophecy
# threaded with the campaign's Unbound arc. The dream is spoken aloud
# if anyone is present, and becomes part of her conversational
# knowledge — ask her about her dream and she'll recount it.
# ─────────────────────────────────────────────────────────────────────────

DREAMER_KEY = "Dierdra the Wisewoman"

DREAM_SYSTEM = (
    "You are the dreaming mind of Dierdra the Wisewoman, a witch-"
    "touched oracle in a dark-fantasy frontier town. You are given the "
    "week's true deeds of real travelers. Compose her dream: first "
    "person, present tense, 90-130 words, surreal and prophetic. Weave "
    "in 2-3 of the deeds, transfigured into dream-imagery (names may "
    "surface once, half-remembered). Thread through it the deep omen: "
    "something ancient — the Unbound — turning in its tomb beneath "
    "everything, a door opening by inches. Never explain. Never break "
    "register. Output only the dream."
)

DREAM_FALLBACK = (
    "I am standing in a field of doors laid flat like graves. Under "
    "every door, breathing. The breathing is patient. A crow lands on "
    "the nearest door and says a name I knew this week and have "
    "already forgotten, and far below, something that has been "
    "counting the years stops counting. It has reached the number it "
    "wanted. The doors are so thin. They were always so thin."
)


def _dream_npc():
    from evennia.objects.models import ObjectDB
    return ObjectDB.objects.filter(db_key=DREAMER_KEY).first()


def _deed_lines(days=7, cap=8):
    """Human-readable lines for recent ledger deeds."""
    lines = []
    for e in ledger_recent(days=days)[-cap:]:
        kind = e.get("kind")
        who = e.get("char", "a traveler")
        if kind == "quest":
            lines.append(
                f"{who} completed '{e.get('title', '?')}'"
                + (f" choosing '{e.get('outcome')}'" if e.get("outcome")
                   else ""))
        elif kind == "rumor":
            lines.append(f"a rumor about {who} spread to "
                         f"{e.get('target', 'someone')}")
        elif kind == "letter":
            lines.append(f"the Dark Forest wrote to {who}")
    return lines


def dream_tick():
    """Weekly: compose Dierdra's dream from the ledger and deliver it."""
    from world import ai_npc
    npc = _dream_npc()
    if not npc:
        print("[living_world.dream] Dierdra not found; skipping",
              flush=True)
        return

    deeds = _deed_lines()

    def _on_reply(text, npc=npc):
        try:
            dream = (text or "").strip() or DREAM_FALLBACK
            if len(dream) > 1200:
                dream = dream[:1200]
            npc.db.current_dream = dream
            # Fold into her conversational knowledge (replace any prior
            # dream block so it never accumulates).
            know = npc.attributes.get("ai_knowledge", default="") or ""
            marker = "\n- HER LATEST DREAM"
            if marker in know:
                know = know.split(marker)[0]
            npc.attributes.add(
                "ai_knowledge",
                know + f"{marker} (recount it, haltingly, if asked "
                f"about dreams or omens): \"{dream}\"")
            # Speak it if anyone is present to hear.
            room = npc.location
            if room and any(getattr(o, "has_account", False)
                            for o in room.contents):
                room.msg_contents(
                    f"|m{npc.key} goes suddenly still. Her eyes close. "
                    f"When she speaks, it is from somewhere else:|n\n"
                    f"|w\"{dream}\"|n")
            try:
                from world import telemetry
                telemetry.incr("living_world.dreams")
            except Exception:
                pass
            print(f"[living_world.dream] new dream set "
                  f"({len(dream)} chars)", flush=True)
        except Exception as exc:
            print(f"[living_world.dream] err: {exc!r}", flush=True)

    if deeds:
        user_text = ("This week's true deeds:\n- "
                     + "\n- ".join(deeds) + "\nCompose the dream.")
    else:
        user_text = ("No travelers did anything of note this week. "
                     "Compose a dream of unbearable stillness — the "
                     "quiet before something wakes.")
    ai_npc.generate(DREAM_SYSTEM, user_text, _on_reply,
                    max_tokens=260, temperature=1.0)


# ─────────────────────────────────────────────────────────────────────────
# Feature 9 — THE CHRONICLE OF THE VALE
#
# Once a week, an unseen chronicler writes a page of bardic prose
# summarizing the week's real player deeds (from the ledger) and
# leaves it on the long table of Songbird's Rest. The last few pages
# remain readable; older pages crumble. Player history becomes lore.
# ─────────────────────────────────────────────────────────────────────────

CHRONICLE_ROOM_KEY = "Songbird's Rest"
CHRONICLE_KEEP = 4

CHRONICLE_SYSTEM = (
    "You are the anonymous Chronicler of the Vale, writing the weekly "
    "page of a frontier town's chronicle in a dark-fantasy world. You "
    "are given the week's true deeds of real travelers. Write the "
    "page: 100-150 words of bardic period prose, third person, "
    "naming the travelers as the deeds name them. Honor what deserves "
    "honor; note what deserves suspicion with a dry, careful pen — "
    "the Chronicler must live here too. Close with one line about "
    "the Vale itself (the season, the mists, the unquiet dead). "
    "Output only the page text."
)


def _chronicle_room():
    from evennia.objects.models import ObjectDB
    return ObjectDB.objects.filter(db_key=CHRONICLE_ROOM_KEY).first()


def _fallback_chronicle(deeds):
    body = "This week the Vale records: " + "; ".join(deeds) + "."
    return (body + " So it is written, and so the mists were "
            "watching, as they always are.")


def chronicle_tick():
    """Weekly: write the chronicle page and place it in the tavern."""
    from world import ai_npc
    room = _chronicle_room()
    if not room:
        print("[living_world.chronicle] tavern not found; skipping",
              flush=True)
        return
    deeds = _deed_lines(days=7, cap=10)
    if not deeds:
        print("[living_world.chronicle] quiet week; no page written",
              flush=True)
        return

    def _on_reply(text, room=room, deeds=deeds):
        try:
            body = (text or "").strip() or _fallback_chronicle(deeds)
            if len(body) > 1500:
                body = body[:1500]
            _place_chronicle_page(room, body)
        except Exception as exc:
            print(f"[living_world.chronicle] err: {exc!r}", flush=True)

    user_text = ("This week's true deeds:\n- " + "\n- ".join(deeds)
                 + "\nWrite the page.")
    ai_npc.generate(CHRONICLE_SYSTEM, user_text, _on_reply,
                    max_tokens=300, temperature=0.95)


def _place_chronicle_page(room, body):
    from evennia.utils import create
    from evennia.objects.models import ObjectDB
    script = _ledger_script()
    page_no = int(script.db.chronicle_page or 0) + 1
    script.db.chronicle_page = page_no

    page = create.create_object(
        "typeclasses.objects.Object",
        key=f"Chronicle of the Vale, page {page_no}",
        location=room,
    )
    page.aliases.add("chronicle")
    page.aliases.add("page")
    page.db.chronicle_page = page_no
    page.db.desc = (
        "A single page of close-written vellum, left on the long table "
        "where anyone might read it. No one has ever seen the "
        "Chronicler write. The ink is always still damp.\n\n|w"
        + body + "|n")
    page.locks.add("get:false()")
    page.db.get_err_msg = (
        "|yThe page will not leave the table. The Chronicle stays "
        "where all may read it.|n")

    # Crumble pages beyond the kept window.
    pages = [o for o in ObjectDB.objects.filter(db_location=room.pk)
             if (o.db.chronicle_page or 0) > 0]
    pages.sort(key=lambda o: o.db.chronicle_page)
    for old in pages[:-CHRONICLE_KEEP]:
        old.delete()

    room.msg_contents(
        "|025A new page lies on the long table that was not there "
        "before. The ink is still damp.|n")
    try:
        from world import telemetry
        telemetry.incr("living_world.chronicle_pages")
    except Exception:
        pass
    print(f"[living_world.chronicle] page {page_no} placed", flush=True)


# ─────────────────────────────────────────────────────────────────────────
# Feature 8 — VENGEFUL RETURNS
#
# Named antagonists flagged db.vengeful=True don't stay down. Days
# after being slain, they rise where they fell — stats restored,
# dialogue updated to KNOW who killed them and how it felt. The
# killer's npc_rep already carries "killed by your hand"; the return
# adds the other half of the relationship.
# ─────────────────────────────────────────────────────────────────────────

VENGEFUL_MIN_DAYS = 3
VENGEFUL_MAX_DAYS = 6

VENGEANCE_MARKER = "\n- RETURNED FROM DEATH"


def on_npc_slain(npc, killers):
    """Called from combat when a vengeful NPC drops. Schedules the
    return. *killers* = account-backed characters present at the kill."""
    try:
        if not npc.db.vengeful or npc.db.vengeful_return_pending:
            return
        npc.db.vengeful_return_pending = True
        npc.db.slain_by = [c.key for c in (killers or [])
                           if c is not None] or ["persons unknown"]
        delay = random.randint(
            VENGEFUL_MIN_DAYS * 86400, VENGEFUL_MAX_DAYS * 86400)
        from evennia import create_script
        script = create_script(
            "typeclasses.scripts.VengefulReturnScript",
            obj=npc,
            key="vengeful_return",
            persistent=True,
            autostart=False,
        )
        if script:
            script.interval = delay
            script.start()
        ledger_add("slain", char=", ".join(npc.db.slain_by),
                   npc=npc.key)
        try:
            from world import telemetry
            telemetry.incr("living_world.vengeful_scheduled")
        except Exception:
            pass
        print(f"[living_world.vengeful] {npc.key} will return in "
              f"{delay // 86400}d (slain by {npc.db.slain_by})",
              flush=True)
    except Exception as exc:
        print(f"[living_world.vengeful] schedule err: {exc!r}",
              flush=True)


def vengeful_return(npc):
    """Restore the slain NPC and teach it who killed it."""
    try:
        npc.db.vengeful_return_pending = False
        killers = list(npc.db.slain_by or ["persons unknown"])
        killer_names = ", ".join(killers)

        # Restore vitals to their full values.
        npc.db.body = npc.db.total_body or npc.db.body or 4
        npc.db.bleed_points = 3
        npc.db.death_points = 3
        npc.db.weakness = 0
        npc.db.in_combat = 0
        npc.db.is_staggered = False
        for part in ("right_arm", "left_arm", "right_leg", "left_leg",
                     "torso"):
            npc.attributes.add(part, 1)

        # Teach its dialogue what happened (replace-not-accumulate).
        know = npc.attributes.get("ai_knowledge", default="") or ""
        if VENGEANCE_MARKER in know:
            know = know.split(VENGEANCE_MARKER)[0]
        npc.attributes.add(
            "ai_knowledge",
            know + f"{VENGEANCE_MARKER}: you were killed — truly "
            f"killed — by {killer_names}, and you came back. You "
            f"remember the iron in their hands and the cold after. "
            f"If you speak with them, let them know, quietly, that "
            f"you remember. You do not forgive.")
        npc.db.killed_by = killers

        room = npc.location
        if room:
            room.msg_contents(
                f"|m{npc.key} draws a breath it should not be able "
                f"to draw, and rises. Something is different about "
                f"the way it looks at the world now — like a debt "
                f"being counted.|n")
        # The killers' own npc_rep gains the other half of the memory.
        try:
            from commands.quests import _adjust_npc_rep
            from evennia.objects.models import ObjectDB
            for name in killers:
                kc = ObjectDB.objects.filter(
                    db_key=name, db_account__isnull=False).first()
                if kc:
                    _adjust_npc_rep(
                        kc, (npc.key or "").lower(), 0,
                        memory_tag="returned from the death you gave "
                                   "them — and remembers it")
        except Exception:
            pass
        ledger_add("returned", npc=npc.key, char=killer_names)
        try:
            from world import telemetry
            telemetry.incr("living_world.vengeful_returns")
        except Exception:
            pass
        print(f"[living_world.vengeful] {npc.key} has returned "
              f"(remembers {killer_names})", flush=True)
    except Exception as exc:
        print(f"[living_world.vengeful] return err: {exc!r}", flush=True)


# ─────────────────────────────────────────────────────────────────────────
# Feature 4 — THE MISTS MOVE
#
# Every few days, the Mists open ONE temporary passage between two
# wild rooms that have no direct connection — and close the last one
# they opened. Purely additive: no real exit is ever touched, so no
# quest geography can break. Dungeon interiors are excluded by the
# em-dash naming convention; transit/chargen rooms by zone.
# ─────────────────────────────────────────────────────────────────────────

MIST_ZONES = ("The Annwyn", "Annwyn", "Tamris", "Mystvale")
MIST_EXIT_KEY = "mist-passage"

# Interior/progression rooms the Mists must never open into. Checked
# as case-insensitive substrings of the room key (em-dash dungeon
# naming is excluded separately).
MIST_DENY_SUBSTRINGS = (
    "barrow", "crypt", "tomb", "sanctum", "corridor", "resting hall",
    "wardstone", "mine", "scriptorium", "office", "deck", "hold",
    "cabin", "cargo", "cell", "prison", "vault", "hovel", "lair",
    "burial", "warding",
)


def _mist_rooms():
    """Wild rooms eligible to host a mist passage."""
    from evennia.objects.models import ObjectDB
    rooms = []
    for room in ObjectDB.objects.filter(
            db_typeclass_path__startswith="typeclasses.rooms"):
        try:
            zone = room.db.zone
            if zone not in MIST_ZONES:
                continue
            key = room.key or ""
            if "—" in key:
                continue  # dungeon sub-rooms (The Mine — ..., etc.)
            key_l = key.lower()
            if any(s in key_l for s in MIST_DENY_SUBSTRINGS):
                continue
            if room.db.no_mist_passage:
                continue
            rooms.append(room)
        except Exception:
            continue
    return rooms


def _close_mist_passage():
    """Delete the current mist passage exits (both directions)."""
    from evennia.objects.models import ObjectDB
    closed_rooms = []
    for ex in list(ObjectDB.objects.filter(db_key=MIST_EXIT_KEY)):
        try:
            loc = ex.location
            if loc:
                closed_rooms.append(loc)
            ex.delete()
        except Exception:
            pass
    for room in closed_rooms:
        try:
            room.msg_contents(
                "|025The wall of mist at the edge of the world thins, "
                "wavers — and is simply gone, taking the path it "
                "offered with it.|n")
        except Exception:
            pass
    return len(closed_rooms)


def mist_tick():
    """Close the old passage, open a new one elsewhere."""
    from evennia.utils import create
    closed = _close_mist_passage()
    rooms = _mist_rooms()
    if len(rooms) < 2:
        print("[living_world.mists] not enough rooms; skipping",
              flush=True)
        return
    random.shuffle(rooms)
    room_a, room_b = None, None
    for cand_a in rooms[:20]:
        for cand_b in rooms[:20]:
            if cand_a == cand_b:
                continue
            # No existing direct connection in either direction.
            if any(getattr(e, "destination", None) == cand_b
                   for e in cand_a.contents):
                continue
            if any(getattr(e, "destination", None) == cand_a
                   for e in cand_b.contents):
                continue
            room_a, room_b = cand_a, cand_b
            break
        if room_a:
            break
    if not room_a:
        print("[living_world.mists] no unconnected pair found",
              flush=True)
        return

    for src, dst in ((room_a, room_b), (room_b, room_a)):
        ex = create.create_object(
            "typeclasses.exits.Exit",
            key=MIST_EXIT_KEY, location=src, destination=dst)
        ex.aliases.add("mist")
        ex.aliases.add("passage")
        ex.db.desc = (
            "A seam in the world where the mist has worn through — "
            "grey light, and the smell of somewhere else.")
        src.msg_contents(
            f"|025The mist along one edge of {src.key} thins to a "
            f"seam of grey light. Through it: somewhere that should "
            f"not be a single step away. The Mists are offering. "
            f"They will change their mind.|n")

    ledger_add("mist_passage", a=room_a.key, b=room_b.key)
    try:
        from world import telemetry
        telemetry.incr("living_world.mist_passages")
    except Exception:
        pass
    print(f"[living_world.mists] closed {closed} old; opened "
          f"{room_a.key} <-> {room_b.key}", flush=True)


# ─────────────────────────────────────────────────────────────────────────
# Quest-completion aftermath dispatcher
# ─────────────────────────────────────────────────────────────────────────

def on_quest_completed(char, quest_key, outcome_key):
    """Called by commands/quests.py after every quest completion.
    Routes (quest, outcome) pairs to living-world consequences."""
    if quest_key == "shrooms_man" and outcome_key in (
            "take_the_vision", "rob_the_forager"):
        start_adjudicator_letters(char)

    # Feed the world ledger (dreams + chronicle source material).
    try:
        from commands.quests import QUESTS
        title = (QUESTS.get(quest_key) or {}).get("title", quest_key)
        ledger_add("quest", char=char.key, quest=quest_key,
                   title=title, outcome=outcome_key)
    except Exception:
        pass
