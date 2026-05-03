import { useCallback } from 'react'
import { PROMPTS } from '../data/commandPrompts'
import './ActionToolbar.css'

/**
 * ActionToolbar — bottom-of-screen contextual action bar for the
 * currently-selected entity. Sits above the 3 entity columns and the
 * command input, mirroring the action toolbars common in Diablo /
 * Dragon Age / Pillars of Eternity bottom HUDs.
 *
 * Shows the entity name + a row of action buttons whose set is
 * type-specific (NPC vs. item vs. PC). Click an action to fire the
 * corresponding command. The toolbar collapses to a thin tip-line
 * when no entity is selected so it doesn't waste vertical space.
 *
 * Inspect / Description / Topics live in the modal version of
 * DetailPanel — this bar is for actions only.
 */

const NPC_ACTIONS = [
  { label: 'Look', icon: '👁', kind: 'send', cmd: (n) => `look ${n}` },
  { label: 'Ask', icon: '🗣', kind: 'prompt', promptKey: 'ask' },
  { label: 'Whisper', icon: '💬', kind: 'prompt', promptKey: 'whisper' },
  { label: 'Give', icon: '🎁', kind: 'give' },
  { label: 'Attack', icon: '⚔', kind: 'send', cmd: (n) => `strike ${n}` },
  { label: 'Follow', icon: '🚶', kind: 'send', cmd: (n) => `follow ${n}` },
]

const ITEM_ACTIONS = [
  { label: 'Look', icon: '👁', kind: 'send', cmd: (n) => `look ${n}` },
  { label: 'Get', icon: '✋', kind: 'send', cmd: (n) => `get ${n}` },
  { label: 'Drop', icon: '↓', kind: 'send', cmd: (n) => `drop ${n}` },
]

const PLAYER_ACTIONS = [
  { label: 'Look', icon: '👁', kind: 'send', cmd: (n) => `look ${n}` },
  { label: 'Whisper', icon: '💬', kind: 'prompt', promptKey: 'whisper' },
  { label: 'Follow', icon: '🚶', kind: 'send', cmd: (n) => `follow ${n}` },
  { label: 'Attack', icon: '⚔', kind: 'send', cmd: (n) => `strike ${n}` },
]

function actionsForType(type) {
  if (type === 'item') return ITEM_ACTIONS
  if (type === 'player') return PLAYER_ACTIONS
  return NPC_ACTIONS // npc / character / default
}

export default function ActionToolbar({
  entity,
  npcMeta,
  playerSilver = 0,
  sendCommand,
  onPrompt,
  onGive,
  onInspect,
  onClose,
}) {
  const handleAction = useCallback((action) => {
    if (!entity) return
    if (action.kind === 'prompt' && onPrompt) {
      const factory = PROMPTS[action.promptKey]
      const promptDef = typeof factory === 'function' ? factory(entity.name) : factory
      if (promptDef) {
        onPrompt(promptDef)
        return
      }
    }
    if (action.kind === 'give' && onGive) {
      onGive(entity.name)
      return
    }
    const text = action.cmd ? action.cmd(entity.name) : ''
    if (text) sendCommand(text)
  }, [entity, sendCommand, onPrompt, onGive])

  if (!entity) {
    return (
      <div className="action-toolbar action-toolbar-empty">
        <span className="action-toolbar-hint">
          Click a character or item to see actions
        </span>
      </div>
    )
  }

  const actions = [...actionsForType(entity.type)]

  // Contextual extras pulled from the NPC's room metadata.
  if ((entity.type === 'npc' || entity.type === 'character') && npcMeta?.isMerchant) {
    actions.push({
      label: 'Browse', icon: '🪙', kind: 'send',
      cmd: (n) => `browse ${n}`,
    })
  }
  if ((entity.type === 'npc' || entity.type === 'character') && npcMeta?.isTavylDealer) {
    const stake = npcMeta.tavylStake || 1
    const canAfford = playerSilver >= stake
    actions.push({
      label: canAfford ? `Tavyl (${stake}s)` : `Tavyl ${stake}s`,
      icon: '🎴',
      kind: 'send',
      cmd: (n) => `tavyl sit ${n}`,
      disabled: !canAfford,
    })
  }

  // Strip Evennia's -N duplicate suffix and Title-case for display.
  const displayName = entity.name
    .replace(/-\d+$/, '')
    .replace(/\b\w/g, (c) => c.toUpperCase())

  const typeLabel = entity.type === 'item'
    ? 'ITEM'
    : entity.type === 'player'
      ? 'PLAYER'
      : 'NPC'

  return (
    <div className={`action-toolbar action-toolbar-${entity.type}`}>
      <div className="action-toolbar-target">
        <span className={`action-toolbar-type type-${entity.type}`}>
          {typeLabel}
        </span>
        <span className="action-toolbar-name">{displayName}</span>
        {onInspect && (
          <button
            className="action-toolbar-inspect"
            onClick={onInspect}
            title="Open full inspect modal"
          >
            ⓘ Inspect
          </button>
        )}
      </div>
      <div className="action-toolbar-actions">
        {actions.map((action) => (
          <button
            key={action.label}
            className={`action-toolbar-btn ${action.disabled ? 'disabled' : ''}`}
            onClick={() => !action.disabled && handleAction(action)}
            disabled={action.disabled}
            title={action.cmd ? action.cmd(entity.name) : action.label}
          >
            <span className="action-toolbar-icon">{action.icon}</span>
            <span className="action-toolbar-label">{action.label}</span>
          </button>
        ))}
      </div>
      {onClose && (
        <button
          className="action-toolbar-close"
          onClick={onClose}
          title="Deselect"
        >
          ✕
        </button>
      )}
    </div>
  )
}
