/**
 * playtest-ui.mjs — Playwright UI smoke-test for EldritchMUSH.
 *
 * Targets deployed environments only (no local). Auth is via Google OAuth,
 * saved per-target to auth-<target>.json after a one-time interactive setup.
 *
 * Usage:
 *   node playtest-ui.mjs setup-auth --target=uat       # one-time, visible browser
 *   node playtest-ui.mjs <scenario>  --target=uat      # headless
 *   node playtest-ui.mjs <scenario>  --target=prod     # read-only scenarios only
 *
 * Env overrides:
 *   PLAYTEST_TARGET=uat|prod            (default: uat)
 *   PLAYTEST_CHARACTER=<name>           (default: Aethel; auto-created if missing)
 *   PLAYTEST_AUTH_STATE=<path>          (override saved auth location — CI uses this)
 *   PLAYTEST_VERBOSE=1                  (dump console + WS frames)
 */

import { chromium } from 'playwright'
import path from 'node:path'
import fs from 'node:fs/promises'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SHOT_DIR = path.join(__dirname, 'screenshots')
const RUNS_DIR = path.join(__dirname, 'runs')

const TARGETS = {
  uat:  { url: 'https://uat.eldritchmush.com', authFile: 'auth-uat.json' },
  prod: { url: 'https://eldritchmush.com',     authFile: 'auth-prod.json' },
}

function parseArgs(argv) {
  const positional = []
  const flags = {}
  for (const a of argv.slice(2)) {
    const m = a.match(/^--([^=]+)=(.*)$/)
    if (m) flags[m[1]] = m[2]
    else positional.push(a)
  }
  return { positional, flags }
}

const { positional, flags } = parseArgs(process.argv)
const SCENARIO = positional[0] || 'crafting-modal'
const TARGET_NAME = (flags.target || process.env.PLAYTEST_TARGET || 'uat').toLowerCase()
const TARGET = TARGETS[TARGET_NAME]
if (!TARGET) {
  console.error(`Unknown target '${TARGET_NAME}'. Known: ${Object.keys(TARGETS).join(', ')}`)
  process.exit(2)
}

const AUTH_STATE = process.env.PLAYTEST_AUTH_STATE
  || path.join(__dirname, TARGET.authFile)
const CHAR_NAME = process.env.PLAYTEST_CHARACTER || 'UAT Bot'

// Scenarios flagged as read-only are the only ones allowed against prod.
const READ_ONLY = new Set(['login', 'crafting-modal', 'crafting-ironhaven', 'crafting-docks'])

// --- helpers ---------------------------------------------------------------

async function snap(page, name) {
  await fs.mkdir(SHOT_DIR, { recursive: true })
  const p = path.join(SHOT_DIR, `${TARGET_NAME}-${SCENARIO}-${name}.png`)
  await page.screenshot({ path: p, fullPage: false })
  console.log(`  📸 ${path.relative(process.cwd(), p)}`)
  return p
}

async function typeCommand(page, cmd) {
  const input = page.locator('input, textarea').first()
  await input.fill(cmd)
  await input.press('Enter')
  await page.waitForTimeout(500)
}

async function authStateExists() {
  try { await fs.access(AUTH_STATE); return true } catch { return false }
}

async function waitForGameOrCharsel(page, timeout = 20000) {
  return Promise.race([
    page.locator('.cmd-sidebar').first().waitFor({ state: 'visible', timeout })
      .then(() => 'game').catch(() => null),
    page.locator('.charsel-screen').first().waitFor({ state: 'visible', timeout })
      .then(() => 'charsel').catch(() => null),
  ])
}

async function ensureCharacter(page, name) {
  const charSelect = page.locator('.charsel-screen')
  if (await charSelect.count() === 0) return  // already puppeted

  // Wait for WS connection; card click sends `ic` via WS.
  await page.locator('.status-label.connected').first()
    .waitFor({ state: 'visible', timeout: 15000 }).catch(() => {})
  await page.waitForTimeout(400)

  // Look for existing character card with matching name.
  const existing = page
    .locator('.charsel-screen .charsel-card', { hasText: name })
    .filter({ hasNot: page.locator('.charsel-card-create') })
    .first()
  if (await existing.count()) {
    console.log(`  → puppeting existing character '${name}'`)
    await existing.click()
    await page.waitForSelector('.cmd-sidebar', { timeout: 15000 })
    await page.waitForTimeout(1000)
    return
  }

  // Not found — create.
  console.log(`  → no character '${name}' yet; creating`)
  await snap(page, '02a-charsel-empty')
  // For accounts with zero characters, the charcreate modal can auto-open
  // on the charsel screen. Check for an already-open modal before clicking
  // the create card (the backdrop blocks the click otherwise).
  const modalInput = page.locator('.charsel-modal-input').first()
  const modalAlreadyOpen = await modalInput.isVisible().catch(() => false)
  if (!modalAlreadyOpen) {
    await page.locator('.charsel-card-create').click()
  }
  await modalInput.waitFor({ state: 'visible', timeout: 10000 })
  await modalInput.fill(name)
  await snap(page, '02b-charcreate-modal')
  await page.locator('.charsel-modal-submit').click()

  // After charcreate, two possible UIs: (a) CharacterSelect re-renders
  // with the new card (user must click to puppet), or (b) server
  // auto-puppets straight into the chargen room (sidebar appears, no
  // card click needed). Wait for whichever lands first.
  const winner = await Promise.race([
    page.locator('.cmd-sidebar').first()
      .waitFor({ state: 'visible', timeout: 20000 })
      .then(() => 'game').catch(() => null),
    page.locator('.charsel-screen .charsel-card:not(.charsel-card-create)', { hasText: name }).first()
      .waitFor({ state: 'visible', timeout: 20000 })
      .then(() => 'card').catch(() => null),
  ])

  if (winner === 'game') {
    await page.waitForTimeout(1000)
    return
  }
  if (winner !== 'card') {
    throw new Error(`After charcreate, neither sidebar nor character card appeared within 20s`)
  }
  const newCard = page
    .locator('.charsel-screen .charsel-card:not(.charsel-card-create)', { hasText: name })
    .first()
  await page.waitForTimeout(600)
  await newCard.click()
  await page.waitForSelector('.cmd-sidebar', { timeout: 15000 })
  await page.waitForTimeout(1000)
}

async function login(page) {
  console.log(`→ ${TARGET.url}  [target=${TARGET_NAME}]`)
  await page.goto(TARGET.url, { waitUntil: 'domcontentloaded' })

  const winner = await waitForGameOrCharsel(page, 25000)
  if (!winner) {
    throw new Error(
      `Neither game UI nor CharacterSelect appeared within 25s. ` +
      `Auth may have expired — re-run: node playtest-ui.mjs setup-auth --target=${TARGET_NAME}`
    )
  }
  await page.waitForTimeout(600)
  await snap(page, '01-post-load')
}

// --- scenarios -------------------------------------------------------------

const SCENARIOS = {
  login: async (page) => {
    // login() + ensureCharacter() already ran; no extra steps.
  },

  'crafting-modal': async (page) => {
    await typeCommand(page, '@tel #2054')  // The Crafter's Quarter
    await page.waitForTimeout(1500)
    await snap(page, '03-crafter-quarter')
    await typeCommand(page, '__crafting_ui__')
    await page.waitForSelector('.alchemy-modal', { timeout: 8000 })
    await snap(page, '04-modal-open')

    const tabs = page.locator('.crafting-tab')
    const n = await tabs.count()
    console.log(`  found ${n} crafting tab(s)`)
    for (let i = 0; i < n; i++) {
      const t = tabs.nth(i)
      const label = (await t.textContent() || '').trim().split('\n')[0].trim()
      await t.click()
      await page.waitForTimeout(250)
      await snap(page, `05-tab-${i}-${label.toLowerCase().replace(/[^a-z]+/g, '')}`)

      const firstRecipe = page.locator('.alchemy-recipe-item').first()
      if (await firstRecipe.count()) {
        await firstRecipe.click()
        await page.waitForTimeout(250)
        await snap(page, `06-tab-${i}-recipe-detail`)
      }
    }
  },

  'crafting-ironhaven': async (page) => {
    await typeCommand(page, '@tel #2078')
    await page.waitForTimeout(1500)
    await snap(page, '03-ironhaven-forge')
    await typeCommand(page, '__crafting_ui__')
    await page.waitForSelector('.alchemy-modal', { timeout: 8000 })
    await snap(page, '04-modal-at-forge')
  },

  'crafting-docks': async (page) => {
    await typeCommand(page, '@tel #2058')
    await page.waitForTimeout(1500)
    await snap(page, '03-back-alley')
    await typeCommand(page, '__crafting_ui__')
    await page.waitForSelector('.alchemy-modal', { timeout: 8000 })
    await snap(page, '04-modal-at-alley')
  },

  // Rescue the Crafters chain (Event 1): 3-part quest chain with prereqs.
  // Quest 1 (rescue_blacksmith) uses the real accept flow at Ser Ewan Bannon's
  // barracks — a safe room. Quests 2/3 have givers (Torben, Marta) inside
  // hostile Crow camps; rather than clearing those camps we bypass the
  // giver-in-room check via @py and exercise the same objective-tick +
  // reward code paths that combat would hit.
  'quest-crows': async (page) => {
    await resetQuestState(page)
    for (const spec of CROWS_QUESTS) await runQuest(page, spec)
    await finalReport(page)
  },

  // One-shot migration: rename the local-dev tavern from
  // "The Raven's Rest Tavern" / "Raven & Candle" to "Songbird's Rest"
  // on the target DB, and rewrite tavern-name phrases in every room/NPC
  // description. Idempotent. Runs `world/rename_tavern.py` via @py exec.
  'migrate-rename-tavern': async (page) => {
    // Base64-encoded rename migration so the payload is deploy-independent
    // (we don't need the branch merged to UAT to run it). Source lives in
    // eldritchmush/world/rename_tavern.py; regenerate the b64 with the
    // helper in that file when the migration changes.
    const MIGRATION_B64 =
      'aW1wb3J0IGV2ZW5uaWEKUEFJUlMgPSBbKCJUaGUgUmF2ZW4ncyBSZXN0IGlzIiwgIlNvbmdiaXJ' +
      'kJ3MgUmVzdCBpcyIpLAogICAgICAgICAoIlRoZSBSYXZlbidzIFJlc3QgVGF2ZXJuIiwgIlNvbm' +
      'diaXJkJ3MgUmVzdCIpLAogICAgICAgICAoIlJhdmVuJ3MgUmVzdCBUYXZlcm4iLCAiU29uZ2Jpc' +
      'mQncyBSZXN0IiksCiAgICAgICAgICgiUmF2ZW4gJiBDYW5kbGUiLCAiU29uZ2JpcmQncyBSZXN0' +
      'IildCmRlZiBzdWIocyk6CiAgICBpZiBub3QgczogcmV0dXJuIHMKICAgIGZvciBvLCBuIGluIFB' +
      'BSVJTOgogICAgICAgIHMgPSBzLnJlcGxhY2UobywgbikKICAgIHJldHVybiBzCnJlbmFtZWQgPS' +
      'AwCnRvdWNoZWQgPSAwCmZvciByIGluIGV2ZW5uaWEuc2VhcmNoX29iamVjdCgiVGhlIFJhdmVuJ' +
      '3MgUmVzdCBUYXZlcm4iKToKICAgIHIua2V5ID0gIlNvbmdiaXJkJ3MgUmVzdCIKICAgIHIuZGIu' +
      'ZGVzYyA9IHN1YihyLmRiLmRlc2MpCiAgICByZW5hbWVkICs9IDEKZm9yIG8gaW4gZXZlbm5pYS5' +
      'zZWFyY2hfb2JqZWN0KCIiKToKICAgIGQgPSBvLmRiLmRlc2MKICAgIGlmIGQgYW5kIHN1YihkKS' +
      'AhPSBkOgogICAgICAgIG8uZGIuZGVzYyA9IHN1YihkKQogICAgICAgIHRvdWNoZWQgKz0gMQptZ' +
      'S5tc2coZiJbbWlncmF0ZV0gcmVuYW1lZCB7cmVuYW1lZH0gdGF2ZXJuIHJvb20ocyk7IHBhdGNo' +
      'ZWQge3RvdWNoZWR9IGRlc2MocykiKQo='
    await typeCommand(page,
      `@py import base64 as _b; exec(_b.b64decode("${MIGRATION_B64}").decode())`)
    await page.waitForTimeout(2000)
    await snap(page, '01-migration-done')
    await typeCommand(page,
      `@py import evennia; rs = evennia.search_object("Songbird's Rest"); ` +
      `me.msg(f"[migrate] rooms named Songbird's Rest: {[(r.id, r.key) for r in rs]}")`)
    await page.waitForTimeout(700)
    await snap(page, '02-verify')
  },

  // All 12 quests end-to-end, in prereq-respecting order. Safe givers
  // (Elara, Grimwald, Mira, Hamond, Ser Ewan) use the real `quest accept`
  // command; camp-based givers (Torben, Marta) are bypassed via @py.
  'quest-all': async (page) => {
    await resetQuestState(page)
    for (const spec of ALL_QUESTS) await runQuest(page, spec)
    await finalReport(page)
  },
}

// --- quest scenario helpers ------------------------------------------------

async function resetQuestState(page) {
  // Wipe quest progress + capture a baseline for the final report.
  await typeCommand(page,
    `@py me.db.quests = {}; me.db._qtest_start_silver = me.db.silver or 0; ` +
    `me.db._qtest_start_inv = sorted(o.key for o in me.contents); ` +
    `me.db._qtest_start_reagents = dict(me.db.reagents or {}); ` +
    `me.msg(f"[qtest] reset. silver={me.db.silver or 0}")`)
  await page.waitForTimeout(400)
  await snap(page, '00-reset')
}

async function finalReport(page) {
  // Single @py that summarizes what happened so the last screenshot
  // tells the whole story: statuses, silver delta, new inventory items,
  // reagent deltas.
  await typeCommand(page, 'quest')
  await page.waitForTimeout(500)
  await snap(page, '98-journal-final')

  await typeCommand(page,
    `@py statuses = {k: v["status"] for k, v in (me.db.quests or {}).items()}; ` +
    `start_s = me.db._qtest_start_silver or 0; ` +
    `start_inv = set(me.db._qtest_start_inv or []); ` +
    `start_r = dict(me.db._qtest_start_reagents or {}); ` +
    `new_inv = sorted(k for k in (o.key for o in me.contents) if k not in start_inv); ` +
    `cur_r = dict(me.db.reagents or {}); ` +
    `delta_r = {k: cur_r.get(k, 0) - start_r.get(k, 0) for k in set(list(cur_r) + list(start_r)) if cur_r.get(k, 0) != start_r.get(k, 0)}; ` +
    `me.msg(f"[qtest] statuses: {statuses}"); ` +
    `me.msg(f"[qtest] silver: {start_s} -> {me.db.silver or 0} (Δ{(me.db.silver or 0) - start_s})"); ` +
    `me.msg(f"[qtest] new inventory: {new_inv}"); ` +
    `me.msg(f"[qtest] reagent deltas: {delta_r}")`)
  await page.waitForTimeout(700)
  await snap(page, '99-final-report')
}

// Run a single quest lifecycle: teleport → accept (or inject) → detail →
// tick objectives → screenshot. `spec.room` is the room KEY to @tel to
// (NOT the NPC key — @tel on a non-room object puts you INSIDE that
// object, which breaks the giver-in-room check in quest accept).
// If spec.room is null, the active state is injected via @py to bypass
// the giver-in-room check (use for quests whose giver lives inside a
// hostile zone or when the giver's room is hard to target by name).
async function runQuest(page, spec) {
  const pre = spec.label  // e.g. "q01-road-clear"
  console.log(`  ▶ ${pre}  [${spec.key}]`)

  if (spec.room) {
    await typeCommand(page, `@tel ${spec.room}`)
    await page.waitForTimeout(1200)
    await snap(page, `${pre}-room`)
    await typeCommand(page, `quest accept ${spec.title}`)
  } else {
    // No safe room for the giver — inject the active state directly.
    await typeCommand(page,
      `@py from world.quest_data import QUESTS; ` +
      `from commands.quests import _fresh_objectives, _ensure_quest_db; ` +
      `_ensure_quest_db(me); ` +
      `me.db.quests["${spec.key}"] = {"status": "active", "objectives": _fresh_objectives(QUESTS["${spec.key}"])}; ` +
      `me.msg("[qtest] ${spec.key} injected as active")`)
  }
  await page.waitForTimeout(500)
  await snap(page, `${pre}-accepted`)

  await typeCommand(page, `quest ${spec.title}`)
  await page.waitForTimeout(400)
  await snap(page, `${pre}-detail`)

  await typeCommand(page, `@py ${spec.tick}`)
  await page.waitForTimeout(600)
  await snap(page, `${pre}-completed`)
}

// --- quest specs -----------------------------------------------------------

// Evennia's @py exec() uses separate globals/locals, which breaks name
// lookup for imports inside list/gen comprehensions ("NameError: 'quest_kill'
// is not defined" from inside a <listcomp>). Workaround: expand repeated
// calls into explicit semicolon-joined statements at module scope.
const rep = (n, stmt) => Array(n).fill(stmt).join('; ')

const SPEC_ROAD_CLEAR = {
  key: 'road_clear', title: 'Clear the Old Road',
  room: "Songbird's Rest",
  label: 'q01-road-clear',
  tick: `from commands.quests import quest_kill; ${rep(5, 'quest_kill(me, "zombie")')}`,
}
const SPEC_WOLF_PROBLEM = {
  key: 'wolf_problem', title: 'The Wolf Problem',
  room: "Songbird's Rest",
  label: 'q02-wolf-problem',
  tick: `from commands.quests import quest_kill; ${rep(3, 'quest_kill(me, "wild wolf")')}`,
}
const SPEC_BANDIT_THREAT = {
  key: 'bandit_threat', title: 'Bandits on the Docks',
  room: "Maker's Hollow",
  label: 'q03-bandit-threat',
  tick: `from commands.quests import quest_kill; ${rep(4, 'quest_kill(me, "bandit")')}`,
}
const SPEC_UNDEAD_PATROL = {
  // prereq: road_clear must be completed first
  key: 'undead_patrol', title: 'Undead Patrol',
  room: "Songbird's Rest",
  label: 'q04-undead-patrol',
  tick:
    `from commands.quests import quest_kill; ` +
    `${rep(3, 'quest_kill(me, "skeleton archer")')}; ` +
    `${rep(3, 'quest_kill(me, "zombie")')}`,
}
const SPEC_REAGENT_RUN = {
  key: 'reagent_run', title: 'Reagent Run',
  room: "The Marketplace",
  label: 'q05-reagent-run',
  tick: `from commands.quests import quest_gather; ${rep(5, 'quest_gather(me, "Sayge")')}`,
}
const SPEC_FORGE_SUPPLIES = {
  // prereq: bandit_threat
  key: 'forge_supplies', title: 'Forge Supplies',
  room: "Maker's Hollow",
  label: 'q06-forge-supplies',
  tick: `from commands.quests import quest_gather; ${rep(5, 'quest_gather(me, "iron ingots")')}`,
}
const SPEC_GRAVEYARD_RECON = {
  key: 'graveyard_recon', title: 'Graveyard Reconnaissance',
  room: "Maker's Hollow",
  label: 'q07-graveyard-recon',
  tick: `from commands.quests import quest_explore; quest_explore(me, "Raven's Rest Graveyard")`,
}
const SPEC_GRIZZLED_VETERAN = {
  // Simulate: win the duel via quest_duel_win, then deliver the contract
  // via the real drop path so the newly-added _fire_item_received →
  // quest_gather tick path is exercised end-to-end.
  key: 'grizzled_veteran', title: 'The Grizzled Veteran',
  room: "The Aentact",
  label: 'q08-grizzled-veteran',
  tick:
    `from commands.quests import quest_duel_win; ` +
    `from world.npc_gifts import announce_item_drop; ` +
    `from evennia import spawn; ` +
    `quest_duel_win(me, "hamond the talon"); ` +
    `items = spawn("SIGNED_OBAN_CONTRACT"); ` +
    `items[0].move_to(me, quiet=True) if items else None; ` +
    `announce_item_drop(me, items[0], from_source_name="Hamond the Talon") if items else None`,
}
const SPEC_MARKET_SURVEY = {
  key: 'market_survey', title: 'Market Survey',
  room: "The Marketplace",
  label: 'q09-market-survey',
  tick: `from commands.quests import quest_explore; quest_explore(me, "The Marketplace")`,
}
const SPEC_RESCUE_BLACKSMITH = {
  key: 'rescue_blacksmith', title: 'Rescue the Crafters: The Blacksmith',
  room: 'The Bannon Barracks', label: 'q10-rescue-blacksmith',
  tick:
    `from commands.quests import quest_kill, quest_explore; ` +
    `${rep(3, 'quest_kill(me, "crow striker")')}; ` +
    `quest_kill(me, "crow bruiser"); ` +
    `quest_explore(me, "Crow Camp — Blacksmith's Prison")`,
}
const SPEC_RESCUE_ALCHEMIST = {
  // prereq rescue_blacksmith; giver Torben lives inside hostile camp — bypass
  key: 'rescue_alchemist', title: 'Rescue the Crafters: The Alchemist',
  room: null, label: 'q11-rescue-alchemist',
  tick:
    `from commands.quests import quest_kill, quest_explore; ` +
    `${rep(3, 'quest_kill(me, "crow striker")')}; ` +
    `${rep(2, 'quest_kill(me, "crow bruiser")')}; ` +
    `quest_explore(me, "Crow Camp — Fox Den")`,
}
const SPEC_RESCUE_ARTIFICER = {
  // prereq rescue_alchemist; giver Marta lives inside hostile camp — bypass
  key: 'rescue_artificer', title: 'Rescue the Crafters: The Artificer',
  room: null, label: 'q12-rescue-artificer',
  tick:
    `from commands.quests import quest_kill; ` +
    `quest_kill(me, "cale the thorn"); ` +
    `${rep(5, 'quest_kill(me, "crow")')}`,
}

const CROWS_QUESTS = [
  SPEC_RESCUE_BLACKSMITH, SPEC_RESCUE_ALCHEMIST, SPEC_RESCUE_ARTIFICER,
]

// Order respects prereqs: road_clear before undead_patrol, bandit_threat
// before forge_supplies, rescue_blacksmith → alchemist → artificer.
const ALL_QUESTS = [
  SPEC_ROAD_CLEAR,
  SPEC_WOLF_PROBLEM,
  SPEC_BANDIT_THREAT,
  SPEC_UNDEAD_PATROL,
  SPEC_REAGENT_RUN,
  SPEC_FORGE_SUPPLIES,
  SPEC_GRAVEYARD_RECON,
  SPEC_GRIZZLED_VETERAN,
  SPEC_MARKET_SURVEY,
  SPEC_RESCUE_BLACKSMITH,
  SPEC_RESCUE_ALCHEMIST,
  SPEC_RESCUE_ARTIFICER,
]

// --- setup-auth ------------------------------------------------------------

async function runSetupAuth() {
  console.log('Opening a visible browser for first-time sign-in.')
  console.log('Click the Google button, finish OAuth, wait for the game UI.')
  console.log(`Target: ${TARGET.url}   Saving auth to: ${AUTH_STATE}`)

  // Google blocks OAuth in automation-flagged browsers. Use real Chrome
  // (channel: 'chrome') and strip automation flags. Headless scenarios
  // reuse the saved session so they never hit Google's checks.
  const browser = await chromium.launch({
    headless: false,
    channel: 'chrome',
    args: ['--disable-blink-features=AutomationControlled'],
    ignoreDefaultArgs: ['--enable-automation'],
  })
  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
    userAgent:
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ' +
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
  })
  const page = await context.newPage()
  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined })
  })
  await page.goto(TARGET.url, { waitUntil: 'domcontentloaded' })

  try {
    await waitForGameOrCharsel(page, 300000)  // 5 min
  } catch {
    console.error('Timed out. Nothing saved.')
    await browser.close()
    process.exit(1)
  }
  await page.waitForTimeout(1500)
  await context.storageState({ path: AUTH_STATE })
  console.log(`\n✅ Saved auth state to ${AUTH_STATE}`)
  await browser.close()
}

// --- main ------------------------------------------------------------------

async function main() {
  if (SCENARIO === 'setup-auth') {
    await runSetupAuth()
    return
  }

  const scenario = SCENARIOS[SCENARIO]
  if (!scenario) {
    console.error(`Unknown scenario: ${SCENARIO}`)
    console.error(`Known: setup-auth, ${Object.keys(SCENARIOS).join(', ')}`)
    process.exit(2)
  }

  if (TARGET_NAME === 'prod' && !READ_ONLY.has(SCENARIO)) {
    console.error(`Scenario '${SCENARIO}' is not read-only; refusing to run against prod.`)
    console.error(`Read-only scenarios: ${[...READ_ONLY].join(', ')}`)
    process.exit(2)
  }

  if (!(await authStateExists())) {
    console.error(
      `No saved auth at ${AUTH_STATE}. ` +
      `Run: node playtest-ui.mjs setup-auth --target=${TARGET_NAME}`
    )
    process.exit(2)
  }

  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
    storageState: AUTH_STATE,
  })
  const page = await context.newPage()

  const consoleErrors = []
  const consoleAll = []
  const gameText = []  // server-side @py me.msg() + [qtest] lines land here
  page.on('pageerror', (err) => consoleErrors.push(`pageerror: ${err.message}`))
  page.on('console', (msg) => {
    consoleAll.push(`[${msg.type()}] ${msg.text()}`)
    if (msg.type() === 'error') consoleErrors.push(`console.error: ${msg.text()}`)
  })
  page.on('requestfailed', (req) =>
    consoleErrors.push(`requestfailed: ${req.url()} — ${req.failure()?.errorText}`))
  page.on('websocket', (ws) => {
    console.log(`  ws opened: ${ws.url()}`)
    ws.on('framereceived', (d) => {
      const raw = typeof d.payload === 'string' ? d.payload : ''
      if (consoleAll.length < 500) consoleAll.push(`[ws<<] ${raw.slice(0, 240)}`)
      // Capture lines starting with [qtest] or [test] from server game feed.
      // Evennia wraps output frames in a Telnet/JSON envelope — cheap grep.
      for (const tag of ['[qtest]', '[test]']) {
        if (raw.includes(tag)) {
          const idx = raw.indexOf(tag)
          gameText.push(raw.slice(Math.max(0, idx - 10), idx + 400))
        }
      }
    })
    ws.on('framesent', (d) => {
      const s = typeof d.payload === 'string' ? d.payload.slice(0, 240) : '(binary)'
      if (consoleAll.length < 500) consoleAll.push(`[ws>>] ${s}`)
    })
  })

  const runStart = new Date()
  let ok = true
  let errMsg = null
  try {
    console.log(`=== Scenario: ${SCENARIO}  [target=${TARGET_NAME}] ===`)
    await login(page)
    await ensureCharacter(page, CHAR_NAME)
    await scenario(page)
    console.log('\n=== PASS ===')
  } catch (err) {
    ok = false
    errMsg = err.message
    console.error(`\n=== FAIL: ${err.message} ===`)
    try { await snap(page, '99-failure') } catch {}
  } finally {
    if (consoleErrors.length) {
      console.log('\nBrowser console errors:')
      for (const e of consoleErrors) console.log(`  ${e}`)
    }
    if (process.env.PLAYTEST_VERBOSE) {
      console.log('\nAll console + WS frames:')
      for (const e of consoleAll) console.log(`  ${e}`)
    }
    await browser.close()
    try {
      const runDir = await archiveRun({
        runStart, ok, errMsg, consoleErrors, gameText,
      })
      console.log(`\n📁 Run archived: ${path.relative(process.cwd(), runDir)}`)
    } catch (archErr) {
      console.error(`(run archive failed: ${archErr.message})`)
    }
  }
  process.exit(ok ? 0 : 1)
}

// Archive screenshots + a markdown summary for this run so past runs
// remain reviewable. Creates runs/<stamp>-<target>-<scenario>/ with
// the PNGs copied in and a run.md summary.
async function archiveRun({ runStart, ok, errMsg, consoleErrors, gameText }) {
  const stamp = runStart.toISOString().replace(/[:.]/g, '-').slice(0, 19)
  const dir = path.join(RUNS_DIR, `${stamp}-${TARGET_NAME}-${SCENARIO}`)
  await fs.mkdir(dir, { recursive: true })

  // Copy screenshots whose names match this run's prefix.
  const prefix = `${TARGET_NAME}-${SCENARIO}-`
  let copied = []
  try {
    const entries = await fs.readdir(SHOT_DIR)
    for (const name of entries) {
      if (!name.startsWith(prefix)) continue
      await fs.copyFile(path.join(SHOT_DIR, name), path.join(dir, name))
      copied.push(name)
    }
    copied.sort()
  } catch {}

  const durationMs = Date.now() - runStart.getTime()
  const lines = [
    `# Playtest run: ${SCENARIO}`,
    '',
    `- **Target:** ${TARGET_NAME} (${TARGET.url})`,
    `- **Character:** ${CHAR_NAME}`,
    `- **Start:** ${runStart.toISOString()}`,
    `- **Duration:** ${(durationMs / 1000).toFixed(1)}s`,
    `- **Result:** ${ok ? '✅ PASS' : `❌ FAIL — ${errMsg || 'unknown'}`}`,
    '',
    '## Screenshots',
    copied.length
      ? copied.map((n) => `- \`${n}\``).join('\n')
      : '_(none)_',
    '',
    '## Game feed (server [qtest]/[test] lines)',
    gameText.length
      ? '```\n' + gameText.slice(0, 200).join('\n') + '\n```'
      : '_(none captured)_',
    '',
    '## Browser console errors',
    consoleErrors.length
      ? '```\n' + consoleErrors.join('\n') + '\n```'
      : '_(none)_',
    '',
  ]
  await fs.writeFile(path.join(dir, 'run.md'), lines.join('\n'))
  return dir
}

main().catch((e) => { console.error(e); process.exit(1) })
