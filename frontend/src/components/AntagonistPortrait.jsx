import { resolveAntagonist } from '../data/antagonists'
import './AntagonistPortrait.css'

// Framed creature portrait for an antagonist present in the room/encounter.
// The portrait art is already gold-framed and vignetted in the PNG (derived
// from Eldritch source illustrations); this component only sizes it, adds the
// single ambient mist drift, and a clickable name plate.
//
// Props:
//   name      — the antagonist's displayed name (used for keyword fallback)
//   artKey    — explicit key from npc.db.art_key (preferred)
//   onClick   — optional; e.g. () => onCommand(`look ${name}`)
//   size      — 'sm' (room column) | 'lg' (encounter hero). default 'sm'
export default function AntagonistPortrait({ name, artKey, onClick, size = 'sm' }) {
  const entry = resolveAntagonist(name, artKey)
  if (!entry) return null

  return (
    <figure
      className={`antagonist-portrait antagonist-portrait-${size}`}
      onClick={onClick}
      title={onClick ? `Look at ${name}` : entry.label}
    >
      <div className="antagonist-frame">
        <img src={entry.portrait} alt={entry.label} loading="lazy" />
        <span className="antagonist-mist" aria-hidden="true" />
      </div>
      <figcaption className="antagonist-name cinzel">{name || entry.label}</figcaption>
    </figure>
  )
}
