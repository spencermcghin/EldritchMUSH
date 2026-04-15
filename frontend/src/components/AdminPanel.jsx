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
  const [purgePreview, setPurgePreview] = useState(null)  // null|{accounts,chars,npcs,counts}
  const [purging, setPurging] = useState(false)
  // Confirm modal state for role changes: {accountId, username, role, action}
  const [pendingRoleChange, setPendingRoleChange] = useState(null)
  const [roleBusy, setRoleBusy] = useState(false)

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

  const runPurge = useCallback(async (mode) => {
    setPurging(true)
    try {
      const resp = await fetch('/api/admin/purge-legacy/', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify({ mode }),
      })
      const data = await resp.json()
      if (!resp.ok) {
        setError(data.error || `HTTP ${resp.status}`)
        return
      }
      setPurgePreview(data)
      if (mode === 'execute') {
        // After execute, refresh accounts list
        fetchAccounts()
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setPurging(false)
    }
  }, [fetchAccounts])

  // Stage-1: clicking a role pill opens the confirm modal rather than
  // mutating immediately. Stage-2 (confirmation) runs the actual API call.
  const requestRoleChange = useCallback((accountId, username, role, hasRole) => {
    setPendingRoleChange({
      accountId,
      username,
      role,
      action: hasRole ? 'remove' : 'add',
    })
  }, [])

  const cancelRoleChange = useCallback(() => {
    if (roleBusy) return
    setPendingRoleChange(null)
  }, [roleBusy])

  const confirmRoleChange = useCallback(async () => {
    if (!pendingRoleChange) return
    const { accountId, role, action } = pendingRoleChange
    setRoleBusy(true)
    try {
      const resp = await fetch('/api/admin/set-role/', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify({ account_id: accountId, role, action }),
      })
      const data = await resp.json()
      if (data.success) {
        // Updating accounts state triggers re-render — active/inactive
        // highlight on the role pill flips automatically because it
        // reads from acct.permissions.
        setAccounts(prev => prev.map(a =>
          a.id === accountId ? { ...a, permissions: data.permissions } : a
        ))
        setPendingRoleChange(null)
      } else {
        setError(data.error || 'Role change failed')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setRoleBusy(false)
    }
  }, [pendingRoleChange])

  if (loading) return <div className="admin-loading">Loading accounts...</div>
  if (error) return <div className="admin-error">{error}</div>

  return (
  <>
    {/* Legacy purge toolbar */}
    <div className="admin-purge-bar">
      <div className="admin-purge-label">
        <span className="cinzel admin-purge-title">Legacy Cleanup</span>
        <span className="admin-purge-hint">
          Removes non-admin accounts, their characters, and any NPCs not
          part of the scripted Gateway roster. Admin-owned characters
          and NPCs with AI personality are always preserved.
        </span>
      </div>
      <div className="admin-purge-actions">
        {!purgePreview && (
          <button
            className="admin-btn"
            onClick={() => runPurge('preview')}
            disabled={purging}
          >
            {purging ? 'Scanning…' : 'Preview Purge'}
          </button>
        )}
        {purgePreview && purgePreview.mode === 'preview' && (
          <>
            <button
              className="admin-btn confirm-no"
              onClick={() => setPurgePreview(null)}
              disabled={purging}
            >
              Cancel
            </button>
            <button
              className="admin-btn reject-btn"
              onClick={() => runPurge('execute')}
              disabled={purging || (
                purgePreview.counts.accounts === 0 &&
                purgePreview.counts.characters === 0 &&
                purgePreview.counts.npcs === 0
              )}
            >
              {purging ? 'Deleting…' : `Delete ${purgePreview.counts.accounts + purgePreview.counts.characters + purgePreview.counts.npcs} items`}
            </button>
          </>
        )}
        {purgePreview && purgePreview.mode === 'executed' && (
          <button
            className="admin-btn"
            onClick={() => setPurgePreview(null)}
          >
            Close ({purgePreview.deleted.accounts} accts, {purgePreview.deleted.characters} chars, {purgePreview.deleted.npcs} npcs deleted)
          </button>
        )}
      </div>
    </div>

    {/* Purge preview / result detail */}
    {purgePreview && (
      <div className="admin-purge-detail">
        {purgePreview.mode === 'preview' && (
          <div className="admin-purge-banner warn">
            Preview only — nothing has been deleted yet.
            Review below and click <b>Delete</b> to execute, or Cancel to abort.
          </div>
        )}
        {purgePreview.mode === 'executed' && (
          <div className="admin-purge-banner ok">
            Purge executed. {purgePreview.deleted.accounts} accounts,
            {' '}{purgePreview.deleted.characters} characters,
            {' '}{purgePreview.deleted.npcs} NPCs deleted.
            {purgePreview.errors && purgePreview.errors.length > 0 && (
              <div className="admin-purge-errors">
                Errors: {purgePreview.errors.join(' | ')}
              </div>
            )}
          </div>
        )}
        <div className="admin-purge-columns">
          <div className="admin-purge-column">
            <div className="audit-section-label">
              Accounts ({purgePreview.counts.accounts})
            </div>
            <div className="admin-purge-list">
              {purgePreview.accounts.map(a => (
                <span key={a.id} className="admin-purge-chip">
                  {a.username} <span className="admin-offender-count">#{a.id}</span>
                </span>
              ))}
              {purgePreview.counts.accounts === 0 && <span className="admin-purge-empty">(none)</span>}
            </div>
          </div>
          <div className="admin-purge-column">
            <div className="audit-section-label">
              Characters ({purgePreview.counts.characters})
            </div>
            <div className="admin-purge-list">
              {purgePreview.characters.map(c => (
                <span key={c.id} className="admin-purge-chip">
                  {c.name} <span className="admin-offender-count">#{c.id}</span>
                </span>
              ))}
              {purgePreview.counts.characters === 0 && <span className="admin-purge-empty">(none)</span>}
            </div>
          </div>
          <div className="admin-purge-column">
            <div className="audit-section-label">
              NPCs ({purgePreview.counts.npcs})
            </div>
            <div className="admin-purge-list">
              {purgePreview.npcs.map(n => (
                <span key={n.id} className="admin-purge-chip">
                  {n.name} {n.location && <span className="admin-offender-count">@{n.location}</span>}
                </span>
              ))}
              {purgePreview.counts.npcs === 0 && <span className="admin-purge-empty">(none)</span>}
            </div>
          </div>
        </div>
      </div>
    )}

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
                // Evennia lowercases permissions on storage ("admin", "player"),
                // but availableRoles are capitalized ("Admin", "Player"). Compare
                // case-insensitively so the active highlight actually fires.
                const roleLower = role.toLowerCase()
                const hasRole = acct.permissions.some(
                  p => String(p).toLowerCase() === roleLower
                )
                return (
                  <button
                    key={role}
                    className={`admin-role-pill ${hasRole ? 'active' : ''}`}
                    onClick={() => requestRoleChange(acct.id, acct.username, role, hasRole)}
                    disabled={acct.isSuperuser}
                    title={acct.isSuperuser ? 'Superusers have all permissions' : `${hasRole ? 'Remove' : 'Add'} ${role}`}
                  >
                    {hasRole ? '✓ ' : ''}{role}
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      ))}
    </div>

    {/* Confirm modal for role add/remove */}
    {pendingRoleChange && (
      <div
        className="admin-confirm-backdrop"
        onClick={cancelRoleChange}
      >
        <div
          className="admin-confirm-modal"
          onClick={e => e.stopPropagation()}
        >
          <div className="admin-confirm-header cinzel">
            {pendingRoleChange.action === 'add' ? 'Grant Role?' : 'Revoke Role?'}
          </div>
          <div className="admin-confirm-body">
            {pendingRoleChange.action === 'add' ? (
              <>
                Grant <span className="admin-confirm-role">{pendingRoleChange.role}</span>
                {' '}to <span className="admin-confirm-account">{pendingRoleChange.username}</span>?
              </>
            ) : (
              <>
                Remove <span className="admin-confirm-role">{pendingRoleChange.role}</span>
                {' '}from <span className="admin-confirm-account">{pendingRoleChange.username}</span>?
              </>
            )}
            <div className="admin-confirm-note">
              {pendingRoleChange.action === 'add'
                ? 'This grants elevated game permissions. Confirm to apply.'
                : 'The user will lose access granted by this role. Confirm to apply.'}
            </div>
          </div>
          <div className="admin-confirm-actions">
            <button
              className="admin-btn"
              onClick={cancelRoleChange}
              disabled={roleBusy}
            >
              Cancel
            </button>
            <button
              className={`admin-btn ${pendingRoleChange.action === 'add' ? 'approve-btn' : 'reject-btn'}`}
              onClick={confirmRoleChange}
              disabled={roleBusy}
            >
              {roleBusy
                ? 'Applying…'
                : (pendingRoleChange.action === 'add' ? 'Grant Role' : 'Revoke Role')}
            </button>
          </div>
        </div>
      </div>
    )}
  </>
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
  // Batch selection in the Characters tab
  const [selected, setSelected] = useState(() => new Set())
  const [bulkConfirm, setBulkConfirm] = useState(false)
  const [bulkBusy, setBulkBusy] = useState(false)
  const [bulkResult, setBulkResult] = useState(null)  // {count, errors} after execute

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

  const toggleSelected = useCallback((charId) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(charId)) next.delete(charId)
      else next.add(charId)
      return next
    })
  }, [])

  const selectAllVisible = useCallback((visibleIds) => {
    setSelected(prev => {
      const next = new Set(prev)
      for (const id of visibleIds) next.add(id)
      return next
    })
  }, [])

  const clearSelection = useCallback(() => {
    setSelected(new Set())
  }, [])

  const runBulkDelete = useCallback(async () => {
    if (selected.size === 0) return
    setBulkBusy(true)
    try {
      const resp = await fetch('/api/admin/bulk-delete-characters/', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify({ character_ids: [...selected] }),
      })
      const data = await resp.json()
      if (!resp.ok) {
        setError(data.error || `HTTP ${resp.status}`)
        return
      }
      // Remove deleted characters from the list and clear selection.
      const deletedIds = new Set((data.deleted || []).map(d => d.id))
      setCharacters(prev => prev.filter(c => !deletedIds.has(c.id)))
      setSelected(new Set())
      setBulkConfirm(false)
      setBulkResult({
        count: data.count || 0,
        errors: data.errors || [],
      })
      // Auto-clear the result banner after 5s
      setTimeout(() => setBulkResult(null), 5000)
    } catch (err) {
      setError(err.message)
    } finally {
      setBulkBusy(false)
    }
  }, [selected])

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
            <>
            {/* Bulk selection toolbar — sticks above the list */}
            <div className="admin-bulk-bar">
              <span className="admin-bulk-summary">
                {selected.size > 0
                  ? <><span className="admin-bulk-count">{selected.size}</span> selected</>
                  : <span className="admin-bulk-hint">Select characters with the checkboxes to delete them in bulk.</span>}
              </span>
              <div className="admin-bulk-actions">
                <button
                  className="admin-btn"
                  onClick={() => selectAllVisible(filtered.map(c => c.id))}
                  disabled={filtered.length === 0}
                >
                  Select Visible ({filtered.length})
                </button>
                <button
                  className="admin-btn"
                  onClick={clearSelection}
                  disabled={selected.size === 0}
                >
                  Clear
                </button>
                <button
                  className="admin-btn delete-btn"
                  onClick={() => setBulkConfirm(true)}
                  disabled={selected.size === 0}
                >
                  Delete {selected.size || ''} Selected
                </button>
              </div>
            </div>

            {bulkResult && (
              <div className={`admin-purge-banner ${bulkResult.errors.length > 0 ? 'warn' : 'ok'}`}>
                Deleted {bulkResult.count} character(s).
                {bulkResult.errors.length > 0 && ` ${bulkResult.errors.length} error(s).`}
              </div>
            )}

            <div className="admin-char-grid">
              {filtered.map(char => (
                <div key={char.id} className={`admin-char-card ${char.online ? 'is-online' : 'is-offline'} ${selected.has(char.id) ? 'is-selected' : ''}`}>
                  {/* Row 1 — identity + status */}
                  <div className="admin-char-row-top">
                    <label className="admin-char-checkbox" title="Select for bulk delete">
                      <input
                        type="checkbox"
                        checked={selected.has(char.id)}
                        onChange={() => toggleSelected(char.id)}
                      />
                      <span className="admin-char-checkbox-box" />
                    </label>
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
            </>
          )}
          </>
          )}
        </div>

        {/* Bulk-delete confirmation modal */}
        {bulkConfirm && (
          <div
            className="admin-confirm-backdrop"
            onClick={() => !bulkBusy && setBulkConfirm(false)}
          >
            <div
              className="admin-confirm-modal"
              onClick={e => e.stopPropagation()}
            >
              <div className="admin-confirm-header cinzel">
                Delete {selected.size} Character{selected.size === 1 ? '' : 's'}?
              </div>
              <div className="admin-confirm-body">
                This will permanently delete{' '}
                <span className="admin-confirm-role">{selected.size}</span>{' '}
                character{selected.size === 1 ? '' : 's'}:
                <div className="admin-bulk-preview">
                  {characters
                    .filter(c => selected.has(c.id))
                    .slice(0, 12)
                    .map(c => (
                      <span key={c.id} className="admin-purge-chip">
                        {c.name} <span className="admin-offender-count">{c.dbref}</span>
                      </span>
                    ))}
                  {selected.size > 12 && (
                    <span className="admin-purge-empty">
                      ...and {selected.size - 12} more
                    </span>
                  )}
                </div>
                <div className="admin-confirm-note">
                  Accounts will be preserved — only the characters are deleted.
                  This cannot be undone.
                </div>
              </div>
              <div className="admin-confirm-actions">
                <button
                  className="admin-btn"
                  onClick={() => setBulkConfirm(false)}
                  disabled={bulkBusy}
                >
                  Cancel
                </button>
                <button
                  className="admin-btn reject-btn"
                  onClick={runBulkDelete}
                  disabled={bulkBusy}
                >
                  {bulkBusy ? 'Deleting…' : `Delete ${selected.size}`}
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="admin-footer">
          <span className="cinzel">✦ ─────── ✦ ─────── ✦</span>
        </div>
      </div>
    </div>
  )
}
