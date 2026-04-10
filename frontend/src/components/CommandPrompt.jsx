import { useState, useEffect, useRef, useCallback } from 'react'
import './CommandPrompt.css'

/**
 * A friendly modal that asks the player for input before sending a MUD command.
 * Used for commands like say/emote/whisper/look that need a target or message.
 *
 * Props:
 * - prompt: { title, label, placeholder, icon, buildCommand: (input) => string } or null
 * - onSubmit: (command: string) => void
 * - onCancel: () => void
 */
export default function CommandPrompt({ prompt, onSubmit, onCancel }) {
  const [value, setValue] = useState('')
  const inputRef = useRef(null)

  // Reset and focus when a new prompt opens
  useEffect(() => {
    if (prompt) {
      setValue('')
      // Focus shortly after mount so the modal animation finishes first
      const t = setTimeout(() => inputRef.current?.focus(), 50)
      return () => clearTimeout(t)
    }
  }, [prompt])

  // Esc to cancel
  useEffect(() => {
    if (!prompt) return
    const onKey = (e) => {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [prompt, onCancel])

  const handleSubmit = useCallback((e) => {
    if (e) e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed) {
      onCancel()
      return
    }
    onSubmit(prompt.buildCommand(trimmed))
  }, [value, prompt, onSubmit, onCancel])

  if (!prompt) return null

  return (
    <div className="command-prompt-overlay" onClick={onCancel}>
      <div className="command-prompt-modal" onClick={(e) => e.stopPropagation()}>
        <div className="command-prompt-header">
          {prompt.icon && <span className="command-prompt-icon">{prompt.icon}</span>}
          <span className="command-prompt-title">{prompt.title}</span>
          <button className="command-prompt-close" onClick={onCancel} title="Cancel (Esc)">✕</button>
        </div>

        <form className="command-prompt-body" onSubmit={handleSubmit}>
          <label className="command-prompt-label">{prompt.label}</label>
          <input
            ref={inputRef}
            type="text"
            className="command-prompt-input"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={prompt.placeholder || ''}
            autoComplete="off"
            spellCheck="false"
          />

          <div className="command-prompt-actions">
            <button type="button" className="command-prompt-btn secondary" onClick={onCancel}>
              Cancel
            </button>
            <button type="submit" className="command-prompt-btn primary" disabled={!value.trim()}>
              {prompt.submitLabel || 'Send'}
            </button>
          </div>

          <div className="command-prompt-hint">
            Press <kbd>Enter</kbd> to send · <kbd>Esc</kbd> to cancel
          </div>
        </form>
      </div>
    </div>
  )
}
