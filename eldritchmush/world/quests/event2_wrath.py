"""Event 2 — The Wrath (Friday Night + Saturday anchors).
Source: Drive / Reboot / Event 2 - The Wrath (folder 1jxlA_zorcovQrAyMYU3paeNR6-m0pCl8).

Quest dict format: see world/quests/__init__.py.
"""

QUESTS = {

    # ─────────────────────────────────────────────────────────────────────────
    # EVENT 2 — THE WRATH (Friday Night anchor quests)
    # Source: Drive / Reboot / Event 2. Full arc spans ~20 encounters;
    # these four cover the Friday Night opening. Saturday content will
    # be added in a later pass.
    # ─────────────────────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    # Festival of Lights — rebuilt 2026-06-11 to restore the doc's dark
    # turn (a witch-thrall host, a man dying of the Curse of Thorns on a
    # timed Medicine save, the incriminating note). Reference exemplar
    # for the timed-rescue (deadline) + skill + ordered-beat primitives;
    # see docs/CONTENT_STANDARDS.md. The rescue is a SOFT deadline: if
    # Grigory dies the investigation still goes on, but the loss is real.
    # ─────────────────────────────────────────────────────────────────────────
    "festival_of_lights": {
        "key": "festival_of_lights",
        "title": "The Festival of Lights",
        "giver": "branwyn the festival herald",
        "description": (
            "House Laurent's yearly Festival of Lights opens at Stag Hall "
            "tonight. Branwyn the herald is recruiting willing hands to "
            "hang the last lanterns — but the wisewoman Dierdra has the "
            "run of the festival games, and the fort has been tense of "
            "late. Light the lanterns, enjoy the night... and be ready, "
            "for the night does not stay gentle. Bring a healer."
        ),
        "objectives": [
            {"type": "gather", "target": "paper lantern", "qty": 2,
             "tag": "lights",
             "desc": "Hang the festival lanterns in the courtyard (0/2)"},
            # The crisis: once the lights are up, Grigory staggers in
            # dying — a poppet sewn into his belly, burning him from the
            # inside (the Curse of Thorns). Cut it free with a Medicine
            # hand before the clock runs out. Soft deadline.
            {"type": "skill", "target": "grigory", "skill": "medicine",
             "requires": "lights", "tag": "grigory", "qty": 1,
             "deadline": 600, "deadline_starts_on": "lights",
             "deadline_fails": "objective",
             "deadline_reason": (
                 "Grigory burned out from the inside before anyone could "
                 "cut the poppet free. The festival falls silent."),
             "desc": "Save dying Grigory before the curse takes him — "
                     "|wtreat grigory|n (medicine) (0/1)"},
            # The reveal: his last breath names the wisewoman. Find the
            # witch's note she's been carrying.
            {"type": "gather", "target": "dierdra's note",
             "requires": "grigory", "tag": "note", "qty": 1,
             "desc": "Search the wisewoman Dierdra for the truth (0/1)"},
            {"type": "deliver", "target": "branwyn the festival herald",
             "requires": "note", "qty": 1,
             "desc": "Bring the witch's note to Branwyn (0/1)"},
        ],
        "rewards": {"silver": 25, "items": [], "reagents": {"Hollyrue": 2}},
        "faction_rep": {"crown": 3, "crows": -2},
        "npc_rep_deltas": {"branwyn the festival herald": 4},
        "npc_memories": {"branwyn the festival herald":
                         "unmasked the witch-thrall hiding inside our own festival"},
        "prereqs": [],
    },

    "signs_of_fair_folk": {
        "key": "signs_of_fair_folk",
        "title": "Signs of the Fair Folk",
        "giver": "captain thelmer of the stag watch",
        "description": (
            "Captain Thelmer's patrols keep finding small stick-and-bone "
            "shrines around the fort, the forest road, and the Old Road "
            "south. He wants four of them collected and brought to him — "
            "whatever they are, he wants them OFF his land."
        ),
        "objectives": [
            {"type": "gather", "target": "stick-and-bone shrine", "qty": 4,
             "desc": "Gather stick-and-bone shrines (0/4)"},
            {"type": "deliver", "target": "captain thelmer of the stag watch",
             "qty": 1, "desc": "Deliver the shrines to Captain Thelmer (0/1)"},
        ],
        "rewards": {"silver": 15, "items": [], "reagents": {}},
        "prereqs": [],
    },

    "caravan_attack": {
        "key": "caravan_attack",
        "title": "Caravan Attack",
        "giver": "captain thelmer of the stag watch",
        "description": (
            "A Laurent supply caravan has come under attack on the Old "
            "Road. The raiders are wearing stolen Laurent tabards — worse, "
            "they know the watch's patrol schedule. Thelmer wants them "
            "put down before the survivors reach the Thornwood."
        ),
        "objectives": [
            {"type": "kill", "target": "caravan raider", "qty": 3,
             "desc": "Put down the caravan raiders (0/3)"},
            {"type": "deliver", "target": "captain thelmer of the stag watch",
             "qty": 1, "desc": "Report the ambush cleared (0/1)"},
        ],
        "rewards": {"silver": 25, "items": [], "reagents": {}},
        "prereqs": [],
    },

    # ─── Event 2 Saturday anchor chain ───────────────────────────────────
    "the_pilgrimage": {
        "key": "the_pilgrimage",
        "title": "The Pilgrimage",
        "giver": "elder symund the pilgrim",
        "description": (
            "Elder Symund leads a small band of pilgrims from Stag Hall "
            "north to the Shrine of Lirit, a bone-and-birch reliquary "
            "deep in the Thornwood. The road isn't safe. Escort them "
            "to the shrine and collect payment at the other end."
        ),
        "outcomes": {
            "escort_safely": {
                "label": "Escort the pilgrims safely to the shrine",
                "description": (
                    "Get Elder Symund and his pilgrims to the Shrine of "
                    "Lirit alive. The Aurorym will remember."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Shrine of Lirit", "qty": 1,
                     "desc": "Reach the Shrine of Lirit (0/1)"},
                    {"type": "deliver", "target": "elder symund the pilgrim",
                     "qty": 1, "desc": "Deliver the pilgrims safely (0/1)"},
                ],
                "rewards": {"silver": 20, "items": [], "reagents": {}},
                "faction_rep": {"crown": 1, "cirque": 0},
            },
            "betray_to_witches": {
                "label": "Hand the pilgrims to the witches",
                "description": (
                    "The witches of the Thornwood pay well for warm "
                    "bodies. Lead the elder to the shrine — then slip "
                    "aside and let the forest take them."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Shrine of Lirit", "qty": 1,
                     "desc": "Reach the Shrine of Lirit (0/1)"},
                    {"type": "gather", "target": "witch's braid", "qty": 1,
                     "desc": "Take a witch's braid as receipt (0/1)"},
                ],
                "rewards": {"silver": 40, "items": [], "reagents": {}},
                "faction_rep": {"crown": -3, "outlaws": 2},
            },
        },
        "prereqs": [],
    },

    "the_heist": {
        "key": "the_heist",
        "title": "The Heist",
        "giver": "quill the fixer",
        "description": (
            "Quill has a job: during the chaos of the Pilgrimage, someone "
            "needs to lift a sealed Laurent strongbox from Stag Hall's "
            "treasury. Take the job clean for the underworld — or flip "
            "to the watch for a cleaner conscience."
        ),
        "outcomes": {
            "pull_the_job": {
                "label": "Pull the heist for the underworld",
                "description": (
                    "Take the strongbox, deliver it to Quill. Stag "
                    "Watch gets smaller; your pocket gets bigger."
                ),
                "objectives": [
                    {"type": "gather", "target": "laurent strongbox", "qty": 1,
                     "desc": "Lift the Laurent strongbox (0/1)"},
                    {"type": "deliver", "target": "quill the fixer", "qty": 1,
                     "desc": "Deliver the strongbox to Quill (0/1)"},
                ],
                "rewards": {"silver": 50, "items": [], "reagents": {}},
                "faction_rep": {"crown": -3, "outlaws": 3, "crows": 1},
            },
            "flip_to_watch": {
                "label": "Flip Quill to the watch",
                "description": (
                    "Meet with Quill, get the details, then turn it all "
                    "over to Captain Thelmer. The underworld will hear "
                    "your name — you'll want allies after this."
                ),
                "objectives": [
                    {"type": "gather", "target": "laurent strongbox", "qty": 1,
                     "desc": "Accept the strongbox as cover (0/1)"},
                    {"type": "deliver", "target": "captain thelmer of the stag watch",
                     "qty": 1, "desc": "Turn Quill over to Captain Thelmer (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"crown": 4, "outlaws": -4},
            },
        },
        "prereqs": [],
    },

    "second_expedition": {
        "key": "second_expedition",
        "title": "The Second Expedition",
        "giver": "curate godrick",
        "description": (
            "Curate Godrick has no word from the First Expedition and "
            "will not wait any longer. He asks you to march north through "
            "the Thornwood, find Captain Aethelflaed's camp, and bring "
            "back Auron Magda — dead or alive. She is carrying a journal "
            "that he wants preserved at all costs."
        ),
        "objectives": [
            {"type": "explore", "target": "First Expedition Camp", "qty": 1,
             "desc": "Reach the First Expedition Camp (0/1)"},
            {"type": "gather", "target": "magda's journal", "qty": 1,
             "desc": "Recover Magda's journal (0/1)"},
            {"type": "deliver", "target": "curate godrick", "qty": 1,
             "desc": "Return the journal to Curate Godrick (0/1)"},
        ],
        "rewards": {"silver": 35, "items": [], "reagents": {}},
        "prereqs": [],
    },

    "witch_interlopers": {
        "key": "witch_interlopers",
        "title": "Witch Interlopers",
        "giver": "captain aethelflaed",
        "description": (
            "The Thornwood witches have found the First Expedition Camp. "
            "Captain Aethelflaed's people have little fight left. Clear "
            "the witches — or make a deal with them. The forest is going "
            "to speak either way."
        ),
        "outcomes": {
            "clear_by_blade": {
                "label": "Kill the witches",
                "description": (
                    "Put them down. Aethelflaed keeps her camp. The "
                    "Thornwood remembers faces."
                ),
                "objectives": [
                    {"type": "kill", "target": "thornwood witch", "qty": 3,
                     "desc": "Kill the Thornwood witches (0/3)"},
                    {"type": "deliver", "target": "captain aethelflaed", "qty": 1,
                     "desc": "Report to Captain Aethelflaed (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"crown": 2, "outlaws": -2},
            },
            "make_the_bargain": {
                "label": "Bargain with the witches",
                "description": (
                    "The witches want the camp. You offer them something "
                    "else — Aethelflaed's expedition paperwork. Crown "
                    "furious; outlaws curious."
                ),
                "objectives": [
                    {"type": "gather", "target": "expedition paperwork", "qty": 1,
                     "desc": "Take the expedition paperwork from the camp (0/1)"},
                    {"type": "gather", "target": "witch's braid", "qty": 1,
                     "desc": "Receive a witch's braid as the bargain's seal (0/1)"},
                ],
                "rewards": {"silver": 40, "items": [], "reagents": {}},
                "faction_rep": {"crown": -4, "outlaws": 2, "crows": 1},
            },
        },
        "prereqs": ["second_expedition"],
    },

    "the_butcher": {
        "key": "the_butcher",
        "title": "The Butcher",
        "giver": "captain aethelflaed",
        "description": (
            "Something took the rest of the expedition. Aethelflaed "
            "only heard the cleaver. His hovel is further north — and "
            "he is not a man, not anymore. Bring back his cleaver as "
            "proof of the kill."
        ),
        "objectives": [
            {"type": "kill", "target": "the butcher", "qty": 1,
             "desc": "Kill the Butcher (0/1)"},
            {"type": "gather", "target": "butcher's cleaver", "qty": 1,
             "desc": "Recover the Butcher's cleaver (0/1)"},
            {"type": "deliver", "target": "captain aethelflaed", "qty": 1,
             "desc": "Return to Captain Aethelflaed with proof (0/1)"},
        ],
        "rewards": {"silver": 60, "items": [], "reagents": {}},
        "prereqs": ["second_expedition"],
    },

    "man_on_the_run": {
        "key": "man_on_the_run",
        "title": "Man on the Run",
        "giver": "captain thelmer of the stag watch",
        "description": (
            "Lynden, a convicted murderer awaiting the rope, broke out of "
            "the Stag Watch's stocks during the festival and fled into "
            "the Thornwood. The fort wants him back — dead or alive — "
            "before he disappears into the woods for good."
        ),
        "outcomes": {
            "bring_him_dead": {
                "label": "Kill Lynden and bring proof",
                "description": (
                    "Put Lynden down and recover his confession as proof. "
                    "The Crown and the Stag Watch reward decisiveness."
                ),
                "objectives": [
                    {"type": "kill", "target": "lynden the murderer", "qty": 1,
                     "desc": "Kill Lynden the Murderer (0/1)"},
                    {"type": "gather", "target": "lynden's confession", "qty": 1,
                     "desc": "Recover Lynden's confession (0/1)"},
                    {"type": "deliver", "target": "captain thelmer of the stag watch",
                     "qty": 1, "desc": "Return to Captain Thelmer (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"crown": 3, "outlaws": -1},
            },
            "take_him_alive": {
                "label": "Take Lynden alive for trial",
                "description": (
                    "Bring Lynden back so the fort can hang him properly. "
                    "Extra coin, the Aurorym's quiet approval, but the "
                    "harder path."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Thornwood Edge", "qty": 1,
                     "desc": "Track Lynden to the Thornwood Edge (0/1)"},
                    {"type": "gather", "target": "lynden's confession", "qty": 1,
                     "desc": "Confiscate Lynden's confession (0/1)"},
                    {"type": "deliver", "target": "captain thelmer of the stag watch",
                     "qty": 1, "desc": "Hand over the confession for the trial (0/1)"},
                ],
                "rewards": {"silver": 40, "items": [], "reagents": {}},
                "faction_rep": {"crown": 4},
            },
            "let_him_run": {
                "label": "Let Lynden disappear into the woods",
                "description": (
                    "The Thornwood will handle him one way or another. "
                    "Walk away. No Crown coin, but the outlaw network "
                    "remembers names."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Thornwood Edge", "qty": 1,
                     "desc": "Follow Lynden to the Thornwood Edge (0/1)"},
                ],
                "rewards": {"silver": 0, "items": [], "reagents": {}},
                "faction_rep": {"crown": -2, "outlaws": 2},
            },
        },
        "prereqs": [],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # EVENT 2 — BATCH 1 EXPANSIONS (2026-06-10)
    # Source: Drive / Reboot / Event 2 - The Wrath — The Herbalist;
    # The Sea Witch ("The Albatross Doom, Part I").
    # ─────────────────────────────────────────────────────────────────────────
    "the_herbalist": {
        "key": "the_herbalist",
        "title": "The Herbalist's Lesson",
        "giver": "magister marionne",
        "description": (
            "Magister Marionne of Hartwood has set up her travelling "
            "still at the Herbalist's Garden and is lecturing to anyone "
            "with the sense to listen. She pays for clean-picked "
            "Orgonnian grapes — and pays better in knowledge than "
            "in coin."
        ),
        "objectives": [
            {"type": "talk", "target": "magister marionne",
             "topic": "herbalism", "qty": 1,
             "desc": "Attend Marionne's herbalism lesson (0/1)"},
            {"type": "gather", "target": "orgonnian grapes", "qty": 3,
             "desc": "Pick clean bunches of Orgonnian grapes (0/3)"},
            {"type": "deliver", "target": "magister marionne", "qty": 1,
             "desc": "Bring the grapes to Marionne (0/1)"},
        ],
        "rewards": {
            "silver": 10,
            "items": [],
            "reagents": {"Verbaena": 2, "Willow Root": 2, "Celandine": 1},
        },
        "prereqs": [],
    },

    "the_sea_witch": {
        "key": "the_sea_witch",
        "title": "The Sea Witch",
        "giver": "captain phoenix swallowsong",
        "description": (
            "Captain Phoenix Swallowsong — the Sea Witch — holds the "
            "darkest booth in the Broken Oar and pays silver for what "
            "she calls 'weather': rumors, routes, and who's moving "
            "what. Bring her tribute worth her time and ask about the "
            "ghost-ship her sailors won't name twice."
        ),
        "objectives": [
            {"type": "deliver", "target": "captain phoenix swallowsong",
             "qty": 1, "desc": "Bring the Sea Witch tribute worth her time (0/1)"},
            {"type": "talk", "target": "captain phoenix swallowsong",
             "topic": "sea wolf", "qty": 1,
             "desc": "Ask her about the Sea Wolf (0/1)"},
        ],
        "rewards": {"silver": 30, "items": [], "reagents": {}},
        "prereqs": ["caravan_attack"],
    },
}
