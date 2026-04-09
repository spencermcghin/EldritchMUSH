import { useMemo } from 'react'
import './RoomView.css'

// Parse room data from game text messages
function parseRoomData(messages) {
  // Look backwards for the most recent room description
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i]
    if (msg.type !== 'game' && msg.type !== 'system') continue
    const raw = (msg.content || '').replace(/<[^>]*>/g, '')

    // Room descriptions typically start with a colored room name on its own line
    // followed by description text, then "Exits:" and "You see:" or "Characters:"
    const hasExits = /Exits?:/i.test(raw)
    if (!hasExits) continue

    // Parse room name (first non-empty line, often colored)
    const lines = raw.split('\n').map(l => l.trim()).filter(Boolean)
    let roomName = ''
    let description = ''
    let exits = []
    let characters = []
    let items = []

    // First line is usually the room name
    if (lines.length > 0) {
      roomName = lines[0]
    }

    // Join remaining lines for parsing
    const body = lines.slice(1).join(' ')

    // Extract description (everything before "Exits:")
    const exitsIdx = body.search(/Exits?:/i)
    if (exitsIdx > 0) {
      description = body.slice(0, exitsIdx).trim()
    }

    // Extract exits
    const exitMatch = body.match(/Exits?:\s*(.+?)(?=Characters?:|You see:|$)/i)
    if (exitMatch) {
      const re = /([^,<]+?)\s*<([^>]+)>/g
      let m
      while ((m = re.exec(exitMatch[1])) !== null) {
        exits.push({ name: m[1].trim().replace(/^\s*and\s+/, ''), dir: m[2].trim() })
      }
    }

    // Extract characters
    const charMatch = body.match(/Characters?:\s*(.+?)(?=You see:|Exits?:|$)/i)
    if (charMatch) {
      characters = charMatch[1].split(/,\s*(?:and\s+)?/).map(s => s.trim()).filter(Boolean)
    }

    // Extract items ("You see:")
    const itemMatch = body.match(/You see:\s*(.+?)(?=Characters?:|Exits?:|$)/i)
    if (itemMatch) {
      items = itemMatch[1].split(/,\s*(?:and\s+)?/).map(s => s.trim()).filter(Boolean)
    }

    if (roomName) {
      return { roomName, description, exits, characters, items }
    }
  }
  return null
}

export default function RoomView({ messages, onCommand }) {
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
                  title={`Go ${exit.dir}`}
                >
                  <span className="room-exit-name">{exit.name}</span>
                  <span className="room-exit-dir">{exit.dir}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Characters in room */}
        {room.characters.length > 0 && (
          <div className="room-section">
            <span className="room-section-label">Characters</span>
            <div className="room-entities">
              {room.characters.map((c, i) => (
                <span key={i} className="room-entity character">{c}</span>
              ))}
            </div>
          </div>
        )}

        {/* Items in room */}
        {room.items.length > 0 && (
          <div className="room-section">
            <span className="room-section-label">You See</span>
            <div className="room-entities">
              {room.items.map((item, i) => (
                <span key={i} className="room-entity item">{item}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
