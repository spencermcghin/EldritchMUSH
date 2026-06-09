"""Event 5 — The Trial (partial: grizzled veteran prologue).
Source: Drive / Reboot / Event 5 - The Trial (folder 1YqBD3cm5Y9swi4XqCMmMNh8I5ejf6QMs).

Quest dict format: see world/quests/__init__.py.
"""

QUESTS = {

    # ─────────────────────────────────────────────────────────────────────────
    # EVENT 5 — THE TRIAL (anchor quests)
    # Source: Drive / Reboot / Event 5 / "Prologue: The Trial".
    # 10th Moon Cycle 765 — late autumn. House Laurent has fallen
    # (Silas + Ludmilla poisoned/captured Spring 765, Carran burned by
    # House Oban). Cale dead (per Event 4 canon). Plague spreads.
    # Nethermancer escaped Spring market with the fel tome. Aurorym
    # faith crumbling.
    # ─────────────────────────────────────────────────────────────────────────
    "bannon_remnant": {
        "key": "bannon_remnant",
        "title": "Bannon Remnant",
        "giver": "ser branwen of lex talionis",
        "description": (
            "Ser Branwen leads the last loyal Lex Talionis company at "
            "the half-burned Stag Hall courtyard. With the Laurents "
            "dead or captive, she's looking to either rebuild what's "
            "left of the Bannon faction in Mistvale's shadow or hand "
            "the company over to whoever can keep her people fed."
        ),
        "outcomes": {
            "rebuild_with_them": {
                "label": "Rebuild the Bannon faction",
                "description": (
                    "Stand with Ser Branwen and the Lex Talionis "
                    "survivors. Pledge supplies and the company holds. "
                    "Bannons remember the loyalty."
                ),
                "objectives": [
                    {"type": "gather", "target": "dawnhaven supply chest", "qty": 1,
                     "desc": "Take a supply chest as foundation goods (0/1)"},
                    {"type": "deliver", "target": "ser branwen of lex talionis", "qty": 1,
                     "desc": "Pledge the chest to the Bannon company (0/1)"},
                ],
                "rewards": {"silver": 40, "items": [], "reagents": {}},
                "faction_rep": {"crown": 4, "outsider": -1},
                "npc_rep_deltas": {"ser branwen of lex talionis": 8},
                "npc_memories": {"ser branwen of lex talionis": "stood with the last Bannons"},
            },
            "hand_over_to_oban": {
                "label": "Hand the company to House Oban",
                "description": (
                    "Sell out the Bannon survivors to Lord Niall Oban "
                    "via Korr the Pardoned. Oban silver in hand, "
                    "Bannon survivors stripped of their last weapons."
                ),
                "objectives": [
                    {"type": "explore", "target": "Stag Hall Courtyard", "qty": 1,
                     "desc": "Audit the Lex Talionis position (0/1)"},
                    {"type": "deliver", "target": "korr the pardoned", "qty": 1,
                     "desc": "Hand intel on Lex Talionis to Korr (0/1)"},
                ],
                "rewards": {"silver": 60, "items": [], "reagents": {}},
                "faction_rep": {"crown": -5, "crows": 3, "outlaws": 2},
                "npc_rep_deltas": {
                    "ser branwen of lex talionis": -10,
                    "korr the pardoned": 4,
                },
                "npc_memories": {
                    "ser branwen of lex talionis": "betrayed the Bannons to Oban",
                    "korr the pardoned": "delivered Bannon intel for coin",
                },
            },
            "walk_away": {
                "label": "Walk away from the politics",
                "description": (
                    "Houses rise, houses fall. None of them are yours. "
                    "Take a small payment for showing up and leave the "
                    "courtyard."
                ),
                "objectives": [
                    {"type": "explore", "target": "Stag Hall Courtyard", "qty": 1,
                     "desc": "Hear Ser Branwen's pitch and refuse (0/1)"},
                ],
                "rewards": {"silver": 10, "items": [], "reagents": {}},
                "faction_rep": {"outsider": 3},
                "npc_rep_deltas": {"ser branwen of lex talionis": -2},
                "npc_memories": {"ser branwen of lex talionis": "would not stand with anyone"},
            },
        },
        "prereqs": [],
    },

    "oban_pardon": {
        "key": "oban_pardon",
        "title": "The Oban Pardon",
        "giver": "korr the pardoned",
        "description": (
            "Korr — a Crow pardoned into Lord Niall Oban's army — "
            "offers a private deal at Carran. The Oban supply manifest "
            "in his locker is worth real coin to the right buyer. The "
            "wrong buyer would mean Korr's neck on a noose. Choose the "
            "buyer."
        ),
        "outcomes": {
            "trust_the_pardoned": {
                "label": "Take the manifest and disappear",
                "description": (
                    "Pocket the Oban supply manifest and slip out of "
                    "Carran clean. Quiet payday; quiet enemy."
                ),
                "objectives": [
                    {"type": "gather", "target": "oban supply manifest", "qty": 1,
                     "desc": "Take the Oban supply manifest (0/1)"},
                    {"type": "explore", "target": "The Mystvale Marketplace", "qty": 1,
                     "desc": "Slip back to Mistvale unseen (0/1)"},
                ],
                "rewards": {"silver": 50, "items": [], "reagents": {}},
                "faction_rep": {"crown": -2, "outlaws": 3, "outsider": 1},
                "npc_rep_deltas": {"korr the pardoned": 4},
                "npc_memories": {"korr the pardoned": "kept the deal quiet"},
            },
            "kill_korr": {
                "label": "Kill Korr as a Crow informant",
                "description": (
                    "An ex-Crow with a noble's seal is too dangerous "
                    "to leave breathing. Take the manifest off the "
                    "corpse. House Oban will be furious."
                ),
                "objectives": [
                    {"type": "kill", "target": "korr the pardoned", "qty": 1,
                     "desc": "Eliminate Korr (0/1)"},
                    {"type": "gather", "target": "oban supply manifest", "qty": 1,
                     "desc": "Recover the manifest (0/1)"},
                ],
                "rewards": {"silver": 25, "items": [], "reagents": {}},
                "faction_rep": {"crown": -1, "crows": -3, "outlaws": -3, "outsider": 2},
                "npc_rep_deltas": {"korr the pardoned": -100},
                "npc_memories": {},
            },
            "report_to_falconer": {
                "label": "Carry the manifest to House Falconer",
                "description": (
                    "Falconer wants to undermine the Obans. Hand the "
                    "manifest to the Falconer apparat at Lady Ella's "
                    "Solar."
                ),
                "objectives": [
                    {"type": "gather", "target": "oban supply manifest", "qty": 1,
                     "desc": "Take the Oban supply manifest (0/1)"},
                    {"type": "deliver", "target": "marta falconer", "qty": 1,
                     "desc": "Deliver the manifest to Marta Falconer (0/1)"},
                ],
                "rewards": {"silver": 40, "items": [], "reagents": {}},
                "faction_rep": {"crown": 2, "outlaws": -1},
                "npc_rep_deltas": {
                    "marta falconer": 6,
                    "korr the pardoned": -4,
                },
                "npc_memories": {
                    "marta falconer": "delivered Oban supply intel",
                    "korr the pardoned": "leaked the deal to Falconer",
                },
            },
        },
        "prereqs": [],
    },

    "hunt_the_nethermancer": {
        "key": "hunt_the_nethermancer",
        "title": "Hunt the Nethermancer",
        "giver": "magister wynn",
        "description": (
            "The nethermancer who escaped the Spring market has "
            "descended into the Annwyn Barrows and shattered the "
            "four Telyrian wards that kept the dead at rest. He "
            "now sits in the Inner Sanctum behind an Oblivion "
            "Coil — invulnerable until the wards are restored. "
            "Magister Wynn wants the nethermancer dead and the "
            "fel tome destroyed.\n\n"
            "Descend through the Barrows. Recover the four "
            "shattered ward-fragments. Reassemble them at the "
            "Altar of Seals in the Wardstone Hall to drop the "
            "Coil. Then put him down."
        ),
        "outcomes": {
            "destroy_tome": {
                "label": "Kill the nethermancer and destroy the tome",
                "description": (
                    "Put the nethermancer down and burn the tome "
                    "where it lies. Auron Calico's sacrifice is "
                    "honored. Wynn's deepest gratitude."
                ),
                "objectives": [
                    {"type": "kill", "target": "the nethermancer", "qty": 1,
                     "desc": "Kill the nethermancer (0/1)"},
                    {"type": "gather", "target": "fel tome", "qty": 1,
                     "desc": "Recover the fel tome (0/1)"},
                    {"type": "deliver", "target": "magister wynn", "qty": 1,
                     "desc": "Hand the tome to Magister Wynn for destruction (0/1)"},
                ],
                "rewards": {"silver": 80, "items": [], "reagents": {}},
                "faction_rep": {"crown": 4, "cirque": 2, "outsider": 3},
                "npc_rep_deltas": {"magister wynn": 10, "sister mariel": 3},
                "npc_memories": {
                    "magister wynn": "honored Calico's sacrifice and burned the fel tome",
                    "sister mariel": "stood against the unhallowed",
                },
            },
            "claim_tome": {
                "label": "Claim the fel tome for yourself",
                "description": (
                    "Kill the nethermancer, but keep the tome. Power "
                    "is power. Wynn will not forget the betrayal."
                ),
                "objectives": [
                    {"type": "kill", "target": "the nethermancer", "qty": 1,
                     "desc": "Kill the nethermancer (0/1)"},
                    {"type": "gather", "target": "fel tome", "qty": 1,
                     "desc": "Take the fel tome (0/1)"},
                    {"type": "explore", "target": "The Mystvale Marketplace", "qty": 1,
                     "desc": "Carry the tome back to Mystvale (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"crown": -3, "cirque": -1, "outsider": 4},
                "npc_rep_deltas": {"magister wynn": -8, "sister mariel": -5},
                "npc_memories": {
                    "magister wynn": "refused to surrender the fel tome",
                    "sister mariel": "withholds an unhallowed relic",
                },
            },
        },
        "prereqs": [],
    },

    "stop_the_plague": {
        "key": "stop_the_plague",
        "title": "Stop the Plague",
        "giver": "magister wynn",
        "description": (
            "Strange illnesses are spreading across the Annwyn — "
            "Grave Rot fever and worse. Magister Wynn at the Apotheca "
            "Chirurgery needs three fresh sample vials to brew a "
            "curative. Help — or sell the samples on the black "
            "market for short coin."
        ),
        "outcomes": {
            "deliver_to_apotheca": {
                "label": "Deliver samples to the Apotheca",
                "description": (
                    "Give Magister Wynn the samples; she'll brew the "
                    "curative. Lives saved; influence pooled toward "
                    "Decisive Moment #2."
                ),
                "objectives": [
                    {"type": "gather", "target": "plague sample vial", "qty": 3,
                     "desc": "Gather plague sample vials (0/3)"},
                    {"type": "deliver", "target": "magister wynn", "qty": 1,
                     "desc": "Deliver the samples to Magister Wynn (0/1)"},
                ],
                "rewards": {"silver": 30, "items": [], "reagents": {}},
                "faction_rep": {"crown": 2, "cirque": 1, "outsider": 3},
                "npc_rep_deltas": {"magister wynn": 6, "burgomaster domitille": 2},
                "npc_memories": {
                    "magister wynn": "delivered the plague samples",
                    "burgomaster domitille": "helped Mistvale weather the plague",
                },
            },
            "sell_blackmarket": {
                "label": "Sell the samples on the black market",
                "description": (
                    "Plague samples are valuable to the wrong sort "
                    "of buyer. Move them through Quill the Fixer; "
                    "the disease spreads further."
                ),
                "objectives": [
                    {"type": "gather", "target": "plague sample vial", "qty": 3,
                     "desc": "Gather plague sample vials (0/3)"},
                    {"type": "deliver", "target": "quill the fixer", "qty": 1,
                     "desc": "Sell the vials to Quill (0/1)"},
                ],
                "rewards": {"silver": 70, "items": [], "reagents": {}},
                "faction_rep": {"crown": -3, "outlaws": 3, "outsider": -3},
                "npc_rep_deltas": {
                    "magister wynn": -4,
                    "quill the fixer": 5,
                },
                "npc_memories": {
                    "magister wynn": "withheld plague samples for profit",
                    "quill the fixer": "delivered plague samples",
                },
            },
        },
        "prereqs": [],
    },
}
