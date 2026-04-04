import { useState } from 'react'
import './LoginScreen.css'

const FLAVOR_LINES = [
  'Enter if you dare. The dark remembers your name.',
  'The void stares back. It has been waiting.',
  'Few return from the depths. Fewer still remain whole.',
  'Your story ends here, or begins. The darkness does not care.',
]

export default function LoginScreen({ connectionState, onConnect }) {
  const [host, setHost] = useState(import.meta.env.VITE_GAME_HOST || 'localhost')
  const [port, setPort] = useState(import.meta.env.VITE_GAME_PORT || '4002')
  const [flavorIdx] = useState(() => Math.floor(Math.random() * FLAVOR_LINES.length))

  const handleConnect = (e) => {
    e.preventDefault()
    onConnect(host, parseInt(port) || 4002)
  }

  return (
    <div className="login-screen">
      {/* Atmospheric radial vignette */}
      <div className="login-vignette" />
      {/* Rune border decoration */}
      <div className="login-rune-border" />

      <div className="login-content">
        {/* Title */}
        <div className="login-title-wrap">
          <div className="login-skull">☠</div>
          <h1 className="login-title">Eldritch MUSH</h1>
          <div className="login-subtitle">A Dark Survival Chronicle</div>
        </div>

        {/* Decorative divider */}
        <div className="login-divider">
          <span className="login-divider-text">✦ ─────── ✦ ─────── ✦</span>
        </div>

        {/* Flavor text */}
        <p className="login-flavor">{FLAVOR_LINES[flavorIdx]}</p>

        {/* Connection form */}
        <form className="login-form panel panel-decorated" onSubmit={handleConnect}>
          <div className="login-form-title">
            <span className="cinzel">ESTABLISH CONNECTION</span>
          </div>

          <div className="login-fields">
            <div className="login-field">
              <label className="login-label cinzel">HOST</label>
              <input
                className="login-input"
                type="text"
                value={host}
                onChange={(e) => setHost(e.target.value)}
                placeholder="localhost"
                autoComplete="off"
                spellCheck="false"
              />
            </div>
            <div className="login-field login-field-port">
              <label className="login-label cinzel">PORT</label>
              <input
                className="login-input"
                type="text"
                value={port}
                onChange={(e) => setPort(e.target.value)}
                placeholder="4002"
                autoComplete="off"
              />
            </div>
          </div>

          <button
            className="login-btn"
            type="submit"
            disabled={connectionState === 'connecting'}
          >
            {connectionState === 'connecting' ? (
              <span className="login-btn-text">ENTERING THE VOID...</span>
            ) : (
              <span className="login-btn-text">ENTER THE DARKNESS</span>
            )}
          </button>

          {connectionState === 'disconnected' && (
            <p className="login-hint">
              After connecting, type{' '}
              <code className="login-code">connect &lt;username&gt; &lt;password&gt;</code>
              {' '}in the command line to log in to your account.
            </p>
          )}
        </form>

        {/* Footer runes */}
        <div className="login-runes">
          ᚠ ᚢ ᚦ ᚨ ᚱ ᚲ ᚷ ᚹ ᚺ ᚾ ᛁ ᛃ ᛇ ᛈ ᛉ ᛊ ᛏ ᛒ ᛖ ᛗ ᛚ ᛜ ᛞ ᛟ
        </div>
      </div>
    </div>
  )
}
