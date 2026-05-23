import { useState, useEffect, useCallback, useRef } from 'react'
import { getEntityIcon } from '../data/entityIcons'
import './CharacterSelect.css'

// Hard upper bound on how long we'll wait for the server's
// character_created / character_create_failed OOB event before
// FALLING BACK to a list re-fetch. Railway disk-backed DB writes
// can take several seconds in the worst case, and the OOB event
// has been observed to drop on the wire occasionally — so we bumped
// this from 6s to 15s and added a re-fetch fallback that resolves
// the create silently if the character actually exists.
const CREATE_TIMEOUT_MS = 15000

/**
 * CharacterSelect — shown after the player authenticates (OAuth or
 * manual login) but before they puppet a character. Lists all
 * playable characters as rich cards with art, name, stats, and last
 * location, plus a "Create New Character" card at the end.
 *
 * Props:
 *   sendCommand: (text) => void
 *   lastCharCreate: { status, name?, reason?, code?, ts } | null
 *     - mirror of oobState.lastCharCreate, set by the server's
 *       character_created / character_create_failed OOB events.
 *   clearLastCharCreate: () => void  -- clears that mirror after we handle it.
 *   onPuppeted: () => void           -- optimistic-UI callback (optional).
 */
export default function CharacterSelect({ sendCommand, lastCharCreate, clearLastCharCreate, onPuppeted }) {
  const [characters, setCharacters] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  // Subscription state — fetched from /api/billing/status on mount.
  // `null` = not yet loaded; otherwise the JSON body of the endpoint.
  const [billing, setBilling] = useState(null)
  const [subscribing, setSubscribing] = useState(false)
  // creating == true between clicking Begin and receiving the server's
  // character_created event (or a failure / timeout). Disables the
  // submit button and shows the "Forging..." label.
  const [creating, setCreating] = useState(false)
  // Modal-local error string (validation OR server failure reason).
  // Distinct from `error` above which is for top-level fetch errors.
  const [modalError, setModalError] = useState(null)
  // Timeout that fires if the server never responds.
  const createTimeoutRef = useRef(null)
  // Snapshot of lastCharCreate.ts at the moment we started the
  // request, so we can ignore stale results from a prior attempt.
  const createStartedAtRef = useRef(0)

  const fetchCharacters = useCallback(async () => {
    setLoading(true)
    try {
      const resp = await fetch('/api/account/characters/', { credentials: 'include' })
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
      const data = await resp.json()
      if (!data.authenticated) {
        setError('You are not logged in.')
        setCharacters([])
        return []
      }
      setCharacters(data.characters || [])
      setError(null)
      // If they have zero characters, jump straight to the create form.
      if ((data.characters || []).length === 0) {
        setShowCreate(true)
      }
      return data.characters || []
    } catch (err) {
      setError(`Could not load characters: ${err.message}`)
      return []
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchCharacters()
  }, [fetchCharacters])

  // Fetch billing/subscription state. Re-fetches on mount and after
  // returning from PayPal (the return URL bounces to /?subscribed=1).
  const fetchBilling = useCallback(async () => {
    try {
      const resp = await fetch('/api/billing/status', { credentials: 'include' })
      if (!resp.ok) {
        setBilling({ error: `HTTP ${resp.status}` })
        return
      }
      setBilling(await resp.json())
    } catch (err) {
      setBilling({ error: err.message })
    }
  }, [])

  useEffect(() => {
    fetchBilling()
    // If the user just returned from PayPal approval, re-fetch shortly
    // so the webhook has a beat to update state.
    if (typeof window !== 'undefined' && /[?&]subscribed=1/.test(window.location.search)) {
      const t = setTimeout(fetchBilling, 1500)
      return () => clearTimeout(t)
    }
  }, [fetchBilling])

  const handleSubscribe = useCallback(async () => {
    if (subscribing) return
    setSubscribing(true)
    try {
      const resp = await fetch('/api/billing/create-subscription', {
        method: 'POST',
        credentials: 'include',
      })
      const body = await resp.json().catch(() => ({}))
      if (!resp.ok || !body.approval_url) {
        alert(body.error || 'Could not start subscription. Please try again later.')
        setSubscribing(false)
        return
      }
      // Redirect to PayPal-hosted approval page. PayPal will bounce
      // the user back to /api/billing/return after they approve.
      window.location.href = body.approval_url
    } catch (err) {
      alert(`Subscription error: ${err.message}`)
      setSubscribing(false)
    }
  }, [subscribing])

  // Clear pending timeout if the component unmounts mid-create.
  useEffect(() => {
    return () => {
      if (createTimeoutRef.current) clearTimeout(createTimeoutRef.current)
    }
  }, [])

  // React to charcreate result events from the server.
  useEffect(() => {
    if (!lastCharCreate) return
    // Only react to events that arrived AFTER we started the current
    // request — protects against a stale event from a previous attempt
    // that fired between unmount/remount.
    if (lastCharCreate.ts <= createStartedAtRef.current) return
    if (!creating) return

    if (createTimeoutRef.current) {
      clearTimeout(createTimeoutRef.current)
      createTimeoutRef.current = null
    }

    if (lastCharCreate.status === 'success') {
      // Server confirmed the character exists. Now puppet it. The
      // account_info OOB event from at_post_puppet will dismiss this
      // whole screen, so we don't need to navigate manually.
      sendCommand(`ic ${lastCharCreate.name}`)
      if (onPuppeted) onPuppeted({ name: lastCharCreate.name })
      // Leave `creating` true; CharacterSelect will unmount on the
      // account_info event. If puppet itself fails we'll be stuck on
      // the spinner — handled below by a fallback timeout.
      clearLastCharCreate()
    } else if (lastCharCreate.status === 'error') {
      setCreating(false)
      setModalError(lastCharCreate.reason || 'Character creation failed.')
      clearLastCharCreate()
    }
  }, [lastCharCreate, creating, sendCommand, onPuppeted, clearLastCharCreate])

  const handlePlay = useCallback((char) => {
    // Paywall: if billing says the account is paywalled, bounce to
    // the subscribe flow instead of attempting to puppet.
    if (billing?.should_be_paywalled) {
      handleSubscribe()
      return
    }
    // Under MULTISESSION_MODE=2, send `ooc` first to unpuppet any
    // currently-puppeted character, then `ic <name>` to puppet the
    // selected one. Without the `ooc`, the old character stays
    // puppeted in the world alongside the new one.
    sendCommand('ooc')
    setTimeout(() => {
      sendCommand(`ic ${char.name}`)
      if (onPuppeted) onPuppeted(char)
    }, 300)
  }, [sendCommand, onPuppeted, billing, handleSubscribe])

  const handleCreateSubmit = useCallback((e) => {
    e.preventDefault()
    if (creating) return
    const name = newName.trim()
    if (!name) return
    // Server-side rules: alpha + spaces, reasonable length.
    if (!/^[A-Za-z][A-Za-z' -]{1,29}$/.test(name)) {
      setModalError('Names use letters, spaces, hyphens, or apostrophes (2–30 chars).')
      return
    }
    setModalError(null)
    setCreating(true)
    createStartedAtRef.current = Date.now()
    // Wipe any stale result from a prior (timed-out) attempt so the
    // useEffect below can't act on it.
    if (clearLastCharCreate) clearLastCharCreate()

    sendCommand(`charcreate ${name}`)

    // Fallback: if the server never replies (lost packet, command not
    // registered, exception eaten), re-fetch the character list and
    // see if the new character actually exists. If yes — silent
    // success, dismiss the modal. If no — surface a real error.
    if (createTimeoutRef.current) clearTimeout(createTimeoutRef.current)
    createTimeoutRef.current = setTimeout(async () => {
      const chars = await fetchCharacters()
      const exists = (chars || []).some(
        c => (c.name || '').toLowerCase() === name.toLowerCase()
      )
      if (exists) {
        // Server actually created the character — the OOB event
        // just got lost on the wire. Dismiss silently and treat
        // this as success.
        setCreating(false)
        setShowCreate(false)
        setNewName('')
        setModalError(null)
      } else {
        setCreating(false)
        setModalError(
          'No response from the server. The character may not have been created — try a different name or refresh the page.'
        )
      }
    }, CREATE_TIMEOUT_MS)
  }, [newName, creating, sendCommand, fetchCharacters, clearLastCharCreate])

  const handleCloseModal = useCallback(() => {
    // Always allow Cancel — even while a create is in-flight. If the
    // server actually succeeded the character will show up on the next
    // characters refetch anyway. Previously this was gated on `creating`
    // which trapped users in hung modals when the character_created OOB
    // event dropped on the wire.
    if (createTimeoutRef.current) {
      clearTimeout(createTimeoutRef.current)
      createTimeoutRef.current = null
    }
    setCreating(false)
    setShowCreate(false)
    setNewName('')
    setModalError(null)
    // Refetch in case the create actually completed server-side before
    // we cancelled — that way the new character appears in the grid.
    fetchCharacters()
  }, [fetchCharacters])

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

        {/* Subscription banner — trial countdown, paywall, or subscribed. */}
        {billing && billing.authenticated && (
          <SubscriptionBanner billing={billing} onSubscribe={handleSubscribe} subscribing={subscribing} />
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
              onClick={() => { setShowCreate(true); setNewName(''); setModalError(null) }}
            >
              <div className="charsel-create-icon">✦</div>
              <div className="charsel-create-label">Create New Character</div>
              <div className="charsel-create-sub">Forge a new soul</div>
            </button>
          </div>
        )}

        {/* Create modal */}
        {showCreate && (
          <div className="charsel-modal-backdrop" onClick={handleCloseModal}>
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
                  onChange={(e) => { setNewName(e.target.value); if (modalError) setModalError(null) }}
                  placeholder="Aldric, Mira, Thorne..."
                  autoFocus
                  spellCheck="false"
                  maxLength={30}
                  disabled={creating}
                />
                {modalError && (
                  <div className="charsel-modal-error">{modalError}</div>
                )}
                <div className="charsel-modal-buttons">
                  <button
                    type="button"
                    className="charsel-modal-cancel"
                    onClick={handleCloseModal}
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


/**
 * SubscriptionBanner — renders the account's billing state above the
 * character grid. One of:
 *   - paywalled: "Your trial has ended. Subscribe — $5/month" + button
 *   - trialing:  "Trial: N days remaining" (and a small Subscribe link)
 *   - active:    "Subscribed — next renewal <date>"
 *   - past_due:  "Payment failed — update your payment method"
 */
function SubscriptionBanner({ billing, onSubscribe, subscribing }) {
  if (!billing) return null
  const price = billing.monthly_price_usd || '5.00'

  if (billing.should_be_paywalled) {
    return (
      <div className="charsel-sub-banner charsel-sub-paywall">
        <div className="charsel-sub-text">
          <strong>Your free trial has ended.</strong> Subscribe to keep playing — <strong>${price}/month</strong>, cancel anytime.
        </div>
        <button
          className="charsel-sub-btn"
          onClick={onSubscribe}
          disabled={subscribing}
        >
          {subscribing ? 'Redirecting…' : 'Subscribe'}
        </button>
      </div>
    )
  }
  if (billing.status === 'past_due') {
    return (
      <div className="charsel-sub-banner charsel-sub-paywall">
        <div className="charsel-sub-text">
          <strong>Payment failed.</strong> Update your payment method to keep playing.
        </div>
        <button
          className="charsel-sub-btn"
          onClick={onSubscribe}
          disabled={subscribing}
        >
          {subscribing ? 'Redirecting…' : 'Fix Payment'}
        </button>
      </div>
    )
  }
  if (billing.subscription_active) {
    const renewal = billing.renewal_at
      ? new Date(billing.renewal_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
      : null
    return (
      <div className="charsel-sub-banner charsel-sub-active">
        <div className="charsel-sub-text">
          ✓ Subscribed{renewal ? ` — next renewal ${renewal}` : ''}
        </div>
      </div>
    )
  }
  if (billing.in_trial) {
    const days = billing.trial_days_remaining
    return (
      <div className="charsel-sub-banner charsel-sub-trial">
        <div className="charsel-sub-text">
          Trial: <strong>{days}</strong> day{days === 1 ? '' : 's'} remaining
        </div>
        <button
          className="charsel-sub-btn charsel-sub-btn-quiet"
          onClick={onSubscribe}
          disabled={subscribing}
        >
          {subscribing ? 'Redirecting…' : `Subscribe — $${price}/mo`}
        </button>
      </div>
    )
  }
  return null
}
