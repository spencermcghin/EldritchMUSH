# EldritchMUSH Bestiary — Encounter Spec

> Encounter-ready monster reference for EldritchMUSH. Each entry maps a Monster Manual
> entry to in-game NPC stats and to a matched piece of committed/Drive art.
>
> **Sources**
> - **Manual:** "Eldritch Monster Manual" — Google Doc `1PNBtuNMXyrjx0JEYTkFpxJAMJw9Ft2w2rJaW6u04dnk` (read in full).
> - **Art (only two permitted pools):**
>   1. Local committed art: `frontend/public/landing/`, `frontend/public/art/`, `frontend/public/art/opt/*` (chargen portraits, labels in `frontend/src/data/chargenData.js`).
>   2. Drive bestiary folder `18XUypzZIxFRQQPMvFC_1Pr7peAxEf8h4` (browsed; filenames/ids confirmed below).
>
> No AI/stock/web art is referenced. Where neither pool has a match, the entry is marked **NO ART — needs commission**.

---

## How the manual maps onto an NPC

The manual is written for a **live-action LARP** (boffer weapons, "killing blow," disease cards, marshals). It does not give body/HP numbers the way the MUD does; instead it gives an **Armor Value (AV)** broken into `Tough` + worn armor, plus a **skills** list (Stagger/Cleave/Sunder/Stun/Disarm/Resist with ranks) and **attributes** (immunities, special rules). Translating to the `typeclasses.npc.Npc` typeclass:

| Manual concept | NPC `db` field | Notes |
|---|---|---|
| "Tough - N" | `db.tough = N` | natural armor; NPC AV is `tough + av` |
| "worn/Medium/Heavy Armor - N" | `db.av = N` | from equipped armor |
| Stagger/Cleave/Sunder/Stun/Disarm/Resist rank | `db.stagger`, `db.cleave`, `db.sunder`, `db.stun`, `db.disarm`, `db.resist` | integer rank |
| Weapon (Small/Medium/Large/2H) | `db.weapon_proto` (prototype key) + `db.weapon_level` | NPC auto-equips `weapon_proto` in combat |
| Bow / pistol | `db.archer` / `db.gunner = 1` | ranged proficiency |
| Challenge Rating (Easy/Challenging/Hard) | suggested `db.tier` 0–4 + threat label below | manual CR → our tier, see each row |
| "always attacks" | `db.is_aggressive = True` | default for NPCs |
| Body / bleed / death | `db.body=3`, `db.bleed_points`, `db.death_points` | manual gives no body number; use NPC defaults unless tuned |
| Portrait (proposed) | `db.art_key` (**new field**) | slug below; frontend resolves slug→image path |
| Special abilities (regen, disease, fear, double-damage vulns) | `db.special` list / custom hooks | **not yet modeled** — needs code in a later pass |

`db.tough` and `db.av` already exist on the NPC typeclass; `db.art_key` and `db.special` are **proposed new fields** a later prototype pass should add.

**Threat label key (proposed):** `ambient` = trivial filler · `minion` = Easy/CR ≤ ½ · `elite` = Challenging/CR 1 · `boss` = Hard/CR 2+ or unique.

---

## Monster roster (one row per manual entry)

### Humans & Humanoids — the Crows / Lost (bandit faction)

| Name | Lore (1–2 lines) | Stats / mechanics (from manual) | Tier / threat | Matched art | `art_key` | Role |
|---|---|---|---|---|---|---|
| **Crow Brute** | Bandit muscle of the Crows; tattered green tabards, pagan war-paint. | Large melee. AV 4 (Tough 2 + Medium 2). Stagger 1, Sunder 1. | T1 / minion | NO ART — needs commission (Bandit "Camp/Battle" scene PNGs exist in Drive folder but are scenes, not portraits) | `crow_brute` | minion |
| **Crow Rogue** | Lightly-armored bandit skirmisher; blade or bow. | Medium melee or 2× Small, **or** Bow. AV 1 (Light 1). Stun 1 **or** Disarm 1. | T0 / minion | NO ART — needs commission | `crow_rogue` | minion |
| **Crow Footman** | Rank-and-file Crow soldier; shield-and-spear line. | 2× Medium, or Medium+Shield, or Bow. AV 3 (Tough 1 + Medium 2). Stagger 1, Disarm 1, or Bow. | T1 / minion | NO ART — needs commission | `crow_footman` | minion |
| **Crow Bandit Lord** | The "Lost Lord"; plate-clad bandit chieftain. | Large, or Medium+Shield. AV 6–8 (Tough 3 + Medium/Heavy 3–5). Resist 2; (Large) Cleave 1 + Sunder 1; (Medium) Stagger 1 + Disarm 1. | T2 / elite–boss | NO ART — needs commission | `crow_bandit_lord` | elite/boss |

### Ghosts

| Name | Lore | Stats / mechanics | Tier / threat | Matched art | `art_key` | Role |
|---|---|---|---|---|---|---|
| **Ghost** (generic) | Manual section is **makeup notes only** — no stats, no name beyond "Ghosts." | None given in manual. | — | Drive `wraith_transparent.png` (id `184gnjfQnquNaLkXDWuFsnpNb_dOV8Dj4`) is the closest spectral art, but there is **no statted ghost entry** — treat as art-with-no-entry. | `ghost` | (no buildable entry) |

### Werewolves

| Name | Lore | Stats / mechanics | Tier / threat | Matched art | `art_key` | Role |
|---|---|---|---|---|---|---|
| **Wurdulac** (lycanthrope spawn) | Diseased werewolf spawn; pack ambusher, all rage and hunger. | Boffer claws / 1H. AV 4 (Tough 4). **Immune to ranged** (bullets/arrows don't bypass armor/tough). Cleave 1. **Lesser Regeneration** (full heal after 1 min unless killing-blowed). **Lycanthropic Infection** on bleed. | T2 / elite | **Local** `frontend/public/landing/werewolf.jpg` (also Drive `Werewolf.jpg` id `1oKVy-wmA1RNpa9iGWxVLDEFyZyagPSYj`) | `werewolf` | elite |
| **Werewolf** (true Dranor) | Apex lycan; howls, rampages with brief invulnerability, regenerates. | 2× boffer claws. AV 10 (Tough 10). **Immune:** ranged, Sunder, Disarm, Stun. Cleave is its normal attack; Disarm at will. **Music of the Dark Forest** (brief invuln rampage). **Lycan Regeneration** (full heal after 30 s unless killing-blowed). | T4 / boss | **Local** `frontend/public/landing/werewolf.jpg` (or Drive `WerewolfWhiteSky.png` id `1t59q94zDCIbGGKHWvHsnHrf_lhGZtfu6`) | `werewolf_alpha` | boss |

### Ghouls

| Name | Lore | Stats / mechanics | Tier / threat | Matched art | `art_key` | Role |
|---|---|---|---|---|---|---|
| **Crypt Ghoul** | Blind, plague-ridden grave-feeder; attacks by sound, rears before striking. | CR Easy. Glowing green claws. AV 4 (Tough 4). **Immune:** Sunder, Disarm. **Pestilent** (Grave Rot Fever on hit). **No Vitals** (ranged → Tough). **Decomposition** (Cleave/Sunder = instant kill). Stagger 1, Cleave 1. | T1 / minion | NO ART — needs commission (closest is Drive `Withered_L.png` id `1qmrfb0gNBO2C4cTM8MEUZRQIZZOGKC3j`, a withered corpse — usable placeholder) | `crypt_ghoul` | minion |
| **Vodnyk** | Bigger, tougher crypt-ghoul kin; same blind sound-hunter behavior. | CR Challenging. Green claws. AV 6 (Tough 6). Same immunities/Pestilent/No-Vitals/Decomposition as Crypt Ghoul. Stagger 2, Cleave 2. | T2 / elite | NO ART — needs commission (reuse `Withered_L.png` placeholder) | `vodnyk` | elite |

### Unhallowed (Risen Dead — nethermancer's undead foot-soldiers)

| Name | Lore | Stats / mechanics | Tier / threat | Matched art | `art_key` | Role |
|---|---|---|---|---|---|---|
| **The Risen Dead** | Grunts of the undead world; rotting brutes raised by a nethermancer. | CR Easy. Claws/1H/2H, no shields/bows. AV 4 (Tough 4). **Immune:** Stun, Stagger. **No Vitals.** **Decomposition** (Bullets/Cleave/Sunder ×2 dmg). **No Dexterity** (slow). 1H→Stagger 1; 2H→Cleave or Sunder 1. | T1 / minion | **Local** `frontend/public/art/skull.png` (generic undead) **or** Drive `Bones_.png` (id `1RQ0ns-tiJTuv7frP-YfD-PE16b0ObxXe`) / `Withered_L.png` | `risen_dead` | minion |
| **Wight** (Dread Wight) | Marginally sentient, far crueler risen dead — once notable warriors, corrupted. | CR Challenging. Claws/any non-ranged ±shield. AV 8 (Tough 8). **Immune:** Stun, Stagger. **No Vitals** (bullets ×2). **Decomposition** ×2. **Dextrous** (light jog). Stagger 2; 2H→Cleave/Sunder 2. | T2 / elite | Drive `Wight.jpg` (id `15QK5aAXETxxhe-mZP6DgdDgN65gmemea`); variants `WightHG.png` (`1iyt5VH8eP5Rm7EZNfDr5xUGfuczXl9NQ`), `Wight2/Wight3` | `wight` | elite |
| **Revenant** | The most dangerous risen dead — fast, capable, relentless. | CR Hard. Claws/non-ranged ±shield. AV 12 (Tough 12). **Immune:** Stun, Stagger. **No Vitals.** **Decomposition** ×2. **Dextrous** (can run). Stagger 3; 2H→Cleave/Sunder 3. | T3 / boss | Drive `Revenant.png` (id `15SG9XIGsjNyxYTS5nBTAVECAh8ern9Vw`) / `Revenant.jpg` (`1giAKfgakSXmj3LuYG2DDTm6FlWQqM9Ty`) | `revenant` | boss |
| **Mortwight** | Plague-spreading nethermancer spawn; crowd-control horror that chains its victims. | CR Hard. 2× 1H (flail + mace). AV 12 (Tough 12). **Immune:** Stun, Disarm, Sunder. **No Vitals.** **Decomposition** ×2. **Lumbering** (walk only). **Herald of Plague** (Disease on any hit → L1 disease card). **Chains of Torment** (redistributes damage to chained thralls). **Fueled by the Essence** (disabled if 7 Deathbound fill the chain). Stagger/Cleave/Disarm/Mass Fear at will. | T3 / boss | NO ART — needs commission (reuse `wight`/`revenant` art as placeholder) | `mortwight` | boss |

### Nethermancers (boss-encounter framework)

> The Nethermancer is an **encounter template**, not a single statline: a boss caster behind an *Oblivion Coil* barrier + a *Seals of Power* puzzle, guarded by a *Netherphage*. Drop the barrier via the puzzle to make the boss vulnerable.

| Name | Lore | Stats / mechanics | Tier / threat | Matched art | `art_key` | Role |
|---|---|---|---|---|---|---|
| **Nethermancer Initiate** | Lesser dark caster; raises the dead, wards itself, sows fear. | CR 2. Claws/short weapons. AV 6 (Tough 6). **Undead Resilience** (≤5 Resists/encounter). **Staring into the Void** (Target Fear ×3). **Nether Ward** (purple barrier). May wear armor/any weapon. Stun 3, Stagger 3; 2H→Cleave 3 + Sunder 3. | T2 / boss | **Local** `frontend/public/landing/nethermancer.jpg` (also Drive `Nethermancer.png` id `1bYt1880AzNlWE1d3zcr6f8zyh7FAco4Q`) | `nethermancer` | boss |
| **Nethermancer Acolyte** | Stronger dark caster; paralyze, mass fear, summons a Necrophage. | CR Hard. Claws/non-ranged ±shield. AV 8 (Tough 8). Undead Resilience (≤5 Resists). **Sphere of Terror** (Mass Fear ×1). Nether Ward. **Necrophage** summon at will. **Chill of the Grave** (Paralyze ×1). No Vitals. Stun 4, Stagger 4, Mass Fear 1, Target Fear 3, Paralyze 1; 2H→Cleave 4 + Sunder 4. | T3 / boss | **Local** `frontend/public/landing/necromancer.jpg` (also Drive `Necromancer.png` id `18HMqGZ8bLUgOezbRi55J7FqAMeGHpTut`) | `necromancer` | boss |
| **Netherphage** | Terrifying summoned bodyguard of a nethermancer; only acts when its master is threatened. | CR Hard. 1–2 2H weapons. AV 12 (Tough 12). **Immune: All** (Undead Resilience — all damage incl. martial skills hits AV). **Thrall** (decomposes when master dies/unsummons). **Unhallowed Resurrection** (re-summonable while master lives). **Fresh Meat** (opens with Stagger/Sunder, escalates to Cleave). | T4 / boss | **Drive** `Netherphage_.png` (id `1bjvuowS5fPiHY44eCMbNSs0Spu3U3mlF`) / `Netherphage_.jpg` (`1KM2gWA48U7BxXkqXR6aUGguacK2JGRFW`) | `netherphage` | boss (guard) |
| **Spawn of the Unhallowed** | Lesser raised servant; only slain by Hallowed (blue+) weapons. | Claws/non-ranged ±shield. AV 8 (Tough 6). **Immune:** Stun, Disarm. **Undead Resilience** (ignore all martial calls, damage→Tough). Stagger 2, Disarm 2, Target Fear 2. **Affected by:** Hallowed Ward/Aegis (blue) repel; killable only by blue/red color-coded sword. | T2 / elite | Drive `Bones_.png` (id `1RQ0ns-tiJTuv7frP-YfD-PE16b0ObxXe`) or `Withered_L.png` | `unhallowed_spawn` | elite |

### The Cirque (carnival mercenaries / outlaws)

| Name | Lore | Stats / mechanics | Tier / threat | Matched art | `art_key` | Role |
|---|---|---|---|---|---|---|
| **Zanie (Menagerie Guard)** | Cirque menagerie guard. | 2× Medium + 1 Small melee. AV 6 (Tough 3 + Medium 3). Stun 2, Resist 2, Disarm 2. | T2 / elite | NO ART — needs commission (chargen `cirque` portrait `/art/opt/1kqL_JlVqK2QRuQBB690J_PXqSpQ5RBrF.jpg` is a friendly acrobat, not a guard) | `zanie` | elite |
| **Naga Escort** | Pit-fighter muscle hired to guard ringmasters. | CR Easy. 2H or 1H+Shield. AV 4 (Tough 1 + armor 3). 1H→1 of Stun/Stagger/Disarm; 2H→1 of Cleave/Sunder. | T1 / minion | NO ART — needs commission | `naga_escort` | minion |
| **Naga Bodyguard** | Veteran Cirque guard in medium/heavy armor. | CR Challenging. 2H or 1H+Shield. AV 8 (Tough 2 + armor 6). 1H→2 of Stun/Stagger/Disarm; 2H→2 of Cleave/Sunder. | T2 / elite | NO ART — needs commission | `naga_bodyguard` | elite |
| **Naga Enforcer** | Elite Cirque enforcer; best of the pits. | CR Hard. 2H or 1H+Shield. AV 12 (Tough 3 + armor 9). 1H→3 of Stun/Stagger/Disarm; 1H+Shield→Resist w/ shield; 2H→3 of Cleave/Sunder. | T3 / boss | NO ART — needs commission | `naga_enforcer` | boss |
| **Cirkee Highwayman** | Cirque road-robber. | CR Easy. 1H or 2H. AV 4 (Tough 1 + armor 3). 1H→1 of Stun/Stagger/Disarm; 2H→1 of Cleave/Sunder. | T1 / minion | NO ART — needs commission | `cirkee_highwayman` | minion |
| **Cirkee Pistolere** | Gunslinger highway robber. | CR Challenging. 1H + pistol. AV 8 (Tough 2 + armor 6). 1H→2 of Stun/Stagger/Disarm; 2H→2 of Cleave/Sunder. (`db.gunner=1`) | T2 / elite | NO ART — needs commission | `cirkee_pistolere` | elite |
| **Ironblood Recruiter** | Ironblood gang strong-arm with hammer and pistol. | CR 1. Large melee + small (hammer) + masterwork pistol. AV 6 (Tough 3 + Medium 3). Sunder 2, Resist 1, Cleave 2. (`db.gunner=1`) | T2 / elite | NO ART — needs commission | `ironblood_recruiter` | elite |

### Cannibals (wilderness raiders)

| Name | Lore | Stats / mechanics | Tier / threat | Matched art | `art_key` | Role |
|---|---|---|---|---|---|---|
| **Cannibal Hunter** | CR ½. Stalker of the wilds. | Medium+Small or Bow. AV 2 (Tough 2). Stagger 2, Disarm 2. | T0 / minion | NO ART — needs commission | `cannibal_hunter` | minion |
| **Cannibal Trapper** | CR ½. Spear-and-snare ambusher. | Spear + Small. AV 2 (Tough 2). Stun 2, Cleave 2, Armor Specialist. | T0 / minion | NO ART — needs commission | `cannibal_trapper` | minion |
| **Cannibal Pit Boss** | CR 1. Cannibal warband leader. | Any weapon. AV 6 (Tough 3 + Medium 3). Sunder 2, Resist 2, Cleave 2, Stagger 2. | T2 / elite | NO ART — needs commission | `cannibal_pit_boss` | elite |
| **Cannibal Hit Man** | CR 1. Cannibal assassin. | Any weapon. AV 6 (Tough 3 + Medium 3). Resist 2, Stun 2, Cleave 2. | T2 / elite | NO ART — needs commission | `cannibal_hit_man` | elite |

### Corrupted Magisters (Plaguist line — disease casters)

| Name | Lore | Stats / mechanics | Tier / threat | Matched art | `art_key` | Role |
|---|---|---|---|---|---|---|
| **Plaguist** | CR ½. Corrupted magister; poisoner whose very blood is toxic. | 2× small melee + throwing knives. AV 3 (Tough 3). Resist 1, Stun 1, Stagger 1. **Pestilent** (knives → random L1 disease). **Cloud of Infection** (on non-coded killing blow → L1 disease to killer). Loot: 3 common reagents. | T1 / minion | NO ART — needs commission (closest is Drive `Witch.jpg` id `19ZYsy_1rna83NUKDh4Vbp_LZxnAwJ_6e` / `hag_transparent.png` — usable placeholder for a corrupted caster) | `plaguist` | minion |
| **Pandemist** | CR 1. Stronger corrupted magister. | 2× small + throwing knives. AV 5 (Tough 5). Resist 2, Stun 2, Stagger 2. Pestilent/Cloud → L2 disease. Loot: 3 uncommon reagents. | T2 / elite | NO ART — needs commission (reuse `Witch.jpg` placeholder) | `pandemist` | elite |
| **Pestis** | CR 2. Apex corrupted magister / disease boss. | 2× small + throwing knives. AV 9 (Tough 9). Resist 3, Stun 3, Stagger 3, Cleave 3. Pestilent/Cloud → L3 disease. Loot: 3 rare reagents. | T3 / boss | NO ART — needs commission (reuse `Witch.jpg`/`witch_large.jpg` placeholder) | `pestis` | boss |

---

## Manual count

**26 statted monster entries** across 7 families (Crows ×4, Wurdulac/Werewolf ×2, Ghouls ×2, Unhallowed ×4, Nethermancers ×4 incl. Spawn of the Unhallowed, Cirque ×7 incl. Zanie/Ironblood, Cannibals ×4, Corrupted Magisters ×3). Plus a stat-less **"Ghosts"** section (makeup notes only — not counted as a buildable monster).

---

## ✅ Ready to build (manual stats **AND** dedicated art)

These have both a full statline and a real matched portrait — they can become NPC prototypes + graphical encounters immediately:

| Monster | Art | `art_key` |
|---|---|---|
| **Werewolf (true)** | `frontend/public/landing/werewolf.jpg` (+ Drive variants) | `werewolf_alpha` |
| **Wurdulac** | `frontend/public/landing/werewolf.jpg` | `werewolf` |
| **Wight** | Drive `Wight.jpg` `15QK5aAXETxxhe-mZP6DgdDgN65gmemea` | `wight` |
| **Revenant** | Drive `Revenant.png` `15SG9XIGsjNyxYTS5nBTAVECAh8ern9Vw` | `revenant` |
| **Nethermancer Initiate** | `frontend/public/landing/nethermancer.jpg` | `nethermancer` |
| **Nethermancer Acolyte** | `frontend/public/landing/necromancer.jpg` | `necromancer` |
| **Netherphage** | Drive `Netherphage_.png` `1bjvuowS5fPiHY44eCMbNSs0Spu3U3mlF` | `netherphage` |
| **The Risen Dead** | `frontend/public/art/skull.png` / Drive `Bones_.png` `1RQ0ns-tiJTuv7frP-YfD-PE16b0ObxXe` | `risen_dead` |
| **Spawn of the Unhallowed** | Drive `Bones_.png` `1RQ0ns-tiJTuv7frP-YfD-PE16b0ObxXe` | `unhallowed_spawn` |

**9 ready-to-build.** (Crypt Ghoul, Vodnyk, Mortwight, Plaguist line all have a *usable placeholder* — `Withered_L.png` / `Witch.jpg` — but no dedicated art; listed under gaps.)

---

## Gaps

### A. Manual monsters with NO dedicated art (need commission)

Crow Brute, Crow Rogue, Crow Footman, Crow Bandit Lord (Lost Lord); Crypt Ghoul, Vodnyk; Mortwight; Zanie, Naga Escort/Bodyguard/Enforcer, Cirkee Highwayman/Pistolere, Ironblood Recruiter; Cannibal Hunter/Trapper/Pit Boss/Hit Man; Plaguist, Pandemist, Pestis.

**= 21 of 26 monsters need portrait commissions** (some have a tolerable placeholder noted in their row).

Suggested placeholders pending commission:
- Crypt Ghoul / Vodnyk → Drive `Withered_L.png` (`1qmrfb0gNBO2C4cTM8MEUZRQIZZOGKC3j`)
- Plaguist / Pandemist / Pestis → Drive `Witch.jpg` (`19ZYsy_1rna83NUKDh4Vbp_LZxnAwJ_6e`) or `witch_large.jpg` (`10uyV2uwDK414Jubf83vRPp671qfCaO_e`)
- Mortwight → reuse `wight`/`revenant` art

### B. Art with NO manual entry (commissioned/available but unstatted)

These exist in the two art pools but have **no statline** in the manual — either future content or named-NPC art:
- **Witch / Hag** — Drive `Witch.jpg`, `Witch.png`, `witch_large.jpg`, `hag_transparent.png`, `hag_floatingpage.png`, `hag_large.jpg`. (Manual has corrupted magisters but no "witch/hag" creature.)
- **Wraith** — Drive `wraith_transparent.png` (`184gnjfQnquNaLkXDWuFsnpNb_dOV8Dj4`), `wraith_large.jpg`. (Closest manual analog is the stat-less "Ghosts" section.)
- **Withered** — Drive `Withered_L.png/.jpg`. (No "Withered" entry; fits ghoul/risen-dead reskins.)
- **Bones ×4** — Drive `Bones_.png`, `Bones_2.png`, `Bones_4.png`, `Bones_darker.png`. (Generic skeletal — fits Risen Dead / Spawn reskins, no dedicated "skeleton" entry.)
- **Fae** — `frontend/public/landing/fae.jpg` + Drive `Fae.jpg/.png`. (No fae monster in the manual.)
- **Clovis** — `frontend/public/landing/clovis.jpg` + Drive `Clovis_.png/.jpg`. Named NPC, not in manual.
- **Grace Bannon** — Drive `Grace_Bannon_.png/.jpg`. Named NPC, not in manual.
- **Mists** — `frontend/public/landing/mists.jpg`. Environment art, not a creature.
- **Encounter scenes** — `frontend/public/art/map/encounter1-3.png`, faction `threat*/threatchampion*` map tokens, Bandit Camp/Battle scenes in Drive. Useful as **encounter backdrops**, not portraits.

---

## Next-pass note: turning a row into a prototype

A later pass can register these as `Npc` prototypes (or build them with the in-game `createnpc`/`editnpc` admin commands). Proposed per-monster `db` payload, using **Wight** as a worked example:

```python
WIGHT = {
    "key": "dread wight",
    "typeclass": "typeclasses.npc.Npc",
    "desc": "A corrupted warrior-corpse, swift and cruel, raised by a nethermancer.",
    # --- AV split (manual: AV 8 = Tough 8) ---
    "tough": 8,            # natural armor
    "av": 0,              # worn armor
    # --- survival (manual gives no body; use NPC defaults or tune) ---
    "body": 3, "bleed_points": 3, "death_points": 3,
    # --- skills (manual ranks) ---
    "stagger": 2, "cleave": 2, "sunder": 2,
    "stun": 0, "disarm": 0, "resist": 0,
    # --- weapon ---
    "weapon_proto": "IRON_LARGE_WEAPON",   # 2H option; set weapon_level to match
    "weapon_level": 2,
    # --- behavior ---
    "is_aggressive": True,
    # --- NEW fields (add to Npc typeclass first) ---
    "art_key": "wight",
    "tier": 2,
    "special": ["immune_stun", "immune_stagger", "no_vitals", "decomposition_x2", "dextrous"],
}
```

**Caveats for the prototype pass:**
1. `tier` and `art_key` and `special` are **not yet on the `Npc` typeclass** — add them to `typeclasses/npc.py:at_object_creation` (default `art_key=""`, `tier=0`, `special=[]`) and run the standard `@py` migration for existing NPCs.
2. The manual's **special attributes** (regeneration, disease-on-hit, ranged immunity, double-damage-vs-Cleave/Sunder, Mass/Target Fear, Paralyze, Nether Ward / Oblivion Coil, Chains of Torment) are **LARP rules with no MUD implementation yet** — the `special` list is a tag placeholder; wiring them is a separate combat-code task.
3. Manual gives **no `body` value** — every entry uses AV (Tough+armor) as its durability. For MUD balance, treat `tough` as the meaningful durability stat and leave `body/bleed/death` at NPC defaults unless tuning.
4. Pick `weapon_proto` from `world/prototypes.py` to match the manual's weapon size (Small/Medium/Large/2H) and set `weapon_level` accordingly.
