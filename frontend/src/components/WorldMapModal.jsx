import { useEffect, useState, useCallback, useRef, useMemo } from 'react'
import './WorldMapModal.css'

// ── Seeded PRNG (mulberry32) ─────────────────────────────────────────
// Deterministic layout: same (zone, mapData) → same positions → same
// label slots across reopens. Required so the always-on cartouche
// labels don't flicker / re-pack on every render.
function mulberry32(seed) {
  let a = seed >>> 0
  return function () {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// Simple force-directed layout for room graph (deterministic).
function layoutGraph(nodes, edges) {
  if (!nodes.length) return { positions: {}, width: 0, height: 0 }

  // Build adjacency
  const adj = {}
  nodes.forEach(n => { adj[n.id] = [] })
  edges.forEach(e => {
    if (adj[e.from]) adj[e.from].push(e.to)
    if (adj[e.to]) adj[e.to].push(e.from)
  })

  // Seed the PRNG from a stable value so positions are reproducible
  // for a given filtered node set.
  const seed = nodes.length * 2654435761 + nodes.reduce((s, n) => s + n.id, 0)
  const rng = mulberry32(seed)

  // Initialize positions on a ring (seeded jitter).
  const pos = {}
  const W = 1040, H = 600
  nodes.forEach((n, i) => {
    const angle = (i / nodes.length) * Math.PI * 2
    const r = 150 + rng() * 100
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
      // Keep in bounds (new wider W)
      pos[n.id].x = Math.max(60, Math.min(W - 60, pos[n.id].x))
      pos[n.id].y = Math.max(40, Math.min(H - 40, pos[n.id].y))
    })
  }

  return { positions: pos, width: W, height: H }
}

// Per-zone palette — gives the map a sense of place at a glance.
// Each settlement gets a tinted base color matching its canon vibe:
// Mystvale gold, Tamris sea-grey, Carran rust, Ironhaven steel,
// Harrowgate cold purple, etc. Falls through to the type-based
// palette for rooms with no zone match.
const ZONE_COLORS = {
  'Gateway':     '#9a8266',
  'Arrival':     '#8b5cf6',
  'The Mists':   '#a8a4a0',
  'The Annwyn':  '#8a7e72',
  'Mystvale':    '#b89244',
  'Tamris':      '#5e8a8c',
  'Carran':      '#a8624a',
  'Ironhaven':   '#6a7585',
  'Harrowgate':  '#7a6a8a',
  'Arcton':      '#7a8a5e',
  'Goldleaf':    '#a8a064',
  'Moonfall':    '#5a6a8e',
  'The Cirque':  '#c0506e',
}

// Fallback per-type palette (used when zone isn't in ZONE_COLORS).
const TYPE_COLORS = {
  room: '#9a8266',
  weather: '#6a8a6a',
  market: '#d4af37',
  chargen: '#8b5cf6',
}

function colorFor(node) {
  return ZONE_COLORS[node.zone] || TYPE_COLORS[node.type] || TYPE_COLORS.room
}

const ZONE_ALL = '__all__'

const NODE_ICONS = {
  room: '🏛',
  weather: '🌲',
  market: '🪙',
  chargen: '✦',
}

// Type glyphs that earn a place on the cartouche name line. Plain rooms
// get no prefix (their zone is read from the tinted circle); only weather
// and chargen add distinguishing signal.
const TYPE_PREFIX = {
  weather: '🌲',
  chargen: '✦',
}

// ── Service indicators ──────────────────────────────────────────────
// A room can advertise up to three services at once. These definitions
// are the single source of truth shared with the legend, the node
// badges, and the cartouche labels. The `color` here is the SAME
// mapping the Minimap uses for its micro-dots, so players learn one
// colour language across both surfaces:
//   Market   🪙 gold   #d4af37  (the marketplace itself)
//   Merchant ⚖  green  #a3b5a8  (a shop/merchant NPC stands here)
//   Crafting ⚒  copper #c87f4a  (a forge or workbench is here)
const SERVICES = [
  { key: 'market', label: 'Market', glyph: '🪙', color: '#d4af37', has: n => n.type === 'market' },
  { key: 'merchant', label: 'Merchant', glyph: '⚖', color: '#a3b5a8', has: n => !!n.hasMerchant },
  { key: 'crafting', label: 'Crafting', glyph: '⚒', color: '#c87f4a', has: n => !!n.hasCrafting },
]

function servicesFor(node) {
  return SERVICES.filter(s => s.has(node))
}

// ── Label placement geometry ─────────────────────────────────────────
// Char-width estimate for proportional Cinzel — tuned against the
// longest real names (e.g. "Raven's Rest Graveyard"). Over-reserve a
// touch so dense zones don't false-negative on collisions.
const CHAR_W = 6.4          // px per name character
const GLYPH_W = 9.5         // px per service-glyph slot
const LABEL_PAD = 8         // box horizontal padding
const LABEL_H = 16          // single-line plate height
const PLATE_GAP = 6         // gap between circle edge and plate

function labelDims(node, displayName) {
  const svcCount = servicesFor(node).length
  const prefix = TYPE_PREFIX[node.type] ? 1 : 0
  const w = displayName.length * CHAR_W + (svcCount + prefix) * GLYPH_W + LABEL_PAD * 2
  const h = node.current ? LABEL_H + 4 : LABEL_H
  return { w: w + 4, h: h + 4 } // +pad over-reserve
}

function rectsOverlap(a, b) {
  return Math.abs(a.cx - b.cx) * 2 < a.w + b.w &&
         Math.abs(a.cy - b.cy) * 2 < a.h + b.h
}

// AABB vs circle overlap (treat circle as its bounding box — cheap,
// slightly conservative, which is what we want for legibility).
function rectOverlapsCircle(rect, circle) {
  const cw = circle.r * 2 + 4
  return Math.abs(rect.cx - circle.cx) * 2 < rect.w + cw &&
         Math.abs(rect.cy - circle.cy) * 2 < rect.h + cw
}

// Compute a box centre for a given anchor side relative to a node.
function anchorBox(p, nodeR, dims, side) {
  const halfW = dims.w / 2
  const halfH = dims.h / 2
  const gap = nodeR + PLATE_GAP
  switch (side) {
    case 'bottom': return { cx: p.x, cy: p.y + gap + halfH }
    case 'top':    return { cx: p.x, cy: p.y - gap - halfH }
    case 'right':  return { cx: p.x + gap + halfW, cy: p.y }
    case 'left':   return { cx: p.x - gap - halfW, cy: p.y }
    default:       return { cx: p.x, cy: p.y + gap + halfH }
  }
}

// ── Deterministic placement pass ─────────────────────────────────────
// Runs once per (zone, layout). Returns a map id → placement:
//   { side, box:{cx,cy,w,h}, crowded, displayName, leader }
function placeLabels(nodes, positions, currentRoom, W, H) {
  const placed = []           // boxes already committed
  const circles = nodes
    .map(n => {
      const p = positions[n.id]
      if (!p) return null
      return { cx: p.x, cy: p.y, r: n.current ? 16 : 12 }
    })
    .filter(Boolean)

  // Importance order: current room first, then service-bearing, then
  // graph degree (edge count) descending.
  const degree = {}
  nodes.forEach(n => { degree[n.id] = 0 })
  // degree is approximated by how many other nodes share an edge —
  // but we don't have edges here; caller passes degree via node._deg.
  const order = [...nodes].sort((a, b) => {
    if (a.current !== b.current) return a.current ? -1 : 1
    const sa = servicesFor(a).length, sb = servicesFor(b).length
    if (sa !== sb) return sb - sa
    return (b._deg || 0) - (a._deg || 0)
  })

  const result = {}

  for (const node of order) {
    const p = positions[node.id]
    if (!p) continue
    const nodeR = node.current ? 16 : 12
    const dims = labelDims(node, node.name)

    // Edge-aware anchor priority: grow text inward, not off-canvas.
    let sides = ['bottom', 'top', 'right', 'left']
    if (p.x < 90) sides = ['bottom', 'top', 'right', 'left'] // prefer right over left
    else if (p.x > W - 90) sides = ['bottom', 'top', 'left', 'right']
    if (p.y < 60) sides = sides.filter(s => s !== 'top').concat('top')
    else if (p.y > H - 60) sides = sides.filter(s => s !== 'bottom').concat('bottom')

    let chosen = null
    for (const side of sides) {
      const c = anchorBox(p, nodeR, dims, side)
      const box = { cx: c.cx, cy: c.cy, w: dims.w, h: dims.h }
      const hitsBox = placed.some(b => rectsOverlap(box, b))
      const hitsCircle = circles.some(cir =>
        !(cir.cx === p.x && cir.cy === p.y) && rectOverlapsCircle(box, cir))
      if (!hitsBox && !hitsCircle) { chosen = { side, box }; break }
    }

    // Micro-relaxation if every anchor collided.
    let crowded = false
    if (!chosen) {
      const side = sides[0]
      const c = anchorBox(p, nodeR, dims, side)
      let box = { cx: c.cx, cy: c.cy, w: dims.w, h: dims.h }
      const horizontal = side === 'left' || side === 'right'
      for (let it = 0; it < 6; it++) {
        // Find deepest overlap & nudge along the relax axis.
        let depth = 0
        for (const b of placed) {
          if (rectsOverlap(box, b)) {
            const ov = horizontal
              ? (box.h + b.h) / 2 - Math.abs(box.cy - b.cy)
              : (box.w + b.w) / 2 - Math.abs(box.cx - b.cx)
            if (ov > depth) depth = ov
          }
        }
        if (depth <= 0) break
        const nudge = Math.max(-14, Math.min(14, depth))
        if (horizontal) box.cy += nudge
        else box.cx += nudge
        // clamp to canvas
        box.cx = Math.max(box.w / 2, Math.min(W - box.w / 2, box.cx))
        box.cy = Math.max(box.h / 2, Math.min(H - box.h / 2, box.cy))
      }
      const stillHits = placed.some(b => rectsOverlap(box, b))
      crowded = stillHits
      chosen = { side, box }
    }

    // Crowded fallback: truncate name, reduce opacity (rendered by CSS).
    let displayName = node.name
    if (crowded && node.name.length > 14) {
      displayName = node.name.slice(0, 14).trimEnd() + '…'
    }

    // Leader line for any non-bottom anchor or displaced/crowded box.
    const leader = chosen.side !== 'bottom' || crowded

    placed.push(chosen.box)
    result[node.id] = { side: chosen.side, box: chosen.box, crowded, displayName, leader }
  }

  return result
}

export default function WorldMapModal({ open, onClose, sendCommand, mapData }) {
  const [loading, setLoading] = useState(true)
  const [layout, setLayout] = useState(null)
  const [tab, setTab] = useState('rooms')
  const [zone, setZone] = useState(ZONE_ALL)
  const [tooltip, setTooltip] = useState(null) // {node, x, y}
  const [hoveredId, setHoveredId] = useState(null)
  const [view, setView] = useState({ tx: 0, ty: 0, k: 1 }) // pan/zoom transform
  const svgRef = useRef(null)
  const panRef = useRef(null) // active pan drag state

  const reduceMotion = useRef(false)
  useEffect(() => {
    reduceMotion.current = window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
  }, [])

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
    // annotate degree for placement importance ordering
    const deg = {}
    filteredNodes.forEach(n => { deg[n.id] = 0 })
    filteredEdges.forEach(e => {
      if (deg[e.from] != null) deg[e.from]++
      if (deg[e.to] != null) deg[e.to]++
    })
    const annotated = filteredNodes.map(n => ({ ...n, _deg: deg[n.id] || 0 }))
    const result = layoutGraph(annotated, filteredEdges)
    setLayout({
      ...result,
      nodes: annotated,
      edges: filteredEdges,
      currentRoom: mapData.currentRoom,
      zones: mapData.zones || [],
      isAllZones: zone === ZONE_ALL,
    })
    setLoading(false)
  }, [mapData, zone])

  // Deterministic label-placement pass — once per (zone, layout).
  // Gated to single-zone mode; All-Zones falls back to no label storm.
  const placements = useMemo(() => {
    if (!layout || layout.isAllZones) return null
    return placeLabels(
      layout.nodes, layout.positions, layout.currentRoom,
      layout.width, layout.height,
    )
  }, [layout])

  // Auto-fit framing: frame the visible nodes' bbox centred on layout
  // change (zone / mapData) and first load. Conservative k (≈1) because
  // labels are always-on.
  useEffect(() => {
    if (!layout || !layout.nodes.length) return
    const pts = layout.nodes.map(n => layout.positions[n.id]).filter(Boolean)
    if (!pts.length) return
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
    pts.forEach(p => {
      if (p.x < minX) minX = p.x
      if (p.y < minY) minY = p.y
      if (p.x > maxX) maxX = p.x
      if (p.y > maxY) maxY = p.y
    })
    const pad = 60 // room for cartouche plates around outer nodes
    minX -= pad; minY -= pad; maxX += pad; maxY += pad
    const bw = Math.max(1, maxX - minX)
    const bh = Math.max(1, maxY - minY)
    const k = Math.max(0.6, Math.min(2.5, Math.min(layout.width / bw, layout.height / bh)))
    // centre the bbox in the viewBox
    const cx = (minX + maxX) / 2
    const cy = (minY + maxY) / 2
    const tx = layout.width / 2 - cx * k
    const ty = layout.height / 2 - cy * k
    setView({ tx, ty, k })
  }, [layout])

  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  // ── viewBox ↔ pixel scale helper ──
  const viewToPixel = useCallback(() => {
    const svg = svgRef.current
    if (!svg || !layout) return 1
    const rect = svg.getBoundingClientRect()
    return rect.width / layout.width
  }, [layout])

  // ── Pan (drag on SVG background) ──
  const handleSvgPointerDown = useCallback((e) => {
    // Only the background starts a pan — node groups stopPropagation.
    panRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      tx: view.tx,
      ty: view.ty,
    }
    e.currentTarget.setPointerCapture?.(e.pointerId)
  }, [view])

  const handleSvgPointerMove = useCallback((e) => {
    if (!panRef.current) return
    const scale = viewToPixel() || 1
    const dx = (e.clientX - panRef.current.startX) / scale
    const dy = (e.clientY - panRef.current.startY) / scale
    setView(v => ({ ...v, tx: panRef.current.tx + dx, ty: panRef.current.ty + dy }))
  }, [viewToPixel])

  const handleSvgPointerUp = useCallback((e) => {
    panRef.current = null
    e.currentTarget.releasePointerCapture?.(e.pointerId)
  }, [])

  // ── Wheel zoom, anchored at pointer ──
  const handleWheel = useCallback((e) => {
    if (!layout) return
    e.preventDefault()
    const svg = svgRef.current
    if (!svg) return
    const rect = svg.getBoundingClientRect()
    const scale = rect.width / layout.width || 1
    // pointer in SVG (pre-transform viewBox) coords
    const px = (e.clientX - rect.left) / scale
    const py = (e.clientY - rect.top) / scale
    setView(v => {
      const factor = e.deltaY < 0 ? 1.12 : 1 / 1.12
      const k = Math.max(0.6, Math.min(2.5, v.k * factor))
      if (k === v.k) return v
      // svg-space point currently under cursor:
      //   sx = (px - tx) / k  must stay fixed → tx' = px - sx*k'
      const sx = (px - v.tx) / v.k
      const sy = (py - v.ty) / v.k
      return { k, tx: px - sx * k, ty: py - sy * k }
    })
  }, [layout])

  const zoomBy = useCallback((factor) => {
    if (!layout) return
    setView(v => {
      const k = Math.max(0.6, Math.min(2.5, v.k * factor))
      if (k === v.k) return v
      // zoom toward viewBox centre
      const px = layout.width / 2, py = layout.height / 2
      const sx = (px - v.tx) / v.k
      const sy = (py - v.ty) / v.k
      return { k, tx: px - sx * k, ty: py - sy * k }
    })
  }, [layout])

  const fitView = useCallback(() => {
    if (!layout || !layout.nodes.length) return
    const pts = layout.nodes.map(n => layout.positions[n.id]).filter(Boolean)
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
    pts.forEach(p => {
      if (p.x < minX) minX = p.x
      if (p.y < minY) minY = p.y
      if (p.x > maxX) maxX = p.x
      if (p.y > maxY) maxY = p.y
    })
    const pad = 60
    minX -= pad; minY -= pad; maxX += pad; maxY += pad
    const bw = Math.max(1, maxX - minX), bh = Math.max(1, maxY - minY)
    const k = Math.max(0.6, Math.min(2.5, Math.min(layout.width / bw, layout.height / bh)))
    const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2
    setView({ k, tx: layout.width / 2 - cx * k, ty: layout.height / 2 - cy * k })
  }, [layout])

  const handleNodeEnter = useCallback((e, node) => {
    const wrap = e.currentTarget.closest('.map-svg-wrap')
    setHoveredId(node.id)
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
    setHoveredId(null)
  }, [])

  if (!open) return null

  // Reorder rendered nodes so the hovered one paints last (top z-order).
  const renderNodes = layout
    ? (hoveredId == null
        ? layout.nodes
        : [...layout.nodes.filter(n => n.id !== hoveredId),
           ...layout.nodes.filter(n => n.id === hoveredId)])
    : []

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
            <div className="map-legend" role="img" aria-label="Map key: a glowing star marks your location; service icons mark market, merchant, and crafting rooms">
              <span className="map-legend-item"><span className="map-dot current" /> You are here</span>
              {SERVICES.map(s => (
                <span key={s.key} className="map-legend-item">
                  <span className="map-legend-glyph" style={{ color: s.color }} aria-hidden="true">{s.glyph}</span>
                  {s.label}
                </span>
              ))}
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
        <div className="world-map-body">
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
            <div className="map-svg-wrap">
              {/* Pan/zoom corner controls */}
              <div className="map-zoom-controls">
                <button className="map-zoom-btn" onClick={() => zoomBy(1.2)} aria-label="Zoom in" title="Zoom in">+</button>
                <button className="map-zoom-btn" onClick={() => zoomBy(1 / 1.2)} aria-label="Zoom out" title="Zoom out">−</button>
                <button className="map-zoom-btn" onClick={fitView} aria-label="Fit map" title="Fit to view">⤢</button>
              </div>
              <svg
                ref={svgRef}
                viewBox={`0 0 ${layout.width} ${layout.height}`}
                className="map-svg"
                preserveAspectRatio="xMidYMid meet"
                onPointerDown={handleSvgPointerDown}
                onPointerMove={handleSvgPointerMove}
                onPointerUp={handleSvgPointerUp}
                onPointerLeave={handleSvgPointerUp}
                onWheel={handleWheel}
              >
                <g
                  className={`map-pan-group ${reduceMotion.current ? 'no-motion' : ''}`}
                  transform={`translate(${view.tx},${view.ty}) scale(${view.k})`}
                >
                {/* Edges — edges connected to the current room get a
                    bright phosphor highlight so the player can see at
                    a glance which directions they can move. */}
                {layout.edges.map((e, i) => {
                  const from = layout.positions[e.from]
                  const to = layout.positions[e.to]
                  if (!from || !to) return null
                  const adjacent = e.from === layout.currentRoom || e.to === layout.currentRoom
                  return (
                    <line
                      key={i}
                      x1={from.x} y1={from.y}
                      x2={to.x} y2={to.y}
                      className={`map-edge ${adjacent ? 'adjacent' : ''}`}
                    />
                  )
                })}
                {/* Nodes — tinted discs with always-on cartouche labels */}
                {renderNodes.map((node) => {
                  const p = layout.positions[node.id]
                  if (!p) return null
                  const color = colorFor(node)
                  const svcs = servicesFor(node)
                  const nodeR = node.current ? 16 : 12
                  // Service badge discs ride above the node, centred and
                  // spaced so 1–3 read clearly (kept as redundant signal).
                  const badgeStep = 16
                  const badgeY = p.y - nodeR - 9
                  const badgeX0 = p.x - ((svcs.length - 1) * badgeStep) / 2

                  const place = placements && placements[node.id]
                  const isHovered = hoveredId === node.id
                  const prefix = TYPE_PREFIX[node.type]

                  return (
                    <g
                      key={node.id}
                      className={`map-node ${node.current ? 'current' : ''} ${isHovered ? 'hovered' : ''}`}
                      onMouseEnter={(e) => handleNodeEnter(e, node)}
                      onMouseMove={handleNodeMove}
                      onMouseLeave={handleNodeLeave}
                      onPointerDown={(e) => e.stopPropagation()}
                    >
                      {node.current && (
                        <circle cx={p.x} cy={p.y} r={22} className="map-node-glow" />
                      )}
                      <circle
                        cx={p.x} cy={p.y}
                        r={nodeR}
                        fill={color}
                        stroke={node.current ? '#00e5a0' : '#4a3828'}
                        strokeWidth={node.current ? 3 : 1.5}
                        className="map-node-circle"
                      />
                      {/* Service badges — one glyph per available
                          service (market / merchant / crafting). */}
                      {svcs.map((s, si) => {
                        const bx = badgeX0 + si * badgeStep
                        return (
                          <g key={s.key} className="map-node-badge" transform={`translate(${bx} ${badgeY})`}>
                            <circle r={7} className="map-node-badge-bg" stroke={s.color} />
                            <text className="map-node-badge-glyph" y={3.5}>{s.glyph}</text>
                          </g>
                        )
                      })}

                      {/* Current-room promoted plate (always rendered). */}
                      {node.current && (
                        <text
                          x={p.x} y={p.y + nodeR + 18}
                          className="map-node-here-label"
                        >
                          ✦ {node.name} ✦
                        </text>
                      )}

                      {/* Always-on cartouche label (single-zone only,
                          non-current rooms). */}
                      {place && !node.current && (
                        <g
                          className={`map-cartouche ${place.crowded ? 'crowded' : ''} ${isHovered ? 'hovered' : ''}`}
                        >
                          {place.leader && (
                            <line
                              x1={p.x} y1={p.y}
                              x2={place.box.cx} y2={place.box.cy}
                              className="map-cartouche-leader"
                            />
                          )}
                          {/* Darkened pill backing only when hovered/focused. */}
                          {isHovered && (
                            <rect
                              x={place.box.cx - place.box.w / 2}
                              y={place.box.cy - place.box.h / 2}
                              width={place.box.w}
                              height={place.box.h}
                              rx={3}
                              className="map-cartouche-pill"
                            />
                          )}
                          <text
                            x={place.box.cx} y={place.box.cy + 3.5}
                            textAnchor="middle"
                            className="map-cartouche-text"
                          >
                            {prefix && <tspan className="map-cartouche-type">{prefix} </tspan>}
                            {place.displayName.toUpperCase()}
                            {svcs.map(s => (
                              <tspan key={s.key} style={{ fill: s.color }}>{' ' + s.glyph}</tspan>
                            ))}
                          </text>
                        </g>
                      )}
                    </g>
                  )
                })}
                </g>
              </svg>
              {tooltip && (
                <div
                  className="map-tooltip"
                  style={{ left: tooltip.x, top: tooltip.y }}
                >
                  <div className="map-tooltip-header">
                    <span
                      className="map-tooltip-dot"
                      style={{ background: colorFor(tooltip.node) }}
                      aria-hidden="true"
                    />
                    <span className="map-tooltip-name">{tooltip.node.name}</span>
                  </div>
                  <div className="map-tooltip-body">
                    {tooltip.node.current && (
                      <div className="map-tooltip-row current">
                        <span className="map-tooltip-icon">✦</span>
                        <span>You are here</span>
                      </div>
                    )}
                    {servicesFor(tooltip.node).map(s => (
                      <div key={s.key} className="map-tooltip-row">
                        <span className="map-tooltip-icon" style={{ color: s.color }}>{s.glyph}</span>
                        <span>{s.label}</span>
                      </div>
                    ))}
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
          ) : null}
        </div>
        <div className="world-map-footer">
          <span className="world-map-hint">Your location is marked with a glowing star — names and services are labeled on the map.</span>
        </div>
      </div>
    </div>
  )
}
