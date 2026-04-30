import { useEffect, useRef, useState, useCallback, useImperativeHandle, forwardRef } from 'react'
import { TITLE_TRACK, GAME_PLAYLIST } from '../data/musicTracks'

const STORAGE_KEY = 'eldritch.audio'

function loadPrefs() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function savePrefs(prefs) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs))
  } catch { /* quota / private mode — ignore */ }
}

/**
 * AudioController — single global <audio> element + playback state.
 *
 * Exposes its API via the forwarded ref so AudioToggle (rendered in the
 * header) can drive enable/volume/skip without prop-drilling.
 *
 * Track selection logic:
 *   - When `atTitleScreen` is true, loop the dedicated title theme.
 *   - When false, walk through GAME_PLAYLIST in order, looping back at
 *     the end. Track ended → advance.
 *
 * Persistence:
 *   - enabled (bool) and volume (0..100) live in localStorage.
 *   - Default: disabled (browser autoplay rules require a user gesture
 *     to start audio anyway, so we wait for the toggle).
 */
const AudioController = forwardRef(function AudioController(
  { atTitleScreen },
  ref,
) {
  const audioRef = useRef(null)
  const prefs = loadPrefs() || {}
  const [enabled, setEnabled] = useState(!!prefs.enabled)
  const [volume, setVolume] = useState(
    typeof prefs.volume === 'number' ? prefs.volume : 35,
  )
  const [trackIndex, setTrackIndex] = useState(0)
  const [currentTrack, setCurrentTrack] = useState(null)

  // Resolve which track should be playing right now.
  const resolveTrack = useCallback(() => {
    if (atTitleScreen) return TITLE_TRACK
    return GAME_PLAYLIST[trackIndex % GAME_PLAYLIST.length] || TITLE_TRACK
  }, [atTitleScreen, trackIndex])

  // Persist prefs whenever they change.
  useEffect(() => {
    savePrefs({ enabled, volume })
  }, [enabled, volume])

  // Keep the audio element's volume in sync with state.
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = Math.max(0, Math.min(1, volume / 100))
    }
  }, [volume])

  // Swap track src when the resolution changes (title↔game or skip).
  // Always loop the title track; the game playlist advances on `ended`.
  useEffect(() => {
    const track = resolveTrack()
    setCurrentTrack(track)
    const el = audioRef.current
    if (!el || !track) return
    if (el.src !== window.location.origin + track.src) {
      el.src = track.src
    }
    el.loop = !!atTitleScreen
    if (enabled) {
      el.play().catch(() => {
        // Autoplay blocked — user hasn't interacted yet. We'll retry
        // on the next toggle/state change. Don't surface an error.
      })
    } else {
      el.pause()
    }
  }, [resolveTrack, atTitleScreen, enabled])

  // Auto-advance through GAME_PLAYLIST.
  const handleEnded = useCallback(() => {
    if (atTitleScreen) return // title track loops, no advance
    setTrackIndex(i => (i + 1) % GAME_PLAYLIST.length)
  }, [atTitleScreen])

  // Imperative API for the header toggle.
  useImperativeHandle(ref, () => ({
    enabled,
    volume,
    currentTrack,
    setEnabled: (val) => {
      setEnabled(val)
      const el = audioRef.current
      if (!el) return
      if (val) {
        // First user-gesture-triggered play — this satisfies autoplay rules.
        el.play().catch(() => {})
      } else {
        el.pause()
      }
    },
    setVolume,
    skip: () => {
      if (atTitleScreen) return
      setTrackIndex(i => (i + 1) % GAME_PLAYLIST.length)
    },
    prev: () => {
      if (atTitleScreen) return
      setTrackIndex(i => (i - 1 + GAME_PLAYLIST.length) % GAME_PLAYLIST.length)
    },
  }), [enabled, volume, currentTrack, atTitleScreen])

  // Audio element is invisible — it's controlled entirely through
  // state and the imperative API above.
  return (
    <audio
      ref={audioRef}
      onEnded={handleEnded}
      preload="none"
      style={{ display: 'none' }}
    />
  )
})

export default AudioController
