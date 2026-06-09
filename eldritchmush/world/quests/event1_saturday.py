"""Event 1 — Relaunch / Saturday tutorials + investigations.
Source: Drive / Reboot / Event 1 - Relaunch / Saturday Morning, Afternoon, Night (folder 1MSWywuW2ZnzJVkYOFmUXoCIRd-vTGOAq).

Quest dict format: see world/quests/__init__.py.
"""

QUESTS = {

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
}
