"""
AI-driven NPC dialogue via an OpenAI-compatible LLM endpoint.

NPCs in the game world can hold in-character conversations with players
through an LLM. The provider is configured via env vars, defaulting to
Groq (free tier) running Kimi K2.

Env vars:
    NPC_LLM_ENABLED   — "1" (default) to enable; "0" disables all AI calls.
    NPC_LLM_API_KEY   — bearer token. Required; if absent, NPCs fall back
                        to canned atmospheric lines.
    NPC_LLM_BASE_URL  — default "https://api.groq.com/openai/v1"
    NPC_LLM_MODEL     — default "moonshotai/kimi-k2-instruct"
    NPC_LLM_MAX_TOKENS— default 220
    NPC_LLM_TIMEOUT   — default 20 (seconds)

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


DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "moonshotai/kimi-k2-instruct"
DEFAULT_MAX_TOKENS = 320          # enough for lore-heavy answers w/o runaway
DEFAULT_TIMEOUT = 20

HISTORY_TURNS = 8           # retained user+assistant exchanges per character
RATE_LIMIT_MSGS = 30        # max messages
RATE_LIMIT_WINDOW = 3600    # per 3600 seconds (1 hour)
MAX_USER_MESSAGE = 600      # chars — caps prompt-injection / context abuse

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


def _fallback_line(npc):
    return random.choice(CANNED_FALLBACKS).format(name=npc.key)


def _build_system_prompt(npc, character=None):
    """Compose the NPC's system prompt from:
       1) the shared canonical world bible (world/ai_lore.py), which ALL
          NPCs share, so no one hallucinates house/faction/geography.
       2) the NPC's personal `ai_personality` — voice, mood, manner.
       3) the NPC's personal `ai_knowledge` — what THIS person knows
          beyond the shared canon (secrets, opinions, local facts).
       4) optional quest hooks.
       5) if `character` is supplied, the NPC's memory of THAT player
          (rep score + memory tags from char.db.npc_rep), so the LLM
          can greet known faces differently from strangers.
    """
    from world import ai_lore

    personality = npc.attributes.get("ai_personality", default=None) or ""
    knowledge = npc.attributes.get("ai_knowledge", default=None) or ""
    quests = npc.attributes.get("ai_quest_hooks", default=None) or []
    # scope controls how much lore this NPC knows. Information flows
    # poorly across the Mists, so Arnesse-side NPCs get rumor-level
    # Annwyn knowledge only. Default "gateway" — safer than leaking
    # interior info.
    scope = npc.attributes.get("ai_scope", default=None) or "gateway"

    parts = [
        ai_lore.get_world_bible(scope=scope),
        "",
        f"=== YOU ARE: {npc.key} ===",
    ]

    if personality:
        parts.extend(["", "VOICE & MANNER:", personality.strip()])
    if knowledge:
        parts.extend([
            "",
            "WHAT YOU PERSONALLY KNOW (beyond the shared world canon):",
            knowledge.strip(),
        ])
    if quests:
        parts.append("")
        parts.append("QUEST HOOKS YOU MAY OFFER WHEN APPROPRIATE:")
        for q in quests:
            parts.append(f"- {q}")

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

    # Personal memory of THIS player — read from char.db.npc_rep by
    # this NPC's lowercase key. Gives the LLM grounding for how to
    # greet known characters.
    if character is not None:
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
            "give at most one item per reply."
        )
        parts.append("Items you can give:")
        for g in giftable:
            parts.append(f"  - {g}")
        parts.append(
            "Example: 'Here, take this. *slides the bundle across "
            "the table*\\n[GIVE: WOLF_PELT]'"
        )

    return "\n".join(parts)


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


def _call_llm(npc, character, message):
    """Synchronous LLM call. Returns the reply text or raises."""
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
        "model": _env("NPC_LLM_MODEL", DEFAULT_MODEL),
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
    # Strip any leading "Name:" the model may have added despite instructions.
    prefix = f"{npc.key}:"
    if reply.lower().startswith(prefix.lower()):
        reply = reply[len(prefix):].strip()
    # Strip surrounding quotes if the whole reply is quoted.
    if len(reply) > 1 and reply[0] in '"“' and reply[-1] in '"”':
        reply = reply[1:-1].strip()
    return reply


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
    # no API call. Runs BEFORE we spin up the thread to save latency.
    banned_hit = ai_safety.check_banned(clean_msg)
    if banned_hit:
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
        msg = (f"|y({npc.key} looks at you, then the door, then you again. "
               f"\"You've been jawing the ear off every soul in Gateway today. "
               f"Come back in about {acct_retry} minutes, bearer.\")|n")
        ai_safety.audit_log(
            npc, character, clean_msg, msg, flags=["rate_limited_account"]
        )
        _dispatch(on_reply, msg)
        return

    def _run():
        try:
            if not _enabled():
                reply = _fallback_line(npc)
                ai_safety.audit_log(
                    npc, character, clean_msg, reply, flags=["llm_disabled"]
                )
                _dispatch(on_reply, reply)
                return

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
            fallback = _fallback_line(npc)
            msg = f"{fallback} |y(LLM HTTP {exc.code}: {body})|n"
            try:
                ai_safety.audit_log(
                    npc, character, clean_msg, msg,
                    flags=[f"llm_http_error:{exc.code}"]
                )
            except Exception:
                pass
            _dispatch(on_reply, msg)
        except Exception as exc:
            fallback = _fallback_line(npc)
            msg = f"{fallback} |y(LLM err: {type(exc).__name__}: {exc})|n"
            try:
                ai_safety.audit_log(
                    npc, character, clean_msg, msg,
                    flags=[f"llm_error:{type(exc).__name__}"]
                )
            except Exception:
                pass
            _dispatch(on_reply, msg)

    threading.Thread(target=_run, daemon=True).start()


def _dispatch(fn, *args):
    """Run fn on Twisted's reactor thread, so Evennia state access is safe."""
    try:
        from twisted.internet import reactor
        reactor.callFromThread(fn, *args)
    except Exception:
        # Fallback: call inline if reactor is unavailable (e.g. test env).
        fn(*args)
