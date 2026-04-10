import { useEffect } from 'react'
import './WorldMapModal.css'

export default function WorldMapModal({ open, onClose }) {
  useEffect(() => {
    if (!open) return
    const handler = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="world-map-modal" onClick={onClose}>
      <div className="world-map-content" onClick={(e) => e.stopPropagation()}>
        <div className="world-map-header">
          <span className="world-map-title">The Annwyn</span>
          <button className="world-map-close" onClick={onClose}>✕</button>
        </div>
        <div className="world-map-body">
          <img
            src="/art/map/annwyn_map.jpg"
            alt="Map of the Annwyn"
            className="world-map-image"
          />
        </div>
        <div className="world-map-footer">
          <span className="world-map-hint">The known lands of Arnesse — click outside or press ESC to close</span>
        </div>
      </div>
    </div>
  )
}
