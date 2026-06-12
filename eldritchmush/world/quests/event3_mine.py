"""Event 3 — The Awakening: "They Call It a Mine".
Source: Drive / Reboot / Event 3 - The Awakening / Encounters /
"They Call It a Mine" (doc 1GR2g2iE4fN5qxlQn4RI6EEwlo7LD1t5pVOKi5eqsJ6E)
+ "Rat Company Captain's Briefing" (1MownFfG3BfI_hRg9Kjv0f-h22NLJzwdt_vOVBztWQyA).

The flagship COMBAT showcase for the Event 3 batch. The Laurent Royal
Expeditionary and Survey Unit — the "Rat Company" — hires desperate hands
to descend an old mine, mark ore veins, and blast open a safe exit. The
dramatic turn the doc hinges on: this is not honest work. Rat Company has
already fed crews into this shaft; the survivors came back "changed,"
mumbling about "them that do not see" and that one must always be quiet
in the mines. The digging has woken the blind stalkers, the underboss is
a skeleton at the bottom with the gate key on him, and Captain Dunn keeps
recruiting anyway. Players can blast out and expose the racket, or seize
the dig and keep Laurent's secret for coin.

Quest dict format: see world/quests/__init__.py.
"""

QUESTS = {

    # ─────────────────────────────────────────────────────────────────────────
    # EVENT 3 — "THEY CALL IT A MINE" (combat dungeon, flagship showcase)
    # Source: Drive / Reboot / Event 3 / "They Call It a Mine".
    # Giver: Captain Dunn of Rat Company (briefs in the Tavern / south gate).
    # Descent gated by ordered beats; Rat Company raiders fight back hard;
    # the blind stalker boss is the awakened thing at the bottom.
    # ─────────────────────────────────────────────────────────────────────────
    "rat_company_descent": {
        "key": "rat_company_descent",
        "title": "They Call It a Mine",
        "giver": "captain dunn of rat company",
        "description": (
            "Captain Dunn of the Laurent 'Rat Company' is hiring hands to "
            "delve an old mine off the Old Road — mark the ore veins, find "
            "a way through, and blast open a new exit so the real digging "
            "can begin. Five silver up front; a gold dragon when you walk "
            "back out. He does not mention that the last crews he sent "
            "down came back wrong, whispering about 'them that do not "
            "see,' and that you must always, always be quiet in the dark. "
            "Tie onto the rope and go down. Find the underboss's office, "
            "find his key, and find out why nobody warns the next crew."
        ),
        "outcomes": {
            "blast_and_expose": {
                "label": "Blast a way out and bring the truth back up",
                "description": (
                    "Fight down to the underboss's office, take the gate "
                    "key off the lost miner's bones, raid the cache for the "
                    "blasting agent, and blow the shaft open. Bring Dunn "
                    "the ore samples AND the accident ledger that proves "
                    "he knew. Honest crews get warned after this — and "
                    "House Laurent's name takes the bruise it earned."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Mine — Low Passage",
                     "qty": 1, "tag": "entered",
                     "desc": "Rope on, hug the ledge into the dark (0/1)"},
                    {"type": "gather", "target": "lost miner's skeleton",
                     "qty": 1, "requires": "entered", "tag": "key",
                     "desc": "Search the lost miner's bones for the gate key (0/1)"},
                    {"type": "kill", "target": "rat company digger",
                     "qty": 3, "requires": "entered",
                     "desc": "Cut down the Rat Company diggers gone feral (0/3)"},
                    {"type": "gather", "target": "underboss's accident ledger",
                     "qty": 1, "requires": "key",
                     "desc": "Take the underboss's accident ledger from the locked office (0/1)"},
                    {"type": "gather", "target": "rich ore samples",
                     "qty": 1, "requires": "key",
                     "desc": "Bag the rich ore samples flagged along the veins (0/1)"},
                    {"type": "gather", "target": "cache of blasting agent",
                     "qty": 1, "requires": "key", "tag": "agent",
                     "desc": "Unlock the hidden cache and take the blasting agent (0/1)"},
                    {"type": "kill", "target": "blind stalker of the deep mine",
                     "qty": 1, "requires": "agent",
                     "desc": "Put down the blind stalker the digging woke (0/1)"},
                    {"type": "deliver", "target": "captain dunn of rat company",
                     "qty": 1,
                     "desc": "Bring Dunn the ore AND the ledger — report what's down there (0/1)"},
                ],
                "rewards": {
                    "silver": 60,
                    "items": ["SPOTTERS_DRAUGHT"],
                    "reagents": {"Phosphorous": 2, "Luminesce": 1},
                },
                "faction_rep": {"crown": -2, "outsider": 4},
                "npc_rep_deltas": {
                    "captain dunn of rat company": -4,
                    "the lost miner of rat company": 3,
                },
                "npc_memories": {
                    "captain dunn of rat company":
                        "came back up with the ledger that proved I knew the mine was a grave",
                    "the lost miner of rat company":
                        "carried my bones and my warning back into the light",
                },
            },
            "seize_the_dig": {
                "label": "Seize the dig and keep Laurent's secret",
                "description": (
                    "The veins are real and the company is shorthanded. "
                    "Clear the shaft, blow the exit, hand Dunn his ore and "
                    "nothing else — and pocket the accident ledger so no "
                    "one above ever reads it. Laurent's operation moves in. "
                    "The next crews are not your problem; the coin is good "
                    "and the company remembers a closed mouth."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Mine — Low Passage",
                     "qty": 1, "tag": "entered",
                     "desc": "Rope on, hug the ledge into the dark (0/1)"},
                    {"type": "gather", "target": "lost miner's skeleton",
                     "qty": 1, "requires": "entered", "tag": "key",
                     "desc": "Search the lost miner's bones for the gate key (0/1)"},
                    {"type": "kill", "target": "rat company digger",
                     "qty": 4, "requires": "entered",
                     "desc": "Silence the feral diggers — no witnesses (0/4)"},
                    {"type": "gather", "target": "rich ore samples",
                     "qty": 1, "requires": "key",
                     "desc": "Bag the rich ore samples flagged along the veins (0/1)"},
                    {"type": "gather", "target": "cache of blasting agent",
                     "qty": 1, "requires": "key", "tag": "agent",
                     "desc": "Unlock the hidden cache and take the blasting agent (0/1)"},
                    {"type": "kill", "target": "blind stalker of the deep mine",
                     "qty": 1, "requires": "agent",
                     "desc": "Put down the blind stalker before it reaches the surface (0/1)"},
                    {"type": "deliver", "target": "captain dunn of rat company",
                     "qty": 1,
                     "desc": "Hand Dunn the ore — say nothing of the ledger (0/1)"},
                ],
                "rewards": {
                    "silver": 110,
                    "items": [],
                    "reagents": {"Fulger Powder": 1},
                },
                "faction_rep": {"crown": 3, "outsider": -3},
                "npc_rep_deltas": {
                    "captain dunn of rat company": 6,
                    "the lost miner of rat company": -4,
                },
                "npc_memories": {
                    "captain dunn of rat company":
                        "delved the shaft, kept the ledger quiet, and took Laurent's coin like a professional",
                    "the lost miner of rat company":
                        "left my warning in the dark so the next crew could join me",
                },
            },
        },
        "prereqs": [],
    },
}
