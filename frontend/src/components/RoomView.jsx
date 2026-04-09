import { useMemo } from 'react'
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

    // Check for (#id) pattern which marks the room name boundary
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
      // Split on first newline or first "Exits:"
      const lines = raw.split(/\n/)
      if (lines.length > 1) {
        roomName = lines[0].trim()
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
        // Single block — try to extract room name as first sentence
        const exitsIdx = raw.search(/Exits?:/i)
        if (exitsIdx > 0) {
          const before = raw.slice(0, exitsIdx)
          // First "sentence" or chunk before the long description
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

    // Clean up room name — remove (#id) suffix
    roomName = roomName.replace(/\(#\d+\)/, '').trim()

    if (roomName) {
      return { roomName, description, exits, characters, items }
    }
  }
  return null
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
    charMatch[1].split(/,\s*(?:and\s+)?/).map(s => s.trim()).filter(Boolean).forEach(c => characters.push(c))
  }

  const itemMatch = text.match(/You see:\s*(.+?)(?=Characters?:|Exits?:|$)/i)
  if (itemMatch) {
    itemMatch[1].split(/,\s*(?:and\s+)?/).map(s => s.trim()).filter(Boolean).forEach(it => items.push(it))
  }
}

export default function RoomView({ messages, onCommand, onEntityClick, onEntityContextMenu, onExitContextMenu }) {
  const room = useMemo(() => parseRoomData(messages), [messages])

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
    <div className="room-view">
      <div className="room-header">
        <h2 className="room-name">{room.roomName}</h2>
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
