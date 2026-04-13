import { useState, useEffect, useCallback } from 'react'
import './AdminPanel.css'

// Read Django's csrftoken cookie for POST requests
function getCsrfToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match ? match[1] : ''
}

function AccountsTab() {
  const [accounts, setAccounts] = useState([])
  const [roles, setRoles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchAccounts = useCallback(async () => {
    setLoading(true)
    try {
      const resp = await fetch('/api/admin/accounts/', { credentials: 'include' })
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
      const data = await resp.json()
      setAccounts(data.accounts || [])
      setRoles(data.availableRoles || [])
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchAccounts() }, [fetchAccounts])

  const handleRoleToggle = useCallback(async (accountId, role, hasRole) => {
    try {
      const resp = await fetch('/api/admin/set-role/', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify({
          account_id: accountId,
          role,
          action: hasRole ? 'remove' : 'add',
        }),
      })
      const data = await resp.json()
      if (data.success) {
        setAccounts(prev => prev.map(a =>
          a.id === accountId ? { ...a, permissions: data.permissions } : a
        ))
      } else {
        setError(data.error)
      }
    } catch (err) {
      setError(err.message)
    }
  }, [])

  if (loading) return <div className="admin-loading">Loading accounts...</div>
  if (error) return <div className="admin-error">{error}</div>

  return (
    <div className="admin-accounts-grid">
      {accounts.map(acct => (
        <div key={acct.id} className={`admin-acct-card ${acct.online ? 'is-online' : ''}`}>
          <div className="admin-acct-header">
            <span className={`admin-status-dot ${acct.online ? 'online' : 'offline'}`} />
            <span className="admin-acct-name">{acct.username}</span>
            <span className="admin-char-dbref">#{acct.id}</span>
            {acct.isSuperuser && <span className="admin-meta-tag superuser">SUPERUSER</span>}
          </div>
          {acct.email && <div className="admin-acct-email">{acct.email}</div>}
          <div className="admin-acct-info">
            <span className="admin-detail-label">Characters:</span>
            <span className="admin-detail-value">
              {acct.characters.length > 0 ? acct.characters.join(', ') : 'none'}
            </span>
          </div>
          {acct.dateJoined && (
            <div className="admin-acct-info">
              <span className="admin-detail-label">Joined:</span>
              <span className="admin-detail-value">{new Date(acct.dateJoined).toLocaleDateString()}</span>
            </div>
          )}
          <div className="admin-roles">
            <span className="admin-detail-label">Roles:</span>
            <div className="admin-role-pills">
              {roles.map(role => {
                const hasRole = acct.permissions.includes(role)
                return (
                  <button
                    key={role}
                    className={`admin-role-pill ${hasRole ? 'active' : ''}`}
                    onClick={() => handleRoleToggle(acct.id, role, hasRole)}
                    disabled={acct.isSuperuser}
                    title={acct.isSuperuser ? 'Superusers have all permissions' : `${hasRole ? 'Remove' : 'Add'} ${role}`}
                  >
                    {role}
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function AdminPanel({ onClose }) {
  const [characters, setCharacters] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const [filter, setFilter] = useState('all')
  const [tab, setTab] = useState('characters')
  const [search, setSearch] = useState('')

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
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
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

  const searchLower = search.toLowerCase()
  const filtered = characters
    .filter(c => {
      if (filter === 'online') return c.online
      if (filter === 'offline') return !c.online
      if (filter === 'chargen') return c.inChargen
      return true
    })
    .filter(c => {
      if (!searchLower) return true
      return c.name.toLowerCase().includes(searchLower)
        || (c.accountName || '').toLowerCase().includes(searchLower)
        || (c.location || '').toLowerCase().includes(searchLower)
        || (c.archetype || '').toLowerCase().includes(searchLower)
    })

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

        {/* Tab switcher */}
        <div className="admin-filter-bar">
          <button
            className={`admin-filter-btn ${tab === 'characters' ? 'active' : ''}`}
            onClick={() => setTab('characters')}
          >
            Characters
          </button>
          <button
            className={`admin-filter-btn ${tab === 'accounts' ? 'active' : ''}`}
            onClick={() => setTab('accounts')}
          >
            Accounts & Roles
          </button>
          <div style={{ flex: 1 }} />
          <input
            className="admin-search"
            type="text"
            placeholder="Search..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            spellCheck="false"
          />
          {tab === 'characters' && ['all', 'online', 'offline', 'chargen'].map(f => (
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
          {tab === 'accounts' ? (
            <AccountsTab />
          ) : (
          <>
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
          </>
          )}
        </div>

        <div className="admin-footer">
          <span className="cinzel">✦ ─────── ✦ ─────── ✦</span>
        </div>
      </div>
    </div>
  )
}
