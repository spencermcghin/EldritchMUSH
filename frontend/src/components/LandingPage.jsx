import './LandingPage.css'

/*
 * LandingPage — the marketing one-pager shown at "/" to visitors who
 * are not signed in. The game client lives a click deeper: the PLAY
 * button calls onPlay(), which pushes "/play" and reveals the existing
 * LoginScreen. Already-authenticated sessions never linger here — the
 * auto-connect effect in App.jsx takes over as soon as the session
 * check returns.
 *
 * Aesthetic: Mistbound Gothic, editorial cut — oversized Cinzel type,
 * asymmetric "bestiary plate" art cards on deep black, CSS-only grain
 * and mist. No JS animation; prefers-reduced-motion respected in CSS.
 *
 * Copy: marketed like a studio homepage — evocative, confident, sparse.
 * State the novel hooks at altitude; don't dissect the systems.
 */

// A sparse bestiary strip — the art carries it; the captions are flavor,
// not feature copy.
const BESTIARY = [
  {
    art: '/landing/fae.jpg',
    alt: 'Ink illustration of a masked fae lord in dark robes, carrying carved masks and a crooked staff',
    caption: 'Fig. I, a fae of the Annwyn',
  },
  {
    art: '/landing/werewolf.jpg',
    alt: 'Ink illustration of a werewolf crouched on a ridge before a full moon, a severed manacled hand in the snow',
    caption: 'Fig. II, a werewolf by moonlight',
  },
  {
    art: '/landing/necromancer.jpg',
    alt: 'Ink illustration of a robed necromancer wreathed in pale smoke, dead hands rising from the earth around her',
    caption: 'Fig. III, a necromancer at her work',
  },
]

// The eight noble houses, each with its own hanging heraldic banner
// (transparent kite-shield art from the per-house art folders).
const HOUSES = [
  'Aragon',
  'Bannon',
  'Blayne',
  'Corveaux',
  'Hale',
  'Innis',
  'Richter',
  'Rourke',
]

export default function LandingPage({ onPlay }) {
  return (
    <div className="landing">
      <div className="landing-grain" aria-hidden="true" />
      <div className="landing-mist" aria-hidden="true" />

      {/* ── Hero ── */}
      <header className="landing-hero">
        <nav className="landing-nav">
          <img src="/art/eldritch-logo.png" alt="EldritchMUSH" className="landing-nav-logo" />
          <button className="landing-nav-play" type="button" onClick={onPlay}>
            Sign in
          </button>
        </nav>

        <div className="landing-hero-grid">
          <div className="landing-hero-copy">
            <p className="landing-kicker">A dark-fantasy survival MUSH, played in the browser</p>
            <h1 className="landing-title">
              <span className="landing-title-line">The Mists</span>
              <span className="landing-title-line landing-title-indent">are</span>
              <span className="landing-title-line">moving</span>
            </h1>
            <p className="landing-lede">
              Past the village of Gateway stands the walled Vale of
              Mystvale, and past the Vale waits the Annwyn. People go in.
              Fewer come back. It's a text world you play by writing, and
              it remembers everything you do.
            </p>
            <div className="landing-cta-row">
              <button className="landing-cta" type="button" onClick={onPlay}>
                Play now
              </button>
              <p className="landing-cta-note">
                Free for 30 days. $5 a month after. Cancel whenever.
              </p>
            </div>
          </div>

          <figure className="landing-hero-plate">
            <img
              src="/landing/nethermancer.jpg"
              alt="Ink illustration of a nethermancer in tattered black robes raising a skull-tipped staff, red sigils circling its feet"
              width="605"
              height="1100"
              fetchpriority="high"
            />
            <figcaption className="landing-plate-caption">
              Fig. 0, a nethermancer recovered from the Annwyn
            </figcaption>
          </figure>
        </div>
      </header>

      {/* ── What it is — one beat, stated at altitude ── */}
      <section className="landing-what" aria-label="What EldritchMUSH is">
        <p className="landing-what-text">
          A multiplayer story you read and write in plain prose. You say
          what your character does, and the world answers. It holds a
          grudge. No XP bars, no grind. Just a village at the edge of
          everything, and a long way to go before any of it is yours.
        </p>
        <p className="landing-pillars">
          Turn-based combat, crafting and alchemy, a living economy, and
          quests that branch on the choices you make.
        </p>
      </section>

      {/* ── Bestiary strip — the art, sparse ── */}
      <section className="landing-bestiary" aria-label="From the bestiary">
        {BESTIARY.map((b) => (
          <figure className="landing-bestiary-plate" key={b.caption}>
            <img src={b.art} alt={b.alt} loading="lazy" width="700" height="940" />
            <figcaption className="landing-plate-caption">{b.caption}</figcaption>
          </figure>
        ))}
      </section>

      {/* ── Interstitial — the world moves on its own ── */}
      <section className="landing-interstitial" aria-label="The living world">
        <figure className="landing-interstitial-figure">
          <img
            src="/landing/mists.jpg"
            alt="Ink illustration of two figures handing off a relic at the edge of a dark, knotted Mist that watches with many eyes"
            loading="lazy"
            width="1400"
            height="906"
          />
        </figure>
        <p className="landing-interstitial-lead">
          The world keeps moving when you log off. Roads open that were
          not there the day before, and if you walk one, you might not
          come out where you went in.
        </p>
      </section>

      {/* ── World map ── */}
      <section className="landing-map" aria-label="The world">
        <div className="landing-map-copy">
          <p className="landing-map-kicker">Three places, getting worse</p>
          <h2 className="landing-map-title">Gateway, Mystvale, the Annwyn</h2>
          <p className="landing-map-body">
            A village where you wash up, a walled country held by quarreling
            houses, and whatever waits beyond the Mists.
          </p>
        </div>
        <figure className="landing-map-figure">
          <img
            src="/landing/annwyn-map.jpg"
            alt="Aged illustrated map of the Vale showing Duskwatch Harbour, the town of Ludavar, forested hinterlands, a knight on horseback, and a noble's coach"
            loading="lazy"
            width="1088"
            height="1100"
          />
          <figcaption className="landing-plate-caption">
            survey of the vale, provenance unknown
          </figcaption>
        </figure>
      </section>

      {/* ── Factions ── */}
      <section className="landing-factions" aria-label="The noble houses">
        <div className="landing-factions-copy">
          <h2 className="landing-factions-title">Pick whose colors you wear</h2>
          <p className="landing-factions-body">
            Rival houses run the Vale, and each one has a long memory and a
            longer list of people who crossed it. Choose with care.
          </p>
        </div>
        <ul className="landing-factions-banners">
          {HOUSES.map((house) => (
            <li className="landing-factions-banner" key={house}>
              <img
                src={`/landing/banner-${house.toLowerCase()}.png`}
                alt={`House ${house} banner`}
                loading="lazy"
                width="362"
                height="600"
              />
            </li>
          ))}
        </ul>
      </section>

      {/* ── Pricing + CTA ── */}
      <section className="landing-start" aria-label="Start playing">
        <div className="landing-pricing">
          <img
            src="/landing/wax-seal.png"
            alt=""
            aria-hidden="true"
            className="landing-pricing-seal"
            width="240"
            height="284"
            loading="lazy"
          />
          <h3 className="landing-pricing-title">The toll</h3>
          <p className="landing-pricing-body">
            The first thirty days cost nothing. You get the full game, no
            card up front and no download. After that it's{' '}
            <strong>$5 a month</strong> through PayPal, and you can cancel
            any time.
          </p>
          <button className="landing-cta" type="button" onClick={onPlay}>
            Begin the trial
          </button>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="landing-footer">
        <img src="/art/eldritch-logo.png" alt="" aria-hidden="true" className="landing-footer-logo" />
        <p className="landing-footer-line">
          EldritchMUSH is a production of Eldritch Workshop, L.L.C.
        </p>
        <p className="landing-footer-line">
          <a href="mailto:admin@eldritchmush.com">admin@eldritchmush.com</a>
          <span aria-hidden="true"> · </span>
          <button className="landing-footer-play" type="button" onClick={onPlay}>Play</button>
          <span aria-hidden="true"> · </span>
          Built on the <a href="https://www.evennia.com" rel="noopener noreferrer" target="_blank">Evennia</a> engine
        </p>
        <p className="landing-footer-fine">
          © {new Date().getFullYear()} Eldritch Workshop, L.L.C. The
          Mists keep what they take.
        </p>
      </footer>
    </div>
  )
}
