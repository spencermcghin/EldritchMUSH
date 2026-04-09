import { useEffect, useRef, useCallback } from 'react'
import './ContextMenu.css'

export default function ContextMenu({ x, y, items, onSelect, onClose }) {
  const menuRef = useRef(null)

  // Close on click outside
  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        onClose()
      }
    }
    function handleEscape(e) {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    // Use a slight delay so the contextmenu event itself doesn't immediately close
    const timer = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside)
      document.addEventListener('keydown', handleEscape)
    }, 10)

    return () => {
      clearTimeout(timer)
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [onClose])

  // Adjust position to stay within viewport
  useEffect(() => {
    if (!menuRef.current) return
    const rect = menuRef.current.getBoundingClientRect()
    const vw = window.innerWidth
    const vh = window.innerHeight

    if (rect.right > vw) {
      menuRef.current.style.left = `${Math.max(0, x - rect.width)}px`
    }
    if (rect.bottom > vh) {
      menuRef.current.style.top = `${Math.max(0, y - rect.height)}px`
    }
  }, [x, y])

  const handleItemClick = useCallback((item) => {
    onSelect(item.action)
    onClose()
  }, [onSelect, onClose])

  return (
    <div
      className="context-menu"
      ref={menuRef}
      style={{ left: x, top: y }}
    >
      <div className="context-menu-inner panel">
        {items.map((item, i) => (
          <button
            key={i}
            className="context-menu-item"
            onClick={() => handleItemClick(item)}
          >
            <span className="context-menu-icon">{item.icon}</span>
            <span className="context-menu-label">{item.label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
