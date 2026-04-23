"""
Quest system commands for EldritchMUSH.

Commands
--------
  quest / quests / q  — list your active and available quests
  quest <title>       — show detail for a specific quest
  quest accept <title>— accept an available quest from a nearby NPC giver
  quest abandon <id>  — drop an active quest (no penalty)

Data model (stored on character db)
------------------------------------
  self.db.quests = {
      "<quest_key>": {
          "status": "active" | "completed" | "failed",
          "objectives": [
              {"type": ..., "target": ..., "qty": N, "current": 0, "desc": "..."},
              ...
          ],
          "outcome": "<outcome_key>",  # present only for branching quests
      },
      ...
  }

Branching quests
----------------
A quest may have an `outcomes` dict in its definition instead of
top-level `objectives` + `rewards`. The player picks one outcome when
accepting the quest (e.g. `quest accept Ship / pocket_it`). Only that
outcome's objectives are tracked; only that outcome's rewards + faction_rep
apply on completion.

Faction rep lives at `self.db.faction_rep` and is a dict of int deltas
(e.g. {"crown": 3, "cirque": -2}).

Quest logic integration
-----------------------
  Progress is ticked by calling quest_progress(caller, type, target) from
  combat/gather hooks.  Completion is checked after every tick.

"""

from evennia import Command
from world.quest_data import QUESTS


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_quest_db(char):
    """Ensure character has a quests dict. Safe to call repeatedly."""
    if not char.db.quests:
        char.db.quests = {}


def _get_quest_state(char, key):
    """Return the character's quest state dict for *key*, or None."""
    _ensure_quest_db(char)
    return char.db.quests.get(key)


def _has_outcomes(quest_def):
    """True if quest uses branching outcomes."""
    return bool(quest_def.get("outcomes"))


def _quest_outcome_def(quest_def, outcome_key):
    """Return the outcome dict for outcome_key, or None."""
    return (quest_def.get("outcomes") or {}).get(outcome_key)


def _effective_objectives_src(quest_def, outcome_key=None):
    """Return the objectives list for the (quest, outcome) pair."""
    if _has_outcomes(quest_def):
        outcome = _quest_outcome_def(quest_def, outcome_key)
        return (outcome or {}).get("objectives", [])
    return quest_def.get("objectives", [])


def _effective_rewards(quest_def, outcome_key=None):
    """Return the rewards dict for the (quest, outcome) pair."""
    if _has_outcomes(quest_def):
        outcome = _quest_outcome_def(quest_def, outcome_key)
        return (outcome or {}).get("rewards", {})
    return quest_def.get("rewards", {})


def _effective_faction_rep(quest_def, outcome_key=None):
    """Faction rep deltas to apply on completion. Only defined for outcomes."""
    if _has_outcomes(quest_def):
        outcome = _quest_outcome_def(quest_def, outcome_key)
        return (outcome or {}).get("faction_rep", {})
    return {}


def _fresh_objectives(quest_def, outcome_key=None):
    """Return a deep-copied list of objective dicts with current=0."""
    return [
        {
            "type": obj["type"],
            "target": obj["target"],
            "qty": obj["qty"],
            "current": 0,
            "desc": obj["desc"],
        }
        for obj in _effective_objectives_src(quest_def, outcome_key)
    ]


def _prerequisites_met(char, quest_def):
    """Return True if all prereqs are met. Prereqs may be strings (quest keys)
    or dicts of form {"quest": key, "outcome": outcome_key} to require a
    specific outcome."""
    _ensure_quest_db(char)
    for prereq in quest_def.get("prereqs", []):
        if isinstance(prereq, dict):
            q_key = prereq["quest"]
            want_outcome = prereq.get("outcome")
            state = char.db.quests.get(q_key)
            if not state or state["status"] != "completed":
                return False
            if want_outcome and state.get("outcome") != want_outcome:
                return False
        else:
            state = char.db.quests.get(prereq)
            if not state or state["status"] != "completed":
                return False
    return True


def _available_quests(char):
    """Return list of quest defs the character can accept (not yet started, prereqs met)."""
    _ensure_quest_db(char)
    result = []
    for key, qdef in QUESTS.items():
        if key in char.db.quests:
            continue  # already started or completed
        if _prerequisites_met(char, qdef):
            result.append(qdef)
    return result


def _active_quests(char):
    """Return list of (quest_def, state) tuples for active quests."""
    _ensure_quest_db(char)
    result = []
    for key, state in char.db.quests.items():
        if state["status"] == "active" and key in QUESTS:
            result.append((QUESTS[key], state))
    return result


def _completed_quests(char):
    """Return list of quest_defs for completed quests."""
    _ensure_quest_db(char)
    result = []
    for key, state in char.db.quests.items():
        if state["status"] == "completed" and key in QUESTS:
            result.append(QUESTS[key])
    return result


def _check_completion(char, key):
    """
    Check if all objectives for *key* are done.  If so, grant rewards and
    mark completed.  Returns True if the quest just completed.
    """
    state = _get_quest_state(char, key)
    if not state or state["status"] != "active":
        return False

    qdef = QUESTS.get(key)
    if not qdef:
        return False

    for obj in state["objectives"]:
        if obj["current"] < obj["qty"]:
            return False

    # All objectives met — complete the quest
    state["status"] = "completed"
    char.db.quests[key] = state

    outcome_key = state.get("outcome")
    char.msg(f"\n|y✦ Quest Complete: |w{qdef['title']}|n")
    if outcome_key:
        outcome_def = _quest_outcome_def(qdef, outcome_key) or {}
        outcome_label = outcome_def.get("label", outcome_key)
        char.msg(f"|540Outcome: |w{outcome_label}|n")

    # Grant rewards (per-outcome if branching)
    rewards = _effective_rewards(qdef, outcome_key)
    silver = rewards.get("silver", 0)
    items_spawned = []
    reagents_granted = False
    if silver:
        char.db.silver = (char.db.silver or 0) + silver
        char.msg(f"|yReward: |w+{silver} silver|n")

    for proto_key in rewards.get("items", []):
        try:
            from evennia import spawn
            items = spawn(proto_key)
            if items:
                items[0].move_to(char, quiet=True)
                items_spawned.append(items[0])
                char.msg(f"|yReward: |w{items[0].key}|n added to inventory.")
                # Fire item_received so the ItemReceivedToast slides in.
                try:
                    from world.npc_gifts import announce_item_drop
                    announce_item_drop(char, items[0],
                                       from_source_name="Quest Reward")
                except Exception:
                    pass
        except Exception:
            pass

    for reagent, qty in rewards.get("reagents", {}).items():
        if not char.db.reagents:
            char.db.reagents = {}
        char.db.reagents[reagent] = char.db.reagents.get(reagent, 0) + qty
        reagents_granted = True
        char.msg(f"|yReward: |w+{qty} {reagent}|n (reagent)")

    # Refresh the web UI sidebar — silver updates the purse display,
    # spawned items update the inventory panel. Without these, the
    # player sees the chat confirmations but the stat/inventory widgets
    # stay stale until the next unrelated refresh.
    if silver or reagents_granted:
        try:
            from world.character_stats import push_character_stats
            push_character_stats(char)
        except Exception:
            pass
    if items_spawned:
        try:
            from world.inventory_oob import push_inventory
            push_inventory(char)
        except Exception:
            pass

    # Apply faction rep deltas (only defined for branching outcomes)
    rep_deltas = _effective_faction_rep(qdef, outcome_key)
    if rep_deltas:
        if not char.db.faction_rep:
            char.db.faction_rep = {}
        for faction, delta in rep_deltas.items():
            before = char.db.faction_rep.get(faction, 0)
            after = before + delta
            char.db.faction_rep[faction] = after
            sign = "|g+" if delta >= 0 else "|r"
            char.msg(f"|540Reputation: {sign}{delta}|n |w{faction.title()}|n "
                     f"|540(now {after})|n")

    # Fire a quest_completed OOB event so the frontend can toast the
    # full summary (title, outcome label, rewards line, rep deltas).
    # Item rewards already fired item_received above for per-item toasts.
    try:
        import time as _time
        outcome_label = None
        if outcome_key:
            odef = _quest_outcome_def(qdef, outcome_key) or {}
            outcome_label = odef.get("label", outcome_key)
        payload = {
            "type": "quest_completed",
            "_ts": _time.time(),
            "key": key,
            "title": qdef["title"],
            "outcome": outcome_key,
            "outcomeLabel": outcome_label,
            "silver": silver or 0,
            "items": [it.key for it in items_spawned],
            "reagents": dict(rewards.get("reagents") or {}),
            "factionRep": dict(rep_deltas or {}),
        }
        for sess in char.sessions.all():
            sess.msg(event=payload)
    except Exception:
        pass

    return True


# ─────────────────────────────────────────────────────────────────────────────
# Public API — called from combat / gather hooks
# ─────────────────────────────────────────────────────────────────────────────

def quest_kill(char, npc_key):
    """
    Call this when *char* kills an NPC with key *npc_key*.
    Ticks any matching 'kill' objectives on active quests.
    """
    _ensure_quest_db(char)
    npc_key_lower = npc_key.lower()
    for key, state in char.db.quests.items():
        if state["status"] != "active":
            continue
        for obj in state["objectives"]:
            if obj["type"] == "kill" and obj["target"].lower() in npc_key_lower:
                if obj["current"] < obj["qty"]:
                    obj["current"] += 1
                    remaining = obj["qty"] - obj["current"]
                    char.msg(
                        f"|540[Quest] {obj['desc'].split('(')[0].strip()} "
                        f"({obj['current']}/{obj['qty']})|n"
                    )
                    _check_completion(char, key)


def quest_gather(char, item_name, qty=1):
    """
    Call this when *char* picks up / delivers *item_name*.
    Ticks matching 'gather' objectives.
    """
    _ensure_quest_db(char)
    item_lower = item_name.lower()
    for key, state in char.db.quests.items():
        if state["status"] != "active":
            continue
        for obj in state["objectives"]:
            if obj["type"] == "gather" and obj["target"].lower() in item_lower:
                before = obj["current"]
                obj["current"] = min(obj["current"] + qty, obj["qty"])
                gained = obj["current"] - before
                if gained > 0:
                    char.msg(
                        f"|540[Quest] {obj['desc'].split('(')[0].strip()} "
                        f"({obj['current']}/{obj['qty']})|n"
                    )
                    _check_completion(char, key)


def quest_duel_win(char, npc_key):
    """
    Call this when *char* wins a wagered duel against an NPC with
    key *npc_key*. Ticks matching 'duel' objectives.
    """
    _ensure_quest_db(char)
    npc_key_lower = npc_key.lower()
    for key, state in char.db.quests.items():
        if state["status"] != "active":
            continue
        for obj in state["objectives"]:
            if obj["type"] == "duel" and obj["target"].lower() in npc_key_lower:
                if obj["current"] < obj["qty"]:
                    obj["current"] += 1
                    char.msg(
                        f"|540[Quest] {obj['desc'].split('(')[0].strip()} "
                        f"({obj['current']}/{obj['qty']})|n"
                    )
                    _check_completion(char, key)


def quest_deliver(char, item_name, npc_key):
    """
    Call this when *char* gives *item_name* to an NPC with key *npc_key*.
    Ticks matching 'deliver' objectives.  A deliver objective's `target` is
    the NPC key; the item is implicit (the player must have been carrying it
    to give it). Completes immediately (deliver is binary).
    """
    _ensure_quest_db(char)
    npc_key_lower = npc_key.lower()
    for key, state in char.db.quests.items():
        if state["status"] != "active":
            continue
        for obj in state["objectives"]:
            if obj["type"] == "deliver" and obj["target"].lower() in npc_key_lower:
                if obj["current"] < obj["qty"]:
                    obj["current"] = obj["qty"]
                    char.msg(
                        f"|540[Quest] {obj['desc'].split('(')[0].strip()} "
                        f"({obj['current']}/{obj['qty']})|n"
                    )
                    _check_completion(char, key)


def quest_explore(char, room_name):
    """
    Call this when *char* enters a room with the given name.
    Ticks matching 'explore' objectives.
    """
    _ensure_quest_db(char)
    room_lower = room_name.lower()
    for key, state in char.db.quests.items():
        if state["status"] != "active":
            continue
        for obj in state["objectives"]:
            if obj["type"] == "explore" and obj["target"].lower() in room_lower:
                if obj["current"] < obj["qty"]:
                    obj["current"] = obj["qty"]  # explore is binary
                    char.msg(f"|540[Quest] Discovered: {obj['target']}|n")
                    _check_completion(char, key)


# ─────────────────────────────────────────────────────────────────────────────
# CmdQuest
# ─────────────────────────────────────────────────────────────────────────────

class CmdQuest(Command):
    """
    View and manage your quests.

    Usage:
      quest                    - list active quests and available quests nearby
      quest <title or key>     - show detail for a specific quest
      quest accept <title>     - accept an available quest
      quest abandon <title>    - drop an active quest (no penalty)

    Examples:
      quest
      quest Clear the Old Road
      quest accept Clear the Old Road
      quest abandon wolf_problem

    Quests are offered by NPCs around the world.  When you're near a quest
    giver, their available quests appear in the |wavailable|n section.
    Complete all objectives to earn your reward automatically.
    """

    key = "quest"
    aliases = ["quests", "q"]
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            self._show_journal(caller)
            return

        # "quest accept <title>"
        if args.lower().startswith("accept "):
            title = args[7:].strip()
            self._accept_quest(caller, title)
            return

        # "quest abandon <title or key>"
        if args.lower().startswith("abandon "):
            title = args[8:].strip()
            self._abandon_quest(caller, title)
            return

        # "quest <title>" — show detail
        self._show_quest_detail(caller, args)

    # ── Display helpers ──────────────────────────────────────────────────────

    def _show_journal(self, caller):
        active = _active_quests(caller)
        available = _available_quests(caller)
        completed = _completed_quests(caller)

        lines = ["\n|y╔═══════════════════════ QUEST JOURNAL ═══════════════════════╗|n"]

        if active:
            lines.append("|y║|w ACTIVE QUESTS                                             |y║|n")
            for qdef, state in active:
                done = sum(1 for o in state["objectives"] if o["current"] >= o["qty"])
                total = len(state["objectives"])
                lines.append(f"|y║|n  |w{qdef['title']}|n  [{done}/{total} objectives]")
                for obj in state["objectives"]:
                    tick = "|g✓|n" if obj["current"] >= obj["qty"] else "|r•|n"
                    lines.append(
                        f"|y║|n    {tick} {obj['desc'].split('(')[0].strip()} "
                        f"|540({obj['current']}/{obj['qty']})|n"
                    )
        else:
            lines.append("|y║|n  |540No active quests.|n")

        lines.append("|y║|n")

        # Find quests from NPCs in current room
        room_npcs = [
            obj for obj in caller.location.contents
            if hasattr(obj, "db") and getattr(obj.db, "is_npc", False)
        ]
        npc_keys = {npc.key.lower() for npc in room_npcs}
        local_available = [
            qdef for qdef in available
            if qdef["giver"].lower() in npc_keys
        ]

        if local_available:
            lines.append("|y║|w AVAILABLE HERE                                            |y║|n")
            for qdef in local_available:
                lines.append(f"|y║|n  |g[!]|n |w{qdef['title']}|n — from |c{qdef['giver'].title()}|n")
                lines.append(
                    f"|y║|n      Type |wquest accept {qdef['title']}|n to begin."
                )
        elif available:
            lines.append("|y║|w AVAILABLE ELSEWHERE                                       |y║|n")
            for qdef in available[:5]:
                lines.append(f"|y║|n  |540{qdef['title']}|n — seek |c{qdef['giver'].title()}|n")

        if completed:
            lines.append("|y║|n")
            lines.append(f"|y║|w COMPLETED ({len(completed)})                                              |y║|n")
            for qdef in completed:
                lines.append(f"|y║|n  |g✓|n |540{qdef['title']}|n")

        lines.append("|y╚══════════════════════════════════════════════════════════════╝|n")
        caller.msg("\n".join(lines))

    def _show_quest_detail(self, caller, search):
        """Show detail for a quest matching search string."""
        search_lower = search.lower()
        match = None

        # Search active first, then all known
        for qdef, state in _active_quests(caller):
            if search_lower in qdef["title"].lower() or search_lower == qdef["key"]:
                match = (qdef, state)
                break

        if not match:
            for key, qdef in QUESTS.items():
                if search_lower in qdef["title"].lower() or search_lower == key:
                    state = _get_quest_state(caller, key)
                    match = (qdef, state)
                    break

        if not match:
            caller.msg(f"|rNo quest found matching '{search}'.|n")
            return

        qdef, state = match
        lines = [f"\n|w{qdef['title'].upper()}|n"]
        lines.append("|540" + "─" * 60 + "|n")
        lines.append(qdef["description"])
        lines.append("")

        outcome_key = state.get("outcome") if state else None

        if state:
            lines.append(f"|540Status:|n |w{state['status'].title()}|n")
            if outcome_key:
                odef = _quest_outcome_def(qdef, outcome_key) or {}
                lines.append(f"|540Path:|n |w{odef.get('label', outcome_key)}|n")
            lines.append("|540Objectives:|n")
            for obj in state["objectives"]:
                tick = "|g✓|n" if obj["current"] >= obj["qty"] else "|r•|n"
                lines.append(
                    f"  {tick} {obj['desc'].split('(')[0].strip()} "
                    f"({obj['current']}/{obj['qty']})"
                )
        elif _has_outcomes(qdef):
            lines.append("|540Paths available:|n")
            for okey, odef in qdef["outcomes"].items():
                lines.append(f"  |y•|n |w{odef.get('label', okey)}|n "
                             f"|540[{okey}]|n")
                lines.append(f"      |540{odef.get('description', '')}|n")
                for obj in odef.get("objectives", []):
                    lines.append(
                        f"      |r•|n {obj['desc'].split('(')[0].strip()} (0/{obj['qty']})"
                    )
        else:
            lines.append("|540Objectives:|n")
            for obj in qdef["objectives"]:
                lines.append(f"  |r•|n {obj['desc'].split('(')[0].strip()} (0/{obj['qty']})")

        # Rewards (current outcome if active, or branch-summary if branching + no state)
        rewards = _effective_rewards(qdef, outcome_key)
        reward_parts = []
        if rewards.get("silver"):
            reward_parts.append(f"|w{rewards['silver']} silver|n")
        for proto_key in rewards.get("items", []):
            reward_parts.append(f"|w{proto_key.replace('_', ' ').lower()}|n")
        for reagent, qty in rewards.get("reagents", {}).items():
            reward_parts.append(f"|w{qty}x {reagent}|n")
        if reward_parts:
            lines.append(f"|540Reward:|n {', '.join(reward_parts)}")

        if not state:
            if _has_outcomes(qdef):
                first_outcome = next(iter(qdef["outcomes"]))
                lines.append(
                    f"\n|gType |wquest accept {qdef['title']} / <path>|g "
                    f"to commit (e.g. |w/{first_outcome}|g).|n"
                )
            else:
                lines.append(f"\n|gType |wquest accept {qdef['title']}|g to begin.|n")

        caller.msg("\n".join(lines))

    # ── Accept / abandon ─────────────────────────────────────────────────────

    def _accept_quest(self, caller, title):
        # Parse optional "/outcome_key" suffix, e.g. "Chain Gang / bloody_break"
        outcome_key = None
        if "/" in title:
            title, outcome_tail = title.rsplit("/", 1)
            outcome_key = outcome_tail.strip().lower().replace(" ", "_")
            title = title.strip()

        search_lower = title.lower()
        qdef = None
        for key, q in QUESTS.items():
            if search_lower in q["title"].lower() or search_lower == key:
                qdef = q
                break

        if not qdef:
            caller.msg(f"|rNo quest found matching '{title}'.|n")
            return

        _ensure_quest_db(caller)

        if qdef["key"] in caller.db.quests:
            status = caller.db.quests[qdef["key"]]["status"]
            if status == "completed":
                caller.msg("|yYou have already completed that quest.|n")
            else:
                caller.msg("|yYou are already on that quest.|n")
            return

        if not _prerequisites_met(caller, qdef):
            caller.msg("|rYou have not yet met the prerequisites for that quest.|n")
            return

        # Check giver is in room
        room_keys = {obj.key.lower() for obj in caller.location.contents}
        if qdef["giver"].lower() not in room_keys:
            caller.msg(
                f"|rYou need to find |w{qdef['giver'].title()}|r to accept this quest.|n"
            )
            return

        # Branching quest — must pick an outcome
        if _has_outcomes(qdef):
            outcomes = qdef["outcomes"]
            if not outcome_key or outcome_key not in outcomes:
                caller.msg(f"\n|w{qdef['title']}|n requires you to choose a path:")
                for okey, odef in outcomes.items():
                    caller.msg(f"  |y•|n |w{odef.get('label', okey)}|n "
                               f"|540[{okey}]|n")
                    caller.msg(f"    |540{odef.get('description', '')}|n")
                caller.msg(
                    f"\n|540Type |wquest accept {qdef['title']} / <path>|n |540"
                    f"to commit (e.g. |wquest accept {qdef['title']} / "
                    f"{next(iter(outcomes))}|540).|n"
                )
                return

        state = {
            "status": "active",
            "objectives": _fresh_objectives(qdef, outcome_key),
        }
        if outcome_key:
            state["outcome"] = outcome_key
        caller.db.quests[qdef["key"]] = state

        caller.msg(f"\n|g✦ Quest Accepted: |w{qdef['title']}|n")
        outcome_label = None
        if outcome_key:
            odef = _quest_outcome_def(qdef, outcome_key)
            outcome_label = odef.get("label", outcome_key) if odef else outcome_key
            caller.msg(f"|540Path: |w{outcome_label}|n")
            caller.msg(f"|540{odef.get('description', '')}|n")
        else:
            caller.msg("|540" + qdef["description"] + "|n")
        caller.msg(f"\n|540Type |wquest {qdef['title']}|540 to track progress.|n")

        # Fire OOB event so the frontend can toast the acceptance —
        # keeps the confirmation out of the raw chat scrollback.
        try:
            import time as _time
            payload = {
                "type": "quest_accepted",
                "_ts": _time.time(),
                "key": qdef["key"],
                "title": qdef["title"],
                "giver": qdef.get("giver", ""),
                "outcome": outcome_key,
                "outcomeLabel": outcome_label,
            }
            for sess in caller.sessions.all():
                sess.msg(event=payload)
        except Exception:
            pass

    def _abandon_quest(self, caller, title):
        search_lower = title.lower()
        found_key = None
        for key, q in QUESTS.items():
            state = _get_quest_state(caller, key)
            if state and state["status"] == "active":
                if search_lower in q["title"].lower() or search_lower == key:
                    found_key = key
                    break

        if not found_key:
            caller.msg(f"|rNo active quest found matching '{title}'.|n")
            return

        qdef = QUESTS[found_key]
        del caller.db.quests[found_key]
        caller.msg(f"|yAbandoned quest: {qdef['title']}|n")
