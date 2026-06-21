# Bestiary Expansion — Reconciliation Pass

> Expands the graphical bestiary from **9** to **15** monsters by reconciling
> the Eldritch Monster Manual statlines against **named Drive Bestiary art**
> that exists under name-mismatched filenames. No new commissions: every new
> portrait derives from a dedicated `Bestiary/` illustration already in the
> Eldritch art repository.
>
> **Note on the count:** the manual has **30** statted entries (Crows 4 +
> Lycanthropes 2 + Ghouls 2 + Unhallowed 4 + Nethermancers 4 + Cirque 7 +
> Cannibals 4 + Corrupted Magisters 3 — `docs/bestiary.md` headlines "26" but
> its own family breakdown sums to 30). 9 were built before this pass, 6 are
> built here, leaving **15** still-uncommissioned.

## Method — why these 6 became coverable

The earlier pass marked 21 of 26 manual monsters "needs commission." It matched
on filenames. This pass matched on **creature concept**, after exporting the
Monster Manual Google Doc (`1PNBtuNMXyrjx0JEYTkFpxJAMJw9Ft2w2rJaW6u04dnk`).

Key finding from the doc export: the manual's *embedded images* for the
art-less families (Crows, Cannibals, Cirque/Nagas, Ironblood) are **costuming
and makeup reference photos**, not creature portraits — so they give no
portrait art. The new coverage instead comes from Bestiary plates whose
**filenames don't match the manual's monster names** but whose subjects are
unmistakably the same creatures:

| Manual monster | Bestiary plate (subject) | Why it matches |
|---|---|---|
| Crypt Ghoul | `Withered_L.jpg` — gaunt, weeping-eyed hooded corpse | The manual itself names Withered as the closest art; it is a dedicated Bestiary illustration of exactly this blind plague-corpse. |
| Vodnyk | `Withered_L.jpg` (distinct, tighter crop) | Bigger crypt-ghoul kin — same creature, rendered as a more menacing bust. |
| Mortwight | `WightHG.png` — snarling lean warrior-corpse mid-swing, glowing blade | A distinct Wight-variant plate (own composition), giving the plague-wight its own portrait instead of reusing the base wight. |
| Plaguist | `Witch.jpg` — gas-masked leaping poisoner | A dedicated Bestiary "corrupted caster" — the gas mask reads as the disease-poisoner Corrupted Magister. |
| Pandemist | `Witch.jpg` (distinct crop, heavier blood tint) | Mid-tier of the same Plaguist line — same poisoner concept, distinct framing. |
| Pestis | `witch_large.jpg` — skull-faced hag mid-cast | A second, separate Witch plate; its dramatic skull-faced read suits the apex disease boss. |

## New monsters (stats from docs/bestiary.md / the manual)

| Prototype | key | tough/av | tier | art_key | Manual skills |
|---|---|---|---|---|---|
| `CRYPT_GHOUL` | crypt ghoul | 4 / 0 | 1 | `crypt_ghoul` | Stagger 1, Cleave 1 |
| `VODNYK` | vodnyk | 6 / 0 | 2 | `vodnyk` | Stagger 2, Cleave 2 |
| `MORTWIGHT` | mortwight | 12 / 0 | 3 | `mortwight` | Stagger/Cleave/Disarm/Mass Fear at will |
| `PLAGUIST` | plaguist | 3 / 0 | 1 | `plaguist` | Resist 1, Stun 1, Stagger 1 |
| `PANDEMIST` | pandemist | 5 / 0 | 2 | `pandemist` | Resist 2, Stun 2, Stagger 2 |
| `PESTIS` | pestis | 9 / 0 | 3 | `pestis` | Resist 3, Stun 3, Stagger 3, Cleave 3 |

Stat mapping follows the existing convention (Tough = natural armor, AV =
Tough + worn armor; manual gives no body number so body/bleed/death stay at
NPC defaults 3/3/3). The manual's special abilities (Pestilent, No Vitals,
Decomposition, Chains of Torment, Cloud of Infection, etc.) are carried as
`db.special` tag strings — data only, same as the original 9; wiring them is a
separate combat-code task.

Spawn in-game: `@spawn CRYPT_GHOUL`, `@spawn PESTIS`, etc. All 15 keys are in
`BESTIARY_KEYS`.

## Provenance table (every pixel from the Eldritch repository)

All sources are from the Drive **Bestiary** folder
(`18XUypzZIxFRQQPMvFC_1Pr7peAxEf8h4`) or local committed art — never the
`Inspiration/House*` web-reference folders, never AI/stock.

| art_key | source file | Drive file id | parent folder | size |
|---|---|---|---|---|
| `crypt_ghoul` | Withered_L.jpg → `_sources/withered.jpg` | `15lGjceRRpQt-DECgawjeYLNpUz9qQ3gv` | Bestiary | 4.6 MB |
| `vodnyk` | Withered_L.jpg → `_sources/withered.jpg` | `15lGjceRRpQt-DECgawjeYLNpUz9qQ3gv` | Bestiary | 4.6 MB |
| `mortwight` | WightHG.png → `_sources/wight_hg.png` | `1iyt5VH8eP5Rm7EZNfDr5xUGfuczXl9NQ` | Bestiary | 2.6 MB |
| `plaguist` | Witch.jpg → `_sources/witch.jpg` | `19ZYsy_1rna83NUKDh4Vbp_LZxnAwJ_6e` | Bestiary | 3.0 MB |
| `pandemist` | Witch.jpg → `_sources/witch.jpg` | `19ZYsy_1rna83NUKDh4Vbp_LZxnAwJ_6e` | Bestiary | 3.0 MB |
| `pestis` | witch_large.jpg → `_sources/witch_large.jpg` | `10uyV2uwDK414Jubf83vRPp671qfCaO_e` | Bestiary | 5.1 MB |

All four downloaded plates were under the ~10 MB Drive MCP download cap.

Rendered portraits (Pillow pipeline, `frontend/tools/antagonist-pipeline/_pipeline.py`):
`frontend/public/art/antagonists/{crypt_ghoul,vodnyk,mortwight,plaguist,pandemist,pestis}-portrait.png`.

## Sources that exceeded the download cap

None of the six plates used here exceeded the cap. The high-res PNG masters of
some Bestiary creatures (e.g. `Bones_.png` ~15 MB, `Withered_L.png` 22.8 MB,
`Netherphage_.png` 16.3 MB) remain over the ~10 MB MCP limit — but the
**flattened JPG / smaller PNG variants** used here were well under it, so no
monster in this pass is blocked on the cap.

## Now-shrunken commission gap — monsters STILL with no art anywhere

After this pass, **15 of 30** statted manual monsters have portraits. The
remaining **15** have *no* creature art in either permitted pool
(Bestiary/Creatures or local committed art). Their only "matches" are
costuming/makeup reference
photos in the manual, wide scene backdrops (Bandit Battle/Camp), or friendly
archetype portraits — none of which is a single-figure antagonist portrait.
These are the true commission gaps:

**Crows / Lost (bandit faction) — 4**
- Crow Brute
- Crow Rogue
- Crow Footman
- Crow Bandit Lord (Lost Lord)

**The Cirque (carnival mercenaries) — 7**
- Zanie (Menagerie Guard)
- Naga Escort
- Naga Bodyguard
- Naga Enforcer
- Cirkee Highwayman
- Cirkee Pistolere
- Ironblood Recruiter

**Cannibals (wilderness raiders) — 4**
- Cannibal Hunter
- Cannibal Trapper
- Cannibal Pit Boss
- Cannibal Hit Man

The 4 + 7 + 4 = **15** lines above are all human/humanoid bandit / mercenary /
raider factions — none has a single-figure creature portrait anywhere in the
repo. (The stat-less "Ghosts" makeup section remains a non-buildable entry:
Wraith art exists, but the manual gives it no statline.)

Gap shrank from **21 → 15** un-portraited statted monsters (the 6 built here),
i.e. **15 of 30** manual monsters are now graphical, up from 9.
