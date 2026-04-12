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

const NODE_ICONS = {
  hasMerchant: '🪙',
  hasCrafting: '🔨',
}

export default function WorldMapModal({ open, onClose, sendCommand, mapData }) {
  const [loading, setLoading] = useState(true)
  const [layout, setLayout] = useState(null)
  const svgRef = useRef(null)

  useEffect(() => {
    if (!open) return
    sendCommand('__map_ui__')
  }, [open, sendCommand])

  useEffect(() => {
    if (mapData && mapData.nodes) {
      // Deduplicate edges
      const seen = new Set()
      const uniqueEdges = mapData.edges.filter(e => {
        const key = [Math.min(e.from, e.to), Math.max(e.from, e.to)].join('-')
        if (seen.has(key)) return false
        seen.add(key)
        return true
      })
      const result = layoutGraph(mapData.nodes, uniqueEdges)
      setLayout({ ...result, nodes: mapData.nodes, edges: uniqueEdges, currentRoom: mapData.currentRoom })
      setLoading(false)
    }
  }, [mapData])

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

  if (!open) return null

  return (
    <div className="world-map-modal" onClick={onClose}>
      <div className="world-map-content" onClick={(e) => e.stopPropagation()}>
        <div className="world-map-header">
          <span className="cinzel world-map-title">WORLD MAP</span>
          <div className="map-legend">
            <span className="map-legend-item"><span className="map-dot current" /> You are here</span>
            <span className="map-legend-item"><span className="map-dot market" /> Market</span>
            <span className="map-legend-item">🪙 Merchant</span>
            <span className="map-legend-item">🔨 Crafting</span>
          </div>
          <button className="world-map-close" onClick={onClose}>✕</button>
        </div>
        <div className="world-map-body">
          {loading ? (
            <div className="map-loading">Charting the known lands...</div>
          ) : layout ? (
            <svg
              ref={svgRef}
              viewBox={`0 0 ${layout.width} ${layout.height}`}
              className="map-svg"
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
              {/* Nodes */}
              {layout.nodes.map(node => {
                const p = layout.positions[node.id]
                if (!p) return null
                const color = NODE_COLORS[node.type] || NODE_COLORS.room
                return (
                  <g
                    key={node.id}
                    className={`map-node ${node.current ? 'current' : ''}`}
                    onClick={() => handleNodeClick(node)}
                  >
                    {/* Glow for current room */}
                    {node.current && (
                      <circle cx={p.x} cy={p.y} r={22} className="map-node-glow" />
                    )}
                    <circle
                      cx={p.x} cy={p.y}
                      r={node.current ? 14 : 10}
                      fill={color}
                      stroke={node.current ? '#00e5a0' : '#4a3828'}
                      strokeWidth={node.current ? 3 : 1.5}
                      className="map-node-circle"
                    />
                    {/* Icons for special features */}
                    {node.hasMerchant && (
                      <text x={p.x + 16} y={p.y - 8} className="map-icon">🪙</text>
                    )}
                    {node.hasCrafting && (
                      <text x={p.x + 16} y={p.y + 8} className="map-icon">🔨</text>
                    )}
                    {/* Room name */}
                    <text
                      x={p.x}
                      y={p.y + (node.current ? 28 : 24)}
                      className={`map-label ${node.current ? 'current' : ''}`}
                    >
                      {node.name}
                    </text>
                  </g>
                )
              })}
            </svg>
          ) : null}
        </div>
        <div className="world-map-footer">
          <span className="world-map-hint">Your location is highlighted in green</span>
        </div>
      </div>
    </div>
  )
}
