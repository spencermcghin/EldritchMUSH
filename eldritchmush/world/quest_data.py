"""
Quest data definitions for EldritchMUSH.

Each quest is a dict with:
  key          - unique str ID used in db storage
  title        - display name
  giver        - NPC key who offers/completes it (matched against NPC .key)
  description  - flavour paragraph shown on quest accept
  objectives   - list of objective dicts (see below)
  rewards      - dict of rewards granted on completion
  prereqs      - list of quest keys that must be COMPLETED first (default [])

Objective dict:
  type    - "kill"  | "gather" | "deliver" | "explore" | "duel"
  target  - NPC key / item key / room key depending on type
  qty     - how many (default 1)
  desc    - short human-readable description shown in quest log

  "duel" ticks when the player wins a wagered duel vs. the target NPC
  (see commands/duel.py). Payout of the wagered stake is handled by
  the duel command itself — the quest hook only tracks victory.

Reward dict keys (all optional, default 0):
  silver  - silver coins
  xp      - experience points (future use)
  items   - list of prototype keys to spawn into inventory
  reagents - dict of {reagent_name: qty}
"""

QUESTS = {
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
    # MISTVALE — The Aentact
    # Canon: Reboot Event 5 / "The Grizzled Veteran" (John Kozar)
    # Hamond the Talon — aka Roderick Wolf, bastard of House Laurent, now
    # head of the Lex Talionis mercenary company — drinks at the Aentact,
    # the Mistvale tavern. He'll wager 1 gold at his "Dance of Dragons"
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
            "a leaf-green Northern Marches cloak — holds court at the Aentact, "
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
}
