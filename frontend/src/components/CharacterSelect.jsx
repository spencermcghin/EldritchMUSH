import { useState, useEffect, useCallback } from 'react'
import { getEntityIcon } from '../data/entityIcons'
import './CharacterSelect.css'

/**
 * CharacterSelect — shown after the player authenticates (OAuth or
 * manual login) but before they puppet a character. Lists all
 * playable characters as rich cards with art, name, stats, and last
 * location, plus a "Create New Character" card at the end.
 *
 * Props:
 *   sendCommand: (text) => void
 *   onPuppeted: () => void  -- called when the player picks a character
 *                              (for optimistic UI updates)
 */
export default function CharacterSelect({ sendCommand, onPuppeted }) {
  const [characters, setCharacters] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [creating, setCreating] = useState(false)

  const fetchCharacters = useCallback(async () => {
    setLoading(true)
    try {
      const resp = await fetch('/api/account/characters/', { credentials: 'include' })
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
      const data = await resp.json()
      if (!data.authenticated) {
        setError('You are not logged in.')
        setCharacters([])
      } else {
        setCharacters(data.characters || [])
        setError(null)
        // If they have zero characters, jump straight to the create form.
        if ((data.characters || []).length === 0) {
          setShowCreate(true)
        }
      }
    } catch (err) {
      setError(`Could not load characters: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchCharacters()
  }, [fetchCharacters])

  const handlePlay = useCallback((char) => {
    sendCommand(`ic ${char.name}`)
    if (onPuppeted) onPuppeted(char)
  }, [sendCommand, onPuppeted])

  const handleCreateSubmit = useCallback((e) => {
    e.preventDefault()
    const name = newName.trim()
    if (!name) return
    // Server-side rules: alpha + spaces, reasonable length
    if (!/^[A-Za-z][A-Za-z' -]{1,29}$/.test(name)) {
      setError('Names use letters, spaces, hyphens, or apostrophes (2–30 chars).')
      return
    }
    setError(null)
    setCreating(true)
    // charcreate creates the character; ic puppets it. The custom
    // CmdCharCreate places the new char in the ChargenRoom so the
    // wizard fires after ic.
    sendCommand(`charcreate ${name}`)
    // Brief delay so the create completes before puppet — Evennia
    // returns the success message before ic resolves anyway.
    setTimeout(() => {
      sendCommand(`ic ${name}`)
      if (onPuppeted) onPuppeted({ name })
    }, 300)
  }, [newName, sendCommand, onPuppeted])

  return (
    <div className="charsel-screen">
      <div className="charsel-vignette" />

      <div className="charsel-content">
        <div className="charsel-header">
          <h1 className="charsel-title">CHOOSE YOUR VESSEL</h1>
          <div className="charsel-divider">✦ ─────── ✦ ─────── ✦</div>
          <p className="charsel-flavor">
            The dark holds many lives. Pick one — or forge a new one from the void.
          </p>
        </div>

        {loading && (
          <div className="charsel-loading">Reading the threads of fate...</div>
        )}

        {error && (
          <div className="charsel-error">{error}</div>
        )}

        {!loading && (
          <div className="charsel-grid">
            {characters.map((char) => (
              <CharacterCard key={char.dbref} char={char} onPlay={() => handlePlay(char)} />
            ))}

            {/* Create New Character card */}
            <button
              className="charsel-card charsel-card-create"
              type="button"
              onClick={() => { setShowCreate(true); setNewName('') }}
            >
              <div className="charsel-create-icon">✦</div>
              <div className="charsel-create-label">Create New Character</div>
              <div className="charsel-create-sub">Forge a new soul</div>
            </button>
          </div>
        )}

        {/* Create modal */}
        {showCreate && (
          <div className="charsel-modal-backdrop" onClick={() => !creating && setShowCreate(false)}>
            <div className="charsel-modal panel panel-decorated" onClick={(e) => e.stopPropagation()}>
              <div className="charsel-modal-header">
                <span className="cinzel">NAME YOUR CHARACTER</span>
              </div>
              <form className="charsel-modal-body" onSubmit={handleCreateSubmit}>
                <p className="charsel-modal-flavor">
                  What name does this soul carry into the dark?
                </p>
                <input
                  className="charsel-modal-input"
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Aldric, Mira, Thorne..."
                  autoFocus
                  spellCheck="false"
                  maxLength={30}
                  disabled={creating}
                />
                <div className="charsel-modal-buttons">
                  <button
                    type="button"
                    className="charsel-modal-cancel"
                    onClick={() => setShowCreate(false)}
                    disabled={creating}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="charsel-modal-submit"
                    disabled={creating || !newName.trim()}
                  >
                    {creating ? 'Forging...' : 'Begin'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function CharacterCard({ char, onPlay }) {
  const portrait = getEntityIcon(char.name, 'character')
  const created = char.last_played ? new Date(char.last_played).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : null

  return (
    <button className="charsel-card" type="button" onClick={onPlay}>
      <div className="charsel-portrait">
        {portrait ? (
          <img src={portrait} alt={char.name} loading="lazy" />
        ) : (
          <div className="charsel-portrait-empty">☠</div>
        )}
      </div>
      <div className="charsel-card-name cinzel">{char.name}</div>
      {char.archetype && (
        <div className="charsel-card-archetype">{char.archetype}</div>
      )}
      <div className="charsel-card-stats">
        <div className="charsel-stat">
          <span className="charsel-stat-label">BODY</span>
          <span className="charsel-stat-value">{char.body}<span className="charsel-stat-max">/{char.total_body}</span></span>
        </div>
        <div className="charsel-stat">
          <span className="charsel-stat-label">AV</span>
          <span className="charsel-stat-value">{char.av}</span>
        </div>
      </div>
      <div className="charsel-card-location">
        <span className="charsel-loc-icon">📍</span> {char.location}
      </div>
      {created && (
        <div className="charsel-card-created">Born {created}</div>
      )}
      {char.in_chargen && (
        <div className="charsel-card-chargen-tag">UNFINISHED</div>
      )}
      <div className="charsel-card-play">PLAY</div>
    </button>
  )
}
