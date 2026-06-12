/**
 * living-world.mjs — one-off Playwright drive of the 12 living-world
 * features on UAT, as character "Spencer Eldritch".
 *
 * Run:  node living-world.mjs
 * Output: per-test RESULT lines + captured game text; screenshots in
 * screenshots/uat-living-world-*.png
 */
import { chromium } from 'playwright'
import path from 'node:path'
import fs from 'node:fs/promises'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SHOT_DIR = path.join(__dirname, 'screenshots')
const AUTH = path.join(__dirname, 'auth-uat.json')
const URL = 'https://uat.eldritchmush.com'
const CHAR = 'Spencer'  // account card label; actual key checked in-game

const frames = []          // decoded WS text payloads, in order
const consoleErrors = []
const results = []         // {test, verdict, notes[]}
const shots = []

function log(s) { console.log(s) }

function lastFrames(n = 12) { return frames.slice(-n).join('\n') }

// Evennia echoes @py input back as ">>> <code>" (HTML-escaped as &gt;&gt;&gt;).
// Those echo frames contain our MARK strings — never match against them.
function isEcho(f) { return /^(\s|<[^>]+>)*(&gt;|>){3}/.test(f) || f.includes('&gt;&gt;&gt;') }

function findSince(idx, pattern) {
  const re = pattern instanceof RegExp ? pattern : new RegExp(pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i')
  for (let i = idx; i < frames.length; i++) {
    if (isEcho(frames[i])) continue
    if (re.test(frames[i])) return { i, text: frames[i] }
  }
  return null
}

async function waitFor(page, sinceIdx, pattern, timeoutMs = 12000) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    const hit = findSince(sinceIdx, pattern)
    if (hit) return hit
    await page.waitForTimeout(250)
  }
  return null
}

// Evennia @py swaps sys.stdout for a FakeStd lacking .flush; living_world
// uses print(..., flush=True) which then raises AttributeError mid-line.
// Shim flush in every @py so server-side prints don't abort our commands.
const FLUSH_SHIM = "import sys as _ss; _ss.stdout.flush = (lambda *a: None); _ss.stderr.flush = (lambda *a: None); "

async function send(page, cmd, settle = 700) {
  if (cmd.startsWith('@py ')) cmd = '@py ' + FLUSH_SHIM + cmd.slice(4)
  const input = page.locator('.cmd-input').first()
  await input.click()
  await input.fill(cmd)
  await input.press('Enter')
  await page.waitForTimeout(settle)
}

async function snap(page, name) {
  await fs.mkdir(SHOT_DIR, { recursive: true })
  const p = path.join(SHOT_DIR, `uat-living-world-${name}.png`)
  await page.screenshot({ path: p })
  shots.push(p)
  log(`  [SHOT] ${p}`)
  return p
}

// strip evennia/html markup-ish noise for quoting
function clean(s) {
  return (s || '').replace(/\|\[?[0-9a-zA-Z\/]{1,3}/g, '').replace(/\s+/g, ' ').trim()
}

async function main() {
  const browser = await chromium.launch({ headless: true })
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 }, storageState: AUTH })
  const page = await ctx.newPage()
  page.on('pageerror', (e) => consoleErrors.push(`pageerror: ${e.message}`))
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(`console.error: ${m.text()}`) })
  page.on('websocket', (ws) => {
    ws.on('framereceived', (d) => {
      const raw = typeof d.payload === 'string' ? d.payload : ''
      try {
        const j = JSON.parse(raw)
        if (Array.isArray(j) && j[0] === 'text') frames.push(String(j[1]))
        else frames.push(raw)
      } catch { frames.push(raw) }
    })
  })

  // ---- login + character select ----
  log(`→ ${URL}`)
  await page.goto(URL, { waitUntil: 'domcontentloaded' })
  const winner = await Promise.race([
    page.locator('.cmd-sidebar').first().waitFor({ state: 'visible', timeout: 25000 }).then(() => 'game').catch(() => null),
    page.locator('.charsel-screen').first().waitFor({ state: 'visible', timeout: 25000 }).then(() => 'charsel').catch(() => null),
  ])
  if (!winner) { log('FATAL: login failed (no game UI, no charsel). Auth may have expired.'); await browser.close(); process.exit(2) }
  if (winner === 'charsel') {
    await page.locator('.status-label.connected').first().waitFor({ state: 'visible', timeout: 15000 }).catch(() => {})
    await page.waitForTimeout(500)
    const card = page.locator('.charsel-screen .charsel-card', { hasText: CHAR }).first()
    if (!(await card.count())) { log(`FATAL: no character card '${CHAR}'`); await browser.close(); process.exit(2) }
    await card.click()
    await page.waitForSelector('.cmd-sidebar', { timeout: 15000 })
  }
  await page.waitForTimeout(1200)
  await snap(page, '00-logged-in')

  const T = async (name, fn) => {
    log(`\n===== ${name} =====`)
    const r = { test: name, verdict: 'PASS', notes: [] }
    results.push(r)
    const note = (s) => { r.notes.push(s); log(`  ${s}`) }
    const fail = (s) => { r.verdict = 'FAIL'; note(`FAIL: ${s}`) }
    const partial = (s) => { if (r.verdict === 'PASS') r.verdict = 'PARTIAL'; note(`PARTIAL: ${s}`) }
    try { await fn({ note, fail, partial }) }
    catch (e) { r.verdict = 'FAIL'; note(`EXCEPTION: ${e.message}`) }
  }

  // ---- SETUP backup ----
  await T('SETUP-backup', async ({ note, fail }) => {
    let i = frames.length
    await send(page, `@py me.db.lw_backup = {'npc_rep': dict(me.db.npc_rep or {}), 'esp': me.db.espionage, 'quests_n': len(me.db.quests or {})}; print('MARK_SETUP_OK key=' + me.key, '| esp=', me.db.lw_backup['esp'], '| quests=', me.db.lw_backup['quests_n'])`)
    const hit = await waitFor(page, i, 'MARK_SETUP_OK')
    if (!hit) fail('backup @py produced no MARK_SETUP_OK. Last: ' + clean(lastFrames(4)))
    else note('backup saved: ' + clean(hit.text))
  })

  // ---- T1 fortunes ----
  await T('T1-true-fortunes', async ({ note, fail, partial }) => {
    let i = frames.length
    await send(page, '@tel The Mystvale Marketplace', 1200)
    i = frames.length
    await send(page, 'look cabinet', 900)
    const cab = await waitFor(page, i, /Artessa/i, 6000)
    if (cab) note('cabinet desc mentions Artessa: ' + clean(cab.text).slice(0, 300))
    else partial('look cabinet did not mention Artessa. Got: ' + clean(lastFrames(3)).slice(0, 300))
    i = frames.length
    await send(page, 'pull crank', 500)
    const fortune = await waitFor(page, i, /It reads:/i, 12000)
    await page.waitForTimeout(800)
    await snap(page, 't1-fortune')
    if (!fortune) fail('no fortune within 12s. Got: ' + clean(lastFrames(5)).slice(0, 400))
    else {
      const after = findSince(fortune.i, /It reads:/i)
      note('FORTUNE: ' + clean(frames.slice(fortune.i, fortune.i + 3).join(' ')).slice(0, 800))
    }
    i = frames.length
    await send(page, 'pull crank', 500)
    const cd = await waitFor(page, i, /repeat herself so soon/i, 8000)
    if (cd) note('cooldown line OK: ' + clean(cd.text).slice(0, 200))
    else fail('no cooldown line on 2nd pull. Got: ' + clean(lastFrames(4)).slice(0, 300))
  })

  // ---- T2 séance ----
  await T('T2-seance', async ({ note, fail, partial }) => {
    let i = frames.length
    await send(page, '@tel The Lost Scriptorium — The Sunken Door', 1500)
    let arrived = findSince(i, /Sunken Door/i)
    if (!arrived) {
      i = frames.length
      await send(page, `@py from evennia.utils.search import search_object; r = [o for o in search_object('The Lost Scriptorium — The Sunken Door')]; print('MARK_DBREF', r[0].dbref if r else 'NONE')`)
      const h = await waitFor(page, i, /MARK_DBREF/)
      const m = h && h.text.match(/MARK_DBREF\s+(#\d+)/)
      if (!m) { fail('could not reach Sunken Door room: ' + clean(lastFrames(4))); return }
      i = frames.length
      await send(page, `@tel ${m[1]}`, 1500)
    }
    i = frames.length
    await send(page, 'ask the apparition of zeke = What can you tell me about the keys?', 500)
    // panel should pop immediately with pending state
    const panelUp = await page.locator('.npc-dialogue-panel').first().waitFor({ state: 'visible', timeout: 8000 }).then(() => true).catch(() => false)
    if (!panelUp) { fail('NPC dialogue panel never appeared'); return }
    // wait for ghost-treated reply
    const ghost = await page.locator('.ghost-text').first().waitFor({ state: 'visible', timeout: 15000 }).then(() => true).catch(() => false)
    await page.waitForTimeout(2500) // let words drift in
    const state = await page.evaluate(() => ({
      seance: !!document.querySelector('.app-container.seance-active'),
      ghostText: document.querySelector('.ghost-text')?.innerText || null,
      strikes: document.querySelectorAll('.ghost-strike').length,
      corrections: document.querySelectorAll('.ghost-correction').length,
      vignette: !!document.querySelector('.seance-vignette'),
    }))
    await snap(page, 't2-seance-active')
    if (!ghost) fail('no .ghost-text reply within 15s')
    else note('GHOST REPLY: ' + clean(state.ghostText).slice(0, 800))
    if (state.seance) note('seance-active class present on app-container: OK')
    else fail('seance-active class NOT present during ghost reply')
    note(`ghost strikes=${state.strikes} corrections=${state.corrections} vignette-el=${state.vignette}`)
    if (state.strikes < 1 || state.corrections < 1) partial('expected >=1 struck-through word + correction')
    // close panel
    await page.locator('.npc-dialogue-close').first().click().catch(async () => {
      await page.locator('.npc-dialogue-backdrop').first().click({ force: true }).catch(() => {})
    })
    await page.waitForTimeout(1200)
    const after = await page.evaluate(() => !!document.querySelector('.app-container.seance-active'))
    await snap(page, 't2-seance-ended')
    if (after) fail('seance-active class STILL present after closing panel')
    else note('séance ended on panel close: OK')
  })

  // ---- T3 confessions + pry ----
  await T('T3-confess-pry', async ({ note, fail }) => {
    let i = frames.length
    await send(page, '@tel The Aurorym Chantry', 1200)
    i = frames.length
    await send(page, 'confess I tested the vault on a Thursday and felt nothing', 700)
    const kept = await waitFor(page, i, /Vault keeps it/i, 8000)
    if (kept) note('confess OK: ' + clean(kept.text).slice(0, 250))
    else fail('no "Vault keeps it" line. Got: ' + clean(lastFrames(4)).slice(0, 300))
    i = frames.length
    await send(page, `@py [o.db.confession_vault.append({'char':'TestSoul','text':'I buried the bell under the dock','ts':0}) for o in me.location.contents if o.db.is_confessor]; print('MARK_T3_SEED')`)
    await waitFor(page, i, 'MARK_T3_SEED')
    i = frames.length
    await send(page, `@py me.db.espionage = 3; print('MARK_T3_ESP3')`)
    await waitFor(page, i, 'MARK_T3_ESP3')
    i = frames.length
    await send(page, 'pry ansgar', 700)
    const pried = await waitFor(page, i, /buried the bell/i, 10000)
    await snap(page, 't3-pry-result')
    if (!pried) fail('pry did not surface seeded secret. Got: ' + clean(lastFrames(5)).slice(0, 400))
    else {
      note('PRY RESULT: ' + clean(pried.text).slice(0, 500))
      if (!/TestSoul/i.test(frames.slice(i).join(' '))) fail('pried secret missing the name TestSoul')
      else note('TestSoul named in pry output: OK')
    }
    i = frames.length
    await send(page, `@py me.db.espionage = 0; print('MARK_T3_ESP0')`)
    await waitFor(page, i, 'MARK_T3_ESP0')
    i = frames.length
    await send(page, `@py me.db.pry_last = None; print('MARK_T3_PL')`)
    await waitFor(page, i, 'MARK_T3_PL')
    i = frames.length
    await send(page, 'pry ansgar', 700)
    const caught = await waitFor(page, i, /broadsheet/i, 8000)
    if (caught) note('caught line OK: ' + clean(caught.text).slice(0, 250))
    else fail('no "reads you like a broadsheet" line. Got: ' + clean(lastFrames(4)).slice(0, 300))
    // CLEANUP
    i = frames.length
    await send(page, `@py [setattr(o.db,'confession_vault',[e for e in (o.db.confession_vault or []) if e.get('char') not in ('Spencer Eldritch','TestSoul',me.key)]) for o in me.location.contents if o.db.is_confessor]; print('MARK_T3_CLEAN')`)
    const cl = await waitFor(page, i, 'MARK_T3_CLEAN')
    note(cl ? 'CLEANUP vault scrub: confirmed' : 'CLEANUP vault scrub: NO ECHO — verify manually')
  })

  // ---- T4 gossip ----
  await T('T4-gossip', async ({ note, fail }) => {
    let i = frames.length
    await send(page, `@py me.db.npc_rep = {'eldreth of the cirque': {'rep': 2, 'memories': ['watched you cheat the regrets-box at the festival'], 'last_interacted': '2026-06-12T00:00:00Z'}, 'father ansgar the keeper': {'rep': 1, 'memories': [], 'last_interacted': '2026-06-12T00:00:00Z'}}; print('MARK_T4_SEED')`)
    await waitFor(page, i, 'MARK_T4_SEED')
    i = frames.length
    await send(page, `@py from world import living_world; living_world.gossip_tick(4); print('MARK_T4_TICK')`)
    await waitFor(page, i, 'MARK_T4_TICK')
    await page.waitForTimeout(9000)
    i = frames.length
    await send(page, `@py import json; print('MARK_T4_DUMP ' + json.dumps({k: v.get('memories') for k, v in (me.db.npc_rep or {}).items()}, default=str))`)
    const dump = await waitFor(page, i, 'MARK_T4_DUMP', 10000)
    if (!dump) { fail('no memories dump. Got: ' + clean(lastFrames(4)).slice(0, 300)); return }
    note('MEMORIES DUMP: ' + clean(dump.text).slice(0, 1000))
    if (/heard a rumor \(by way of/i.test(dump.text)) note('rumor propagated: OK')
    else fail('no memory starting "heard a rumor (by way of ...)" found in npc_rep')
  })

  // ---- T5 adjudicator letter ----
  await T('T5-adjudicator-letter', async ({ note, fail }) => {
    let i = frames.length
    await send(page, `@py from world import living_world; living_world.deliver_letter(me, 0); print('MARK_T5_SENT')`)
    await waitFor(page, i, 'MARK_T5_SENT')
    const whisper = await waitFor(page, i, /whispers against your pack/i, 12000)
    if (whisper) note('delivery line OK: ' + clean(whisper.text).slice(0, 200))
    else fail('no "whispers against your pack" within 12s')
    i = frames.length
    await send(page, 'look letter', 800)
    let body = await waitFor(page, i, /Adjudicator|parchment|cease/i, 5000)
    if (!body) {
      i = frames.length
      await send(page, 'look sealed letter', 800)
      body = await waitFor(page, i, /Adjudicator|parchment|cease/i, 5000)
    }
    await snap(page, 't5-letter')
    if (!body) fail('letter not readable. Got: ' + clean(lastFrames(5)).slice(0, 300))
    else {
      const blob = clean(frames.slice(body.i, body.i + 4).join(' '))
      note('LETTER: ' + blob.slice(0, 900))
      if (!/Spencer/i.test(blob)) note('WARNING: letter text shown does not name Spencer')
    }
    // CLEANUP
    i = frames.length
    await send(page, `@py [o.delete() for o in me.contents if 'sealed letter' in o.key]; print('MARK_T5_C1')`)
    await waitFor(page, i, 'MARK_T5_C1')
    i = frames.length
    await send(page, `@py [s.stop() for s in me.scripts.all() if s.key.startswith('adjudicator_letter')]; print('MARK_T5_C2')`)
    await waitFor(page, i, 'MARK_T5_C2')
    i = frames.length
    await send(page, `@py me.db.adjudicator_letters_started = None; print('MARK_T5_C3')`)
    const c3 = await waitFor(page, i, 'MARK_T5_C3')
    note(c3 ? 'CLEANUP letter+scripts+flag: confirmed' : 'CLEANUP T5: NO ECHO — verify manually')
  })

  // ---- T6 dream ----
  await T('T6-dierdra-dream', async ({ note, fail }) => {
    let i = frames.length
    await send(page, `@py from world import living_world; living_world.dream_tick(); print('MARK_T6_TICK')`)
    await waitFor(page, i, 'MARK_T6_TICK')
    await page.waitForTimeout(9000)
    i = frames.length
    await send(page, `@py from world import living_world; print('MARK_T6_DREAM ' + str(living_world._dream_npc().db.current_dream))`)
    const dream = await waitFor(page, i, 'MARK_T6_DREAM', 10000)
    if (!dream) fail('no dream dump')
    else {
      const d = clean(dream.text)
      note('DREAM: ' + d.slice(0, 900))
      if (/MARK_T6_DREAM\s*None/.test(dream.text)) fail('current_dream is None')
    }
    i = frames.length
    await send(page, `@py from world import living_world; print('MARK_T6_COUNT', living_world._dream_npc().attributes.get('ai_knowledge', default='').count('HER LATEST DREAM'))`)
    const cnt = await waitFor(page, i, 'MARK_T6_COUNT', 8000)
    if (cnt && /MARK_T6_COUNT\s*1\b/.test(cnt.text)) note('ai_knowledge contains exactly 1 HER LATEST DREAM block: OK')
    else fail('HER LATEST DREAM count != 1: ' + clean(cnt ? cnt.text : lastFrames(3)).slice(0, 200))
  })

  // ---- T7 chronicle ----
  await T('T7-chronicle', async ({ note, fail }) => {
    let i = frames.length
    await send(page, `@py from world import living_world; living_world.chronicle_tick(); print('MARK_T7_TICK')`)
    await waitFor(page, i, 'MARK_T7_TICK')
    await page.waitForTimeout(9000)
    await send(page, "@tel Songbird's Rest", 1200)
    i = frames.length
    await send(page, 'look chronicle', 900)
    const pageHit = await waitFor(page, i, /Chronicle/i, 6000)
    await snap(page, 't7-chronicle')
    if (!pageHit) fail('look chronicle gave nothing chronicle-ish: ' + clean(lastFrames(4)).slice(0, 300))
    else note('CHRONICLE: ' + clean(frames.slice(pageHit.i, pageHit.i + 3).join(' ')).slice(0, 900))
    i = frames.length
    await send(page, 'get chronicle', 800)
    const refusal = await waitFor(page, i, /where all may read it/i, 6000)
    if (refusal) note('get refusal OK: ' + clean(refusal.text).slice(0, 200))
    else fail('chronicle was takeable or refusal line missing: ' + clean(lastFrames(3)).slice(0, 250))
  })

  // ---- T8 mists ----
  await T('T8-moving-mists', async ({ note, fail }) => {
    let i = frames.length
    await send(page, `@py from world import living_world; living_world.mist_tick(); print('MARK_T8_TICK')`, 1500)
    await waitFor(page, i, 'MARK_T8_TICK')
    i = frames.length
    await send(page, `@py from evennia.objects.models import ObjectDB; print('MARK_T8_PAIR ' + str([(e.location.key, '->', e.destination.key) for e in ObjectDB.objects.filter(db_key='mist-passage')]))`)
    const pair = await waitFor(page, i, 'MARK_T8_PAIR', 8000)
    if (!pair) { fail('no mist-passage listing'); return }
    note('PASSAGES: ' + clean(pair.text).slice(0, 400))
    const m = pair.text.match(/\[\('([^']+)',\s*'->',\s*'([^']+)'\)/)
    if (!m) { fail('could not parse passage endpoints — maybe zero passages exist'); return }
    const [, src, dst] = m
    note(`walking ${src} -> ${dst}`)
    await send(page, `@tel ${src}`, 1500)
    i = frames.length
    await send(page, 'look', 1000)
    const vis = await waitFor(page, i, /mist-passage|mist passage/i, 6000)
    if (vis) note('mist-passage visible in room: OK')
    else note('WARNING: mist-passage not obviously listed in look output')
    i = frames.length
    await send(page, 'mist-passage', 1500)
    let arrived = await waitFor(page, i, new RegExp(dst.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i'), 8000)
    if (!arrived) {
      i = frames.length
      await send(page, 'mist', 1500)
      arrived = await waitFor(page, i, new RegExp(dst.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i'), 8000)
    }
    await snap(page, 't8-passage-room')
    if (arrived) note(`arrived at ${dst}: OK`)
    else fail(`did not arrive at ${dst}. Got: ` + clean(lastFrames(5)).slice(0, 300))
  })

  // ---- T9 withering maw ----
  await T('T9-withering-maw', async ({ note, fail }) => {
    let i = frames.length
    await send(page, `@py from world import living_world; print('MARK_T9_FROM ' + living_world._maw().location.key)`)
    const fromHit = await waitFor(page, i, 'MARK_T9_FROM', 8000)
    if (!fromHit) { fail('could not read maw location'); return }
    const fromRoom = clean(fromHit.text).replace(/.*MARK_T9_FROM /, '').trim()
    i = frames.length
    await send(page, `@py from world import living_world; living_world.maw_tick(); print('MARK_T9_TO ' + living_world._maw().location.key + ' | zone=' + str(living_world._maw().location.db.zone))`, 1500)
    const toHit = await waitFor(page, i, 'MARK_T9_TO', 10000)
    if (!toHit) { fail('maw_tick produced no destination print'); return }
    const toLine = clean(toHit.text)
    note('MAW MOVE: from "' + fromRoom + '" → ' + toLine.replace(/.*MARK_T9_TO /, ''))
    if (/mystvale/i.test(toLine.replace(/.*zone=/, ''))) fail('maw zone is Mystvale — forbidden')
    else note('zone is non-Mystvale: OK')
    await send(page, `@tel ${fromRoom}`, 1500)
    i = frames.length
    await send(page, 'look', 1000)
    const corr = await waitFor(page, i, /dragged swath/i, 6000)
    await snap(page, 't9-corruption')
    if (corr) note('corruption line present in vacated room: OK')
    else fail('no corruption line in vacated room "' + fromRoom + '": ' + clean(lastFrames(4)).slice(0, 300))
  })

  // ---- T10 moonstorm ----
  await T('T10-moonstorm', async ({ note, fail }) => {
    await send(page, '@tel The Milersylvania Trailhead', 1500)
    let i = frames.length
    await send(page, `@py from world import living_world; living_world._start_moonstorm(); print('MARK_T10_START')`, 1000)
    await waitFor(page, i, 'MARK_T10_START')
    const storm = await waitFor(page, i, /moonstorm is on the Vale/i, 6000)
    await snap(page, 't10-storm-line')
    if (storm) note('moonstorm broadcast seen: ' + clean(storm.text).slice(0, 250))
    else fail('no moonstorm broadcast in room within 6s')
    i = frames.length
    await send(page, `@py from world import living_world; m = living_world._maw(); print('MARK_T10_BUFF', m.db.master_of_arms, m.db.moonstorm_buffed)`)
    const buff = await waitFor(page, i, 'MARK_T10_BUFF', 8000)
    if (buff && /MARK_T10_BUFF\s*3\s*True/.test(buff.text)) note('maw buffed to 3/True: OK')
    else fail('maw buff state wrong: ' + clean(buff ? buff.text : lastFrames(3)).slice(0, 200))
    // CLEANUP (mandatory)
    i = frames.length
    await send(page, `@py from world import living_world; print('MARK_T10_END', living_world.end_moonstorm())`, 1000)
    const end = await waitFor(page, i, 'MARK_T10_END', 10000)
    note('end_moonstorm → ' + clean(end ? end.text : 'NO ECHO').slice(0, 200))
    i = frames.length
    await send(page, `@py from world import living_world; m = living_world._maw(); print('MARK_T10_VERIFY', m.db.master_of_arms, m.db.moonstorm_buffed)`)
    const ver = await waitFor(page, i, 'MARK_T10_VERIFY', 8000)
    if (ver && /MARK_T10_VERIFY\s*2\s*(False|None)/.test(ver.text)) note('CLEANUP confirmed: maw back to 2/False')
    else fail('CLEANUP verify failed: ' + clean(ver ? ver.text : 'no echo').slice(0, 200))
  })

  // ---- T11 vengeful return ----
  await T('T11-vengeful-return', async ({ note, fail, partial }) => {
    let i = frames.length
    await send(page, `@py from world import living_world; b = living_world._maw(); living_world.on_npc_slain(b, [me]); print('MARK_T11_SLAIN', b.db.slain_by)`)
    const slain = await waitFor(page, i, 'MARK_T11_SLAIN', 8000)
    note('slain_by: ' + clean(slain ? slain.text : 'no echo').slice(0, 200))
    i = frames.length
    await send(page, `@py from world import living_world; living_world.vengeful_return(living_world._maw()); print('MARK_T11_RISE')`, 1000)
    await waitFor(page, i, 'MARK_T11_RISE')
    i = frames.length
    await send(page, `@py from world import living_world; print('MARK_T11_KB', living_world._maw().db.killed_by)`)
    const kb = await waitFor(page, i, 'MARK_T11_KB', 8000)
    if (kb && /Spencer/.test(kb.text)) note('killed_by includes Spencer: OK — ' + clean(kb.text).slice(0, 150))
    else fail('killed_by wrong: ' + clean(kb ? kb.text : 'no echo').slice(0, 200))
    // find maw room + an adjacent room and the exit back in
    i = frames.length
    await send(page, `@py from world import living_world; r = living_world._maw().location; print('MARK_T11_ROOM', r.key, '||', [(e.key, e.destination.key) for e in r.exits])`)
    const roomHit = await waitFor(page, i, 'MARK_T11_ROOM', 8000)
    if (!roomHit) { fail('could not read maw room/exits'); return }
    note('maw room/exits: ' + clean(roomHit.text).slice(0, 400))
    const rm = roomHit.text.match(/MARK_T11_ROOM\s+(.+?)\s*\|\|\s*\[(.*)\]/s)
    if (!rm) { fail('could not parse maw room'); return }
    const mawRoom = rm[1].trim()
    const exitM = rm[2].match(/\('([^']+)',\s*'([^']+)'\)/)
    if (!exitM) { fail('maw room has no exits — cannot walk in'); return }
    const adjRoom = exitM[2]
    // find exit from adjacent room back into maw room
    i = frames.length
    await send(page, `@py from evennia.utils.search import search_object; rs = [r for r in search_object(${JSON.stringify(adjRoom)}) if hasattr(r, 'exits')]; r = rs[0]; back = [e.key for e in r.exits if e.destination and e.destination.key == ${JSON.stringify(mawRoom)}]; print('MARK_T11_BACK', back)`)
    const backHit = await waitFor(page, i, 'MARK_T11_BACK', 8000)
    const backM = backHit && backHit.text.match(/MARK_T11_BACK\s+\['([^']+)'/)
    if (!backM) { fail('no return exit from ' + adjRoom + ' into ' + mawRoom); return }
    await send(page, `@tel ${adjRoom}`, 1500)
    i = frames.length
    await send(page, backM[1], 1500)
    const greet = await waitFor(page, i, /remember the iron/i, 10000)
    await snap(page, 't11-greeting')
    if (greet) note('GREETING: ' + clean(greet.text).slice(0, 400))
    else fail('no vengeful greeting on entering maw room. Got: ' + clean(lastFrames(6)).slice(0, 400))
    // bail if combat engaged
    const combat = findSince(i, /combat|attacks you|strikes at you/i)
    if (combat) {
      note('combat may have engaged — disengaging: ' + clean(combat.text).slice(0, 150))
      await send(page, 'disengage', 1200)
    }
    await send(page, '@tel Mystvale Square', 1200)
    i = frames.length
    await send(page, `@py print('MARK_T11_REP', (me.db.npc_rep or {}).get('the withering maw'))`)
    const rep = await waitFor(page, i, 'MARK_T11_REP', 8000)
    if (rep && /returned from the death you gave them/i.test(rep.text)) note('npc_rep memory OK: ' + clean(rep.text).slice(0, 300))
    else if (rep) fail('npc_rep memory missing expected text: ' + clean(rep.text).slice(0, 300))
    else fail('no npc_rep echo')
    // CLEANUP
    i = frames.length
    await send(page, `@py from world import living_world; m = living_world._maw(); m.db.killed_by = None; m.db.slain_by = None; m.db.vengeful_return_pending = None; m.attributes.add('ai_knowledge', ''); print('MARK_T11_C1')`)
    await waitFor(page, i, 'MARK_T11_C1')
    i = frames.length
    await send(page, `@py from world import living_world; [s.stop() for s in living_world._maw().scripts.all() if s.key == 'vengeful_return']; print('MARK_T11_C2')`)
    const c2 = await waitFor(page, i, 'MARK_T11_C2')
    note(c2 ? 'CLEANUP maw state + scripts: confirmed' : 'CLEANUP T11: NO ECHO — verify manually')
  })

  // ---- T12 siege ----
  await T('T12-siege', async ({ note, fail }) => {
    let i = frames.length
    await send(page, '@siege held', 1200)
    const res = await waitFor(page, i, /Siege resolved/i, 8000)
    if (res) note('siege resolve: ' + clean(res.text).slice(0, 300))
    else fail('no "Siege resolved" line: ' + clean(lastFrames(4)).slice(0, 250))
    await send(page, '@tel Mystvale North Gate', 1500)
    i = frames.length
    await send(page, 'look', 1000)
    const scar = await waitFor(page, i, /gouge|fresh graves|gatepost/i, 6000)
    await snap(page, 't12-siege-scar')
    if (scar) note('SCAR: ' + clean(scar.text).slice(0, 500))
    else fail('no siege scar paragraph in gate look')
    // CLEANUP (mandatory)
    i = frames.length
    await send(page, '@siege clear', 1200)
    const cleared = await waitFor(page, i, /Siege state cleared/i, 8000)
    note(cleared ? 'CLEANUP @siege clear: confirmed' : 'CLEANUP @siege clear: LINE NOT SEEN')
    i = frames.length
    await send(page, 'look', 1000)
    await page.waitForTimeout(800)
    const still = findSince(i, /gouge|fresh graves cut into the gatepost/i)
    if (still) fail('scar text still present after @siege clear')
    else note('scar gone after clear: OK')
  })

  // ---- FINAL CLEANUP ----
  await T('FINAL-cleanup', async ({ note, fail }) => {
    let i = frames.length
    await send(page, `@py me.db.npc_rep = me.db.lw_backup['npc_rep']; me.db.espionage = me.db.lw_backup['esp']; me.db.lw_backup = None; print('MARK_FINAL_RESTORE')`)
    const r1 = await waitFor(page, i, 'MARK_FINAL_RESTORE', 8000)
    if (!r1) fail('restore @py no echo: ' + clean(lastFrames(3)).slice(0, 250))
    else note('npc_rep/espionage restored, backup cleared')
    i = frames.length
    await send(page, `@py me.db.fortune_last_pull = None; me.db.pry_last = None; print('MARK_FINAL_FLAGS')`)
    const r2 = await waitFor(page, i, 'MARK_FINAL_FLAGS', 8000)
    note(r2 ? 'fortune/pry cooldowns cleared' : 'WARN: flags clear no echo')
    await send(page, '@tel Mystvale Square', 1500)
    note('returned to Mystvale Square')
  })

  await browser.close()

  // ---- report ----
  log('\n\n========== VERDICTS ==========')
  for (const r of results) log(`${r.verdict.padEnd(8)} ${r.test}`)
  log('\n========== CONSOLE ERRORS ==========')
  if (!consoleErrors.length) log('(none)')
  else consoleErrors.slice(0, 40).forEach((e) => log('  ' + e))
  log('\n========== SCREENSHOTS ==========')
  shots.forEach((s) => log('  ' + s))
  process.exit(results.some((r) => r.verdict === 'FAIL') ? 1 : 0)
}

main().catch((e) => { console.error('FATAL', e); process.exit(2) })
