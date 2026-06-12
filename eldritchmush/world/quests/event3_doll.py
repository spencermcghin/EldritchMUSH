"""Event 3 — The Awakening: "The Awakened Doll" (Penny).
Source: Drive / Reboot / Event 3 / "Encounter: Awakened Doll" by Harrison
        (folder 1Lj6rNRfQdFMwaL7GSCwKzhuFUsNHkav7;
         doc 1bES33IWBH0F0deFADk3usR2qFbGGxZMlSP40yFgRTOE).

A quiet-horror, dialogue-and-choice piece — the deliberate tonal contrast
to the combat anchors. A witch's shrine and a spurned bride's wish woke
Penny, a child's doll grown person-sized, sociopathic and innocent at once.
She murdered Abigail's faithless betrothed as a "game," and Abigail —
terrified — abandoned her blindfolded in the woods. Now Penny waits at
the treeline below Manor Row, weeping for her lost friend, while Abigail
hides at the Stag Hall kitchen yard, praying no one reunites them.

The doc's spine is a TALK + SKILL + BRANCH showcase:
  * You cannot kill Penny with a blade — steel only ragdolls her; she
    keeps talking. So there is no `kill` path here. Resolution is
    conversation and skilled ritual, not damage.
  * Four mutually exclusive resolutions of the doll, each from a
    different discipline, each writing a different memory on Penny:
      - Disenchant (faith / vigil) — sever the curse-link, free her soul.
      - Dissect    (espionage)     — cut her open for Welkin + Metaphysics lore.
      - Dismantle  (blacksmith)    — render her for wood, gold, iron, leather.
      - Set free   (talk)          — teach her empathy; she walks singing
                                     into the woods (FUTURE PLOT seed).
  * And a separate human reckoning over Abigail — keep her secret, or
    turn her in for witchcraft and murder.

Per CONTENT_STANDARDS: branches change play (distinct objectives + gates),
skill beats use real skills via `treat`, and consequence persists — a
destroyed Penny remembers being unmade; a freed Penny remembers mercy.

Quest dict format: see world/quests/__init__.py.
"""

QUESTS = {

    # ─────────────────────────────────────────────────────────────────────
    # THE AWAKENED DOLL — the doll's fate (4 ways; no path can be "killed")
    # Giver: penny (the weeping doll). She does not know she is a problem;
    # the talk beats are how the player uncovers her nature. Abigail seeds
    # the destruction paths in her own knowledge, but Penny is the giver
    # because the encounter begins at her crying.
    # ─────────────────────────────────────────────────────────────────────
    "the_awakened_doll": {
        "key": "the_awakened_doll",
        "title": "The Awakened Doll",
        "giver": "penny the doll",
        "description": (
            "Something is weeping at the treeline below Manor Row — a "
            "child's doll grown to the size of a person, one arm gone, "
            "blood dried brown on the hand that remains. She calls "
            "herself Penny, and she is looking for her friend Abigail. "
            "Talk to her long enough and the cold truth surfaces: Penny "
            "killed a man as a game, feels nothing for it, and would "
            "dearly like to play again. Steel will not end her — it only "
            "lays her in the dirt, still talking. What is done with her "
            "is a matter of conscience, not combat. Draw out her story, "
            "then choose her fate."
        ),
        "outcomes": {

            # ── DISENCHANT — the faith path (Aurorym / vigil) ────────────
            "disenchant_her": {
                "label": "Sever the curse and free her soul (faith)",
                "description": (
                    "The malice is not Penny's; it is the witch's sigil "
                    "and the link to Abigail's grief. Coax the truth of "
                    "her waking from her, then pray it out of her — a "
                    "Faithful hand can return her to a small, still, "
                    "sleeping toy and quiet the witch's shrine a little. "
                    "No lore, no salvage; only mercy and a blow against "
                    "the Awakening. (Learn how she woke, then |wtreat "
                    "penny the doll|n — needs vigil.)"
                ),
                "objectives": [
                    {"type": "talk", "target": "penny the doll",
                     "topic": "shrine", "tag": "waking", "qty": 1,
                     "desc": "Learn how Penny woke — ask her about the |wshrine|n (0/1)"},
                    {"type": "skill", "target": "penny the doll",
                     "skill": "vigil", "requires": "waking", "qty": 1,
                     "desc": "Pray the curse out of her — |wtreat penny the doll|n (vigil) (0/1)"},
                ],
                "rewards": {"silver": 15, "items": [], "reagents": {}},
                "faction_rep": {"crown": 2, "outsider": 2, "outlaws": -1},
                "npc_rep_deltas": {"penny the doll": 8, "abigail the cook": 4},
                "npc_memories": {
                    "penny the doll":
                        "laid her down gentle and prayed the witch's sigil "
                        "out — she fell asleep smiling, a child's toy again",
                    "abigail the cook":
                        "freed her of the cursed thing without spilling her "
                        "secret to the pyre — and struck at the witch besides",
                },
            },

            # ── DISSECT — the scholar path (espionage / study) ───────────
            "dissect_her": {
                "label": "Open her up for what she knows (study)",
                "description": (
                    "Penny does not feel pain and stays unnervingly "
                    "talkative under the knife — she will answer questions "
                    "about her own insides while you cut. A careful study "
                    "yields a cloth heart that pulses (Metaphysics) and a "
                    "bottled, restless smoke from her burned stuffing "
                    "(Welkin). The study ruins her for salvage and ends "
                    "her for good. (Draw out the sigil's |wvengeance|n, "
                    "then |wtreat penny the doll|n — needs espionage.)"
                ),
                "objectives": [
                    {"type": "talk", "target": "penny the doll",
                     "topic": "vengeance", "tag": "studied", "qty": 1,
                     "desc": "Get her talking about the sigil — ask about |wvengeance|n (0/1)"},
                    {"type": "skill", "target": "penny the doll",
                     "skill": "espionage", "requires": "studied", "qty": 1,
                     "desc": "Dissect her for her secrets — |wtreat penny the doll|n (espionage) (0/1)"},
                ],
                "rewards": {
                    "silver": 20,
                    "items": ["MORPHOS_LORE_SCROLL"],
                    "reagents": {},
                },
                "faction_rep": {"crown": 1, "outsider": -1},
                "npc_rep_deltas": {"penny the doll": -10, "abigail the cook": 3},
                "npc_memories": {
                    "penny the doll":
                        "cut me open piece by piece while I answered their "
                        "questions, and took the sigil from my head — it was "
                        "not a fun game",
                    "abigail the cook":
                        "unmade the doll for its secrets and asked no awkward "
                        "questions of the cook",
                },
            },

            # ── DISMANTLE — the crafter path (blacksmith / salvage) ──────
            "dismantle_her": {
                "label": "Render her down for materials (crafting)",
                "description": (
                    "Strip the doll to her parts: seasoned wood, the gold "
                    "of her eyes, iron joints, good leather. A practical "
                    "end, and a profitable one — but it buys nothing of "
                    "what she knew, and she talks the whole way down. "
                    "(Get her to show you her |wseams|n, then |wtreat "
                    "penny the doll|n — needs blacksmith.)"
                ),
                "objectives": [
                    {"type": "talk", "target": "penny the doll",
                     "topic": "seams", "tag": "opened", "qty": 1,
                     "desc": "Get her to show you her |wseams|n (0/1)"},
                    {"type": "skill", "target": "penny the doll",
                     "skill": "blacksmith", "requires": "opened", "qty": 1,
                     "desc": "Render her for materials — |wtreat penny the doll|n (blacksmith) (0/1)"},
                ],
                # The doc's "valuable resources (wood, gold, iron, leather)"
                # — abstracted to coin (no raw-material prototype exists to
                # spawn) plus a salvaged reagent off her stuffing.
                "rewards": {
                    "silver": 45,
                    "items": [],
                    "reagents": {"Amber Lichen": 2},
                },
                "faction_rep": {"outsider": -2},
                "npc_rep_deltas": {"penny the doll": -10, "abigail the cook": 3},
                "npc_memories": {
                    "penny the doll":
                        "pulled my seams open for the wood and the gold while "
                        "I asked them why — they would not say",
                    "abigail the cook":
                        "took the doll apart for parts and never breathed a "
                        "word of her cook to the watch",
                },
            },

            # ── SET FREE — the mercy-without-faith path (talk only) ──────
            "set_her_free": {
                "label": "Teach her, and let her go (talk)",
                "description": (
                    "Penny does not know what pain is, or that murder is "
                    "anything but a game — and no one ever told her. It "
                    "can be done, but it takes patience: teach her what "
                    "hurting is, what empathy means, and give her gentler "
                    "games to want. Convince her, and she will walk "
                    "singing into the woods and trouble no one — for now. "
                    "(Teach her about |wpain|n, then about |wempathy|n.)"
                ),
                "objectives": [
                    {"type": "talk", "target": "penny the doll",
                     "topic": "pain", "tag": "pain", "qty": 1,
                     "desc": "Teach her what |wpain|n is (0/1)"},
                    {"type": "talk", "target": "penny the doll",
                     "topic": "empathy", "requires": "pain", "qty": 1,
                     "desc": "Teach her |wempathy|n, and a kinder game to play (0/1)"},
                ],
                "rewards": {"silver": 10, "items": [], "reagents": {}},
                "faction_rep": {"outsider": 3, "crown": -1},
                "npc_rep_deltas": {"penny the doll": 12, "abigail the cook": -2},
                "npc_memories": {
                    "penny the doll":
                        "taught me that hurting is real and gave me new games "
                        "— I will remember them, and I will remember the hand "
                        "that let me walk into the trees",
                    "abigail the cook":
                        "set the doll loose in the woods instead of ending it "
                        "— she is still out there, and Abigail knows it",
                },
            },
        },
        "prereqs": [],
    },

    # ─────────────────────────────────────────────────────────────────────
    # ABIGAIL'S RECKONING — the human verdict, after Penny is dealt with.
    # Abigail wished a man dead in earshot of a cursed doll; the doll
    # obliged. Keep her secret, or hand her to the watch for witchcraft
    # and murder. She would rather run than burn.
    # ─────────────────────────────────────────────────────────────────────
    "abigails_reckoning": {
        "key": "abigails_reckoning",
        "title": "Abigail's Reckoning",
        "giver": "abigail the cook",
        "description": (
            "With the doll dealt with, the cook is left — Abigail, who "
            "wished her faithless betrothed dead in a doll's hearing and "
            "watched it carry the wish out in the night. She will confess "
            "the wish and the murder if she is promised protection; what "
            "she fears is the pyre the Aurorym keeps for witches. The "
            "verdict is yours: keep her secret and let her live, or give "
            "her to Captain Vance for witchcraft and a man's death."
        ),
        "outcomes": {
            "keep_her_secret": {
                "label": "Keep Abigail's secret",
                "description": (
                    "A wish is not a knife. Hear her confession, promise "
                    "your silence, and let a frightened woman keep her "
                    "life. The Crown would not approve, if the Crown knew."
                ),
                "objectives": [
                    {"type": "talk", "target": "abigail the cook",
                     "topic": "confession", "qty": 1,
                     "desc": "Hear Abigail's |wconfession|n (0/1)"},
                ],
                "rewards": {"silver": 10, "items": [], "reagents": {}},
                "faction_rep": {"outsider": 2, "crown": -2, "outlaws": 1},
                "npc_rep_deltas": {"abigail the cook": 10},
                "npc_memories": {
                    "abigail the cook":
                        "heard the worst of me and swore to keep it — I owe "
                        "them my life and they will never have to ask twice",
                },
            },
            "turn_her_in": {
                "label": "Hand Abigail to the watch",
                "description": (
                    "Witchcraft and a murder done by it. Get her "
                    "confession and march her to Captain Vance before she "
                    "bolts for the trees. The Aurorym will see her "
                    "burned; the Crown calls it justice."
                ),
                "objectives": [
                    {"type": "talk", "target": "abigail the cook",
                     "topic": "confession", "tag": "confessed", "qty": 1,
                     "desc": "Get Abigail's |wconfession|n (0/1)"},
                    {"type": "deliver", "target": "captain vance of the mistguard",
                     "requires": "confessed", "qty": 1,
                     "desc": "Turn Abigail over to Captain Vance (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"crown": 3, "outsider": -3, "outlaws": -1},
                "npc_rep_deltas": {
                    "abigail the cook": -100,
                    "captain vance of the mistguard": 4,
                },
                "npc_memories": {
                    "abigail the cook":
                        "gave me to the pyre for a wish I made in grief — if "
                        "I had run faster I would be free",
                    "captain vance of the mistguard":
                        "brought a confessed witch in for the murder at Stag Hall",
                },
            },
        },
        "prereqs": ["the_awakened_doll"],
    },
}
