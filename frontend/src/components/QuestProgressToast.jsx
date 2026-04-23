import { useEffect, useState } from 'react'
import './QuestToasts.css'

// Tiny ephemeral indicator for each objective tick — 2.2s slide-in.
// Deliberately smaller + shorter than accept/complete toasts so a
// rapid sequence of ticks doesn't drown the UI. The most recent tick
// replaces the previous one in place.
export default function QuestProgressToast({ progress }) {
  const [visible, setVisible] = useState(false)
  const [current, setCurrent] = useState(null)

  useEffect(() => {
    if (!progress || !progress.ts) return
    setCurrent(progress)
    setVisible(true)
    const hideTimer = setTimeout(() => setVisible(false), 2000)
    const clearTimer = setTimeout(() => setCurrent(null), 2500)
    return () => {
      clearTimeout(hideTimer)
      clearTimeout(clearTimer)
    }
  }, [progress?.ts])

  if (!current) return null

  const isDone = current.done || current.current >= current.qty

  return (
    <div className={`quest-toast quest-toast-progress ${visible ? 'quest-toast-in' : 'quest-toast-out'}`}>
      <div className="quest-toast-eyebrow cinzel">
        {isDone ? 'OBJECTIVE COMPLETE' : 'QUEST PROGRESS'}
      </div>
      <div className="quest-toast-progress-line">
        <span className="quest-toast-progress-desc">{current.desc}</span>
        <span className="quest-toast-progress-count">
          {current.current}/{current.qty}
        </span>
      </div>
    </div>
  )
}
