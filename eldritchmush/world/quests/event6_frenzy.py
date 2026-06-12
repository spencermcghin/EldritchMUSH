"""Event 6 — The Tower: Moon Frenzy Victims (Friday Evening).

Source: Drive / Reboot / Event 6 — The Tower / Friday Night /
"Moon Frenzy Victims" (doc id 1rWuzbKsTK9-btNgw_MK-cQ0x4ltEj_TIqeMB6rl1y4E),
"We're Wolves — Moon Frenzy Victims" by Spencer McGhin.

The dramatic turn from the doc, preserved:
  Two Oban soldiers, mauled by the man-wolves of the Dranor, stagger
  into Mystvale's tavern carrying the Lycanthropic Infection — "Moon
  Frenzy". Their change is IMMINENT and there is NO known cure; the
  PCs have only minutes. The first soldier (DOUGAL) arrives begging
  for any care at all. Then QUINN drags in behind him, knifed in the
  gut by Dougal himself when the two fought on the road — and Quinn's
  first act is to name Dougal as dangerous. The scene is meant to be a
  desperate, gruesome MEDIATION, not a brawl: a medic racing the moon
  to hold two frightened, dying men together before either turns.

  If the medic reaches a victim in time, his fever breaks for the
  night and he is bound, sedated, and survives to be studied — the
  better path. If the moon rises first, that victim FRENZIES into a
  flesh-eating berserker and must be put down. Both endings let the
  errand close; what changes is whether the town keeps a living
  witness or buries a soldier it might have saved.

This quest is the full-primitive showcase called for in
docs/CONTENT_STANDARDS.md:
  - SKILL beats: a medic `treat`s each victim, gated on `medicine`.
  - TIMED deadline: a per-victim soft deadline races the moonrise;
    missing it costs that man (deadline_fails: "objective") and turns
    him loose as a frenzied enemy.
  - COMBAT teeth: the frenzied form (a separate seeded aggressive NPC,
    "frenzied moon-victim") fights back and must be killed to close
    the night.

Engine note on the frenzy "flip": the quest engine does not mutate a
passive walk-in NPC into an aggressive combatant mid-quest, and a
mandatory `kill` objective would hard-lock the party that saved BOTH
men (no frenzied form would ever spawn). So the kill is deliberately
NOT a tracked objective. The populate spec seeds a SEPARATE, already-
aggressive "frenzied moon-victim" (is_aggressive + weapon_proto) that
the Town Marshal reveals when a soft deadline fires; it attacks of its
own accord — live combat teeth — without needing a kill objective to
drive it. The soft-failed `treat` beat is what records the lost man;
the report-to-Wynn beat closes the night on either ending. See the
populate spec.

Quest dict format: see world/quests/__init__.py.
"""

QUESTS = {

    # ─────────────────────────────────────────────────────────────────────
    # Moon Frenzy Victims — timed Medicine triage racing the moonrise.
    # Giver: Magister Wynn, Mystvale's chirurgeon (a town healer who
    # sends the medic). Scene plays out in Songbird's Rest, the tavern.
    # ─────────────────────────────────────────────────────────────────────
    "moon_frenzy_victims": {
        "key": "moon_frenzy_victims",
        "title": "Moon Frenzy Victims",
        "giver": "Magister Wynn",
        "description": (
            "Two Oban soldiers have staggered out of the northern dark "
            "into Songbird's Rest, raving of 'giant man-wolves' and "
            "burning with a fever Magister Wynn has never seen. She "
            "names it the Moon Frenzy — Lycanthropy — and there is no "
            "cure she knows. Dougal arrived first, begging for any "
            "care at all; Quinn dragged in behind him, gut-knifed by "
            "Dougal's own hand on the road, and swears the man is "
            "dangerous. Both are close to turning. Get a steady "
            "Medicine hand on them and hold them through the night — "
            "BEFORE the moon rises. A man you cannot reach in time "
            "will not stay a man for long. Bring a healer, and be "
            "ready for what you cannot save."
        ),
        "objectives": [
            # The premise beat: Wynn briefs the medic and arms the
            # clock. Reaching this is what 'starts' the moonrise timers.
            {"type": "talk", "target": "Magister Wynn",
             "topic": "moon frenzy", "tag": "briefed", "qty": 1,
             "desc": "Hear Magister Wynn out on the Moon Frenzy — "
                     "|wask wynn about moon frenzy|n (0/1)"},

            # VICTIM 1 — Quinn. The knifed, bled-out soldier; weaker,
            # closer to collapse, so the doc puts him on the shorter
            # fuse. A medic can stabilise his wound AND his fever if
            # they get to him first. Soft deadline: if the moon takes
            # him, this beat is lost and Quinn frenzies.
            {"type": "skill", "target": "quinn the bled soldier",
             "skill": "medicine", "requires": "briefed", "tag": "quinn",
             "qty": 1,
             "deadline": 480, "deadline_starts_on": "briefed",
             "deadline_fails": "objective",
             "deadline_reason": (
                 "Quinn's wound and his fever ran out the same glass. "
                 "He arched off the floor, and what stood up was no "
                 "longer Quinn — put it down before it reaches the "
                 "tables."),
             "desc": "Stop Quinn's bleeding and break his fever before "
                     "moonrise — |wtreat quinn the bled soldier|n "
                     "(medicine) (0/1)"},

            # VICTIM 2 — Dougal. The aggressor who knifed Quinn; still
            # the stronger of the two, so he gets the longer fuse. The
            # doc's dramatic knot: the man begging for help is the same
            # man who stabbed his comrade. Soft deadline → frenzy.
            {"type": "skill", "target": "dougal the feverish soldier",
             "skill": "medicine", "requires": "briefed", "tag": "dougal",
             "qty": 1,
             "deadline": 600, "deadline_starts_on": "briefed",
             "deadline_fails": "objective",
             "deadline_reason": (
                 "The fever finished what the moon began. Dougal's "
                 "begging turned to a wet snarl — the soldier is gone, "
                 "and the thing wearing him is hungry."),
             "desc": "Calm Dougal and break his fever before moonrise — "
                     "|wtreat dougal the feverish soldier|n "
                     "(medicine) (0/1)"},

            # COMBAT teeth — NOT a tracked objective on purpose.
            # The engine completes a quest only when EVERY objective is
            # met, and `optional` is not a carried field — so a
            # mandatory `kill` here would hard-lock the party that saved
            # BOTH men (no frenzied form ever spawns). Instead the
            # populate seeds an already-aggressive "frenzied moon-victim"
            # that the Town Marshal reveals on the soft-fail; because it
            # is is_aggressive with a weapon_proto it attacks on its own
            # turn whether or not anyone is "tracking a kill." The teeth
            # are real; the bookkeeping just doesn't gate the report.
            # The lost man is already recorded by the soft-failed treat
            # beat above (`_failed: True`).

            # Report back. 'Report to Wynn' = a talk beat per the
            # standards (report beats are talk, not deliver).
            {"type": "talk", "target": "Magister Wynn",
             "topic": "the victims", "requires": "briefed", "qty": 1,
             "desc": "Report the night's reckoning to Magister Wynn — "
                     "|wask wynn about the victims|n (0/1)"},
        ],
        # Reward leans toward the saved path: the silver is the watch's
        # standing bounty, and the reagents are Wynn's gift to a medic
        # who keeps her patients breathing. (If the engine grows a
        # per-objective reward, scale this by lives saved; for now the
        # faction/npc memory below carries the saved-vs-slain weight.)
        "rewards": {"silver": 30, "items": [],
                    "reagents": {"Sayge": 2, "Willow Root": 1}},
        "faction_rep": {"crown": 3, "rangers": 1},
        "npc_rep_deltas": {"Magister Wynn": 4},
        "npc_memories": {
            "Magister Wynn":
                "raced the moon for two fevered Oban soldiers in my "
                "tavern — the first to bring me a living lycanthrope to "
                "study, and the first to understand the Frenzy is no "
                "ordinary plague",
        },
        "prereqs": [],
    },
}
