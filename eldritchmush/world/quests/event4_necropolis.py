"""Event 4 — The Sacrifice: "Battle for the Necropolis — Part 1: The Barrows".
Source: Drive / Reboot / Event 4 - The Sacrifice / Encounters /
"Battle for the Necropolis - The Barrows"
(doc 11jwz0n9MmKMXr1SnLvzEgyvhEE-e-yMYhiY72oZ9otk),
with the chain framed by "Battle for the Necropolis - Master Draft"
(1mbdPKp5RkWZ9J1R5GQWWg-VI6Az0bTSkHUHqW5TzEn4) and the deferred climax
"Battle for the Necropolis - Showdown with Oblivion"
(1Q9zMf896dKZKnQ0H2kWEVi95cAKCDYNvS_xNc5Nhyno).

The WAVE-COMBAT showcase of Event 4. A Nethermancer (this setting's
necromancer) has descended into the ancient Annwyn Barrows above the
ruins of Tamris, butchering the Telyrian rune-seals that kept the dead
at rest for centuries. The risen are spilling out into the open. Ser
Wulfrun of the Vellatora has tracked the infestation here and hands the
players off at the smashed barrow door; Brom — an incognito priest of
Lirit posing as a lost magister — waits at the threshold to be the guide.

PART 1 is the approach and the first undead-wave defense: cut a way up
through the haunted Tamris graveyard (Risen Dead grunts), hold the
sunken crypt-yard against the heavier dead (Wights), and break the
barrow ravager that guards the smashed door. At the threshold the choice
the doc supports — the doc's "restore the seals" beat vs its "if PCs
don't, the dead keep rising" fallback: seal the Athan tomb with the
recovered burial rite so no fresh dead rise behind you, or leave it open
and press straight onto the Nethermancer's trail. Either way the barrow descent and the Showdown
with Oblivion (Decima's betrayal, the Coil, the Nethermancer) wait below
for Part 2 — gated on having cleared this approach.

Undead stat blocks are modeled on event3_mine's _arm_rat_digger / Blind
Stalker (the combat-teeth pattern) and on the Eldritch Monster Manual
ratings in the source: Risen Dead = Easy (Tough 4, Stagger 1), Wight =
Challenging (Tough 8, Stagger 2 / Cleave-Sunder 2), scaled into the
engine's stat bands. See populate spec returned alongside this module.

Quest dict format: see world/quests/__init__.py.
"""

QUESTS = {

    # ─────────────────────────────────────────────────────────────────────────
    # EVENT 4 — "BATTLE FOR THE NECROPOLIS — PART 1: THE BARROWS"
    # Source: Drive / Reboot / Event 4 / "Battle for the Necropolis - The
    # Barrows" (Friday-night approach + first undead-wave defense).
    # Giver: Ser Wulfrun, Knight of the Vellatora (escorts the player to the
    # barrow door at the Ruins of Tamris). Brom, priest of Lirit, waits at
    # the threshold and is the report/hook beat for Part 2.
    # Waves escalate by room via ordered tags: graveyard Risen Dead, then
    # the crypt-yard Wights, then the barrow ravager at the smashed door.
    # The threshold choice — seal the tomb or press the trail — is the
    # doc's "restore the seals" vs "the dead keep rising" fork.
    # ─────────────────────────────────────────────────────────────────────────
    "necropolis_the_barrows": {
        "key": "necropolis_the_barrows",
        "title": "Battle for the Necropolis — The Barrows",
        "giver": "ser wulfrun knight of the vellatora",
        "description": (
            "Ser Wulfrun of the Vellatora has been driving the risen dead "
            "back from Mystvale's outskirts for days, and has tracked them "
            "to their source: the ancient barrows above the ruins of Tamris. "
            "A Nethermancer — a corruptor of the dead — has gone down into "
            "them and shattered the Telyrian seals that kept the buried at "
            "rest. The dead are climbing out into the open. Wulfrun will "
            "take you as far as the smashed barrow door, then must ride for "
            "reinforcements. Cut your way up through the haunted graveyard, "
            "hold the sunken crypt-yard against the heavier dead, and break "
            "whatever guards the threshold. Brom — a stray magister who "
            "found the place before you — waits at the door to guide you "
            "down. What lies deeper is a matter for another night."
        ),
        "outcomes": {
            "seal_the_tomb": {
                "label": "Seal the Athan tomb behind you",
                "description": (
                    "Fight up through the graveyard, hold the crypt-yard, "
                    "and break the barrow ravager at the door. Take the "
                    "Athan rune-fragment off the skeleton, perform the "
                    "burial rite at the threshold to re-bind the broken "
                    "ward, and report to Brom. The dead stop rising behind "
                    "you — the descent will be cleaner, and Brom marks you "
                    "as one who honors the old rites. Slower, but the way "
                    "back stays closed."
                ),
                "objectives": [
                    {"type": "explore", "target": "Tamris Graveyard — The Outskirts",
                     "qty": 1, "tag": "arrived",
                     "desc": "Follow Ser Wulfrun up into the haunted graveyard (0/1)"},
                    {"type": "kill", "target": "tamris risen dead",
                     "qty": 3, "requires": "arrived", "tag": "graveyard_cleared",
                     "desc": "Cut down the risen dead clawing out of the graves (0/3)"},
                    {"type": "explore", "target": "Tamris Barrows — The Sunken Crypt-Yard",
                     "qty": 1, "requires": "graveyard_cleared", "tag": "cryptyard",
                     "desc": "Push on to the sunken crypt-yard (0/1)"},
                    {"type": "kill", "target": "barrow wight",
                     "qty": 2, "requires": "cryptyard", "tag": "cryptyard_cleared",
                     "desc": "Hold the crypt-yard against the barrow wights (0/2)"},
                    {"type": "kill", "target": "barrow ravager",
                     "qty": 1, "requires": "cryptyard_cleared", "tag": "door_won",
                     "desc": "Break the barrow ravager guarding the smashed door (0/1)"},
                    {"type": "gather", "target": "shattered athan rune-fragment",
                     "qty": 1, "requires": "door_won", "tag": "rune",
                     "desc": "Take the Athan rune-fragment from the skeleton at the door (0/1)"},
                    {"type": "gather", "target": "athan burial-rite stone",
                     "qty": 1, "requires": "rune", "tag": "rite",
                     "desc": "Set the fragment in the threshold ward — perform the Athan burial rite (0/1)"},
                    {"type": "talk", "target": "brom priest of lirit",
                     "qty": 1, "requires": "rite",
                     "desc": "|wask brom|n what waits below — report the door is sealed (0/1)"},
                ],
                "rewards": {
                    "silver": 45,
                    "items": [],
                    "reagents": {"Grave Blood": 2},
                },
                "faction_rep": {"crown": 4, "outsider": 2},
                "npc_rep_deltas": {
                    "ser wulfrun knight of the vellatora": 6,
                    "brom priest of lirit": 8,
                },
                "npc_memories": {
                    "ser wulfrun knight of the vellatora":
                        "held the barrow door and broke the first undead wave at Tamris",
                    "brom priest of lirit":
                        "honored the Athan rite and re-bound the broken ward before descending",
                },
            },
            "press_the_trail": {
                "label": "Press the Nethermancer's trail without sealing",
                "description": (
                    "No time for rites. Fight up through the graveyard, "
                    "hold the crypt-yard, break the ravager, and go "
                    "straight for the smashed door before the trail goes "
                    "cold. You take the dead's own — heavier loot off the "
                    "ravager — and reach Brom faster. But the seal stays "
                    "broken: the dead keep rising behind you, and Brom "
                    "marks you as reckless with the old powers."
                ),
                "objectives": [
                    {"type": "explore", "target": "Tamris Graveyard — The Outskirts",
                     "qty": 1, "tag": "arrived",
                     "desc": "Follow Ser Wulfrun up into the haunted graveyard (0/1)"},
                    {"type": "kill", "target": "tamris risen dead",
                     "qty": 3, "requires": "arrived", "tag": "graveyard_cleared",
                     "desc": "Cut down the risen dead clawing out of the graves (0/3)"},
                    {"type": "explore", "target": "Tamris Barrows — The Sunken Crypt-Yard",
                     "qty": 1, "requires": "graveyard_cleared", "tag": "cryptyard",
                     "desc": "Push on to the sunken crypt-yard (0/1)"},
                    {"type": "kill", "target": "barrow wight",
                     "qty": 3, "requires": "cryptyard", "tag": "cryptyard_cleared",
                     "desc": "Carve a path through the wights — they keep rising (0/3)"},
                    {"type": "kill", "target": "barrow ravager",
                     "qty": 1, "requires": "cryptyard_cleared", "tag": "door_won",
                     "desc": "Break the barrow ravager guarding the smashed door (0/1)"},
                    {"type": "gather", "target": "necropolis trail-map",
                     "qty": 1, "requires": "door_won", "tag": "map",
                     "desc": "Take the Nethermancer's trail-map from the skeleton at the door (0/1)"},
                    {"type": "talk", "target": "brom priest of lirit",
                     "qty": 1, "requires": "map",
                     "desc": "|wask brom|n what waits below — report the trail is hot (0/1)"},
                ],
                "rewards": {
                    "silver": 60,
                    "items": [],
                    "reagents": {"Grave Blood": 3},
                },
                "faction_rep": {"crown": 2, "outsider": -1, "cirque": 1},
                "npc_rep_deltas": {
                    "ser wulfrun knight of the vellatora": 3,
                    "brom priest of lirit": -3,
                },
                "npc_memories": {
                    "ser wulfrun knight of the vellatora":
                        "broke the first undead wave at Tamris but left the seal shattered",
                    "brom priest of lirit":
                        "chased the Nethermancer's trail and left the dead rising at our backs",
                },
            },
        },
        "prereqs": [],
    },
}
