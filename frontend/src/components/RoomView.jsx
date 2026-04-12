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
          // First line is long — might be "RoomNameDescription..." merged.
          // Try splitting at the first lowercase letter after some uppercase
          // chars, or at the first period/comma within 60 chars.
          const sentenceEnd = firstLine.search(/[.!]/)
          if (sentenceEnd > 0 && sentenceEnd < 60) {
            roomName = firstLine.slice(0, sentenceEnd).trim()
            description = firstLine.slice(sentenceEnd + 1).trim()
          } else {
            // Look for a transition from titlecase to lowercase sentence
            const caseBreak = firstLine.search(/[A-Z][a-z]+\s+[A-Z][a-z]/)
            if (caseBreak > 0 && caseBreak < 60) {
              // Find the space after the titlecase word
              const spaceAfter = firstLine.indexOf(' ', caseBreak + 2)
              if (spaceAfter > 0) {
                roomName = firstLine.slice(0, spaceAfter).trim()
                description = firstLine.slice(spaceAfter + 1).trim()
              }
            }
            if (!roomName) {
              // Fallback: just take the first 50 chars
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

// Split "a Foo, a Bar, and a Baz" or "a Foo and a Bar" into ["Foo", "Bar", "Baz"]
function splitEntities(str) {
  return str
    .split(/,\s*(?:and\s+)?|\s+and\s+/)
    .map(s => s.trim())
    .filter(Boolean)
    .map(s => s.replace(/^(?:a|an|the|some)\s+/i, '')) // strip articles
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
                  onClick={onEntityClick ? () => onEntityClick(c, 'character') : () => onCommand(`look ${c}`)}
                  onContextMenu={onEntityContextMenu ? (e) => onEntityContextMenu(e, c, 'character') : undefined}
                  title={`Look at ${c}`}
                >
                  <span className="entity-icon">⚔</span>
                  <span className="entity-name">{c}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Items in room — each clickable */}
        {room.items.length > 0 && (
          <div className="room-section">
            <span className="room-section-label">You See</span>
            <div className="room-entities">
              {room.items.map((item, i) => (
                <button
                  key={i}
                  className="room-entity-btn item"
                  onClick={onEntityClick ? () => onEntityClick(item, 'item') : () => onCommand(`look ${item}`)}
                  onContextMenu={onEntityContextMenu ? (e) => onEntityContextMenu(e, item, 'item') : undefined}
                  title={`Look at ${item}`}
                >
                  <span className="entity-icon">◆</span>
                  <span className="entity-name">{item}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
