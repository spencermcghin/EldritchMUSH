/**
 * playtest-ui.mjs — Playwright-driven UI smoke-test for EldritchMUSH.
 *
 * Drives the real web client (Google OAuth or username/password) through
 * a scripted sequence and saves screenshots to ./screenshots/ for visual
 * verification.
 *
 * Because Google OAuth cannot be automated, auth is a one-time step:
 *
 *   node playtest-ui.mjs setup-auth     # opens a visible browser; you
 *                                       # sign in with Google once, then
 *                                       # we save cookies to auth-state.json
 *
 *   node playtest-ui.mjs crafting-modal # headless, reuses saved cookies
 *
 * For local username/password accounts you can skip OAuth and pass:
 *   export PLAYTEST_USER=...
 *   export PLAYTEST_PASS=...
 *
 * Override frontend URL (defaults: vite 5173, then evennia 4001):
 *   export PLAYTEST_URL=http://localhost:5173
 */

import { chromium } from 'playwright'
import path from 'node:path'
import fs from 'node:fs/promises'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SHOT_DIR = path.join(__dirname, 'screenshots')
const AUTH_STATE = path.join(__dirname, 'auth-state.json')

const USER = process.env.PLAYTEST_USER
const PASS = process.env.PLAYTEST_PASS

// Candidate frontends to try in order. Vite dev first (this project
// configures it to port 3000; default vite is 5173); falls back to the
// Evennia-served production build on 4001 if nothing is running on the
// dev port.
const CANDIDATE_URLS = process.env.PLAYTEST_URL
  ? [process.env.PLAYTEST_URL]
  : ['http://localhost:3000', 'http://localhost:5173', 'http://localhost:4001']

const SCENARIO = process.argv[2] || 'crafting-modal'

// --- helpers ---------------------------------------------------------------

async function pickReachableUrl() {
  for (const url of CANDIDATE_URLS) {
    try {
      const res = await fetch(url, { method: 'GET' })
      if (res.ok || res.status < 500) return url
    } catch {}
  }
  throw new Error(
    `No frontend reachable. Tried: ${CANDIDATE_URLS.join(', ')}. ` +
    `Start the dev server: cd frontend && npm run dev`
  )
}

async function snap(page, name) {
  await fs.mkdir(SHOT_DIR, { recursive: true })
  const p = path.join(SHOT_DIR, `${SCENARIO}-${name}.png`)
  await page.screenshot({ path: p, fullPage: false })
  console.log(`  📸 ${path.relative(process.cwd(), p)}`)
  return p
}

async function typeCommand(page, cmd) {
  // The command input is always present while connected. Find it and
  // submit the command via keyboard Enter.
  const input = page.locator('input, textarea').first()
  await input.fill(cmd)
  await input.press('Enter')
  // Small settle — server round-trip + render
  await page.waitForTimeout(500)
}

async function clickSidebarButton(page, label) {
  // Sidebar entries are .cmd-entry with a .cmd-key span.
  const entry = page.locator('.cmd-entry', { hasText: label }).first()
  try {
    await entry.waitFor({ state: 'visible', timeout: 5000 })
  } catch (err) {
    // Dump the sidebar so we know what's there
    const sidebar = await page.locator('.cmd-sidebar').textContent().catch(() => '(no sidebar)')
    throw new Error(`Sidebar button '${label}' not found. Sidebar contents:\n${sidebar}`)
  }
  await entry.click()
  await page.waitForTimeout(400)
}

async function authStateExists() {
  try {
    await fs.access(AUTH_STATE)
    return true
  } catch {
    return false
  }
}

// When using username/password (no Google OAuth), we need a *Django*
// session so fetch('/api/account/characters/') works. The WebSocket
// `connect <user> <pass>` login only auths the MUD session, not Django.
// POST to /admin/login/ first to establish the Django session cookie.
async function djangoLoginFallback(context, baseUrl) {
  const loginUrl = new URL('/admin/login/', baseUrl).toString()
  // First GET to obtain CSRF
  const getResp = await context.request.get(loginUrl)
  const getBody = await getResp.text()
  const m = getBody.match(/name="csrfmiddlewaretoken"\s+value="([^"]+)"/)
  if (!m) throw new Error('Could not extract CSRF token from /admin/login/')
  const csrf = m[1]

  const postResp = await context.request.post(loginUrl, {
    form: {
      csrfmiddlewaretoken: csrf,
      username: USER,
      password: PASS,
      next: '/admin/',
    },
    headers: {
      referer: loginUrl,
    },
  })
  // Django redirects to /admin/ on success; a 200 with the login form
  // again means bad creds.
  if (postResp.status() >= 400) {
    throw new Error(`Django /admin/login/ returned ${postResp.status()}`)
  }
  const finalBody = await postResp.text()
  if (finalBody.includes('name="password"') && finalBody.includes('action="/admin/login/"')) {
    throw new Error('Django /admin/login/ rejected credentials')
  }
}

async function login(page, url) {
  console.log(`→ ${url}`)

  // If we have username/password, establish a Django session first so
  // the REST endpoints the React app calls (characters list, etc.)
  // return authenticated data.
  if (USER && PASS) {
    try {
      await djangoLoginFallback(page.context(), url)
      console.log('  ✓ Django session established via /admin/login/')
    } catch (err) {
      console.warn(`  ⚠ Django /admin/login/ pre-step failed: ${err.message}`)
    }
  }

  await page.goto(url, { waitUntil: 'domcontentloaded' })

  // Wait up to 20s for ANY of: game UI visible (auth succeeded from
  // Django session / saved cookies) OR login form visible (need to
  // type credentials). Whichever wins tells us what to do next.
  const gameSel = '.cmd-sidebar, .charsel-screen'
  const formSel = 'input[autocomplete="username"]'
  const winner = await Promise.race([
    page.locator(gameSel).first().waitFor({ state: 'visible', timeout: 20000 })
      .then(() => 'game').catch(() => null),
    page.locator(formSel).first().waitFor({ state: 'visible', timeout: 20000 })
      .then(() => 'form').catch(() => null),
  ])

  if (winner === 'game') {
    await page.waitForTimeout(600)
    await snap(page, '02-post-login-restored')
    return
  }

  if (winner !== 'form') {
    throw new Error('Neither game UI nor login form appeared within 20s.')
  }

  // Need credentials.
  if (!USER || !PASS) {
    throw new Error(
      'Not authenticated and no PLAYTEST_USER/PLAYTEST_PASS set. ' +
      'Run `node playtest-ui.mjs setup-auth` once to log in via Google, ' +
      'or export PLAYTEST_USER/PASS for username login.'
    )
  }

  const toggle = page.locator('button.login-fallback-toggle')
  if (await toggle.count()) {
    const text = await toggle.textContent()
    if (text && text.includes('sign in with username')) {
      await toggle.click()
    }
  }
  await page.locator(formSel).fill(USER)
  await page.locator('input[autocomplete="current-password"]').fill(PASS)
  await snap(page, '01-login-form')
  await page.locator('button.login-btn[type="submit"]').click()

  await page.locator(gameSel).first().waitFor({ state: 'visible', timeout: 15000 })
  await page.waitForTimeout(800)
  await snap(page, '02-post-login')
}

async function pickCharacterIfNeeded(page, preferredName = null) {
  // If CharacterSelect is showing, click the named character (or first).
  const charSelect = page.locator('.charsel-screen')
  if (await charSelect.count() === 0) return

  // Find the card labeled with the preferred character name. Skip
  // "Create New Character" cards.
  let target = null
  if (preferredName) {
    const candidate = page
      .locator('.charsel-screen .charsel-card', { hasText: preferredName })
      .first()
    if (await candidate.count()) target = candidate
  }
  if (!target) {
    const cards = page.locator('.charsel-screen .charsel-card')
    const n = await cards.count()
    for (let i = 0; i < n; i++) {
      const text = (await cards.nth(i).textContent()) || ''
      if (!text.toLowerCase().includes('create new')) {
        target = cards.nth(i)
        break
      }
    }
  }
  if (target && (await target.count())) {
    // Wait for the WebSocket to finish connecting before clicking — the
    // card's handler sends `ic <name>` via the WS, which is a no-op if
    // we click while still in the `connecting` state.
    await page
      .locator('.status-label.connected')
      .first()
      .waitFor({ state: 'visible', timeout: 15000 })
      .catch(() => {})
    await page.waitForTimeout(400)

    // The whole card is a <button>. Clicking it fires the puppet flow
    // (`ooc` then `ic <name>`).
    await target.click()
    await page.waitForSelector('.cmd-sidebar', { timeout: 15000 })
    await page.waitForTimeout(1000)
  }
}

// --- scenarios -------------------------------------------------------------

const SCENARIOS = {
  login: async (page) => {
    // Login + post-login already captured by login(). Nothing extra.
  },

  'crafting-modal': async (page) => {
    await typeCommand(page, "@tel #2054")  // The Crafter's Quarter
    await page.waitForTimeout(1500)
    await snap(page, '03-crafter-quarter')

    // Opening the modal via direct OOB is more robust than waiting for
    // the sidebar push to land. Both paths exercise the same backend.
    await typeCommand(page, '__crafting_ui__')
    await page.waitForSelector('.alchemy-modal', { timeout: 8000 })
    await page.waitForTimeout(400)
    await snap(page, '04-modal-open')

    // Try each tab and snap
    const tabs = page.locator('.crafting-tab')
    const n = await tabs.count()
    console.log(`  found ${n} crafting tab(s)`)
    for (let i = 0; i < n; i++) {
      const t = tabs.nth(i)
      const label = (await t.textContent() || '').trim().split('\n')[0].trim()
      await t.click()
      await page.waitForTimeout(250)
      await snap(page, `05-tab-${i}-${label.toLowerCase().replace(/[^a-z]+/g, '')}`)

      // Click the first recipe if any
      const firstRecipe = page.locator('.alchemy-recipe-item').first()
      if (await firstRecipe.count()) {
        await firstRecipe.click()
        await page.waitForTimeout(250)
        await snap(page, `06-tab-${i}-recipe-detail`)
      }
    }
  },

  'crafting-ironhaven': async (page) => {
    await typeCommand(page, '@tel #2078')  // Ironhaven Forge
    await page.waitForTimeout(1500)
    await snap(page, '03-ironhaven-forge')
    await typeCommand(page, '__crafting_ui__')
    await page.waitForSelector('.alchemy-modal', { timeout: 8000 })
    await snap(page, '04-modal-at-forge')
  },

  'crafting-docks': async (page) => {
    await typeCommand(page, '@tel #2058')  // The Back Alley
    await page.waitForTimeout(1500)
    await snap(page, '03-back-alley')
    // The Back Alley has no crafting station; modal should still open
    // in superuser mode but with all tabs reporting "no station".
    await typeCommand(page, '__crafting_ui__')
    await page.waitForSelector('.alchemy-modal', { timeout: 8000 })
    await snap(page, '04-modal-at-alley')
  },
}

// --- main ------------------------------------------------------------------

// setup-auth: launch a visible browser so the user can click through
// Google OAuth manually. When they land back on the game UI we save
// the cookies + localStorage to AUTH_STATE for future headless runs.
async function runSetupAuth() {
  const url = await pickReachableUrl()
  console.log('Opening a visible browser for first-time sign-in.')
  console.log('Click the Google button, finish OAuth in the window, and')
  console.log('wait until the game UI loads. The session will be saved.')
  console.log(`Target: ${url}`)

  const browser = await chromium.launch({ headless: false })
  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
  })
  const page = await context.newPage()
  await page.goto(url, { waitUntil: 'domcontentloaded' })

  // Wait up to 3 minutes for the game UI to appear (after OAuth returns).
  try {
    await page
      .locator('.cmd-sidebar, .charsel-screen')
      .first()
      .waitFor({ state: 'visible', timeout: 180000 })
  } catch {
    console.error('Timed out waiting for game UI. Nothing saved.')
    await browser.close()
    process.exit(1)
  }

  await page.waitForTimeout(1500)
  await context.storageState({ path: AUTH_STATE })
  console.log(`\n✅ Saved auth state to ${path.relative(process.cwd(), AUTH_STATE)}`)
  console.log('Future runs will reuse this session headlessly.')
  await browser.close()
}

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

  const url = await pickReachableUrl()
  const browser = await chromium.launch({ headless: true })

  const contextOpts = { viewport: { width: 1400, height: 900 } }
  if (await authStateExists()) {
    contextOpts.storageState = AUTH_STATE
  }
  const context = await browser.newContext(contextOpts)
  const page = await context.newPage()

  // Capture console errors + all console output for the report
  const consoleErrors = []
  const consoleAll = []
  page.on('pageerror', (err) => consoleErrors.push(`pageerror: ${err.message}`))
  page.on('console', (msg) => {
    consoleAll.push(`[${msg.type()}] ${msg.text()}`)
    if (msg.type() === 'error') {
      consoleErrors.push(`console.error: ${msg.text()}`)
    }
  })
  // Capture network failures
  page.on('requestfailed', (req) =>
    consoleErrors.push(`requestfailed: ${req.url()} — ${req.failure()?.errorText}`)
  )
  page.on('websocket', (ws) => {
    console.log(`  ws opened: ${ws.url()}`)
    ws.on('close', () => console.log(`  ws closed: ${ws.url()}`))
    ws.on('framereceived', (data) => {
      const s = typeof data.payload === 'string'
        ? data.payload.slice(0, 120)
        : '(binary)'
      if (consoleAll.length < 50) consoleAll.push(`[ws<<] ${s}`)
    })
    ws.on('framesent', (data) => {
      const s = typeof data.payload === 'string'
        ? data.payload.slice(0, 120)
        : '(binary)'
      if (consoleAll.length < 50) consoleAll.push(`[ws>>] ${s}`)
    })
    ws.on('socketerror', (e) => consoleErrors.push(`ws socketerror: ${e}`))
  })

  let ok = true
  try {
    console.log(`=== Scenario: ${SCENARIO} ===`)
    await login(page, url)
    await pickCharacterIfNeeded(page, process.env.PLAYTEST_CHARACTER || 'Aethel')
    await scenario(page)
    console.log('\n=== PASS ===')
  } catch (err) {
    ok = false
    console.error(`\n=== FAIL: ${err.message} ===`)
    try {
      await snap(page, '99-failure')
    } catch {}
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

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
