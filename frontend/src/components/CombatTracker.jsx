import './CombatTracker.css'

const EVENT_ICONS = {
  hit: '⚔',
  miss: '✕',
  bleed: '🩸',
  dying: '☠',
  disengage: '↩',
  start: '⚡',
  end: '◼',
}

function HpBar({ hp }) {
  const pct = Math.max(0, Math.min(100, hp ?? 100))
  const cls =
    pct > 60 ? 'hp-high' : pct > 30 ? 'hp-mid' : 'hp-low'
  return (
    <div className="hp-bar-track">
      <div className={`hp-bar-fill ${cls}`} style={{ width: `${pct}%` }} />
    </div>
  )
}

export default function CombatTracker({ oobState }) {
  const { combatTurnOrder, combatantHp, combatLog, myTurn, characterName } = oobState
  const recentLog = combatLog.slice(0, 3)

  return (
    <div className="combat-tracker panel">
      <div className="combat-tracker-header">
        <span className="combat-active-dot" />
        <span className="combat-tracker-title cinzel">COMBAT ACTIVE</span>
        {myTurn && (
          <span className="combat-your-turn">YOUR TURN</span>
        )}
      </div>

      {/* Turn order */}
      <div className="combat-turn-list">
        {combatTurnOrder.length === 0 && (
          <div className="combat-empty">Awaiting turn data...</div>
        )}
        {combatTurnOrder.map((name, idx) => {
          const hp = combatantHp[name] ?? 100
          const isCurrent = idx === 0
          const isDead = hp <= 0
          const isMe = name === characterName
          return (
            <div
              key={name}
              className={`combat-combatant ${isCurrent ? 'current-turn' : ''} ${isDead ? 'dead' : ''} ${isMe ? 'is-me' : ''}`}
            >
              <span className="combat-turn-arrow">{isCurrent ? '→' : `${idx + 1}`}</span>
              <span className="combat-combatant-name">{name}{isMe ? ' (you)' : ''}</span>
              <HpBar hp={hp} />
              <span className="combat-hp-pct">{Math.round(hp)}%</span>
            </div>
          )
        })}
      </div>

      {/* Recent event feed */}
      {recentLog.length > 0 && (
        <div className="combat-log">
          {recentLog.map((entry) => (
            <div key={entry.id} className={`combat-log-entry entry-${entry.type}`}>
              <span className="combat-log-icon">{EVENT_ICONS[entry.type] || '•'}</span>
              <span className="combat-log-text">{entry.text}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
