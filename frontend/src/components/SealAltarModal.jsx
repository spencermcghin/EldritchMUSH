import { useEffect, useState } from 'react'
import './SealAltarModal.css'

/**
 * SealAltarModal — Wardstone Hall puzzle UI.
 *
 * Visualises the Altar of Seals as four Telyrian rune slots arranged
 * around a circle. Each slot starts dark (the ward shattered); when
 * the player places a fragment, the corresponding slot lights up
 * with its Elder Futhark glyph. When all four are set, the Oblivion
 * Coil collapses in the adjacent Inner Sanctum.
 *
 * The player drives placements by clicking the "Place [rune]"
 * buttons at the bottom — each fires `place <fragment>` via
 * sendCommand. The server emits a fresh `seal_altar_state` OOB
 * event after each placement, refreshing this modal.
 *
 * Props:
 *   altar — { room, slots: [{name,symbol,meaning,filled,carried}],
 *            placed, total, complete, ts } or null
 *   sendCommand — (cmd) => void
 *   onClose — () => void  (manual dismiss)
 */
export default function SealAltarModal({ altar, sendCommand, onClose }) {
  const [open, setOpen] = useState(false)
  const [current, setCurrent] = useState(null)

  useEffect(() => {
    if (!altar || !altar.ts) return
    setCurrent(altar)
    setOpen(true)
  }, [altar?.ts])

  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (e.key === 'Escape') dismiss() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open])

  const dismiss = () => {
    setOpen(false)
    if (onClose) onClose()
  }

  if (!open || !current) return null

  const { slots = [], placed = 0, total = 4, complete = false } = current
  const carried = (slot) => !!slot.carried

  return (
    <div className="seal-altar-backdrop" onClick={dismiss}>
      <div className="seal-altar-modal" onClick={e => e.stopPropagation()}>
        <div className="seal-altar-header">
          <span className="cinzel seal-altar-eyebrow">
            ✦ ALTAR OF SEALS ✦
          </span>
          <button
            className="seal-altar-close"
            onClick={dismiss}
            title="Close"
          >✕</button>
        </div>

        <div className="seal-altar-body">
          <div className="seal-altar-progress cinzel">
            {placed} / {total} wards restored
          </div>

          {/* Four slots arranged in a 2×2 grid evoking the warding
              circle. Filled slots show the lit glyph; empty slots
              show a dim shattered placeholder. */}
          <div className="seal-altar-circle">
            {slots.map((slot) => (
              <div
                key={slot.name}
                className={`seal-slot ${slot.filled ? 'filled' : 'empty'}`}
              >
                <div className="seal-slot-glyph">
                  {slot.filled ? slot.symbol : '·'}
                </div>
                <div className="seal-slot-name cinzel">
                  {slot.name}
                </div>
                <div className="seal-slot-meaning">
                  {slot.meaning}
                </div>
              </div>
            ))}
          </div>

          {complete ? (
            <div className="seal-altar-complete">
              The four wards are whole. The Oblivion Coil has
              collapsed in the Inner Sanctum. The nethermancer is
              exposed.
            </div>
          ) : (
            <>
              <div className="seal-altar-actions">
                {slots.map((slot) => {
                  if (slot.filled) return null
                  const have = carried(slot)
                  return (
                    <button
                      key={slot.name}
                      className={`seal-altar-btn ${have ? 'ready' : 'waiting'}`}
                      onClick={() => sendCommand && sendCommand(`place ${slot.name}`)}
                      disabled={!have}
                      title={have
                        ? `Place the ${slot.name} ward`
                        : `You don't carry the ${slot.name} ward yet`
                      }
                    >
                      <span className="seal-btn-glyph">{slot.symbol}</span>
                      <span className="seal-btn-label">
                        Place {slot.name}
                      </span>
                    </button>
                  )
                })}
              </div>

              <div className="seal-altar-hint">
                The Nethermancer shattered four wards on his way down.
                Recover them from the Barrows above and set them here.
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
