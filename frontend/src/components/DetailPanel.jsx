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
  { label: 'Ask', icon: '🗣', kind: 'prompt', promptKey: 'ask' },
  { label: 'Whisper', icon: '💬', kind: 'prompt', promptKey: 'whisper' },
  { label: 'Give', icon: '🎁', kind: 'give' },
  { label: 'Attack', icon: '⚔', kind: 'send', command: (name) => `strike ${name}` },
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

export default function DetailPanel({ entityName, entityType, onClose, sendCommand, injectCommand, onPrompt, onGive, description, npcMeta, playerSilver = 0 }) {
  // Base actions per entity-type, plus any contextual actions from NPC
  // metadata (Tavyl dealer, merchant) appended at the end.
  const baseActions = getActions(entityType)
  const contextActions = []
  if (npcMeta?.isTavylDealer) {
    const stake = npcMeta.tavylStake || 1
    const canAfford = playerSilver >= stake
    contextActions.push({
      label: canAfford ? `Play Tavyl (${stake}s)` : `Play Tavyl — need ${stake}s`,
      icon: '🎴',
      kind: 'send',
      command: (name) => `tavyl sit ${name}`,
      disabled: !canAfford,
      tooltip: canAfford
        ? `Pay ${stake} silver to sit (you have ${playerSilver})`
        : `You need ${stake} silver to sit. You have ${playerSilver}.`,
    })
  }
  if (npcMeta?.isMerchant) {
    contextActions.push({
      label: 'Browse Wares', icon: '🪙', kind: 'send',
      command: (name) => `browse ${name}`,
    })
  }
  const actions = [...baseActions, ...contextActions]
  const topics = npcMeta?.topics || []

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
    if (action.kind === 'give' && onGive) {
      onGive(entityName)
      return
    }
    const text = action.command ? action.command(entityName) : ''
    if (action.kind === 'inject' && injectCommand) {
      injectCommand(text)
    } else if (text) {
      sendCommand(text)
    }
  }, [entityName, sendCommand, injectCommand, onPrompt, onGive])

  // Clicking a topic chip sends the ask directly — no intermediate
  // modal. The topic text is what gets asked verbatim.
  const handleTopicClick = useCallback((topic) => {
    if (!topic) return
    sendCommand(`ask ${entityName} = ${topic}`)
  }, [entityName, sendCommand])

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

        {/* Topic chips — only shown for NPCs with quest hooks. Each
            chip is a clickable hint at what to ask about. */}
        {topics.length > 0 && (
          <>
            <div className="status-section-label cinzel">TOPICS</div>
            <div className="detail-topics">
              {topics.map((t, i) => (
                <button
                  key={i}
                  className="detail-topic-chip"
                  onClick={() => handleTopicClick(t)}
                  title={`Ask ${displayName} about this`}
                >
                  {t}
                </button>
              ))}
            </div>
          </>
        )}

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
