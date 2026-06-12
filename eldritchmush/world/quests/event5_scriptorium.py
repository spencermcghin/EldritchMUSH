"""Event 5 — The Lost Scriptorium (the EXPLORE + ORDERED-BEAT + TALK showcase).

Source: Drive / Reboot / Event 5 - The Trial (folder
1YqBD3cm5Y9swi4XqCMmMNh8I5ejf6QMs) → "The Lost Scriptorium" by Spencer
McGhin, with Zeke's Letter and the door-riddle prop
("What is written, must be sealed").

FIDELITY NOTE
The researcher Zeke followed a map he believed led to a hidden library
of the Annwyn's secrets. It was a trap. The scriptorium was raised by
nethermancers and kept standing by what they did to the dead; Zeke was
cut down at its locked door before he could leave a last warning for
his friend Tyran. His corpse rose as a chained ghoul; his ghost replays
his final minutes, fleeing toward the door, searching his pockets for
keys he no longer carries. His unfinished business is the unwritten
note — and the journal of the builders, which his letter begged be
*burned, not read*: "Don't read it. Just burn it. There's nothing in
there you want to know."

This is an investigation, not a fight. The player descends through the
scriptorium grounds (EXPLORE), recovers Zeke's two keys from the chained
ghoul and works the lock-riddle (ordered GATHER), gathers the writing
implements so the ghost can finish his note (ordered GATHER), and only
THEN — having learned the truth — can address the ghost (TALK), and
choose: honour his last wish and burn the journal to lay him to rest,
or break it and keep the nethermancers' secrets for yourself.

Quest dict format: see world/quests/__init__.py.
"""

QUESTS = {

    # ─────────────────────────────────────────────────────────────────────────
    # EVENT 5 — THE LOST SCRIPTORIUM
    # Entrance attached to "The Ruins of Tamris — The Old Square" (a real,
    # pre-existing Tamris room: "something has been digging among the
    # ruins recently; fresh earth surrounds several broken crypts").
    # The giver is the ghost itself — the player meets Zeke's looping
    # apparition at the scriptorium door and is drawn into laying it to
    # rest. Per source, a luminous Zeke flees toward the locked door,
    # again and again, until his ghoul is dealt with and his note is
    # finished.
    # ─────────────────────────────────────────────────────────────────────────
    "the_lost_scriptorium": {
        "key": "the_lost_scriptorium",
        "title": "The Lost Scriptorium",
        "giver": "the apparition of zeke",
        "description": (
            "Among the broken crypts of old Tamris a light moves that is "
            "not a torch: the shade of a man named Zeke, a researcher who "
            "followed a map to a hidden library and found a trap instead. "
            "Again and again his apparition flees toward a locked door, "
            "searching his pockets for keys he no longer carries, and "
            "vanishes — only to begin again. He cannot rest until the "
            "letter he died trying to write is finished and his last wish "
            "honoured.\n\n"
            "Descend through the scriptorium. His chained corpse still "
            "wears the satchel with his keys; the door asks a riddle of "
            "their order. Inside, the dark drinks every flame. Find what "
            "he needs to set down his final words — then learn what this "
            "place truly is, and decide what becomes of the journal he "
            "begged be burned."
        ),
        "outcomes": {

            # ─────────────────────────────────────────────────────────────
            # PATH 1 — Lay him to rest. Honour the letter: burn the
            # journal unread, let Zeke finish his warning, release him.
            # ─────────────────────────────────────────────────────────────
            "lay_to_rest": {
                "label": "Burn the journal, lay Zeke to rest",
                "description": (
                    "Do as the dying man asked. Recover his keys, open "
                    "the door in the order the riddle demands, give his "
                    "ghost the means to finish his letter — then burn the "
                    "nethermancers' journal unread, as he begged. The "
                    "light goes out of him gently. He is grateful, at the "
                    "last, to a stranger who kept faith with a dead man's "
                    "wish."
                ),
                "objectives": [
                    # EXPLORE — the descent through the scriptorium grounds.
                    {"type": "explore", "target": "The Lost Scriptorium — The Sunken Door",
                     "tag": "door", "qty": 1,
                     "desc": "Follow Zeke's apparition down to the sunken scriptorium door (0/1)"},
                    # GATHER (ordered) — recover the two keys from the chained
                    # ghoul, then read the door-riddle. The ghoul's satchel
                    # holds the quill key and the wax key. The keys are
                    # examined-from-the-corpse clue props.
                    {"type": "gather", "target": "the quill key",
                     "requires": "door", "tag": "quill_key", "qty": 1,
                     "desc": "Take the quill-marked key from the chained ghoul's satchel (0/1)"},
                    {"type": "gather", "target": "the wax-seal key",
                     "requires": "door", "tag": "wax_key", "qty": 1,
                     "desc": "Take the wax-seal key from the chained ghoul's satchel (0/1)"},
                    # GATHER (ordered) — solve the lock-riddle: study the
                    # graven door. "What is written, must be sealed" — quill
                    # (written) first, wax (sealed) after. This is the ordered
                    # gate that opens the way in.
                    {"type": "gather", "target": "the graven scriptorium door",
                     "requires": "wax_key", "tag": "unlocked", "qty": 1,
                     "desc": "Work the riddle — written, then sealed — and unlock the door (0/1)"},
                    # EXPLORE — within. The dark drinks every flame.
                    {"type": "explore", "target": "The Lost Scriptorium — The Reading Hall",
                     "requires": "unlocked", "tag": "inside", "qty": 1,
                     "desc": "Step into the dead reading hall (0/1)"},
                    # GATHER (ordered) — the writing implements Zeke's ghost
                    # needs to finish his note: ink, quill, paper, and a lit
                    # candle. All four are examined-from-the-scene clue props.
                    {"type": "gather", "target": "the spilled inkwell",
                     "requires": "inside", "tag": "ink", "qty": 1,
                     "desc": "Salvage ink from the spilled well for the ghost's pen (0/1)"},
                    {"type": "gather", "target": "the broken quill",
                     "requires": "inside", "tag": "pen", "qty": 1,
                     "desc": "Find a quill the ghost can hold (0/1)"},
                    {"type": "gather", "target": "the last clean page",
                     "requires": "inside", "tag": "page", "qty": 1,
                     "desc": "Find one unspoiled page among the ruin (0/1)"},
                    {"type": "gather", "target": "the guttered candle",
                     "requires": "inside", "tag": "light", "qty": 1,
                     "desc": "Coax a single candle to light so he can see to write (0/1)"},
                    # GATHER (ordered) — only once he can write does the truth
                    # surface: the nethermancers' journal, the thing his letter
                    # begged be burned. Finding it is the dramatic turn.
                    {"type": "gather", "target": "the nethermancers' journal",
                     "requires": "light", "tag": "journal", "qty": 1,
                     "desc": "Uncover the builders' journal Zeke died to keep shut (0/1)"},
                    # TALK (ordered) — confront the ghost with what you have
                    # learned. Promise to burn it. This is the resolution beat,
                    # gated on the whole investigation.
                    {"type": "talk", "target": "the apparition of zeke",
                     "topic": "burn", "requires": "journal", "tag": "promise", "qty": 1,
                     "desc": "Tell Zeke's ghost the journal will burn, as he asked — "
                             "|wask the apparition of zeke about burn|n (0/1)"},
                    # GATHER (ordered) — the act itself: burn the journal at
                    # the cold hearth. Consumes the clue. The light leaves him.
                    {"type": "gather", "target": "the cold scriptorium hearth",
                     "requires": "promise", "qty": 1,
                     "desc": "Burn the journal unread at the hearth and let Zeke rest (0/1)"},
                ],
                "rewards": {"silver": 35, "items": [],
                            "reagents": {"Grave Blood": 1, "Crypt Moss": 2}},
                "faction_rep": {"crown": 2, "outsider": 3},
                "npc_rep_deltas": {"the apparition of zeke": 10},
                "npc_memories": {
                    "the apparition of zeke":
                        "kept faith with a dead man's last wish and burned the "
                        "journal unread — released me, grateful, into the dark",
                },
            },

            # ─────────────────────────────────────────────────────────────
            # PATH 2 — The darker turn. Take the nethermancers' journal for
            # yourself. Read what he begged you not to. Zeke does not rest;
            # he watches you walk out with the thing that killed him.
            # ─────────────────────────────────────────────────────────────
            "claim_the_journal": {
                "label": "Read the journal, keep its secrets",
                "description": (
                    "He begged that it be burned. But a library of the "
                    "Annwyn's secrets does not come twice, and the dead "
                    "have no use for knowledge. Recover the keys, open the "
                    "door, find the journal of the men who raised this "
                    "place — and keep it. Zeke's ghost does not vanish. It "
                    "watches you carry his murder out into the light, and "
                    "it does not forgive."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Lost Scriptorium — The Sunken Door",
                     "tag": "door", "qty": 1,
                     "desc": "Follow Zeke's apparition down to the sunken scriptorium door (0/1)"},
                    {"type": "gather", "target": "the quill key",
                     "requires": "door", "tag": "quill_key", "qty": 1,
                     "desc": "Take the quill-marked key from the chained ghoul's satchel (0/1)"},
                    {"type": "gather", "target": "the wax-seal key",
                     "requires": "door", "tag": "wax_key", "qty": 1,
                     "desc": "Take the wax-seal key from the chained ghoul's satchel (0/1)"},
                    {"type": "gather", "target": "the graven scriptorium door",
                     "requires": "wax_key", "tag": "unlocked", "qty": 1,
                     "desc": "Work the riddle — written, then sealed — and unlock the door (0/1)"},
                    {"type": "explore", "target": "The Lost Scriptorium — The Reading Hall",
                     "requires": "unlocked", "tag": "inside", "qty": 1,
                     "desc": "Step into the dead reading hall (0/1)"},
                    # The darker path skips the act of mercy — no implements
                    # for the ghost, no finished note. Go straight for the
                    # forbidden journal once inside.
                    {"type": "gather", "target": "the nethermancers' journal",
                     "requires": "inside", "tag": "journal", "qty": 1,
                     "desc": "Seize the builders' journal Zeke died to keep shut (0/1)"},
                    # TALK (ordered) — face him with your intent. Tell him you
                    # mean to keep it. He pleads, and is refused.
                    {"type": "talk", "target": "the apparition of zeke",
                     "topic": "keep", "requires": "journal", "tag": "refusal", "qty": 1,
                     "desc": "Tell Zeke's ghost the journal is yours now — "
                             "|wask the apparition of zeke about keep|n (0/1)"},
                    # EXPLORE — carry the thing that killed him back into the
                    # ruins. He does not vanish; the loop does not end.
                    {"type": "explore", "target": "The Ruins of Tamris — The Old Square",
                     "requires": "refusal", "qty": 1,
                     "desc": "Carry the journal back up into the light of Tamris (0/1)"},
                ],
                "rewards": {"silver": 15, "items": [],
                            "reagents": {"Essence of the Unhallowed": 1, "Grave Blood": 1}},
                "faction_rep": {"crown": -3, "outsider": 4},
                "npc_rep_deltas": {"the apparition of zeke": -100},
                "npc_memories": {
                    "the apparition of zeke":
                        "broke faith with my last wish and carried the "
                        "nethermancers' journal out into the world — I do not "
                        "rest, and I will know the hand that did it",
                },
            },
        },
        "prereqs": [],
    },
}
