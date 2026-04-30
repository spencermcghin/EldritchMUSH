import { useEffect, useRef } from 'react'
import DOMPurify from 'dompurify'
import './GameOutput.css'

function formatTime(ts) {
  const d = new Date(ts)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

// Parse "Exits: Tavern Ruins <N>, Market <NW>, ..." into clickable buttons
function parseExits(html) {
  // Strip HTML tags for matching
  const stripped = html.replace(/<[^>]*>/g, '')
  const exitMatch = stripped.match(/Exits?:\s*(.+)/)
  if (!exitMatch) return null

  const exitStr = exitMatch[1]
  // Match patterns like "Room Name <DIR>" or just "<DIR>"
  const exits = []
  const re = /([^,<]+?)\s*<([^>]+)>/g
  let m
  while ((m = re.exec(exitStr)) !== null) {
    exits.push({ name: m[1].trim().replace(/^\s*and\s+/, ''), dir: m[2].trim() })
  }
  return exits.length > 0 ? exits : null
}

function ExitButtons({ exits, onCommand }) {
  return (
    <div className="exit-buttons">
      <span className="exit-label">Exits:</span>
      {exits.map((exit, i) => (
        <button
          key={i}
          className="exit-btn"
          onClick={() => onCommand(exit.dir)}
          title={`Go ${exit.dir} to ${exit.name}`}
        >
          {exit.name} <span className="exit-dir">{exit.dir}</span>
        </button>
      ))}
    </div>
  )
}

// Apply lightweight markdown-ish prettification:
//   *action* → italic dim-gold "(action)" feel — used heavily by AI NPC
//              replies to indicate gestures: *Pauses, hands clasped*.
//   "speech" → keep as-is (Evennia color codes already highlight the
//              speaker name; the quotes themselves are visual cues).
//   `> command` echo lines → muted prefix.
// Run BEFORE DOMPurify so the inserted spans aren't stripped.
function prettify(html) {
  if (!html) return html
  return html.replace(
    /\*([^*\n]{1,200}?)\*/g,
    '<em class="msg-action">$1</em>'
  )
}

function MessageLine({ msg, index, onCommand }) {
  const raw = msg.content || ''
  const html = prettify(raw)
  const exits = parseExits(html)

  // If this message contains exits, render them as buttons
  if (exits) {
    // Render the non-exit part as HTML, then the exit buttons
    const beforeExits = html.replace(/Exits?:.*$/s, '')
    return (
      <div className="msg-with-exits" style={{ animationDelay: `${Math.min(index * 0.01, 0.1)}s` }}>
        {beforeExits && (
          <div
            className={`msg msg-${msg.type}`}
            data-time={formatTime(msg.timestamp)}
            dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(beforeExits || '&nbsp;', { ADD_TAGS: ['em'], ADD_ATTR: ['class'] }) }}
          />
        )}
        <ExitButtons exits={exits} onCommand={onCommand} />
      </div>
    )
  }

  return (
    <div
      className={`msg msg-${msg.type}`}
      data-time={formatTime(msg.timestamp)}
      style={{ animationDelay: `${Math.min(index * 0.01, 0.1)}s` }}
      dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html || '&nbsp;', { ADD_TAGS: ['em'], ADD_ATTR: ['class'] }) }}
    />
  )
}

export default function GameOutput({ messages, inCombat, onCommand }) {
  const containerRef = useRef(null)
  const bottomRef = useRef(null)
  const userScrolledRef = useRef(false)

  useEffect(() => {
    if (!userScrolledRef.current && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [messages])

  const handleScroll = () => {
    const el = containerRef.current
    if (!el) return
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 30
    userScrolledRef.current = !atBottom
  }

  return (
    <div className={`game-output-wrap ${inCombat ? 'in-combat' : ''}`}>
      <div
        className="game-output"
        ref={containerRef}
        onScroll={handleScroll}
      >
        {messages.length === 0 && (
          <div className="game-output-empty">
            <span className="cinzel">Awaiting the server&apos;s voice...</span>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageLine key={msg.id} msg={msg} index={i} onCommand={onCommand} />
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="crt-overlay" />
    </div>
  )
}
