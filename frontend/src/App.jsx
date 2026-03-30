import { useRef, useState } from 'react'
import { useEvennia } from './hooks/useEvennia'
import LoginScreen from './components/LoginScreen'
import GameOutput from './components/GameOutput'
import CombatTracker from './components/CombatTracker'
import CommandSidebar from './components/CommandSidebar'
import CharacterStatus from './components/CharacterStatus'
import CommandInput from './components/CommandInput'
import './App.css'

function App() {
  const { connectionState, messages, oobState, latency, sendCommand, connect, disconnect } =
    useEvennia()

  // Ref for CommandInput — so sidebar can inject commands
  const inputRef = useRef(null)

  const injectCommand = (text) => {
    if (inputRef.current) {
      inputRef.current.setValue(text)
      inputRef.current.focus()
    }
  }

  const isConnected = connectionState === 'connected'

  const statusLabel = {
    connected: 'CONNECTED',
    connecting: 'CONNECTING',
    disconnected: 'OFFLINE',
  }[connectionState]

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="app-header-title">
          <span className="skull">☠</span>
          Eldritch MUSH
        </div>
        <div className="app-header-rule" />
        <div className="app-header-status">
          <div className={`status-dot ${connectionState}`} />
          <span className={`status-label ${connectionState}`}>{statusLabel}</span>
          {latency !== null && isConnected && (
            <span className="status-latency">{latency}ms</span>
          )}
          {isConnected && (
            <button
              className="header-disconnect-btn"
              onClick={disconnect}
              title="Disconnect"
            >
              ✕
            </button>
          )}
        </div>
      </header>

      {/* Body */}
      {!isConnected && connectionState !== 'connecting' ? (
        <LoginScreen
          connectionState={connectionState}
          onConnect={connect}
        />
      ) : (
        <div className="app-body">
          {/* Left: Command Sidebar */}
          <CommandSidebar
            availableCommands={oobState.availableCommands}
            inCombat={oobState.inCombat}
            myTurn={oobState.myTurn}
            onCommandClick={injectCommand}
          />

          {/* Center: Game Output + Input */}
          <div className="app-main">
            <GameOutput messages={messages} inCombat={oobState.inCombat} />
            {oobState.inCombat && (
              <CombatTracker
                oobState={oobState}
              />
            )}
            <CommandInput
              ref={inputRef}
              onSend={sendCommand}
              availableCommands={oobState.availableCommands}
              disabled={!isConnected}
            />
          </div>

          {/* Right: Character Status */}
          <CharacterStatus oobState={oobState} connectionState={connectionState} />
        </div>
      )}

      {/* Connecting overlay */}
      {connectionState === 'connecting' && (
        <div className="app-body">
          <div style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--accent-gold)',
            fontFamily: "'Cinzel', serif",
            fontSize: '18px',
            letterSpacing: '2px',
            flexDirection: 'column',
            gap: '16px',
          }}>
            <div style={{ animation: 'glow-gold 1.5s infinite' }}>Connecting to the void...</div>
            <div style={{ fontSize: '12px', color: 'var(--text-aged)', fontFamily: "'Share Tech Mono', monospace" }}>
              Establishing connection
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
