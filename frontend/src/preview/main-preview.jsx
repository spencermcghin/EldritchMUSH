// Style-preview harness — mounts the core game surfaces with fixture
// data so styling passes can be screenshotted without auth or a live
// server. Served at /preview.html in `vite dev`; not linked from the
// app and excluded from the production build entry.
import React from 'react'
import ReactDOM from 'react-dom/client'
import '../App.css'
import RoomView from '../components/RoomView.jsx'
import GameOutput from '../components/GameOutput.jsx'
import NpcDialoguePanel from '../components/NpcDialoguePanel.jsx'
import QuestOfferModal from '../components/QuestOfferModal.jsx'
import QuestCompletedToast from '../components/QuestCompletedToast.jsx'
import CombatEncounterPanel from '../components/CombatEncounterPanel.jsx'
import CombatEncounterHost from '../components/CombatEncounterHost.jsx'
import { ANTAGONISTS } from '../data/antagonists'

const ROOM_MSG = {
  content: [
    'Stag Hall Courtyard',
    'A flagstone courtyard open to grey Annwyn sky. A ring-fountain ' +
      'stands at its center, water trickling from antlered spouts into a ' +
      'moss-ringed basin. Training dummies line the north wall where the ' +
      'Laurent household guard drill daily. The Great Hall’s double ' +
      'doors stand at the eastern side; east lets onto the Great Hall.',
    'Exits: The Great Hall <east>, Stag Hall Courtyard Gate <south>',
    'Characters: Ser Ewan Bannon, Drill Sergeant Maela',
    'Items: a training sword rack, one Laurent strongbox',
  ].join('\n'),
  type: 'game',
}

const LOG_MESSAGES = [
  { content: '&gt; ask bannon about the crows', type: 'system' },
  {
    content:
      'Ser Ewan Bannon turns from the fountain, rainwater beading on his ' +
      'pauldron. “The Crows hold three camps in the forest,” he ' +
      'says, voice low. “The blacksmith first — Torben is no ' +
      'fighter, and they know what he is worth.”',
    type: 'game',
  },
  {
    content: '*He traces a line on the map, tapping the Fox Den.*',
    type: 'game',
  },
  { content: 'Your strike lands true — the Crow Striker staggers!', type: 'combat' },
  { content: 'Quest objective: Clear the Fox Den (3/5)', type: 'game' },
]

const DIALOGUE = {
  ts: 1,
  npc: 'Ser Ewan Bannon',
  npcDesc:
    'A broad-shouldered knight of House Bannon, surcoat patched at the shoulder, eyes that have counted losses.',
  question: 'ask bannon about the crows',
  reply:
    'Ser Ewan Bannon studies you for a long moment, then nods toward the ' +
    'gate. “If you mean to ride for the Fox Den, take the south road ' +
    'past the Mistgate — and keep your blade loose. The Crows post a ' +
    'striker in the treeline.”',
  topics: ['the rescue', 'the Fox Den', 'House Bannon'],
  channel: 'ask',
}

function Swatch({ name, varName, text }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <span
        style={{
          width: 28,
          height: 28,
          background: `var(${varName})`,
          border: '1px solid var(--border-bright)',
          display: 'inline-block',
        }}
      />
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-aged)' }}>
        {name}
      </span>
      {text && (
        <span style={{ color: `var(${varName})`, fontFamily: 'var(--font-body)', fontSize: 15 }}>
          {text}
        </span>
      )}
    </div>
  )
}

const OFFER = {
  key: 'rescue_blacksmith',
  title: 'Rescue the Crafters: The Blacksmith',
  giver: 'Ser Ewan Bannon',
  description:
    'Crow bandits have kidnapped Mystvale’s blacksmith and are holding ' +
    'him at a camp in the forest. Ser Ewan Bannon is looking for ' +
    'volunteers to raid the camp and bring the smith home — by blade, ' +
    'by parley, or by ransom.',
  // linear offer → shows the wax-seal ACCEPT button; add ?branching=1
  // for the outcome-picker variant.
  objectives: [
    { desc: 'Defeat the Crow Striker', qty: 1 },
    { desc: 'Walk Torben home to the Crafter’s Quarter', qty: 1 },
  ],
  rewards: ['25 silver', 'crow signal whistle'],
}

const COMPLETED_QUEST = {
  ts: 1,
  title: 'The Festival of Lights',
  outcomeLabel: 'Every lantern lit',
  silver: 20,
  items: ['paper lantern'],
  reagents: { Sayge: 2 },
  factionRep: { crown: 2 },
  npcRep: { 'curate godrick': 1 },
}

// ── Bestiary combat fixtures ──
// Per-monster encounter payloads keyed by art_key, mirroring what the
// server's combat_encounter_prompt OOB event carries (name/desc/artKey/
// isBoss/tier). The label/source come straight from the antagonists.js
// registry so the preview can't drift from the real art mapping.
// T3+ monsters render with the gold boss frame.
const MOB_STATS = {
  werewolf_alpha: { hp: 30, maxHp: 30, status: 'rampaging', boss: true },
  werewolf:       { hp: 18, maxHp: 18 },
  wight:          { hp: 22, maxHp: 22, status: 'dextrous' },
  revenant:       { hp: 28, maxHp: 28, boss: true },
  risen_dead:     { hp: 12, maxHp: 12, status: 'lumbering' },
  unhallowed_spawn:{ hp: 16, maxHp: 16 },
  nethermancer:   { hp: 20, maxHp: 20, status: 'warded', boss: true },
  necromancer:    { hp: 24, maxHp: 24, status: 'warded', boss: true },
  netherphage:    { hp: 30, maxHp: 30, status: 'immune', boss: true },
}

function mobEncounter(artKey) {
  const reg = ANTAGONISTS[artKey]
  const s = MOB_STATS[artKey] || { hp: 20, maxHp: 20 }
  return {
    name: reg ? reg.label : artKey,
    desc: reg ? `Bestiary plate: ${reg.source}` : '',
    artKey,
    isBoss: !!s.boss,
    hp: s.hp,
    maxHp: s.maxHp,
    status: s.status,
    myTurn: true,
    turnOrder: [
      { name: 'You', hp: 14, maxHp: 14, isMe: true },
      { name: reg ? reg.label : artKey, hp: s.hp, maxHp: s.maxHp, isAntagonist: true },
    ],
  }
}

// Live-combat fixture: a mock useEvennia oobState mid-fight, fed through
// the real CombatEncounterHost so the preview exercises the actual
// prompt→live mapping (foe identity, per-combatant HP rail, myTurn gating,
// SLAIN). combatantHp is a 0..100 percentage, matching the OOB reducer.
const LIVE_COMBAT_STATE = {
  inCombat: true,
  characterName: 'Aldric',
  myTurn: true,
  combatTurnOrder: ['Aldric', 'Wight', 'Risen Dead'],
  combatantHp: { Aldric: 80, Wight: 45, 'Risen Dead': 70 },
  // The walk-in prompt that PRECEDED this fight — the host remembers it
  // to enrich the bare turn-order names with portrait art + boss flag.
  combatEncounter: {
    room: 'Raven’s Rest Graveyard',
    ts: 1,
    hostiles: [
      {
        name: 'Wight',
        desc: 'Bestiary plate: ' + (ANTAGONISTS.wight ? ANTAGONISTS.wight.source : ''),
        artKey: 'wight',
        isBoss: false,
        tier: 2,
      },
      {
        name: 'Risen Dead',
        desc: 'A shambling corpse.',
        artKey: 'risen_dead',
        isBoss: false,
        tier: 1,
      },
    ],
  },
}

// ?panel=1 — NPC dialogue modal; ?offer=1 — quest offer modal (wax
// seal accept); ?toast=1 — completed toast. Modals backdrop the page.
// ?combat=1&mob=<art_key> — the static graphical combat encounter panel
//   facing one of the 9 bestiary monsters (default: wight).
// ?combat=live — the SUSTAINED live face-off driven through the real
//   CombatEncounterHost from a mid-fight mock oobState.
const Q = new URLSearchParams(window.location.search)
const SHOW_PANEL = Q.has('panel')
const SHOW_OFFER = Q.has('offer')
const SHOW_TOAST = Q.has('toast')
const COMBAT_MODE = Q.get('combat')
const SHOW_COMBAT = Q.has('combat') && COMBAT_MODE !== 'live'
const SHOW_LIVE_COMBAT = COMBAT_MODE === 'live'
const MOB = Q.get('mob') || 'wight'

function Preview() {
  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--void)', overflow: 'auto' }}>
      <div style={{ padding: '10px 18px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 22, flexWrap: 'wrap' }}>
        <Swatch name="--bone" varName="--bone" text="prose" />
        <Swatch name="--mist" varName="--mist" text="the living" />
        <Swatch name="--accent-gold" varName="--accent-gold" text="action" />
        <Swatch name="--blood-bright" varName="--blood-bright" text="danger" />
        <Swatch name="--text-aged" varName="--text-aged" text="chrome" />
      </div>
      <div style={{ flex: '0 0 560px', display: 'flex', flexDirection: 'column', position: 'relative' }}>
        <RoomView messages={[ROOM_MSG]} onCommand={() => {}} onEntityClick={() => {}} />
        <GameOutput messages={LOG_MESSAGES} inCombat={false} onCommand={() => {}} />
      </div>
      {SHOW_PANEL && (
        <NpcDialoguePanel
          dialogue={DIALOGUE}
          pendingDialogue={null}
          sendCommand={() => {}}
          questOffers={[]}
          onAcceptOffer={() => {}}
          onAcceptOfferOutcome={() => {}}
          onDeclineOffer={() => {}}
        />
      )}
      {SHOW_OFFER && (
        <QuestOfferModal
          open
          offer={OFFER}
          onAccept={() => {}}
          onAcceptOutcome={() => {}}
          onDecline={() => {}}
          onClose={() => {}}
        />
      )}
      {SHOW_TOAST && <QuestCompletedToast quest={COMPLETED_QUEST} />}
      {SHOW_COMBAT && (
        <CombatEncounterPanel
          encounter={mobEncounter(MOB)}
          actions={[
            { key: 'strike', label: 'Strike', danger: true },
            { key: 'cleave', label: 'Cleave', danger: true },
            { key: 'disarm', label: 'Disarm' },
          ]}
          onAction={() => {}}
          onFlee={() => {}}
          onTargetOther={() => {}}
        />
      )}
      {SHOW_LIVE_COMBAT && (
        <CombatEncounterHost
          oobState={LIVE_COMBAT_STATE}
          onCommand={() => {}}
          onHold={() => {}}
        />
      )}
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(<Preview />)
