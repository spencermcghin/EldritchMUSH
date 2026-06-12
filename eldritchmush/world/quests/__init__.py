"""
Quest data definitions for EldritchMUSH.

Each quest is a dict with:
  key          - unique str ID used in db storage
  title        - display name
  giver        - NPC key who offers/completes it (matched against NPC .key)
  description  - flavour paragraph shown on quest accept
  prereqs      - list of prereq entries (see below; default [])

  Single-outcome quests also have:
    objectives - list of objective dicts
    rewards    - dict of rewards granted on completion

  Branching (multi-outcome) quests have instead:
    outcomes   - dict of {outcome_key: outcome_dict}
    Each outcome_dict is:
      label       - short name shown at accept time (e.g. "Bloody break")
      description - one-paragraph flavour of this path
      objectives  - list of objective dicts for this path
      rewards     - dict (same shape as above)
      faction_rep - dict of {faction_name: delta_int}, applied on completion

Objective dict:
  type    - "kill"  | "gather" | "deliver" | "explore" | "duel"
  target  - NPC key / item key / room key depending on type
  qty     - how many (default 1)
  desc    - short human-readable description shown in quest log

  "duel" ticks when the player wins a wagered duel vs. the target NPC.

Reward dict keys (all optional, default 0):
  silver  - silver coins
  items   - list of prototype keys to spawn into inventory
  reagents - dict of {reagent_name: qty}

Prereq entry can be either:
  "quest_key"  (str) — requires that quest to be completed (any outcome),
  or {"quest": "...", "outcome": "..."} — requires a specific outcome.

Faction keys (convention): crown, cirque, rangers, crows, outlaws, outsider.
"""

from world.quests import (
    event1_walkins,
    event1_saturday,
    event2_wrath,
    event2_gambling,
    event5_trial,
    event5_resources,
    event5_scriptorium,
    event5_shiptour,
    event4_sacrifice,
    event4_necropolis,
    event3_awakening,
    event3_mine,
    event3_doll,
    event3_shrooms,
    event6_frenzy,
)

_MODULES = (
    event1_walkins, event1_saturday, event2_wrath, event2_gambling,
    event5_trial, event5_resources, event5_scriptorium, event5_shiptour,
    event4_sacrifice, event4_necropolis,
    event3_awakening, event3_mine, event3_doll, event3_shrooms,
    event6_frenzy,
)

QUESTS = {}
for _mod in _MODULES:
    for _key, _qdef in _mod.QUESTS.items():
        if _key in QUESTS:
            raise ValueError(
                f"Duplicate quest key {_key!r} in "
                f"{_mod.__name__} — quest keys must be "
                f"globally unique across event modules."
            )
        QUESTS[_key] = _qdef
