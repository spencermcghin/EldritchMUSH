import { useRef, useState, useCallback } from 'react'
import { useEvennia } from './hooks/useEvennia'
import LoginScreen from './components/LoginScreen'
import GameOutput from './components/GameOutput'
import CombatTracker from './components/CombatTracker'
import CommandSidebar from './components/CommandSidebar'
import CharacterStatus from './components/CharacterStatus'
import DetailPanel from './components/DetailPanel'
import ContextMenu from './components/ContextMenu'
import CommandInput from './components/CommandInput'
import ChargenWizard from './components/ChargenWizard'
import RoomView from './components/RoomView'
import './App.css'

const NPC_CONTEXT_ITEMS = (name) => [
  { label: 'Look', icon: '👁', action: `look ${name}` },
  { label: 'Attack', icon: '⚔', action: `strike ${name}` },
  { label: 'Talk', icon: '💬', action: `say to ${name}` },
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
  const { connectionState, messages, oobState, latency, sendCommand, connect, disconnect, exitChargen, enterChargen } =
    useEvennia()

  const inputRef = useRef(null)

  // Entity detail panel state
  const [selectedEntity, setSelectedEntity] = useState(null)
  // selectedEntity: { name: string, type: 'character'|'item'|'player' } or null

  // Context menu state
  const [contextMenu, setContextMenu] = useState(null)
  // contextMenu: { x: number, y: number, items: array } or null

  // Entity description captured from look commands
  const [entityDescription, setEntityDescription] = useState('')

  const injectCommand = (text) => {
    if (inputRef.current) {
      inputRef.current.setValue(text)
      inputRef.current.focus()
    }
  }

  const handleEntityClick = useCallback((name, type) => {
    setSelectedEntity({ name, type })
    setEntityDescription('')
    sendCommand(`look ${name}`)
  }, [sendCommand])

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

  const handleContextMenuSelect = useCallback((action) => {
    sendCommand(action)
  }, [sendCommand])

  const handleContextMenuClose = useCallback(() => {
    setContextMenu(null)
  }, [])

  const handleDetailPanelClose = useCallback(() => {
    setSelectedEntity(null)
    setEntityDescription('')
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

      {/* ── Chargen Wizard ── */}
      {isConnected && oobState.inChargen && (
        <ChargenWizard
          sendCommand={sendCommand}
          onExit={exitChargen}
        />
      )}

      {/* ── Main Game UI ── */}
      {isConnected && !oobState.inChargen && (
        <div className="app-body">
          {/* Left sidebar: commands */}
          <CommandSidebar
            availableCommands={oobState.availableCommands}
            inCombat={oobState.inCombat}
            myTurn={oobState.myTurn}
            onCommandClick={injectCommand}
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
              description={entityDescription}
            />
          ) : (
            <CharacterStatus
              oobState={oobState}
              connectionState={connectionState}
              sendCommand={sendCommand}
              onChargen={enterChargen}
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

    </div>
  )
}

export default App
