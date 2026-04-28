import { useEffect, useState } from 'react'
import './QuestToasts.css'

// Celebratory summary toast when a quest finishes. Shows title,
// chosen outcome, reward line (silver + items), and faction rep deltas.
// Stays on-screen a little longer than the accepted toast.
export default function QuestCompletedToast({ quest }) {
  const [visible, setVisible] = useState(false)
  const [current, setCurrent] = useState(null)

  useEffect(() => {
    if (!quest || !quest.ts) return
    setCurrent(quest)
    setVisible(true)
    const hideTimer = setTimeout(() => setVisible(false), 6500)
    const clearTimer = setTimeout(() => setCurrent(null), 7000)
    return () => {
      clearTimeout(hideTimer)
      clearTimeout(clearTimer)
    }
  }, [quest?.ts])

  if (!current) return null

  const rewardParts = []
  if (current.silver) rewardParts.push(`${current.silver} silver`)
  for (const name of current.items || []) rewardParts.push(name)
  for (const [k, qty] of Object.entries(current.reagents || {})) rewardParts.push(`${qty}× ${k}`)

  const repEntries = Object.entries(current.factionRep || {}).filter(([, d]) => d)
  const npcRepEntries = Object.entries(current.npcRep || {}).filter(([, d]) => d)

  return (
    <div className={`quest-toast quest-toast-completed ${visible ? 'quest-toast-in' : 'quest-toast-out'}`}>
      <div className="quest-toast-eyebrow cinzel">QUEST COMPLETE</div>
      <div className="quest-toast-title">{current.title}</div>
      {current.outcomeLabel && (
        <div className="quest-toast-sub">{current.outcomeLabel}</div>
      )}
      {rewardParts.length > 0 && (
        <div className="quest-toast-rewards">
          {rewardParts.map((r, i) => (
            <span key={i} className="quest-toast-reward-chip">{r}</span>
          ))}
        </div>
      )}
      {repEntries.length > 0 && (
        <div className="quest-toast-rep">
          {repEntries.map(([k, d]) => (
            <span key={k} className={`quest-toast-rep-chip ${d >= 0 ? 'pos' : 'neg'}`}>
              {d >= 0 ? '+' : ''}{d} {k}
            </span>
          ))}
        </div>
      )}
      {npcRepEntries.length > 0 && (
        <div className="quest-toast-rep quest-toast-npc-rep">
          {npcRepEntries.map(([k, d]) => (
            <span key={k} className={`quest-toast-rep-chip npc ${d >= 0 ? 'pos' : 'neg'}`} title="Personal reputation with this NPC">
              {d >= 0 ? '+' : ''}{d} <span className="quest-toast-npc-name">{k.replace(/(^|\s)\S/g, c => c.toUpperCase())}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
