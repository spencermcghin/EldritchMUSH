import { useEffect, useMemo, useRef } from 'react'
import './Minimap.css'

/*
 * Minimap — a compact, always-on map of the player's CURRENT ZONE,
 * pinned to the top of the right rail. The room graph comes from the
 * same __map_ui__ payload the full WorldMapModal uses; the live
 * position (the gold X) tracks oobState.currentRoomId, which room_meta
 * refreshes on every move. Clicking opens the full world map.
 *
 * The layout is computed per-zone and memoized on a stable zone
 * signature, so walking between rooms in the same zone only moves the
 * marker — the rooms themselves stay put.
 */

// Muted zone tints (a quieter echo of the full map's palette).
const ZONE_TINT = {
  Gateway: '#9a8266', Arrival: '#8b5cf6', 'The Mists': '#a8a4a0',
  'The Annwyn': '#8a7e72', Mystvale: '#b89244', Tamris: '#5e8a8c',
  Carran: '#a8624a', Ironhaven: '#6a7585', Harrowgate: '#7a6a8a',
  Arcton: '#7a8a5e', Goldleaf: '#a8a064', Moonfall: '#5a6a8e',
  'The Cirque': '#c0506e',
}

const VIEW_W = 100
const VIEW_H = 78

// ── Service colour mapping ──────────────────────────────────────────
// Emoji are illegible at this scale, so services are shown as tiny
// colour-coded micro-dots instead. The colours MUST match the full
// world map's legend so the language is learnable across surfaces:
//   Market   gold   #d4af37   (the marketplace itself: type === 'market')
//   Merchant green  #a3b5a8   (a shop/merchant NPC: hasMerchant)
//   Crafting copper #c87f4a   (a forge/workbench: hasCrafting)
// Ordered by priority — when space is tight the first one wins.
const SERVICES = [
  { key: 'market', color: '#d4af37', has: n => n.type === 'market' },
  { key: 'merchant', color: '#a3b5a8', has: n => !!n.hasMerchant },
  { key: 'crafting', color: '#c87f4a', has: n => !!n.hasCrafting },
]

function servicesFor(node) {
  return SERVICES.filter(s => s.has(node))
}

// Deterministic force-directed layout (no Math.random, so the map is
// stable across remounts), normalized into the VIEW box.
function layoutZone(nodes, edges) {
  const n = nodes.length
  if (!n) return {}
  if (n === 1) return { [nodes[0].id]: { x: VIEW_W / 2, y: VIEW_H / 2 } }

  const pos = {}
  nodes.forEach((node, i) => {
    const a = (i / n) * Math.PI * 2
    // index-based radius wobble keeps initial positions distinct
    // without randomness
    const r = 26 + (i % 5) * 4
    pos[node.id] = { x: 50 + Math.cos(a) * r, y: 39 + Math.sin(a) * r }
  })

  const adj = edges.filter(e => pos[e.from] && pos[e.to])
  const REP = 220, SPRING = 0.04, REST = 22, DAMP = 0.82, ITERS = 140
  const vel = {}
  nodes.forEach(node => { vel[node.id] = { x: 0, y: 0 } })

  for (let it = 0; it < ITERS; it++) {
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const a = nodes[i].id, b = nodes[j].id
        let dx = pos[a].x - pos[b].x, dy = pos[a].y - pos[b].y
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
      v.x *= DAMP; v.y *= DAMP
      pos[node.id].x += v.x; pos[node.id].y += v.y
    })
  }

  // Normalize into the view box with a margin.
  const xs = nodes.map(nd => pos[nd.id].x), ys = nodes.map(nd => pos[nd.id].y)
  const minX = Math.min(...xs), maxX = Math.max(...xs)
  const minY = Math.min(...ys), maxY = Math.max(...ys)
  const M = 12
  const sx = (maxX - minX) || 1, sy = (maxY - minY) || 1
  nodes.forEach(nd => {
    pos[nd.id].x = M + ((pos[nd.id].x - minX) / sx) * (VIEW_W - 2 * M)
    pos[nd.id].y = M + ((pos[nd.id].y - minY) / sy) * (VIEW_H - 2 * M)
  })
  return pos
}

export default function Minimap({ mapData, currentRoomId, onExpand, sendCommand }) {
  // Pull the graph once if we don't have it yet.
  const requestedRef = useRef(false)
  useEffect(() => {
    if (!mapData && sendCommand && !requestedRef.current) {
      requestedRef.current = true
      sendCommand('__map_ui__')
    }
  }, [mapData, sendCommand])

  const curNode = mapData?.nodes?.find(nd => nd.id === currentRoomId) || null
  const zone = curNode?.zone || mapData?.currentZone || null

  // Stable signature: layout only recomputes when the zone or its set
  // of rooms changes — not on every step within a zone.
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
    // Dedupe bidirectional edges for cleaner lines.
    const seen = new Set(), lines = []
    zoneEdges.forEach(e => {
      const k = e.from < e.to ? `${e.from}-${e.to}` : `${e.to}-${e.from}`
      if (seen.has(k)) return
      seen.add(k); lines.push(e)
    })
    return { zoneNodes, lines, positions: layoutZone(zoneNodes, zoneEdges) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [zoneSig])

  const tint = ZONE_TINT[zone] || '#9a8266'
  const cur = view && currentRoomId != null ? view.positions[currentRoomId] : null

  return (
    <div
      className="minimap"
      role="button"
      tabIndex={0}
      title="Open the full world map"
      onClick={onExpand}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onExpand?.() }}
    >
      <div className="minimap-frame">
        <div className="minimap-header">
          <span className="minimap-label">{zone || 'Locating…'}</span>
          <span className="minimap-expand" aria-hidden="true">⤢</span>
        </div>
        <div className="minimap-canvas">
          {view ? (
            <svg viewBox={`0 0 ${VIEW_W} ${VIEW_H}`} preserveAspectRatio="xMidYMid meet">
              {view.lines.map((e, i) => {
                const a = view.positions[e.from], b = view.positions[e.to]
                if (!a || !b) return null
                return <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y} className="minimap-edge" />
              })}
              {view.zoneNodes.map(nd => {
                const p = view.positions[nd.id]
                if (!p) return null
                const here = nd.id === currentRoomId
                const svcs = servicesFor(nd)
                // The current room's body is the gold X (drawn last, on
                // top); we still render its service dots underneath so a
                // marketplace you're standing in still reads as one.
                return (
                  <g key={nd.id}>
                    {!here && (
                      <circle
                        cx={p.x} cy={p.y} r={svcs.length ? 2.6 : 2}
                        fill={tint}
                        className="minimap-node"
                      />
                    )}
                    {/* Service micro-dots — up to three, fanned in a tiny
                        arc above the node, colour-coded to the full map's
                        legend. */}
                    {svcs.map((s, si) => {
                      const span = (svcs.length - 1) * 0.9
                      const off = -span / 2 + si * 0.9
                      return (
                        <circle
                          key={s.key}
                          cx={p.x + off} cy={p.y - 3.4}
                          r={1.05}
                          fill={s.color}
                          className="minimap-svc-dot"
                        />
                      )
                    })}
                  </g>
                )
              })}
              {cur && (
                <g className="minimap-here" transform={`translate(${cur.x} ${cur.y})`}>
                  <circle r="5.5" className="minimap-here-halo" />
                  <path d="M -3 -3 L 3 3 M -3 3 L 3 -3" className="minimap-x" />
                </g>
              )}
            </svg>
          ) : (
            <div className="minimap-empty">mapping…</div>
          )}
        </div>
      </div>
    </div>
  )
}
