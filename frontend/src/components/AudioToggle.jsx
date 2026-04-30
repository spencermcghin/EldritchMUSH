import { useState, useEffect, useRef } from 'react'
import './AudioToggle.css'

/**
 * AudioToggle — header control for background music.
 *
 * Tiny note icon that opens a popover on click. Popover holds:
 *   - Mute / Unmute toggle (the autoplay-gesture trigger)
 *   - Volume slider
 *   - Skip / Prev buttons (in-game only — disabled on title screen
 *     where the title track loops)
 *   - "Now playing" line (track + album)
 *
 * `audioRef.current` exposes the imperative API from AudioController
 * so this component doesn't need to own playback state itself.
 */
export default function AudioToggle({ audioRef, atTitleScreen }) {
  const [open, setOpen] = useState(false)
  const popoverRef = useRef(null)
  // Force a re-render on tick so the "now playing" line picks up
  // ref.current changes (refs don't trigger React updates by default).
  const [, setTick] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000)
    return () => clearInterval(id)
  }, [])

  // Click-outside to close.
  useEffect(() => {
    if (!open) return
    const onClick = (e) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [open])

  const ctrl = audioRef.current
  const enabled = !!ctrl?.enabled
  const volume = ctrl?.volume ?? 35
  const track = ctrl?.currentTrack

  const handleToggle = () => ctrl?.setEnabled(!enabled)
  const handleVolume = (e) => ctrl?.setVolume(parseInt(e.target.value, 10))
  const handleSkip = () => ctrl?.skip?.()
  const handlePrev = () => ctrl?.prev?.()

  // Icon glyph: speaker-on when enabled, speaker-off when muted.
  const icon = enabled ? '♪' : '♪'

  return (
    <div className="audio-toggle-wrap" ref={popoverRef}>
      <button
        className={`audio-toggle-btn ${enabled ? 'on' : 'off'}`}
        onClick={() => setOpen(o => !o)}
        title={enabled ? 'Music on — click to adjust' : 'Music muted — click to enable'}
        aria-label="Music controls"
      >
        <span className="audio-toggle-icon">{icon}</span>
        {!enabled && <span className="audio-toggle-strike" />}
      </button>

      {open && (
        <div className="audio-popover">
          <div className="audio-popover-header">
            <span className="cinzel">MUSIC</span>
          </div>

          <button
            className={`audio-popover-toggle ${enabled ? 'on' : 'off'}`}
            onClick={handleToggle}
          >
            {enabled ? '◼ Mute' : '▶ Play'}
          </button>

          <div className="audio-popover-volume">
            <label className="audio-popover-label">Volume</label>
            <input
              type="range"
              min="0"
              max="100"
              value={volume}
              onChange={handleVolume}
              className="audio-popover-slider"
            />
            <span className="audio-popover-value">{volume}</span>
          </div>

          {!atTitleScreen && (
            <div className="audio-popover-controls">
              <button
                className="audio-popover-skip"
                onClick={handlePrev}
                title="Previous track"
              >
                ◄◄
              </button>
              <button
                className="audio-popover-skip"
                onClick={handleSkip}
                title="Next track"
              >
                ►►
              </button>
            </div>
          )}

          {track && (
            <div className="audio-popover-now">
              <div className="audio-popover-now-label">Now playing</div>
              <div className="audio-popover-track">{track.title}</div>
              <div className="audio-popover-album">
                {track.album?.artist} — <em>{track.album?.title}</em>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
