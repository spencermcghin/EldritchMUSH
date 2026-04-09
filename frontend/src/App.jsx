import { useRef } from 'react'
import { useEvennia } from './hooks/useEvennia'
import LoginScreen from './components/LoginScreen'
import GameOutput from './components/GameOutput'
import CombatTracker from './components/CombatTracker'
import CommandSidebar from './components/CommandSidebar'
import CharacterStatus from './components/CharacterStatus'
import CommandInput from './components/CommandInput'
import ChargenWizard from './components/ChargenWizard'
import './App.css'

function App() {
  const { connectionState, messages, oobState, latency, sendCommand, connect, disconnect } =
    useEvennia()

  const inputRef = useRef(null)

  const injectCommand = (text) => {
    if (inputRef.current) {
      inputRef.current.setValue(text)
      inputRef.current.focus()
    }
  }

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
          <div className="app-connecting-text">Entering the void…</div>
        </div>
      )}

      {/* ── Chargen Wizard ── */}
      {isConnected && oobState.inChargen && (
        <ChargenWizard
          sendCommand={sendCommand}
          onExit={() => {}}
        />
      )}

      {/* ── Main UI ── */}
      {isConnected && !oobState.inChargen && (
        <div className="app-body">
          <CommandSidebar
            availableCommands={oobState.availableCommands}
            inCombat={oobState.inCombat}
            myTurn={oobState.myTurn}
            onCommandClick={injectCommand}
          />
          <div className="app-main">
            <GameOutput messages={messages} />
            {oobState.inCombat && <CombatTracker oobState={oobState} />}
            <CommandInput
              ref={inputRef}
              onSend={sendCommand}
              availableCommands={oobState.availableCommands}
              disabled={false}
            />
          </div>
          <CharacterStatus oobState={oobState} connectionState={connectionState} />
        </div>
      )}

    </div>
  )
}

export default App
