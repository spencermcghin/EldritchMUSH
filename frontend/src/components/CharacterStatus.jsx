import './CharacterStatus.css'

function StatBar({ label, value, max, colorClass }) {
  const pct = max > 0 ? Math.max(0, Math.min(100, (value / max) * 100)) : 0
  return (
    <div className="stat-bar-row">
      <span className="stat-bar-label cinzel">{label}</span>
      <div className="stat-bar-track">
        <div className={`stat-bar-fill ${colorClass}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="stat-bar-value">
        {value !== null && max !== null ? `${value}/${max}` : '—'}
      </span>
    </div>
  )
}

function StatusTag({ label, active, className }) {
  if (!active) return null
  return (
    <div className={`status-tag ${className}`}>
      {label}
    </div>
  )
}

const EQUIP_SLOTS = [
  { key: 'rightHand', label: 'R. Hand', icon: '⚔' },
  { key: 'leftHand', label: 'L. Hand', icon: '🛡' },
  { key: 'body', label: 'Armor', icon: '◈' },
]

export default function CharacterStatus({ oobState, connectionState, onChargen, sendCommand, onWorldMap }) {
  const {
    characterName,
    body,
    totalBody,
    bleedPoints,
    deathPoints,
    av,
    statusFlags,
    equipment,
    inCombat,
  } = oobState

  const isConnected = connectionState === 'connected'

  return (
    <aside className="char-status panel panel-decorated">
      <div className="char-status-header">
        <span className="cinzel char-status-title">STATUS</span>
      </div>

      <div className="char-status-body">
        {/* Character name */}
        <div className="char-name-row">
          {characterName ? (
            <span className="char-name">{characterName}</span>
          ) : (
            <span className="char-name-empty">— unknown —</span>
          )}
        </div>

        {/* Status tags */}
        <div className="status-tags">
          <StatusTag label="⚔ IN COMBAT" active={inCombat} className="tag-combat" />
          <StatusTag label="🩸 BLEEDING" active={statusFlags?.bleeding} className="tag-bleeding" />
          <StatusTag label="☠ DYING" active={statusFlags?.dying} className="tag-dying" />
          <StatusTag label="💤 UNCONSCIOUS" active={statusFlags?.unconscious} className="tag-unconscious" />
        </div>

        {/* Stats divider */}
        <div className="status-section-label cinzel">VITALS</div>

        {/* Stat bars */}
        <div className="stat-bars">
          <StatBar
            label="BODY"
            value={body}
            max={totalBody ?? 3}
            colorClass={body !== null && body <= 1 ? 'bar-danger' : 'bar-health'}
          />
          <StatBar
            label="BLEED"
            value={bleedPoints}
            max={3}
            colorClass="bar-bleed"
          />
          <StatBar
            label="DEATH"
            value={deathPoints}
            max={3}
            colorClass="bar-death"
          />
        </div>

        {/* Armor value */}
        <div className="av-row">
          <span className="av-label cinzel">ARMOR VALUE</span>
          <span className="av-value">{av ?? 0}</span>
        </div>

        {/* Divider */}
        <div className="status-section-label cinzel">EQUIPMENT</div>

        {/* Equipment slots */}
        <div className="equip-slots">
          {EQUIP_SLOTS.map((slot) => {
            const item = equipment?.[slot.key]
            return (
              <div key={slot.key} className="equip-slot">
                <span className="equip-icon">{slot.icon}</span>
                <span className="equip-slot-label cinzel">{slot.label}</span>
                <span className={`equip-item ${item ? '' : 'equip-empty'}`}>
                  {item || 'empty'}
                </span>
              </div>
            )
          })}
        </div>

        {/* Hint when no data yet */}
        {!characterName && isConnected && (
          <div className="status-hint">
            Type <code className="hint-code">charsheet</code> to load your stats
          </div>
        )}

        {/* Quick actions */}
        {isConnected && (
          <div className="char-actions">
            <div className="status-section-label cinzel">ACTIONS</div>
            <button className="char-action-btn" onClick={() => sendCommand('charsheet')}>
              View Charsheet
            </button>
            <button className="char-action-btn chargen-btn-link" onClick={onChargen}>
              Character Builder
            </button>
            {onWorldMap && (
              <button className="char-action-btn world-map-link" onClick={onWorldMap}>
                ✦ World Map
              </button>
            )}
          </div>
        )}
      </div>

      {/* Decorative footer */}
      <div className="char-status-footer">
        <span className="cinzel">✦ ─── ✦</span>
      </div>
    </aside>
  )
}
