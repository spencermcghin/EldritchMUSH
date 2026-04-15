import { useEffect } from 'react'
import './PrimerModal.css'

export default function PrimerModal({ open, onClose, primerData }) {
  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open) return null
  if (!primerData) {
    return (
      <div className="primer-backdrop" onClick={onClose}>
        <div className="primer-book" onClick={e => e.stopPropagation()}>
          <div className="primer-loading">Unfolding the Primer…</div>
        </div>
      </div>
    )
  }

  return (
    <div className="primer-backdrop" onClick={onClose}>
      <div className="primer-book" onClick={e => e.stopPropagation()}>
        <button className="primer-close" onClick={onClose}>✕</button>

        <div className="primer-page">
          {/* Title */}
          <div className="primer-title-block">
            <div className="primer-flourish">✦ ─── ✦ ─── ✦</div>
            <h1 className="primer-title cinzel">{primerData.title}</h1>
            <div className="primer-flourish">✦ ─── ✦ ─── ✦</div>
            {primerData.subtitle && (
              <p className="primer-subtitle">{primerData.subtitle}</p>
            )}
          </div>

          {/* Sections */}
          <div className="primer-sections">
            {primerData.sections?.map((sec, i) => (
              <div key={i} className="primer-section">
                <h2 className="primer-section-header cinzel">
                  {sec.header}
                </h2>
                {sec.rows && sec.rows.length > 0 && (
                  <table className="primer-table">
                    <tbody>
                      {sec.rows.map((row, j) => (
                        <tr key={j}>
                          <td className="primer-cmd">
                            <code>{row[0]}</code>
                          </td>
                          <td className="primer-desc">{row[1]}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
                {sec.note && (
                  <p className="primer-note">{sec.note}</p>
                )}
              </div>
            ))}
          </div>

          {/* Signature */}
          {primerData.signature && (
            <div className="primer-signature">
              <div className="primer-flourish">✦ ─── ✦ ─── ✦</div>
              <p className="primer-sig-text">{primerData.signature}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
