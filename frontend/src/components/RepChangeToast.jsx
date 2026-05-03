import { useEffect, useState } from 'react'
import './QuestToasts.css'

/**
 * RepChangeToast — fades in a toast when the player's reputation
 * changes (NPC personal rep or faction-wide rep). Re-renders on
 * every fresh rep_change OOB event via the `change.ts` field.
 */
export default function RepChangeToast({ change }) {
  const [visible, setVisible] = useState(false)
  const [current, setCurrent] = useState(null)

  useEffect(() => {
    if (!change || !change.ts) return
    setCurrent(change)
    setVisible(true)
    const t = setTimeout(() => setVisible(false), 4500)
    return () => clearTimeout(t)
  }, [change?.ts])

  if (!current) return null

  const { scope, key, delta, newTotal } = current
  const sign = delta > 0 ? '+' : ''
  const positive = delta > 0
  const niceKey = (key || '').replace(/\b\w/g, (c) => c.toUpperCase())
  const scopeLabel = scope === 'faction' ? 'FACTION' : 'NPC'

  return (
    <div className={`quest-toast rep-change-toast ${positive ? 'positive' : 'negative'} ${visible ? 'in' : 'out'}`}>
      <div className="quest-toast-eyebrow">
        {positive ? '✦ REPUTATION GAINED' : '✦ REPUTATION LOST'}
      </div>
      <div className="quest-toast-title">
        <span className="rep-toast-scope">{scopeLabel}</span> {niceKey}
      </div>
      <div className="quest-toast-body">
        <span className={`rep-delta ${positive ? 'positive' : 'negative'}`}>
          {sign}{delta}
        </span>
        <span className="rep-total"> · now {newTotal}</span>
      </div>
    </div>
  )
}
