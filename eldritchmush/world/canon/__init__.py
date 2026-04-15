"""
Canon library — modular lore sources for AI NPC dialogue.

The basic system prompt (world/ai_lore.py) gives every NPC a universal
world bible: setting, timeline, the Great Houses, the major factions,
the Writ, the Aurorym (top-level). That's the always-on baseline.

This package adds DEPTH. Each NPC carries a `canon_tags` attribute —
e.g. ["faction:aurorym", "house:laurent", "region:hearthlands"] — and
when their system prompt is built, only the canon entries whose tags
overlap with theirs are included. So Brother Alaric (Aurorym Auron)
gets the deep Aurorym + Vellatora doctrine; an Innis scout in the
Northern Marches gets House Innis lineage + Northern Marches geography
+ the Pooka knight order.

Scope still applies on top of that. Annwyn-interior canon (specific
internal politics, supernatural threats actually witnessed) is gated
behind ai_scope="annwyn" — Gateway-side NPCs get rumor-only versions.

If an NPC has no canon_tags, they fall back to the bible only —
"common knowledge" stuff. Extra canon gets added as we tag more NPCs.
"""

from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class CanonEntry:
    """One block of canonical lore that can be added to an NPC's prompt.

    title: short label used as the prompt header for this entry.
    text: the lore body. Plain prose. Multiline OK.
    scope:
      "common"  — anyone with matching tags gets it (default)
      "gateway" — Gateway-scope NPCs only (Arnesse-side knowledge)
      "annwyn"  — Annwyn-interior NPCs only (firsthand of the otherworld)
      "secret"  — never auto-included; admin/staff-only
    Tags below are sets of strings. An entry matches an NPC if ANY of
    the NPC's canon_tags overlap with ANY of the entry's tag sets.
    """
    title: str
    text: str
    scope: str = "common"
    factions: Set[str] = field(default_factory=set)
    houses: Set[str] = field(default_factory=set)
    regions: Set[str] = field(default_factory=set)
    archetypes: Set[str] = field(default_factory=set)


# Aggregate registry. Each module under world/canon/ appends its
# entries here on import.
ENTRIES: List[CanonEntry] = []


def _norm(tags):
    """Normalize a tag list to a set of lowercase strings."""
    if not tags:
        return set()
    out = set()
    for t in tags:
        s = str(t).strip().lower()
        if not s:
            continue
        # Strip optional category prefix ("house:richter" → "richter")
        # so prompts can be tagged either way.
        if ":" in s:
            cat, _, val = s.partition(":")
            out.add(s)        # "house:richter"
            out.add(val)      # "richter"
        else:
            out.add(s)
    return out


def _entry_matches(entry: CanonEntry, npc_tags: Set[str], scope: str) -> bool:
    # Scope filter
    if entry.scope == "secret":
        return False
    if entry.scope == "annwyn" and scope != "annwyn":
        return False
    if entry.scope == "gateway" and scope == "annwyn":
        # Annwyn NPCs get common + annwyn entries; gateway-only ones
        # are intentionally rumor-shaped, so omit for Annwyn-side NPCs.
        return False
    # If the entry has NO tags it's "universal supplemental" — always
    # included. Otherwise require overlap with the NPC's tags.
    entry_tags = entry.factions | entry.houses | entry.regions | entry.archetypes
    if not entry_tags:
        return True
    norm_entry_tags = _norm(entry_tags)
    return bool(norm_entry_tags & npc_tags)


def collect_for_npc(npc) -> str:
    """Return a formatted canon block for the NPC's system prompt.

    The block is a series of "## Title\\n<text>\\n" sections, one per
    matching entry. Returns an empty string if nothing matches.
    """
    raw_tags = npc.attributes.get("canon_tags", default=None)
    npc_tags = _norm(raw_tags)
    scope = npc.attributes.get("ai_scope", default="gateway") or "gateway"

    matching = [e for e in ENTRIES if _entry_matches(e, npc_tags, scope)]
    if not matching:
        return ""

    parts = ["=== EXTENDED CANON RELEVANT TO YOU ==="]
    for entry in matching:
        parts.append(f"\n## {entry.title}")
        parts.append(entry.text.strip())
    return "\n".join(parts)


# Side-effect imports populate ENTRIES.
# Each module is independent — failure to load one does not disable
# the rest.
for _mod in ("factions", "houses", "regions", "history", "secrets"):
    try:
        __import__(f"world.canon.{_mod}")
    except Exception as _exc:
        import sys
        print(f"[canon] WARN: failed to load world.canon.{_mod}: {_exc}",
              file=sys.stderr)
