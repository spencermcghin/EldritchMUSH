"""Event 3 — The Awakening (Chapter III).
Source: Drive / Reboot / Event 3 - The Awakening (folder 1ncmu_zzlYnJNzEK7DPm0z17YkaJMKeel).

Quest dict format: see world/quests/__init__.py.
"""

QUESTS = {

    # ─────────────────────────────────────────────────────────────────────────
    # EVENT 3 — THE AWAKENING (anchor quests)
    # Source: Drive / Reboot / Event 3 / "Chapter III — The Awakening".
    # Maps to the three Decisive Moments + a Mistguard combat anchor.
    # ─────────────────────────────────────────────────────────────────────────
    "dawnhaven_aid": {
        "key": "dawnhaven_aid",
        "title": "Dawnhaven Aid",
        "giver": "sister mariel",
        "description": (
            "Sister Mariel leads the Aurorym pilgrim camp at Dawnhaven, "
            "ten miles north of Mystvale. The camp is short on food, "
            "lumber, and medicine — and Crow raiders are picking off "
            "every supply caravan that approaches. She'll take help in "
            "any form a willing hand can offer."
        ),
        "outcomes": {
            "gather_supplies": {
                "label": "Bring supplies up from Mystvale",
                "description": (
                    "Fill the Dawnhaven supply chest from Mystvale's "
                    "stores. Honest work; Aurorym remembers."
                ),
                "objectives": [
                    {"type": "gather", "target": "dawnhaven supply chest", "qty": 1,
                     "desc": "Take the supply chest (0/1)"},
                    {"type": "deliver", "target": "sister mariel", "qty": 1,
                     "desc": "Return the filled chest to Sister Mariel (0/1)"},
                ],
                "rewards": {"silver": 25, "items": [], "reagents": {}},
                "faction_rep": {"crown": 2, "outsider": 1},
                "npc_rep_deltas": {"sister mariel": 5, "curate godrick": 2},
                "npc_memories": {
                    "sister mariel": "kept the camp alive through Winter's edge",
                    "curate godrick": "did right by the faithful",
                },
            },
            "fight_crows": {
                "label": "Hunt Crow raiders threatening the camp",
                "description": (
                    "Take the fight to the Crows preying on Dawnhaven's "
                    "supply lines. Bloodier path; the Aurorym remembers "
                    "harder."
                ),
                "objectives": [
                    {"type": "kill", "target": "caravan raider", "qty": 3,
                     "desc": "Drive off Crow raiders (0/3)"},
                    {"type": "deliver", "target": "sister mariel", "qty": 1,
                     "desc": "Report back to Sister Mariel (0/1)"},
                ],
                "rewards": {"silver": 35, "items": [], "reagents": {}},
                "faction_rep": {"crown": 3, "crows": -3},
                "npc_rep_deltas": {"sister mariel": 6, "curate godrick": 3},
                "npc_memories": {
                    "sister mariel": "spilled blood for the faithful",
                    "curate godrick": "took the war to the Crows",
                },
            },
        },
        "prereqs": [],
    },

    "witch_cult_invitation": {
        "key": "witch_cult_invitation",
        "title": "The Wytch Cult's Invitation",
        "giver": "the masked stranger",
        "description": (
            "A figure in a deer-skull mask waits at the edge of the "
            "Thornwood. The cult is recruiting; the protection they "
            "offer comes with a bone token and a price you may not "
            "yet understand."
        ),
        "outcomes": {
            "accept_token": {
                "label": "Accept the bone token",
                "description": (
                    "Take the cult's mark. The witches mean their "
                    "protection. The Aurorym mean their condemnation."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Thornwood Edge", "qty": 1,
                     "desc": "Meet the masked stranger (0/1)"},
                    {"type": "gather", "target": "bone token", "qty": 1,
                     "desc": "Accept the bone token (0/1)"},
                ],
                "rewards": {"silver": 0, "items": [], "reagents": {}},
                "faction_rep": {"crown": -3, "outlaws": 2, "outsider": 3},
                "npc_rep_deltas": {"the masked stranger": 5, "sister mariel": -5},
                "npc_memories": {
                    "the masked stranger": "knelt and was spared",
                    "sister mariel": "took the cult's mark",
                },
            },
            "refuse_walk_away": {
                "label": "Refuse and walk away",
                "description": (
                    "No alliance, no warning to the watch — just turn "
                    "and leave. Neutral ground, but the witches notice."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Thornwood Edge", "qty": 1,
                     "desc": "Meet the masked stranger (0/1)"},
                    {"type": "explore", "target": "The Mystvale Marketplace", "qty": 1,
                     "desc": "Walk back to Mystvale without speaking (0/1)"},
                ],
                "rewards": {"silver": 0, "items": [], "reagents": {}},
                "faction_rep": {"outsider": 1},
                "npc_rep_deltas": {"the masked stranger": -1},
                "npc_memories": {"the masked stranger": "refused the offer"},
            },
            "report_to_watch": {
                "label": "Report the cult emissary to the watch",
                "description": (
                    "Take the bone token as evidence. The Mistguard pays "
                    "in coin and the Aurorym pays in approval."
                ),
                "objectives": [
                    {"type": "gather", "target": "bone token", "qty": 1,
                     "desc": "Pocket the bone token as evidence (0/1)"},
                    {"type": "deliver", "target": "captain vance of the mistguard",
                     "qty": 1, "desc": "Hand the token to Captain Vance (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"crown": 4, "outlaws": -2},
                "npc_rep_deltas": {
                    "captain vance of the mistguard": 4,
                    "sister mariel": 3,
                    "the masked stranger": -10,
                },
                "npc_memories": {
                    "captain vance of the mistguard": "brought a Wytch Cult emissary in",
                    "sister mariel": "stood with the faithful against the witches",
                    "the masked stranger": "betrayed the offering",
                },
            },
        },
        "prereqs": [],
    },

    "mistvale_refuge": {
        "key": "mistvale_refuge",
        "title": "Mistvale Refuge",
        "giver": "burgomaster domitille",
        "description": (
            "Refugees from Carran, Arcton, and Ironhaven are flooding "
            "Mystvale's south gate, fleeing the witchcraft plague. "
            "Burgomaster Domitille needs help — but how the help is "
            "rendered will mark Mystvale for the rest of Winter."
        ),
        "outcomes": {
            "shelter_them": {
                "label": "Shelter the refugees freely",
                "description": (
                    "Open Mystvale's doors to the refugees. The Crown "
                    "approves; the town's resources thin."
                ),
                "objectives": [
                    {"type": "gather", "target": "refugee elder's letter", "qty": 1,
                     "desc": "Take the refugee elder's letter (0/1)"},
                    {"type": "deliver", "target": "burgomaster domitille", "qty": 1,
                     "desc": "Argue for shelter to Burgomaster Domitille (0/1)"},
                ],
                "rewards": {"silver": 15, "items": [], "reagents": {}},
                "faction_rep": {"crown": 2, "cirque": 1, "outsider": 2},
                "npc_rep_deltas": {"burgomaster domitille": 4},
                "npc_memories": {"burgomaster domitille": "argued for the refugees"},
            },
            "charge_a_fee": {
                "label": "Charge a settlement fee",
                "description": (
                    "Refugees stay only if they pay. Some town coffers "
                    "fattened, some refugees turned to the woods."
                ),
                "objectives": [
                    {"type": "gather", "target": "refugee elder's letter", "qty": 1,
                     "desc": "Take the refugee elder's letter (0/1)"},
                    {"type": "deliver", "target": "burgomaster domitille", "qty": 1,
                     "desc": "Propose the fee to Burgomaster Domitille (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"crown": 1, "outlaws": 1, "outsider": -2},
                "npc_rep_deltas": {"burgomaster domitille": 1},
                "npc_memories": {"burgomaster domitille": "found a profit in the suffering"},
            },
            "turn_them_away": {
                "label": "Turn the refugees away",
                "description": (
                    "Mystvale's resources are too thin; tell them to "
                    "walk on. Cold pragmatism — and a long memory in "
                    "the people you turned away."
                ),
                "objectives": [
                    {"type": "deliver", "target": "burgomaster domitille", "qty": 1,
                     "desc": "Convince Burgomaster Domitille to refuse (0/1)"},
                ],
                "rewards": {"silver": 5, "items": [], "reagents": {}},
                "faction_rep": {"crown": -1, "outsider": -4},
                "npc_rep_deltas": {"burgomaster domitille": -2},
                "npc_memories": {"burgomaster domitille": "shut Mystvale's gate to the desperate"},
            },
        },
        "prereqs": [],
    },

    "gateway_under_siege": {
        "key": "gateway_under_siege",
        "title": "Gateway Under Siege",
        "giver": "captain vance of the mistguard",
        "description": (
            "Ten thousand Richter Iron Guard are marching on Gateway. "
            "The Mistguard is two hundred. Captain Vance offers three "
            "ways to act on it — none of them clean."
        ),
        "outcomes": {
            "hold_the_line": {
                "label": "Hold the line — kill the Iron Guard scouts",
                "description": (
                    "Take the fight forward. Kill the Iron Guard scouts "
                    "before they map the Mistwall's defences."
                ),
                "objectives": [
                    {"type": "kill", "target": "iron guard scout", "qty": 3,
                     "desc": "Cut down the Iron Guard scouts (0/3)"},
                    {"type": "deliver", "target": "captain vance of the mistguard",
                     "qty": 1, "desc": "Report back to Captain Vance (0/1)"},
                ],
                "rewards": {"silver": 50, "items": [], "reagents": {}},
                "faction_rep": {"crown": 4, "crows": 1},
                "npc_rep_deltas": {"captain vance of the mistguard": 7},
                "npc_memories": {"captain vance of the mistguard": "stood the line at the Mistwall"},
            },
            "negotiate": {
                "label": "Carry the herald's writ to Vance unopened",
                "description": (
                    "Recover the Richter herald's surrender writ and "
                    "give it to Vance to consider. Soft path — the "
                    "Crown thinks less of you, but lives are saved."
                ),
                "objectives": [
                    {"type": "gather", "target": "richter herald's writ", "qty": 1,
                     "desc": "Take the Richter herald's writ (0/1)"},
                    {"type": "deliver", "target": "captain vance of the mistguard",
                     "qty": 1, "desc": "Hand the writ to Captain Vance unopened (0/1)"},
                ],
                "rewards": {"silver": 25, "items": [], "reagents": {}},
                "faction_rep": {"crown": -1, "outsider": 2},
                "npc_rep_deltas": {"captain vance of the mistguard": 2},
                "npc_memories": {"captain vance of the mistguard": "brought terms instead of bodies"},
            },
            "desert": {
                "label": "Desert and slip into the Annwyn",
                "description": (
                    "Walk away from the Mistwall. Iron Guard or no, "
                    "this is not your fight. The Mistguard won't forget "
                    "the empty post."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Mystvale Marketplace", "qty": 1,
                     "desc": "Slip back to Mystvale unnoticed (0/1)"},
                ],
                "rewards": {"silver": 0, "items": [], "reagents": {}},
                "faction_rep": {"crown": -4, "outsider": 3, "outlaws": 1},
                "npc_rep_deltas": {"captain vance of the mistguard": -8},
                "npc_memories": {"captain vance of the mistguard": "abandoned the wall"},
            },
        },
        "prereqs": [],
    },

    # ─── Event 2 backlog encounters (after the Friday + Saturday anchors) ──
    "into_the_woods": {
        "key": "into_the_woods",
        "title": "Into the Woods",
        "giver": "captain thelmer of the stag watch",
        "description": (
            "Captain Thelmer wants a patrol pushed past the Old Road and "
            "into the Thornwood proper before nightfall. The signs of "
            "the Fair Folk are turning into something worse. Bring back "
            "what you find — a signal-fire, tracks, anything."
        ),
        "objectives": [
            {"type": "explore", "target": "The Thornwood Edge", "qty": 1,
             "desc": "Patrol to the Thornwood Edge (0/1)"},
            {"type": "gather", "target": "crow signal-fire", "qty": 1,
             "desc": "Recover a Crow signal-fire (0/1)"},
            {"type": "gather", "target": "scattered tracks", "qty": 1,
             "desc": "Note the scattered tracks (0/1)"},
            {"type": "deliver", "target": "captain thelmer of the stag watch",
             "qty": 1, "desc": "Report your patrol findings (0/1)"},
        ],
        "rewards": {"silver": 18, "items": [], "reagents": {}},
        "npc_rep_deltas": {"captain thelmer of the stag watch": 3},
        "npc_memories": {"captain thelmer of the stag watch": "ran a clean patrol of the Thornwood Edge"},
        "prereqs": [],
    },

    "murder_most_foul_pt1": {
        "key": "murder_most_foul_pt1",
        "title": "Murder Most Foul",
        "giver": "captain thelmer of the stag watch",
        "description": (
            "A pilgrim's body has turned up in Stag Hall's courtyard — "
            "throat cut, killer unknown. Thelmer wants the case worked: "
            "examine the body, find any evidence, find someone who saw."
        ),
        "objectives": [
            {"type": "gather", "target": "victim's body", "qty": 1,
             "desc": "Examine the victim's body (0/1)"},
            {"type": "gather", "target": "bloodstained letter", "qty": 1,
             "desc": "Recover the bloodstained letter (0/1)"},
            {"type": "deliver", "target": "old inga", "qty": 1,
             "desc": "Get Old Inga's testimony (0/1)"},
        ],
        "rewards": {"silver": 20, "items": [], "reagents": {}},
        "prereqs": [],
    },

    "murder_most_foul_pt2": {
        "key": "murder_most_foul_pt2",
        "title": "Murder Most Foul: The Reckoning",
        "giver": "captain thelmer of the stag watch",
        "description": (
            "Old Inga's testimony names Lynden. The case is closed — "
            "but Thelmer leaves the verdict to you. Execute the "
            "murderer where he stands, drag him back for trial, or "
            "something less merciful that the watch won't formally "
            "acknowledge."
        ),
        "outcomes": {
            "execute_at_thornwood": {
                "label": "Execute Lynden in the Thornwood",
                "description": (
                    "Justice with a knife. Quick, quiet, no trial. The "
                    "Crown nods; the outlaws note your name."
                ),
                "objectives": [
                    {"type": "kill", "target": "lynden the murderer", "qty": 1,
                     "desc": "Execute Lynden in the Thornwood (0/1)"},
                    {"type": "deliver", "target": "captain thelmer of the stag watch",
                     "qty": 1, "desc": "Report the deed done (0/1)"},
                ],
                "rewards": {"silver": 25, "items": [], "reagents": {}},
                "faction_rep": {"crown": 2, "outlaws": -2},
                "npc_rep_deltas": {"captain thelmer of the stag watch": 4},
                "npc_memories": {"captain thelmer of the stag watch": "dispatched Lynden cleanly"},
            },
            "drag_back_for_trial": {
                "label": "Drag Lynden back for public trial",
                "description": (
                    "By the book. Slow. Costs more, gains the Aurorym's "
                    "respect, and sets a public example."
                ),
                "objectives": [
                    {"type": "gather", "target": "lynden's confession", "qty": 1,
                     "desc": "Take Lynden's confession (0/1)"},
                    {"type": "deliver", "target": "captain thelmer of the stag watch",
                     "qty": 1, "desc": "Hand Lynden over for trial (0/1)"},
                ],
                "rewards": {"silver": 35, "items": [], "reagents": {}},
                "faction_rep": {"crown": 4, "cirque": 1},
                "npc_rep_deltas": {
                    "captain thelmer of the stag watch": 5,
                    "curate godrick": 3,
                },
                "npc_memories": {
                    "captain thelmer of the stag watch": "honored the law over the easy kill",
                    "curate godrick": "saw the law done properly",
                },
            },
            "let_thornwood_take_him": {
                "label": "Leave Lynden for the Thornwood",
                "description": (
                    "Don't kill him. Don't catch him. Let the witches do "
                    "what they're already going to do. Closes the case "
                    "without your hands on it."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Thornwood Edge", "qty": 1,
                     "desc": "Confirm Lynden is in the Thornwood (0/1)"},
                    {"type": "deliver", "target": "captain thelmer of the stag watch",
                     "qty": 1, "desc": "Report Lynden 'lost in the woods' (0/1)"},
                ],
                "rewards": {"silver": 15, "items": [], "reagents": {}},
                "faction_rep": {"crown": -1, "outlaws": 1, "outsider": 2},
                "npc_rep_deltas": {"captain thelmer of the stag watch": -1},
                "npc_memories": {"captain thelmer of the stag watch": "gave him a Thornwood verdict"},
            },
        },
        "prereqs": ["murder_most_foul_pt1", "man_on_the_run"],
    },

    "the_heist_pt2": {
        "key": "the_heist_pt2",
        "title": "The Heist: False Bottom",
        "giver": "quill the fixer",
        "description": (
            "The Laurent strongbox had a false bottom. What was inside "
            "is bigger than a smash-and-grab — Crown ledger pages, named "
            "debts, a sealed letter of credit. Quill wants a partner "
            "for the next move; the watch wants the truth before "
            "anyone moves at all."
        ),
        "outcomes": {
            "split_with_quill": {
                "label": "Split the false-bottom take with Quill",
                "description": (
                    "Move the papers through Quill's fence. Cleanest "
                    "way out. Quill remembers a partner who delivers."
                ),
                "objectives": [
                    {"type": "gather", "target": "false-bottom papers", "qty": 1,
                     "desc": "Pry out the false-bottom papers (0/1)"},
                    {"type": "deliver", "target": "quill the fixer", "qty": 1,
                     "desc": "Hand the papers to Quill (0/1)"},
                ],
                "rewards": {"silver": 60, "items": [], "reagents": {}},
                "faction_rep": {"crown": -3, "outlaws": 4, "crows": 1},
                "npc_rep_deltas": {"quill the fixer": 6},
                "npc_memories": {"quill the fixer": "delivered the false-bottom papers without skimming"},
            },
            "turn_the_papers_in": {
                "label": "Turn the papers over to the watch",
                "description": (
                    "Hand the false-bottom evidence to Captain Thelmer. "
                    "The Crown rewards loyalty; Quill remembers betrayal."
                ),
                "objectives": [
                    {"type": "gather", "target": "false-bottom papers", "qty": 1,
                     "desc": "Pry out the false-bottom papers (0/1)"},
                    {"type": "deliver", "target": "captain thelmer of the stag watch",
                     "qty": 1, "desc": "Hand the papers to the watch (0/1)"},
                ],
                "rewards": {"silver": 40, "items": [], "reagents": {}},
                "faction_rep": {"crown": 5, "outlaws": -5},
                "npc_rep_deltas": {
                    "quill the fixer": -8,
                    "captain thelmer of the stag watch": 5,
                },
                "npc_memories": {
                    "quill the fixer": "burned me with the false-bottom papers",
                    "captain thelmer of the stag watch": "gave the Crown its evidence",
                },
            },
        },
        # Either pull_the_job or flip_to_watch from the_heist Pt 1
        # qualifies — the false-bottom complication arrives no matter
        # which path the player took on Pt 1.
        "prereqs": ["the_heist"],
    },

    "rise_of_the_underworld": {
        "key": "rise_of_the_underworld",
        "title": "Rise of the Underworld",
        "giver": "quill the fixer",
        "description": (
            "Knuckles the Bruiser is moving on Quill's network. Quill "
            "asks for help putting him down — or, if the player is more "
            "ambitious, replacing Quill with Knuckles instead. The Back "
            "Alley is going to belong to someone after tonight."
        ),
        "outcomes": {
            "back_quill": {
                "label": "Put Knuckles down for Quill",
                "description": (
                    "Side with Quill. The Back Alley remembers the "
                    "people who keep their bargains."
                ),
                "objectives": [
                    {"type": "kill", "target": "knuckles the bruiser", "qty": 1,
                     "desc": "Defeat Knuckles the Bruiser (0/1)"},
                    {"type": "deliver", "target": "quill the fixer", "qty": 1,
                     "desc": "Report to Quill (0/1)"},
                ],
                "rewards": {"silver": 35, "items": [], "reagents": {}},
                "faction_rep": {"outlaws": 4, "crown": -1},
                "npc_rep_deltas": {"quill the fixer": 8},
                "npc_memories": {"quill the fixer": "stood with me against Knuckles"},
            },
            "back_knuckles": {
                "label": "Help Knuckles take Quill's network",
                "description": (
                    "Back the upstart. Knuckles owes you the Back Alley "
                    "afterward. Quill is a much smaller problem dead "
                    "than alive."
                ),
                "objectives": [
                    {"type": "kill", "target": "quill the fixer", "qty": 1,
                     "desc": "Eliminate Quill (0/1)"},
                    {"type": "deliver", "target": "knuckles the bruiser", "qty": 1,
                     "desc": "Confirm to Knuckles (0/1)"},
                ],
                "rewards": {"silver": 50, "items": [], "reagents": {}},
                "faction_rep": {"outlaws": 2, "crows": 1, "crown": -2},
                "npc_rep_deltas": {"knuckles the bruiser": 8, "quill the fixer": -100},
                "npc_memories": {
                    "knuckles the bruiser": "put Quill in the ground for me",
                },
            },
        },
        "prereqs": ["the_heist"],
    },

    "a_colds_winters_tale": {
        "key": "a_colds_winters_tale",
        "title": "A Cold Winter's Tale",
        "giver": "old threnody",
        "description": (
            "Old Threnody at the Broken Oar will sing a Volgan witch-"
            "tale older than the Houses if the silver crosses her palm. "
            "It is the kind of story whispered around fires that should "
            "not go out — and there are reasons to know it tonight."
        ),
        "objectives": [
            {"type": "explore", "target": "The Broken Oar", "qty": 1,
             "desc": "Settle in at the Broken Oar (0/1)"},
            {"type": "deliver", "target": "old threnody", "qty": 1,
             "desc": "Cross Threnody's palm with silver (0/1)"},
            {"type": "gather", "target": "volgan winter-tale fragment", "qty": 1,
             "desc": "Take the tale fragment she leaves you (0/1)"},
        ],
        "rewards": {"silver": 0, "items": [], "reagents": {}},
        "prereqs": [],
    },

    "tale_to_remember": {
        "key": "tale_to_remember",
        "title": "A Tale to Remember",
        "giver": "kestren the bard",
        "description": (
            "Kestren the bard sings old Arnessian mythology at the "
            "Songbird's Rest — the First Hunt, the Constellations, the "
            "fall of Dun Siarach. Listen to her tale and tip well; she "
            "keeps written fragments of the oldest stories for the patrons "
            "who reward her properly."
        ),
        "objectives": [
            {"type": "explore", "target": "Songbird's Rest",
             "qty": 1, "desc": "Listen to Kestren's tale at the tavern (0/1)"},
            {"type": "deliver", "target": "kestren the bard", "qty": 1,
             "desc": "Tip Kestren with anything from your pack (0/1)"},
        ],
        "rewards": {
            "silver": 0,
            "items": ["MORPHOS_LORE_SCROLL"],
            "reagents": {},
        },
        "prereqs": [],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # EVENT 3 — BATCH 1 EXPANSIONS (2026-06-10)
    # Source: Drive / Reboot / Event 3 - The Awakening — Crow Tolls /
    # Crippled Crow / Tempest's Revenge III-V / Heist Pt 3 / Murder Pt III.
    # ─────────────────────────────────────────────────────────────────────────
    "crow_tolls": {
        "key": "crow_tolls",
        "title": "The Crow Toll",
        "giver": "captain thelmer of the stag watch",
        "description": (
            "The Crows have hung a toll-gate on the Forest Road — one "
            "silver a head, collected by a reeve with a tally-cord and "
            "two bored tollmen. Thelmer wants the road open. How it "
            "opens is your business."
        ),
        "outcomes": {
            "break_the_racket": {
                "label": "Break the toll racket by force",
                "description": (
                    "Put the tollmen down and scatter the gate. The "
                    "road opens; the Crows remember."
                ),
                "objectives": [
                    {"type": "kill", "target": "crow tollman", "qty": 2,
                     "desc": "Drive off the Crow tollmen (0/2)"},
                    {"type": "deliver", "target": "captain thelmer of the stag watch",
                     "qty": 1, "desc": "Report the road cleared (0/1)"},
                ],
                "rewards": {"silver": 25, "items": [], "reagents": {}},
                "faction_rep": {"crown": 3, "crows": -3},
                "npc_rep_deltas": {"captain thelmer of the stag watch": 3},
                "npc_memories": {"captain thelmer of the stag watch":
                                 "broke the Crow toll-gate on the Forest Road"},
            },
            "learn_the_passphrase": {
                "label": "Learn the Crow passphrase and walk through",
                "description": (
                    "There's a phrase that opens that gate for free. "
                    "Speak it to the reeve and report what you learn — "
                    "or keep what you learn for yourself."
                ),
                "objectives": [
                    {"type": "talk", "target": "crow toll-reeve",
                     "topic": "uncaged", "qty": 1,
                     "desc": "Give the reeve the Crow passphrase (0/1)"},
                    {"type": "deliver", "target": "captain thelmer of the stag watch",
                     "qty": 1, "desc": "Report the gate's workings to Thelmer (0/1)"},
                ],
                "rewards": {"silver": 15, "items": [], "reagents": {}},
                "faction_rep": {"crown": 1, "crows": 2},
                "npc_rep_deltas": {"crow toll-reeve": 3},
                "npc_memories": {"crow toll-reeve":
                                 "knew the passphrase and was waved through as kin"},
            },
        },
        "prereqs": [],
    },

    "the_crippled_crow": {
        "key": "the_crippled_crow",
        "title": "The Crippled Crow",
        "giver": "feargus the lame crow",
        "description": (
            "A lamed Crow deserter begs at the south gate, one eye on "
            "every shadow — Cale the Thorn doesn't pension his people "
            "off. He needs a meal and, though he'd never ask, a medic "
            "willing to mend a badly-set leg. Or the watch would pay "
            "to know exactly where he sits."
        ),
        "outcomes": {
            "show_kindness": {
                "label": "Feed him and win his trust",
                "description": (
                    "Kindness first. A fed Feargus talks — about tolls, "
                    "rotations, and the words that open Crow gates."
                ),
                "objectives": [
                    {"type": "deliver", "target": "feargus the lame crow",
                     "qty": 1,
                     "desc": "Give Feargus a meal or something useful (0/1)"},
                ],
                "rewards": {"silver": 5, "items": [], "reagents": {"Sayge": 2}},
                "faction_rep": {"crows": 2, "outsider": 1},
                "npc_rep_deltas": {"feargus the lame crow": 6},
                "npc_memories": {"feargus the lame crow":
                                 "showed him kindness when the whole vale looked away"},
            },
            "mend_his_leg": {
                "label": "Feed him AND mend his crippled leg",
                "description": (
                    "He never imagined anyone would look at the leg — it "
                    "was set crooked two winters back and he'd written it "
                    "off. A skilled medic could rebreak and set it true. "
                    "(Feed him first, then |wtreat feargus|n — needs the "
                    "medicine skill.)"
                ),
                "objectives": [
                    {"type": "deliver", "target": "feargus the lame crow",
                     "tag": "fed", "qty": 1,
                     "desc": "Give Feargus a meal or something useful (0/1)"},
                    {"type": "skill", "target": "feargus the lame crow",
                     "skill": "medicine", "requires": "fed", "qty": 1,
                     "desc": "Once he trusts you, tend his badly-set leg (0/1)"},
                ],
                "rewards": {"silver": 10, "items": [], "reagents": {"Sayge": 3}},
                "faction_rep": {"crows": 3, "outsider": 2},
                "npc_rep_deltas": {"feargus the lame crow": 10},
                "npc_memories": {"feargus the lame crow":
                                 "gave him back his stride when no one else would even look"},
            },
            "sell_him_out": {
                "label": "Report him to the watch",
                "description": (
                    "A deserter with Crow knowledge is worth coin to "
                    "the Stag Watch. Feargus will find out who told."
                ),
                "objectives": [
                    {"type": "talk", "target": "feargus the lame crow",
                     "topic": "crows", "qty": 1,
                     "desc": "Draw Feargus out about the Crows (0/1)"},
                    {"type": "deliver", "target": "captain thelmer of the stag watch",
                     "qty": 1, "desc": "Report the deserter to Thelmer (0/1)"},
                ],
                "rewards": {"silver": 20, "items": [], "reagents": {}},
                "faction_rep": {"crown": 2, "crows": -2},
                "npc_rep_deltas": {"feargus the lame crow": -8},
                "npc_memories": {"feargus the lame crow":
                                 "sold him to the watch after he talked"},
            },
        },
        "prereqs": [],
    },

    "tempest_damned_crew": {
        "key": "tempest_damned_crew",
        "title": "Tempest's Revenge: The Damned Crew",
        "giver": "kestren the bard",
        "description": (
            "Kestren's sea-wolf legend was no legend. Fog has settled "
            "over the Broken Pier and drowned sailors walk it, chains "
            "grown into their wrists, mouthing one word over and over. "
            "She knows the word — the old shanty-law that even the "
            "damned must honor."
        ),
        "outcomes": {
            "honor_the_parlay": {
                "label": "Walk the pier and call for parlay",
                "description": (
                    "Sea-law older than drowning: call parlay, and the "
                    "dead must hear you out."
                ),
                "objectives": [
                    {"type": "explore", "target": "Tamris Harbor — The Broken Pier",
                     "qty": 1, "desc": "Walk the fogbound Broken Pier (0/1)"},
                    {"type": "talk", "target": "black sam tempest",
                     "topic": "parlay", "qty": 1,
                     "desc": "Call parlay with the dead captain (0/1)"},
                ],
                "rewards": {"silver": 15, "items": [], "reagents": {}},
                "faction_rep": {"outsider": 2},
                "npc_rep_deltas": {"black sam tempest": 4},
                "npc_memories": {"black sam tempest":
                                 "honored parlay like a proper sailor"},
            },
            "drive_them_back": {
                "label": "Drive the damned crew back into the water",
                "description": (
                    "Steel works on the drowned, after a fashion. It "
                    "doesn't work on what sent them."
                ),
                "objectives": [
                    {"type": "kill", "target": "ghost of the damned crew", "qty": 3,
                     "desc": "Scatter the damned crew on the pier (0/3)"},
                    {"type": "deliver", "target": "kestren the bard", "qty": 1,
                     "desc": "Bring Kestren proof for her next verse (0/1)"},
                ],
                "rewards": {"silver": 25, "items": [], "reagents": {}},
                "faction_rep": {"crown": 1, "outsider": -1},
                "npc_rep_deltas": {"black sam tempest": -4},
                "npc_memories": {"black sam tempest":
                                 "raised steel against his crew instead of honoring parlay"},
            },
        },
        "prereqs": ["tale_to_remember"],
    },

    "tempest_captain_returns": {
        "key": "tempest_captain_returns",
        "title": "Tempest's Revenge: The Captain Returns",
        "giver": "kestren the bard",
        "description": (
            "Black Sam Tempest has come for what is his. His cursed "
            "coin is scattered through Mystvale's purses and floorboards "
            "— and everyone holding a piece of it dies with the tide "
            "unless every last coin goes back. Gather the black-spotted "
            "gold and settle the dead captain's account."
        ),
        "objectives": [
            {"type": "gather", "target": "cursed coin", "qty": 5,
             "desc": "Gather the black-spotted coins scattered through the vale (0/5)"},
            {"type": "deliver", "target": "black sam tempest",
             "item": "cursed coin", "qty": 5,
             "desc": "Return EVERY cursed coin to Black Sam at the Broken Pier (0/5)"},
        ],
        "rewards": {
            "silver": 20,
            "items": ["WATERLOGGED_PISTOL"],
            "reagents": {},
        },
        "prereqs": ["tempest_damned_crew"],
    },

    "heist_pt3_cat_sith": {
        "key": "heist_pt3_cat_sith",
        "title": "The Heist: Rescue the Cat Sith",
        "giver": "quill the fixer",
        "description": (
            "The false-bottom papers named the place: a Laurent "
            "waystation on the Old Road, where a star-marked chest "
            "waits for the morning vault-wagon — and inside it, the "
            "Cat Sith idol the Innis have hunted for two seasons. "
            "Quill wants it lifted tonight. There's a password, a "
            "nervous courier who knows it, and two guards who don't "
            "have to die."
        ),
        "outcomes": {
            "quiet_job": {
                "label": "Talk your way in with the password",
                "description": (
                    "The courier leaks like a holed skiff. Get the "
                    "password out of him, walk past the guards like "
                    "you belong, and lift the idol clean."
                ),
                "objectives": [
                    {"type": "talk", "target": "laurent waystation messenger",
                     "topic": "password", "tag": "password", "qty": 1,
                     "desc": "Coax the password out of the courier (0/1)"},
                    {"type": "gather", "target": "cat sith idol", "qty": 1,
                     "requires": "password",
                     "desc": "With the password, lift the Cat Sith idol from the star-marked chest (0/1)"},
                    {"type": "deliver", "target": "quill the fixer", "qty": 1,
                     "desc": "Deliver the idol to Quill (0/1)"},
                ],
                "rewards": {"silver": 70, "items": [], "reagents": {}},
                "faction_rep": {"outlaws": 4, "crown": -2},
                "npc_rep_deltas": {"quill the fixer": 6},
                "npc_memories": {"quill the fixer":
                                 "lifted the Cat Sith without a drop of blood — an artist"},
            },
            "loud_job": {
                "label": "Put the guards down and take it",
                "description": (
                    "No finesse, no witnesses standing. The Laurents "
                    "will know, and so will everyone else."
                ),
                "objectives": [
                    {"type": "kill", "target": "laurent waystation guard", "qty": 2,
                     "desc": "Deal with the waystation guards (0/2)"},
                    {"type": "gather", "target": "cat sith idol", "qty": 1,
                     "desc": "Take the Cat Sith idol (0/1)"},
                    {"type": "deliver", "target": "quill the fixer", "qty": 1,
                     "desc": "Deliver the idol to Quill (0/1)"},
                ],
                "rewards": {"silver": 55, "items": [], "reagents": {}},
                "faction_rep": {"outlaws": 3, "crown": -4},
                "npc_rep_deltas": {"quill the fixer": 3},
                "npc_memories": {"quill the fixer":
                                 "got the idol, loudly — competent, but the heat was real"},
            },
        },
        "prereqs": [{"quest": "the_heist_pt2", "outcome": "split_with_quill"}],
    },

    "murder_most_foul_pt3": {
        "key": "murder_most_foul_pt3",
        "title": "Murder Most Foul: Shireen Revealed",
        "giver": "captain thelmer of the stag watch",
        "description": (
            "Lynden is dealt with — and the killings haven't stopped. "
            "Same glyph, same verdicts, new hand. Thelmer's trackers "
            "followed the cold up to the Thornwood Edge and refused to "
            "go further. Whatever judges 'the guilty' out there wears "
            "a veil and was never human. End it, or come to terms "
            "with it."
        ),
        "outcomes": {
            "banish_the_banshee": {
                "label": "Banish Shireen by steel and will",
                "description": (
                    "She can be driven out of the vale. Not killed — "
                    "things like her don't die — but broken enough to "
                    "leave."
                ),
                "objectives": [
                    {"type": "kill", "target": "banshee of the thornwood", "qty": 1,
                     "desc": "Break Shireen's hold on the Thornwood (0/1)"},
                    {"type": "deliver", "target": "captain thelmer of the stag watch",
                     "qty": 1, "desc": "Report the Thornwood quiet (0/1)"},
                ],
                "rewards": {"silver": 40, "items": [], "reagents": {}},
                "faction_rep": {"crown": 4},
                "npc_rep_deltas": {"captain thelmer of the stag watch": 5,
                                   "the banshee of the thornwood": -6},
                "npc_memories": {"captain thelmer of the stag watch":
                                 "faced the thing behind the murders and drove it out",
                                 "the banshee of the thornwood":
                                 "drove me from the Thornwood by blade — I will not forget the hand that did it"},
            },
            "dark_bargain": {
                "label": "Strike a bargain with the banshee",
                "description": (
                    "She only kills the guilty — by her count. Agree "
                    "her verdicts stop arriving in Mystvale, and tell "
                    "the watch the woods are clear. Live with it."
                ),
                "objectives": [
                    {"type": "talk", "target": "banshee of the thornwood",
                     "topic": "bargain", "qty": 1,
                     "desc": "Offer Shireen a bargain (0/1)"},
                    {"type": "deliver", "target": "captain thelmer of the stag watch",
                     "qty": 1, "desc": "Tell Thelmer the Thornwood is clear (0/1)"},
                ],
                "rewards": {"silver": 25, "items": [], "reagents": {"Grave Blood": 2}},
                "faction_rep": {"outlaws": 2, "crown": -2},
                "npc_rep_deltas": {"the banshee of the thornwood": 6,
                                   "captain thelmer of the stag watch": -2},
                "npc_memories": {"the banshee of the thornwood":
                                 "spoke terms with her in the dusk and kept them",
                                 "captain thelmer of the stag watch":
                                 "reported the Thornwood clear — something in it didn't sit right"},
            },
        },
        "prereqs": ["murder_most_foul_pt2"],
    },
}
