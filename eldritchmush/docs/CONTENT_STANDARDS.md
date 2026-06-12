# EldritchMUSH Encounter Content Standards

How to turn a Reboot LARP encounter doc into a faithful in-game quest.
Derived from the 2026-06 playtest audit, which found that flat
adaptations all failed the same way: checkbox-only branching, skill
beats reduced to chat, lost dramatic turns, and weak consequence. The
engine primitives below exist specifically to close those gaps. If a
quest doesn't use the primitive its source doc calls for, it isn't
faithful yet.

The boot-time validator (`world/quest_validation.py`) enforces the
mechanical half of this document. The judgement half is on the author.

---

## 1. The fidelity checklist (apply to every quest)

1. **Preserve the dramatic turn.** If the doc has a twist — a friendly
   host who is a witch-thrall, a game that is a curse-trap, a rescue
   that can fail — the quest must contain it. A doc's set piece reduced
   to a fetch errand scores 1/5. (See Festival of Lights as the
   reference rebuild.)
2. **Branches must change play, not just checkboxes.** "Quiet vs loud"
   has to *play* differently — different objectives, different order,
   different risk — not the same steps with a different label. Use
   ordered objectives (`requires`) and distinct objective sets per
   outcome.
3. **Skill beats use skills.** "A medic can mend his leg," "Tracking 2
   finds the trail," "a Chirurgeon stabilises him" → a `skill`
   objective gated on the real skill, triggered by `treat`. Never
   collapse a skill beat into a `talk` topic.
4. **Stakes are real.** Timed rescues use a `deadline`. A failed rescue
   should cost something (a life, a memory, a reward tier) — see soft
   vs hard deadlines below.
5. **Consequence persists.** Outcomes write `faction_rep`,
   `npc_rep_deltas`, and `npc_memories` — including on the *antagonist*
   (a banished banshee remembers the hand that drove her out; that seed
   feeds the deferred binding arc). Betrayal locks doors: gate the next
   quest on the cooperative outcome (`{"quest": ..., "outcome": ...}`).
6. **The giver can talk about the quest.** Put the quest, its stakes,
   and where to go into the giver NPC's `ai_knowledge`. An LLM NPC that
   can't discuss its own errand breaks immersion.
7. **Name targets exactly.** Copy room/NPC/item keys verbatim from
   `populate_mistvale.py`; mind em-dashes and apostrophes. Keep target
   strings long enough to be unambiguous (the validator warns on short
   or multi-matching targets).
8. **Report beats are `talk`, not `deliver`.** "Report to Thelmer" =
   a `talk` objective on Thelmer. Reserve `deliver` for handing over a
   physical thing. (Players told to "report" walk up and talk; they
   don't rummage for an item.)

---

## 2. Objective types

| type      | ticks when… | target is |
|-----------|-------------|-----------|
| `kill`    | the player kills a matching NPC | NPC key |
| `gather`  | the player `get`s a matching item — OR examines a matching scene prop (a refused `get` on `get:false()` scenery still ticks: "examine the body") | item key |
| `deliver` | the player `give`s to the matching NPC | NPC key |
| `explore` | the player enters the matching room | room key |
| `duel`    | the player wins a wagered duel vs the NPC | NPC key |
| `talk`    | the player `ask`/`say`/`whisper`s the NPC (mentioning `topic` if set) | NPC key |
| `skill`   | the player `treat`s the NPC while holding `skill` ≥ 1 | NPC key |

Every objective: `{"type", "target", "qty", "desc"}` minimum. `desc`
should read as a player instruction and may name the command in `|w…|n`
(e.g. "|wtreat grigory|n (medicine)").

---

## 3. The primitives (optional objective fields)

These are what make an adaptation *faithful* instead of flat. All are
carried through `_fresh_objectives` and validated at boot.

### Ordered beats — `tag` / `requires`
Name a beat with `tag`; gate a later beat with `requires: "<tag>"`. The
gated beat won't tick until the tagged one is complete, and the player
gets a one-line "finish the earlier step first" nudge.

```python
{"type": "talk", "target": "messenger", "topic": "password",
 "tag": "password", "qty": 1, "desc": "Coax the password out (0/1)"},
{"type": "gather", "target": "idol", "requires": "password", "qty": 1,
 "desc": "With the password, lift the idol (0/1)"},
```
This is what makes a "quiet" heist genuinely require the password
before the steal, instead of a cosmetic checkbox.

### Skill beats — `skill`
A `skill` objective ticks when the player runs `treat <target>` and
holds `char.db.<skill>` ≥ 1. If they lack it, the game tells them to
find someone who has it. Pair with a non-skill alternative outcome so a
party without that skill isn't hard-locked (the doc usually frames the
skill path as the *better* path, not the only one).

```python
{"type": "skill", "target": "feargus", "skill": "medicine",
 "requires": "fed", "qty": 1,
 "desc": "Once he trusts you, tend his badly-set leg — treat feargus (0/1)"},
```

### Consuming deliver — `item`
A `deliver` with an explicit `item` and `qty > 1` makes the handoff
surrender the *whole stack* — every matching item is swept from the
player's pack to the NPC. "Return ALL the cursed coin," not one.

```python
{"type": "deliver", "target": "black sam tempest",
 "item": "cursed coin", "qty": 5,
 "desc": "Return EVERY cursed coin to Black Sam (0/5)"},
```

### Timed rescue — `deadline` / `deadline_starts_on` / `deadline_fails`
When the beat tagged `deadline_starts_on` completes, a persistent timer
arms; if this objective isn't finished in `deadline` seconds, the
quest reacts:
- `deadline_fails: "objective"` (soft) — only this beat is lost
  (Grigory dies); the larger quest can still complete. Use when there's
  more story after the rescue.
- default (hard) — the whole quest fails with `deadline_reason`.

Always warn the player in the quest description, and make the gating
skill reasonably available. The timer disarms automatically when the
beat completes or the quest ends.

```python
{"type": "skill", "target": "grigory", "skill": "medicine",
 "requires": "lights", "tag": "grigory", "qty": 1,
 "deadline": 600, "deadline_starts_on": "lights",
 "deadline_fails": "objective",
 "deadline_reason": "Grigory burned out before anyone could cut the poppet free.",
 "desc": "Save dying Grigory — treat grigory (medicine) (0/1)"},
```

---

## 4. Branching & consequence

- Branch with `outcomes: {key: {label, description, objectives,
  rewards, faction_rep, npc_rep_deltas, npc_memories}}`. The player
  picks one at accept; only that path is tracked.
- **Outcome-gated prereqs** make betrayal cost something:
  `"prereqs": [{"quest": "the_heist_pt2", "outcome": "split_with_quill"}]`
  — a player who burned Quill gets no more of Quill's jobs.
- **Faction keys** (only these): `crown`, `cirque`, `rangers`, `crows`,
  `outlaws`, `outsider`. **Reagent and prototype names** must match
  `world/reagents.py` / `world/prototypes.py` exactly (validator
  enforces).
- Write a memory on the antagonist too, when a path defeats/spares
  them — it's how deferred arcs ("she vows revenge") get their seed.

---

## 5. The build loop

1. Read the Drive doc (per `project_quest_system` memory). Identify the
   dramatic turn, the branches, the skill/timed beats.
2. Seed NPCs/items/rooms in `populate_mistvale.py` (idempotent helpers
   `get_or_create_npc` / `_ensure_walkin_npc` / `_ensure_walkin_item`).
   Investigation props that are examined-not-carried → `gettable=False`.
   Drama NPCs that talk → LLM-driven with `ai_personality` +
   `ai_knowledge` (give antagonists a "NEVER admit it" instruction).
3. Write the quest def in the right `world/quests/event*.py`, using the
   primitives the doc calls for. Copy target strings verbatim from
   populate.
4. `evennia shell` → run populate → `run_and_report()` must show **0
   errors**. Fix every error; review warnings.
5. Smoke-test the full flow through real `get`/`give`/`ask`/`treat`/
   `quest` commands (a fresh populate first — repeated runs deplete
   single-instance items).
6. Push to UAT → verify boot validator + populate → playtest →
   promote to master.

A quest is **done** when: 0 validator errors, every branch completes
through real commands, the dramatic turn is present, skill/timed beats
use their primitives, and consequence is written on all sides.
