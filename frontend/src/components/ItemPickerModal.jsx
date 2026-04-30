import { useEffect, useMemo, useState } from 'react'
import './ItemPickerModal.css'

const TYPE_ICONS = {
  weapon: '⚔',
  bow: '🏹',
  shield: '🛡',
  armor: '🪖',
  gloves: '🧤',
  boots: '👢',
  clothing: '👘',
  cloak: '🧥',
  kit: '🧰',
  arrows: '➳',
  bullets: '⊛',
  consumable: '⚗',
  misc: '◆',
}

/**
 * Generic inventory picker. Renders the player's inventory items as
 * clickable cards; calls onPick(item) when one is selected. Used to
 * power the "Give to NPC" flow from DetailPanel and EquipModal.
 *
 * Props:
 *   title         — header text (e.g. "GIVE TO MARTA")
 *   subtitle      — optional one-line hint under the header
 *   onPick        — (item) => void
 *   onClose       — () => void
 *   inventoryData — { items: [...] } from oobState
 *   sendCommand   — used to refresh inventory on mount
 *   excludeEquipped (default true) — hide currently-equipped items so
 *     the player doesn't accidentally hand over their armor mid-fight
 */
export default function ItemPickerModal({
  title = 'CHOOSE AN ITEM',
  subtitle = '',
  onPick,
  onClose,
  inventoryData,
  sendCommand,
  excludeEquipped = true,
}) {
  const [filter, setFilter] = useState('')

  useEffect(() => {
    if (sendCommand) sendCommand('__equip_ui__')
  }, [sendCommand])

  const items = useMemo(() => {
    const all = inventoryData?.items || []
    const visible = excludeEquipped ? all.filter(i => !i.equipped) : all
    if (!filter) return visible
    const f = filter.toLowerCase()
    return visible.filter(i =>
      (i.name || '').toLowerCase().includes(f) ||
      (i.type || '').toLowerCase().includes(f)
    )
  }, [inventoryData, filter, excludeEquipped])

  const loading = !inventoryData

  return (
    <div className="ip-modal-backdrop" onClick={onClose}>
      <div className="ip-modal" onClick={e => e.stopPropagation()}>
        <div className="ip-modal-header">
          <span className="cinzel ip-modal-title">{title}</span>
          <button className="ip-modal-close" onClick={onClose}>✕</button>
        </div>
        {subtitle && <div className="ip-modal-subtitle">{subtitle}</div>}

        <div className="ip-filter-wrap">
          <input
            className="ip-filter"
            placeholder="Filter inventory..."
            value={filter}
            onChange={e => setFilter(e.target.value)}
            autoFocus
          />
        </div>

        <div className="ip-modal-body">
          {loading ? (
            <div className="ip-loading">Counting your worldly goods...</div>
          ) : items.length === 0 ? (
            <div className="ip-empty">
              {excludeEquipped
                ? 'Nothing in your inventory to hand off.'
                : 'Your pack is empty.'}
            </div>
          ) : (
            <div className="ip-grid">
              {items.map(item => {
                const icon = TYPE_ICONS[item.type] || '◆'
                return (
                  <button
                    key={item.id}
                    className="ip-item"
                    onClick={() => onPick(item)}
                    title={item.desc || item.name}
                  >
                    <span className="ip-item-icon">{icon}</span>
                    <span className="ip-item-name">{item.name}</span>
                    {item.broken && <span className="ip-item-tag broken">BROKEN</span>}
                  </button>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
