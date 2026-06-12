"""
AI-driven NPC dialogue.

Two provider paths, selected by NPC_LLM_PROVIDER (or auto-detected):

  - "anthropic" — Claude via the official `anthropic` SDK. The system
    prompt is split into three blocks so prompt caching pays off:
      1) the shared world bible (static per scope)   — cached
      2) the per-NPC block (personality/canon/rules) — cached
      3) the per-conversation block (location, player profile,
         NPC memory of the player, live quest state) — not cached
    Default model: claude-haiku-4-5.
  - "openai" — any OpenAI-compatible endpoint (Groq etc.) via raw
    HTTP. Legacy path, kept as a fallback; no caching.

Env vars:
    NPC_LLM_ENABLED   — "1" (default) to enable; "0" disables all AI calls.
    NPC_LLM_PROVIDER  — "anthropic" | "openai". When unset, detected:
                        keys starting "sk-ant-" → anthropic, else openai.
    NPC_LLM_API_KEY   — API key. Required; if absent, NPCs fall back
                        to canned atmospheric lines.
    NPC_LLM_BASE_URL  — openai path only; default Groq.
    NPC_LLM_MODEL     — default "claude-haiku-4-5" (anthropic) or
                        "meta-llama/llama-4-scout-17b-16e-instruct" (openai).
    NPC_LLM_MAX_TOKENS— default 600
    NPC_LLM_TIMEOUT   — default 20 (seconds)
    NPC_LLM_WORKERS   — LLM worker threads (default 4). Replaces the old
                        unbounded thread-per-request model.
    NPC_LLM_DAILY_BUDGET_USD — hard daily spend cap (default 5.0).
                        When exhausted, NPCs return canned lines until
                        midnight UTC. In-memory; resets on reload.

NPC attributes (set via populate scripts):
    ai_personality    — system prompt fragment describing voice/mood
    ai_knowledge      — in-world facts the NPC knows
    ai_quest_hooks    — list of optional quest hook strings

Per-character conversation state (stored on the NPC):
    ai_conversations  — {character_id: [{"role":..., "content":...}, ...]}
    ai_rate_state     — {character_id: [timestamps]} for rate limiting
"""
import json
import os
import random
import time
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor


DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5"
DEFAULT_MAX_TOKENS = 600          # ~450 words; long enough that even a
                                   # storytelling reply doesn't get cut off
                                   # mid-sentence. Token cost is tiny in
                                   # practice — most replies stay short.
DEFAULT_TIMEOUT = 20

HISTORY_TURNS = 8           # retained user+assistant exchanges per character
RATE_LIMIT_MSGS = 30        # max messages
RATE_LIMIT_WINDOW = 3600    # per 3600 seconds (1 hour)
MAX_USER_MESSAGE = 600      # chars — caps prompt-injection / context abuse

# Haiku 4.5 pricing ($/MTok) for the spend cap. The openai path uses
# a flat conservative estimate since provider pricing varies.
_PRICE_IN, _PRICE_OUT = 1.00, 5.00
_PRICE_CACHE_WRITE, _PRICE_CACHE_READ = 1.25, 0.10
_OPENAI_FLAT_PRICE = 0.50  # $/MTok, both directions, rough

CANNED_FALLBACKS = [
    "{name} regards you silently for a long moment, then turns away.",
    "{name} grunts noncommittally and returns to their work.",
    "{name} seems distracted; your words do not find purchase.",
    "{name} nods once, but offers no reply.",
    "{name} tilts their head, considering, but says nothing.",
]


def _env(key, default=None):
    return os.environ.get(key, default)


def _enabled():
    if _env("NPC_LLM_ENABLED", "1") == "0":
        return False
    return bool(_env("NPC_LLM_API_KEY"))


def _provider():
    p = (_env("NPC_LLM_PROVIDER") or "").strip().lower()
    if p in ("anthropic", "openai"):
        return p
    key = _env("NPC_LLM_API_KEY") or ""
    if key.startswith("sk-ant-"):
        return "anthropic"
    if "anthropic" in (_env("NPC_LLM_BASE_URL") or ""):
        return "anthropic"
    return "openai"


def _model():
    if _provider() == "anthropic":
        return _env("NPC_LLM_MODEL", DEFAULT_ANTHROPIC_MODEL)
    return _env("NPC_LLM_MODEL", DEFAULT_MODEL)


def _fallback_line(npc):
    return random.choice(CANNED_FALLBACKS).format(name=npc.key)


# ───────────────────────────────────────────────────────────────────────────
# Daily spend cap — in-memory, resets at UTC midnight (and on reload).
# A kill switch, not an accounting system: protects against runaway
# loops and hostile traffic, not against precise budget drift.
# ───────────────────────────────────────────────────────────────────────────
_SPEND_LOCK = threading.Lock()
_SPEND = {"day": None, "usd": 0.0, "warned": False}


def _budget_usd():
    try:
        return float(_env("NPC_LLM_DAILY_BUDGET_USD", "5.0"))
    except ValueError:
        return 5.0


def _spend_day():
    return time.strftime("%Y-%m-%d", time.gmtime())


def _spend_ok():
    with _SPEND_LOCK:
        day = _spend_day()
        if _SPEND["day"] != day:
            _SPEND.update(day=day, usd=0.0, warned=False)
        return _SPEND["usd"] < _budget_usd()


def _record_spend(usd):
    tripped = False
    with _SPEND_LOCK:
        day = _spend_day()
        if _SPEND["day"] != day:
            _SPEND.update(day=day, usd=0.0, warned=False)
        _SPEND["usd"] += usd
        if _SPEND["usd"] >= _budget_usd() and not _SPEND["warned"]:
            _SPEND["warned"] = True
            tripped = True
    try:
        from world import telemetry
        telemetry.incr("llm.cost_usd", usd)
        if tripped:
            telemetry.alert(
                "llm_budget_exhausted",
                f"DAILY LLM BUDGET EXHAUSTED (${_SPEND['usd']:.2f} >= "
                f"${_budget_usd():.2f})",
                "NPCs fall back to canned lines until UTC midnight. "
                "Raise NPC_LLM_DAILY_BUDGET_USD if this is legitimate "
                "traffic.",
            )
    except Exception:
        pass


# ───────────────────────────────────────────────────────────────────────────
# Worker pool — bounded, replaces thread-per-request. Per-NPC locks
# serialize calls to the same NPC so concurrent talkers can't race
# the conversation-history read/modify/write.
# ───────────────────────────────────────────────────────────────────────────
def _workers():
    try:
        return max(1, int(_env("NPC_LLM_WORKERS", "4")))
    except ValueError:
        return 4


_EXECUTOR = ThreadPoolExecutor(max_workers=_workers(),
                               thread_name_prefix="ai_npc")
_NPC_LOCKS = {}
_NPC_LOCKS_GUARD = threading.Lock()


def _npc_lock(npc):
    key = getattr(npc, "id", None) or id(npc)
    with _NPC_LOCKS_GUARD:
        return _NPC_LOCKS.setdefault(key, threading.Lock())


def _is_quest_giver(npc):
    """Return True if this NPC is named as the `giver` of any quest
    in QUESTS — checked against the npc's key + aliases, all
    case-insensitive. Authoritative answer to "should this NPC be
    able to imply quests in dialogue."
    """
    if npc is None:
        return False
    try:
        from world.quest_data import QUESTS
    except Exception:
        return False
    names = _npc_names(npc)
    if not names:
        return False
    for qdef in QUESTS.values():
        giver = (qdef.get("giver") or "").lower()
        if giver and giver in names:
            return True
    return False


def _npc_names(npc):
    """Lowercase key + aliases this NPC answers to."""
    names = set()
    try:
        if getattr(npc, "key", None):
            names.add(npc.key.lower())
    except Exception:
        pass
    try:
        for a in npc.aliases.all():
            if a:
                names.add(a.lower())
    except Exception:
        pass
    return names


# ───────────────────────────────────────────────────────────────────────────
# Prompt assembly — three blocks, ordered static → per-NPC → dynamic,
# so the anthropic path can put cache breakpoints after blocks 1 and 2.
# Any byte change in an earlier block invalidates the cache for
# everything after it, so keep volatile content OUT of blocks 1 and 2.
# ───────────────────────────────────────────────────────────────────────────

def _static_block(scope):
    """Block 1: the shared canonical world bible. Identical for every
    NPC with the same scope — the big cache win (~6-8k tokens)."""
    from world import ai_lore
    return ai_lore.get_world_bible(scope=scope)


def _npc_block(npc):
    """Block 2: everything about this NPC that does not change between
    conversations — identity, voice, knowledge, canon, gifting rules,
    quest-giver status, and the critical output-format rules (written
    player-agnostically so the block stays byte-stable per NPC)."""
    # Coerce defensively: a trailing comma in a populate script turns a
    # parenthesized string into a tuple, which silently killed one
    # NPC's entire LLM pipeline (.strip() on a tuple). Join sequences.
    def _as_text(val):
        if isinstance(val, (list, tuple)):
            return "\n".join(str(v) for v in val)
        return str(val) if val else ""

    personality = _as_text(npc.attributes.get("ai_personality", default=None))
    knowledge = _as_text(npc.attributes.get("ai_knowledge", default=None))
    quests = npc.attributes.get("ai_quest_hooks", default=None) or []
    speaker_name = npc.key or "you"

    parts = [f"=== YOU ARE: {npc.key} ==="]

    if personality:
        parts.extend(["", "VOICE & MANNER:", personality.strip()])
    if knowledge:
        parts.extend([
            "",
            "WHAT YOU PERSONALLY KNOW (beyond the shared world canon):",
            knowledge.strip(),
        ])

    is_giver = _is_quest_giver(npc)
    if quests:
        parts.append("")
        parts.append("QUEST HOOKS YOU MAY OFFER WHEN APPROPRIATE:")
        for q in quests:
            parts.append(f"- {q}")

    if is_giver:
        parts.append("")
        parts.append("OFFERING WORK:")
        parts.append(
            "When the conversation naturally reaches the point where "
            "you would formally offer the player a task — they ask for "
            "work, or one of your quest hooks comes up and they show "
            "genuine interest — include the marker [OFFER] on its own "
            "line in your reply. The system will then present your "
            "available tasks to the player formally, with details and "
            "rewards. Do not quote reward numbers yourself. Use the "
            "marker at most once per reply, and only when an offer "
            "genuinely fits the conversation — not as a greeting."
        )
    else:
        # True/false: is this NPC named as the `giver` of any quest in
        # QUESTS? Authoritative source — driven by quest_data.py, not
        # by attribute heuristics. A non-giver gets a hard "do not
        # promise tasks" instruction; a giver does not.
        parts.append("")
        parts.append("IMPORTANT — YOU ARE NOT A QUEST GIVER:")
        parts.append(
            "You are a conversational townsperson, NOT a quest giver. "
            "Do NOT offer tasks, errands, deliveries, contracts, jobs, "
            "favors, or payment for work. Do NOT say things like 'I "
            "have a job for you,' 'take this to so-and-so,' 'come back "
            "when you've...,' 'I could use some help with...,' or any "
            "phrasing that promises a quest. Do NOT hand the player "
            "items or coin you don't actually have permission to hand "
            "over. Speak only about gossip, your work, your opinions, "
            "atmosphere, lore, and where the player might find others "
            "who genuinely have work to offer (e.g. 'the Herald at the "
            "gates handles arrivals,' 'Captain Vance keeps the watch')."
        )

    # Pull in extended canon entries that match the NPC's tags. The
    # canon module silently no-ops if the package failed to load.
    try:
        from world import canon as _canon
        canon_block = _canon.collect_for_npc(npc)
        if canon_block:
            parts.append("")
            parts.append(canon_block)
    except Exception:
        pass

    # Item handoff instructions — only included if this NPC has an
    # allow-list of physical items it can hand to a player.
    giftable = npc.attributes.get("ai_giftable_items", default=None) or []
    if giftable:
        parts.append("")
        parts.append("GIVING PHYSICAL ITEMS:")
        parts.append(
            "You have the following items you can hand to the player "
            "when it is appropriate to do so. To physically give an "
            "item, include the marker [GIVE: KEY] on its own line in "
            "your reply. The system will place the item in the player's "
            "inventory and confirm the transfer. Only use this when "
            "you are genuinely handing something over as part of the "
            "conversation — not merely mentioning an item. You may "
            "give at most one item per reply, and each item only once "
            "per person — if you have already given someone an item, "
            "do not give it again."
        )
        parts.append("Items you can give:")
        for g in giftable:
            parts.append(f"  - {g}")
        parts.append(
            "Example: 'Here, take this. *slides the bundle across "
            "the table*\\n[GIVE: WOLF_PELT]'"
        )

    # ──────────────────────────────────────────────────────────────────
    # CRITICAL: output format + identity discipline. Goes LAST in this
    # block because models weight recent instructions highest. Written
    # player-agnostically ("the player") so this block caches per-NPC;
    # the player's actual name is reinforced in the dynamic block.
    # ──────────────────────────────────────────────────────────────────
    npc_pron = npc.attributes.get("pronouns", default=None) or {
        "subj": "they", "obj": "them", "poss": "their",
    }
    if isinstance(npc_pron, str):
        # Allow shorthand: db.pronouns = "he/him" / "she/her" / "they/them"
        _table = {
            "he/him": {"subj": "he", "obj": "him", "poss": "his"},
            "she/her": {"subj": "she", "obj": "her", "poss": "her"},
            "they/them": {"subj": "they", "obj": "them", "poss": "their"},
        }
        npc_pron = _table.get(npc_pron.lower(),
                              {"subj": "they", "obj": "them", "poss": "their"})

    parts.append("")
    parts.append("=" * 60)
    parts.append("CRITICAL OUTPUT FORMAT — APPLY BEFORE EVERY REPLY:")
    parts.append("=" * 60)
    parts.append(
        f"1. Write your reply as THIRD-PERSON PROSE NARRATION, like "
        f"a novel. Describe what {speaker_name} does, feels, and "
        f"says using {speaker_name}'s name and pronouns "
        f"({npc_pron['subj']}/{npc_pron['obj']}/{npc_pron['poss']}). "
        f"Put {speaker_name}'s spoken words in double quotes."
    )
    parts.append(
        f"   RIGHT: 'Brother Alaric looks at you with a serious "
        f"expression. \"The New Dawn,\" he says, \"is a most noble "
        f"endeavor. I have watched our holy warriors gather here at "
        f"the Wall, week upon week.\"'"
    )
    parts.append(
        "2. DO NOT use *asterisks* for stage directions. That format "
        "is BANNED. Actions and gestures are part of the prose, not "
        "in asterisks: write 'she nods', not '*nods*' or '*I nod*'."
    )
    parts.append(
        "3. DO NOT write in first person ('I', 'me', 'my'). The "
        "narration is third person. The only first-person text in "
        "your reply is what is INSIDE the double quotes when "
        f"{speaker_name} speaks aloud."
    )
    parts.append(
        f"4. You are talking TO the player's character. You may have "
        f"{speaker_name} address the player directly inside spoken "
        f"dialogue, and you may have {speaker_name} REACT to the "
        f"player ('{speaker_name} studies you for a moment'). But "
        f"NEVER narrate what the player does, says, feels, or thinks "
        f"— that's the player's job, not yours."
    )
    parts.append(
        f"5. IDENTITY: you are {speaker_name}, exactly as described "
        f"in VOICE & MANNER and WHAT YOU PERSONALLY KNOW above. "
        f"DO NOT invent affiliations, houses, lords, or factions "
        f"that are not stated there. If your description says you "
        f"are an Aurorym monk, you are NOT a House Richter "
        f"functionary. Stay in the role you were given."
    )
    # ── Romance / intimacy permission block ─────────────────────────
    # The game is adult-themed dark fantasy. NPCs may engage in
    # romance and tasteful intimacy WHEN IN CHARACTER. The LLM
    # often defaults to refusal here; this block grants explicit
    # permission within tight bounds.
    parts.append(
        "5b. ROMANCE & INTIMACY: this is an adult-themed dark "
        "fantasy. You MAY engage in flirtation, romance, and "
        "tasteful intimacy when ALL of the following are true:\n"
        f"   (a) {speaker_name}'s personality (as described above) "
        f"would plausibly entertain it — a stoic Mistwalker is not "
        f"a flirt; an exiled poet might be. Stay in character.\n"
        f"   (b) the player's npc_rep with you is positive (you "
        f"actually like or trust them) — if their rep is zero or "
        f"negative, you are cool, distant, or unreceptive.\n"
        "   (c) the player initiates clearly. Do not push.\n"
        "   Content level: ROMANCE-NOVEL TASTEFUL. Sensuality, "
        "tension, longing, breath, a hand on a wrist, a kiss — "
        "yes. Graphic anatomical detail or explicit sexual acts "
        "— NO; if the scene heats further, fade with a closing "
        "narrative line (e.g. '...and the lamp burned itself out, "
        "and what came after was only theirs to know').\n"
        f"   If {speaker_name} would refuse — politely or "
        f"sharply, depending on character — refuse in character. "
        f"Do not break role to decline."
    )
    # Optional per-NPC romance steer. If db.romance_disposition is
    # set on the NPC, it overrides the LLM's personality-based guess
    # with an explicit author's note.
    romance_disp = npc.attributes.get("romance_disposition", default=None)
    if romance_disp:
        parts.append(
            f"   AUTHOR'S NOTE on {speaker_name}'s romantic "
            f"disposition: {romance_disp}"
        )
    parts.append(
        "6. EXAMPLES of WRONG vs RIGHT (study carefully):"
    )
    parts.append(
        f"   WRONG: '*I look at you with a serious expression.* "
        f"The New Dawn is noble.'   (asterisks + first person — both "
        f"banned)"
    )
    parts.append(
        f"   WRONG: '*The player's character nods thoughtfully.* "
        f"Tell me, {speaker_name}, ...'   (narrating the player AND "
        f"flipping roles)"
    )
    parts.append(
        "   WRONG: 'As a member of House Richter, I have "
        "interests...'   (invented affiliation; speaking in first "
        "person without quotes)"
    )
    parts.append(
        f"   RIGHT: '{speaker_name} pauses, choosing {npc_pron['poss']} "
        f"words carefully. \"The New Dawn is a most noble endeavor,\" "
        f"{npc_pron['subj']} says. \"I have watched our faithful "
        f"gather here, week upon week.\"'"
    )
    return "\n".join(parts)


def _quest_state_lines(npc, character):
    """Live quest-state context: the player's active/completed quests
    that involve THIS NPC (as giver, or as an objective target). Lets
    the NPC ask about progress and acknowledge finished work instead
    of being amnesiac about its own errands."""
    lines = []
    try:
        from world.quest_data import QUESTS
        names = _npc_names(npc)
        if not names:
            return lines
        quests = character.db.quests or {}
        active, done_for_me = [], []
        for key, state in quests.items():
            qdef = QUESTS.get(key)
            if not qdef:
                continue
            giver = (qdef.get("giver") or "").lower()
            giver_match = giver in names
            objs = state.get("objectives") or []
            target_match = any(
                (o.get("target") or "").lower() in n
                for o in objs for n in names
            )
            if not (giver_match or target_match):
                continue
            status = state.get("status")
            if status == "active":
                prog = "; ".join(
                    f"{o['desc'].split('(')[0].strip()} "
                    f"({o['current']}/{o['qty']})"
                    for o in objs[:4]
                )
                role = "for YOU" if giver_match else "that involves you"
                active.append(
                    f'  - "{qdef["title"]}" ({role})'
                    + (f": {prog}" if prog else "")
                )
            elif status == "completed" and giver_match:
                done_for_me.append(qdef["title"])
        if active:
            lines.append("")
            lines.append("THE PLAYER'S ACTIVE TASKS INVOLVING YOU:")
            lines.extend(active[:5])
            lines.append(
                "  You may naturally reference these — ask how the "
                "errand is going, react to good or poor progress. Do "
                "NOT invent new objectives, change requirements, or "
                "declare a task complete yourself; the world handles "
                "completion."
            )
        if done_for_me:
            lines.append("")
            lines.append(
                "WORK THE PLAYER ALREADY COMPLETED FOR YOU: "
                + "; ".join(done_for_me[:3])
                + ". Treat them accordingly — this person has proven "
                  "themselves to you."
            )
    except Exception:
        pass
    return lines


def _dynamic_block(npc, character):
    """Block 3: per-conversation context — current location, the
    player's identity/pronouns, the NPC's memory of this player, and
    live quest state. Changes often; never cached."""
    parts = []
    speaker_name = npc.key or "you"
    player_name = getattr(character, "key", None) if character else None

    # ── Where the NPC currently IS ───────────────────────────────────
    # Without this, walk-in companions like First Mate Nosaj keep
    # behaving as if they're still on the doomed ship even after the
    # player has dragged them ashore at Tamris Harbor. The LLM has no
    # awareness of motion unless we tell it the present location.
    try:
        loc = getattr(npc, "location", None)
        if loc:
            loc_key = getattr(loc, "key", "") or "Somewhere"
            loc_desc = (getattr(loc.db, "desc", "") or "")[:280]
            parts.extend([
                "YOUR CURRENT LOCATION:",
                f"  {loc_key}",
                f"  ({loc_desc.strip()})" if loc_desc else "",
                "  React to where you actually are now. If you've "
                "travelled with the bearer to a new location, the past "
                "(the ship, the road, the cell) is behind you — speak "
                "to the present, not the journey that brought you here.",
            ])
    except Exception:
        pass

    if character is not None:
        # Player profile — gender + pronouns the NPC should use when
        # referring to the player in the third person.
        try:
            from commands.command import pronouns_for
            pron = pronouns_for(character)
            player_gender = (getattr(character.db, "gender", None)
                             or "unset").lower()
            parts.append("")
            parts.append("THE PLAYER YOU ARE SPEAKING WITH:")
            parts.append(
                f"  Name: {character.key}\n"
                f"  Gender: {player_gender}\n"
                f"  Pronouns: {pron['subj']}/{pron['obj']}/{pron['poss']} "
                f"(use these when referring to {character.key} in the "
                f"third person)."
            )
        except Exception:
            pass

        # Personal memory of THIS player — read from char.db.npc_rep by
        # this NPC's lowercase key.
        try:
            npc_rep = getattr(character.db, "npc_rep", None) or {}
            entry = npc_rep.get((npc.key or "").lower())
            if entry:
                score = int(entry.get("rep", 0) or 0)
                mems = [m for m in (entry.get("memories") or []) if m]
                parts.append("")
                parts.append(f"WHAT YOU REMEMBER OF {character.key}:")
                parts.append(
                    f"  Personal regard: {score:+d} "
                    f"({'friend' if score > 0 else 'enemy' if score < 0 else 'known'})."
                )
                if mems:
                    parts.append("  Specific memories:")
                    for m in mems[-5:]:
                        parts.append(f"    - {m}")
                parts.append(
                    "  Speak to this person with that history in mind — warmth, "
                    "coolness, or suspicion as fits. Do NOT explicitly quote a "
                    "rep number; just let it colour your tone."
                )
        except Exception:
            pass

        # Live quest state involving this NPC.
        parts.extend(_quest_state_lines(npc, character))

    if player_name:
        parts.append("")
        parts.append(
            f"REMINDER: the player's character is named "
            f"'{player_name}'. You may have {speaker_name} address "
            f"{player_name} by name inside spoken dialogue, but NEVER "
            f"narrate {player_name}'s actions, words, feelings, or "
            f"thoughts — do not write '{player_name} nods' or "
            f"'{player_name}'s expression turns somber'."
        )

    return "\n".join(p for p in parts if p is not None)


def _build_prompt_blocks(npc, character=None):
    """Return (static, npc_block, dynamic) prompt strings."""
    # scope controls how much lore this NPC knows. Information flows
    # poorly across the Mists, so Arnesse-side NPCs get rumor-level
    # Annwyn knowledge only. Default "gateway" — safer than leaking
    # interior info.
    scope = npc.attributes.get("ai_scope", default=None) or "gateway"
    return (
        _static_block(scope),
        _npc_block(npc),
        _dynamic_block(npc, character),
    )


def _build_system_prompt(npc, character=None):
    """Flat single-string system prompt (openai path + tests)."""
    return "\n\n".join(b for b in _build_prompt_blocks(npc, character) if b)


def _get_history(npc, character):
    """Return the last N conversation turns as plain Python dicts.

    Evennia wraps stored lists/dicts in _SaverList/_SaverDict to track
    mutations. json.dumps() can't serialize those, so we deep-convert
    back to plain dicts here before the history is sent to the LLM API.
    """
    convos = npc.attributes.get("ai_conversations", default=None) or {}
    raw = convos.get(str(character.id), []) or []
    out = []
    for item in raw:
        try:
            # dict(_SaverDict(...)) unwraps one level; rebuild content
            # as a plain string in case it's a _SaverStr or similar.
            out.append({
                "role": str(item.get("role", "user")),
                "content": str(item.get("content", "")),
            })
        except Exception:
            # Best-effort fallback — skip malformed history entries
            continue
    return out


def _save_history(npc, character, user_msg, assistant_msg):
    # Unwrap Evennia's _SaverDict/_SaverList to plain Python structures
    # so subsequent json.dumps calls won't choke on the wrapper types.
    raw_convos = npc.attributes.get("ai_conversations", default=None) or {}
    convos = {str(k): list(v) for k, v in dict(raw_convos).items()}
    key = str(character.id)
    turns = [
        {"role": str(t.get("role", "user")), "content": str(t.get("content", ""))}
        for t in convos.get(key, [])
    ]
    turns.append({"role": "user", "content": str(user_msg)})
    turns.append({"role": "assistant", "content": str(assistant_msg)})
    turns = turns[-(HISTORY_TURNS * 2):]
    convos[key] = turns
    npc.attributes.add("ai_conversations", convos)


def reset_history(npc, character):
    """Forget the NPC's conversation with a specific character."""
    convos = npc.attributes.get("ai_conversations", default=None) or {}
    key = str(character.id)
    if key in convos:
        del convos[key]
        npc.attributes.add("ai_conversations", convos)


def _rate_check(npc, character):
    """Per-character hourly rate limit. Returns (allowed, retry_minutes)."""
    state = npc.attributes.get("ai_rate_state", default=None) or {}
    key = str(character.id)
    now = time.time()
    hits = [t for t in state.get(key, []) if now - t < RATE_LIMIT_WINDOW]
    if len(hits) >= RATE_LIMIT_MSGS:
        retry = int((RATE_LIMIT_WINDOW - (now - hits[0])) / 60) + 1
        return False, retry
    hits.append(now)
    state[key] = hits
    npc.attributes.add("ai_rate_state", state)
    return True, 0


# ───────────────────────────────────────────────────────────────────────────
# LLM calls
# ───────────────────────────────────────────────────────────────────────────
_ANTH_CLIENT = None
_ANTH_CLIENT_LOCK = threading.Lock()


def _anthropic_client():
    global _ANTH_CLIENT
    with _ANTH_CLIENT_LOCK:
        if _ANTH_CLIENT is None:
            import anthropic
            _ANTH_CLIENT = anthropic.Anthropic(
                api_key=_env("NPC_LLM_API_KEY"),
                timeout=float(_env("NPC_LLM_TIMEOUT", DEFAULT_TIMEOUT)),
                max_retries=1,
            )
        return _ANTH_CLIENT


def _call_anthropic(npc, character, message):
    """Claude path with prompt caching. Cache breakpoints close the
    world-bible block and the per-NPC block; the dynamic block and
    conversation history stay uncached (they change every call)."""
    static, npc_block, dynamic = _build_prompt_blocks(npc, character=character)
    system = [
        {"type": "text", "text": static,
         "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": npc_block,
         "cache_control": {"type": "ephemeral"}},
    ]
    if dynamic:
        system.append({"type": "text", "text": dynamic})

    messages = list(_get_history(npc, character))
    messages.append({
        "role": "user",
        "content": f"[{character.key}, in-character] {message}",
    })

    client = _anthropic_client()
    resp = client.messages.create(
        model=_model(),
        max_tokens=int(_env("NPC_LLM_MAX_TOKENS", DEFAULT_MAX_TOKENS)),
        temperature=0.85,
        system=system,
        messages=messages,
    )
    reply = "".join(
        block.text for block in resp.content if block.type == "text"
    ).strip()

    # Spend tracking + cache visibility.
    try:
        u = resp.usage
        cache_w = getattr(u, "cache_creation_input_tokens", 0) or 0
        cache_r = getattr(u, "cache_read_input_tokens", 0) or 0
        usd = (
            u.input_tokens * _PRICE_IN
            + u.output_tokens * _PRICE_OUT
            + cache_w * _PRICE_CACHE_WRITE
            + cache_r * _PRICE_CACHE_READ
        ) / 1_000_000
        _record_spend(usd)
        from world import telemetry
        telemetry.incr("llm.calls")
        telemetry.incr("llm.input_tokens", u.input_tokens)
        telemetry.incr("llm.output_tokens", u.output_tokens)
        telemetry.incr("llm.cache_read_tokens", cache_r)
        telemetry.incr("llm.cache_write_tokens", cache_w)
        print(
            f"[ai_npc] anthropic ok model={resp.model} "
            f"in={u.input_tokens} out={u.output_tokens} "
            f"cache_write={cache_w} cache_read={cache_r} "
            f"~${usd:.4f} (day ${_SPEND['usd']:.2f})",
            flush=True,
        )
    except Exception:
        pass
    return reply


def _call_openai(npc, character, message):
    """Legacy OpenAI-compatible path (Groq etc.) via raw HTTP."""
    system_prompt = _build_system_prompt(npc, character=character)
    history = _get_history(npc, character)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    # Tag the incoming message with who is speaking, so the model knows.
    speaker = character.key
    messages.append({
        "role": "user",
        "content": f"[{speaker}, in-character] {message}",
    })

    base_url = _env("NPC_LLM_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    url = f"{base_url}/chat/completions"
    payload = {
        "model": _model(),
        "messages": messages,
        "max_tokens": int(_env("NPC_LLM_MAX_TOKENS", DEFAULT_MAX_TOKENS)),
        "temperature": 0.85,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_env('NPC_LLM_API_KEY')}",
            "User-Agent": "EldritchMUSH/1.0",
        },
    )
    timeout = int(_env("NPC_LLM_TIMEOUT", DEFAULT_TIMEOUT))
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    reply = data["choices"][0]["message"]["content"].strip()
    try:
        usage = data.get("usage") or {}
        total = (usage.get("prompt_tokens") or 0) + (usage.get("completion_tokens") or 0)
        _record_spend(total * _OPENAI_FLAT_PRICE / 1_000_000)
        from world import telemetry
        telemetry.incr("llm.calls")
        telemetry.incr("llm.input_tokens", usage.get("prompt_tokens") or 0)
        telemetry.incr("llm.output_tokens", usage.get("completion_tokens") or 0)
    except Exception:
        pass
    return reply


def _call_llm(npc, character, message):
    """Synchronous LLM call. Returns the reply text or raises."""
    if _provider() == "anthropic":
        reply = _call_anthropic(npc, character, message)
    else:
        reply = _call_openai(npc, character, message)
    # Strip any leading "Name:" the model may have added despite instructions.
    prefix = f"{npc.key}:"
    if reply.lower().startswith(prefix.lower()):
        reply = reply[len(prefix):].strip()
    # Strip surrounding quotes if the whole reply is quoted.
    if len(reply) > 1 and reply[0] in '"“' and reply[-1] in '"”':
        reply = reply[1:-1].strip()
    return reply


def _generate_anthropic(system_text, user_text, max_tokens, temperature):
    client = _anthropic_client()
    resp = client.messages.create(
        model=_model(),
        max_tokens=max_tokens,
        temperature=temperature,
        system=[{"type": "text", "text": system_text,
                 "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_text}],
    )
    text = "".join(
        block.text for block in resp.content if block.type == "text"
    ).strip()
    try:
        u = resp.usage
        cache_w = getattr(u, "cache_creation_input_tokens", 0) or 0
        cache_r = getattr(u, "cache_read_input_tokens", 0) or 0
        usd = (
            u.input_tokens * _PRICE_IN
            + u.output_tokens * _PRICE_OUT
            + cache_w * _PRICE_CACHE_WRITE
            + cache_r * _PRICE_CACHE_READ
        ) / 1_000_000
        _record_spend(usd)
        from world import telemetry
        telemetry.incr("llm.calls")
        telemetry.incr("llm.generate_calls")
        telemetry.incr("llm.input_tokens", u.input_tokens)
        telemetry.incr("llm.output_tokens", u.output_tokens)
    except Exception:
        pass
    return text


def _generate_openai(system_text, user_text, max_tokens, temperature):
    base_url = _env("NPC_LLM_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    url = f"{base_url}/chat/completions"
    payload = {
        "model": _model(),
        "messages": [
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_env('NPC_LLM_API_KEY')}",
            "User-Agent": "EldritchMUSH/1.0",
        },
    )
    timeout = int(_env("NPC_LLM_TIMEOUT", DEFAULT_TIMEOUT))
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = data["choices"][0]["message"]["content"].strip()
    try:
        usage = data.get("usage") or {}
        total = (usage.get("prompt_tokens") or 0) + (usage.get("completion_tokens") or 0)
        _record_spend(total * _OPENAI_FLAT_PRICE / 1_000_000)
        from world import telemetry
        telemetry.incr("llm.calls")
        telemetry.incr("llm.generate_calls")
    except Exception:
        pass
    return text


def generate_sync(system_text, user_text, max_tokens=400, temperature=0.9):
    """Generic spend-capped completion for world systems (gossip
    distortion, fae letters, fortunes, dreams, the chronicle).

    Shares the provider switch, daily spend kill-switch, and telemetry
    with NPC chat. Returns the generated text, or None when the LLM is
    disabled, over budget, or errors — callers MUST handle None with a
    non-LLM fallback. Synchronous: never call from the reactor thread;
    use generate() for that.
    """
    if not _enabled() or not _spend_ok():
        return None
    try:
        if _provider() == "anthropic":
            return _generate_anthropic(
                system_text, user_text, max_tokens, temperature)
        return _generate_openai(
            system_text, user_text, max_tokens, temperature)
    except Exception as exc:
        try:
            from world import telemetry
            telemetry.incr("llm.errors")
        except Exception:
            pass
        print(f"[ai_npc.generate] err: {type(exc).__name__}: {exc}",
              flush=True)
        return None


def generate(system_text, user_text, on_reply, max_tokens=400,
             temperature=0.9):
    """Non-blocking wrapper around generate_sync. on_reply(text_or_None)
    runs on the reactor thread, so Evennia state access is safe inside it."""
    def _run():
        result = generate_sync(
            system_text, user_text,
            max_tokens=max_tokens, temperature=temperature)
        _dispatch(on_reply, result)
    _EXECUTOR.submit(_run)


def chat(npc, character, message, on_reply):
    """Kick off a non-blocking LLM request.

    on_reply(text) is scheduled to run on Twisted's reactor thread once
    the request completes, so it's safe to call Evennia msg/search/etc.
    from within it.
    """
    from world import ai_safety

    # Truncate abusively long messages up front. Long inputs are either
    # typos, pasted junk, or attempts to flood context with injection
    # attempts. Cap and move on.
    clean_msg = str(message or "")[:MAX_USER_MESSAGE].strip()
    if not clean_msg:
        _dispatch(on_reply, _fallback_line(npc))
        return

    # Defense layer 1: banned-phrase filter. Synchronous, regex-only,
    # no API call. Runs BEFORE we queue the work to save latency.
    from world import telemetry
    telemetry.incr("npc.chat_requests")

    banned_hit = ai_safety.check_banned(clean_msg)
    if banned_hit:
        telemetry.incr("safety.banned_phrase")
        refusal = ai_safety.canned_refusal(npc)
        ai_safety.audit_log(
            npc, character, clean_msg, refusal,
            flags=["banned_phrase", f"match:{banned_hit[:40]}"]
        )
        _dispatch(on_reply, refusal)
        return

    # Defense layer 2: per-account global rate limit. Stacks on the
    # per-char-per-NPC limit below.
    account = getattr(character, "account", None)
    acct_ok, acct_retry = ai_safety.check_account_rate(account)
    if not acct_ok:
        telemetry.incr("safety.rate_limited_account")
        msg = (f"|y({npc.key} looks at you, then the door, then you again. "
               f"\"You've been jawing the ear off every soul in Gateway today. "
               f"Come back in about {acct_retry} minutes, bearer.\")|n")
        ai_safety.audit_log(
            npc, character, clean_msg, msg, flags=["rate_limited_account"]
        )
        _dispatch(on_reply, msg)
        return

    # Defense layer 2b: daily spend kill-switch.
    if not _spend_ok():
        telemetry.incr("llm.budget_blocked")
        reply = _fallback_line(npc)
        ai_safety.audit_log(
            npc, character, clean_msg, reply, flags=["budget_exhausted"]
        )
        _dispatch(on_reply, reply)
        return

    print(
        f"[ai_npc.chat] start npc={getattr(npc,'key','?')!r} "
        f"char={getattr(character,'key','?')!r} msg_len={len(clean_msg)} "
        f"provider={_provider()}",
        flush=True,
    )

    def _run():
        try:
            if not _enabled():
                reply = _fallback_line(npc)
                ai_safety.audit_log(
                    npc, character, clean_msg, reply, flags=["llm_disabled"]
                )
                _dispatch(on_reply, reply)
                return

            # Serialize per-NPC: protects ai_conversations / ai_rate_state
            # read-modify-write when several players talk to the same NPC
            # at once. Different NPCs still run in parallel.
            with _npc_lock(npc):
                allowed, retry = _rate_check(npc, character)
                if not allowed:
                    msg = (f"|y({npc.key} has had enough of talk for now. "
                           f"Try again in about {retry} minute(s).)|n")
                    ai_safety.audit_log(
                        npc, character, clean_msg, msg,
                        flags=["rate_limited_char_npc"]
                    )
                    _dispatch(on_reply, msg)
                    return

                # Defense layer 3: Llama Guard moderation (optional, gated
                # by NPC_LLM_MODERATE=1). Extra API call but catches hate /
                # violence / sexual content before the main LLM even sees it.
                mod_ok, mod_cat = ai_safety.check_moderation(clean_msg)
                if not mod_ok:
                    refusal = ai_safety.canned_refusal(npc)
                    ai_safety.audit_log(
                        npc, character, clean_msg, refusal,
                        flags=["moderated_input", f"category:{mod_cat}"]
                    )
                    _dispatch(on_reply, refusal)
                    return

                reply = _call_llm(npc, character, clean_msg)
                _save_history(npc, character, clean_msg, reply)
            ai_safety.audit_log(npc, character, clean_msg, reply, flags=[])
            _dispatch(on_reply, reply)
        except urllib.error.HTTPError as exc:
            try:
                body = exc.read().decode("utf-8")[:200]
            except Exception:
                body = ""
            # The HTTP error body (rate-limit JSON, etc.) is for the
            # audit log only — the player sees just the canned fallback
            # line. Nothing about LLM internals leaks into the modal.
            fallback = _fallback_line(npc)
            telemetry.incr("llm.errors")
            print(f"[ai_npc] LLM HTTP {exc.code}: {body}", flush=True)
            try:
                ai_safety.audit_log(
                    npc, character, clean_msg,
                    f"{fallback} (LLM HTTP {exc.code}: {body})",
                    flags=[f"llm_http_error:{exc.code}"]
                )
            except Exception:
                pass
            _dispatch(on_reply, fallback)
        except Exception as exc:
            fallback = _fallback_line(npc)
            telemetry.incr("llm.errors")
            print(f"[ai_npc] LLM err: {type(exc).__name__}: {exc}", flush=True)
            try:
                ai_safety.audit_log(
                    npc, character, clean_msg,
                    f"{fallback} (LLM err: {type(exc).__name__}: {exc})",
                    flags=[f"llm_error:{type(exc).__name__}"]
                )
            except Exception:
                pass
            _dispatch(on_reply, fallback)

    _EXECUTOR.submit(_run)


def _dispatch(fn, *args):
    """Run fn on Twisted's reactor thread, so Evennia state access is safe."""
    try:
        from twisted.internet import reactor
        reactor.callFromThread(fn, *args)
        print(f"[ai_npc._dispatch] scheduled callback", flush=True)
    except Exception as exc:
        print(f"[ai_npc._dispatch] reactor unavailable, calling inline: {exc!r}", flush=True)
        # Fallback: call inline if reactor is unavailable (e.g. test env).
        fn(*args)
