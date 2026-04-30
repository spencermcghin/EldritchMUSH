import { useEffect, useMemo, useState } from 'react'
import './ReputationModal.css'

const REP_TIER_BUCKETS = [
  { label: 'heroic', min: 10, color: '#5fb35f' },
  { label: 'friend', min: 5, color: '#9bc46a' },
  { label: 'known', min: 1, color: '#c9b899' },
  { label: 'stranger', min: 0, color: '#888' },
  { label: 'suspect', min: -4, color: '#c08080' },
  { label: 'enemy', min: -9, color: '#aa3030' },
  { label: 'marked', min: -999, color: '#7a1c1c' },
]

function tierColor(label) {
  return (REP_TIER_BUCKETS.find(t => t.label === label) || {}).color || '#c9b899'
}

// Faction rep bar — diverging from center (0). Width and side derive
// from score, capped at ±15 for display.
function FactionBar({ faction }) {
  const score = faction.score || 0
  const cap = 15
  const pct = Math.min(Math.abs(score) / cap, 1) * 50
  const positive = score > 0
  const negative = score < 0
  return (
    <div className="rep-faction">
      <div className="rep-faction-row">
        <span className="rep-faction-name">{faction.name}</span>
        <span
          className="rep-faction-score"
          style={{ color: tierColor(faction.label) }}
        >
          {score > 0 ? `+${score}` : score} <em>({faction.label})</em>
        </span>
      </div>
      <div className="rep-faction-track">
        <div className="rep-faction-axis" />
        {negative && (
          <div
            className="rep-faction-fill rep-faction-fill-neg"
            style={{ width: `${pct}%`, right: '50%' }}
          />
        )}
        {positive && (
          <div
            className="rep-faction-fill rep-faction-fill-pos"
            style={{ width: `${pct}%`, left: '50%' }}
          />
        )}
      </div>
      {faction.blurb && (
        <div className="rep-faction-blurb">{faction.blurb}</div>
      )}
    </div>
  )
}

function NpcRow({ npc, expanded, onToggle }) {
  return (
    <div className={`rep-npc ${expanded ? 'expanded' : ''}`}>
      <button className="rep-npc-head" onClick={onToggle}>
        <span className="rep-npc-name">{npc.name}</span>
        <span
          className="rep-npc-score"
          style={{ color: tierColor(npc.label) }}
        >
          {npc.score > 0 ? `+${npc.score}` : npc.score}{' '}
          <em>({npc.label})</em>
        </span>
        <span className="rep-npc-toggle">{expanded ? '−' : '+'}</span>
      </button>
      {expanded && (
        <div className="rep-npc-body">
          {npc.lastInteracted && (
            <div className="rep-npc-meta">Last noted: {npc.lastInteracted}</div>
          )}
          {npc.memories && npc.memories.length > 0 ? (
            <ul className="rep-npc-memories">
              {npc.memories.map((m, i) => (
                <li key={i}>{m}</li>
              ))}
            </ul>
          ) : (
            <div className="rep-npc-empty">
              No specific memories — just a vague impression.
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function ReputationModal({ onClose, sendCommand, reputationData }) {
  const [expandedNpc, setExpandedNpc] = useState(null)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    sendCommand('__rep_ui__')
  }, [sendCommand])

  const factions = reputationData?.factions || []
  const npcs = reputationData?.npcs || []
  const loading = !reputationData

  const filteredNpcs = useMemo(() => {
    if (!filter) return npcs
    const f = filter.toLowerCase()
    return npcs.filter(n =>
      n.name.toLowerCase().includes(f) ||
      (n.memories || []).some(m => (m || '').toLowerCase().includes(f))
    )
  }, [npcs, filter])

  return (
    <div className="rep-modal-backdrop" onClick={onClose}>
      <div className="rep-modal" onClick={e => e.stopPropagation()}>
        <div className="rep-modal-header">
          <span className="cinzel rep-modal-title">REPUTATION</span>
          <button className="rep-modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="rep-modal-body">
          {loading && <div className="rep-loading">Listening to gossip...</div>}

          {!loading && (
            <>
              <div className="rep-section">
                <div className="rep-section-title cinzel">FACTION STANDING</div>
                {factions.length === 0 ? (
                  <div className="rep-empty">No faction ties yet.</div>
                ) : (
                  factions.map(f => <FactionBar key={f.key} faction={f} />)
                )}
              </div>

              <div className="rep-section">
                <div className="rep-section-title cinzel">PERSONAL RELATIONSHIPS</div>
                {npcs.length > 8 && (
                  <input
                    className="rep-filter"
                    placeholder="Filter by name or memory..."
                    value={filter}
                    onChange={e => setFilter(e.target.value)}
                  />
                )}
                {npcs.length === 0 ? (
                  <div className="rep-empty">No one knows your face yet.</div>
                ) : filteredNpcs.length === 0 ? (
                  <div className="rep-empty">No matches.</div>
                ) : (
                  filteredNpcs.map(n => (
                    <NpcRow
                      key={n.key}
                      npc={n}
                      expanded={expandedNpc === n.key}
                      onToggle={() =>
                        setExpandedNpc(expandedNpc === n.key ? null : n.key)
                      }
                    />
                  ))
                )}
              </div>
            </>
          )}
        </div>

        <div className="rep-modal-footer">
          <span className="cinzel">✦ ─── ✦ ─── ✦</span>
        </div>
      </div>
    </div>
  )
}
