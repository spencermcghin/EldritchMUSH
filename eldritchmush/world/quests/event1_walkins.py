"""Event 1 — Relaunch / Friday Night walk-ins (Ship, Cirque, Noble, Explorer, Chain Gang) + rescue chain.
Source: Drive / Reboot / Event 1 - Relaunch (folder 1MSWywuW2ZnzJVkYOFmUXoCIRd-vTGOAq).

Quest dict format: see world/quests/__init__.py.
"""

QUESTS = {
    # ─────────────────────────────────────────────────────────────────────────
    # EVENT 1 — WALK-INS: HOW YOU EMERGED FROM THE MISTS INTO MYSTVALE
    #
    # Five arrival paths, each a branching quest. The Herald at the Mystvale
    # Gates offers all five to a newly-arrived character. Only one can be
    # accepted at a time, but the others remain available (useful for alts
    # or replay). Each quest's chosen outcome applies faction_rep deltas
    # that later Event 1+ content can key off.
    # ─────────────────────────────────────────────────────────────────────────
    "walkin_ship": {
        "key": "walkin_ship",
        "title": "From the Mists: Ship",
        "giver": "herald at the gates",
        "description": (
            "You'll sail the Mists. A merchant ship has been chartered for "
            "the Annwyn crossing; you and a handful of passengers will "
            "board at the Mistwall, slip down into the cargo hold, and "
            "trust the captain to find Tamris Harbor through the fog. "
            "Ships that try this almost always wash up empty. You should "
            "expect the worst. What you do with what you find on the wreck "
            "is your choice."
        ),
        # Parent arc — accepting walkin_ship auto-accepts every subquest
        # below. Children can be completed in any order; all eight can
        # be active at once. Mutex still applies at the parent level —
        # picking Ship locks out Cirque/Noble/Explorer/Chain Gang.
        "subquests": [
            "ship_find_key",
            "ship_plug_hull",
            "ship_find_navigator",
            "ship_tie_knots",
            "ship_chart_stars",
            "ship_deliver_manifest",
            "ship_wreck_salvage",
            "ship_burn_hold",
        ],
        "prereqs": [],
        "mutex_group": "walkin",
    },

    # ── Ship sub-quests (parent: walkin_ship) ──────────────────────
    # Each has no `giver` (the Herald only gives the parent) and a
    # `parent` link back to walkin_ship for journal grouping.

    "ship_find_key": {
        "key": "ship_find_key",
        "title": "The Captain's Door Key",
        "parent": "walkin_ship",
        "description": (
            "The captain locked the cargo hold from the outside and took "
            "the key with him. There is, however, a SPARE — the lookout "
            "hid it somewhere in the hold during a drunken night and "
            "wrote a regretful journal entry about not remembering where. "
            "Find the spare."
        ),
        "objectives": [
            {"type": "gather", "target": "captain's door key",
             "qty": 1, "desc": "Find the captain's door key in the cargo hold (0/1)"},
        ],
        "rewards": {"silver": 5},
        "prereqs": [],
    },

    "ship_plug_hull": {
        "key": "ship_plug_hull",
        "title": "Plug the Hull",
        "parent": "walkin_ship",
        "description": (
            "Water is coming in through a hole in the hull. The chief "
            "engineer's notes say you need exactly four litres of pitch-"
            "mixed seawater to patch it — but you only have three buckets, "
            "marked 8, 5, and 3 litres. Measure exactly 4 with what you "
            "have. (Type |whelp buckets|n at the buckets for the commands.)"
        ),
        "objectives": [
            # synthetic: ticked by the bucket-puzzle CmdSet, not a room
            {"type": "explore", "target": "plugged hull", "synthetic": True,
             "qty": 1, "desc": "Measure exactly 4 litres with the three buckets (0/1)"},
        ],
        "rewards": {"silver": 10},
        "prereqs": [],
    },

    "ship_find_navigator": {
        "key": "ship_find_navigator",
        "title": "Find the Navigator",
        "parent": "walkin_ship",
        "description": (
            "First Mate Nosaj is the only surviving crew. He can chart a "
            "course — if you can find him on the wreck. Get up to the "
            "ship's deck and locate him."
        ),
        "objectives": [
            {"type": "explore", "target": "The Doomed Ship's Deck",
             "qty": 1, "desc": "Reach the ship's deck (0/1)"},
        ],
        "rewards": {"silver": 5},
        "prereqs": [],
    },

    "ship_tie_knots": {
        "key": "ship_tie_knots",
        "title": "Tie the Sails",
        "parent": "walkin_ship",
        "description": (
            "The storm tore the rigging. Four masts need fresh knots before "
            "the wind picks back up. The Chief Engineer's syllabus on the "
            "deck lists which knot belongs on which mast. (Type "
            "|wtie <knot> on <mast>|n at the deck.)"
        ),
        "objectives": [
            # synthetic: ticked by the knot-puzzle CmdSet, not a room
            {"type": "explore", "target": "knots tied", "synthetic": True,
             "qty": 4, "desc": "Tie the correct knot on each of the four masts (0/4)"},
        ],
        "rewards": {"silver": 15},
        "prereqs": [],
    },

    "ship_chart_stars": {
        "key": "ship_chart_stars",
        "title": "Chart the Stars",
        "parent": "walkin_ship",
        "description": (
            "The stars over the deck are not Arnesse stars. You'll need "
            "to match the Annwyn-side constellations against the cardinal "
            "directions to feed the navigator a course. The constellation "
            "chart shows which star-cluster sits over which heading. "
            "(Type |wchart <constellation> <direction>|n at the deck.)"
        ),
        "objectives": [
            # synthetic: ticked by the constellation-puzzle CmdSet, not a room
            {"type": "explore", "target": "stars charted", "synthetic": True,
             "qty": 4, "desc": "Chart all four constellations to their cardinal directions (0/4)"},
        ],
        "rewards": {"silver": 15},
        "prereqs": [],
    },

    "ship_deliver_manifest": {
        "key": "ship_deliver_manifest",
        "title": "Report to the Harbormaster",
        "parent": "walkin_ship",
        "description": (
            "Recover the wreck's manifest and deliver it to the Mystvale "
            "Harbormaster at Tamris Harbor. A legitimate path — the "
            "Crown takes a cut, and remembers a courier who plays it "
            "straight."
        ),
        "objectives": [
            {"type": "gather", "target": "wreck manifest",
             "qty": 1, "desc": "Recover the wreck manifest at Tamris Harbor (0/1)"},
            {"type": "deliver", "target": "mystvale harbormaster",
             "qty": 1, "desc": "Deliver the manifest to the Mystvale Harbormaster at Tamris Harbor (0/1)"},
        ],
        "rewards": {"silver": 15},
        "faction_rep": {"crown": 2, "outsider": 1},
        "prereqs": [],
    },

    "ship_wreck_salvage": {
        "key": "ship_wreck_salvage",
        "title": "Pocket the Salvage",
        "parent": "walkin_ship",
        "description": (
            "Strip the wreck for yourself before the authorities count "
            "everything. More coin, quieter life — if you don't get "
            "caught. The wreck is at Tamris Harbor."
        ),
        "objectives": [
            {"type": "gather", "target": "wreck salvage",
             "qty": 3, "desc": "Strip salvage from the wreck at Tamris Harbor (0/3)"},
        ],
        "rewards": {"silver": 25},
        "faction_rep": {"crown": -1, "outlaws": 1, "outsider": 1},
        "prereqs": [],
    },

    "ship_burn_hold": {
        "key": "ship_burn_hold",
        "title": "Burn What the Captain Told You to Burn",
        "parent": "walkin_ship",
        "description": (
            "The captain's dying request: destroy the hold before anyone "
            "opens it. You won't be thanked, but the thing under the "
            "hull will stay under. The seal is at the wreck on Tamris "
            "Harbor."
        ),
        "objectives": [
            {"type": "gather", "target": "captain's seal",
             "qty": 1, "desc": "Recover the captain's seal from the wreck at Tamris Harbor (0/1)"},
        ],
        "rewards": {"silver": 10, "items": ["MORPHOS_LORE_SCROLL"]},
        "faction_rep": {"outsider": 3},
        "prereqs": [],
    },

    "walkin_cirque": {
        "key": "walkin_cirque",
        "title": "From the Mists: Cirque",
        "giver": "herald at the gates",
        "description": (
            "You'll cross with the Grand Cirque Obscura's caravan. They're "
            "camped at the Mistwall — the hired Mistwalker never came, "
            "and the cargo (four iron-banded crates) still needs to reach "
            "Eldreth on the Annwyn side. Yan, the Cirque's foreman, will "
            "hand you the contract and walk the Tangle with you. Expect "
            "the Lost between the trees and the Underwriter past them — "
            "neither will let you through for nothing. The crates that "
            "survive go to the Ringmaster at the Mystvale Marketplace."
        ),
        "outcomes": {
            "deliver_all_four": {
                "label": "Fight the Lost, pay the Underwriter, deliver all four",
                "description": (
                    "Cut through the Lost in the Tangle. Pay the "
                    "Underwriter in coin for the trod torch. Carry all "
                    "four crates over the ghost-bridge to the Ringmaster "
                    "at the Mystvale Marketplace. The Cirque pays in "
                    "favour, not pity."
                ),
                "objectives": [
                    {"type": "kill", "target": "the first lost",
                     "qty": 1, "desc": "Put down the First Lost in the Tangle (0/1)"},
                    {"type": "kill", "target": "the second lost",
                     "qty": 1, "desc": "Put down the Second Lost in the Tangle (0/1)"},
                    {"type": "gather", "target": "trod torch",
                     "qty": 1, "desc": "Buy the trod torch from the Underwriter (0/1)"},
                    {"type": "deliver", "target": "the ringmaster",
                     "qty": 1, "desc": "Deliver the Cirque cargo manifest to the Ringmaster at the Mystvale Marketplace (0/1)"},
                ],
                "rewards": {"silver": 40, "items": [], "reagents": {}},
                "faction_rep": {"cirque": 4, "outlaws": 1},
            },
            "mercy_to_the_lost": {
                "label": "Give the Lost a crate, deliver three",
                "description": (
                    "Hand the Lost a crate. They take it into the dark "
                    "and let you pass. Pay the Underwriter for the "
                    "torch. Bring three crates to the Ringmaster. The "
                    "Cirque notes the loss and the mercy."
                ),
                "objectives": [
                    {"type": "deliver", "target": "the first lost",
                     "qty": 1, "desc": "Give a Cirque crate to the First Lost (0/1)"},
                    {"type": "gather", "target": "trod torch",
                     "qty": 1, "desc": "Buy the trod torch from the Underwriter (0/1)"},
                    {"type": "deliver", "target": "the ringmaster",
                     "qty": 1, "desc": "Deliver the Cirque cargo manifest to the Ringmaster at the Mystvale Marketplace (0/1)"},
                ],
                "rewards": {"silver": 20, "items": [], "reagents": {}},
                "faction_rep": {"cirque": 2, "outsider": 2},
            },
            "barter_with_underwriter": {
                "label": "Trade a crate to the Underwriter for the torch",
                "description": (
                    "Make it past the Lost as you can. Hand the "
                    "Underwriter one of the Cirque's crates as payment "
                    "for the trod torch. Carry three crates through. "
                    "The Cirque charges the loss to your share."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Tangle",
                     "qty": 1, "desc": "Cross the Tangle (0/1)"},
                    {"type": "deliver", "target": "the underwriter",
                     "qty": 1, "desc": "Give a Cirque crate to the Underwriter for the trod torch (0/1)"},
                    {"type": "deliver", "target": "the ringmaster",
                     "qty": 1, "desc": "Deliver the Cirque cargo manifest to the Ringmaster at the Mystvale Marketplace (0/1)"},
                ],
                "rewards": {"silver": 25, "items": [], "reagents": {}},
                "faction_rep": {"cirque": 1, "outsider": 1},
            },
            "sell_to_underwriter": {
                "label": "Sell all four crates to the Underwriter",
                "description": (
                    "The Underwriter offers a heavy purse for the whole "
                    "manifest. Take it. Walk into Mystvale alone, "
                    "wealthy, and on the Cirque's blacklist forever. "
                    "Disappear into the Marketplace crowd."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Tangle",
                     "qty": 1, "desc": "Cross the Tangle (0/1)"},
                    {"type": "deliver", "target": "the underwriter",
                     "qty": 1, "desc": "Sell the Cirque cargo manifest to the Underwriter (0/1)"},
                    {"type": "explore", "target": "The Mystvale Marketplace",
                     "qty": 1, "desc": "Slip into the Mystvale Marketplace (0/1)"},
                ],
                "rewards": {"silver": 60, "items": [], "reagents": {}},
                "faction_rep": {"cirque": -4, "outlaws": 2, "outsider": 2},
            },
        },
        "prereqs": [],
        "mutex_group": "walkin",
    },

    "walkin_noble": {
        "key": "walkin_noble",
        "title": "From the Mists: Noble",
        "giver": "herald at the gates",
        "description": (
            "You'll cross with a minor noble retinue — as one of them or "
            "in their service, however you tell it. The party hired the "
            "Mistwalker Martin in Gateway, and his assistant Wil is "
            "ready to lead you out to Martin's camp past the Mistwall. "
            "What waits there is not what Wil promised. Beyond the "
            "camp is the Spider-Wood, Martin's true fate, and a leather "
            "journal whose secret the Crown and the Crows would both "
            "kill for."
        ),
        "outcomes": {
            "expose_wil": {
                "label": "Bring Wil's fraud and Martin's journal to Lady Ysolde",
                "description": (
                    "Survive the Spider-Wood. Take Martin's journal from "
                    "the Hollow where Wil drops it. Carry both the "
                    "journal and the story of Wil's con back to Lady "
                    "Ysolde at the Mystvale Town Hall. The Crown will "
                    "remember the courier who handed it a Mistwalker's "
                    "route and a false Guide's name in the same breath."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Spider-Wood",
                     "qty": 1, "desc": "Cross the Spider-Wood (0/1)"},
                    {"type": "gather", "target": "Martin's journal",
                     "qty": 1, "desc": "Take Martin's journal from the Web-Wreathed Hollow (0/1)"},
                    {"type": "deliver", "target": "lady ysolde of the crescent",
                     "qty": 1, "desc": "Deliver Martin's journal to Lady Ysolde at the Mystvale Town Hall (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"crown": 3, "outlaws": -1},
            },
            "let_wil_go": {
                "label": "Let Wil flee — no blood, no journal",
                "description": (
                    "Hear Wil's confession in the Hollow. Pity him. Let "
                    "him take Martin's journal and vanish into the "
                    "Mystvale crowd. You arrive in the Marketplace with "
                    "nothing but a story nobody will pay for. The Crown "
                    "and the Crows both wonder where the Guide's gear "
                    "went."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Spider-Wood",
                     "qty": 1, "desc": "Cross the Spider-Wood (0/1)"},
                    {"type": "explore", "target": "The Web-Wreathed Hollow",
                     "qty": 1, "desc": "Hear Wil's confession in the Web-Wreathed Hollow (0/1)"},
                    {"type": "explore", "target": "The Mystvale Marketplace",
                     "qty": 1, "desc": "Arrive in the Mystvale Marketplace (0/1)"},
                ],
                "rewards": {"silver": 10, "items": [], "reagents": {}},
                "faction_rep": {"outsider": 2},
            },
            "kill_wil": {
                "label": "Kill Wil for the deception",
                "description": (
                    "A conman ran your retinue into the Spider-Wood for "
                    "coin. Cut him down in the Hollow when he tries to "
                    "flee. Take Martin's journal. Walk into Mystvale "
                    "with the dead Guide's secret in your pack."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Spider-Wood",
                     "qty": 1, "desc": "Cross the Spider-Wood (0/1)"},
                    {"type": "kill", "target": "wil the conman",
                     "qty": 1, "desc": "Put Wil down in the Web-Wreathed Hollow (0/1)"},
                    {"type": "gather", "target": "Martin's journal",
                     "qty": 1, "desc": "Take Martin's journal from the Hollow (0/1)"},
                ],
                "rewards": {"silver": 25, "items": [], "reagents": {}},
                "faction_rep": {"crown": 1, "outlaws": 2},
            },
            "sell_journal_to_crows": {
                "label": "Sell Martin's journal to the Crows",
                "description": (
                    "The journal contains a route through the Mists the "
                    "Crown does not own. The Crows will pay in heavy "
                    "silver and protection for it. Cross the Spider-Wood, "
                    "take the journal at the Hollow, and find the Crow "
                    "Agent on the Old Road south. The Crown will know "
                    "your name and hate it."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Spider-Wood",
                     "qty": 1, "desc": "Cross the Spider-Wood (0/1)"},
                    {"type": "gather", "target": "Martin's journal",
                     "qty": 1, "desc": "Take Martin's journal from the Hollow (0/1)"},
                    {"type": "deliver", "target": "crow agent",
                     "qty": 1, "desc": "Sell Martin's journal to the Crow Agent on the Old Road south (0/1)"},
                ],
                "rewards": {"silver": 50, "items": [], "reagents": {}},
                "faction_rep": {"crown": -3, "crows": 4},
            },
        },
        "prereqs": [],
        "mutex_group": "walkin",
    },

    "walkin_scout": {
        "key": "walkin_scout",
        "title": "From the Mists: Explorer",
        "giver": "herald at the gates",
        "description": (
            "You'll cross with the Lodge of the Metaphysical Mind. "
            "Magister Ipwin summoned scholars to the Annwyn to study "
            "its spirit phenomena; you and Magister Vell answered. "
            "Ipwin went ahead through the Mists days ago, leaving "
            "blacklight lanterns to mark his trail and a note about a "
            "barrow he'd opened. The trail is waiting on the far side "
            "of the Mistwall. What you'll find at the barrow's end is "
            "Ipwin — and the spirit that now wears him."
        ),
        "outcomes": {
            "save_ipwin": {
                "label": "Reassemble the binding-figure, exorcise Shireen, save Ipwin",
                "description": (
                    "Gather the four rune-bones from the barrow floor. "
                    "Lay them in the figure carved on the wall. Shireen "
                    "is bound back into the earth and Magister Ipwin "
                    "walks out of the barrow himself. Deliver him to "
                    "Lady Ysolde at the Mystvale Town Hall — the "
                    "Lodge's standing in the Crown's eye rises."
                ),
                "objectives": [
                    {"type": "gather", "target": "rune-bone",
                     "qty": 4, "desc": "Gather all four rune-bones in the Barrow (0/4)"},
                    {"type": "deliver", "target": "lady ysolde of the crescent",
                     "qty": 1, "desc": "Deliver Ipwin's journal to Lady Ysolde at the Mystvale Town Hall (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"crown": 2, "rangers": 2},
            },
            "fight_shireen": {
                "label": "Destroy Shireen — Ipwin survives, the lore burns",
                "description": (
                    "Drive Shireen out of Ipwin by sword and prayer. "
                    "She dies hard. Ipwin lives, but the Witch-Queen "
                    "loses a daughter, the bones lie scattered, and "
                    "the lore Ipwin came for is mostly gone. Walk "
                    "him into the Mystvale Marketplace alive."
                ),
                "objectives": [
                    {"type": "kill", "target": "shireen",
                     "qty": 1, "desc": "Destroy Shireen in the Barrow (0/1)"},
                    {"type": "explore", "target": "The Mystvale Marketplace",
                     "qty": 1, "desc": "Bring Ipwin into the Mystvale Marketplace (0/1)"},
                ],
                "rewards": {"silver": 20, "items": [], "reagents": {}},
                "faction_rep": {"crown": 1, "outsider": 1},
            },
            "take_ipwins_journal": {
                "label": "Abandon Ipwin — take his research to the Crown",
                "description": (
                    "Ipwin is gone. Shireen wears him. The Lodge "
                    "loses a scholar; the Crown gains a journal of "
                    "his metaphysical findings. Take Ipwin's journal "
                    "from the camp and carry it to Lady Ysolde at "
                    "the Mystvale Town Hall."
                ),
                "objectives": [
                    {"type": "gather", "target": "Ipwin's journal",
                     "qty": 1, "desc": "Take Ipwin's journal from his camp (0/1)"},
                    {"type": "deliver", "target": "lady ysolde of the crescent",
                     "qty": 1, "desc": "Deliver Ipwin's journal to Lady Ysolde at the Mystvale Town Hall (0/1)"},
                ],
                "rewards": {"silver": 25, "items": [], "reagents": {}},
                "faction_rep": {"crown": 2, "outsider": 2},
            },
            "serve_shireen": {
                "label": "Refuse the binding — accept the Witch-Queen's gift",
                "description": (
                    "Leave the bones where they lie. Speak with "
                    "Shireen. Accept the Witch-Queen's gift — a "
                    "touch of fae sight, a debt called in later. "
                    "Walk into Mystvale changed. The Crown will not "
                    "thank you. The old powers will remember."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Barrow of Shireen",
                     "qty": 1, "desc": "Reach Shireen in the Barrow (0/1)"},
                    {"type": "deliver", "target": "shireen",
                     "qty": 1, "desc": "Offer Ipwin's journal to Shireen as tribute (0/1)"},
                    {"type": "explore", "target": "The Mystvale Marketplace",
                     "qty": 1, "desc": "Walk into the Mystvale Marketplace marked (0/1)"},
                ],
                "rewards": {"silver": 20, "items": [], "reagents": {}},
                "faction_rep": {"crown": -3, "crows": 2, "outsider": 3},
            },
        },
        "prereqs": [],
        "mutex_group": "walkin",
    },

    "walkin_chain_gang": {
        "key": "walkin_chain_gang",
        "title": "From the Mists: Chain Gang",
        "giver": "herald at the gates",
        "description": (
            "You'll cross the Mists the way the condemned do — chained "
            "to a wagon at the Mistwall with a column of other prisoners "
            "the jailers won't be bringing back. Your weapons go in a "
            "Laurent-stamped crate that gets carried off into the fog. "
            "Beside you on the chain is a Northman named Ulfric who "
            "already knows your name and has plans for the both of you. "
            "Whatever happens in the woods between the Mistwall and "
            "Mystvale will define what you become on the far side."
        ),
        "outcomes": {
            "join_ulfric": {
                "label": "Throw in with Ulfric — take the gold, kill the guard",
                "description": (
                    "Stand with Ulfric at the clearing. Help him put down "
                    "Killian, take the Laurent strongbox, and walk into "
                    "Mystvale a gang. The Crown will know your name and "
                    "hate it. The outlaw network will know your name and "
                    "shake your hand."
                ),
                "objectives": [
                    {"type": "explore", "target": "A Clearing in the Mists",
                     "qty": 1, "desc": "Reach the clearing in the Mists (0/1)"},
                    {"type": "kill", "target": "killian",
                     "qty": 1, "desc": "Help Ulfric put Killian down at the Clearing (0/1)"},
                    {"type": "gather", "target": "Laurent strongbox",
                     "qty": 1, "desc": "Take the Laurent strongbox (0/1)"},
                    {"type": "explore", "target": "The Mystvale Marketplace",
                     "qty": 1, "desc": "Escape into the Mystvale Marketplace (0/1)"},
                ],
                "rewards": {"silver": 40, "items": [], "reagents": {}},
                "faction_rep": {"crown": -4, "outlaws": 4, "crows": 1},
            },
            "save_killian": {
                "label": "Defend Killian — return the gold to House Laurent",
                "description": (
                    "Refuse Ulfric. Stand between him and Killian. Bring "
                    "the Laurent strongbox and Lord Laurent's letter "
                    "through the Mists to the Mystvale Captain of the "
                    "Watch — House Laurent will remember the name of the "
                    "stranger who held the line."
                ),
                "objectives": [
                    {"type": "explore", "target": "A Clearing in the Mists",
                     "qty": 1, "desc": "Reach the clearing in the Mists (0/1)"},
                    {"type": "kill", "target": "ulfric the coldhand",
                     "qty": 1, "desc": "Put Ulfric down at the Clearing (0/1)"},
                    {"type": "gather", "target": "Laurent strongbox",
                     "qty": 1, "desc": "Recover the Laurent strongbox at the Clearing (0/1)"},
                    {"type": "deliver", "target": "mystvale captain of the watch",
                     "qty": 1, "desc": "Deliver the strongbox to the watch captain at the Bannon Barracks (0/1)"},
                ],
                "rewards": {"silver": 20, "items": [], "reagents": {}},
                "faction_rep": {"crown": 4, "rangers": 1, "outlaws": -3},
            },
            "take_gold_spare_killian": {
                "label": "Take the gold — leave Killian alive",
                "description": (
                    "No kill, no glory. Bind Killian's wound, take the "
                    "Laurent strongbox, and walk past him into the "
                    "Mystvale crowd. You arrive in the Marketplace a "
                    "free outlaw with a heavy purse and no story you'd "
                    "want told."
                ),
                "objectives": [
                    {"type": "explore", "target": "A Clearing in the Mists",
                     "qty": 1, "desc": "Reach the clearing in the Mists (0/1)"},
                    {"type": "gather", "target": "Laurent strongbox",
                     "qty": 1, "desc": "Take the Laurent strongbox (0/1)"},
                    {"type": "explore", "target": "The Mystvale Marketplace",
                     "qty": 1, "desc": "Slip into the Mystvale Marketplace (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"crown": -1, "outlaws": 2, "outsider": 2},
            },
            "turn_in_ulfric": {
                "label": "Subdue Ulfric — march him to the watch with Lord Laurent's letter",
                "description": (
                    "Put Ulfric down before he can move on the chest, "
                    "find Lord Laurent's letter at the Clearing, and "
                    "carry it to the Mystvale Captain of the Watch. The "
                    "Crown files your name as a useful man. The outlaw "
                    "network files your name in ink."
                ),
                "objectives": [
                    {"type": "explore", "target": "A Clearing in the Mists",
                     "qty": 1, "desc": "Reach the clearing in the Mists (0/1)"},
                    {"type": "kill", "target": "ulfric the coldhand",
                     "qty": 1, "desc": "Subdue Ulfric at the Clearing (0/1)"},
                    {"type": "gather", "target": "Lord Laurent's letter",
                     "qty": 1, "desc": "Recover Lord Laurent's letter at the Clearing (0/1)"},
                    {"type": "deliver", "target": "mystvale captain of the watch",
                     "qty": 1, "desc": "Deliver the letter to the watch captain at the Bannon Barracks (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"crown": 3, "outlaws": -4},
            },
        },
        "prereqs": [],
        "mutex_group": "walkin",
    },

    # ─────────────────────────────────────────────────────────────────────────
    # MISTVALE — Songbird's Rest
    # Canon: Reboot Event 5 / "The Grizzled Veteran" (John Kozar)
    # Hamond the Talon — aka Roderick Wolf, bastard of House Laurent, now
    # head of the Lex Talionis mercenary company — drinks at Songbird's
    # Rest, the Mistvale tavern. He'll wager 1 gold at his "Dance of Dragons"
    # duel. Win and he drops a signed contract proving his betrayal of
    # the Laurents to House Oban — the betrayal that brought down Stag
    # Hall at the start of the year. Entire arc plays out Mistvale-side.
    # ─────────────────────────────────────────────────────────────────────────
    "grizzled_veteran": {
        "key": "grizzled_veteran",
        "title": "The Grizzled Veteran",
        "giver": "hamond the talon",
        "description": (
            "Hamond the Talon — a scarred old soldier with silver rings and "
            "a leaf-green Northern Marches cloak — holds court at Songbird's Rest, "
            "buying drinks for anyone who'll listen to his war stories. "
            "He's offering coin at his old dueling game: the |yDance of "
            "Dragons|n. One gold on the table, first to yield loses all. "
            "Win and press him — there are whispers that Lex Talionis did "
            "not fight as contracted when Stag Hall fell, and the old man "
            "may be carrying proof of it himself."
        ),
        "objectives": [
            {
                "type": "duel",
                "target": "hamond the talon",
                "qty": 1,
                "desc": "Win the Dance of Dragons against Hamond (0/1)",
            },
            {
                "type": "gather",
                "target": "signed oban contract",
                "qty": 1,
                "desc": "Recover the signed Oban contract (0/1)",
            },
        ],
        "rewards": {
            "silver": 20,
            "items": ["MORPHOS_LORE_SCROLL"],
            "reagents": {},
        },
        "prereqs": [],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # EVENT 1 — Rescue the Crafters (3-part quest chain)
    # Ser Ewan Bannon → Torben the Blacksmith → Marta the Alchemist
    # Crow bandits have kidnapped Mystvale's three key crafters and are
    # holding them at three camps in the forest and along the Old Road.
    # ─────────────────────────────────────────────────────────────────────────
    "rescue_blacksmith": {
        "key": "rescue_blacksmith",
        "title": "Rescue the Crafters: The Blacksmith",
        "giver": "ser ewan bannon",
        "description": (
            "Crow bandits have kidnapped Mystvale's blacksmith and are "
            "holding him at a camp in the forest. Ser Ewan Bannon is "
            "looking for volunteers to raid the camp and bring the "
            "blacksmith home. The Crows will fight anyone they think "
            "is Bannon-affiliated — or they may be talked down."
        ),
        "outcomes": {
            "clear_by_blade": {
                "label": "Take the camp by force",
                "description": (
                    "Kill the Crows, recover the blacksmith, seize the "
                    "camp's lockbox. The loud way."
                ),
                "objectives": [
                    {"type": "kill", "target": "crow striker", "qty": 3,
                     "desc": "Clear the camp of Strikers (0/3)"},
                    {"type": "kill", "target": "crow bruiser", "qty": 1,
                     "desc": "Defeat the Crow Bruiser (0/1)"},
                    {"type": "explore", "target": "Crow Camp — Blacksmith's Prison",
                     "qty": 1, "desc": "Find the Crow camp (0/1)"},
                ],
                "rewards": {"silver": 15, "items": ["CROW_CAMP_LETTER"], "reagents": {}},
                "faction_rep": {"crown": 1, "crows": -3},
                "npc_rep_deltas": {
                    "torben the blacksmith": 8,
                    "ser ewan bannon": 4,
                },
                "npc_memories": {
                    "torben the blacksmith": "rescued me from the Crow camp by blade",
                    "ser ewan bannon": "cleared the camp cleanly",
                },
            },
            "clear_by_parley": {
                "label": "Persuade the Crows to let him go",
                "description": (
                    "The Crows will parley if convinced you're not Bannon. "
                    "Quieter, fewer graves, no Crown reward."
                ),
                "objectives": [
                    {"type": "explore", "target": "Crow Camp — Blacksmith's Prison",
                     "qty": 1, "desc": "Find the Crow camp (0/1)"},
                    {"type": "gather", "target": "rowyna's diary of exile",
                     "qty": 1, "desc": "Find evidence of the Crows' plight (0/1)"},
                ],
                "rewards": {"silver": 10, "items": ["CROW_CAMP_LETTER"], "reagents": {}},
                "faction_rep": {"crows": 2, "crown": -1},
                "npc_rep_deltas": {
                    "torben the blacksmith": 5,
                    "ser ewan bannon": -2,
                },
                "npc_memories": {
                    "torben the blacksmith": "spared blood to bring me home",
                    "ser ewan bannon": "took the quiet way; crown business unfinished",
                },
            },
        },
        "prereqs": [],
    },

    "rescue_alchemist": {
        "key": "rescue_alchemist",
        "title": "Rescue the Crafters: The Alchemist",
        "giver": "torben the blacksmith",
        "description": (
            "The rescued blacksmith, Torben, begs you to find his spouse "
            "Marta — an alchemist taken to the Owl's Roost, a second "
            "Crow camp deeper in the forest. More Crows, and they'll be "
            "ready for trouble — or ready to talk, depending on your "
            "approach."
        ),
        "outcomes": {
            "clear_by_blade": {
                "label": "Take the Roost by force",
                "description": (
                    "Kill the Crows at the Owl's Roost, recover Marta's "
                    "recipe scroll. The direct way."
                ),
                "objectives": [
                    {"type": "kill", "target": "crow striker", "qty": 3,
                     "desc": "Clear the Owl's Roost of Strikers (0/3)"},
                    {"type": "kill", "target": "crow bruiser", "qty": 2,
                     "desc": "Defeat the Crow Bruisers (0/2)"},
                    {"type": "explore", "target": "Crow Camp — Owl's Roost",
                     "qty": 1, "desc": "Find the Owl's Roost (0/1)"},
                ],
                "rewards": {
                    "silver": 20, "items": ["ALCHEMY_RECIPE_SCROLL"],
                    "reagents": {"Sayge": 5, "Blackthorn": 3},
                },
                "faction_rep": {"crown": 1, "crows": -3},
            },
            "clear_by_parley": {
                "label": "Negotiate Marta's release",
                "description": (
                    "Show the Crows they're not fighting Bannons and "
                    "bargain for Marta's freedom. Lower reward, higher "
                    "standing with the outlaw network."
                ),
                "objectives": [
                    {"type": "explore", "target": "Crow Camp — Owl's Roost",
                     "qty": 1, "desc": "Find the Owl's Roost (0/1)"},
                    {"type": "deliver", "target": "marta the alchemist",
                     "qty": 1, "desc": "Hand Marta the camp letter (0/1)"},
                ],
                "rewards": {
                    "silver": 15, "items": ["ALCHEMY_RECIPE_SCROLL"],
                    "reagents": {"Sayge": 3},
                },
                "faction_rep": {"crows": 2, "outlaws": 1, "crown": -1},
            },
        },
        "prereqs": ["rescue_blacksmith"],
    },

    "rescue_artificer": {
        "key": "rescue_artificer",
        "title": "Rescue the Crafters: The Artificer",
        "giver": "marta the alchemist",
        "description": (
            "Marta tells you of a third captive — Fenn, a young "
            "artificer, held at the Fox Den, the largest Crow camp. "
            "It's run by a lieutenant called Cale the Thorn. Cale is "
            "a trained swordsman with a reputation — but every man has "
            "a price, and every camp has its limits."
        ),
        "outcomes": {
            "clear_by_blade": {
                "label": "Kill Cale and clear the Fox Den",
                "description": (
                    "End the Crow lieutenant. Free Fenn. The Crows won't "
                    "forgive this, but the Crown will."
                ),
                "objectives": [
                    {"type": "kill", "target": "cale the thorn", "qty": 1,
                     "desc": "Defeat Cale the Thorn (0/1)"},
                    {"type": "kill", "target": "crow", "qty": 5,
                     "desc": "Clear the Fox Den (0/5)"},
                ],
                "rewards": {
                    "silver": 30, "items": ["CROW_INTELLIGENCE_REPORT"],
                    "reagents": {},
                },
                "faction_rep": {"crown": 3, "crows": -5},
            },
            "pay_the_ransom": {
                "label": "Pay Cale's ransom for Fenn",
                "description": (
                    "Cale values coin over blood today. Buy Fenn's "
                    "freedom and leave the Fox Den standing."
                ),
                "objectives": [
                    {"type": "explore", "target": "Crow Camp — Fox Den",
                     "qty": 1, "desc": "Reach the Fox Den (0/1)"},
                    {"type": "deliver", "target": "cale the thorn", "qty": 1,
                     "desc": "Hand Cale the ransom (0/1)"},
                ],
                "rewards": {
                    "silver": 10, "items": ["CROW_INTELLIGENCE_REPORT"],
                    "reagents": {},
                },
                "faction_rep": {"crows": 3, "crown": -2},
            },
        },
        "prereqs": ["rescue_alchemist"],
    },
}
