import { useMemo } from 'react'
import { detectBiome } from '../data/biomes'
import './RoomView.css'

// Decode HTML entities
function decodeEntities(str) {
  const el = typeof document !== 'undefined' ? document.createElement('textarea') : null
  if (el) {
    el.innerHTML = str
    return el.value
  }
  return str.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&').replace(/&quot;/g, '"')
}

// Parse room data from game text messages
function parseRoomData(messages) {
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i]

    // Strip HTML tags, then decode entities — check ALL message types
    const raw = decodeEntities((msg.content || '').replace(/<[^>]*>/g, ''))

    const hasExits = /Exits?:/i.test(raw)
    if (!hasExits) continue

    // DEBUG: log the raw text and line split to help diagnose title parsing
    if (typeof window !== 'undefined' && window.__ROOM_DEBUG) {
      const lines = raw.split(/\n/).map(l => l.trim()).filter(Boolean)
      console.log('[RoomView parseRoomData] raw length:', raw.length,
        'lines:', lines.length,
        'line0:', JSON.stringify(lines[0]?.substring(0, 80)),
        'hasId:', /\(#\d+\)/.test(raw))
    }

    let roomName = ''
    let description = ''
    let exits = []
    let characters = []
    let items = []

    // Evennia room format: "RoomName(#id)Description...Exits: ...Characters: ..."
    // Or with line breaks: "RoomName\nDescription\nExits: ..."
    // Try to split room name from description

    // Check for (#id) pattern which marks the room name boundary.
    // Evennia shows (#id) only to Builder+ accounts; regular players
    // just get "RoomName\nDescription\nExits: ...".
    const idMatch = raw.match(/^(.+?)\(#\d+\)(.*)$/s)
    if (idMatch) {
      roomName = idMatch[1].trim()
      const rest = idMatch[2]
      const exitsIdx = rest.search(/Exits?:/i)
      if (exitsIdx >= 0) {
        description = rest.slice(0, exitsIdx).trim()
        parseExitsAndEntities(rest.slice(exitsIdx), exits, characters, items)
      }
    } else {
      // No (#id) — split on newlines. Evennia 5.x sends the room name
      // as its own line, followed by the description on subsequent lines.
      const lines = raw.split(/\n/).map(l => l.trim()).filter(Boolean)
      if (lines.length > 1) {
        // The room name is typically the FIRST SHORT line (under ~60 chars).
        // If the first line is too long, it's probably the description
        // jammed onto the name line — try to split at the first sentence.
        const firstLine = lines[0]
        if (firstLine.length <= 60) {
          roomName = firstLine
          const body = lines.slice(1).join(' ')
          const exitsIdx = body.search(/Exits?:/i)
          if (exitsIdx >= 0) {
            description = body.slice(0, exitsIdx).trim()
            parseExitsAndEntities(body.slice(exitsIdx), exits, characters, items)
          } else {
            description = body.trim()
            parseExitsAndEntities(raw, exits, characters, items)
          }
        } else {
          // First line is long — "RoomNameDescription..." merged without
          // a separator. Evennia sends name and desc as separate text
          // messages but the webclient may concatenate them into one line.
          //
          // Detection strategies, in priority order:
          // 1. Lowercase→Uppercase transition with no space ("WorldsYou")
          //    — strongest signal that two strings were concatenated.
          // 2. Period/exclamation within the first 60 chars — sentence end.
          // 3. Fallback to first 50 chars.
          const camelJoin = firstLine.search(/[a-z][A-Z]/)
          if (camelJoin > 0 && camelJoin < 60) {
            roomName = firstLine.slice(0, camelJoin + 1).trim()
            description = firstLine.slice(camelJoin + 1).trim()
          } else {
            const sentenceEnd = firstLine.search(/[.!]/)
            if (sentenceEnd > 0 && sentenceEnd < 60) {
              roomName = firstLine.slice(0, sentenceEnd).trim()
              description = firstLine.slice(sentenceEnd + 1).trim()
            } else if (!roomName) {
              roomName = firstLine.slice(0, 50).trim()
              description = firstLine.slice(50).trim()
            }
          }
          // Add remaining lines to description
          if (lines.length > 1) {
            const restBody = lines.slice(1).join(' ')
            const exitsIdx = restBody.search(/Exits?:/i)
            if (exitsIdx >= 0) {
              description = (description + ' ' + restBody.slice(0, exitsIdx)).trim()
              parseExitsAndEntities(restBody.slice(exitsIdx), exits, characters, items)
            } else {
              description = (description + ' ' + restBody).trim()
              parseExitsAndEntities(raw, exits, characters, items)
            }
          }
        }
      } else {
        // Single block — try to extract room name as first sentence
        const exitsIdx = raw.search(/Exits?:/i)
        if (exitsIdx > 0) {
          const before = raw.slice(0, exitsIdx)
          const firstDot = before.indexOf('.')
          if (firstDot > 0 && firstDot < 80) {
            roomName = before.slice(0, firstDot).trim()
            description = before.slice(firstDot + 1).trim()
          } else {
            roomName = before.slice(0, 60).trim()
            description = before.slice(60).trim()
          }
          parseExitsAndEntities(raw.slice(exitsIdx), exits, characters, items)
        }
      }
    }

    // Clean up room name — remove (#id) suffix and trailing punctuation
    roomName = roomName.replace(/\(#\d+\)/, '').trim()

    if (roomName) {
      return { roomName, description, exits, characters, items }
    }
  }
  return null
}

// Naive singularize for item names — strips trailing 's' when the item
// has a count > 1, handling common English plural patterns.
function singularize(name) {
  if (name.endsWith('ies')) return name.slice(0, -3) + 'y'
  if (name.endsWith('ves')) return name.slice(0, -3) + 'f'
  if (name.endsWith('ses') || name.endsWith('xes') || name.endsWith('zes') || name.endsWith('ches') || name.endsWith('shes')) return name.slice(0, -2)
  if (name.endsWith('s') && !name.endsWith('ss')) return name.slice(0, -1)
  return name
}

// Build a command-safe item reference. When there are multiple copies
// of the same item in a room, Evennia disambiguates with "1-name",
// "2-name" etc. We always prefix with "1-" so Evennia grabs the first
// match without asking the player to narrow the target.
// MUST be lowercase — Evennia's search is case-insensitive but the
// N- prefix matching requires lowercase.
function cmdRef(name) {
  return `1-${name.toLowerCase()}`
}

// Number words → numeric values for quantity parsing
const NUMBER_WORDS = {
  two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8,
  nine: 9, ten: 10, eleven: 11, twelve: 12, thirteen: 13, fourteen: 14,
  fifteen: 15, sixteen: 16, seventeen: 17, eighteen: 18, nineteen: 19, twenty: 20,
}

// Split "a Foo, twelve Bar, and a Baz" into [{name: "Foo", count: 1}, {name: "Bar", count: 12}, ...]
// Then group duplicates by name, summing counts.
function splitEntities(str) {
  const raw = str
    .split(/,\s*(?:and\s+)?|\s+and\s+/)
    .map(s => s.trim())
    .filter(Boolean)

  const parsed = raw.map(s => {
    // Strip articles
    s = s.replace(/^(?:a|an|the|some)\s+/i, '')
    // Check for a leading number word or digit
    const numWordMatch = s.match(/^(\w+)\s+(.+)$/)
    if (numWordMatch) {
      const maybeNum = numWordMatch[1].toLowerCase()
      if (NUMBER_WORDS[maybeNum]) {
        return { name: numWordMatch[2], count: NUMBER_WORDS[maybeNum] }
      }
      const asInt = parseInt(maybeNum)
      if (!isNaN(asInt) && asInt > 0) {
        return { name: numWordMatch[2], count: asInt }
      }
    }
    return { name: s, count: 1 }
  })

  // Group by normalized name, summing counts
  const grouped = new Map()
  for (const { name, count } of parsed) {
    const key = name.toLowerCase()
    if (grouped.has(key)) {
      const existing = grouped.get(key)
      existing.count += count
    } else {
      grouped.set(key, { name, count })
    }
  }
  return Array.from(grouped.values())
}

function parseExitsAndEntities(text, exits, characters, items) {
  // Extract exits: "Exits: Room Name <DIR>, ..."
  const exitMatch = text.match(/Exits?:\s*(.+?)(?=Characters?:|You see:|$)/i)
  if (exitMatch) {
    const re = /([^,<]+?)\s*<([^>]+)>/g
    let m
    while ((m = re.exec(exitMatch[1])) !== null) {
      exits.push({ name: m[1].trim().replace(/^\s*and\s+/, ''), dir: m[2].trim() })
    }
  }

  const charMatch = text.match(/Characters?:\s*(.+?)(?=You see:|Exits?:|$)/i)
  if (charMatch) {
    splitEntities(charMatch[1]).forEach(c => characters.push(c))
  }

  const itemMatch = text.match(/You see:\s*(.+?)(?=Characters?:|Exits?:|$)/i)
  if (itemMatch) {
    // items are now {name, count} objects
    splitEntities(itemMatch[1]).forEach(it => items.push(it))
  }
}

export default function RoomView({ messages, onCommand, onEntityClick, onEntityContextMenu, onExitContextMenu }) {
  const room = useMemo(() => parseRoomData(messages), [messages])
  const biome = useMemo(
    () => room ? detectBiome(room.roomName, room.description) : null,
    [room]
  )

  if (!room) {
    return (
      <div className="room-view">
        <div className="room-view-empty">
          <span className="cinzel">Type <code>look</code> to view your surroundings</span>
        </div>
      </div>
    )
  }

  return (
    <div
      className="room-view"
      style={biome ? { '--biome-tint': biome.tint, '--biome-accent': biome.accent } : undefined}
    >
      {/* Atmospheric biome tint overlay */}
      <div className="room-biome-tint" />

      {/* Scene header: room name on left, large faded biome art on right */}
      <div className="room-header">
        <div className="room-header-text">
          <h2 className="room-name">{room.roomName}</h2>
        </div>
        {biome && (
          <img
            src={biome.icon}
            alt={biome.label}
            className="room-biome-backdrop"
            loading="lazy"
          />
        )}
      </div>

      {room.description && (
        <p className="room-desc">{room.description}</p>
      )}

      <div className="room-details">
        {/* Exits */}
        {room.exits.length > 0 && (
          <div className="room-section">
            <span className="room-section-label">Exits</span>
            <div className="room-exits">
              {room.exits.map((exit, i) => (
                <button
                  key={i}
                  className="room-exit-btn"
                  onClick={() => onCommand(exit.dir)}
                  onContextMenu={onExitContextMenu ? (e) => onExitContextMenu(e, exit.dir) : undefined}
                  title={`Go ${exit.dir}`}
                >
                  <span className="room-exit-name">{exit.name}</span>
                  <span className="room-exit-dir">{exit.dir}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Characters in room — each as an interactive card */}
        {room.characters.length > 0 && (
          <div className="room-section">
            <span className="room-section-label">Characters</span>
            <div className="room-entities">
              {room.characters.map((c, i) => (
                <button
                  key={i}
                  className="room-entity-btn character"
                  onClick={onEntityClick ? () => onEntityClick(c.name, 'character') : () => onCommand(`look ${c.name}`)}
                  onContextMenu={onEntityContextMenu ? (e) => onEntityContextMenu(e, c.name, 'character') : undefined}
                  title={`Look at ${c.name}`}
                >
                  <span className="entity-icon">⚔</span>
                  <span className="entity-name">{c.name}</span>
                  {c.count > 1 && <span className="entity-count">x{c.count}</span>}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Items in room — each clickable, with count badges */}
        {room.items.length > 0 && (
          <div className="room-section">
            <span className="room-section-label">You See</span>
            <div className="room-entities">
              {room.items.map((item, i) => {
                // Singularize when plural, and prefix with 1- to avoid
                // Evennia's "more than one match" disambiguation prompt
                const baseName = item.count > 1 ? singularize(item.name) : item.name
                const ref = item.count > 1 ? cmdRef(baseName) : baseName
                return (
                  <button
                    key={i}
                    className="room-entity-btn item"
                    onClick={onEntityClick ? () => onEntityClick(ref, 'item') : () => onCommand(`look ${ref}`)}
                    onContextMenu={onEntityContextMenu ? (e) => onEntityContextMenu(e, ref, 'item') : undefined}
                    title={`Look at ${baseName}`}
                  >
                    <span className="entity-icon">◆</span>
                    <span className="entity-name">{item.name}</span>
                    {item.count > 1 && <span className="entity-count">x{item.count}</span>}
                  </button>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
