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

    # ─────────────────────────────────────────────────────────────────────────
    # EVENT 1 — SATURDAY ARC
    # Tutorial + investigative quests layered on top of the Friday walk-ins
    # and the Saturday rescue chain. Source: Drive / Reboot / Event 1 /
    # Saturday Morning, Afternoon, Night.
    # ─────────────────────────────────────────────────────────────────────────
    "combat_training": {
        "key": "combat_training",
        "title": "Combat Training",
        "giver": "drillmaster aglent",
        "description": (
            "Drillmaster Aglent — named for Meyer's old strike diagrams "
            "on the yard wall — offers to put you through the paces. "
            "Strike the training dummies and loose shafts at the archery "
            "targets until he's satisfied you won't embarrass the town."
        ),
        "objectives": [
            {"type": "kill", "target": "training dummy", "qty": 3,
             "desc": "Strike the training dummies (0/3)"},
            {"type": "kill", "target": "archery target", "qty": 2,
             "desc": "Loose shafts at the archery targets (0/2)"},
        ],
        "rewards": {"silver": 10, "items": [], "reagents": {}},
        "prereqs": [],
    },

    "alchemy_training": {
        "key": "alchemy_training",
        "title": "Alchemy Training",
        "giver": "sister ivy",
        "description": (
            "Sister Ivy at the Apotheca Chirurgery will teach any "
            "apprentice willing to keep a clean mortar. Gather a bundle "
            "of Sayge from her stores and bring it back so she can walk "
            "you through the fundamentals of the brew."
        ),
        "objectives": [
            {"type": "gather", "target": "Sayge", "qty": 1,
             "desc": "Gather a bundle of Sayge (0/1)"},
            {"type": "deliver", "target": "sister ivy", "qty": 1,
             "desc": "Return to Sister Ivy with the reagent (0/1)"},
        ],
        "rewards": {
            "silver": 5,
            "items": [],
            "reagents": {"Sayge": 3, "Distilled Spirits": 2},
        },
        "prereqs": [],
    },

    "business_opportunity": {
        "key": "business_opportunity",
        "title": "A Business Opportunity",
        "giver": "eldreth of the cirque",
        "description": (
            "Eldreth of the Cirque has paid work for a discreet hand. "
            "A body was found on the Old Road south of Mystvale, and "
            "something about it has the troupe spooked. She wants you "
            "to find Yan the Woodsman — he knows what's out there — "
            "and bring back his account. The Cirque will want to shape "
            "the story before the watch does."
        ),
        "outcomes": {
            "help_cirque_cover": {
                "label": "Give the testimony to Eldreth",
                "description": (
                    "Return Yan's account to the Cirque first. They'll "
                    "shape the story; you'll share in the silence money."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Old Road",
                     "qty": 1, "desc": "Walk the Old Road south (0/1)"},
                    {"type": "gather", "target": "yan's testimony",
                     "qty": 1, "desc": "Collect Yan's testimony (0/1)"},
                    {"type": "deliver", "target": "eldreth of the cirque",
                     "qty": 1, "desc": "Deliver the testimony to Eldreth (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"cirque": 3, "crown": -1},
            },
            "report_to_watch": {
                "label": "Report the testimony to the watch",
                "description": (
                    "Skip the Cirque and take Yan's account straight to "
                    "the Mystvale watch. Clean conscience, Crown coin, "
                    "and an enemy in the caravan."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Old Road",
                     "qty": 1, "desc": "Walk the Old Road south (0/1)"},
                    {"type": "gather", "target": "yan's testimony",
                     "qty": 1, "desc": "Collect Yan's testimony (0/1)"},
                    {"type": "deliver", "target": "mystvale captain of the watch",
                     "qty": 1, "desc": "Report to the watch captain (0/1)"},
                ],
                "rewards": {"silver": 25, "items": [], "reagents": {}},
                "faction_rep": {"crown": 3, "cirque": -3},
            },
        },
        "prereqs": [
            # Gated on any outcome of walkin_cirque — Eldreth will only
            # approach characters who came through the Cirque walk-in.
            "walkin_cirque",
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # EVENT 2 — THE WRATH (Friday Night anchor quests)
    # Source: Drive / Reboot / Event 2. Full arc spans ~20 encounters;
    # these four cover the Friday Night opening. Saturday content will
    # be added in a later pass.
    # ─────────────────────────────────────────────────────────────────────────
    "festival_of_lights": {
        "key": "festival_of_lights",
        "title": "The Festival of Lights",
        "giver": "branwyn the festival herald",
        "description": (
            "House Laurent's yearly Festival of Lights opens at Stag Hall "
            "tonight. Branwyn the herald is recruiting willing hands to "
            "hang the last lanterns in the courtyard before dusk — the "
            "fort has been tense of late and the ritual matters more than "
            "usual. A simple task; the Laurents remember those who show up."
        ),
        "objectives": [
            {"type": "gather", "target": "paper lantern", "qty": 2,
             "desc": "Gather paper lanterns from the courtyard (0/2)"},
            {"type": "deliver", "target": "branwyn the festival herald",
             "qty": 1, "desc": "Return to Branwyn with the lanterns hung (0/1)"},
        ],
        "rewards": {"silver": 10, "items": [], "reagents": {}},
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
}
