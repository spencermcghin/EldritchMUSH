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

export default function CharacterStatus({ oobState, connectionState, onChargen, sendCommand, onWorldMap, onCharSheet, onSwitchCharacter, onAdmin, onQuestJournal, onReputation }) {
  const {
    characterName,
    body,
    totalBody,
    bleedPoints,
    deathPoints,
    av,
    purse,
    statusFlags,
    equipment,
    inCombat,
  } = oobState

  const silver = purse?.silver ?? 0
  const gold = purse?.gold ?? 0
  const copper = purse?.copper ?? 0

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

        {/* Purse */}
        <div className="status-section-label cinzel">PURSE</div>
        <div className="purse-row">
          <span className="coin coin-gold" title={`${gold} gold`}>
            <span className="coin-amt">{gold}</span>
            <span className="coin-label">gold</span>
          </span>
          <span className="coin coin-silver" title={`${silver} silver`}>
            <span className="coin-amt">{silver}</span>
            <span className="coin-label">silver</span>
          </span>
          <span className="coin coin-copper" title={`${copper} copper`}>
            <span className="coin-amt">{copper}</span>
            <span className="coin-label">copper</span>
          </span>
        </div>

        {/* Divider */}
        <div className="status-section-label cinzel">EQUIPMENT</div>

        {/* Equipment slots — click an equipped item to unequip */}
        <div className="equip-slots">
          {EQUIP_SLOTS.map((slot) => {
            const rawItem = equipment?.[slot.key]
            // Strip brackets/parens and #id that Evennia may include
            const item = rawItem
              ? rawItem.replace(/^\[|\]$/g, '').replace(/\(#\d+\)/, '').trim()
              : null
            return (
              <div key={slot.key} className={`equip-slot ${item ? 'has-item' : ''}`}>
                <span className="equip-icon">{slot.icon}</span>
                <span className="equip-slot-label cinzel">{slot.label}</span>
                {item ? (
                  <button
                    className="equip-item-btn"
                    onClick={() => sendCommand(`unequip ${item}`)}
                    title={`Unequip ${item}`}
                  >
                    {item} <span className="unequip-x">✕</span>
                  </button>
                ) : (
                  <span className="equip-item equip-empty">empty</span>
                )}
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
            <button className="char-action-btn" onClick={onCharSheet || (() => sendCommand('charsheet'))}>
              View Charsheet
            </button>
            {onQuestJournal && (
              <button className="char-action-btn" onClick={onQuestJournal}>
                Quest Journal
              </button>
            )}
            {onReputation && (
              <button className="char-action-btn" onClick={onReputation}>
                Reputation
              </button>
            )}
            <button className="char-action-btn chargen-btn-link" onClick={onChargen}>
              Character Builder
            </button>
            {onSwitchCharacter && (
              <button className="char-action-btn" onClick={onSwitchCharacter}>
                Switch Character
              </button>
            )}
            {onWorldMap && (
              <button className="char-action-btn world-map-link" onClick={onWorldMap}>
                ✦ World Map
              </button>
            )}
            {onAdmin && (
              <button className="char-action-btn admin-link" onClick={onAdmin}>
                Admin Dashboard
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
