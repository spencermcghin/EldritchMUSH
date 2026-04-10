import { useState, useEffect } from 'react'
import './LoginScreen.css'

const FLAVOR_LINES = [
  'Enter if you dare. The dark remembers your name.',
  'The void stares back. It has been waiting.',
  'Few return from the depths. Fewer still remain whole.',
  'Your story ends here, or begins. The darkness does not care.',
]

const LS_USERNAME = 'em_username'
const LS_REMEMBER = 'em_remember'

export default function LoginScreen({ connectionState, onConnect }) {
  const detectedHost = import.meta.env.VITE_GAME_HOST || window.location.hostname || 'localhost'
  const detectedPort = import.meta.env.VITE_GAME_PORT || window.location.port || (window.location.protocol === 'https:' ? '443' : '80')
  const [host, setHost] = useState(detectedHost)
  const [port, setPort] = useState(String(detectedPort))
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [remember, setRemember] = useState(true)
  const [showFallback, setShowFallback] = useState(false)
  const [flavorIdx] = useState(() => Math.floor(Math.random() * FLAVOR_LINES.length))

  // Restore last username on mount
  useEffect(() => {
    const saved = localStorage.getItem(LS_USERNAME) || ''
    const wasRemembered = localStorage.getItem(LS_REMEMBER) === '1'
    if (saved) {
      setUsername(saved)
      setRemember(wasRemembered)
      setShowFallback(true) // returning user — show creds form by default
    }
  }, [])

  const handleGoogleSignIn = () => {
    // Send the user to django-allauth's Google login URL. After OAuth
    // success, allauth redirects to "/" (the React frontend root) and
    // the Django session cookie is set. The useEvennia hook then
    // fetches the csessid and opens the WS authenticated.
    const next = encodeURIComponent(window.location.pathname || '/')
    window.location.href = `/accounts/google/login/?next=${next}`
  }

  const handleManualConnect = (e) => {
    e.preventDefault()
    if (remember && username) {
      localStorage.setItem(LS_USERNAME, username)
      localStorage.setItem(LS_REMEMBER, '1')
    } else {
      localStorage.removeItem(LS_USERNAME)
      localStorage.removeItem(LS_REMEMBER)
    }
    // Pass credentials up; useEvennia will queue a `connect user pass`
    // command once the WS opens.
    onConnect(host, parseInt(port) || 4002, { username, password })
  }

  return (
    <div className="login-screen">
      <div className="login-vignette" />
      <div className="login-rune-border" />

      <div className="login-content">
        <div className="login-title-wrap">
          <div className="login-skull">☠</div>
          <h1 className="login-title">Eldritch MUSH</h1>
          <div className="login-subtitle">A Dark Survival Chronicle</div>
        </div>

        <div className="login-divider">
          <span className="login-divider-text">✦ ─────── ✦ ─────── ✦</span>
        </div>

        <p className="login-flavor">{FLAVOR_LINES[flavorIdx]}</p>

        <div className="login-form panel panel-decorated">
          <div className="login-form-title">
            <span className="cinzel">CROSS THE THRESHOLD</span>
          </div>

          {/* Primary: Google sign-in */}
          <button
            className="login-google-btn"
            type="button"
            onClick={handleGoogleSignIn}
            disabled={connectionState === 'connecting'}
          >
            <svg className="google-g" viewBox="0 0 18 18" width="18" height="18">
              <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z"/>
              <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"/>
              <path fill="#FBBC05" d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"/>
              <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"/>
            </svg>
            <span className="login-google-text">Sign in with Google</span>
          </button>

          {/* Toggle: manual login fallback */}
          <button
            className="login-fallback-toggle"
            type="button"
            onClick={() => setShowFallback((s) => !s)}
          >
            {showFallback ? '— hide username login —' : '— sign in with username instead —'}
          </button>

          {showFallback && (
            <form className="login-fallback-form" onSubmit={handleManualConnect}>
              <div className="login-field">
                <label className="login-label cinzel">USERNAME</label>
                <input
                  className="login-input"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="your account name"
                  autoComplete="username"
                  spellCheck="false"
                />
              </div>
              <div className="login-field">
                <label className="login-label cinzel">PASSWORD</label>
                <input
                  className="login-input"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                />
              </div>

              <label className="login-remember">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                />
                <span>Remember my username on this device</span>
              </label>

              {/* Advanced: host/port for dev */}
              <details className="login-advanced">
                <summary className="login-advanced-summary">Advanced</summary>
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
              </details>

              <button
                className="login-btn"
                type="submit"
                disabled={connectionState === 'connecting' || !username || !password}
              >
                {connectionState === 'connecting' ? (
                  <span className="login-btn-text">ENTERING THE VOID...</span>
                ) : (
                  <span className="login-btn-text">ENTER THE DARKNESS</span>
                )}
              </button>
            </form>
          )}
        </div>

        <div className="login-runes">
          ᚠ ᚢ ᚦ ᚨ ᚱ ᚲ ᚷ ᚹ ᚺ ᚾ ᛁ ᛃ ᛇ ᛈ ᛉ ᛊ ᛏ ᛒ ᛖ ᛗ ᛚ ᛜ ᛞ ᛟ
        </div>
      </div>
    </div>
  )
}
