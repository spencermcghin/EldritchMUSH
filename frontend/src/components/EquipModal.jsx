import { useState, useEffect, useCallback } from 'react'
import './EquipModal.css'

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

const TYPE_LABELS = {
  weapon: 'Weapon',
  bow: 'Bow',
  shield: 'Shield',
  armor: 'Armor',
  gloves: 'Gloves',
  boots: 'Boots',
  clothing: 'Clothing',
  cloak: 'Cloak',
  kit: 'Kit',
  arrows: 'Arrows',
  bullets: 'Bullets',
  consumable: 'Consumable',
  misc: 'Item',
}

function ItemCard({ item, onEquip, onUnequip, onDrop, onGive, onInspect, feedback }) {
  const icon = TYPE_ICONS[item.type] || '◆'
  const typeLabel = TYPE_LABELS[item.type] || 'Item'

  const canUse = item.canUse !== false  // default to true if field is missing

  return (
    <div className={`equip-item-card ${item.equipped ? 'equipped' : ''} ${item.broken ? 'broken' : ''} ${!canUse ? 'unusable' : 'usable'}`}>
      <div className="equip-item-icon">{icon}</div>
      <div className="equip-item-info">
        <div className="equip-item-name">
          {item.name}
          {item.broken && <span className="equip-item-broken-tag">BROKEN</span>}
          {!canUse && item.requiredSkill && (
            <span className="equip-item-skill-tag">Requires {item.requiredSkill}</span>
          )}
        </div>
        <div className="equip-item-type">{typeLabel}</div>
        {item.desc && <div className="equip-item-desc">{item.desc}</div>}
        <div className="equip-item-stats">
          {item.damage > 0 && <span className="equip-stat">DMG {item.damage}</span>}
          {item.materialValue > 0 && <span className="equip-stat">AV +{item.materialValue}</span>}
          {item.twohanded && <span className="equip-stat">2H</span>}
          {item.level > 0 && <span className="equip-stat">T{item.level}</span>}
        </div>
      </div>
      <div className="equip-item-actions">
        {item.equipped ? (
          <button
            className="equip-action-btn unequip"
            onClick={() => onUnequip(item.name)}
            disabled={feedback}
            title="Unequip"
          >
            {feedback ? 'Removing...' : 'Remove'}
          </button>
        ) : (
          <>
            {(item.type === 'weapon' || item.type === 'shield' || item.type === 'bow') && !item.twohanded ? (
              <div className="equip-hand-btns">
                <button
                  className="equip-action-btn equip"
                  onClick={() => onEquip(item.name, 'right')}
                  disabled={item.broken || !canUse || feedback}
                  title="Equip to right hand"
                >
                  {feedback ? '...' : 'R'}
                </button>
                <button
                  className="equip-action-btn equip"
                  onClick={() => onEquip(item.name, 'left')}
                  disabled={item.broken || !canUse || feedback}
                  title="Equip to left hand"
                >
                  {feedback ? '...' : 'L'}
                </button>
              </div>
            ) : (
              <button
                className="equip-action-btn equip"
                onClick={() => onEquip(item.name)}
                disabled={item.broken || !canUse || feedback}
                title={item.broken ? 'Item is broken' : !canUse ? `Requires ${item.requiredSkill} skill` : `Equip to ${item.targetSlotLabel || 'slot'}`}
              >
                {feedback ? 'Equipping...' : 'Equip'}
              </button>
            )}
            <button
              className="equip-action-btn drop"
              onClick={() => onDrop(item.name)}
              disabled={feedback}
              title="Drop item on the ground"
            >
              Drop
            </button>
            {onGive && (
              <button
                className="equip-action-btn give"
                onClick={() => onGive(item)}
                disabled={feedback}
                title="Give to someone in this room"
              >
                Give
              </button>
            )}
            {item.type === 'consumable' && onInspect && (
              <button
                className="equip-action-btn inspect"
                onClick={() => onInspect(item.name)}
                disabled={feedback}
                title="Inspect this consumable's effect"
              >
                Inspect
              </button>
            )}
          </>
        )}
      </div>
      {item.equipped && (
        <div className="equip-item-slot-badge">{item.equippedSlot}</div>
      )}
    </div>
  )
}

function SlotDisplay({ slots }) {
  if (!slots) return null
  const slotEntries = Object.entries(slots).filter(([, v]) => v)

  return (
    <div className="equip-slots-bar">
      {slotEntries.map(([key, slot]) => (
        <div key={key} className={`equip-slot ${slot.item ? 'filled' : 'empty'}`}>
          <span className="equip-slot-label">{slot.label}</span>
          <span className="equip-slot-item">{slot.item || '---'}</span>
        </div>
      ))}
    </div>
  )
}

export default function EquipModal({ onClose, sendCommand, inventoryData, onGiveRequest }) {
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(!inventoryData)

  // Request inventory data on mount
  useEffect(() => {
    sendCommand('__equip_ui__')
  }, [sendCommand])

  // Once data arrives, stop loading
  useEffect(() => {
    if (inventoryData) setLoading(false)
  }, [inventoryData])

  const [actionFeedback, setActionFeedback] = useState(null)

  const handleEquip = useCallback((name, slot) => {
    setActionFeedback({ name, action: 'equipping' })
    const cmd = slot ? `equip ${name} to ${slot}` : `equip ${name}`
    sendCommand(cmd)
    setTimeout(() => {
      sendCommand('__equip_ui__')
      setActionFeedback(null)
    }, 800)
  }, [sendCommand])

  const handleUnequip = useCallback((name) => {
    setActionFeedback({ name, action: 'removing' })
    sendCommand(`unequip ${name}`)
    setTimeout(() => {
      sendCommand('__equip_ui__')
      setActionFeedback(null)
    }, 800)
  }, [sendCommand])

  const handleDrop = useCallback((name) => {
    setActionFeedback({ name, action: 'dropping' })
    sendCommand(`drop ${name}`)
    setTimeout(() => {
      sendCommand('__equip_ui__')
      setActionFeedback(null)
    }, 800)
  }, [sendCommand])

  // "Inspect" runs `look <item>` so the player sees Effect/Type/Level
  // for consumables (the only details surfaced on look today). It's
  // a stand-in for a real `use` command — until we wire the apply/coat
  // mechanics, this is what a player can do with a brewed substance.
  const handleInspect = useCallback((name) => {
    sendCommand(`look ${name}`)
  }, [sendCommand])

  // Give: ask App.jsx to open the NpcPickerModal scoped to this item.
  // App.jsx already knows the room NPC list (roomNpcMeta), so we lift
  // the picker flow up rather than duplicating it here.
  const handleGive = useCallback((item) => {
    if (onGiveRequest) onGiveRequest(item)
  }, [onGiveRequest])

  const items = inventoryData?.items || []
  const slots = inventoryData?.slots || {}

  // Filter items
  const filteredItems = filter === 'all'
    ? items
    : filter === 'equipped'
      ? items.filter(i => i.equipped)
      : items.filter(i => i.type === filter)

  // Group by equipped/unequipped
  const equippedItems = filteredItems.filter(i => i.equipped)
  const unequippedItems = filteredItems.filter(i => !i.equipped)

  const filterOptions = [
    { key: 'all', label: 'All' },
    { key: 'equipped', label: 'Equipped' },
    { key: 'weapon', label: 'Weapons' },
    { key: 'armor', label: 'Armor' },
    { key: 'shield', label: 'Shields' },
    { key: 'consumable', label: 'Consumables' },
    { key: 'misc', label: 'Other' },
  ]

  return (
    <div className="equip-modal-backdrop" onClick={onClose}>
      <div className="equip-modal" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="equip-modal-header">
          <span className="cinzel equip-modal-title">ARMORY</span>
          <button className="equip-modal-close" onClick={onClose}>✕</button>
        </div>

        {/* Equipment Slots Overview */}
        <SlotDisplay slots={slots} />

        {/* Filter Bar */}
        <div className="equip-filter-bar">
          {filterOptions.map(opt => (
            <button
              key={opt.key}
              className={`equip-filter-btn ${filter === opt.key ? 'active' : ''}`}
              onClick={() => setFilter(opt.key)}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="equip-modal-body">
          {loading ? (
            <div className="equip-loading">Gathering your possessions...</div>
          ) : items.length === 0 ? (
            <div className="equip-empty">
              Your inventory is empty. Pick up items from the world to equip them.
            </div>
          ) : (
            <>
              {equippedItems.length > 0 && (
                <div className="equip-section">
                  <div className="equip-section-label cinzel">EQUIPPED</div>
                  <div className="equip-item-grid">
                    {equippedItems.map(item => (
                      <ItemCard
                        key={item.id}
                        item={item}
                        onEquip={handleEquip}
                        onUnequip={handleUnequip}
                        onDrop={handleDrop}
                        onGive={handleGive}
                        onInspect={handleInspect}
                        feedback={actionFeedback && actionFeedback.name === item.name}
                      />
                    ))}
                  </div>
                </div>
              )}
              {unequippedItems.length > 0 && (
                <div className="equip-section">
                  <div className="equip-section-label cinzel">INVENTORY</div>
                  <div className="equip-item-grid">
                    {unequippedItems.map(item => (
                      <ItemCard
                        key={item.id}
                        item={item}
                        onEquip={handleEquip}
                        onUnequip={handleUnequip}
                        onDrop={handleDrop}
                        onGive={handleGive}
                        onInspect={handleInspect}
                        feedback={actionFeedback && actionFeedback.name === item.name}
                      />
                    ))}
                  </div>
                </div>
              )}
              {filteredItems.length === 0 && (
                <div className="equip-empty">No items match this filter.</div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="equip-modal-footer">
          <span className="cinzel">✦ ─────── ✦ ─────── ✦</span>
        </div>
      </div>
    </div>
  )
}
