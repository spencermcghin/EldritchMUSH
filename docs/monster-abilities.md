# Monster Abilities — wiring `db.special` into combat

The bestiary monsters (`world/bestiary_prototypes.py`) each carry a
`db.special` list of LARP-manual ability **names** as flags. They were
data-only (see `docs/bestiary-build.md` §5.2). This pass turns the safe,
clearly-defined ones into real, **flag-gated** combat mechanics.

All logic lives in **`world/monster_abilities.py`** as small helper functions
called from the combat commands and the NPC turn hook. An NPC *without* a given
flag behaves exactly as before, and players (who never carry these flags) are
unaffected.

`world/bestiary_prototypes.py` and the React frontend were **not** touched —
flag names are read as-is.

---

## Implemented

| Flag(s) | Rule | Hook |
|---|---|---|
| `immune_ranged` | `shoot` does nothing. The arrow is **not** spent, the maneuver fizzles with a flavour line, the turn is consumed. | `commands/combat_commands/shoot.py` → `is_immune(target, "shoot")` |
| `immune_stun` | `stun` fizzles (turn consumed, no skip applied). | `combat_commands/stun.py` → `is_immune(target, "stun")` |
| `immune_stagger` | `stagger` fizzles. | `combat_commands/stagger.py` |
| `immune_disarm` | `disarm` fizzles. | `combat_commands/disarm.py` |
| `immune_sunder` | `sunder` fizzles (no gear/AV damage). | `combat_commands/sunder.py` |
| `immune_all` (Netherphage) | Every **martial control maneuver** (`stun`/`stagger`/`disarm`/`sunder`) fizzles. Raw-damage verbs (`strike`/`shoot`/`cleave`) still land and resolve **through AV** as normal — faithful to the manual note "only raw damage via AV applies". | `is_immune(target, maneuver)` returns True for the control verbs only |
| `lesser_regeneration` | +1 natural armor (`tough`, mirrored into `av`) each of the monster's own turns, capped at its starting `tough`; leftover tops `body` toward `total_body`. | `typeclasses/npc.py:Npc.take_combat_turn` → `apply_regen(self)` |
| `lycan_regeneration` | As above, **+2** per turn. | same |
| `undead_resilience` | As above, **+1** per turn. (Also flagged on several casters; same regen rule.) | same |
| `target_fear_1/2/3` | When the monster lands a `strike`/`cleave` hit, the **struck target** gains the existing `db.fear` status. | `combat_commands/strike.py`, `cleave.py` → `apply_fear(attacker, target, room)` |
| `mass_fear_1/2` | On a landed hit, **every player in the room** gains `db.fear`. | same |
| `sphere_of_terror` | Treated as a room-wide fear (strongest scope wins). | same |

**Regeneration killing-condition.** A monster already at `bleed_points == 0`
(bleeding out / down) does **not** regenerate — being knocked out of the fight
is the stop condition. The starting `tough` is cached once in
`db.regen_tough_cap` so repeated sunder-then-regen can never push a monster
above its origin durability.

**Fear recovery.** `apply_fear` reuses the same boolean `db.fear` status that
`Rally` (`commands/combat.py`) and healing (`commands/heal.py`) already clear —
no new recovery plumbing. The fear *magnitude* (1/2/3) is carried in the flag
table for future tuning but currently only sets/clears the boolean.

---

## Deferred (documented, not wired)

These need new systems or design decisions beyond the conservative scope of
this pass. Each note says what wiring them would require.

| Flag | Why deferred / what it needs |
|---|---|
| `raise_dead` | Needs a spawn-on-turn mechanic: caster spends a turn to spawn a `THE_RISEN_DEAD` into the loop. Requires loop-insertion + spawn-budget rules. |
| `summon_necrophage` | Same as `raise_dead` but summons `NETHERPHAGE` once, gated on the caster being threatened (`boss_encounter` trigger). |
| `thrall` | Netherphage only acts when its master is in combat; needs a master-link attribute and an aggro gate in `take_combat_turn`. |
| `nether_ward` | Caster damage-immunity barrier. The codebase already has a precedent — `oblivion_coil_active` in `commands/combatant.py:takeDamage` bounces all damage. Wiring `nether_ward` would set/clear a similar `db` flag plus a way for players to drop it. |
| `unhallowed_resurrection` | On death, revive after N turns unless killed by Hallowed weapon — needs a death hook + delayed-revive timer. |
| `killable_only_by_hallowed` | Only blue-coded "Hallowed" weapons deal lasting damage. The damage path already has `creature_color` weapon-colour matching in `Combatant.takeDeathDamage`; this flag would extend that to all damage stages. Needs a canonical "hallowed" weapon attribute. |
| `paralyze_1` | Hard skip-turn lock for N turns (stronger than stun). Could reuse `db.skip_turn`, but needs a duration counter and a save/break rule so it isn't an unbreakable lock. |
| `lycanthropic_infection` | Disease-on-hit: infect the player with lycanthropy. Needs the disease/`db.disease` system fleshed out (progression, cure). |
| `decomposition_x2` | Takes **double** damage from a damage type/source (manual: vs. certain attacks). Needs a damage-multiplier hook in `takeDamage` keyed to the attack type. |
| `no_vitals` / `no_dexterity` | Hit-location modifiers (no torso-kill / dex effects). Needs changes to `shotFinder` / `targetArray` weighting per monster. |
| `music_of_the_dark_forest`, `staring_into_the_void`, `chill_of_the_grave`, `fresh_meat`, `dextrous`, `dexterous` | Pure flavour / unspecified in the manual statline — no mechanic defined. Left as data. |

---

## How to test

```bash
cd eldritchmush
# Helper-level checks (immunity / regen / fear + flagless control):
../.venv/bin/evennia shell -c "exec(open('world/monster_abilities_test.py').read())"
# Command-level e2e (real WEREWOLF, real `stun` command fizzle + control):
../.venv/bin/evennia shell -c "exec(open('world/monster_abilities_e2e.py').read())"
```

Both scripts spawn throwaway NPCs (a flagged one per ability **and** a flagless
control), exercise the maneuver, assert the immunity fizzles / regen heals /
fear applies — and that the control NPC is unaffected — then delete everything
they created. Last run: **25/25** helper checks and **8/8** e2e checks passed.
