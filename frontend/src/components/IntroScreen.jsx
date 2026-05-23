import { useEffect, useState, useRef } from 'react'
import './IntroScreen.css'

/**
 * IntroScreen — full-screen lore crawl shown ONCE per character
 * after they finish chargen and before they're dropped into the
 * world for the first time.
 *
 * Visual: dark vignetted background, parchment-coloured Cormorant
 * serif text, slow auto-scroll. "Continue" button at the bottom
 * once the scroll completes (or anytime via "Skip" in the corner).
 *
 * Per-character gate: stores `eldritchmush.intro_seen.<charname>`
 * in localStorage so a given character only sees it on their first
 * arrival, never again. Wiped if you delete the character or clear
 * site data.
 *
 * Props:
 *   characterName  string  — used for the localStorage key and the title
 *   onDismiss      ()=>void — fired when Skip or Continue is clicked
 */
export default function IntroScreen({ characterName, onDismiss }) {
  const scrollRef = useRef(null)
  const [atBottom, setAtBottom] = useState(false)

  // Auto-scroll the crawl at a slow steady rate so the player can
  // read along without scrolling manually. They can scroll themselves
  // to override; once they're at the bottom we surface Continue.
  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    let raf = 0
    let last = performance.now()
    // ~22 pixels per second — comfortable reading pace.
    const pxPerSec = 22
    const tick = (now) => {
      const dt = (now - last) / 1000
      last = now
      el.scrollTop += pxPerSec * dt
      const near = el.scrollTop + el.clientHeight >= el.scrollHeight - 4
      if (near) {
        setAtBottom(true)
        return
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [])

  const handleScroll = () => {
    const el = scrollRef.current
    if (!el) return
    const near = el.scrollTop + el.clientHeight >= el.scrollHeight - 4
    setAtBottom(near)
  }

  const handleDismiss = () => {
    try {
      if (characterName) {
        localStorage.setItem(`eldritchmush.intro_seen.${characterName}`, '1')
      }
    } catch (e) {
      // localStorage may be disabled — ignore.
    }
    onDismiss?.()
  }

  return (
    <div className="intro-screen">
      <div className="intro-vignette" />
      <button className="intro-skip" onClick={handleDismiss}>SKIP</button>

      <div className="intro-content">
        <div className="intro-header">
          <div className="intro-eyebrow">— A PROLOGUE —</div>
          <h1 className="intro-title">The Day of Mist</h1>
        </div>

        <div className="intro-crawl" ref={scrollRef} onScroll={handleScroll}>
          <p>
            Almost six moon cycles ago, on the fifteenth day of the second moon
            cycle, the Mist came. It rolled out of nowhere at the Witching Hour and
            swallowed the Kingdom of Arnesse in cold grey silence. It persisted a
            full day and a full night before retreating from whence it came.
          </p>

          <p>
            When the Mist withdrew, livestock had perished, crops had failed in the
            southern fields, and people — some of them — were simply <em>gone</em>.
            Swallowed entire by the fog, never seen again.
          </p>

          <p>
            And then came word of the <strong>Annwyn</strong>. Sailors out of
            Breakwater Bay told of a long line of fog that had swallowed their
            ship whole and spat it out again days later. They spoke of a land
            beyond — ancient ruins, terrible creatures, fantastic treasures. A
            land lost to time. The Otherworld.
          </p>

          <p>
            Scouts found that a stretch of the western coast was indeed ringed
            by a wall of deep rolling fog. Expeditions went in. Almost none came
            out. Curiosity gave way to fear, and the Mists became a place of
            execution as much as exploration — the &ldquo;Last Walk&rdquo;,
            given to prisoners and the unwanted.
          </p>

          <p>
            Then the <strong>Mistwalkers</strong> appeared. Strange figures who
            claimed they could navigate the fog and take others through. After
            enough demonstrations, the Crown and the Compact came to terms with
            them: pay their fee, and you would cross. But heed the saying that
            now runs in every tavern from Highcourt to the Sovereignlands —{' '}
            <em>once the Annwyn has you, only she can let you go</em>.
          </p>

          <div className="intro-divider">✦ ─── ✦ ─── ✦</div>

          <h2 className="intro-section">Gateway</h2>

          <p>
            You are in <strong>Gateway</strong>: a ramshackle palisade-town on
            the Arnesse side of the Mistwall, raised in haste to feed the
            constant traffic of would-be settlers, pilgrims, scholars, exiles,
            and condemned. It is a stinking, hopeful, dangerous place. The
            Mistguard — knights of Houses Richter and Bannon — keep what civil
            order can be kept. Most arrivals end up sheltering in the tent city
            beyond the wooden wall.
          </p>

          <p>
            You will not be staying long.
          </p>

          <div className="intro-divider">✦ ─── ✦ ─── ✦</div>

          <h2 className="intro-section">What you must do</h2>

          <p>
            Find the <strong>Herald at the Gates</strong> in Gateway Square. She
            briefs every traveller on the crossing-paths into the Annwyn. There
            are five: by <em>ship</em>, with the <em>Cirque caravan</em>, in a
            <em> noble retinue</em>, with the <em>Lodge of the Metaphysical
            Mind</em>, or chained in a <em>chain gang</em>. The path you choose
            shapes what you become on the other side, and what waits for you
            there.
          </p>

          <p>
            Pick a path. Walk north to the Mistwalker&rsquo;s Tent, then west to
            the Mistwall, then{' '}
            <code>through the mists</code>. You will emerge changed.
          </p>

          <p className="intro-closing">
            The dark is wide, {characterName ? characterName : 'traveller'}.
            Walk carefully.
          </p>
        </div>

        <div className="intro-actions">
          <button
            className={`intro-continue ${atBottom ? 'ready' : 'pending'}`}
            onClick={handleDismiss}
          >
            {atBottom ? 'Begin' : 'Skip to the Gate'}
          </button>
        </div>
      </div>
    </div>
  )
}
