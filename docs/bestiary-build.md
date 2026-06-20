# Bestiary Build — 9 Graphical Combat Encounters

This pass makes the **9 "ready-to-build" Eldritch Monster Manual entries**
(those with BOTH a manual statline AND dedicated art) real: spawnable NPC
prototypes wired to framed combat portraits, displayed end-to-end through
the graphical `CombatEncounterPanel`. It consolidates work that previously
lived on separate prototype branches (combat panel, antagonist portrait
pipeline, bestiary spec).

Source spec: `docs/bestiary.md`. Art catalogue: the Drive `Bestiary/`
folder. Combat-panel design: `docs/combat-encounter-graphical.md`.
Portrait pipeline notes: `docs/antagonist-portraits.md`.

---

## 1. The 9 monsters — stats, art source, art_key

Manual AV is split into `db.tough` (natural armor) + `db.av` (worn). NPC AV
= `tough + av`. The manual gives **no body/HP number** — see the HP/body
decision in §4. Skill ranks (Stagger/Cleave/Sunder/Stun/Disarm/Resist) map
1:1 to `db.<skill>`. Special-ability names are carried in `db.special` as
**data-only flags** (no MUD mechanic yet — §4).

| Monster | proto key | tier | tough / av | skills (manual) | weapon | art source (Drive Bestiary/) | art_key |
|---|---|---|---|---|---|---|---|
| Wurdulac | `WURDULAC` | 2 | 4 / 0 | Cleave 1 | IRON_MEDIUM (L1) | Werewolf.jpg `1oKVy-…` | `werewolf` |
| Werewolf (true) | `WEREWOLF` | 4 (boss) | 10 / 0 | Cleave 1, Disarm 1 | IRON_LARGE (L2) | Werewolf.jpg `1oKVy-…` (reused) | `werewolf_alpha` |
| The Risen Dead | `THE_RISEN_DEAD` | 1 | 4 / 0 | Stagger 1 | IRON_MEDIUM (L1) | **local skull.png** (subst.) | `risen_dead` |
| Dread Wight | `WIGHT` | 2 | 8 / 0 | Stagger 2, Cleave 2, Sunder 2 | IRON_LARGE (L2) | Wight.jpg `15QK5aAXETxxhe-mZP6DgdDgN65gmemea` | `wight` |
| Revenant | `REVENANT` | 3 (boss) | 12 / 0 | Stagger 3, Cleave 3, Sunder 3 | IRON_LARGE (L2) | Revenant.jpg `1giAKfgakSXmj3LuYG2DDTm6FlWQqM9Ty` | `revenant` |
| Spawn of the Unhallowed | `UNHALLOWED_SPAWN` | 2 | 6 / 2 | Stagger 2, Disarm 2 | IRON_MEDIUM (L1) | **local skull.png** (subst.) | `unhallowed_spawn` |
| Nethermancer Initiate | `NETHERMANCER_INITIATE` | 2 (boss) | 6 / 0 | Stun 3, Stagger 3, Cleave 3, Sunder 3 | IRON_LARGE (L2) | Nethermancer.jpg `1wNRNTY-MF5me3DxVq7elXbePFPVonB1c` | `nethermancer` |
| Nethermancer Acolyte | `NETHERMANCER_ACOLYTE` | 3 (boss) | 8 / 0 | Stun 4, Stagger 4, Cleave 4, Sunder 4 | IRON_LARGE (L2) | Necromancer.jpg `1ItpVIrlpwUpZQPbT-Eba6_hIhR20bbhT` | `necromancer` |
| Netherphage | `NETHERPHAGE` | 4 (boss) | 12 / 0 | — (Immune: All) | IRON_LARGE (L2) | Netherphage_.jpg `1KM2gWA48U7BxXkqXR6aUGguacK2JGRFW` | `netherphage` |

**Art provenance:** every portrait derives from the Eldritch art repo only
— the Drive `Bestiary/` JPGs (downloaded via the Google Drive MCP, raw
sources saved under `frontend/public/art/antagonists/_sources/`) or the
local committed `skull.png`. None of the Drive `Inspiration/House*` web
references were used.

### Art substitutions (honest record)

- **The Risen Dead** and **Spawn of the Unhallowed** were specced to use
  Drive `Bones_.png` (`1RQ0ns-…`). That file is 15 MB, **over the Drive MCP
  10 MB download limit**, so per the fallback rule both fall back to the
  local committed `frontend/public/art/skull.png` plate (different crops).
  Replacing them with the real `Bones_` plate later only means dropping it
  into `_sources/` and rerunning `_pipeline.py`.
- **Werewolf (true)** reuses the **Wurdulac** plate (Werewolf.jpg) — the
  manual matches both to the same art; intentional reuse, not a gap.

### Shared art (intentional reuse)

`werewolf` (Wurdulac) and `werewolf_alpha` (true Werewolf) both render from
`Werewolf.jpg`. Both Nethermancer ranks were specced to the Nethermancer
plate; we used the distinct **Nethermancer** plate for the Initiate and the
**Necromancer** plate for the Acolyte (both exist in `Bestiary/`), giving
the two ranks visually distinct portraits.

---

## 2. The render pipeline

`frontend/public/art/antagonists/_pipeline.py` (adapted from the antagonist
prototype). It reads `_sources/*.{jpg,png}` and writes framed **512×683
(3:4)** PNGs into `frontend/public/art/antagonists/`.

**Review corrections applied:**

- **Rectangular / portrait crop**, not a tight circle — the combat panel
  (`cep-frame`) frames rectangularly at 3:4, so the crop matches.
- **Lighter tint** — `TINT_STRENGTH = 0.45` blends the Mistbound tritone
  over a contrast-tweaked colour base instead of replacing it, so busy
  bestiary linework stays legible (the prior heavy tritone muddied it).
- Each output was visually checked; netherphage / revenant / both skull
  crops were retuned after the first pass to stop the face/jaw being cut.

Outputs (one per art_key): `wight-`, `revenant-`, `netherphage-`,
`nethermancer-`, `necromancer-`, `werewolf-`, `werewolf_alpha-`,
`risen_dead-`, `unhallowed_spawn-` + `-portrait.png`.

---

## 3. Data + OOB wiring

**Frontend registry** — `frontend/src/data/antagonists.js`: all 9 `art_key`
slugs → framed portrait + label + keyword fallback. `resolveAntagonist(name,
artKey)` prefers the explicit `art_key`, else keyword-matches the name.

**Combat panel** — `frontend/src/components/CombatEncounterPanel.jsx` now
resolves its portrait through that registry (`resolvePortrait` →
`resolveAntagonist`), with `skull.png` as the unknown-horror fallback. The
panel is purely presentational; its action buttons map 1:1 to existing text
commands (`strike` / `cleave` / `disarm` / `disengage`-via-Flee). The
existing `CombatEncounterModal` / `CombatTracker` text path is untouched —
this is an added graphical layer.

**NPC typeclass** — `eldritchmush/typeclasses/npc.py`: the base
`Npc.at_object_creation` now initializes `db.art_key=""`, `db.tier=0`,
`db.special=[]` (defaults keep legacy NPCs unaffected). Run the standard
migration for existing NPCs:

```
@py [n.attributes.add(k, v) for n in evennia.search_object("*", typeclass="typeclasses.npc.Npc") for k, v in (("art_key",""),("tier",0),("special",[])) if n.attributes.get(k) is None]
```

**OOB emit** — mirrors the existing `world/events.py` pattern. The encounter
packet is the already-existing `combat_encounter_prompt` event fired from
`typeclasses/characters.py:_push_combat_encounter_prompt()` when a player
enters a room with hostiles. It now carries `artKey` and `tier` per hostile
(alongside the existing `name`/`dbref`/`desc`/`isBoss`), and `isBoss` is
true when `boss_encounter` is set **or** `tier >= 3`. The frontend's
`CombatEncounterPanel` / `AntagonistPortrait` consume `artKey` to pick the
portrait.

**Prototypes** — `eldritchmush/world/bestiary_prototypes.py`: 9 ALL_CAPS
prototype dicts (`WIGHT` is the worked template from `docs/bestiary.md`).
Spawn with `@spawn WIGHT`, etc.

---

## 4. Verification

- `python3 -m py_compile world/bestiary_prototypes.py typeclasses/npc.py
  typeclasses/characters.py` → **OK**.
- Preview harness extended: `frontend/src/preview/main-preview.jsx` mounts
  the panel at `?combat=1&mob=<art_key>` (default `wight`) for all 9. Ran
  `vite` on port 5219 (main repo `node_modules` symlinked, then removed) and
  screenshotted 5 monsters with the playtest playwright. Saved under
  `docs/img/bestiary-{wight,werewolf_alpha,netherphage,risen_dead,revenant}.png`.
  Wight renders the standard blood "YOU ARE BESET" frame; werewolf_alpha /
  netherphage / revenant render the gold "BOSS ENCOUNTER" frame.

---

## 5. What remains (not in scope here)

1. **The 21 commission monsters** — Crows ×4, Crypt Ghoul, Vodnyk,
   Mortwight, the Cirque ×7, Cannibals ×4, the Corrupted Magisters ×3 — have
   no dedicated art (some have a tolerable placeholder noted in
   `docs/bestiary.md` §Gaps). They need portrait commissions before they can
   become graphical encounters.
2. **Special abilities are data-only.** `db.special` carries the manual's
   ability NAMES (regen, ranged-immunity, disease-on-hit, Mass/Target Fear,
   Paralyze, Nether Ward / Oblivion Coil, Chains of Torment, Decomposition
   ×2, No-Vitals, Undead Resilience, Immune-All, etc.) as flags. **None are
   wired into combat** — they are LARP rules with no MUD mechanic yet. Wiring
   them (regen ticks, ranged→Tough redirection, double-damage-vs-Cleave/
   Sunder, fear/paralyze status, caster wards) is a separate combat-code
   task.
3. **HP/body mapping decision.** The manual gives no body number — every
   entry is durability-by-AV (Tough + armor). We left `body/bleed/death` at
   the NPC defaults (3/3/3) and treat **`tough` as the meaningful durability
   stat**. If combat balance later wants distinct HP pools per tier, set
   `body`/`total_body` per prototype; the field is already in each dict.
4. **`db.av` from worn armor.** Prototypes set `av` numerically
   (`unhallowed_spawn` av=2) rather than equipping an armor object. If the
   combat code recomputes AV from equipped gear, give those mobs an armor
   `worn` prototype instead.
5. **Live OOB screenshot.** Verification used the vite preview harness with
   fixtures, not a running Evennia server emitting the real
   `combat_encounter_prompt`. The packet shape matches, but an end-to-end
   in-server capture (spawn `WIGHT`, walk a web-client PC in) was not run.
