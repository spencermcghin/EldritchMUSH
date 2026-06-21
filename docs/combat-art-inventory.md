# Combat & Antagonist Art Inventory

> Canonical inventory of Eldritch-repository art usable to make antagonists and combat
> encounters more graphical, in an old-school graphical-MUD / dungeon-crawler spirit
> (framed monster portraits you face in a room).
>
> **Provenance constraint (HARD):** every asset below traces to one of two sources only —
> (1) local committed art under `frontend/public/art/**` and `frontend/public/landing/**`,
> or (2) the project's Google Drive art repository. No AI art, no stock, no web images.
> See the Provenance Note at the bottom for the exact Drive folders searched.

---

## A. Usable Asset Table

Tags: `antagonist` = villain/monster portrait · `creature` = beast/undead · `backdrop` =
encounter scene/room · `frame` = border/wax-stamp/skull dressing · `emblem` = faction
banner/heraldry · `atmosphere` = mood/setting · `token` = map combat icon.

### Local — `frontend/public/landing/`

| Name | Path | Dimensions / Format | Use tag |
|------|------|---------------------|---------|
| Necromancer | `frontend/public/landing/necromancer.jpg` | 654×900 JPG | antagonist |
| Nethermancer | `frontend/public/landing/nethermancer.jpg` | 605×1100 JPG | antagonist |
| Werewolf | `frontend/public/landing/werewolf.jpg` | 689×900 JPG | creature |
| Fae | `frontend/public/landing/fae.jpg` | 616×900 JPG | creature / antagonist |
| Clovis (named NPC) | `frontend/public/landing/clovis.jpg` | 736×900 JPG | antagonist (boss/NPC) |
| Mists | `frontend/public/landing/mists.jpg` | 1400×906 JPG | backdrop / atmosphere |
| Annwyn map | `frontend/public/landing/annwyn-map.jpg` | 1088×1100 JPG | atmosphere / backdrop |
| Wax seal | `frontend/public/landing/wax-seal.png` | 240×284 PNG | frame |
| Banner — Aragon | `frontend/public/landing/banner-aragon.png` | 362×600 PNG | emblem |
| Banner — Bannon | `frontend/public/landing/banner-bannon.png` | 362×600 PNG | emblem |
| Banner — Blayne | `frontend/public/landing/banner-blayne.png` | 362×600 PNG | emblem |
| Banner — Corveaux | `frontend/public/landing/banner-corveaux.png` | 362×600 PNG | emblem |
| Banner — Hale | `frontend/public/landing/banner-hale.png` | 362×600 PNG | emblem |
| Banner — Innis | `frontend/public/landing/banner-innis.png` | 362×600 PNG | emblem |
| Banner — Richter | `frontend/public/landing/banner-richter.png` | 362×600 PNG | emblem |
| Banner — Rourke | `frontend/public/landing/banner-rourke.png` | 362×600 PNG | emblem |

### Local — `frontend/public/art/`

| Name | Path | Dimensions / Format | Use tag |
|------|------|---------------------|---------|
| Skull (high-res) | `frontend/public/art/skull.png` | 3189×4320 PNG | frame / atmosphere |
| Eldritch icon ("E") | `frontend/public/art/eldritch-icon.png` | 161×256 PNG | frame |
| Eldritch logo | `frontend/public/art/eldritch-logo.png` | 1024×281 PNG | frame |
| Encounter backdrop 1 | `frontend/public/art/map/encounter1.png` | 256×256 PNG | backdrop |
| Encounter backdrop 2 | `frontend/public/art/map/encounter2.png` | 256×256 PNG | backdrop |
| Encounter backdrop 3 | `frontend/public/art/map/encounter3.png` | 256×256 PNG | backdrop |
| Ruin tile | `frontend/public/art/map/ruin.png` | 256×115 PNG | backdrop / atmosphere |
| Castle tiles 1–3 | `frontend/public/art/map/castle{1,2,3}.png` | 256×256 PNG | backdrop |
| Threat tokens 1–4 | `frontend/public/art/map/threat{1..4}.png` | 256×256 PNG | token (enemy marker) |
| Threat-champion tokens 1–4 | `frontend/public/art/map/threatchampion{1..4}.png` | 256×256 PNG | token (elite/boss marker) |
| Faction flags (8 houses) | `frontend/public/art/map/flag_*.png` | small PNG | emblem (map token) |
| Faction unit tokens | `frontend/public/art/map/{knight,ranger,scout,troop,stake}_*.png` | small PNG | token / atmosphere |

> The 44 `frontend/public/art/opt/*.jpg` files (≈170–400 px, all ≤400 px tall) are **archetype
> portraits** used by the chargen wizard (`frontend/src/data/chargenData.js` maps each ID to a
> subject). Most read as townsfolk/professions, but several double as antagonist types — see the
> shortlist. They are Drive-derived, optimized copies and are legitimately in-repo.

### Drive — creature / bestiary folder (`18XUypzZIxFRQQPMvFC_1Pr7peAxEf8h4`)

High-res monster/villain art. Most exist as both PNG (transparent, larger) and JPG (flattened).

| Name | Drive file id | Format / size | Use tag |
|------|---------------|---------------|---------|
| Necromancer | `1ItpVIrlpwUpZQPbT-Eba6_hIhR20bbhT` (jpg) / `18HMqGZ8bLUgOezbRi55J7FqAMeGHpTut` (png) | JPG 4.9 MB / PNG 9.7 MB | antagonist |
| Nethermancer | `1wNRNTY-MF5me3DxVq7elXbePFPVonB1c` (jpg) / `1bYt1880AzNlWE1d3zcr6f8zyh7FAco4Q` (png) | JPG 4.8 MB / PNG 19.8 MB | antagonist |
| Netherphage | `1KM2gWA48U7BxXkqXR6aUGguacK2JGRFW` (jpg) / `1bjvuowS5fPiHY44eCMbNSs0Spu3U3mlF` (png) | JPG 1.4 MB / PNG 16.3 MB | creature / antagonist |
| Withered (L) | `15lGjceRRpQt-DECgawjeYLNpUz9qQ3gv` (jpg) / `1qmrfb0gNBO2C4cTM8MEUZRQIZZOGKC3j` (png) | JPG 4.6 MB / PNG 22.8 MB | creature (undead) |
| Wight | `15QK5aAXETxxhe-mZP6DgdDgN65gmemea` (jpg) / `1iyt5VH8eP5Rm7EZNfDr5xUGfuczXl9NQ` (png) | JPG 3.2 MB / PNG | creature (undead) |
| Wight 2 | `1Xzu-9EeNW5MDq7VIFJvzNDgqiFwVxU5k` (jpg) / `1Eogsmptin-ypQ-7OKg21FeOYCCNws1C6` (png) | JPG / PNG | creature (undead) |
| Wight 3 | `1IEqJhVSc2gTWiDb1Gz8YXMVJTx_PTslg` (jpg) / `1qfM3rG9JQPe7zP3cXBahlxleJX0HcGiw` (png) | JPG / PNG | creature (undead) |
| Wight (HG variant) | `1iyt5VH8eP5Rm7EZNfDr5xUGfuczXl9NQ` | PNG 2.6 MB | creature (undead) |
| Revenant | `1giAKfgakSXmj3LuYG2DDTm6FlWQqM9Ty` (jpg) / `15SG9XIGsjNyxYTS5nBTAVECAh8ern9Vw` (png) | JPG 4.3 MB / PNG 4.3 MB | creature (undead) |
| Wraith (large) | `1tyo2fi6cGMIZnXgXjb91My8mzvkiWrjY` (jpg) / `184gnjfQnquNaLkXDWuFsnpNb_dOV8Dj4` (png, transparent) | JPG 4.5 MB / PNG 5.4 MB | creature (undead) |
| Werewolf (large) | `1n4AAf5DkpPNfugTd3gyj7oAzbVzLtIKU` (jpg) / `1KA7m1dUFhBOFJMQoq91Mcxo_S9uA2PBu` (png) | JPG 9.2 MB / PNG 7.6 MB | creature |
| Witch (large) | `10uyV2uwDK414Jubf83vRPp671qfCaO_e` (jpg) / `1vC5L9AadUWGTCoqGD9xcl0BS4S3P98Wq` (png) | JPG 5.1 MB / PNG 4.2 MB | antagonist |
| Witch (alt) | `19ZYsy_1rna83NUKDh4Vbp_LZxnAwJ_6e` | JPG 3.0 MB | antagonist |
| Fae | `1x03dYyRgm3FsSx5L2aogcoECXc5Lz2Pw` (jpg) / `1kExcCnb3N2LelTfUowyUMwkVKkKEc7dR` (png) | JPG 5.8 MB / PNG 7.6 MB | creature / antagonist |
| Bones (skeleton) ×4 | `1RQ0ns-tiJTuv7frP-YfD-PE16b0ObxXe`, `1jKBTb4Be_bZVGu2SyXL4h9eZAYYjd67C`, `12zh972QGqp3k4K_RHqv9pS7OzGJ-icTR`, `1X5Mue1BYRnU8rJTq541K0KVdhfcs0lqd` (darker) | PNG ~15–17 MB each | creature (undead) |
| Clovis (named NPC) | `1mYdR_MPa9cVOH49wWOOuJGQEkQ94XpKJ` (jpg) / `1QyaGqokGMOSMvIy7vczjYoy8bGEKqZZY` (png) | JPG 1.6 MB / PNG 5.7 MB | antagonist (boss/NPC) |
| Grace Bannon (named NPC) | `1m1xSTlAb93RtJg432fZvcZMhopbxuKNS` (jpg) / `127Z-tDqYDOuhw69S4GnY3AFGC7ixLchh` (png) | JPG 1.3 MB / PNG 19.6 MB | antagonist (NPC) |

### Drive — Skull Witch set (`1a0td_mpBfDNShielqINEO3-rBJzog6Fs`)

| Name | Drive file id | Format / size | Use tag |
|------|---------------|---------------|---------|
| Skull Witch | `1L126HfNG4_Qreiafigy1GEG4_EZHbdqd` | JPG 1.6 MB | antagonist |
| Skull Witch 2 | `1VzFHpSOZ82x2DStVtQHcS0hOt-8ZVg1d` | JPG 1.5 MB | antagonist |
| Skull Witch 3 | `1Nr-Pvp1FBwE0A0Lq4nG2Grtk3WwJaVPx` | JPG 1.1 MB | antagonist |
| Skull Witch 2 (alt) | `1LdZLwWAR6jhdMSbfaxfmTSnPCkhlMMvp` | JPG 1.8 MB | antagonist |

### Drive — encounter scene art (bandit / fae feast)

| Name | Drive file id | Format / size | Use tag |
|------|---------------|---------------|---------|
| Bandit Battle | `1f9VZ3GjCKpZB77NvtpkExkUpk1SzvmIe` | JPG 18 MB | backdrop (bandit combat) |
| Bandit Battle-2 | `1NB0DRCyP46mx2KiXvWzNN7FJoidirz8w` | JPG 15.6 MB | backdrop |
| Bandit Battle-3 | `1aUGHXYVS5hpdsFOt2oF2wFUeVBPi2JUJ` | JPG 14.5 MB | backdrop |
| Bandit Battle-4 | `1_8RYBiXIdzRGEsOI8uoAyFu7tpDFglh4` | JPG 12.6 MB | backdrop |
| Bandit Battle-5 | `1bKlkWbc5S9TzOGehXstuBfEx4sfETV3l` | JPG 11.7 MB | backdrop |
| Bandit Camp | `1XVdk9yT14vh5syI_LmGGJawuFkK8Jhj3` | JPG 2.0 MB | backdrop |
| Bandit Camp-2 | `1luzDexElDOK7BCIMp_sYTgKZLiXs4myY` | JPG 11.2 MB | backdrop |
| Bandit waiting | `1rY_jflQg_30aJOuPFAEemSKJW8BKjVGq` | JPG 1.8 MB | backdrop / atmosphere |
| Bandit Escape | `1u1fZfUlsaG6NXeFyXwsnTcpbojbjkUkU` | JPG 1.3 MB | backdrop |
| Bandit Negotiations (×3) | `1YdUdbohJNkFtJKMZE6pJu68LVsrQNmgH`, `1Qo-Bg20Rr5GtjNAGwVA-XlW_zEUZlhP_`, `134dbeSHlH2mSpYRZF1kB960ZKCXT2cev` | JPG | atmosphere (parley) |
| The Fae Feast (15 stills, -10 … -19) | folder `1BwBSrO_dvP_qPzYD_XoUWUYiMrHXcDXR` (e.g. `1JtRnyKAQvrmces4h7liu1sTZMVk_0bP2`) | JPG 18–29 MB | backdrop (fae encounter) |
| Holly Schoales scene set 1–7 + extras | folder `1Xs2J2UxYFWQwKhzukGOAid5R9FaPpp-4` (e.g. Plague `1FzfzUTU5lXSFb7ifX-kMKkWJ1XKGKp1G`, Final Act `1zprZrqYJ4JXQvJGo6QHbOBzXQNj53Mat`) | PNG 3.4–6.4 MB | backdrop / atmosphere |

### Drive — frames, borders, skulls, beast heads

| Name | Drive file id | Format / size | Use tag |
|------|---------------|---------------|---------|
| Skull (clean PNG; matches local skull.png) | `1RwrXcr9nlIbpbKN46xekGEZVs99VhEmu` | PNG 592 KB | frame |
| Skull (master JPG) | `1-aNvJXkp2rLSE96C7KInUY8_rWQ9zpTc` | JPG 1.5 MB | frame |
| Woodcut border (set of 6) | `1b_e7BW8ktExtRfAxF39rWya40bzYHEej`, `1qxe86WZe0UMgeZNIPjkJQI0MKzAvHcBJ`, `1PBTQEOk6C01bQPrzGpyb-5pxSX19y0qF`, `1c0Qujfn7jXIAgTZIwlqRyyW2QtGBD3nA`, `1t17D9RIMePpPZNiIhAeIPm-TUCrZkTvv`, `1MXibWTfyO_uetVIVYpphuaFcsoH9fnoD` | JPG 80 KB–1.4 MB | frame |
| Rats border | `1DWriao6vJBOmPCFy6dTzfykQ61939fZJ` | PNG 423 KB | frame |
| Arnesse map borders | `1Z7fmISB9QsNv3uwd5_ZrlKmsatXsdhEg` | JPG 42 MB | frame / atmosphere |
| head_beast_fox | `1GQjRZ8kPF5KmqSl5gDtiEgG35WuRj_GL` | JPEG 161 KB | creature (beast head) |
| Fayne head (no hood / mask) | `1M2thQOib23ETbOC2kTUT9bjCTGFkEtbJ`, `1WCJjAlkUIppnbtSCLHXJHYqzlRQ7ab8r` | PNG ~2 MB | antagonist (masked NPC) |
| Crow silhouettes (×2) | `1Yz0lk4EGyOXiZ4JYbgW0d9XBw3RZ6kGY`, `1llb3d1E59mR5XzJW57hH1wPW7_h_evqG` | PNG ~45–52 KB | atmosphere (Crows faction motif — stock silhouette, low fidelity) |

> The crow silhouettes are generic stock-style cutouts that happen to live in the Drive repo;
> usable for a faction motif but not a true portrait. Flagged, not recommended for a featured frame.

---

## B. Antagonist-Portrait / Creature Shortlist (best 8–15)

Ranked for "framed monster you face in a room." All are tall-ish single-subject pieces that
crop cleanly to a portrait box. Prefer the **PNG** (transparent) variant where one exists so the
subject can sit inside a parchment/skull frame; otherwise the JPG.

1. **Necromancer** — `frontend/public/landing/necromancer.jpg` (local, 654×900) or Drive `1ItpVIrlpwUpZQPbT-Eba6_hIhR20bbhT`. Iconic spellcaster villain; already in-repo, portrait-ready.
2. **Nethermancer** — `frontend/public/landing/nethermancer.jpg` (local, 605×1100). Tall, naturally vertical — best portrait crop in the set.
3. **Witch** (large) — Drive PNG `1vC5L9AadUWGTCoqGD9xcl0BS4S3P98Wq` / JPG `10uyV2uwDK414Jubf83vRPp671qfCaO_e`. Classic antagonist; transparent PNG frames well.
4. **Skull Witch** — Drive `1L126HfNG4_Qreiafigy1GEG4_EZHbdqd`. Strong dark-fantasy boss read; great for an elite/boss frame.
5. **Wraith** — Drive transparent PNG `184gnjfQnquNaLkXDWuFsnpNb_dOV8Dj4`. Already cut out — drops straight into a portrait frame, no masking needed.
6. **Revenant** — Drive `15SG9XIGsjNyxYTS5nBTAVECAh8ern9Vw` (png) / `1giAKfgakSXmj3LuYG2DDTm6FlWQqM9Ty` (jpg). Undead melee threat; good mid-tier enemy.
7. **Wight** (pick best of 3 variants) — Drive `1qfM3rG9JQPe7zP3cXBahlxleJX0HcGiw` (Wight3 png). Undead foot-soldier; 3 variants let you vary mooks.
8. **Withered** — Drive `1qmrfb0gNBO2C4cTM8MEUZRQIZZOGKC3j` (png). Gaunt undead/diseased; pairs with the "Plague" scene.
9. **Netherphage** — Drive `1bjvuowS5fPiHY44eCMbNSs0Spu3U3mlF` (png). Otherworldly horror; good "eldritch" capstone monster.
10. **Werewolf** — `frontend/public/landing/werewolf.jpg` (local, 689×900) or Drive `1KA7m1dUFhBOFJMQoq91Mcxo_S9uA2PBu` (png). Beast encounter; landscape-ish, crop to bust.
11. **Fae** — `frontend/public/landing/fae.jpg` (local, 616×900). Ambiguous antagonist; ties to Fae Feast encounter art.
12. **Bones / skeleton** (4 variants) — Drive `1RQ0ns-tiJTuv7frP-YfD-PE16b0ObxXe` + 3 others. Cheapest mook tier; 4 variants for swarms.
13. **Clovis** (named boss NPC) — `frontend/public/landing/clovis.jpg` (local) / Drive `1QyaGqokGMOSMvIy7vczjYoy8bGEKqZZY`. Use as a specific story antagonist.
14. **Grace Bannon** (named NPC) — Drive `127Z-tDqYDOuhw69S4GnY3AFGC7ixLchh` (png). Named-character portrait; antagonist or quest-giver depending on arc.

**Framing notes:** Local landing JPGs are already ~600–700 × 900–1100 — ideal portrait aspect,
use as-is. Drive masters are 2–10k px; downscale to ~600–900 px wide for a portrait card. Prefer
transparent PNGs (Wraith, Witch, Wight, Bones, Werewolf, Netherphage, Withered) so the subject can
be composited inside the local `skull.png` / woodcut-border frame for the "framed monster" look.

---

## C. Gaps — enemy types with NO matching art

These appear in game data / quests / canon but have **no dedicated portrait or creature art** in
either source. New commissions from the Drive pipeline would be needed.

| Enemy type | Where it appears | Art status |
|------------|------------------|------------|
| **Zombie** | The only enemy NPC in the DB (CLAUDE.md Priority 1) | **No art.** Closest stand-ins are the undead set (Wight / Revenant / Withered / Bones), but no piece is labelled or drawn as a zombie. Needs commission, or re-skin a Wight. |
| **Bandit / brigand (individual portrait)** | Quests; chargen `brigand` archetype | **Scene-only.** "Bandit Battle/Camp" exist as wide *backdrops*, not a single-figure antagonist portrait. The opt `brigand` portrait (`1o9ve4NdLN52boXbK-NdHsOf5atjuIQxJ`) is a duelist and the best stand-in; a true bandit bust is missing. |
| **The Crows (faction enemies)** | Quest canon (Rourke smugglers / Crows) | **No character art.** Only generic crow *silhouettes* exist (`1Yz0lk4EGyOXiZ4JYbgW0d9XBw3RZ6kGY`). No Crow-member/enforcer portrait. Needs commission. |
| **Generic beasts (wolf, bear, boar, etc.)** | Wilderness/field encounters | **Near-zero.** Only `head_beast_fox` (a stylized fox head) and the Werewolf. No mundane animal antagonists. |
| **Ghoul / vampire / spectral undead beyond the set** | Implied by dark-fantasy genre | Partial. Undead set covers wight/wraith/revenant/withered/bones; no ghoul or vampire specifically. |
| **Demon / devil / infernal** | Not yet in DB but genre-expected | **No art** (one *woodcut* of a devil-and-magician exists as a border illustration, not a portrait). |
| **Encounter frame / portrait border purpose-built for combat** | UI need | Partial. `skull.png` + woodcut borders + wax-seal can be composed into a frame, but there is **no ready-made "monster portrait frame"** asset — it must be assembled. |

---

## D. Provenance Note

All assets listed above come **exclusively** from the two permitted Eldritch sources. No
AI-generated, stock, or web imagery is included.

**Source 1 — local committed art (inspected with `sips` for real dimensions):**
- `frontend/public/art/` (top level, `map/`, `opt/`)
- `frontend/public/landing/`
- The opt/ archetype-portrait IDs are labelled in `frontend/src/data/chargenData.js`.

**Source 2 — Google Drive art repository (searched via the Google Drive MCP).** Folders / parent
ids confirmed during this audit:
- `18XUypzZIxFRQQPMvFC_1Pr7peAxEf8h4` — **creature / bestiary art** (Necromancer, Nethermancer,
  Netherphage, Withered, Wight ×4, Wraith, Revenant, Werewolf, Witch, Fae, Bones, plus named NPCs
  Clovis & Grace Bannon). This is the primary monster-art folder.
- `1a0td_mpBfDNShielqINEO3-rBJzog6Fs` — Skull Witch set.
- `1BwBSrO_dvP_qPzYD_XoUWUYiMrHXcDXR` / `1O9fVLnY2bQ5Octsuh9Qjknc-BqSzXpW7` — "The Fae Feast"
  encounter stills.
- `1Xs2J2UxYFWQwKhzukGOAid5R9FaPpp-4` — Holly Schoales 2026 scene set (Plague, Everfrost, Final
  Act, Dusk Ceremony, Cheese King, Fae Feast, Wedding) — encounter backdrops.
- `1HR2Otbt4imlEW3yPCthQIMkRdCHrAoo9` — woodcut borders/frames.
- `1cfkeMj8GGzxn0XAoud_vRaKuusw41UBd` — misc borders (Rats, Gathering Nodes).
- Bandit Battle/Camp/Negotiation/Escape scenes (root-level, owner spencer.mcghin@gmail.com).
- Faction heraldry banners (Hale, Rourke, Corveaux, Richter, Bannon, Blayne, Innis, Dragon/Sun
  variants) under per-house folders.

Search queries used: title/fullText matches for `creature`, `monster`, `antagonist`,
`werewolf`, `necromancer`, `fae`, `zombie`, `bandit`, `crow`, `beast`, `demon`, `ghoul`,
`wraith`, `skull`, `wax`, `frame`, `border`, `portrait`, plus a full `parentId` enumeration of the
bestiary folder. No enemy-specific art was found for the gaps listed in Section C.
