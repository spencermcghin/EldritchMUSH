import { useEffect, useState } from 'react'
import './CombatEncounterModal.css'

/**
 * CombatEncounterModal — opt-in prompt fired when the player walks
 * into a room with hostile NPCs. Lets them engage on their own terms
 * rather than being shoved into a fight by the next click.
 *
 * Props:
 *   encounter — { room, hostiles: [{name, dbref, desc, isBoss}], ts } or null
 *   onEngage  — (npcName) => void  fires `strike <npc>`
 *   onHold    — () => void         dismisses without engaging
 */
export default function CombatEncounterModal({ encounter, onEngage, onHold }) {
  const [open, setOpen] = useState(false)
  const [current, setCurrent] = useState(null)

  useEffect(() => {
    if (!encounter || !encounter.ts) return
    setCurrent(encounter)
    setOpen(true)
  }, [encounter?.ts])

  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (e.key === 'Escape') dismiss() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open])

  const dismiss = () => {
    setOpen(false)
    if (onHold) onHold()
  }

  const engage = (name) => {
    setOpen(false)
    if (onEngage) onEngage(name)
  }

  if (!open || !current || !current.hostiles?.length) return null

  const boss = current.hostiles.find(h => h.isBoss) || current.hostiles[0]
  const others = current.hostiles.filter(h => h !== boss)
  const isBoss = !!boss.isBoss

  return (
    <div className="combat-encounter-backdrop" onClick={dismiss}>
      <div
        className={`combat-encounter-modal ${isBoss ? 'boss' : ''}`}
        onClick={e => e.stopPropagation()}
      >
        <div className="combat-encounter-header">
          <span className="cinzel combat-encounter-eyebrow">
            {isBoss ? '☠ BOSS ENCOUNTER' : '⚔ HOSTILE PRESENCE'}
          </span>
          <button
            className="combat-encounter-close"
            onClick={dismiss}
            title="Hold back"
          >✕</button>
        </div>

        <div className="combat-encounter-body">
          <div className="combat-encounter-title cinzel">{boss.name}</div>
          {boss.desc && (
            <p className="combat-encounter-desc">{boss.desc}</p>
          )}

          {others.length > 0 && (
            <div className="combat-encounter-section">
              <div className="combat-encounter-label cinzel">ALSO HERE</div>
              <ul className="combat-encounter-list">
                {others.map((h) => (
                  <li key={h.dbref || h.name}>
                    <button
                      className="combat-encounter-target"
                      onClick={() => engage(h.name)}
                    >
                      {h.name}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="combat-encounter-actions">
            <button
              className="combat-encounter-btn engage"
              onClick={() => engage(boss.name)}
            >
              Engage {boss.name}
            </button>
            <button
              className="combat-encounter-btn hold"
              onClick={dismiss}
            >
              Hold back
            </button>
          </div>

          <div className="combat-encounter-hint">
            You can leave the room and come back if you'd rather prepare first.
          </div>
        </div>
      </div>
    </div>
  )
}
