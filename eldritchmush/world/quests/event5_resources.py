"""Event 5 — The Trial: "Finding Resources" (the settlement supply arc).
Source: Drive / Reboot / Event 5 - The Trial / Encounters /
"Finding Resources" by Spencer McGhin
(doc 1SMhNCIV7clm_nTqI-MRHhRGnfthXuy6YooFbdekKcO4).

Doc core: with House Laurent gone, the young settlement of Mystvale must
secure its own raw materials — apothecarial reagents, iron, good soil,
wild game/leather, and blighted lumber — from a contested wilderness held
by local residents, rival cirque troupes, and Blayne's Bastards thugs.
An Oban Lieutenant hands the town's people a map and a list of errands;
each resource is a two-step beat — first LOCATE it (a tracking/perception
skill read), then PERFORM a separate challenge to claim it — and the
proceeds raise the settlement's structures (a hunting lodge, a farmstead,
a forge). The doc's standing tension is the "expulsion of others from
newly acquired territory to solidify the claim": fortify the claim by
force, or share the bounty with the residents already on the land.

This is the GATHER + SKILL + ORDERED-BEAT showcase (no combat focus).
See docs/CONTENT_STANDARDS.md for the primitive reference.

Quest dict format: see world/quests/__init__.py.
"""

QUESTS = {

    # ─────────────────────────────────────────────────────────────────────────
    # FINDING RESOURCES — the foraging showcase.
    # Giver: Lieutenant Oban of the New Order (the doc's "Oban Lieutenant").
    # Each trail is an ordered chain: SCOUT (skill: tracking/perception)
    # → HARVEST (gather) → DELIVER (consuming) → the structure rises.
    # Branch at accept: secure the claim by driving the squatters off
    # (fortify), or share the bounty with the folk already on the land.
    # ─────────────────────────────────────────────────────────────────────────
    "finding_resources": {
        "key": "finding_resources",
        "title": "Finding Resources",
        "giver": "lieutenant oban of the new order",
        "description": (
            "With the Laurents fallen, no House feeds Mystvale now. "
            "Lieutenant Oban of the New Order spreads a map of "
            "Milersylvania across the gate table and marks it with the "
            "things the settlement starves for: herbs for the apothecary, "
            "iron for the forge, good soil for the fields, game and "
            "leather from the wood. Each must be FOUND before it can be "
            "TAKEN — a tracker's eye to read the trail, then the labour "
            "to claim it.\n\n"
            "But the wood is contested. Local woodfolk still work these "
            "trails, and Blayne's Bastards have been seen between the "
            "stakes. Oban offers a choice: secure the claim — drive the "
            "squatters off and raise the settlement's own — or share the "
            "bounty with the folk already on the land and raise it "
            "together. Bring a tracker; bring a sharp eye."
        ),
        "outcomes": {

            # ── PATH A: FORTIFY ──────────────────────────────────────────
            # The doc's hardline reading: "expulsion of others from their
            # newly acquired territory to solidify their claim." Drive the
            # rival claimants off the trails, then raise the lodge for the
            # New Order alone. Crown/Oban approves; the locals do not forget.
            "fortify_the_claim": {
                "label": "Secure the claim by force",
                "description": (
                    "Oban's way. The trails are Mystvale's now — run the "
                    "woodfolk and Blayne's Bastards off them, harvest "
                    "what the land owes, and raise the hunting lodge "
                    "under the New Order's banner. The Obans remember "
                    "loyalty. The land remembers the rest."
                ),
                "objectives": [
                    # ── Wild-game trail: ordered SCOUT → HARVEST → DELIVER.
                    # The doc's three tracking stakes (grouse/boar/deer)
                    # condensed to one tracking read that gates the harvest.
                    {"type": "skill", "target": "the game trail", "skill": "tracking",
                     "tag": "trail", "qty": 1,
                     "desc": "Read the game trail to its end — |wtreat the game trail|n "
                             "(tracking) (0/1)"},
                    {"type": "gather", "target": "bundle of raw leather",
                     "requires": "trail", "tag": "leather", "qty": 3,
                     "desc": "Once the trail is read, take the trappers' leather (0/3)"},
                    # Drive the rival claimants off the contested ground.
                    {"type": "kill", "target": "blayne's bastard",
                     "tag": "cleared", "qty": 2,
                     "desc": "Run Blayne's Bastards off the trail (0/2)"},
                    # ── Herb-foraging beat (the doc's scavenger hunt).
                    {"type": "gather", "target": "wild reagent cache", "qty": 3,
                     "desc": "Forage the wild reagent caches and map them (0/3)"},
                    # ── Iron source: a PERCEPTION read, not tracking — the
                    # doc's "use the magnet on soil samples to find iron."
                    {"type": "skill", "target": "the ore outcrop", "skill": "perception",
                     "tag": "ore", "qty": 1,
                     "desc": "Find iron in the rock — |wtreat the ore outcrop|n "
                             "(perception) (0/1)"},
                    # ── Deliver the whole haul to raise the lodge (consuming).
                    {"type": "deliver", "target": "lieutenant oban of the new order",
                     "item": "bundle of raw leather", "requires": "leather", "qty": 3,
                     "desc": "Pledge ALL the leather to raise the hunting lodge (0/3)"},
                ],
                "rewards": {
                    "silver": 45,
                    "items": ["LEATHER_ARMOR"],
                    "reagents": {"Thornwood Fern": 2, "Willow Root": 2, "Sayge": 2},
                },
                "faction_rep": {"crown": 4, "outlaws": -3, "outsider": -2},
                "npc_rep_deltas": {
                    "lieutenant oban of the new order": 8,
                    "rhys of the thornwood": -6,
                },
                "npc_memories": {
                    "lieutenant oban of the new order":
                        "secured the trails for the New Order and raised the lodge",
                    "rhys of the thornwood":
                        "drove my people off the trails we've worked for years",
                },
            },

            # ── PATH B: SHARE ────────────────────────────────────────────
            # Work WITH the woodfolk instead of clearing them. The locals
            # show you the trails (the skill beats still gate harvest), and
            # you cleanse the blighted lumber instead of taking it by force.
            # Crown gives less; the land and the rangers remember the hand.
            "share_the_bounty": {
                "label": "Share the bounty with the woodfolk",
                "description": (
                    "Rhys of the Thornwood and his people have read "
                    "these trails for years. Work the land WITH them — "
                    "let them guide you to the game, lift the Hive "
                    "Mother's blight from the lumber instead of stripping "
                    "the wood bare, and raise the farmstead for everyone "
                    "who'll winter here. The Obans pay less for mercy. "
                    "The wood will pay it back."
                ),
                "objectives": [
                    # Same ordered SCOUT → HARVEST, but the woodfolk's
                    # guidance is what arms the tracking read.
                    {"type": "talk", "target": "rhys of the thornwood", "topic": "trails",
                     "tag": "guide", "qty": 1,
                     "desc": "Ask Rhys to share the trails (0/1)"},
                    {"type": "skill", "target": "the game trail", "skill": "tracking",
                     "requires": "guide", "tag": "trail", "qty": 1,
                     "desc": "With Rhys's word, read the game trail — "
                             "|wtreat the game trail|n (tracking) (0/1)"},
                    {"type": "gather", "target": "bundle of raw leather",
                     "requires": "trail", "tag": "leather", "qty": 2,
                     "desc": "Share the take of leather with the settlement (0/2)"},
                    # The doc's Lumber beat: cleanse the Hive Mother's
                    # blight rather than fell the infected wood.
                    {"type": "gather", "target": "soil sample",
                     "tag": "soil", "qty": 3,
                     "desc": "Collect soil samples for the alchemists to read (0/3)"},
                    {"type": "skill", "target": "the blighted stump", "skill": "perception",
                     "requires": "soil", "tag": "blight", "qty": 1,
                     "desc": "Trace the Hive Mother's mycelium to its root — "
                             "|wtreat the blighted stump|n (perception) (0/1)"},
                    # Deliver to raise the farmstead — for everyone.
                    {"type": "deliver", "target": "rhys of the thornwood",
                     "item": "soil sample", "requires": "soil", "qty": 3,
                     "desc": "Bring the soil to Rhys to seed the shared farmstead (0/3)"},
                ],
                "rewards": {
                    "silver": 25,
                    "items": [],
                    "reagents": {
                        "Celandine": 2, "Amber Lichen": 2,
                        "Creeper Moss": 2, "Willow Root": 1,
                    },
                },
                "faction_rep": {"crown": 1, "rangers": 4, "outsider": 3},
                "npc_rep_deltas": {
                    "rhys of the thornwood": 8,
                    "lieutenant oban of the new order": -3,
                },
                "npc_memories": {
                    "rhys of the thornwood":
                        "worked the trails with us and raised the farmstead for all",
                    "lieutenant oban of the new order":
                        "shared the settlement's bounty instead of seizing it",
                },
            },
        },
        "prereqs": [],
    },
}
