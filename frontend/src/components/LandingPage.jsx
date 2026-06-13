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
 */

const FEATURES = [
  {
    numeral: 'I',
    title: 'The world remembers you',
    art: '/landing/fae.jpg',
    alt: 'Ink illustration of a masked fae lord in dark robes, carrying carved masks and a crooked staff',
    caption: 'Fig. I — a fae of the Annwyn',
    body: `The people here keep track of you. Lie to the innkeeper and
    the smith hears about it by week's end, the story a little worse
    each time it's told. A seer dreams about something you did and
    repeats it back to you as prophecy. Confess to the priest if it
    helps — but his confessional has been broken into before.`,
  },
  {
    numeral: 'II',
    title: 'Combat with real depth',
    art: '/landing/werewolf.jpg',
    alt: 'Ink illustration of a werewolf crouched on a ridge before a full moon, a severed manacled hand in the snow',
    caption: 'Fig. II — werewolf, by moonlight',
    body: `Turn-based fights you can actually think your way through.
    Position matters. You target specific limbs, armor wears down and
    stops protecting, and a clean hit can disarm, sunder, or stagger.
    Take enough and you start bleeding out. A creature called the
    Withering Maw wanders the map on its own, so the room you walk
    into may already have teeth in it.`,
  },
  {
    numeral: 'III',
    title: 'Quests with teeth',
    art: '/landing/necromancer.jpg',
    alt: 'Ink illustration of a robed necromancer wreathed in pale smoke, dead hands rising from the earth around her',
    caption: 'Fig. III — a necromancer at her work',
    body: `Quests branch, and how they end is up to you. Rob the
    forager, or take the vision he offers — either choice writes
    itself into what happens next, and a letter usually arrives to
    remind you. The houses track where you stand with them. So do a
    few of the dead, if you can hold a séance without losing your
    nerve.`,
  },
  {
    numeral: 'IV',
    title: 'Make, mend, trade',
    art: '/landing/clovis.jpg',
    alt: 'Ink illustration of a suit of armor and skull disassembled into its parts, swords fanned behind it',
    caption: 'Fig. IV — a soldier, itemized',
    body: `Forge weapons, fletch arrows, brew tinctures, haggle in the
    market. There are sixty-six alchemy recipes, arms and armor for all
    eight houses, and a silver economy that remembers what you owe.
    Everything you carry, you made, bought, or took off something that
    no longer needs it.`,
  },
]

const STEPS = [
  {
    n: '1',
    title: 'Arrive',
    body: 'Open eldritchmush.com in any browser. No download, no client, no telnet incantations.',
  },
  {
    n: '2',
    title: 'Sign in',
    body: 'One click with Google, or a plain username if you prefer the old ways.',
  },
  {
    n: '3',
    title: 'Cross over',
    body: 'Make a character and choose how you arrive: by ship, riding with the Cirque caravan, in a noble retinue, among the Lodge scholars, or chained in the Last Walk.',
  },
  {
    n: '4',
    title: 'Play',
    body: 'Type what you do, read what happens. The world keeps moving when you log off.',
  },
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
              Fewer come back. It's a text world you play by writing:
              turn-based combat, choices that stick to you, and neighbors
              you'll wish you had never met.
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
              Fig. 0 — nethermancer, recovered from the Annwyn
            </figcaption>
          </figure>
        </div>
      </header>

      {/* ── What it is ── */}
      <section className="landing-what" aria-label="What EldritchMUSH is">
        <p className="landing-what-text">
          EldritchMUSH is a multiplayer story you read and write in plain
          prose. You say what your character does; the world answers. The
          people in it gossip about you, hold grudges for weeks, and dream
          your worst deeds back at you as prophecy. No XP bars, no minimap.
          Just a village at the edge of everything, and a long way to go
          before any of it belongs to you.
        </p>
      </section>

      {/* ── Features ── */}
      <section className="landing-features" aria-label="Features">
        {FEATURES.map((f, i) => (
          <article className={`landing-feature${i % 2 ? ' landing-feature-flip' : ''}`} key={f.numeral}>
            <div className="landing-feature-copy">
              <span className="landing-feature-numeral" aria-hidden="true">{f.numeral}</span>
              <h2 className="landing-feature-title">{f.title}</h2>
              <p className="landing-feature-body">{f.body}</p>
            </div>
            <figure className="landing-feature-plate">
              <img src={f.art} alt={f.alt} loading="lazy" width="700" height="940" />
              <figcaption className="landing-plate-caption">{f.caption}</figcaption>
            </figure>
          </article>
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
          About once a night a moonstorm rolls over the Vale, and the
          Mists open roads that were not there the day before. Walk one
          and you might not come out where you went in.
        </p>
      </section>

      {/* ── World map ── */}
      <section className="landing-map" aria-label="The world">
        <div className="landing-map-copy">
          <p className="landing-map-kicker">Three places, getting worse</p>
          <h2 className="landing-map-title">Gateway, Mystvale, the Annwyn</h2>
          <p className="landing-map-body">
            Gateway is the village where you wash up — taverns, a market,
            people who will sell you out. The Vale of Mystvale is the
            walled country behind it, held by eight quarreling houses. The
            Annwyn is what's on the far side of the Mists, and the maps of
            it tend to be wrong on purpose.
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
            survey of the vale — provenance unknown
          </figcaption>
        </figure>
      </section>

      {/* ── Factions ── */}
      <section className="landing-factions" aria-label="The eight noble houses">
        <figure className="landing-factions-figure">
          <img
            src="/landing/faction-banners.jpg"
            alt="Eight noble house banners side by side, each bearing a shield and sigil"
            loading="lazy"
            width="1200"
            height="458"
          />
        </figure>
        <div className="landing-factions-copy">
          <h2 className="landing-factions-title">Eight houses run the Vale</h2>
          <p className="landing-factions-names">
            Aragon · Bannon · Blayne · Corveaux · Hale · Innis · Richter · Rourke
          </p>
          <p className="landing-factions-body">
            Pick whose colors you wear with some care. Each house has a
            long memory and a longer list of people who crossed it.
          </p>
        </div>
      </section>

      {/* ── How to start + pricing ── */}
      <section className="landing-start" aria-label="How to start">
        <h2 className="landing-start-title">Crossing over</h2>
        <ol className="landing-steps">
          {STEPS.map((s) => (
            <li className="landing-step" key={s.n}>
              <span className="landing-step-n" aria-hidden="true">{s.n}</span>
              <h3 className="landing-step-title">{s.title}</h3>
              <p className="landing-step-body">{s.body}</p>
            </li>
          ))}
        </ol>

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
            The first thirty days cost nothing — the full game, no card
            up front. After that it's <strong>$5 a month</strong> through
            PayPal, and you can cancel any time. Nobody here holds you to
            a contract.
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
