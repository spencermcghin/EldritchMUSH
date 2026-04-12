import { useRef, useState, useCallback, useEffect } from 'react'
import { useEvennia } from './hooks/useEvennia'
import LoginScreen from './components/LoginScreen'
import CharacterSelect from './components/CharacterSelect'
import GameOutput from './components/GameOutput'
import CombatTracker from './components/CombatTracker'
import CommandSidebar from './components/CommandSidebar'
import CharacterStatus from './components/CharacterStatus'
import DetailPanel from './components/DetailPanel'
import ContextMenu from './components/ContextMenu'
import CommandInput from './components/CommandInput'
import ChargenWizard from './components/ChargenWizard'
import RoomView from './components/RoomView'
import WorldMapModal from './components/WorldMapModal'
import EquipModal from './components/EquipModal'
import CommandPrompt from './components/CommandPrompt'
import { PROMPTS, getPromptForCommand } from './data/commandPrompts'
import './App.css'

const NPC_CONTEXT_ITEMS = (name) => [
  { label: 'Look', icon: '👁', action: `look ${name}` },
  { label: 'Attack', icon: '⚔', action: `strike ${name}` },
  { label: 'Whisper', icon: '💬', action: 'whisper', kind: 'prompt', target: name },
  { label: 'Follow', icon: '🚶', action: `follow ${name}` },
]

const ITEM_CONTEXT_ITEMS = (name) => [
  { label: 'Look', icon: '👁', action: `look ${name}` },
  { label: 'Get', icon: '✋', action: `get ${name}` },
  { label: 'Drop', icon: '↓', action: `drop ${name}` },
  { label: 'Examine', icon: '🔍', action: `examine ${name}` },
]

const EXIT_CONTEXT_ITEMS = (dir) => [
  { label: `Go ${dir}`, icon: '🚪', action: dir },
]

function App() {
  const { connectionState, messages, oobState, latency, sendCommand, connect, disconnect, exitChargen, enterChargen, clearLastCharCreate } =
    useEvennia()

  const inputRef = useRef(null)

  // Auto-connect after OAuth redirect: when the page loads, ask the
  // backend whether we already have a Django session. If so, skip the
  // LoginScreen entirely and open the WebSocket — Evennia will see the
  // csessid and auto-puppet the player's character.
  const autoConnectAttemptedRef = useRef(false)
  useEffect(() => {
    if (autoConnectAttemptedRef.current) return
    if (connectionState !== 'disconnected') return
    autoConnectAttemptedRef.current = true
    fetch('/api/webclient_session/', { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data && data.authenticated) {
          const host = import.meta.env.VITE_GAME_HOST || window.location.hostname || 'localhost'
          const port = parseInt(
            import.meta.env.VITE_GAME_PORT ||
              window.location.port ||
              (window.location.protocol === 'https:' ? '443' : '80')
          )
          connect(host, port)
        }
      })
      .catch(() => { /* endpoint not deployed yet — show LoginScreen */ })
  }, [connectionState, connect])

  // Entity detail panel state
  const [selectedEntity, setSelectedEntity] = useState(null)
  // selectedEntity: { name: string, type: 'character'|'item'|'player' } or null

  // Context menu state
  const [contextMenu, setContextMenu] = useState(null)
  // contextMenu: { x: number, y: number, items: array } or null

  // Entity description captured from look commands
  const [entityDescription, setEntityDescription] = useState('')
  // Index where we last sent a look command — used to capture the next response
  const lookWatcherRef = useRef(null)
  // lookWatcherRef.current: { entityName: string, fromIndex: number } or null

  // World map modal
  const [worldMapOpen, setWorldMapOpen] = useState(false)

  // Equip modal
  const [equipOpen, setEquipOpen] = useState(false)

  // Friendly command-input prompt modal
  const [commandPrompt, setCommandPrompt] = useState(null)
  // commandPrompt: { title, label, placeholder, icon, submitLabel, buildCommand } or null

  const openPrompt = useCallback((promptDef) => {
    setCommandPrompt(promptDef)
  }, [])

  const closePrompt = useCallback(() => {
    setCommandPrompt(null)
  }, [])

  const handlePromptSubmit = useCallback((finalCommand) => {
    sendCommand(finalCommand)
    setCommandPrompt(null)
  }, [sendCommand])

  const injectCommand = (text) => {
    if (inputRef.current) {
      inputRef.current.setValue(text)
      inputRef.current.focus()
    }
  }

  const lookTimeoutRef = useRef(null)

  const handleEntityClick = useCallback((name, type) => {
    setSelectedEntity({ name, type })
    setEntityDescription('')
    // Mark the current message index — anything new after this is the look response.
    // +1 to skip the echo message that sendCommand adds synchronously.
    lookWatcherRef.current = { entityName: name, fromIndex: messages.length + 1 }
    sendCommand(`look ${name}`)
    // After 1.5s, stop accumulating — clear the watcher so the effect
    // stops re-running. If nothing was captured, show a fallback.
    if (lookTimeoutRef.current) clearTimeout(lookTimeoutRef.current)
    lookTimeoutRef.current = setTimeout(() => {
      if (lookWatcherRef.current) {
        lookWatcherRef.current = null
        setEntityDescription((prev) => prev || 'No description available.')
      }
    }, 1500)
  }, [sendCommand, messages.length])

  // Watch for the entity look response and capture it as description.
  // Evennia sends the look response as MULTIPLE separate text messages
  // (name, description, level, value, durability — each as its own
  // frame). We accumulate all non-system messages that arrive after
  // the look command until the 2-second timeout fires, then combine
  // them into a single description string.
  useEffect(() => {
    const watcher = lookWatcherRef.current
    if (!watcher) return
    if (messages.length <= watcher.fromIndex) return

    const parts = []
    const namePattern = watcher.entityName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

    for (let i = watcher.fromIndex; i < messages.length; i++) {
      const msg = messages[i]
      if (!msg || msg.type === 'system') continue
      const raw = (msg.content || '').replace(/<[^>]*>/g, '').trim()
      if (!raw) continue

      let cleaned = raw
        // Strip "EntityName(#id)" prefix
        .replace(new RegExp(`^${namePattern}(-\\d+)?\\s*\\(#\\d+\\)\\s*`, 'i'), '')
        .replace(/^[A-Za-z][^\n]{0,40}\(#\d+\)\s*/, '')
      // Strip entity name without (#id)
      cleaned = cleaned.replace(new RegExp(`^${namePattern}(-\\d+)?\\s*`, 'i'), '')
      // Fix concatenated text joins
      cleaned = cleaned
        .replace(/([a-z])([A-Z])/g, '$1\n$2')
        .replace(/(\.)([A-Z])/g, '$1\n$2')
        .replace(/(\d)([A-Z])/g, '$1\n$2')
      cleaned = cleaned.trim()
      if (cleaned) parts.push(cleaned)
    }

    if (parts.length > 0) {
      setEntityDescription(parts.join('\n'))
    }
  }, [messages])

  const handleEntityContextMenu = useCallback((e, name, type) => {
    e.preventDefault()
    let items
    if (type === 'character' || type === 'npc' || type === 'player') {
      items = NPC_CONTEXT_ITEMS(name)
    } else {
      items = ITEM_CONTEXT_ITEMS(name)
    }
    setContextMenu({ x: e.clientX, y: e.clientY, items })
  }, [])

  const handleExitContextMenu = useCallback((e, dir) => {
    e.preventDefault()
    setContextMenu({ x: e.clientX, y: e.clientY, items: EXIT_CONTEXT_ITEMS(dir) })
  }, [])

  const handleContextMenuSelect = useCallback((action, kind, item) => {
    if (kind === 'prompt') {
      // Look up the friendly prompt definition; for whisper/tell we need
      // a target-aware prompt factory.
      const promptKey = action
      let promptDef = null
      if (typeof PROMPTS[promptKey] === 'function' && item?.target) {
        promptDef = PROMPTS[promptKey](item.target)
      } else if (typeof PROMPTS[promptKey] === 'object') {
        promptDef = PROMPTS[promptKey]
      }
      if (promptDef) {
        setCommandPrompt(promptDef)
        return
      }
    }
    if (kind === 'inject') {
      injectCommand(action)
    } else {
      sendCommand(action)
    }
  }, [sendCommand])

  const handleContextMenuClose = useCallback(() => {
    setContextMenu(null)
  }, [])

  const handleDetailPanelClose = useCallback(() => {
    setSelectedEntity(null)
    setEntityDescription('')
    lookWatcherRef.current = null
  }, [])

  const isConnected = connectionState === 'connected'
  const isConnecting = connectionState === 'connecting'

  const statusLabel = { connected: 'CONNECTED', connecting: 'CONNECTING', disconnected: 'OFFLINE' }[connectionState]

  return (
    <div className="app-container">

      {/* ── Header ── */}
      <header className="app-header">
        <div className="app-header-title">
          <span className="skull">☠</span> Eldritch MUSH
        </div>
        <div className="app-header-rule" />
        <div className="app-header-status">
          <div className={`status-dot ${connectionState}`} />
          <span className={`status-label ${connectionState}`}>{statusLabel}</span>
          {latency !== null && isConnected && (
            <span className="status-latency">{latency}ms</span>
          )}
          {isConnected && (
            <button className="header-disconnect-btn" onClick={disconnect} title="Disconnect">✕</button>
          )}
        </div>
      </header>

      {/* ── Login ── */}
      {!isConnected && !isConnecting && (
        <LoginScreen connectionState={connectionState} onConnect={connect} />
      )}

      {/* ── Connecting ── */}
      {isConnecting && (
        <div className="app-connecting">
          <div className="app-connecting-text">Entering the void...</div>
        </div>
      )}

      {/* ── Character Select ── */}
      {/* Shown after authentication, before puppeting a character.
          Auto-dismissed when an account_info OOB event arrives confirming
          puppet success (which only happens after `ic <name>`). */}
      {isConnected && oobState.atCharacterSelect && !oobState.inChargen && (
        <CharacterSelect
          sendCommand={sendCommand}
          lastCharCreate={oobState.lastCharCreate}
          clearLastCharCreate={clearLastCharCreate}
        />
      )}

      {/* ── Chargen Wizard ── */}
      {isConnected && !oobState.atCharacterSelect && oobState.inChargen && (
        <ChargenWizard
          sendCommand={sendCommand}
          onExit={exitChargen}
          viewMode={oobState.chargenViewMode || false}
          isAdmin={oobState.isAdmin}
          characterName={oobState.characterName}
          characterSkills={oobState.characterSkills || {}}
        />
      )}

      {/* ── Main Game UI ── */}
      {isConnected && !oobState.atCharacterSelect && !oobState.inChargen && (
        <div className="app-body">
          {/* Left sidebar: commands */}
          <CommandSidebar
            availableCommands={oobState.availableCommands}
            inCombat={oobState.inCombat}
            myTurn={oobState.myTurn}
            onCommandClick={injectCommand}
            onPrompt={openPrompt}
            sendCommand={sendCommand}
            onEquip={() => setEquipOpen(true)}
          />

          {/* Center: room view on top, log + input on bottom */}
          <div className="app-main">
            <RoomView
              messages={messages}
              onCommand={sendCommand}
              onEntityClick={handleEntityClick}
              onEntityContextMenu={handleEntityContextMenu}
              onExitContextMenu={handleExitContextMenu}
            />
            {oobState.inCombat && <CombatTracker oobState={oobState} />}
            <div className="app-log-area">
              <GameOutput messages={messages} onCommand={sendCommand} />
              <CommandInput
                ref={inputRef}
                onSend={sendCommand}
                availableCommands={oobState.availableCommands}
                disabled={false}
              />
            </div>
          </div>

          {/* Right sidebar: character status or detail panel */}
          {selectedEntity ? (
            <DetailPanel
              entityName={selectedEntity.name}
              entityType={selectedEntity.type}
              onClose={handleDetailPanelClose}
              sendCommand={sendCommand}
              injectCommand={injectCommand}
              onPrompt={openPrompt}
              description={entityDescription}
            />
          ) : (
            <CharacterStatus
              oobState={oobState}
              connectionState={connectionState}
              sendCommand={sendCommand}
              onChargen={enterChargen}
              onWorldMap={() => setWorldMapOpen(true)}
            />
          )}
        </div>
      )}

      {/* Context menu overlay */}
      {contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          items={contextMenu.items}
          onSelect={handleContextMenuSelect}
          onClose={handleContextMenuClose}
        />
      )}

      {/* World map modal */}
      <WorldMapModal open={worldMapOpen} onClose={() => setWorldMapOpen(false)} />

      {/* Equip modal */}
      {equipOpen && (
        <EquipModal
          onClose={() => setEquipOpen(false)}
          sendCommand={sendCommand}
          inventoryData={oobState.inventoryData}
        />
      )}

      {/* Friendly command input prompt modal */}
      <CommandPrompt
        prompt={commandPrompt}
        onSubmit={handlePromptSubmit}
        onCancel={closePrompt}
      />

    </div>
  )
}

export default App
