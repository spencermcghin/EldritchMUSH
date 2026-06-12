"""Event 3 — The Awakening: "'Shrooms Man".
Source: Drive / Reboot / Event 3 - The Awakening / Encounters /
  "'Shrooms Man" (doc 1vYLd7g-dImAlii2UAetoVY-AYSf2YBQI2I2gsIwFt5M)
  + "Eating a Mushroom - Consequence Letters" (Adjudicator letters,
  doc 1JmRcDCply5IO6N-leoPOSGONCM8aeKLQUZj779UZhj8).

Fidelity notes
--------------
The LARP plot: fae mushrooms from the Dark Forest grow in rings around
the site. Most who eat them sicken and could die; one player (Leila
Ember), uniquely "blessed with the Ancient Blood," instead receives
revelatory visions of past and future — at the cost of escalating
threats from the Fae (the Adjudicator's cease-and-desist letters) and
an eventual reckoning. The mushrooms are not loot: picked, they turn
to dust within a day, "denied the mystical energy of the Welkin."

In-game this becomes the apothecary/consumable + lore-vision showcase.
The dealer is reframed as a wilds forager — Welkin, the mushroom-man —
who tends the ring at the Thornwood Edge and warns that the Dark
Forest minds its property. The vision delivered is faithful to the
doc's vision slate: Vision 5 (the Unbound stirring in their tombs, a
passage through the realm of the Umbral and their impending rise) is
the prophecy this encounter foreshadows, with the Witch Queen rising
from her prison-tomb (pre-game vision) as the nearer dread. The risk
(sickness / the bad trip) and the Fae's retribution (the Adjudicator)
are preserved as the cost branch and the consequence written on all
sides.

Quest dict format: see world/quests/__init__.py.
"""

QUESTS = {

    # ─────────────────────────────────────────────────────────────────────────
    # EVENT 3 — "'SHROOMS MAN"  (alchemy/consumable + lore-vision showcase)
    # Anchor room: The Thornwood Edge (existing Annwyn forest room).
    # Branches: take the vision / refuse and walk clean / rob the forager.
    # ─────────────────────────────────────────────────────────────────────────
    "shrooms_man": {
        "key": "shrooms_man",
        "title": "The 'Shrooms Man",
        "giver": "welkin the forager",
        "description": (
            "A ring of pale, faintly-glowing mushrooms has pushed up "
            "through the leaf-mould at the Thornwood Edge, and a hermit "
            "tends them — Welkin, who calls himself a forager and smells "
            "of loam and something sweeter underneath. He'll let you eat "
            "one. He warns you the Dark Forest counts its mushrooms, that "
            "most who swallow one only sicken, and that what you might "
            "see could be worth more than your wits. Picked, the caps "
            "turn to dust by morning; this choice has to be made here, "
            "now, in the ring."
        ),
        "outcomes": {
            "take_the_vision": {
                "label": "Eat the mushroom and take the vision",
                "description": (
                    "Swallow the cap in the ring and let the Welkin take "
                    "you under. Most would only sicken — but you ride the "
                    "trip down into prophecy and come back with a vision "
                    "of the Unbound turning in their tombs and the Witch "
                    "Queen rising from her prison. The Dark Forest notices "
                    "the theft; the Adjudicator already has your name."
                ),
                "objectives": [
                    {"type": "explore", "target": "The Thornwood Edge", "qty": 1,
                     "tag": "in_ring",
                     "desc": "Step into the mushroom ring at the Thornwood Edge (0/1)"},
                    {"type": "gather", "target": "glowing fae mushroom", "qty": 1,
                     "requires": "in_ring", "tag": "ate",
                     "desc": "Take a glowing fae mushroom from the ring and eat it (0/1)"},
                    {"type": "talk", "target": "welkin the forager",
                     "topic": "the vision", "requires": "ate", "qty": 1,
                     "desc": "Let Welkin guide you through the vision — |wask welkin the vision|n (0/1)"},
                    {"type": "gather", "target": "vision of the unbound", "qty": 1,
                     "requires": "ate",
                     "desc": "Carry the vision back — take the vision of the Unbound (0/1)"},
                ],
                # The trip is real: the reward is preternatural insight (the
                # lore item) and the raw fae substance, against the cost of
                # the Adjudicator's enmity. No silver — you didn't sell
                # anything, you stole a glimpse.
                "rewards": {
                    "silver": 0,
                    "items": [],
                    "reagents": {"Harrowdust": 1, "Widow's Petal": 1},
                },
                "faction_rep": {"outsider": 3, "crown": -1},
                "npc_rep_deltas": {
                    "welkin the forager": 4,
                    "the adjudicator": -8,
                },
                "npc_memories": {
                    "welkin the forager":
                        "ate from the ring and rode the trip down into a true vision — Ancient Blood, maybe",
                    "the adjudicator":
                        "stole a glimpse of our realm through the sacred caps — the name is written; the reckoning is owed",
                },
            },

            "refuse_walk_clean": {
                "label": "Refuse the mushroom and walk away clean",
                "description": (
                    "Hear the Welkin out, study the ring, and leave the "
                    "caps where they grew. No vision, no sickness, no name "
                    "in the Book of the Unforgiven. The forager respects a "
                    "soul that knows when not to reach."
                ),
                "objectives": [
                    {"type": "talk", "target": "welkin the forager",
                     "topic": "the mushrooms", "qty": 1,
                     "desc": "Hear the Welkin out about the ring — |wask welkin the mushrooms|n (0/1)"},
                    {"type": "gather", "target": "glowing fae mushroom ring", "qty": 1,
                     "desc": "Study the ring without picking it (0/1)"},
                    {"type": "explore", "target": "The Old Road — South", "qty": 1,
                     "desc": "Walk back to the Old Road without eating a cap (0/1)"},
                ],
                "rewards": {"silver": 0, "items": [], "reagents": {}},
                "faction_rep": {"outsider": 1},
                "npc_rep_deltas": {"welkin the forager": 2},
                "npc_memories": {
                    "welkin the forager":
                        "knew when not to reach — left the ring as it grew",
                },
            },

            "rob_the_forager": {
                "label": "Rob the forager and hoard the caps",
                "description": (
                    "Don't eat one — take the lot. Strip the Welkin's ring "
                    "and pocket what you can sell to a desperate alchemist. "
                    "The caps will be dust by morning, the forager will not "
                    "forget the hand that robbed him, and the Dark Forest "
                    "marks a thief as surely as it marks a vision-thief."
                ),
                "objectives": [
                    {"type": "gather", "target": "glowing fae mushroom", "qty": 1,
                     "tag": "stripped",
                     "desc": "Strip the ring of its caps (0/1)"},
                    {"type": "deliver", "target": "welkin the forager",
                     "requires": "stripped", "qty": 1,
                     "desc": "Shove the forager aside — confront Welkin (0/1)"},
                ],
                "rewards": {
                    "silver": 20,
                    "items": [],
                    "reagents": {"Sayge": 2},
                },
                "faction_rep": {"outsider": -3, "outlaws": 2},
                "npc_rep_deltas": {
                    "welkin the forager": -10,
                    "the adjudicator": -4,
                },
                "npc_memories": {
                    "welkin the forager":
                        "stripped my ring bare and shoved me down for a fistful of dust",
                    "the adjudicator":
                        "laid hands on the sacred caps as a common thief — marked, lesser, but marked",
                },
            },
        },
        "prereqs": [],
    },
}
