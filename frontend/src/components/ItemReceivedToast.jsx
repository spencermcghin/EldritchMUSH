import { useEffect, useState } from 'react'
import './ItemReceivedToast.css'

// Slides in for ~4 seconds when a new item_received event fires.
// Stacks one-deep; a second arrival replaces the first.
export default function ItemReceivedToast({ item }) {
  const [visible, setVisible] = useState(false)
  const [current, setCurrent] = useState(null)

  useEffect(() => {
    if (!item || !item.ts) return
    setCurrent(item)
    setVisible(true)
    const hideTimer = setTimeout(() => setVisible(false), 4200)
    const clearTimer = setTimeout(() => setCurrent(null), 4700)
    return () => {
      clearTimeout(hideTimer)
      clearTimeout(clearTimer)
    }
  }, [item?.ts])

  if (!current) return null

  return (
    <div className={`item-toast ${visible ? 'item-toast-in' : 'item-toast-out'}`}>
      <div className="item-toast-eyebrow cinzel">
        {current.fromNpc ? `${current.fromNpc} offers you` : 'You receive'}
      </div>
      <div className="item-toast-name">{current.itemName}</div>
      {current.desc && <div className="item-toast-desc">{current.desc}</div>}
    </div>
  )
}
