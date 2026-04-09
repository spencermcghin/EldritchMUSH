import { useState, useEffect, useCallback } from 'react'
import './DetailPanel.css'

const NPC_ACTIONS = [
  { label: 'Look', icon: '👁', command: (name) => `look ${name}` },
  { label: 'Attack', icon: '⚔', command: (name) => `strike ${name}` },
  { label: 'Talk', icon: '💬', command: (name) => `say to ${name}` },
  { label: 'Follow', icon: '🚶', command: (name) => `follow ${name}` },
]

const ITEM_ACTIONS = [
  { label: 'Look', icon: '👁', command: (name) => `look ${name}` },
  { label: 'Get', icon: '✋', command: (name) => `get ${name}` },
  { label: 'Drop', icon: '↓', command: (name) => `drop ${name}` },
]

const PLAYER_ACTIONS = [
  { label: 'Look', icon: '👁', command: (name) => `look ${name}` },
  { label: 'Attack', icon: '⚔', command: (name) => `strike ${name}` },
  { label: 'Talk', icon: '💬', command: (name) => `say to ${name}` },
  { label: 'Follow', icon: '🚶', command: (name) => `follow ${name}` },
]

function getActions(entityType) {
  switch (entityType) {
    case 'npc':
    case 'character':
      return NPC_ACTIONS
    case 'item':
      return ITEM_ACTIONS
    case 'player':
      return PLAYER_ACTIONS
    default:
      return NPC_ACTIONS
  }
}

function getTypeLabel(entityType) {
  switch (entityType) {
    case 'npc':
    case 'character':
      return 'NPC'
    case 'item':
      return 'Item'
    case 'player':
      return 'Player'
    default:
      return 'Entity'
  }
}

function getTypeClass(entityType) {
  switch (entityType) {
    case 'npc':
    case 'character':
      return 'type-npc'
    case 'item':
      return 'type-item'
    case 'player':
      return 'type-player'
    default:
      return 'type-npc'
  }
}

export default function DetailPanel({ entityName, entityType, onClose, sendCommand, description }) {
  const actions = getActions(entityType)
  const typeLabel = getTypeLabel(entityType)
  const typeClass = getTypeClass(entityType)

  const handleAction = useCallback((action) => {
    sendCommand(action.command(entityName))
  }, [entityName, sendCommand])

  return (
    <aside className="detail-panel panel panel-decorated">
      <div className="detail-panel-header">
        <span className="cinzel detail-panel-title">INSPECT</span>
        <button className="detail-panel-close" onClick={onClose} title="Close">✕</button>
      </div>

      <div className="detail-panel-body">
        {/* Entity name */}
        <div className="detail-name-row">
          <span className="detail-name">{entityName}</span>
        </div>

        {/* Type tag */}
        <div className="detail-type-row">
          <span className={`detail-type-tag ${typeClass}`}>{typeLabel}</span>
        </div>

        {/* Description */}
        <div className="status-section-label cinzel">DESCRIPTION</div>
        <div className="detail-description">
          {description || (
            <span className="detail-desc-empty">
              No description loaded. Click "Look" to inspect.
            </span>
          )}
        </div>

        {/* Actions */}
        <div className="detail-actions">
          <div className="status-section-label cinzel">ACTIONS</div>
          {actions.map((action) => (
            <button
              key={action.label}
              className="detail-action-btn"
              onClick={() => handleAction(action)}
              title={action.command(entityName)}
            >
              <span className="detail-action-icon">{action.icon}</span>
              <span className="detail-action-label">{action.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Decorative footer */}
      <div className="detail-panel-footer">
        <span className="cinzel">✦ ─── ✦</span>
      </div>
    </aside>
  )
}
