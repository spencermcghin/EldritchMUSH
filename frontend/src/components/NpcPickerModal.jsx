import { useMemo, useState } from 'react'
import './ItemPickerModal.css'

/**
 * Pick an NPC from the current room. Reads roomNpcMeta (already
 * populated whenever the player walks into a room). Used by the
 * EquipModal "Give" flow so the player doesn't have to leave the
 * inventory screen to hand a quest item over.
 *
 * Props:
 *   title     — header text (e.g. "GIVE BLADE OIL TO...")
 *   roomNpcMeta — object keyed by lowercase NPC name → meta entry
 *                 (we just pull .name out for display)
 *   onPick    — (npcName: string) => void
 *   onClose   — () => void
 */
export default function NpcPickerModal({
  title = 'CHOOSE A RECIPIENT',
  subtitle = '',
  roomNpcMeta,
  onPick,
  onClose,
}) {
  const [filter, setFilter] = useState('')

  // Dedupe by display name — meta is keyed by both name and aliases,
  // so the same NPC can show up under multiple keys.
  const npcs = useMemo(() => {
    const seen = new Set()
    const out = []
    for (const entry of Object.values(roomNpcMeta || {})) {
      const name = entry?.name
      if (!name || seen.has(name)) continue
      seen.add(name)
      out.push(entry)
    }
    if (!filter) return out
    const f = filter.toLowerCase()
    return out.filter(n => (n.name || '').toLowerCase().includes(f))
  }, [roomNpcMeta, filter])

  return (
    <div className="ip-modal-backdrop" onClick={onClose}>
      <div className="ip-modal" onClick={e => e.stopPropagation()}>
        <div className="ip-modal-header">
          <span className="cinzel ip-modal-title">{title}</span>
          <button className="ip-modal-close" onClick={onClose}>✕</button>
        </div>
        {subtitle && <div className="ip-modal-subtitle">{subtitle}</div>}

        {npcs.length > 4 && (
          <div className="ip-filter-wrap">
            <input
              className="ip-filter"
              placeholder="Filter NPCs..."
              value={filter}
              onChange={e => setFilter(e.target.value)}
              autoFocus
            />
          </div>
        )}

        <div className="ip-modal-body">
          {npcs.length === 0 ? (
            <div className="ip-empty">No one in this room to receive it.</div>
          ) : (
            <div className="ip-grid">
              {npcs.map(npc => (
                <button
                  key={npc.name}
                  className="ip-item"
                  onClick={() => onPick(npc.name)}
                  title={`Give to ${npc.name}`}
                >
                  <span className="ip-item-icon">👤</span>
                  <span className="ip-item-name">{npc.name}</span>
                  {npc.isMerchant && <span className="ip-item-tag">MERCHANT</span>}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
