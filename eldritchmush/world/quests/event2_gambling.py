"""Event 2 — The Gambling Den (Saturday Evening).

Source: Drive / Reboot / Event 2 - The Wrath / "The Gambling Den"
(John Kozar). Folder 1jxlA_zorcovQrAyMYU3paeNR6-m0pCl8;
doc id 1zaJHmenRuqFJQl4aMwwpC_5sUjhCKEWc.

This is Event 2's SOCIAL + ECONOMY showcase — a deliberate contrast to
the combat anchors. A Cirque troupe of con-artists, the Critter Crew
(Fox, Rabbit, Owl), set up an illicit Street Dice game in the back room
of the Broken Oar. The menace here is social and economic, not martial:
a rigged game, a debt, a sting, a recruitment.

MECHANICAL NOTE — there is NO bespoke gambling engine, and the quest
does NOT wager on a live RNG. Players are encouraged to roll the real
`dice` command (commands/dice.py — `dice 2d6`, craps-style) at the table
for flavour and table-talk, but the *quest beats* are modelled with the
existing primitives:

  * TALK   — buying in, being pitched, being recruited, talking down
             angry marks (`ask`/`say`/`whisper`).
  * GATHER — picking up the stake purse / a copper debt marker / the
             loaded dice (a scene prop you palm).
  * DELIVER (consuming `item`) — handing over your debt markers (the
             whole stack) when you settle or get fleeced.
  * SKILL  — `treat <npc>` gated on `espionage` (spot/work the rig) or
             `influential` (out-talk the marks). The doc's "spend 1
             Espionage to roll loaded dice that always come up 7/11" and
             "use creative persuasion to diffuse the customers" map onto
             these two skill beats; the skill path is the *better* path,
             never the only one (cf. CONTENT_STANDARDS §3).

BRANCHING is the heart of both quests: play straight and get fleeced,
read the con and turn it around, or throw in with the Crew — each with
distinct rewards, faction_rep (outlaws / cirque), npc_rep, and memories
so Fox & Rabbit remember the player at later events.

Quest dict format: see world/quests/__init__.py.
"""

QUESTS = {

    # ─────────────────────────────────────────────────────────────────────
    # STREET DICE — the buy-in and the con.
    # The Critter Crew aren't subtle; they pitch a "straight game of dice"
    # and fleece anyone who plays it honest. The dramatic turn: the game
    # is rigged, and a sharp enough mark can read it and flip the table.
    # ─────────────────────────────────────────────────────────────────────
    "street_dice": {
        "key": "street_dice",
        "title": "Street Dice",
        "giver": "rabbit of the critter crew",
        "description": (
            "A Cirque troupe in animal masks — the Critter Crew — has set "
            "up a dice game in the back room of the Broken Oar. Rabbit does "
            "the talking; Fox works the cup; the big one, Owl, just leans on "
            "the doorframe with a longsword and watches. They swear it's a "
            "straight game of Street Dice, coppers only, and that there's "
            "coin to be won.\n\n"
            "It is not a straight game. How you learn that is up to you. "
            "(Roll the real |wdice|n at the table for the feel of it — but "
            "the cup is loaded, and no honest toss will save your purse.)"
        ),
        "outcomes": {

            # ── Play it honest → get fleeced, walk out owing markers. ──
            "play_straight": {
                "label": "Play the game honest",
                "description": (
                    "Buy a stake in coppers, throw the bones, and trust the "
                    "Crew's word. The dice are kind for a toss or two — long "
                    "enough to make you bet big — and then they aren't. You "
                    "leave lighter than you came, holding nothing but a "
                    "scrawled debt marker. A hard lesson, cheaply bought."
                ),
                "objectives": [
                    {"type": "talk", "target": "rabbit of the critter crew",
                     "topic": "buy in", "tag": "buyin", "qty": 1,
                     "desc": "Buy into the game — |wask rabbit about buy in|n (0/1)"},
                    {"type": "gather", "target": "stake purse",
                     "requires": "buyin", "tag": "staked", "qty": 1,
                     "desc": "Pick up your stake of coppers (0/1)"},
                    {"type": "gather", "target": "copper debt marker",
                     "requires": "staked", "qty": 1,
                     "desc": "The bones turn cold — collect the debt marker "
                             "you've been left holding (0/1)"},
                    {"type": "deliver", "target": "fox of the critter crew",
                     "item": "copper debt marker", "qty": 1,
                     "desc": "Settle up — hand your marker to Fox (0/1)"},
                ],
                "rewards": {"silver": 0, "items": [], "reagents": {}},
                "faction_rep": {"cirque": 1, "outlaws": 1},
                "npc_rep_deltas": {"fox of the critter crew": 2,
                                   "rabbit of the critter crew": 1},
                "npc_memories": {
                    "fox of the critter crew":
                        "an easy mark who threw good coppers after bad and "
                        "never once smelled the rig — come back any time",
                    "rabbit of the critter crew":
                        "played our game straight and paid without a fuss; "
                        "useful, and gullible",
                },
            },

            # ── Read the rig (espionage) → catch the cheat, flip it. ──
            "catch_the_cheat": {
                "label": "Read the con and flip the table",
                "description": (
                    "Watch the cup, not the coins. A sharp enough eye "
                    "(|wespionage|n) catches the weighted bones every time "
                    "they come up seven, and the same twist of the wrist that "
                    "rigs the game can rig it your way. Palm the loaded dice, "
                    "call Fox's bluff, and walk out with the pot — Rabbit "
                    "respects a clean play even when it's at her expense."
                ),
                "objectives": [
                    {"type": "talk", "target": "rabbit of the critter crew",
                     "topic": "buy in", "tag": "buyin", "qty": 1,
                     "desc": "Buy into the game — |wask rabbit about buy in|n (0/1)"},
                    {"type": "skill", "target": "fox of the critter crew",
                     "skill": "espionage", "requires": "buyin", "tag": "spotted",
                     "qty": 1,
                     "desc": "Catch Fox working the rig — |wtreat fox of the "
                             "critter crew|n (espionage) (0/1)"},
                    {"type": "gather", "target": "loaded dice",
                     "requires": "spotted", "tag": "palmed", "qty": 1,
                     "desc": "Palm the loaded dice off the table as proof (0/1)"},
                    {"type": "deliver", "target": "rabbit of the critter crew",
                     "requires": "palmed", "qty": 1,
                     "desc": "Set the loaded dice in front of Rabbit and "
                             "collect the pot (0/1)"},
                ],
                "rewards": {"silver": 40, "items": [], "reagents": {}},
                "faction_rep": {"cirque": 2, "outlaws": 2},
                "npc_rep_deltas": {"rabbit of the critter crew": 4,
                                   "fox of the critter crew": -1},
                "npc_memories": {
                    "rabbit of the critter crew":
                        "read our rig cold and beat us at our own bones "
                        "without raising a hand — that one has the eye, and "
                        "I'd sooner hire them than cross them",
                    "fox of the critter crew":
                        "caught me working the cup and palmed our loaded "
                        "dice; never live that down",
                },
            },

            # ── Throw in with the Crew → join the racket. ──
            "join_the_crew": {
                "label": "Join the Critter Crew's racket",
                "description": (
                    "Why beat the con when you can run it? Show Rabbit you "
                    "see the game for what it is and offer to work the room "
                    "— steer fresh marks to the table, watch the door, take "
                    "a cut. The Crew pays Privilege to the Crimson Cartel to "
                    "stay independent; another sharp pair of hands is welcome. "
                    "The Crown would not approve."
                ),
                "objectives": [
                    {"type": "talk", "target": "fox of the critter crew",
                     "topic": "join the crew", "tag": "pitched", "qty": 1,
                     "desc": "Tell Fox you want in — |wask fox of the critter "
                             "crew about join the crew|n (0/1)"},
                    {"type": "skill", "target": "rabbit of the critter crew",
                     "skill": "espionage", "requires": "pitched", "tag": "proved",
                     "qty": 1,
                     "desc": "Prove your hands to Rabbit — |wtreat rabbit of "
                             "the critter crew|n (espionage) (0/1)"},
                    {"type": "gather", "target": "loaded dice",
                     "requires": "proved", "qty": 1,
                     "desc": "Take a pair of the Crew's loaded dice as your "
                             "own (0/1)"},
                ],
                "rewards": {"silver": 25, "items": [], "reagents": {}},
                "faction_rep": {"cirque": 3, "outlaws": 3, "crown": -3},
                "npc_rep_deltas": {"rabbit of the critter crew": 3,
                                   "fox of the critter crew": 3},
                "npc_memories": {
                    "rabbit of the critter crew":
                        "asked to run the bones with us and proved the hands "
                        "for it — a Critter now, owed a cut and a mask",
                    "fox of the critter crew":
                        "threw in with the Crew at the Broken Oar; one of "
                        "ours, and Rabbit likes them, worse luck for me",
                },
            },
        },
        "prereqs": [],
    },

    # ─────────────────────────────────────────────────────────────────────
    # BAD BEAT — the dramatic turn. Mid-game, two disgruntled marks (Blake
    # & Eckhart) storm the back room swearing the Crew fleeced them out of
    # five silver with scam dice. Both carry daggers; Owl squares up. The
    # doc puts resolution on the PCs: pay them off, talk them down, or side
    # with them against the Crew. Little to no fighting unless the player
    # forces it.
    # ─────────────────────────────────────────────────────────────────────
    "bad_beat": {
        "key": "bad_beat",
        "title": "Bad Beat",
        "giver": "rabbit of the critter crew",
        "description": (
            "The game's barely warm when two locals — Blake and Eckhart — "
            "shove past Owl into the back room, daggers half-drawn, swearing "
            "the Crew cheated them out of five silver. Rabbit's smile never "
            "moves; Fox's hand drifts toward the cup; Owl steps off the wall. "
            "Insult to injury, the Crew offers the furious pair a chance to "
            "win it back at the table. It falls to you to cool this down "
            "before it turns to knives in a crowded tavern."
        ),
        "outcomes": {

            # ── Pay them off → clean, costs you silver. ──
            "pay_them_off": {
                "label": "Pay the marks off yourself",
                "description": (
                    "Five silver buys quiet. Cover the Crew's debt out of "
                    "your own purse, press the coin into Blake's hand, and "
                    "send the pair off muttering. The Crew owes you one — "
                    "and they don't forget a favour any more than a slight."
                ),
                "objectives": [
                    {"type": "talk", "target": "blake the disgruntled mark",
                     "topic": "the debt", "tag": "heard", "qty": 1,
                     "desc": "Hear out Blake's grievance — |wask blake about "
                             "the debt|n (0/1)"},
                    {"type": "gather", "target": "settlement purse",
                     "requires": "heard", "tag": "purse", "qty": 1,
                     "desc": "Count out five silver of your own (0/1)"},
                    {"type": "deliver", "target": "blake the disgruntled mark",
                     "requires": "purse", "qty": 1,
                     "desc": "Press the silver on Blake and send him off (0/1)"},
                    {"type": "deliver", "target": "rabbit of the critter crew",
                     "qty": 1,
                     "desc": "Tell Rabbit it's handled (0/1)"},
                ],
                "rewards": {"silver": 10, "items": [], "reagents": {}},
                "faction_rep": {"cirque": 2, "outlaws": 1},
                "npc_rep_deltas": {"rabbit of the critter crew": 3,
                                   "fox of the critter crew": 2},
                "npc_memories": {
                    "rabbit of the critter crew":
                        "paid off our angry marks out of their own purse to "
                        "keep the bones rolling — a friend of the Crew, and "
                        "owed a favour",
                    "blake the disgruntled mark":
                        "the stranger who covered the Crew's debt; honest "
                        "enough, but they bought a cheat's silence",
                },
            },

            # ── Talk them down (influential) → no coin changes hands. ──
            "talk_them_down": {
                "label": "Talk the marks down",
                "description": (
                    "No coin, no blades — just words. Get Blake and Eckhart "
                    "telling their side until the heat bleeds out of them "
                    "(|winfluential|n), and walk them back from the knife's "
                    "edge to the door. The Crew keeps its silver; you keep "
                    "the peace; and two locals remember who spoke for them "
                    "when steel was already out."
                ),
                "objectives": [
                    {"type": "talk", "target": "blake the disgruntled mark",
                     "topic": "the debt", "tag": "heard", "qty": 1,
                     "desc": "Hear out Blake's grievance — |wask blake about "
                             "the debt|n (0/1)"},
                    {"type": "skill", "target": "eckhart the disgruntled mark",
                     "skill": "influential", "requires": "heard", "tag": "calmed",
                     "qty": 1,
                     "desc": "Cool Eckhart's temper before he draws — "
                             "|wtreat eckhart the disgruntled mark|n "
                             "(influential) (0/1)"},
                    {"type": "deliver", "target": "rabbit of the critter crew",
                     "requires": "calmed", "qty": 1,
                     "desc": "Let Rabbit know the room's calm again (0/1)"},
                ],
                "rewards": {"silver": 20, "items": [], "reagents": {}},
                "faction_rep": {"cirque": 1, "outlaws": 1, "crown": 1},
                "npc_rep_deltas": {"rabbit of the critter crew": 4,
                                   "blake the disgruntled mark": 2,
                                   "eckhart the disgruntled mark": 2},
                "npc_memories": {
                    "rabbit of the critter crew":
                        "talked our furious marks back from the door without "
                        "spending a copper of anyone's coin — that is rarer "
                        "than a sharp eye, and worth twice as much to me",
                    "eckhart the disgruntled mark":
                        "spoke me down from a stupid knife-fight I'd have "
                        "lost; I owe that one a hearing",
                },
            },

            # ── Side with the marks → expose the Crew, force the refund. ──
            "side_with_marks": {
                "label": "Side with the marks against the Crew",
                "description": (
                    "Blake and Eckhart aren't wrong, and you both know it. "
                    "Read the rig for what it is (|wespionage|n), set the "
                    "Crew's own loaded dice on the table where the whole "
                    "room can see, and make Rabbit pay the five silver back. "
                    "The marks walk away whole — the Crew walks away "
                    "remembering exactly who burned them."
                ),
                "objectives": [
                    {"type": "talk", "target": "blake the disgruntled mark",
                     "topic": "the debt", "tag": "heard", "qty": 1,
                     "desc": "Hear out Blake's grievance — |wask blake about "
                             "the debt|n (0/1)"},
                    {"type": "skill", "target": "fox of the critter crew",
                     "skill": "espionage", "requires": "heard", "tag": "exposed",
                     "qty": 1,
                     "desc": "Catch out the rig in front of the room — "
                             "|wtreat fox of the critter crew|n "
                             "(espionage) (0/1)"},
                    {"type": "gather", "target": "loaded dice",
                     "requires": "exposed", "tag": "proof", "qty": 1,
                     "desc": "Seize the loaded dice as proof for all to see (0/1)"},
                    {"type": "deliver", "target": "blake the disgruntled mark",
                     "requires": "proof", "qty": 1,
                     "desc": "Hand the recovered silver back to Blake (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"cirque": -3, "outlaws": -2, "crown": 2},
                "npc_rep_deltas": {"blake the disgruntled mark": 4,
                                   "eckhart the disgruntled mark": 4,
                                   "rabbit of the critter crew": -3,
                                   "fox of the critter crew": -3},
                "npc_memories": {
                    "blake the disgruntled mark":
                        "proved the Crew cheated us and made them pay it "
                        "back to the copper; a true friend, and welcome at "
                        "my hearth",
                    "rabbit of the critter crew":
                        "exposed our bones to a full room and shamed us into "
                        "a refund — cost us the den and worse, cost us face; "
                        "the Crew does not forget that",
                    "fox of the critter crew":
                        "showed the whole Oar our loaded dice; if I ever see "
                        "that mask of a face again it'll be the last thing "
                        "they gamble on",
                },
            },
        },
        "prereqs": ["street_dice"],
    },
}
