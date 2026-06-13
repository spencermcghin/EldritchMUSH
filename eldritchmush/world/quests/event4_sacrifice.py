"""Event 4 — The Sacrifice (prologue).
Source: Drive / Reboot / Event 4 - The Sacrifice (folder 1Q1OvO_xXKvJgswfBTb4s0ZoZQchNxDRb).

Quest dict format: see world/quests/__init__.py.
"""

QUESTS = {

    # ─────────────────────────────────────────────────────────────────────────
    # EVENT 4 — THE SACRIFICE (anchor quests)
    # Source: Drive / Reboot / Event 4 / "Prologue: The Sacrifice".
    # Spring 765. Decisive Moments are now FACTION ALLEGIANCE choices —
    # which house do you back as House Laurent slips? Plus the doppelganger
    # murder mystery, Silver Company patrols vs the rising Cale, and
    # Aurorym zealotry at Dawnhaven.
    # ─────────────────────────────────────────────────────────────────────────
    "back_house_laurent": {
        "key": "back_house_laurent",
        "title": "Back House Laurent",
        "giver": "lord silas laurent",
        "description": (
            "Lord Silas Laurent has stepped in for his dying mother "
            "Ludmilla and is barely holding the Bannon faction together. "
            "He needs a public ally — or, if you prefer, a quiet rival "
            "to feed his enemies. Spring brings the question: where do "
            "you stand when the houses move?"
        ),
        "outcomes": {
            "support_silas": {
                "label": "Stand publicly with Lord Silas",
                "description": (
                    "Pledge to House Laurent. Bannon-loyal. Helps "
                    "Silas hold the seat through Spring."
                ),
                "objectives": [
                    {"type": "deliver", "target": "lord silas laurent", "qty": 1,
                     "desc": "Pledge to House Laurent in the Great Hall (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"crown": 4, "outsider": -1},
                "npc_rep_deltas": {"lord silas laurent": 8},
                "npc_memories": {"lord silas laurent": "stood with House Laurent in Spring"},
            },
            "undermine_silas": {
                "label": "Undermine Silas for a rival house",
                "description": (
                    "Silas is weak; another house is rising. Quietly "
                    "tip the balance against him. Falconer or Hardinger "
                    "rewards the favor."
                ),
                "objectives": [
                    {"type": "explore", "target": "Stag Hall — The Great Hall", "qty": 1,
                     "desc": "Sit through the council session (0/1)"},
                    {"type": "deliver", "target": "rook of the ironbloods", "qty": 1,
                     "desc": "Hand Rook a council secret (0/1)"},
                ],
                "rewards": {"silver": 45, "items": [], "reagents": {}},
                "faction_rep": {"crown": -3, "cirque": 2, "outlaws": 1},
                "npc_rep_deltas": {
                    "lord silas laurent": -8,
                    "rook of the ironbloods": 3,
                },
                "npc_memories": {
                    "lord silas laurent": "leaked council business",
                    "rook of the ironbloods": "delivered useful court intel",
                },
            },
            "stay_neutral": {
                "label": "Stay clear of the politics",
                "description": (
                    "Listen, leave. Don't pledge, don't sell. Spring is "
                    "long; choose later if at all."
                ),
                "objectives": [
                    {"type": "explore", "target": "Stag Hall — The Great Hall", "qty": 1,
                     "desc": "Attend the Great Hall session in silence (0/1)"},
                ],
                "rewards": {"silver": 5, "items": [], "reagents": {}},
                "faction_rep": {"outsider": 2},
                "npc_rep_deltas": {"lord silas laurent": -1},
                "npc_memories": {"lord silas laurent": "watched without choosing"},
            },
        },
        "prereqs": [],
    },

    "the_doppelganger": {
        "key": "the_doppelganger",
        "title": "The Doppelganger",
        "giver": "rook of the ironbloods",
        "description": (
            "Two men named Henri stood trial for Eldreth's murder; the "
            "town judge let both walk. Rook of the Ironbloods has not "
            "let it go. She wants the real killer — confession in hand — "
            "delivered to whichever justice you think fits. The "
            "confession never leaves the guilty man's coat: question "
            "the twins at the Town Hall, then take it off his body."
        ),
        "outcomes": {
            "deliver_to_cirque": {
                "label": "Hand Henri's confession to Rook",
                "description": (
                    "Cirque justice for a Cirque death. Rook will close "
                    "the file her own way. The Crown will not approve."
                ),
                "objectives": [
                    {"type": "talk", "target": "henri", "topic": "confession",
                     "tag": "pressed", "qty": 1,
                     "desc": "Question the twins at the Town Hall — |wask henri about the confession|n (0/1)"},
                    {"type": "kill", "target": "henri", "qty": 1,
                     "tag": "confronted", "requires": "pressed",
                     "desc": "Confront the guilty Henri — he will not be taken alive (0/1)"},
                    {"type": "gather", "target": "henri's confession", "qty": 1,
                     "requires": "confronted",
                     "desc": "Take the confession from his body (0/1)"},
                    {"type": "deliver", "target": "rook of the ironbloods", "qty": 1,
                     "desc": "Hand the confession to Rook (0/1)"},
                ],
                "rewards": {"silver": 50, "items": [], "reagents": {}},
                "faction_rep": {"cirque": 4, "crown": -2, "outlaws": 1},
                "npc_rep_deltas": {"rook of the ironbloods": 8},
                "npc_memories": {"rook of the ironbloods": "delivered Henri's confession"},
            },
            "lawful_arrest": {
                "label": "Hand the confession to the Mystvale watch",
                "description": (
                    "Take it through the proper channels. The watch "
                    "will reopen the case publicly. Slow, public, lawful."
                ),
                "objectives": [
                    {"type": "talk", "target": "henri", "topic": "confession",
                     "tag": "pressed", "qty": 1,
                     "desc": "Question the twins at the Town Hall — |wask henri about the confession|n (0/1)"},
                    {"type": "kill", "target": "henri", "qty": 1,
                     "tag": "confronted", "requires": "pressed",
                     "desc": "Confront the guilty Henri — he will not be taken alive (0/1)"},
                    {"type": "gather", "target": "henri's confession", "qty": 1,
                     "requires": "confronted",
                     "desc": "Recover the confession as evidence (0/1)"},
                    {"type": "deliver", "target": "mystvale captain of the watch", "qty": 1,
                     "desc": "Hand the confession to the watch captain (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"crown": 4, "cirque": -1},
                "npc_rep_deltas": {
                    "mystvale captain of the watch": 4,
                    "rook of the ironbloods": -2,
                },
                "npc_memories": {
                    "mystvale captain of the watch": "reopened the Eldreth case lawfully",
                    "rook of the ironbloods": "took the slow road",
                },
            },
            "shield_henri": {
                "label": "Shield the innocent twin",
                "description": (
                    "Burn the confession before either justice gets it. "
                    "The killer walks; so does the innocent twin. The "
                    "Cirque will not forget."
                ),
                "objectives": [
                    {"type": "kill", "target": "henri", "qty": 1,
                     "tag": "confronted",
                     "desc": "Confront and put down the guilty Henri (0/1)"},
                    {"type": "gather", "target": "henri's confession", "qty": 1,
                     "requires": "confronted",
                     "desc": "Take the confession from his body and burn it (0/1)"},
                ],
                "rewards": {"silver": 15, "items": [], "reagents": {}},
                "faction_rep": {"crown": -2, "cirque": -3, "outlaws": 2, "outsider": 2},
                "npc_rep_deltas": {"rook of the ironbloods": -6},
                "npc_memories": {"rook of the ironbloods": "burned the case rather than deliver it"},
            },
        },
        "prereqs": [],
    },

    "silver_company_patrol": {
        "key": "silver_company_patrol",
        "title": "Silver Company Patrol",
        "giver": "sergeant marrow of the silver company",
        "description": (
            "Sergeant Marrow's Silver Company is patrolling the roads "
            "around Mystvale to keep Crow attacks down. Cale the Thorn "
            "— the new Crow firebrand — has been spotted near Fox Den. "
            "Run the patrol; deal with Cale however the contract reads."
        ),
        "outcomes": {
            "crush_cale": {
                "label": "Kill Cale and break the patrol's ambush",
                "description": (
                    "Cut Cale down with the Crows trying to ambush you. "
                    "Marrow pays a bounty; the Crows take a generation "
                    "to recover."
                ),
                "objectives": [
                    {"type": "kill", "target": "crow ambusher", "qty": 2,
                     "desc": "Beat back the ambush (0/2)"},
                    {"type": "kill", "target": "cale the thorn", "qty": 1,
                     "desc": "Put down Cale the Thorn (0/1)"},
                    {"type": "deliver", "target": "sergeant marrow of the silver company", "qty": 1,
                     "desc": "Report the patrol cleared (0/1)"},
                ],
                "rewards": {"silver": 60, "items": [], "reagents": {}},
                "faction_rep": {"crown": 3, "crows": -5},
                "npc_rep_deltas": {
                    "sergeant marrow of the silver company": 6,
                    "cale the thorn": -100,
                },
                "npc_memories": {
                    "sergeant marrow of the silver company": "broke Cale's ambush",
                },
            },
            "let_him_walk": {
                "label": "Let Cale walk in exchange for a peace",
                "description": (
                    "Cale will stand the Crows down on the Old Road if "
                    "you walk away. Marrow's contract pays less without "
                    "a body. Outlaw network respects the choice."
                ),
                "objectives": [
                    {"type": "kill", "target": "crow ambusher", "qty": 2,
                     "desc": "Beat back the ambush before talk is possible (0/2)"},
                    {"type": "deliver", "target": "sergeant marrow of the silver company", "qty": 1,
                     "desc": "Report the patrol clear without a body (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"crown": -1, "crows": 3, "outlaws": 2},
                "npc_rep_deltas": {
                    "sergeant marrow of the silver company": -1,
                    "cale the thorn": 4,
                },
                "npc_memories": {
                    "cale the thorn": "let me walk on the Old Road in spring",
                },
            },
        },
        "prereqs": [],
    },

    "aurorym_zealotry": {
        "key": "aurorym_zealotry",
        "title": "The Branded",
        "giver": "sister mariel",
        "description": (
            "The faithful at Dawnhaven have begun branding themselves "
            "with the Vellatora's flame in proof of devotion. Sister "
            "Mariel will not order the practice stopped — but she will "
            "not order it continued either. The fire is hot in the "
            "camp tonight, and someone needs to choose."
        ),
        "outcomes": {
            "accept_brand": {
                "label": "Accept the brand",
                "description": (
                    "Press the iron to your forearm. Walk out of "
                    "Dawnhaven Aurorym in the deepest sense. The "
                    "outsiders will keep their distance."
                ),
                "objectives": [
                    {"type": "explore", "target": "Dawnhaven", "qty": 1,
                     "desc": "Stand the brand-circle at Dawnhaven (0/1)"},
                    {"type": "gather", "target": "vellatora branding iron", "qty": 1,
                     "desc": "Accept the iron (0/1)"},
                ],
                "rewards": {"silver": 0, "items": [], "reagents": {}},
                "faction_rep": {"crown": 2, "cirque": -1, "outsider": -3},
                "npc_rep_deltas": {"sister mariel": 8, "curate godrick": 4},
                "npc_memories": {
                    "sister mariel": "took the Vellatora brand",
                    "curate godrick": "stood with the Order in fire",
                },
            },
            "refuse_walk_away": {
                "label": "Refuse the brand and walk away",
                "description": (
                    "Tell Mariel no. Some things are not for fire. "
                    "Neutral; quiet."
                ),
                "objectives": [
                    {"type": "explore", "target": "Dawnhaven", "qty": 1,
                     "desc": "Walk through Dawnhaven (0/1)"},
                ],
                "rewards": {"silver": 5, "items": [], "reagents": {}},
                "faction_rep": {"outsider": 2},
                "npc_rep_deltas": {"sister mariel": -1},
                "npc_memories": {"sister mariel": "walked the brand-circle uncommitted"},
            },
            "report_excesses": {
                "label": "Report the branding to the Burgomaster",
                "description": (
                    "Take the iron itself to Burgomaster Domitille as "
                    "evidence of zealotry on Mystvale's doorstep. The "
                    "town wants the camp watched; the Aurorym will "
                    "remember the betrayal."
                ),
                "objectives": [
                    {"type": "gather", "target": "vellatora branding iron", "qty": 1,
                     "desc": "Take the branding iron (0/1)"},
                    {"type": "deliver", "target": "burgomaster domitille", "qty": 1,
                     "desc": "Show the iron to Burgomaster Domitille (0/1)"},
                ],
                "rewards": {"silver": 25, "items": [], "reagents": {}},
                "faction_rep": {"crown": 3, "outsider": 1},
                "npc_rep_deltas": {
                    "burgomaster domitille": 4,
                    "sister mariel": -6,
                    "curate godrick": -3,
                },
                "npc_memories": {
                    "burgomaster domitille": "warned the town about Aurorym zealotry",
                    "sister mariel": "carried our shame to the Burgomaster",
                    "curate godrick": "spoke against the Order to the Burgomaster",
                },
            },
        },
        "prereqs": [],
    },
}
