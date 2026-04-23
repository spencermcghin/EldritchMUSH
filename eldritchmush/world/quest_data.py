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
            "You remember the deck of the ship, the horizon bending the "
            "wrong way, stars that were not the stars you knew. You remember "
            "the captain's last whispered name for what was under the hull. "
            "Everything after that is salt and fog — until you woke on the "
            "Mystvale shore, the wreck still bleeding timber into the tide. "
            "The harbormaster will want to hear about the cargo. Others will "
            "want to hear less."
        ),
        "outcomes": {
            "salvage_for_crown": {
                "label": "Report to the harbormaster",
                "description": (
                    "Deliver the wreck's manifest to the Mystvale harbormaster. "
                    "A legitimate path — and the Crown takes a cut."
                ),
                "objectives": [
                    {"type": "gather", "target": "wreck manifest",
                     "qty": 1, "desc": "Recover the wreck manifest (0/1)"},
                    {"type": "deliver", "target": "mystvale harbormaster",
                     "qty": 1, "desc": "Deliver the manifest to the harbormaster (0/1)"},
                ],
                "rewards": {"silver": 15, "items": [], "reagents": {}},
                "faction_rep": {"crown": 2, "outsider": 1},
            },
            "pocket_it": {
                "label": "Pocket the salvage",
                "description": (
                    "Strip the wreck for yourself before the authorities arrive. "
                    "More coin, quieter life — if you don't get caught."
                ),
                "objectives": [
                    {"type": "gather", "target": "wreck salvage",
                     "qty": 3, "desc": "Strip salvage from the wreck (0/3)"},
                ],
                "rewards": {"silver": 25, "items": [], "reagents": {}},
                "faction_rep": {"crown": -1, "outlaws": 1, "outsider": 1},
            },
            "burn_it": {
                "label": "Burn what the captain told you to burn",
                "description": (
                    "The captain's dying request: destroy the hold before "
                    "anyone opens it. You won't be thanked, but the thing "
                    "under the hull will stay under."
                ),
                "objectives": [
                    {"type": "gather", "target": "captain's seal",
                     "qty": 1, "desc": "Recover the captain's seal from the wreck (0/1)"},
                ],
                "rewards": {"silver": 10, "items": ["MORPHOS_LORE_SCROLL"],
                            "reagents": {}},
                "faction_rep": {"outsider": 3},
            },
        },
        "prereqs": [],
    },

    "walkin_cirque": {
        "key": "walkin_cirque",
        "title": "From the Mists: Cirque",
        "giver": "herald at the gates",
        "description": (
            "You travelled with the Grand Cirque Obscura through fog that "
            "swallowed miles. When the caravan stopped at the Mystvale gates, "
            "one of the troupe was missing — Eldreth, the fortune-teller. "
            "The ringmaster is not the kind of man who reports such things "
            "to the watch. He is, however, the kind of man who rewards "
            "discretion."
        ),
        "outcomes": {
            "return_alive": {
                "label": "Find Eldreth and bring her back",
                "description": (
                    "Track Eldreth into the forest and return her to the caravan. "
                    "Clean. The Cirque remembers."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Old Road",
                     "qty": 1, "desc": "Search the road south (0/1)"},
                    {"type": "gather", "target": "eldreth's pendant",
                     "qty": 1, "desc": "Find Eldreth's pendant (0/1)"},
                    {"type": "deliver", "target": "the ringmaster",
                     "qty": 1, "desc": "Return to the ringmaster (0/1)"},
                ],
                "rewards": {"silver": 20, "items": [], "reagents": {}},
                "faction_rep": {"cirque": 3},
            },
            "cover_up": {
                "label": "Help the Cirque cover her disappearance",
                "description": (
                    "Whatever Eldreth was hiding, the Cirque wants it stay hidden. "
                    "Silence the witness. The troupe will owe you."
                ),
                "objectives": [
                    {"type": "kill", "target": "nosy farmhand",
                     "qty": 1, "desc": "Silence the witness (0/1)"},
                    {"type": "gather", "target": "eldreth's pendant",
                     "qty": 1, "desc": "Recover the pendant (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"cirque": 2, "crown": -2, "outlaws": 1},
            },
            "turn_in": {
                "label": "Turn the Cirque over to Mystvale's watch",
                "description": (
                    "Walk to the watch and tell them exactly what the Cirque "
                    "was hiding. You'll be paid in Crown coin, not Cirque coin — "
                    "and the Cirque doesn't forget."
                ),
                "objectives": [
                    {"type": "gather", "target": "eldreth's pendant",
                     "qty": 1, "desc": "Find evidence (0/1)"},
                    {"type": "deliver", "target": "mystvale captain of the watch",
                     "qty": 1, "desc": "Report to the watch captain (0/1)"},
                ],
                "rewards": {"silver": 25, "items": [], "reagents": {}},
                "faction_rep": {"crown": 3, "cirque": -3},
            },
        },
        "prereqs": [],
    },

    "walkin_noble": {
        "key": "walkin_noble",
        "title": "From the Mists: Noble",
        "giver": "herald at the gates",
        "description": (
            "You rode in the retinue of a minor noble house — or you rode "
            "as one, depending on how you tell it. The Mists parted onto "
            "the road to Mystvale, and with you came a sealed letter bound "
            "for a contact in the upper city. Bandits know these roads. "
            "So do crueler things."
        ),
        "outcomes": {
            "delivered_sealed": {
                "label": "Deliver the letter, seal intact",
                "description": (
                    "Reach the contact, seal unbroken. The court will note "
                    "your reliability."
                ),
                "objectives": [
                    {"type": "kill", "target": "road bandit",
                     "qty": 2, "desc": "Survive the ambush (0/2)"},
                    {"type": "deliver", "target": "lady ysolde of the crescent",
                     "qty": 1, "desc": "Deliver the letter unopened (0/1)"},
                ],
                "rewards": {"silver": 25, "items": [], "reagents": {}},
                "faction_rep": {"crown": 3},
            },
            "read_it_first": {
                "label": "Read the letter before delivering",
                "description": (
                    "Break the seal. Read it. Re-seal it with wax and hope. "
                    "What you learn is worth more than the delivery fee — "
                    "if you survive knowing it."
                ),
                "objectives": [
                    {"type": "kill", "target": "road bandit",
                     "qty": 2, "desc": "Survive the ambush (0/2)"},
                    {"type": "gather", "target": "unsealed letter",
                     "qty": 1, "desc": "Break the seal and read (0/1)"},
                    {"type": "deliver", "target": "lady ysolde of the crescent",
                     "qty": 1, "desc": "Deliver the letter (0/1)"},
                ],
                "rewards": {"silver": 15, "items": ["MORPHOS_LORE_SCROLL"],
                            "reagents": {}},
                "faction_rep": {"crown": 1, "outsider": 2},
            },
            "sell_to_crows": {
                "label": "Sell the letter to the Crows",
                "description": (
                    "The Crows pay well for Crown correspondence. The Crown "
                    "pays less well for traitors. You'll have to pick a side."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Old Road",
                     "qty": 1, "desc": "Meet the Crow agent on the road (0/1)"},
                    {"type": "deliver", "target": "crow agent",
                     "qty": 1, "desc": "Hand over the letter (0/1)"},
                ],
                "rewards": {"silver": 40, "items": [], "reagents": {}},
                "faction_rep": {"crown": -4, "crows": 4},
            },
        },
        "prereqs": [],
    },

    "walkin_scout": {
        "key": "walkin_scout",
        "title": "From the Mists: Scout",
        "giver": "herald at the gates",
        "description": (
            "You came through the wilderness — the long way, the quiet way. "
            "Somewhere in the pine shadow you saw Crow sign: fresh tracks, "
            "a felled messenger bird, a waymark cut into bark. The watch "
            "should hear of it. Or they shouldn't. Your call."
        ),
        "outcomes": {
            "warn_watch": {
                "label": "Warn the Mystvale watch",
                "description": (
                    "Report what you saw. Honest work. The watch remembers "
                    "faces that help them."
                ),
                "objectives": [
                    {"type": "gather", "target": "crow waymark",
                     "qty": 1, "desc": "Recover the waymark (0/1)"},
                    {"type": "deliver", "target": "mystvale captain of the watch",
                     "qty": 1, "desc": "Warn the watch captain (0/1)"},
                ],
                "rewards": {"silver": 15, "items": [], "reagents": {}},
                "faction_rep": {"crown": 2, "rangers": 2},
            },
            "sell_intel_crows": {
                "label": "Sell the intel back to the Crows",
                "description": (
                    "They'd rather know that you saw than have you warn anyone. "
                    "The price is good. The cost is your reputation."
                ),
                "objectives": [
                    {"type": "gather", "target": "crow waymark",
                     "qty": 1, "desc": "Recover the waymark (0/1)"},
                    {"type": "deliver", "target": "crow agent",
                     "qty": 1, "desc": "Return the waymark to the Crows (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"crown": -2, "rangers": -1, "crows": 3},
            },
            "stay_silent": {
                "label": "Say nothing",
                "description": (
                    "The forest keeps its secrets. You keep yours. You arrived "
                    "in Mystvale. The rest is nobody's business."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Mystvale Marketplace",
                     "qty": 1, "desc": "Slip into Mystvale quietly (0/1)"},
                ],
                "rewards": {"silver": 5, "items": [], "reagents": {}},
                "faction_rep": {"rangers": 1, "outsider": 1},
            },
        },
        "prereqs": [],
    },

    "walkin_chain_gang": {
        "key": "walkin_chain_gang",
        "title": "From the Mists: Chain Gang",
        "giver": "herald at the gates",
        "description": (
            "You do not remember the crime. You remember the chains. The "
            "jailers marched the gang through the Mists for a day and a "
            "night, and when the fog thinned, the Mystvale Gates were ahead "
            "and an opportunity was behind. Break free, plead your case, or "
            "sell out the others. Choose before the cart rolls on."
        ),
        "outcomes": {
            "bloody_break": {
                "label": "Kill the jailers, free the gang",
                "description": (
                    "Violence and freedom. The Crown hates you. Some of the "
                    "freed prisoners won't forget you."
                ),
                "objectives": [
                    {"type": "kill", "target": "mystvale jailer",
                     "qty": 2, "desc": "Put down the jailers (0/2)"},
                    {"type": "explore", "target": "The Mystvale Marketplace",
                     "qty": 1, "desc": "Escape into the city (0/1)"},
                ],
                "rewards": {"silver": 10, "items": [], "reagents": {}},
                "faction_rep": {"crown": -4, "crows": 2, "outlaws": 3},
            },
            "quiet_slip": {
                "label": "Slip your chains alone",
                "description": (
                    "Slide out while no one's looking. No blood, no friends, "
                    "no enemies — just you, free, in Mystvale."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Mystvale Marketplace",
                     "qty": 1, "desc": "Disappear into the crowd (0/1)"},
                ],
                "rewards": {"silver": 5, "items": [], "reagents": {}},
                "faction_rep": {"outsider": 2},
            },
            "legal_appeal": {
                "label": "Surrender and plead your case",
                "description": (
                    "Walk up to the watch captain and argue for a hearing. "
                    "If you can prove the charge was bogus, you arrive in "
                    "Mystvale a free citizen with a debt owed to no one."
                ),
                "objectives": [
                    {"type": "gather", "target": "forged warrant",
                     "qty": 1, "desc": "Find evidence the warrant was forged (0/1)"},
                    {"type": "deliver", "target": "mystvale captain of the watch",
                     "qty": 1, "desc": "Present your case (0/1)"},
                ],
                "rewards": {"silver": 20, "items": [], "reagents": {}},
                "faction_rep": {"crown": 3, "outlaws": -1},
            },
            "turncoat": {
                "label": "Sell out the gang for your own freedom",
                "description": (
                    "Hand over the ringleader in exchange for a pardon. "
                    "The Crown files your name as a useful man. The outlaw "
                    "network files your name in ink."
                ),
                "objectives": [
                    {"type": "kill", "target": "chain gang ringleader",
                     "qty": 1, "desc": "Subdue the ringleader (0/1)"},
                    {"type": "deliver", "target": "mystvale captain of the watch",
                     "qty": 1, "desc": "Turn the ringleader in (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"crown": 3, "outlaws": -4, "crows": -2},
            },
        },
        "prereqs": [],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # CHAPTER 1 — Getting Your Bearings
    # ─────────────────────────────────────────────────────────────────────────
    "road_clear": {
        "key": "road_clear",
        "title": "Clear the Old Road",
        "giver": "elara",
        "description": (
            "The Old Road north of the Tavern has become overrun with "
            "shambling dead. Elara, the innkeeper, begs you to put them down "
            "before they reach the settlement. Kill five zombies to make the "
            "road safe again."
        ),
        "objectives": [
            {
                "type": "kill",
                "target": "zombie",
                "qty": 5,
                "desc": "Slay zombies on the Old Road (0/5)",
            }
        ],
        "rewards": {
            "silver": 15,
            "items": [],
            "reagents": {},
        },
        "prereqs": [],
    },

    "wolf_problem": {
        "key": "wolf_problem",
        "title": "The Wolf Problem",
        "giver": "elara",
        "description": (
            "Livestock have been vanishing from the outlying cabins. "
            "Old tracks suggest a pack of wild wolves denning somewhere near "
            "the eastern fields. Elara asks you to thin the pack — put down "
            "three wolves and the losses should stop."
        ),
        "objectives": [
            {
                "type": "kill",
                "target": "wild wolf",
                "qty": 3,
                "desc": "Kill wild wolves near the cabins (0/3)",
            }
        ],
        "rewards": {
            "silver": 10,
            "items": ["WOLF_PELT"],
            "reagents": {},
        },
        "prereqs": [],
    },

    "bandit_threat": {
        "key": "bandit_threat",
        "title": "Bandits on the Docks",
        "giver": "grimwald",
        "description": (
            "Grimwald the blacksmith has heard reports of armed bandits "
            "extorting merchants at the Docks. He's lost two ore shipments "
            "already. Find the bandits and drive them off — permanently."
        ),
        "objectives": [
            {
                "type": "kill",
                "target": "bandit",
                "qty": 4,
                "desc": "Defeat bandits at the Docks (0/4)",
            }
        ],
        "rewards": {
            "silver": 20,
            "items": [],
            "reagents": {},
        },
        "prereqs": [],
    },

    "undead_patrol": {
        "key": "undead_patrol",
        "title": "Undead Patrol",
        "giver": "elara",
        "description": (
            "The undead don't stay down for long. Elara needs someone to "
            "make regular sweeps and ensure the roads stay clear. The skeletal "
            "archers at Raven's Rest are particularly dangerous — deal with them."
        ),
        "objectives": [
            {
                "type": "kill",
                "target": "skeleton archer",
                "qty": 3,
                "desc": "Destroy skeleton archers at Raven's Rest (0/3)",
            },
            {
                "type": "kill",
                "target": "zombie",
                "qty": 3,
                "desc": "Slay zombies on patrol (0/3)",
            },
        ],
        "rewards": {
            "silver": 25,
            "items": ["IRON_MEDIUM_ARMOR"],
            "reagents": {},
        },
        "prereqs": ["road_clear"],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # CHAPTER 2 — Crafting & Trade
    # ─────────────────────────────────────────────────────────────────────────
    "reagent_run": {
        "key": "reagent_run",
        "title": "Reagent Run",
        "giver": "mira",
        "description": (
            "Mira the apothecary is running dangerously low on Sayge, a "
            "critical reagent for her healing supplies. She asks you to bring "
            "her five bundles of Sayge from the wild fields east of the Tavern."
        ),
        "objectives": [
            {
                "type": "gather",
                "target": "Sayge",
                "qty": 5,
                "desc": "Bring Sayge to Mira (0/5)",
            }
        ],
        "rewards": {
            "silver": 12,
            "items": [],
            "reagents": {"Blackthorn": 3, "Crow Feather": 2},
        },
        "prereqs": [],
    },

    "forge_supplies": {
        "key": "forge_supplies",
        "title": "Forge Supplies",
        "giver": "grimwald",
        "description": (
            "Grimwald needs iron ingots to keep the forge running. The supply "
            "wagons aren't getting through with bandits on the road. Gather "
            "five iron ingots — loot them from the bandits or find them in "
            "abandoned caches — and bring them to the forge."
        ),
        "objectives": [
            {
                "type": "gather",
                "target": "iron ingots",
                "qty": 5,
                "desc": "Deliver iron ingots to Grimwald (0/5)",
            }
        ],
        "rewards": {
            "silver": 18,
            "items": ["IRON_SMALL_WEAPON"],
            "reagents": {},
        },
        "prereqs": ["bandit_threat"],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # CHAPTER 3 — Exploration
    # ─────────────────────────────────────────────────────────────────────────
    "graveyard_recon": {
        "key": "graveyard_recon",
        "title": "Graveyard Reconnaissance",
        "giver": "grimwald",
        "description": (
            "Reports suggest something powerful is animating the dead at "
            "Raven's Rest Graveyard. Grimwald asks you to scout the graveyard "
            "and return with information. Just getting there and back alive "
            "would be proof enough."
        ),
        "objectives": [
            {
                "type": "explore",
                "target": "Raven's Rest Graveyard",
                "qty": 1,
                "desc": "Visit Raven's Rest Graveyard",
            }
        ],
        "rewards": {
            "silver": 8,
            "items": [],
            "reagents": {"Bone Ash": 2},
        },
        "prereqs": [],
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

    "market_survey": {
        "key": "market_survey",
        "title": "Market Survey",
        "giver": "mira",
        "description": (
            "Mira wants to know what other merchants are selling at the "
            "Marketplace. Visit the market stalls and report back to her."
        ),
        "objectives": [
            {
                "type": "explore",
                "target": "The Marketplace",
                "qty": 1,
                "desc": "Visit the Marketplace",
            }
        ],
        "rewards": {
            "silver": 5,
            "items": [],
            "reagents": {"Sayge": 2},
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
            "blacksmith home. The Crows are armed and hostile — expect "
            "a fight."
        ),
        "objectives": [
            {
                "type": "kill",
                "target": "crow striker",
                "qty": 3,
                "desc": "Clear the Crow camp of Strikers (0/3)",
            },
            {
                "type": "kill",
                "target": "crow bruiser",
                "qty": 1,
                "desc": "Defeat the Crow Bruiser (0/1)",
            },
            {
                "type": "explore",
                "target": "Crow Camp — Blacksmith's Prison",
                "qty": 1,
                "desc": "Find the Crow camp (0/1)",
            },
        ],
        "rewards": {
            "silver": 15,
            "items": ["CROW_CAMP_LETTER"],
            "reagents": {},
        },
        "prereqs": [],
    },

    "rescue_alchemist": {
        "key": "rescue_alchemist",
        "title": "Rescue the Crafters: The Alchemist",
        "giver": "torben the blacksmith",
        "description": (
            "The rescued blacksmith, Torben, begs you to find his spouse "
            "Marta — an alchemist taken to the Fox Den, a second Crow "
            "camp deeper in the forest. The camp letter you found "
            "describes its location. More Crows, and they'll be ready "
            "for trouble."
        ),
        "objectives": [
            {
                "type": "kill",
                "target": "crow striker",
                "qty": 3,
                "desc": "Clear the Fox Den of Strikers (0/3)",
            },
            {
                "type": "kill",
                "target": "crow bruiser",
                "qty": 2,
                "desc": "Defeat the Crow Bruisers (0/2)",
            },
            {
                "type": "explore",
                "target": "Crow Camp — Fox Den",
                "qty": 1,
                "desc": "Find the Fox Den camp (0/1)",
            },
        ],
        "rewards": {
            "silver": 20,
            "items": ["ALCHEMY_RECIPE_SCROLL"],
            "reagents": {"Sayge": 5, "Blackthorn": 3},
        },
        "prereqs": ["rescue_blacksmith"],
    },

    "rescue_artificer": {
        "key": "rescue_artificer",
        "title": "Rescue the Crafters: The Artificer",
        "giver": "marta the alchemist",
        "description": (
            "Marta tells you of a third captive — Fenn, a young "
            "artificer, held at the Owl's Roost, the largest Crow camp. "
            "It's run by a lieutenant called Cale the Thorn. This will "
            "be the hardest fight yet, but freeing all three crafters "
            "will establish Mystvale's workshops for good."
        ),
        "objectives": [
            {
                "type": "kill",
                "target": "cale the thorn",
                "qty": 1,
                "desc": "Defeat Cale the Thorn (0/1)",
            },
            {
                "type": "kill",
                "target": "crow",
                "qty": 5,
                "desc": "Clear the Owl's Roost (0/5)",
            },
        ],
        "rewards": {
            "silver": 30,
            "items": ["CROW_INTELLIGENCE_REPORT"],
            "reagents": {},
        },
        "prereqs": ["rescue_alchemist"],
    },
}
