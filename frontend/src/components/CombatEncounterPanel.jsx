import { useEffect, useMemo, useState } from 'react'
import { resolveAntagonist } from '../data/antagonists'
import './CombatEncounterPanel.css'

/**
 * CombatEncounterPanel — old-school graphical-MUD / dungeon-crawler
 * combat surface. You face a framed antagonist portrait (the screen's
 * dominant element), with their name as a Cinzel gold title, HP as a
 * blood bar, a mist turn-indicator, and action buttons in the existing
 * Mistbound-Gothic button language.
 *
 * This is the GRAPHICAL evolution of CombatEncounterModal: where the
 * modal was a text "do you want to engage?" prompt, this panel is the
 * sustained face-off you look at for the duration of the fight.
 *
 * ── Art provenance ───────────────────────────────────────────────
 * Portraits come ONLY from the committed Eldritch art repository: the
 * framed bestiary plates under frontend/public/art/antagonists/ (built
 * from the Drive Bestiary/ folder via _pipeline.py) resolved through the
 * antagonists.js registry, plus the skull.png fallback (no AI/stock/
 * external art). The `portrait` prop is an explicit path; `artKey`
 * resolves via the registry; otherwise the name keyword-matches.
 *
 * Props:
 *   encounter — {
 *     name,                 // antagonist display name
 *     desc,                 // short flavor line (bone serif)
 *     portrait,             // path under /public (e.g. '/landing/werewolf.jpg')
 *     artKey,               // optional: resolves via antagonists.js if no portrait
 *     isBoss,               // gold frame + "BOSS" eyebrow when true
 *     hp, maxHp,            // antagonist health → blood bar
 *     status,               // optional status word (e.g. 'staggered', 'bleeding')
 *     myTurn,               // true → mist "YOUR TURN" + actions enabled
 *     turnOrder,            // [{ name, hp, maxHp, isMe, isAntagonist }]
 *     also,                 // [{ name }] other hostiles present (selectable)
 *   } or null
 *   actions  — [{ key, label, danger }]  buttons to render
 *   onAction — (actionKey) => void   fires e.g. `strike <antagonist>`
 *   onFlee   — () => void            disengage / retreat
 *   onTargetOther — (name) => void   re-target a different hostile
 */

// Fallback "unknown horror" — the project skull plate — for any NPC that
// resolves to no bestiary portrait.
const DEFAULT_PORTRAIT = '/art/skull.png'

function resolvePortrait(enc) {
  if (enc.portrait) return enc.portrait
  const entry = resolveAntagonist(enc.name, enc.artKey)
  if (entry) return entry.portrait
  return DEFAULT_PORTRAIT
}

function BloodBar({ hp, maxHp, label }) {
  const pct = maxHp > 0 ? Math.max(0, Math.min(100, (hp / maxHp) * 100)) : 0
  const low = pct <= 30
  return (
    <div className="cep-blood">
      <div className="cep-blood-track">
        <div
          className={`cep-blood-fill ${low ? 'cep-blood-low' : ''}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {label && (
        <span className="cep-blood-label font-mono">
          {Math.max(0, Math.round(hp))} / {maxHp}
        </span>
      )}
    </div>
  )
}

export default function CombatEncounterPanel({
  encounter,
  actions,
  onAction,
  onFlee,
  onTargetOther,
}) {
  const [hitFlash, setHitFlash] = useState(0)
  const portrait = useMemo(
    () => (encounter ? resolvePortrait(encounter) : null),
    [encounter?.portrait, encounter?.artKey],
  )

  // Pulse the portrait frame red whenever the antagonist's HP drops.
  const hp = encounter?.hp
  useEffect(() => {
    if (hp === undefined) return
    setHitFlash((n) => n + 1)
  }, [hp])

  if (!encounter) return null

  const {
    name,
    desc,
    isBoss,
    maxHp = 100,
    status,
    myTurn,
    turnOrder = [],
    also = [],
  } = encounter
  const slain = encounter.hp !== undefined && encounter.hp <= 0
  const defaultActions = [
    { key: 'strike', label: 'Strike', danger: true },
    { key: 'cleave', label: 'Cleave', danger: true },
    { key: 'stagger', label: 'Stagger' },
    { key: 'disarm', label: 'Disarm' },
  ]
  const acts = actions && actions.length ? actions : defaultActions

  return (
    <div className="cep-backdrop">
      <div className={`cep-arena ${isBoss ? 'cep-boss' : ''} ${slain ? 'cep-slain' : ''}`}>
        {/* Ambient drifting mist at the arena edges — the one allowed motion */}
        <div className="cep-mist" aria-hidden />

        <div className="cep-header">
          <span className="cep-eyebrow cinzel">
            {isBoss ? '☠ BOSS ENCOUNTER' : '⚔ YOU ARE BESET'}
          </span>
          {status && <span className="cep-status font-mono">{status}</span>}
        </div>

        {/* Portrait — the dominant element. Framed, gold-cornered,
            vignetted; remounts keyed by hitFlash so each HP change
            triggers the frame's red pulse. */}
        <div className="cep-stage">
          <figure className={`cep-portrait ${isBoss ? 'cep-portrait-boss' : ''}`}>
            <div className="cep-frame" key={hitFlash}>
              <span className="cep-corner tl" aria-hidden>✦</span>
              <span className="cep-corner tr" aria-hidden>✦</span>
              <span className="cep-corner bl" aria-hidden>✦</span>
              <span className="cep-corner br" aria-hidden>✦</span>
              <img
                className="cep-portrait-img"
                src={portrait}
                alt={name}
                draggable={false}
              />
              <div className="cep-vignette" aria-hidden />
              {slain && <div className="cep-slain-overlay cinzel">SLAIN</div>}
            </div>
          </figure>

          <h2 className="cep-name cinzel">{name}</h2>
          {desc && <p className="cep-desc">{desc}</p>}

          <BloodBar hp={encounter.hp ?? maxHp} maxHp={maxHp} label />

          {also.length > 0 && (
            <div className="cep-also">
              <span className="cep-also-label cinzel">ALSO HERE</span>
              {also.map((h) => (
                <button
                  key={h.name}
                  className="cep-also-chip font-mono"
                  onClick={() => onTargetOther && onTargetOther(h.name)}
                >
                  {h.name}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Turn order rail — compact, mist-toned */}
        {turnOrder.length > 0 && (
          <div className="cep-turns">
            {turnOrder.map((c, idx) => (
              <div
                key={c.name}
                className={`cep-turn ${idx === 0 ? 'cep-turn-current' : ''} ${
                  c.isMe ? 'cep-turn-me' : ''
                } ${c.isAntagonist ? 'cep-turn-foe' : ''}`}
              >
                <span className="cep-turn-arrow">{idx === 0 ? '▸' : idx + 1}</span>
                <span className="cep-turn-name">
                  {c.name}
                  {c.isMe ? ' (you)' : ''}
                </span>
                <BloodBar hp={c.hp ?? 100} maxHp={c.maxHp ?? 100} />
              </div>
            ))}
          </div>
        )}

        {/* Turn indicator + actions */}
        <div className="cep-footer">
          <div className={`cep-turn-banner ${myTurn ? 'cep-turn-on' : ''}`}>
            {myTurn ? 'YOUR TURN' : 'The foe moves…'}
          </div>

          <div className="cep-actions">
            {acts.map((a) => (
              <button
                key={a.key}
                className={`cep-btn ${a.danger ? 'cep-btn-danger' : ''}`}
                disabled={!myTurn || slain}
                onClick={() => onAction && onAction(a.key)}
              >
                {a.label}
              </button>
            ))}
            <button className="cep-btn cep-btn-flee" onClick={() => onFlee && onFlee()}>
              Flee
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
