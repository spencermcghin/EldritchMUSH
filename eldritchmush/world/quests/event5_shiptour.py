"""Event 5 — The Trial: "A Three Hour Tour" (landlocked pirate-ship dungeon).

Source: Drive / Reboot / Event 5 - The Trial / Encounters /
"A Three Hour Tour - Rourke Lost Ship" → doc "Lost Crew of the Black
Cat's Luck" (1mkBoWMCWWPEcROzILJa_RwP2rbTiOOlAK9uWYAGl7Xo) by Spencer
McGhin & Myka, plus the in-world "Ship Log of Captain Fairweather" and
the follow-up "Letter to Captain Sutton" (folder 1Xue_68ttHrKX...).

The dramatic turn the doc hinges on: the Black Cat's Luck was a real
sailing ship caught at sea the night the Annwyn appeared, then stranded
in the middle of a hostile forest — landlocked. Her crew starved, then
turned to cannibalism, and when their hunger outran the dead, Captain
Maribel Fairweather let her own crew carve and eat HER flesh to keep
their loyalty. For some reason she does not die. The ship itself is
cursed — a witch of House Richter laid the doom on the Far Abyss line
generations back, after Fairweather's treachery against a Richter
Primehammer — so any captain who reaches for true glory is dragged back
to calmer water by endless calamity. The Rourkes prize the ship for its
old smuggler's cannons; that is the bait that draws ambitious folk in.

Players are sent by an escaped logger whose camp-mates were dragged off
and eaten. They cross an abandoned logging camp, find the captain's log,
and breach the ship: clear the cannibal-pirate DECK, search the HOLD
(captain's log, cursed blacktyde coin, smuggled gun-ammo, the Thrice
Locked Chest), then parley with Fairweather in her cabin before the
inevitable fight. The branch: lay the undying captain and her cursed
ship to rest (the right thing; the camp's dead are honored) — or seize
the wreck and its cannons for yourself and inherit the curse (Rourke
coin, a captain's piece of eight, and the doom that comes with it).

Quest dict format: see world/quests/__init__.py.
"""

QUESTS = {

    # ─────────────────────────────────────────────────────────────────────────
    # EVENT 5 — "A THREE HOUR TOUR" (explore + combat dungeon)
    # Giver: Hadwin the Logger (escaped peasant; briefs at the Tavern).
    # Descent gated by ordered beats: clear the deck → search the hold for
    # the gate-key & log → parley/fight the undying captain in her cabin.
    # Cannibal pirates fight back hard; Captain Fairweather is the boss.
    # ─────────────────────────────────────────────────────────────────────────
    "black_cats_luck": {
        "key": "black_cats_luck",
        "title": "A Three Hour Tour",
        "giver": "hadwin the logger",
        "description": (
            "Hadwin the logger burst into the tavern half-mad, the only "
            "soul to crawl out of his camp alive. His mates were dragged "
            "off one by one in the night and taken to a ship — a real "
            "three-masted ship, sitting landlocked in the middle of the "
            "forest, cannons and treasure and half-eaten bodies in her "
            "hold. The things that crew her are not men any longer; they "
            "are hungry. He'll point the way to the abandoned logging "
            "camp and the wreck beyond it, but no further.\n\n"
            "Cross the camp, find the captain's log, and breach the Black "
            "Cat's Luck. Cut your way across the deck, search the hold for "
            "the gate-key, and face whatever sits feasting in the captain's "
            "cabin. Bring out any survivors you can — and decide what to do "
            "with a ship that will not let its dead lie down."
        ),
        "outcomes": {
            "lay_her_to_rest": {
                "label": "Lay the undying captain and her cursed ship to rest",
                "description": (
                    "Parley fails, as it always does. Put Captain "
                    "Fairweather down for good, take the cursed blacktyde "
                    "coin out of the hold so the doom dies with her, and "
                    "carry the captain's log back to Hadwin so the camp's "
                    "dead have a name to grieve. The Black Cat's Luck burns. "
                    "Mistvale sleeps a little easier; the Rourkes lose a "
                    "prize they wanted badly."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Abandoned Logging Camp",
                     "qty": 1, "tag": "camp",
                     "desc": "Pick across the abandoned logging camp (0/1)"},
                    {"type": "gather", "target": "captain's ship-log",
                     "qty": 1, "requires": "camp", "tag": "log",
                     "desc": "Read the dropped captain's ship-log at the camp (0/1)"},
                    {"type": "explore", "target": "The Black Cat's Luck — Main Deck",
                     "qty": 1, "requires": "log", "tag": "deck",
                     "desc": "Breach the landlocked ship and board the deck (0/1)"},
                    {"type": "kill", "target": "cannibal pirate of the Black Cat's Luck",
                     "qty": 4, "requires": "deck", "tag": "deck_clear",
                     "desc": "Cut down the cannibal pirates crewing the deck (0/4)"},
                    {"type": "gather", "target": "marooned crewman's bones",
                     "qty": 1, "requires": "deck_clear",
                     "desc": "Search the marooned crewman's bones in the hold for the gate-key (0/1)"},
                    {"type": "gather", "target": "cursed blacktyde coin",
                     "qty": 1, "requires": "deck_clear", "tag": "coin",
                     "desc": "Take the cursed blacktyde coin out of the hold so the doom dies with it (0/1)"},
                    {"type": "kill", "target": "Captain Maribel Fairweather",
                     "qty": 1, "requires": "coin",
                     "desc": "Put the undying captain down for good in her cabin (0/1)"},
                    {"type": "deliver", "target": "hadwin the logger",
                     "qty": 1,
                     "desc": "Carry the captain's log back to Hadwin — give the camp's dead a name (0/1)"},
                ],
                "rewards": {
                    "silver": 70,
                    "items": ["STALWART_BOOTS"],
                    "reagents": {"Black Salt": 1, "Luminesce": 1},
                },
                "faction_rep": {"crown": 3, "cirque": 1, "outsider": 3, "outlaws": -3},
                "npc_rep_deltas": {
                    "hadwin the logger": 8,
                    "Captain Maribel Fairweather": -100,
                },
                "npc_memories": {
                    "hadwin the logger":
                        "carried my mates' names out of that ship and burned the thing that ate them",
                    "Captain Maribel Fairweather":
                        "the hand that finally let me die and broke the Far Abyss curse",
                },
            },
            "claim_the_wreck": {
                "label": "Seize the wreck, her cannons, and her curse",
                "description": (
                    "A landlocked ship with smuggler's cannons is worth a "
                    "fortune to the right buyer — and the Rourkes are the "
                    "right buyer. Kill Fairweather, but keep the cursed coin "
                    "and the captain's piece of eight, leave the log to rot "
                    "in the hold, and sell the Black Cat's Luck to the "
                    "Rourke fixer. The ship has a new captain now. So does "
                    "the curse. The Far Abyss always needs a captain."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Abandoned Logging Camp",
                     "qty": 1, "tag": "camp",
                     "desc": "Pick across the abandoned logging camp (0/1)"},
                    {"type": "gather", "target": "captain's ship-log",
                     "qty": 1, "requires": "camp", "tag": "log",
                     "desc": "Read the dropped captain's ship-log at the camp (0/1)"},
                    {"type": "explore", "target": "The Black Cat's Luck — Main Deck",
                     "qty": 1, "requires": "log", "tag": "deck",
                     "desc": "Breach the landlocked ship and board the deck (0/1)"},
                    {"type": "kill", "target": "cannibal pirate of the Black Cat's Luck",
                     "qty": 5, "requires": "deck", "tag": "deck_clear",
                     "desc": "Butcher the crew — no witnesses to the prize (0/5)"},
                    {"type": "gather", "target": "marooned crewman's bones",
                     "qty": 1, "requires": "deck_clear",
                     "desc": "Search the marooned crewman's bones in the hold for the gate-key (0/1)"},
                    {"type": "gather", "target": "cursed blacktyde coin",
                     "qty": 1, "requires": "deck_clear", "tag": "coin",
                     "desc": "Pocket the cursed blacktyde coin from the hold (0/1)"},
                    {"type": "kill", "target": "Captain Maribel Fairweather",
                     "qty": 1, "requires": "coin", "tag": "captain",
                     "desc": "Kill Fairweather and take the captaincy of the Far Abyss (0/1)"},
                    {"type": "gather", "target": "captain's piece of eight",
                     "qty": 1, "requires": "captain",
                     "desc": "Cut the captain's piece of eight from her chain (0/1)"},
                    {"type": "deliver", "target": "padraig the rourke fixer",
                     "qty": 1,
                     "desc": "Sell the Black Cat's Luck to Padraig the Rourke fixer (0/1)"},
                ],
                "rewards": {
                    "silver": 140,
                    "items": ["BASIC_PISTOL", "BULLETS"],
                    "reagents": {"Essence of the Unhallowed": 1},
                },
                "faction_rep": {"crown": -3, "outlaws": 4, "outsider": -2, "cirque": -1},
                "npc_rep_deltas": {
                    "hadwin the logger": -6,
                    "padraig the rourke fixer": 7,
                    "Captain Maribel Fairweather": -100,
                },
                "npc_memories": {
                    "hadwin the logger":
                        "left my mates unnamed in the hold and sold the thing that ate them for coin",
                    "padraig the rourke fixer":
                        "delivered the Black Cat's Luck and her smuggler's cannons to the Rourkes",
                    "Captain Maribel Fairweather":
                        "killed me only to wear my curse — the Far Abyss has its next captain",
                },
            },
        },
        "prereqs": [],
    },
}
