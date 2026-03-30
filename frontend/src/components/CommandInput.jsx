import { useState, useRef, useImperativeHandle, forwardRef, useCallback } from 'react'
import './CommandInput.css'

const MAX_HISTORY = 100

function getCompletions(partial, availableCommands) {
  if (!partial || partial.length < 1) return []
  const lower = partial.toLowerCase()
  return availableCommands
    .filter((cmd) => cmd.key.startsWith(lower) || (cmd.label || '').toLowerCase().startsWith(lower))
    .map((cmd) => cmd.key)
    .slice(0, 8)
}

const CommandInput = forwardRef(function CommandInput(
  { onSend, availableCommands = [], disabled = false },
  ref
) {
  const [value, setValue] = useState('')
  const [historyIndex, setHistoryIndex] = useState(-1)
  const [completions, setCompletions] = useState([])
  const [completionIdx, setCompletionIdx] = useState(-1)
  const historyRef = useRef([])
  const inputRef = useRef(null)

  // Expose setValue and focus to parent
  useImperativeHandle(ref, () => ({
    setValue: (text) => {
      setValue(text)
      setCompletions([])
      setCompletionIdx(-1)
    },
    focus: () => {
      inputRef.current?.focus()
    },
  }))

  const handleSend = useCallback(
    (text) => {
      const trimmed = text.trim()
      if (!trimmed) return
      onSend(trimmed)
      // Add to history (skip duplicates at head)
      const hist = historyRef.current
      if (hist[0] !== trimmed) {
        historyRef.current = [trimmed, ...hist].slice(0, MAX_HISTORY)
      }
      setValue('')
      setHistoryIndex(-1)
      setCompletions([])
      setCompletionIdx(-1)
    },
    [onSend]
  )

  const handleKeyDown = (e) => {
    const hist = historyRef.current

    if (e.key === 'Enter') {
      e.preventDefault()
      if (completionIdx >= 0 && completions[completionIdx]) {
        // Accept completion
        const completed = completions[completionIdx] + ' '
        setValue(completed)
        setCompletions([])
        setCompletionIdx(-1)
      } else {
        handleSend(value)
      }
      return
    }

    if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (completions.length > 0) {
        setCompletionIdx((i) => (i <= 0 ? completions.length - 1 : i - 1))
        return
      }
      const nextIdx = Math.min(historyIndex + 1, hist.length - 1)
      setHistoryIndex(nextIdx)
      if (hist[nextIdx] !== undefined) {
        setValue(hist[nextIdx])
        setCompletions([])
      }
      return
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (completions.length > 0) {
        setCompletionIdx((i) => (i >= completions.length - 1 ? 0 : i + 1))
        return
      }
      if (historyIndex <= 0) {
        setHistoryIndex(-1)
        setValue('')
        return
      }
      const nextIdx = historyIndex - 1
      setHistoryIndex(nextIdx)
      setValue(hist[nextIdx] || '')
      return
    }

    if (e.key === 'Tab') {
      e.preventDefault()
      if (completions.length === 0) {
        const newCompletions = getCompletions(value.trim(), availableCommands)
        if (newCompletions.length === 1) {
          setValue(newCompletions[0] + ' ')
        } else if (newCompletions.length > 1) {
          setCompletions(newCompletions)
          setCompletionIdx(0)
        }
      } else {
        setCompletionIdx((i) => (i >= completions.length - 1 ? 0 : i + 1))
      }
      return
    }

    if (e.key === 'Escape') {
      setCompletions([])
      setCompletionIdx(-1)
      return
    }
  }

  const handleChange = (e) => {
    const v = e.target.value
    setValue(v)
    setHistoryIndex(-1)
    // Clear completions on edit
    if (completions.length > 0) {
      setCompletions([])
      setCompletionIdx(-1)
    }
  }

  const handleCompletionClick = (cmd) => {
    setValue(cmd + ' ')
    setCompletions([])
    setCompletionIdx(-1)
    inputRef.current?.focus()
  }

  return (
    <div className="cmd-input-wrap">
      {/* Tab completion dropdown */}
      {completions.length > 0 && (
        <div className="cmd-completions">
          {completions.map((cmd, i) => (
            <div
              key={cmd}
              className={`cmd-completion-item ${i === completionIdx ? 'active' : ''}`}
              onMouseDown={(e) => {
                e.preventDefault()
                handleCompletionClick(cmd)
              }}
            >
              {cmd}
            </div>
          ))}
        </div>
      )}

      <div className={`cmd-input-row ${disabled ? 'disabled' : ''}`}>
        <span className="cmd-prompt">›</span>
        <input
          ref={inputRef}
          className="cmd-input"
          type="text"
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? 'Connecting...' : 'Type a command...'}
          disabled={disabled}
          autoComplete="off"
          autoCorrect="off"
          spellCheck="false"
          autoCapitalize="off"
        />
        <button
          className="cmd-send-btn"
          onClick={() => handleSend(value)}
          disabled={disabled || !value.trim()}
          tabIndex={-1}
          title="Send (Enter)"
        >
          ⏎
        </button>
      </div>
    </div>
  )
})

export default CommandInput
