import { useEffect, useState, useCallback } from 'react'
import './QuestJournalModal.css'

function ObjectivesList({ objectives }) {
  if (!objectives || objectives.length === 0) return null
  return (
    <ul className="qj-obj-list">
      {objectives.map((o, i) => (
        <li key={i} className={`qj-obj ${o.done ? 'done' : ''}`}>
          <span className="qj-obj-tick">{o.done ? '✓' : '•'}</span>
          <span className="qj-obj-desc">{o.desc}</span>
          <span className="qj-obj-count">
            {o.current}/{o.qty}
          </span>
        </li>
      ))}
    </ul>
  )
}

function RewardLine({ rewards }) {
  if (!rewards || rewards.length === 0) return null
  return (
    <div className="qj-reward">
      <span className="qj-reward-label">Reward:</span>{' '}
      <span className="qj-reward-text">{rewards.join(', ')}</span>
    </div>
  )
}

function ActiveQuestCard({ quest, onAbandon, busyKey }) {
  const total = quest.objectives?.length || 0
  const done = (quest.objectives || []).filter(o => o.done).length
  const isBusy = busyKey === quest.key
  return (
    <div className="qj-card qj-card-active">
      <div className="qj-card-header">
        <div className="qj-card-title">{quest.title}</div>
        <div className="qj-card-progress">
          {done}/{total}
        </div>
      </div>
      {quest.outcomeLabel && (
        <div className="qj-card-outcome">Path: {quest.outcomeLabel}</div>
      )}
      {quest.giver && (
        <div className="qj-card-giver">From: {quest.giver}</div>
      )}
      {quest.description && (
        <p className="qj-card-desc">{quest.description}</p>
      )}
      <ObjectivesList objectives={quest.objectives} />
      <RewardLine rewards={quest.rewards} />
      <div className="qj-card-actions">
        <button
          className="qj-btn qj-btn-abandon"
          onClick={() => onAbandon(quest)}
          disabled={isBusy}
          title="Abandon this quest"
        >
          {isBusy ? 'Abandoning...' : 'Abandon'}
        </button>
      </div>
    </div>
  )
}

function AvailableQuestCard({ quest, onAccept, busyKey }) {
  const busyTag = quest.outcomeKey ? `${quest.key}/${quest.outcomeKey}` : quest.key
  const isBusy = busyKey === busyTag
  return (
    <div className="qj-card qj-card-available">
      <div className="qj-card-header">
        <div className="qj-card-title">
          <span className="qj-bang">[!]</span> {quest.title}
        </div>
      </div>
      {quest.outcomeLabel && (
        <div className="qj-card-outcome">Path: {quest.outcomeLabel}</div>
      )}
      {quest.giver && (
        <div className="qj-card-giver">From: {quest.giver}</div>
      )}
      {quest.outcomeDescription ? (
        <p className="qj-card-desc">{quest.outcomeDescription}</p>
      ) : quest.description ? (
        <p className="qj-card-desc">{quest.description}</p>
      ) : null}
      <ObjectivesList objectives={quest.objectives} />
      <RewardLine rewards={quest.rewards} />
      <div className="qj-card-actions">
        <button
          className="qj-btn qj-btn-accept"
          onClick={() => onAccept(quest)}
          disabled={isBusy}
        >
          {isBusy ? 'Accepting...' : 'Accept'}
        </button>
      </div>
    </div>
  )
}

function CompletedQuestRow({ quest }) {
  return (
    <div className="qj-completed-row">
      <span className="qj-completed-tick">✓</span>
      <span className="qj-completed-title">{quest.title}</span>
      {quest.outcomeLabel && (
        <span className="qj-completed-outcome">— {quest.outcomeLabel}</span>
      )}
    </div>
  )
}

export default function QuestJournalModal({ onClose, sendCommand, questLog }) {
  const [tab, setTab] = useState('active')
  const [busyKey, setBusyKey] = useState(null)
  const loading = !questLog

  // Request data on mount
  useEffect(() => {
    sendCommand('__quest_ui__')
  }, [sendCommand])

  // Re-fetch whenever the modal observes a stale state after action
  const refresh = useCallback(() => {
    sendCommand('__quest_ui__')
  }, [sendCommand])

  const handleAccept = useCallback((quest) => {
    const tag = quest.outcomeKey ? `${quest.key}/${quest.outcomeKey}` : quest.key
    setBusyKey(tag)
    const cmd = quest.outcomeKey
      ? `quest accept ${quest.title} / ${quest.outcomeKey}`
      : `quest accept ${quest.title}`
    sendCommand(cmd)
    setTimeout(() => {
      refresh()
      setBusyKey(null)
    }, 700)
  }, [sendCommand, refresh])

  const handleAbandon = useCallback((quest) => {
    if (!window.confirm(`Abandon "${quest.title}"? Progress will be lost.`)) return
    setBusyKey(quest.key)
    sendCommand(`quest abandon ${quest.title}`)
    setTimeout(() => {
      refresh()
      setBusyKey(null)
    }, 600)
  }, [sendCommand, refresh])

  const active = questLog?.active || []
  const available = questLog?.availableHere || []
  const completed = questLog?.completed || []

  return (
    <div className="qj-modal-backdrop" onClick={onClose}>
      <div className="qj-modal" onClick={e => e.stopPropagation()}>
        <div className="qj-modal-header">
          <span className="cinzel qj-modal-title">QUEST JOURNAL</span>
          <button className="qj-modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="qj-tabs">
          <button
            className={`qj-tab ${tab === 'active' ? 'active' : ''}`}
            onClick={() => setTab('active')}
          >
            Active <span className="qj-tab-count">{active.length}</span>
          </button>
          <button
            className={`qj-tab ${tab === 'available' ? 'active' : ''}`}
            onClick={() => setTab('available')}
          >
            Available Here <span className="qj-tab-count">{available.length}</span>
          </button>
          <button
            className={`qj-tab ${tab === 'completed' ? 'active' : ''}`}
            onClick={() => setTab('completed')}
          >
            Completed <span className="qj-tab-count">{completed.length}</span>
          </button>
        </div>

        <div className="qj-modal-body">
          {loading && <div className="qj-loading">Recalling your sworn oaths...</div>}

          {!loading && tab === 'active' && (
            active.length === 0 ? (
              <div className="qj-empty">No active quests. Speak to the locals.</div>
            ) : (
              active.map(q => (
                <ActiveQuestCard
                  key={q.key}
                  quest={q}
                  onAbandon={handleAbandon}
                  busyKey={busyKey}
                />
              ))
            )
          )}

          {!loading && tab === 'available' && (
            available.length === 0 ? (
              <div className="qj-empty">No quest givers in this room.</div>
            ) : (
              available.map(q => (
                <AvailableQuestCard
                  key={q.outcomeKey ? `${q.key}/${q.outcomeKey}` : q.key}
                  quest={q}
                  onAccept={handleAccept}
                  busyKey={busyKey}
                />
              ))
            )
          )}

          {!loading && tab === 'completed' && (
            completed.length === 0 ? (
              <div className="qj-empty">No completed quests yet.</div>
            ) : (
              <div className="qj-completed-list">
                {completed.map(q => (
                  <CompletedQuestRow key={q.key} quest={q} />
                ))}
              </div>
            )
          )}
        </div>

        <div className="qj-modal-footer">
          <span className="cinzel">✦ ─── ✦ ─── ✦</span>
        </div>
      </div>
    </div>
  )
}
