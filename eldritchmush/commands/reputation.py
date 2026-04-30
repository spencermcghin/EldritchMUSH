"""
Reputation command — show faction + per-NPC personal reputation.

Usage:
  rep              — summary: faction rep + top/bottom personal rep
  rep <npc_name>   — detail: specific NPC's rep + remembered memories

Faction rep comes from `char.db.faction_rep`; personal rep from
`char.db.npc_rep` (see typeclasses/characters.py for schema).
Both are driven by branching quest outcomes today; combat / gift
hooks will feed them in future work.
"""
from evennia import Command


_FACTION_ORDER = ["crown", "cirque", "rangers", "crows", "outlaws", "outsider"]


def _any_webclient(char):
    """True if the character has at least one web-client session."""
    try:
        for sess in char.sessions.all():
            if (getattr(sess, "protocol_key", "") or "").startswith("webclient"):
                return True
    except Exception:
        pass
    return False


def _rep_label(score):
    """Short adjective for a rep score — purely for display colour."""
    if score >= 10:
        return "|g(heroic)|n"
    if score >= 5:
        return "|g(friend)|n"
    if score >= 1:
        return "|540(known)|n"
    if score == 0:
        return "|540(stranger)|n"
    if score >= -4:
        return "|r(suspect)|n"
    if score >= -9:
        return "|r(enemy)|n"
    return "|r(marked)|n"


class CmdReputation(Command):
    """
    Check your standing in the world.

    Usage:
      rep                 — faction rep + notable personal relationships
      rep <npc name>      — full memory of a specific NPC

    Faction rep reflects big-picture stance with a power block (the
    Crown, the Cirque, the Rangers, the Crows, the outlaw network,
    or "outsider" for wanderers). Personal rep is how a specific
    NPC feels about YOU — shaped by quests, gifts, and blood.
    """
    key = "rep"
    aliases = ["reputation", "standing"]
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        caller = self.caller
        args = (self.args or "").strip()
        if args:
            self._show_npc_detail(caller, args)
            return
        # Web clients see the rich Reputation modal via OOB; telnet
        # users keep the text summary.
        if _any_webclient(caller):
            try:
                from world.reputation_oob import push_reputation
                push_reputation(caller)
                import time as _time
                payload = {"type": "reputation_open", "_ts": _time.time()}
                for sess in caller.sessions.all():
                    if (getattr(sess, "protocol_key", "") or "").startswith("webclient"):
                        sess.msg(event=payload)
            except Exception:
                pass
            return
        self._show_summary(caller)

    # ─── Summary ─────────────────────────────────────────────────────────
    def _show_summary(self, caller):
        faction_rep = caller.db.faction_rep or {}
        npc_rep = caller.db.npc_rep or {}

        lines = ["\n|y╔═══════════════════ REPUTATION ═══════════════════╗|n"]

        lines.append("|y║|w FACTION STANDING                                |y║|n")
        any_faction = False
        for f in _FACTION_ORDER:
            score = int(faction_rep.get(f, 0) or 0)
            if score == 0:
                continue
            any_faction = True
            sign = "|g+" if score > 0 else "|r"
            lines.append(f"|y║|n  |w{f.title():10}|n {sign}{score:>3}|n  {_rep_label(score)}")
        if not any_faction:
            lines.append("|y║|n  |540No faction ties yet.|n")

        lines.append("|y║|n")
        lines.append("|y║|w PERSONAL RELATIONSHIPS                         |y║|n")
        if not npc_rep:
            lines.append("|y║|n  |540No one knows your face yet.|n")
        else:
            # Sort by abs(rep) descending so the most-charged
            # relationships bubble up first.
            sorted_rep = sorted(
                npc_rep.items(),
                key=lambda kv: abs(int((kv[1] or {}).get("rep", 0) or 0)),
                reverse=True,
            )
            for npc_key, entry in sorted_rep[:8]:
                score = int((entry or {}).get("rep", 0) or 0)
                sign = "|g+" if score > 0 else ("|r" if score < 0 else "|540")
                mem_count = len((entry or {}).get("memories") or [])
                mem_note = f"  |540[{mem_count} memor{'y' if mem_count == 1 else 'ies'}]|n" if mem_count else ""
                lines.append(
                    f"|y║|n  |w{npc_key.title()[:30]:30}|n {sign}{score:>3}|n  "
                    f"{_rep_label(score)}{mem_note}"
                )
            if len(sorted_rep) > 8:
                lines.append(f"|y║|n  |540... and {len(sorted_rep) - 8} more.|n")
            lines.append("|y║|n")
            lines.append("|y║|n  |540Use |wrep <name>|540 for detail on a specific NPC.|n")

        lines.append("|y╚══════════════════════════════════════════════════╝|n")
        caller.msg("\n".join(lines))

    # ─── Detail ──────────────────────────────────────────────────────────
    def _show_npc_detail(self, caller, name):
        npc_rep = caller.db.npc_rep or {}
        name_l = name.lower()
        # Try exact, then substring match.
        entry = npc_rep.get(name_l)
        matched_key = name_l
        if not entry:
            for k, v in npc_rep.items():
                if name_l in k:
                    entry = v
                    matched_key = k
                    break
        if not entry:
            caller.msg(f"|rNo one remembers you by that name. '{name}' has no entry in your memory.|n")
            return

        score = int(entry.get("rep", 0) or 0)
        sign = "|g+" if score > 0 else ("|r" if score < 0 else "|540")
        lines = [f"\n|w{matched_key.title()}|n  {sign}{score}|n  {_rep_label(score)}"]
        lines.append("|540" + "─" * 50 + "|n")

        last = entry.get("last_interacted")
        if last:
            lines.append(f"|540Last noted:|n {last}")

        memories = list(entry.get("memories") or [])
        if memories:
            lines.append("|540Memories:|n")
            for m in memories:
                lines.append(f"  |y•|n {m}")
        else:
            lines.append("|540No specific memories — just a vague impression.|n")

        caller.msg("\n".join(lines))
