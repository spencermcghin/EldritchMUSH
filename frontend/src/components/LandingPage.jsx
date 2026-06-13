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
    body: `Every soul in the Vale keeps an account of you. Lie to the
    innkeeper and the smith hears of it within the week, warped in the
    telling. A seer dreams of your deeds and recites them back as
    prophecy. You can confess your secrets to the priest, if it
    comforts you — though that vault has been robbed before.`,
  },
  {
    numeral: 'II',
    title: 'Combat is a held breath',
    art: '/landing/werewolf.jpg',
    alt: 'Ink illustration of a werewolf crouched on a ridge before a full moon, a severed manacled hand in the snow',
    caption: 'Fig. II — werewolf, by moonlight',
    body: `Turn-based, tactical, unsentimental. Blades sunder, armor
    fails by inches, wounds go to bleeding before they go to black.
    Somewhere out there a thing called the Withering Maw walks from
    room to room on its own appointed rounds, and it holds a grudge.`,
  },
  {
    numeral: 'III',
    title: 'Quests with teeth',
    art: '/landing/necromancer.jpg',
    alt: 'Ink illustration of a robed necromancer wreathed in pale smoke, dead hands rising from the earth around her',
    caption: 'Fig. III — a necromancer at her work',
    body: `Branching quests resolve in outcomes, not checkmarks. Rob
    the forager or take the vision; either way, letters will find you
    afterward. Factions keep score. So do certain ghosts, who can be
    spoken with, provided you keep your nerve through the séance.`,
  },
  {
    numeral: 'IV',
    title: 'Make, mend, trade',
    art: '/landing/clovis.jpg',
    alt: 'Ink illustration of a suit of armor and skull disassembled into its parts, swords fanned behind it',
    caption: 'Fig. IV — a soldier, itemized',
    body: `Forge, fletch, brew, and barter. Sixty-six alchemical
    recipes, eight noble houses' worth of arms and armor, and an
    economy in silver that does not forgive bad debts. What you carry
    is what you made, bought, or pried from something's hands.`,
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
    body: 'Make a character and pick your road into the Annwyn — by ship, with the Cirque caravan, in a noble retinue, among the Lodge scholars, or chained in the Last Walk.',
  },
  {
    n: '4',
    title: 'Play',
    body: 'Prose in, world out. The story runs whether you are watching or not.',
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
              Beyond the village of Gateway lies the walled Vale of
              Mystvale, and beyond the Vale lies the Annwyn, which does
              not give things back. A living text world of turn-based
              combat, consequence, and company you will come to regret.
              Cross, and the Annwyn takes you.
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
          EldritchMUSH is a multiplayer story told in prose — a MUSH, in
          the old tongue. You write what your character does; the world
          writes back. Its people are played by a machine intelligence
          with a long memory: they gossip about you, dream about you,
          carry grudges across weeks. There is no level grind and no
          minimap. There is a village at the edge of the world, and
          everything past it is earned.
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
        <p>Roughly once a night, a moonstorm breaks over the Vale.</p>
        <p>The Mists open passages that were not there yesterday.</p>
        <p>Neither asks permission.</p>
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
          <h2 className="landing-factions-title">Eight houses keep the Vale</h2>
          <p className="landing-factions-names">
            Aragon · Bannon · Blayne · Corveaux · Hale · Innis · Richter · Rourke
          </p>
          <p className="landing-factions-body">
            Choose carefully whose colors you stand under. They are
            keeping score too.
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
          <h3 className="landing-pricing-title">The toll</h3>
          <p className="landing-pricing-body">
            The first thirty days are free — the whole game, no card up
            front. After that it is <strong>$5 a month</strong>, paid
            through PayPal. Cancel whenever you like; the Mists hold no
            contracts.
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
