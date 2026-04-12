import { useCallback } from 'react'
import { getEntityIcon } from '../data/entityIcons'
import { PROMPTS } from '../data/commandPrompts'
import './DetailPanel.css'

// Action types:
//   'send'   = fire the command immediately
//   'inject' = put it in the input box so the user can finish typing
//   'prompt' = open a friendly modal asking for input (factory key in PROMPTS)
const NPC_ACTIONS = [
  { label: 'Look', icon: '👁', kind: 'send', command: (name) => `look ${name}` },
  { label: 'Attack', icon: '⚔', kind: 'send', command: (name) => `strike ${name}` },
  { label: 'Whisper', icon: '💬', kind: 'prompt', promptKey: 'whisper' },
  { label: 'Follow', icon: '🚶', kind: 'send', command: (name) => `follow ${name}` },
]

const ITEM_ACTIONS = [
  { label: 'Look', icon: '👁', kind: 'send', command: (name) => `look ${name}` },
  { label: 'Get', icon: '✋', kind: 'send', command: (name) => `get ${name}` },
  { label: 'Drop', icon: '↓', kind: 'send', command: (name) => `drop ${name}` },
]

const PLAYER_ACTIONS = [
  { label: 'Look', icon: '👁', kind: 'send', command: (name) => `look ${name}` },
  { label: 'Attack', icon: '⚔', kind: 'send', command: (name) => `strike ${name}` },
  { label: 'Whisper', icon: '💬', kind: 'prompt', promptKey: 'whisper' },
  { label: 'Follow', icon: '🚶', kind: 'send', command: (name) => `follow ${name}` },
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

export default function DetailPanel({ entityName, entityType, onClose, sendCommand, injectCommand, onPrompt, description }) {
  const actions = getActions(entityType)
  const typeLabel = getTypeLabel(entityType)
  const typeClass = getTypeClass(entityType)
  // Strip Evennia's -N duplicate suffix (e.g. "bow-1" → "Bow")
  const displayName = entityName
    .replace(/-\d+$/, '')
    .replace(/\b\w/g, c => c.toUpperCase())
  const iconSrc = getEntityIcon(displayName, entityType)

  const handleAction = useCallback((action) => {
    if (action.kind === 'prompt' && onPrompt) {
      const factory = PROMPTS[action.promptKey]
      const promptDef = typeof factory === 'function' ? factory(entityName) : factory
      if (promptDef) {
        onPrompt(promptDef)
        return
      }
    }
    const text = action.command ? action.command(entityName) : ''
    if (action.kind === 'inject' && injectCommand) {
      injectCommand(text)
    } else if (text) {
      sendCommand(text)
    }
  }, [entityName, sendCommand, injectCommand, onPrompt])

  return (
    <aside className="detail-panel panel panel-decorated">
      <div className="detail-panel-header">
        <span className="cinzel detail-panel-title">INSPECT</span>
        <button className="detail-panel-close" onClick={onClose} title="Close">✕</button>
      </div>

      <div className="detail-panel-body">
        {/* Entity portrait */}
        {iconSrc && (
          <div className={`detail-portrait ${typeClass}`}>
            <img src={iconSrc} alt={entityName} className="detail-portrait-img" loading="lazy" />
          </div>
        )}

        {/* Entity name */}
        <div className="detail-name-row">
          <span className="detail-name">{displayName}</span>
        </div>

        {/* Type tag */}
        <div className="detail-type-row">
          <span className={`detail-type-tag ${typeClass}`}>{typeLabel}</span>
        </div>

        {/* Description */}
        <div className="status-section-label cinzel">DESCRIPTION</div>
        <div className="detail-description" style={{ whiteSpace: 'pre-line' }}>
          {description || (
            <span className="detail-desc-empty">
              Inspecting...
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
              title={action.command ? action.command(entityName) : action.label}
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
