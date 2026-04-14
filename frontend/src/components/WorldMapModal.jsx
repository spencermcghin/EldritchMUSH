import { useEffect, useState, useCallback, useRef } from 'react'
import './WorldMapModal.css'

// Simple force-directed layout for room graph
function layoutGraph(nodes, edges) {
  if (!nodes.length) return { positions: {}, width: 0, height: 0 }

  // Build adjacency
  const adj = {}
  nodes.forEach(n => { adj[n.id] = [] })
  edges.forEach(e => {
    if (adj[e.from]) adj[e.from].push(e.to)
    if (adj[e.to]) adj[e.to].push(e.from)
  })

  // Initialize positions randomly
  const pos = {}
  const W = 800, H = 600
  nodes.forEach((n, i) => {
    const angle = (i / nodes.length) * Math.PI * 2
    const r = 150 + Math.random() * 100
    pos[n.id] = { x: W / 2 + Math.cos(angle) * r, y: H / 2 + Math.sin(angle) * r }
  })

  // Simple force simulation
  const ITERATIONS = 150
  const REPULSION = 8000
  const SPRING = 0.02
  const REST_LEN = 120
  const DAMPING = 0.85

  const vel = {}
  nodes.forEach(n => { vel[n.id] = { x: 0, y: 0 } })

  for (let iter = 0; iter < ITERATIONS; iter++) {
    // Repulsion between all pairs
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i].id, b = nodes[j].id
        const dx = pos[a].x - pos[b].x
        const dy = pos[a].y - pos[b].y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        const force = REPULSION / (dist * dist)
        const fx = (dx / dist) * force
        const fy = (dy / dist) * force
        vel[a].x += fx; vel[a].y += fy
        vel[b].x -= fx; vel[b].y -= fy
      }
    }

    // Spring attraction along edges
    edges.forEach(e => {
      if (!pos[e.from] || !pos[e.to]) return
      const dx = pos[e.to].x - pos[e.from].x
      const dy = pos[e.to].y - pos[e.from].y
      const dist = Math.sqrt(dx * dx + dy * dy) || 1
      const force = SPRING * (dist - REST_LEN)
      const fx = (dx / dist) * force
      const fy = (dy / dist) * force
      vel[e.from].x += fx; vel[e.from].y += fy
      vel[e.to].x -= fx; vel[e.to].y -= fy
    })

    // Apply velocity with damping
    nodes.forEach(n => {
      vel[n.id].x *= DAMPING
      vel[n.id].y *= DAMPING
      pos[n.id].x += vel[n.id].x
      pos[n.id].y += vel[n.id].y
      // Keep in bounds
      pos[n.id].x = Math.max(60, Math.min(W - 60, pos[n.id].x))
      pos[n.id].y = Math.max(40, Math.min(H - 40, pos[n.id].y))
    })
  }

  return { positions: pos, width: W, height: H }
}

const NODE_COLORS = {
  room: '#9a8266',
  weather: '#6a8a6a',
  market: '#d4af37',
  chargen: '#8b5cf6',
}

const ZONE_ALL = '__all__'

const NODE_ICONS = {
  room: '🏛',
  weather: '🌲',
  market: '🪙',
  chargen: '✦',
}

export default function WorldMapModal({ open, onClose, sendCommand, mapData }) {
  const [loading, setLoading] = useState(true)
  const [layout, setLayout] = useState(null)
  const [tab, setTab] = useState('rooms')
  const [zone, setZone] = useState(ZONE_ALL)
  const [tooltip, setTooltip] = useState(null) // {node, x, y}
  const svgRef = useRef(null)

  useEffect(() => {
    if (!open) return
    sendCommand('__map_ui__')
  }, [open, sendCommand])

  // Auto-select the zone of the player's current room on first load
  useEffect(() => {
    if (mapData && mapData.currentZone && zone === ZONE_ALL) {
      setZone(mapData.currentZone)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapData])

  // Recompute layout when zone filter or mapData changes
  useEffect(() => {
    if (!mapData || !mapData.nodes) return
    // Filter nodes by zone (ALL shows everything)
    const filteredNodes = zone === ZONE_ALL
      ? mapData.nodes
      : mapData.nodes.filter(n => n.zone === zone)
    const nodeIds = new Set(filteredNodes.map(n => n.id))
    // Deduplicate edges and keep only those connecting visible nodes
    const seen = new Set()
    const filteredEdges = mapData.edges.filter(e => {
      if (!nodeIds.has(e.from) || !nodeIds.has(e.to)) return false
      const key = [Math.min(e.from, e.to), Math.max(e.from, e.to)].join('-')
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
    if (filteredNodes.length === 0) {
      setLayout(null)
      setLoading(false)
      return
    }
    const result = layoutGraph(filteredNodes, filteredEdges)
    setLayout({
      ...result,
      nodes: filteredNodes,
      edges: filteredEdges,
      currentRoom: mapData.currentRoom,
      zones: mapData.zones || [],
    })
    setLoading(false)
  }, [mapData, zone])

  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  const handleNodeClick = useCallback((node) => {
    if (node.current) return // already here
    // Could add pathfinding later; for now just show info
  }, [])

  const handleNodeEnter = useCallback((e, node) => {
    const wrap = e.currentTarget.closest('.map-svg-wrap')
    if (!wrap) return
    const rect = wrap.getBoundingClientRect()
    setTooltip({
      node,
      x: e.clientX - rect.left + 14,
      y: e.clientY - rect.top + 14,
    })
  }, [])

  const handleNodeMove = useCallback((e) => {
    const wrap = e.currentTarget.closest('.map-svg-wrap')
    if (!wrap) return
    const rect = wrap.getBoundingClientRect()
    setTooltip(t => t ? {
      ...t,
      x: e.clientX - rect.left + 14,
      y: e.clientY - rect.top + 14,
    } : null)
  }, [])

  const handleNodeLeave = useCallback(() => {
    setTooltip(null)
  }, [])

  if (!open) return null

  return (
    <div className="world-map-modal" onClick={onClose}>
      <div className="world-map-content" onClick={(e) => e.stopPropagation()}>
        <div className="world-map-header">
          <span className="cinzel world-map-title">WORLD MAP</span>
          <div className="map-tabs">
            <button className={`map-tab-btn ${tab === 'rooms' ? 'active' : ''}`} onClick={() => setTab('rooms')}>
              Room Map
            </button>
            <button className={`map-tab-btn ${tab === 'world' ? 'active' : ''}`} onClick={() => setTab('world')}>
              The Annwyn
            </button>
          </div>
          {tab === 'rooms' && (
            <div className="map-legend">
              <span className="map-legend-item"><span className="map-dot current" /> You are here</span>
              <span className="map-legend-item"><span className="map-dot market" /> Market</span>
              <span className="map-legend-item">🪙 Merchant</span>
              <span className="map-legend-item">🔨 Crafting</span>
            </div>
          )}
          <button className="world-map-close" onClick={onClose}>✕</button>
        </div>
        {/* Zone selector — only for Room Map */}
        {tab === 'rooms' && layout && layout.zones && layout.zones.length > 1 && (
          <div className="map-zone-bar">
            <button
              className={`map-zone-btn ${zone === ZONE_ALL ? 'active' : ''}`}
              onClick={() => setZone(ZONE_ALL)}
            >
              All Zones
              <span className="map-zone-count">{mapData?.nodes?.length || 0}</span>
            </button>
            {layout.zones.map(z => (
              <button
                key={z.name}
                className={`map-zone-btn ${zone === z.name ? 'active' : ''}`}
                onClick={() => setZone(z.name)}
              >
                {z.name}
                <span className="map-zone-count">{z.count}</span>
              </button>
            ))}
          </div>
        )}
        <div className={`world-map-body ${tab === 'rooms' ? 'has-sidebar' : ''}`}>
          {tab === 'world' ? (
            <div className="world-map-scroll">
              <img
                src="/art/map/annwyn_map.jpg"
                alt="Map of the Annwyn"
                className="world-map-image"
              />
            </div>
          ) : loading ? (
            <div className="map-loading">Charting the known lands...</div>
          ) : layout ? (
            <>
              <div className="map-svg-wrap">
              <svg
                ref={svgRef}
                viewBox={`0 0 ${layout.width} ${layout.height}`}
                className="map-svg"
                preserveAspectRatio="xMidYMid meet"
              >
                {/* Edges */}
                {layout.edges.map((e, i) => {
                  const from = layout.positions[e.from]
                  const to = layout.positions[e.to]
                  if (!from || !to) return null
                  return (
                    <line
                      key={i}
                      x1={from.x} y1={from.y}
                      x2={to.x} y2={to.y}
                      className="map-edge"
                    />
                  )
                })}
                {/* Nodes — numbered circles */}
                {layout.nodes.map((node, idx) => {
                  const p = layout.positions[node.id]
                  if (!p) return null
                  const color = NODE_COLORS[node.type] || NODE_COLORS.room
                  const num = idx + 1
                  return (
                    <g
                      key={node.id}
                      className={`map-node ${node.current ? 'current' : ''}`}
                      onMouseEnter={(e) => handleNodeEnter(e, { ...node, num })}
                      onMouseMove={handleNodeMove}
                      onMouseLeave={handleNodeLeave}
                    >
                      {node.current && (
                        <circle cx={p.x} cy={p.y} r={22} className="map-node-glow" />
                      )}
                      <circle
                        cx={p.x} cy={p.y}
                        r={node.current ? 16 : 12}
                        fill={color}
                        stroke={node.current ? '#00e5a0' : '#4a3828'}
                        strokeWidth={node.current ? 3 : 1.5}
                        className="map-node-circle"
                      />
                      <text
                        x={p.x} y={p.y + 4}
                        className="map-node-num"
                      >
                        {num}
                      </text>
                    </g>
                  )
                })}
              </svg>
              {tooltip && (
                <div
                  className="map-tooltip"
                  style={{ left: tooltip.x, top: tooltip.y }}
                >
                  <div className="map-tooltip-header">
                    <span
                      className="map-tooltip-dot"
                      style={{ background: NODE_COLORS[tooltip.node.type] || NODE_COLORS.room }}
                    >
                      {tooltip.node.num}
                    </span>
                    <span className="map-tooltip-name">{tooltip.node.name}</span>
                  </div>
                  <div className="map-tooltip-body">
                    {tooltip.node.current && (
                      <div className="map-tooltip-row current">
                        <span className="map-tooltip-icon">✦</span>
                        <span>You are here</span>
                      </div>
                    )}
                    {tooltip.node.hasMerchant && (
                      <div className="map-tooltip-row">
                        <span className="map-tooltip-icon">🪙</span>
                        <span>Merchant</span>
                      </div>
                    )}
                    {tooltip.node.hasCrafting && (
                      <div className="map-tooltip-row">
                        <span className="map-tooltip-icon">🔨</span>
                        <span>Crafting</span>
                      </div>
                    )}
                    {tooltip.node.zone && (
                      <div className="map-tooltip-row zone">
                        <span className="map-tooltip-icon">{NODE_ICONS[tooltip.node.type] || NODE_ICONS.room}</span>
                        <span>{tooltip.node.zone}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
              </div>
              {/* Sidebar key */}
              <div className="map-key">
                <div className="map-key-title cinzel">LOCATIONS</div>
                <div className="map-key-list">
                  {layout.nodes.map((node, idx) => (
                    <div
                      key={node.id}
                      className={`map-key-item ${node.current ? 'current' : ''}`}
                    >
                      <span
                        className="map-key-num"
                        style={{ background: NODE_COLORS[node.type] || NODE_COLORS.room }}
                      >
                        {idx + 1}
                      </span>
                      <span className="map-key-name">{node.name}</span>
                      {node.hasMerchant && <span className="map-key-icon">🪙</span>}
                      {node.hasCrafting && <span className="map-key-icon">🔨</span>}
                      {node.current && <span className="map-key-you">YOU</span>}
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : null}
        </div>
        <div className="world-map-footer">
          <span className="world-map-hint">Your location is highlighted in green</span>
        </div>
      </div>
    </div>
  )
}
