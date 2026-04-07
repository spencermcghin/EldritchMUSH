import { useEffect, useRef } from 'react'
import './GameOutput.css'

function formatTime(ts) {
  const d = new Date(ts)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function MessageLine({ msg, index }) {
  const html = msg.content || ''
  return (
    <div
      className={`msg msg-${msg.type}`}
      data-time={formatTime(msg.timestamp)}
      style={{ animationDelay: `${Math.min(index * 0.01, 0.1)}s` }}
      dangerouslySetInnerHTML={{ __html: html || '&nbsp;' }}
    />
  )
}

export default function GameOutput({ messages, inCombat }) {
  const containerRef = useRef(null)
  const bottomRef = useRef(null)
  const userScrolledRef = useRef(false)

  // Auto-scroll to bottom unless user has scrolled up
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
          <MessageLine key={msg.id} msg={msg} index={i} />
        ))}
        <div ref={bottomRef} />
      </div>
      {/* CRT scanline overlay */}
      <div className="crt-overlay" />
    </div>
  )
}
