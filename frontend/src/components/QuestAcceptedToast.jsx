import { useEffect, useState } from 'react'
import './QuestToasts.css'

// Brief confirmation toast that slides in when `quest accept` succeeds.
// Stacks below ItemReceivedToast via a different `top` offset.
export default function QuestAcceptedToast({ quest }) {
  const [visible, setVisible] = useState(false)
  const [current, setCurrent] = useState(null)

  useEffect(() => {
    if (!quest || !quest.ts) return
    setCurrent(quest)
    setVisible(true)
    const hideTimer = setTimeout(() => setVisible(false), 3800)
    const clearTimer = setTimeout(() => setCurrent(null), 4300)
    return () => {
      clearTimeout(hideTimer)
      clearTimeout(clearTimer)
    }
  }, [quest?.ts])

  if (!current) return null

  return (
    <div className={`quest-toast quest-toast-accepted ${visible ? 'quest-toast-in' : 'quest-toast-out'}`}>
      <div className="quest-toast-eyebrow cinzel">QUEST ACCEPTED</div>
      <div className="quest-toast-title">{current.title}</div>
      {current.outcomeLabel && (
        <div className="quest-toast-sub">Path: {current.outcomeLabel}</div>
      )}
    </div>
  )
}
