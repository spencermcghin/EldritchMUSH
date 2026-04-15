import { useEffect } from 'react'
import './TavylModal.css'

// Card art tints by type — Pestilence in blood-red, Bonesman in
// phosphor-green, all others in wax-stamp gold.
const CARD_TINT = (type) => {
  if (type === 'pestilence') return 'card-pestilence'
  if (type === 'bonesman') return 'card-bonesman'
  return 'card-action'
}

function CardFace({ card, onClick, disabled }) {
  return (
    <button
      className={`tavyl-card ${CARD_TINT(card.type)}`}
      onClick={onClick}
      disabled={disabled}
      title={card.effect}
    >
      <div className="tavyl-card-name cinzel">{card.name.toUpperCase()}</div>
      <div className="tavyl-card-divider" />
      <div className="tavyl-card-effect">{card.effect}</div>
    </button>
  )
}

function PlayerSeat({ player }) {
  const cls = [
    'tavyl-seat',
    player.isYou ? 'is-you' : '',
    player.isDealer ? 'is-dealer' : '',
    player.alive ? '' : 'is-out',
  ].filter(Boolean).join(' ')
  return (
    <div className={cls}>
      <div className="tavyl-seat-name cinzel">{player.name}</div>
      <div className="tavyl-seat-meta">
        <span className="tavyl-seat-cards">{player.handSize} cards</span>
        {!player.alive && <span className="tavyl-seat-dead">ELIMINATED</span>}
      </div>
    </div>
  )
}

export default function TavylModal({ open, onClose, sendCommand, tavylState }) {
  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open) return null
  const state = tavylState

  if (!state) {
    return (
      <div className="tavyl-backdrop" onClick={onClose}>
        <div className="tavyl-modal" onClick={e => e.stopPropagation()}>
          <div className="tavyl-empty">
            <span className="cinzel">No active Tavyl game.</span>
            <p>
              Find a Tavyl dealer (Mab the Gambler at the Broken Oar)
              and type <code>tavyl sit mab</code> to deal yourself in.
            </p>
            <button className="tavyl-close" onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    )
  }

  const yourTurn = state.yourTurn
  const cantPlay = !yourTurn

  const handlePlay = (card) => {
    // Targeted cards prompt for target via inject; non-targeted go direct
    const targeted = ['assassin', 'trader', 'merchant']
    if (targeted.includes(card.type)) {
      // Only one opponent in 2-player game; auto-target dealer
      const opp = state.players.find(p => !p.isYou && p.alive)
      if (opp) {
        sendCommand(`tavyl play ${card.type} on ${opp.name}`)
      } else {
        sendCommand(`tavyl play ${card.type}`)
      }
    } else if (card.type === 'bonesman' || card.type === 'pestilence') {
      // Not playable voluntarily — silently no-op, the button shouldn't be enabled
      return
    } else {
      sendCommand(`tavyl play ${card.type}`)
    }
  }

  return (
    <div className="tavyl-backdrop" onClick={onClose}>
      <div className="tavyl-modal" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="tavyl-header">
          <span className="cinzel tavyl-title">TAVYL</span>
          <span className="tavyl-subtitle">at {state.dealer}'s table — stake {state.stake} silver</span>
          <button className="tavyl-close" onClick={onClose}>✕</button>
        </div>

        {/* Seats */}
        <div className="tavyl-seats">
          {state.players.map(p => <PlayerSeat key={p.id} player={p} />)}
        </div>

        {/* Table state */}
        <div className="tavyl-table-state">
          <div className="tavyl-pile">
            <div className="tavyl-pile-name cinzel">FATE</div>
            <div className="tavyl-pile-count">{state.fateDeckSize}</div>
          </div>
          <div className="tavyl-turn-indicator">
            {yourTurn ? (
              <>
                <span className="tavyl-turn-label cinzel">YOUR TURN</span>
                <span className="tavyl-turn-hint">Play a card or draw to end your turn.</span>
              </>
            ) : (
              <>
                <span className="tavyl-turn-label cinzel waiting">{state.currentPlayer}'S TURN</span>
                <span className="tavyl-turn-hint">Waiting for opponent…</span>
              </>
            )}
          </div>
          <div className="tavyl-pile">
            <div className="tavyl-pile-name cinzel">CRYPT</div>
            <div className="tavyl-pile-count">{state.cryptSize}</div>
          </div>
        </div>

        {/* Actions */}
        <div className="tavyl-actions">
          <button
            className="tavyl-action draw"
            onClick={() => sendCommand('tavyl draw')}
            disabled={cantPlay}
          >
            Draw a Card
          </button>
          <button
            className="tavyl-action pass"
            onClick={() => sendCommand('tavyl pass')}
            disabled={cantPlay}
          >
            Pass
          </button>
          <button
            className="tavyl-action leave"
            onClick={() => sendCommand('tavyl leave')}
          >
            Fold &amp; Leave
          </button>
        </div>

        {/* Hand */}
        <div className="tavyl-hand-section">
          <div className="tavyl-hand-label cinzel">YOUR HAND ({state.yourHand.length})</div>
          <div className="tavyl-hand">
            {state.yourHand.map((card, i) => (
              <CardFace
                key={`${card.type}-${i}`}
                card={card}
                onClick={() => handlePlay(card)}
                disabled={cantPlay || card.type === 'bonesman' || card.type === 'pestilence'}
              />
            ))}
            {state.yourHand.length === 0 && (
              <div className="tavyl-empty-hand">Your hand is empty.</div>
            )}
          </div>
        </div>

        {/* Log */}
        {state.log && state.log.length > 0 && (
          <div className="tavyl-log">
            <div className="tavyl-log-label cinzel">RECENT EVENTS</div>
            <div className="tavyl-log-lines">
              {state.log.slice().reverse().map((line, i) => (
                <div key={i} className="tavyl-log-line">{line}</div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
