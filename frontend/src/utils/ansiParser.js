import React from 'react'

// Evennia color code → CSS color
const FG_COLORS = {
  r: '#e03030',
  R: '#ff6666',
  g: '#33aa44',
  G: '#66ff88',
  y: '#ccaa00',
  Y: '#ffee44',
  b: '#3355cc',
  B: '#6688ff',
  m: '#cc33cc',
  M: '#ff77ff',
  c: '#22aacc',
  C: '#66ddff',
  w: '#aaaaaa',
  W: '#f0ece0',
  x: '#444444',
  X: '#777777',
}

const BG_COLORS = {
  r: '#3a0000',
  R: '#5a1010',
  g: '#003a00',
  G: '#105a10',
  y: '#3a3000',
  Y: '#5a5010',
  b: '#00003a',
  B: '#10105a',
  m: '#3a003a',
  M: '#5a105a',
  c: '#003a3a',
  C: '#105a5a',
  w: '#2a2a2a',
  W: '#4a4a4a',
  x: '#000000',
  X: '#1a1a1a',
}

/**
 * Convert a 0-5 cube index to an RGB channel value for xterm-256 6x6x6 cube.
 */
function cubeToRgb(n) {
  if (n === 0) return 0
  return 95 + (n - 1) * 40
}

/**
 * Parse Evennia |000–|555 xterm256 color codes.
 * Format: 3 digits, each 0-5 for R, G, B.
 */
function xterm256ToRgb(code) {
  if (!/^[0-5]{3}$/.test(code)) return null
  const r = cubeToRgb(parseInt(code[0]))
  const g = cubeToRgb(parseInt(code[1]))
  const b = cubeToRgb(parseInt(code[2]))
  return `rgb(${r},${g},${b})`
}

/**
 * Parse Evennia ANSI/color markup into React elements.
 * Returns an array of React nodes (spans, brs).
 */
export function parseAnsi(text, keyPrefix = '') {
  if (!text || typeof text !== 'string') return []

  const nodes = []
  let currentStyle = {}  // { color?, backgroundColor? }
  let buffer = ''
  let i = 0
  let segIndex = 0

  function flushBuffer() {
    if (buffer.length === 0) return
    const style = { ...currentStyle }
    const hasStyle = Object.keys(style).length > 0
    nodes.push(
      hasStyle
        ? React.createElement('span', { key: `${keyPrefix}-${segIndex++}`, style }, buffer)
        : React.createElement(React.Fragment, { key: `${keyPrefix}-${segIndex++}` }, buffer)
    )
    buffer = ''
  }

  while (i < text.length) {
    if (text[i] === '|') {
      const next = text[i + 1]
      if (next === undefined) {
        buffer += '|'
        i++
        continue
      }

      // || → literal |
      if (next === '|') {
        buffer += '|'
        i += 2
        continue
      }

      // |/ → line break
      if (next === '/') {
        flushBuffer()
        nodes.push(React.createElement('br', { key: `${keyPrefix}-br-${segIndex++}` }))
        i += 2
        continue
      }

      // |n → reset
      if (next === 'n') {
        flushBuffer()
        currentStyle = {}
        i += 2
        continue
      }

      // |[X → background color
      if (next === '[') {
        const bgChar = text[i + 2]
        if (bgChar && BG_COLORS[bgChar]) {
          flushBuffer()
          currentStyle = { ...currentStyle, backgroundColor: BG_COLORS[bgChar] }
          i += 3
          continue
        }
        buffer += '|'
        i++
        continue
      }

      // |000–|555 → xterm256 fg color (3 digits)
      if (/[0-5]/.test(next)) {
        const code = text.slice(i + 1, i + 4)
        if (/^[0-5]{3}$/.test(code)) {
          const rgb = xterm256ToRgb(code)
          if (rgb) {
            flushBuffer()
            currentStyle = { ...currentStyle, color: rgb }
            i += 4
            continue
          }
        }
        buffer += '|'
        i++
        continue
      }

      // |r|R|g|G etc. → foreground color
      if (FG_COLORS[next]) {
        flushBuffer()
        currentStyle = { ...currentStyle, color: FG_COLORS[next] }
        i += 2
        continue
      }

      // Unrecognized escape — output literal |
      buffer += '|'
      i++
    } else {
      buffer += text[i]
      i++
    }
  }

  flushBuffer()
  return nodes
}
