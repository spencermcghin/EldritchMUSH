import { useState } from 'react'
import './VerifyEmailBanner.css'

// Shown to unverified password players after they enter the game. AI NPC
// chat needs a verified email (or a Google sign-in); until then NPCs give
// short stock replies. The button sends the in-game `verify` command,
// whose reply appears in the game output.
export default function VerifyEmailBanner({ emailOnFile, sendCommand }) {
  const [dismissed, setDismissed] = useState(false)
  const [requested, setRequested] = useState(false)
  const [email, setEmail] = useState('')

  if (dismissed) return null

  const send = (e) => {
    e.preventDefault()
    if (emailOnFile) {
      sendCommand('verify')
    } else {
      const addr = email.trim()
      if (!addr) return
      sendCommand(`verify ${addr}`)
    }
    setRequested(true)
  }

  return (
    <div className="verify-banner" role="status">
      <button
        type="button"
        className="verify-banner-close"
        aria-label="Dismiss"
        onClick={() => setDismissed(true)}
      >
        ×
      </button>
      <div className="verify-banner-text">
        NPCs only give short stock replies until your email is verified.
      </div>
      {requested ? (
        <div className="verify-banner-done">
          Link requested. Check your inbox and spam folder.
        </div>
      ) : (
        <form className="verify-banner-form" onSubmit={send}>
          {!emailOnFile && (
            <input
              type="email"
              className="verify-banner-input"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              aria-label="Email address"
              required
            />
          )}
          <button type="submit" className="verify-banner-button">
            Send me a verification link
          </button>
        </form>
      )}
    </div>
  )
}
