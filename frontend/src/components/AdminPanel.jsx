import { useState, useEffect, useCallback } from 'react'
import './AdminPanel.css'

export default function AdminPanel({ onClose }) {
  const [characters, setCharacters] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const [filter, setFilter] = useState('all')

  const fetchCharacters = useCallback(async () => {
    setLoading(true)
    try {
      const resp = await fetch('/api/admin/characters/', { credentials: 'include' })
      if (!resp.ok) {
        if (resp.status === 403) throw new Error('Admin access required')
        throw new Error(`HTTP ${resp.status}`)
      }
      const data = await resp.json()
      setCharacters(data.characters || [])
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchCharacters() }, [fetchCharacters])

  const handleDelete = useCallback(async (charId, charName) => {
    try {
      const resp = await fetch('/api/admin/delete-character/', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ character_id: charId }),
      })
      const data = await resp.json()
      if (data.success) {
        setCharacters(prev => prev.filter(c => c.id !== charId))
        setDeleteConfirm(null)
      } else {
        setError(data.error || 'Delete failed')
      }
    } catch (err) {
      setError(err.message)
    }
  }, [])

  const filtered = filter === 'all' ? characters
    : filter === 'online' ? characters.filter(c => c.online)
    : filter === 'offline' ? characters.filter(c => !c.online)
    : filter === 'chargen' ? characters.filter(c => c.inChargen)
    : characters

  const onlineCount = characters.filter(c => c.online).length
  const totalCount = characters.length

  return (
    <div className="admin-backdrop" onClick={onClose}>
      <div className="admin-panel" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="admin-header">
          <span className="cinzel admin-title">ADMIN DASHBOARD</span>
          <div className="admin-stats">
            <span className="admin-stat online">{onlineCount} online</span>
            <span className="admin-stat total">{totalCount} total</span>
          </div>
          <button className="admin-close" onClick={onClose}>✕</button>
        </div>

        {/* Filter bar */}
        <div className="admin-filter-bar">
          {['all', 'online', 'offline', 'chargen'].map(f => (
            <button
              key={f}
              className={`admin-filter-btn ${filter === f ? 'active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="admin-body">
          {loading && <div className="admin-loading">Loading characters...</div>}
          {error && <div className="admin-error">{error}</div>}

          {!loading && !error && (
            <div className="admin-char-grid">
              {filtered.map(char => (
                <div key={char.id} className={`admin-char-card ${char.online ? 'is-online' : 'is-offline'}`}>
                  <div className="admin-char-header">
                    <span className={`admin-status-dot ${char.online ? 'online' : 'offline'}`} />
                    <span className="admin-char-name">{char.name}</span>
                    <span className="admin-char-dbref">{char.dbref}</span>
                  </div>

                  <div className="admin-char-meta">
                    {char.archetype && (
                      <span className="admin-meta-tag archetype">{char.archetype}</span>
                    )}
                    {char.inChargen && (
                      <span className="admin-meta-tag chargen">IN CHARGEN</span>
                    )}
                    {char.online && (
                      <span className="admin-meta-tag online">ONLINE</span>
                    )}
                  </div>

                  <div className="admin-char-details">
                    <div className="admin-detail">
                      <span className="admin-detail-label">Account</span>
                      <span className="admin-detail-value">{char.accountName || 'unlinked'}</span>
                    </div>
                    <div className="admin-detail">
                      <span className="admin-detail-label">Location</span>
                      <span className="admin-detail-value">{char.location}</span>
                    </div>
                    <div className="admin-detail">
                      <span className="admin-detail-label">Body</span>
                      <span className="admin-detail-value">{char.body}/{char.totalBody}</span>
                    </div>
                    <div className="admin-detail">
                      <span className="admin-detail-label">AV</span>
                      <span className="admin-detail-value">{char.av}</span>
                    </div>
                    <div className="admin-detail">
                      <span className="admin-detail-label">Created</span>
                      <span className="admin-detail-value">
                        {char.created ? new Date(char.created).toLocaleDateString() : '—'}
                      </span>
                    </div>
                  </div>

                  <div className="admin-char-actions">
                    {deleteConfirm === char.id ? (
                      <div className="admin-delete-confirm">
                        <span className="admin-delete-warn">Delete {char.name}?</span>
                        <button
                          className="admin-btn confirm-yes"
                          onClick={() => handleDelete(char.id, char.name)}
                        >
                          Yes, Delete
                        </button>
                        <button
                          className="admin-btn confirm-no"
                          onClick={() => setDeleteConfirm(null)}
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        className="admin-btn delete-btn"
                        onClick={() => setDeleteConfirm(char.id)}
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              ))}
              {filtered.length === 0 && (
                <div className="admin-empty">No characters match this filter.</div>
              )}
            </div>
          )}
        </div>

        <div className="admin-footer">
          <span className="cinzel">✦ ─────── ✦ ─────── ✦</span>
        </div>
      </div>
    </div>
  )
}
