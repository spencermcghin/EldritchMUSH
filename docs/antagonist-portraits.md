# Antagonist Portraits — Graphical Creature Presence

Give enemy NPCs a **framed graphical presence** in the web client: when a
hostile creature is in a room or encounter, the player sees a vignetted,
gold-framed portrait of it — old-school graphical-MUD / dungeon spirit, on
top of the existing text play.

> **Art provenance is a hard rule.** Every output pixel derives from a
> committed Eldritch source illustration. The pipeline only *manipulates*
> source art (crop / desaturate / tint / vignette / frame). No external,
> stock, or AI-generated art is introduced. See the provenance table below.

---

## What ships in this prototype

| Path | What it is |
|------|------------|
| `frontend/public/art/antagonists/*-portrait.png` | 4 derived render samples (512×512) |
| `frontend/public/art/antagonists/_pipeline.py` | The repeatable Pillow pipeline that produced them |
| `frontend/src/data/antagonists.js` | `art_key` → portrait registry + keyword resolver |
| `frontend/src/components/AntagonistPortrait.jsx` / `.css` | Framed portrait component |
| `frontend/src/components/RoomView.jsx` | Renders a portrait banner when an antagonist is present |

---

## Provenance table (derived render → Eldritch source)

| Derived file | Eldritch source (committed) | Crop (L,T,R,B frac) | Notes |
|--------------|------------------------------|----------------------|-------|
| `werewolf-portrait.png` | `frontend/public/landing/werewolf.jpg` | 0.26, 0.22, 0.70, 0.62 | snarling moonlit head + shoulders |
| `necromancer-portrait.png` | `frontend/public/landing/necromancer.jpg` | 0.22, 0.04, 0.82, 0.55 | cowled figure, head + raised hand |
| `fae-portrait.png` | `frontend/public/landing/fae.jpg` | 0.20, 0.02, 0.80, 0.48 | masked, thorn-crowned head/shoulders |
| `nethermancer-portrait.png` | `frontend/public/landing/nethermancer.jpg` | 0.10, 0.05, 0.92, 0.62 | arms-raised conjurer + skull-staff |

All four sources are single full illustrations (≈600–700 × 900–1100, sepia
ink on near-white paper). The pipeline is deterministic — re-running
`_pipeline.py` regenerates byte-stable portraits from the same sources.

---

## The pipeline (exact commands)

Tooling: **Python 3 + Pillow** (no ImageMagick required). Run from the output
directory:

```bash
cd frontend/public/art/antagonists
python3 _pipeline.py
```

Per-portrait stages (see `_pipeline.py` for the implementation):

1. **Crop** the source to a portrait window (fractions above), then
   `ImageOps.fit` to a square inner window (centering biased slightly up so
   the face sits in the upper third).
2. **Grayscale + autocontrast** (`cutoff=1`) so the ink linework reads
   regardless of the source's paper tone.
3. **Tritone tint** onto the Mistbound palette: shadows → near-void
   (`#12161 5`), midtones → verdigris `--mist` (`#a3b5a8`), highlights →
   a brightened verdigris. Optional **blood bleed** into the midtones per
   creature (werewolf/nethermancer get more menace).
4. **Whisper toward `--void`** (8%) so bone-prose stays the brightest UI
   element (a Mistbound rule).
5. **Radial vignette** composites the edges down into shadow, focusing the
   face.
6. **Verdigris bloom** — screen a blurred copy back in to lift highlights
   (the one ambient *static* glow; the live drift is CSS, below).
7. **Gold frame** — a rounded `--void` plate with a `--accent-gold` border
   (gold is reserved for frame/interactive per the palette), art pasted into
   a rounded inner window.

Output: `512×512` PNG with a 22px gold frame. To add a creature, append an
entry to `PORTRAITS` in `_pipeline.py` (source file + crop box + blood mix)
and re-run.

---

## How an NPC `art_key` maps to a portrait

The server-side enemy NPC (`eldritchmush/typeclasses/npc.py`, the `Npc`
typeclass) can carry an optional attribute:

```python
self.db.art_key = "werewolf"   # set in at_object_creation or via @set
```

The web client resolves a portrait in this order (`frontend/src/data/antagonists.js`):

1. **explicit** `art_key` sent by the server → exact registry entry, or
2. **keyword** fallback against the displayed name (e.g. a name containing
   "wolf"/"beast" → werewolf; "zombie"/"undead" → necromancer).

```js
import { resolveAntagonist } from '../data/antagonists'
const entry = resolveAntagonist(name, npc.art_key) // → {portrait, label, source, keywords} | null
```

PCs and vendors resolve to `null` and render no portrait — only recognised
antagonists get the graphical treatment.

> **Wiring `art_key` end-to-end (next step, not in this prototype):** the
> Evennia webclient currently sends room text, not structured NPC data. To
> drive portraits off `db.art_key` rather than name keywords, emit the key in
> an OOB payload (the project already uses OOB events per the quest system)
> or include it in the character listing the client parses. Until then the
> keyword resolver gives a working graphical presence with zero server
> changes.

---

## How it renders (RoomView / encounter)

`RoomView.jsx` computes the antagonists present from the parsed character
list and, when any resolve, renders a portrait banner above the existing
three-column Exits/Characters/Items layout:

```jsx
{antagonists.length > 0 && (
  <div className="room-antagonists">
    {antagonists.map((a, i) => (
      <AntagonistPortrait
        key={i}
        name={a.name}
        artKey={a.artKey}
        size="sm"
        onClick={() => onCommand(`look ${a.name}`)}
      />
    ))}
  </div>
)}
```

The plain skull-icon character buttons remain — the portrait is an *added*
graphical layer, not a replacement, so nothing regresses for screen readers
or text-first players. For a dedicated encounter screen, render the same
component at `size="lg"` (232px) as the encounter "hero".

### The component

```jsx
import { resolveAntagonist } from '../data/antagonists'
import './AntagonistPortrait.css'

export default function AntagonistPortrait({ name, artKey, onClick, size = 'sm' }) {
  const entry = resolveAntagonist(name, artKey)
  if (!entry) return null
  return (
    <figure className={`antagonist-portrait antagonist-portrait-${size}`}
            onClick={onClick} title={onClick ? `Look at ${name}` : entry.label}>
      <div className="antagonist-frame">
        <img src={entry.portrait} alt={entry.label} loading="lazy" />
        <span className="antagonist-mist" aria-hidden="true" />
      </div>
      <figcaption className="antagonist-name cinzel">{name || entry.label}</figcaption>
    </figure>
  )
}
```

Mistbound conformance: gold only on the frame/name-plate; the figure reads in
cold verdigris; danger shows as a blood underglow on hover; the **single
ambient motion** is one slow mist drift (`antagonist-mist-drift`), disabled
under `prefers-reduced-motion`. No CRT, no scanlines.

---

## Composite vs. fresh Drive commissions — recommendation

**This composite pipeline is the right path to ship now**, and Drive holds
better *source* art to feed it later. Both are true; they are the same
pipeline with different inputs.

- The local `landing/*.jpg` illustrations are full-body plates on white
  paper. Cropping a face out of a full scene (especially the busy werewolf
  plate) is serviceable but not ideal — the framing fights the composition.
- A Drive search surfaced **purpose-built creature art that would feed this
  exact pipeline far better**, with zero new commission cost:
  - `wraith_transparent.png` (id `184gnjfQnquNaLkXDWuFsnpNb_dOV8Dj4`) —
    transparent cutout; composite straight onto the void plate, no crop fight.
  - `Fayne-head-mask.png` / `Fayne-head-no-hood.png` — already head-framed.
  - `head_beast_fox.jpeg` — an existing beast *head* crop.
  - `Monster Eye.jpg`, `wraith_large.jpg` (4.5 MB) — high-res menace.

**Recommendation:** keep the composite pipeline as the rendering system; do
**not** commission fresh art. Instead, pull the head-cropped / transparent
Drive assets above into `frontend/public/art/antagonists/_sources/`, point
new `PORTRAITS` entries at them, and the transparent ones skip the crop step
entirely (paste onto the void plate). That yields cleaner portraits than the
landing-plate crops while staying 100% within the Eldritch art repository.
Reserve a commission only if a *named boss* needs a bespoke portrait no
existing asset covers.
```
