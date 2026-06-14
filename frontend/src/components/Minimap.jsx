import { useEffect, useMemo, useRef, useState } from 'react'
import './Minimap.css'

/*
 * Minimap — a zoomed-in, draggable map of the player's CURRENT ZONE,
 * pinned to the top of the right rail. The room graph comes from the
 * same __map_ui__ payload the full WorldMapModal uses.
 *
 * It behaves like a game minimap: zoomed in on the player (the gold X),
 * camera centred on you and following as you walk. Drag the map body to
 * pan and look ahead; it snaps back to follow you on your next move.
 * Click the header (or its ⤢) to open the full world map.
 *
 * Service icons (market/merchant/crafting) deliberately live only on
 * the full map, where there's room to read them — the minimap stays a
 * clean "where am I / what's the shape of the zone" glance.
 */

const ZONE_TINT = {
  Gateway: '#9a8266', Arrival: '#8b5cf6', 'The Mists': '#a8a4a0',
  'The Annwyn': '#8a7e72', Mystvale: '#b89244', Tamris: '#5e8a8c',
  Carran: '#a8624a', Ironhaven: '#6a7585', Harrowgate: '#7a6a8a',
  Arcton: '#7a8a5e', Goldleaf: '#a8a064', Moonfall: '#5a6a8e',
  'The Cirque': '#c0506e',
}

// Zoom WINDOW (world units shown). Smaller = more zoomed in. Edges
// settle ~20 units apart, so a 46-wide window frames the player's room
// and its immediate neighbours; pan to see further.
const WIN_W = 46
const WIN_H = 36

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v))

// Deterministic force-directed layout (no Math.random, stable across
// remounts). Returns WORLD coordinates centred on the graph centroid;
// a gentle centre gravity keeps the graph compact so orphan rooms
// don't drift off.
function layoutZone(nodes, edges) {
  const n = nodes.length
  if (!n) return {}
  if (n === 1) return { [nodes[0].id]: { x: 0, y: 0 } }

  const pos = {}
  nodes.forEach((node, i) => {
    const a = (i / n) * Math.PI * 2
    const r = 26 + (i % 5) * 4
    pos[node.id] = { x: Math.cos(a) * r, y: Math.sin(a) * r }
  })

  const adj = edges.filter(e => pos[e.from] && pos[e.to])
  const REP = 200, SPRING = 0.04, REST = 20, DAMP = 0.82, ITERS = 170, GRAV = 0.02
  const vel = {}
  nodes.forEach(node => { vel[node.id] = { x: 0, y: 0 } })

  for (let it = 0; it < ITERS; it++) {
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const a = nodes[i].id, b = nodes[j].id
        const dx = pos[a].x - pos[b].x, dy = pos[a].y - pos[b].y
        const d = Math.sqrt(dx * dx + dy * dy) || 0.5
        const f = REP / (d * d)
        vel[a].x += (dx / d) * f; vel[a].y += (dy / d) * f
        vel[b].x -= (dx / d) * f; vel[b].y -= (dy / d) * f
      }
    }
    adj.forEach(e => {
      const dx = pos[e.to].x - pos[e.from].x, dy = pos[e.to].y - pos[e.from].y
      const d = Math.sqrt(dx * dx + dy * dy) || 0.5
      const f = SPRING * (d - REST)
      vel[e.from].x += (dx / d) * f; vel[e.from].y += (dy / d) * f
      vel[e.to].x -= (dx / d) * f; vel[e.to].y -= (dy / d) * f
    })
    nodes.forEach(node => {
      const v = vel[node.id]
      v.x -= pos[node.id].x * GRAV
      v.y -= pos[node.id].y * GRAV
      v.x *= DAMP; v.y *= DAMP
      pos[node.id].x += v.x; pos[node.id].y += v.y
    })
  }

  const xs = nodes.map(nd => pos[nd.id].x), ys = nodes.map(nd => pos[nd.id].y)
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2
  const cy = (Math.min(...ys) + Math.max(...ys)) / 2
  nodes.forEach(nd => { pos[nd.id].x -= cx; pos[nd.id].y -= cy })
  return pos
}

export default function Minimap({ mapData, currentRoomId, onExpand, sendCommand }) {
  const requestedRef = useRef(false)
  useEffect(() => {
    if (!mapData && sendCommand && !requestedRef.current) {
      requestedRef.current = true
      sendCommand('__map_ui__')
    }
  }, [mapData, sendCommand])

  const curNode = mapData?.nodes?.find(nd => nd.id === currentRoomId) || null
  const zone = curNode?.zone || mapData?.currentZone || null

  const zoneSig = useMemo(() => {
    if (!mapData?.nodes || !zone) return ''
    const ids = mapData.nodes.filter(nd => nd.zone === zone).map(nd => nd.id).sort((a, b) => a - b)
    return `${zone}:${ids.join(',')}`
  }, [mapData, zone])

  const view = useMemo(() => {
    if (!mapData?.nodes || !zone) return null
    const zoneNodes = mapData.nodes.filter(nd => nd.zone === zone)
    if (!zoneNodes.length) return null
    const ids = new Set(zoneNodes.map(nd => nd.id))
    const zoneEdges = (mapData.edges || []).filter(e => ids.has(e.from) && ids.has(e.to))
    const seen = new Set(), lines = []
    zoneEdges.forEach(e => {
      const k = e.from < e.to ? `${e.from}-${e.to}` : `${e.to}-${e.from}`
      if (seen.has(k)) return
      seen.add(k); lines.push(e)
    })
    const positions = layoutZone(zoneNodes, zoneEdges)
    const xs = zoneNodes.map(nd => positions[nd.id]?.x ?? 0)
    const ys = zoneNodes.map(nd => positions[nd.id]?.y ?? 0)
    const bounds = {
      minX: Math.min(...xs), maxX: Math.max(...xs),
      minY: Math.min(...ys), maxY: Math.max(...ys),
    }
    return { zoneNodes, lines, positions, bounds }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [zoneSig])

  // ── Camera: follows the player; drag to pan; snaps back on move ──
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [dragging, setDragging] = useState(false)
  const canvasRef = useRef(null)
  const dragRef = useRef(null)

  useEffect(() => { setPan({ x: 0, y: 0 }) }, [currentRoomId, zoneSig])

  const worldPerPx = () => {
    const el = canvasRef.current
    if (!el) return WIN_W / 200
    const r = el.getBoundingClientRect()
    const scale = Math.min(r.width / WIN_W, r.height / WIN_H) // 'meet'
    return scale > 0 ? 1 / scale : WIN_W / 200
  }

  const onPointerDown = (e) => {
    if (!view) return
    e.currentTarget.setPointerCapture?.(e.pointerId)
    dragRef.current = { sx: e.clientX, sy: e.clientY, px: pan.x, py: pan.y }
    setDragging(true)
  }
  const onPointerMove = (e) => {
    const d = dragRef.current
    if (!d) return
    const wpp = worldPerPx()
    setPan({ x: d.px - (e.clientX - d.sx) * wpp, y: d.py - (e.clientY - d.sy) * wpp })
  }
  const onPointerUp = (e) => {
    dragRef.current = null
    setDragging(false)
    e.currentTarget.releasePointerCapture?.(e.pointerId)
  }

  const tint = ZONE_TINT[zone] || '#9a8266'
  const playerPos = (view && currentRoomId != null && view.positions[currentRoomId]) || { x: 0, y: 0 }

  let camX = playerPos.x + pan.x
  let camY = playerPos.y + pan.y
  if (view) {
    const mx = WIN_W * 0.5, my = WIN_H * 0.5
    camX = clamp(camX, view.bounds.minX - mx, view.bounds.maxX + mx)
    camY = clamp(camY, view.bounds.minY - my, view.bounds.maxY + my)
  }
  const camTransform = `translate(${WIN_W / 2 - camX} ${WIN_H / 2 - camY})`

  return (
    <div className="minimap">
      <div className="minimap-frame">
        <button
          type="button"
          className="minimap-header"
          onClick={onExpand}
          title="Open the full world map"
        >
          <span className="minimap-label">{zone || 'Locating…'}</span>
          <span className="minimap-expand" aria-hidden="true">⤢</span>
        </button>
        <div
          ref={canvasRef}
          className={`minimap-canvas${dragging ? ' dragging' : ''}`}
          aria-label="Zone minimap. Drag to pan."
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
        >
          {view ? (
            <svg viewBox={`0 0 ${WIN_W} ${WIN_H}`} preserveAspectRatio="xMidYMid meet">
              <g
                className="minimap-camera"
                transform={camTransform}
                style={{ transition: dragging ? 'none' : 'transform 0.35s ease' }}
              >
                {view.lines.map((e, i) => {
                  const a = view.positions[e.from], b = view.positions[e.to]
                  if (!a || !b) return null
                  return <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y} className="minimap-edge" />
                })}
                {view.zoneNodes.map(nd => {
                  const p = view.positions[nd.id]
                  if (!p || nd.id === currentRoomId) return null
                  return <circle key={nd.id} cx={p.x} cy={p.y} r="1.8" fill={tint} className="minimap-node" />
                })}
                {/* Current room: the gold X, drawn last so it's on top. */}
                <g className="minimap-here" transform={`translate(${playerPos.x} ${playerPos.y})`}>
                  <circle r="4.6" className="minimap-here-halo" />
                  <path d="M -3 -3 L 3 3 M -3 3 L 3 -3" className="minimap-x" />
                </g>
              </g>
            </svg>
          ) : (
            <div className="minimap-empty">mapping…</div>
          )}
        </div>
      </div>
    </div>
  )
}
