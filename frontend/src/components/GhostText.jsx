import { memo } from 'react'
import './GhostText.css'

/**
 * GhostText — otherworldly text treatment for séance-mode dialogue.
 *
 * - Words drift in with a staggered animation-delay (word-level, not
 *   per-character, to cap DOM/animation work). Only the first
 *   GHOST_STAGGER_CHAR_CAP characters get individual word spans; the
 *   remainder fades in as a single block.
 * - One mid-sentence word per line is "rewritten": rendered as a
 *   struck-through <del> followed by the same word in caps/italics,
 *   as if the ghost corrected itself. The word is chosen by hashing
 *   the line (deterministic — stable across re-renders, no
 *   Math.random at render time).
 * - memo()'d so parent re-renders (e.g. typing in the dialogue input)
 *   don't remount the spans and re-trigger the CSS animations.
 */

const GHOST_STAGGER_CHAR_CAP = 200
const WORD_STAGGER_MS = 55

// djb2 — small, stable string hash.
function hashLine(s) {
  let h = 5381
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) + h + s.charCodeAt(i)) | 0
  }
  return Math.abs(h)
}

// Pick the index (among word tokens) of the word to strike through.
// Candidates: mid-sentence words (not first, not last) that are
// plain-alphabetic and at least 4 chars — avoids striking "a", "the—",
// names with punctuation, etc. Returns -1 when nothing qualifies.
function pickStrikeIndex(words, hash) {
  const candidates = []
  for (let i = 1; i < words.length - 1; i++) {
    if (/^[a-zA-Z]{4,}$/.test(words[i])) candidates.push(i)
  }
  if (candidates.length === 0) return -1
  return candidates[hash % candidates.length]
}

const GhostText = memo(function GhostText({ text }) {
  const line = text || ''
  const hash = hashLine(line)
  // Split keeping whitespace so spacing survives reassembly.
  const tokens = line.split(/(\s+)/)
  const words = tokens.filter((t) => t && !/^\s+$/.test(t))
  const strikeIdx = pickStrikeIndex(words, hash)

  const out = []
  const blockRest = []
  let wordIdx = -1 // index among word tokens
  let staggerIdx = 0 // index among staggered (animated) word spans
  let charCount = 0
  let inBlock = false

  tokens.forEach((tok, i) => {
    if (!tok) return
    if (/^\s+$/.test(tok)) {
      ;(inBlock ? blockRest : out).push(tok)
      return
    }
    wordIdx += 1
    charCount += tok.length

    const content =
      wordIdx === strikeIdx ? (
        <>
          <del className="ghost-strike">{tok}</del>{' '}
          <em className="ghost-correction">{tok.toUpperCase()}</em>
        </>
      ) : (
        tok
      )

    if (inBlock) {
      blockRest.push(<span key={i}>{content}</span>)
    } else {
      out.push(
        <span
          key={i}
          className="ghost-word"
          style={{ animationDelay: `${staggerIdx * WORD_STAGGER_MS}ms` }}
        >
          {content}
        </span>
      )
      staggerIdx += 1
      if (charCount >= GHOST_STAGGER_CHAR_CAP) inBlock = true
    }
  })

  return (
    <span className="ghost-text">
      {out}
      {blockRest.length > 0 && (
        <span
          className="ghost-block"
          style={{ animationDelay: `${staggerIdx * WORD_STAGGER_MS}ms` }}
        >
          {blockRest}
        </span>
      )}
    </span>
  )
})

export default GhostText
