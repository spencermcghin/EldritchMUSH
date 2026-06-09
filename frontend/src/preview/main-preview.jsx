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

// ?panel=1 shows the NPC dialogue modal (it backdrops everything else)
const SHOW_PANEL = new URLSearchParams(window.location.search).has('panel')

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
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(<Preview />)
