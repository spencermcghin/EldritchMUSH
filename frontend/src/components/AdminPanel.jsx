import { useState, useEffect, useCallback } from 'react'
import './AdminPanel.css'

// Read Django's csrftoken cookie for POST requests
function getCsrfToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match ? match[1] : ''
}

// Flag classification for NPC audit log. Determines which flags are
// "suspicious" (counted in the summary / filter) vs operational.
const SUSPICIOUS_FLAGS = new Set(['banned_phrase', 'moderated_input'])
const NOISY_FLAGS = new Set(['rate_limited_account', 'rate_limited_char_npc'])

function isSuspicious(record) {
  return (record.flags || []).some(f => {
    const base = f.split(':')[0]
    return SUSPICIOUS_FLAGS.has(base)
  })
}

function isNoisy(record) {
  return (record.flags || []).some(f => {
    const base = f.split(':')[0]
    return NOISY_FLAGS.has(base)
  })
}

function flagBadgeClass(flag) {
  const base = flag.split(':')[0]
  if (SUSPICIOUS_FLAGS.has(base)) return 'flag-badge suspicious'
  if (NOISY_FLAGS.has(base)) return 'flag-badge noisy'
  if (base.startsWith('llm_error') || base.startsWith('llm_http_error')) return 'flag-badge error'
  return 'flag-badge neutral'
}

function formatTimeAgo(ts) {
  if (!ts) return ''
  const diff = Math.floor(Date.now() / 1000 - ts)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

function NpcAuditTab() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('suspicious')  // 'all' | 'suspicious' | 'rate' | 'errors'

  const fetchRecords = useCallback(async () => {
    setLoading(true)
    try {
      const resp = await fetch('/api/admin/npc-audit/?limit=500', { credentials: 'include' })
      if (!resp.ok) {
        if (resp.status === 403) throw new Error('Admin access required')
        throw new Error(`HTTP ${resp.status}`)
      }
      const data = await resp.json()
      setRecords(data.records || [])
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchRecords()
    const iv = setInterval(fetchRecords, 30000)  // auto-refresh every 30s
    return () => clearInterval(iv)
  }, [fetchRecords])

  // Summary stats
  const suspiciousRecords = records.filter(isSuspicious)
  const noisyRecords = records.filter(isNoisy)
  const errorRecords = records.filter(r => (r.flags || []).some(f => f.startsWith('llm_error') || f.startsWith('llm_http_error')))

  // Per-account offender counts (suspicious only)
  const offenderCounts = {}
  for (const r of suspiciousRecords) {
    const k = r.account || '(unknown)'
    offenderCounts[k] = (offenderCounts[k] || 0) + 1
  }
  const repeatOffenders = Object.entries(offenderCounts)
    .filter(([, n]) => n >= 3)
    .sort((a, b) => b[1] - a[1])

  // Filter for display
  let displayed = records
  if (filter === 'suspicious') displayed = suspiciousRecords
  else if (filter === 'rate') displayed = noisyRecords
  else if (filter === 'errors') displayed = errorRecords

  return (
    <div className="npc-audit">
      {/* Summary strip */}
      <div className="audit-summary-strip">
        <div className={`audit-summary-card ${suspiciousRecords.length > 0 ? 'alert' : ''}`}>
          <div className="audit-summary-value">{suspiciousRecords.length}</div>
          <div className="audit-summary-label">Suspicious</div>
        </div>
        <div className="audit-summary-card">
          <div className="audit-summary-value">{noisyRecords.length}</div>
          <div className="audit-summary-label">Rate-limited</div>
        </div>
        <div className="audit-summary-card">
          <div className="audit-summary-value">{errorRecords.length}</div>
          <div className="audit-summary-label">LLM errors</div>
        </div>
        <div className="audit-summary-card">
          <div className="audit-summary-value">{records.length}</div>
          <div className="audit-summary-label">Total (last 500)</div>
        </div>
        <div className="audit-summary-spacer" />
        <button className="audit-refresh-btn" onClick={fetchRecords}>↻ Refresh</button>
      </div>

      {/* Repeat offenders — only shown if there are any */}
      {repeatOffenders.length > 0 && (
        <div className="audit-offenders">
          <div className="audit-section-label">⚠ Repeat offenders (3+ suspicious attempts)</div>
          <div className="audit-offender-list">
            {repeatOffenders.map(([acct, count]) => (
              <span key={acct} className="audit-offender-chip">
                {acct} <span className="audit-offender-count">{count}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Filter bar */}
      <div className="audit-filter-bar">
        {[
          { key: 'suspicious', label: `Suspicious (${suspiciousRecords.length})` },
          { key: 'rate', label: `Rate-limited (${noisyRecords.length})` },
          { key: 'errors', label: `Errors (${errorRecords.length})` },
          { key: 'all', label: `All (${records.length})` },
        ].map(f => (
          <button
            key={f.key}
            className={`admin-filter-btn ${filter === f.key ? 'active' : ''}`}
            onClick={() => setFilter(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Records */}
      <div className="audit-records">
        {loading && records.length === 0 && (
          <div className="admin-loading">Loading audit log...</div>
        )}
        {error && <div className="admin-error">{error}</div>}
        {!loading && !error && displayed.length === 0 && (
          <div className="admin-empty">
            {filter === 'suspicious'
              ? 'No suspicious activity in the last 500 records. ✓'
              : 'No records match this filter.'}
          </div>
        )}
        {displayed.map((r, i) => (
          <div key={`${r.ts}-${i}`} className={`audit-record ${isSuspicious(r) ? 'suspicious' : ''}`}>
            <div className="audit-record-header">
              <span className="audit-time">{formatTimeAgo(r.ts)}</span>
              <span className="audit-account">{r.account || '(no account)'}</span>
              <span className="audit-arrow">→</span>
              <span className="audit-npc">{r.npc}</span>
              <span className="audit-char">as {r.char}</span>
              <div className="audit-flags">
                {(r.flags || []).map((f, j) => (
                  <span key={j} className={flagBadgeClass(f)}>{f}</span>
                ))}
              </div>
            </div>
            <div className="audit-record-body">
              <div className="audit-turn">
                <span className="audit-turn-label">Player:</span>
                <span className="audit-turn-text player">{r.msg}</span>
              </div>
              <div className="audit-turn">
                <span className="audit-turn-label">NPC:</span>
                <span className="audit-turn-text npc">{r.reply}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
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

  const [rejectInput, setRejectInput] = useState({})

  const handleApproval = useCallback(async (charId, action, reason = '') => {
    try {
      const resp = await fetch('/api/admin/approve-character/', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify({ character_id: charId, action, reason }),
      })
      const data = await resp.json()
      if (data.success) {
        fetchCharacters()
      } else {
        setError(data.error)
      }
    } catch (err) {
      setError(err.message)
    }
  }, [fetchCharacters])

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
  // Separate out pending characters — they get their own tab so the
  // main Characters view isn't cluttered with people awaiting review.
  const pendingChars = characters.filter(c => c.approvalStatus === 'pending')
  const activeChars = characters.filter(c => c.approvalStatus !== 'pending')

  const searchMatch = (c) => {
    if (!searchLower) return true
    return c.name.toLowerCase().includes(searchLower)
      || (c.accountName || '').toLowerCase().includes(searchLower)
      || (c.location || '').toLowerCase().includes(searchLower)
      || (c.archetype || '').toLowerCase().includes(searchLower)
  }

  const filtered = activeChars
    .filter(c => {
      if (filter === 'online') return c.online
      if (filter === 'offline') return !c.online
      if (filter === 'chargen') return c.inChargen
      return true
    })
    .filter(searchMatch)

  const filteredPending = pendingChars.filter(searchMatch)

  const onlineCount = characters.filter(c => c.online).length
  const totalCount = characters.length
  const pendingCount = pendingChars.length

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
            className={`admin-filter-btn ${tab === 'approvals' ? 'active' : ''} ${pendingCount > 0 ? 'has-pending' : ''}`}
            onClick={() => setTab('approvals')}
          >
            Approvals
            {pendingCount > 0 && (
              <span className="admin-tab-badge">{pendingCount}</span>
            )}
          </button>
          <button
            className={`admin-filter-btn ${tab === 'accounts' ? 'active' : ''}`}
            onClick={() => setTab('accounts')}
          >
            Accounts & Roles
          </button>
          <button
            className={`admin-filter-btn ${tab === 'audit' ? 'active' : ''}`}
            onClick={() => setTab('audit')}
          >
            NPC Audit
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
          ) : tab === 'audit' ? (
            <NpcAuditTab />
          ) : tab === 'approvals' ? (
            <>
              {loading && <div className="admin-loading">Loading pending characters...</div>}
              {error && <div className="admin-error">{error}</div>}
              {!loading && !error && (
                <div className="admin-approvals-grid">
                  {filteredPending.length === 0 && (
                    <div className="admin-empty">
                      No characters awaiting approval.
                    </div>
                  )}
                  {filteredPending.map(char => (
                    <div key={char.id} className="admin-approval-card">
                      <div className="admin-approval-header">
                        <div className="admin-approval-name-block">
                          <span className="admin-approval-name">{char.name}</span>
                          <span className="admin-char-dbref">{char.dbref}</span>
                        </div>
                        <div className="admin-approval-meta">
                          {char.archetype && (
                            <span className="admin-meta-tag archetype">{char.archetype}</span>
                          )}
                          <span className="admin-meta-tag pending">PENDING</span>
                          {char.online && (
                            <span className="admin-meta-tag online">ONLINE</span>
                          )}
                        </div>
                      </div>
                      <div className="admin-approval-facts">
                        <div className="admin-approval-fact">
                          <span className="admin-detail-label">Account</span>
                          <span className="admin-detail-value wide">{char.accountName || 'unlinked'}</span>
                        </div>
                        <div className="admin-approval-fact">
                          <span className="admin-detail-label">Location</span>
                          <span className="admin-detail-value wide">{char.location}</span>
                        </div>
                        <div className="admin-approval-fact">
                          <span className="admin-detail-label">Submitted</span>
                          <span className="admin-detail-value wide">
                            {char.created ? new Date(char.created).toLocaleString() : '—'}
                          </span>
                        </div>
                      </div>
                      <div className="admin-approval-actions">
                        <button
                          className="admin-btn approve-btn admin-btn-big"
                          onClick={() => handleApproval(char.id, 'approve')}
                        >
                          ✓ Approve Crossing
                        </button>
                        <input
                          className="admin-reject-input"
                          placeholder="Rejection reason (optional)"
                          value={rejectInput[char.id] || ''}
                          onChange={e => setRejectInput(prev => ({ ...prev, [char.id]: e.target.value }))}
                        />
                        <button
                          className="admin-btn reject-btn admin-btn-big"
                          onClick={() => handleApproval(char.id, 'reject', rejectInput[char.id] || '')}
                        >
                          ✕ Reject
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
          <>
          {loading && <div className="admin-loading">Loading characters...</div>}
          {error && <div className="admin-error">{error}</div>}

          {!loading && !error && (
            <div className="admin-char-grid">
              {filtered.map(char => (
                <div key={char.id} className={`admin-char-card ${char.online ? 'is-online' : 'is-offline'}`}>
                  {/* Row 1 — identity + status */}
                  <div className="admin-char-row-top">
                    <span className={`admin-status-dot ${char.online ? 'online' : 'offline'}`} />
                    <span className="admin-char-name">{char.name}</span>
                    <span className="admin-char-dbref">{char.dbref}</span>
                    <div className="admin-char-tags">
                      {char.archetype && (
                        <span className="admin-meta-tag archetype">{char.archetype}</span>
                      )}
                      {char.inChargen && (
                        <span className="admin-meta-tag chargen">IN CHARGEN</span>
                      )}
                      {char.approvalStatus === 'approved' && (
                        <span className="admin-meta-tag approved">APPROVED</span>
                      )}
                      {char.approvalStatus === 'rejected' && (
                        <span className="admin-meta-tag rejected">REJECTED</span>
                      )}
                      {char.online && (
                        <span className="admin-meta-tag online">ONLINE</span>
                      )}
                    </div>
                  </div>

                  {/* Row 2 — facts + actions */}
                  <div className="admin-char-row-bottom">
                    <div className="admin-char-facts">
                      <span className="admin-fact">
                        <span className="admin-detail-label">Account:</span>
                        <span className="admin-detail-value">{char.accountName || 'unlinked'}</span>
                      </span>
                      <span className="admin-fact">
                        <span className="admin-detail-label">Location:</span>
                        <span className="admin-detail-value">{char.location}</span>
                      </span>
                      <span className="admin-fact">
                        <span className="admin-detail-label">Body:</span>
                        <span className="admin-detail-value">{char.body}/{char.totalBody}</span>
                      </span>
                      <span className="admin-fact">
                        <span className="admin-detail-label">AV:</span>
                        <span className="admin-detail-value">{char.av}</span>
                      </span>
                      <span className="admin-fact">
                        <span className="admin-detail-label">Created:</span>
                        <span className="admin-detail-value">
                          {char.created ? new Date(char.created).toLocaleDateString() : '—'}
                        </span>
                      </span>
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
