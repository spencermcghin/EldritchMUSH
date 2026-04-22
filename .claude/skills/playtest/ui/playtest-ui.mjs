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
  await page.locator('.charsel-card-create').click()
  await page.locator('.charsel-modal-input').fill(name)
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
}

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
      const s = typeof d.payload === 'string' ? d.payload.slice(0, 120) : '(binary)'
      if (consoleAll.length < 50) consoleAll.push(`[ws<<] ${s}`)
    })
    ws.on('framesent', (d) => {
      const s = typeof d.payload === 'string' ? d.payload.slice(0, 120) : '(binary)'
      if (consoleAll.length < 50) consoleAll.push(`[ws>>] ${s}`)
    })
  })

  let ok = true
  try {
    console.log(`=== Scenario: ${SCENARIO}  [target=${TARGET_NAME}] ===`)
    await login(page)
    await ensureCharacter(page, CHAR_NAME)
    await scenario(page)
    console.log('\n=== PASS ===')
  } catch (err) {
    ok = false
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
  }
  process.exit(ok ? 0 : 1)
}

main().catch((e) => { console.error(e); process.exit(1) })
