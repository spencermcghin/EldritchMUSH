import { useRef, useState, useCallback, useEffect } from 'react'
import { useEvennia } from './hooks/useEvennia'
import LoginScreen from './components/LoginScreen'
import LandingPage from './components/LandingPage'
import CharacterSelect from './components/CharacterSelect'
import IntroScreen from './components/IntroScreen'
import CombatTracker from './components/CombatTracker'
import ActionToolbar from './components/ActionToolbar'
import CommandSidebar from './components/CommandSidebar'
import CharacterStatus from './components/CharacterStatus'
import DetailPanel from './components/DetailPanel'
import ContextMenu from './components/ContextMenu'
import CommandInput from './components/CommandInput'
import GameOutput from './components/GameOutput'
import ChargenWizard from './components/ChargenWizard'
import RoomView from './components/RoomView'
import WorldMapModal from './components/WorldMapModal'
import EquipModal from './components/EquipModal'
import CharSheetModal from './components/CharSheetModal'
import AdminPanel from './components/AdminPanel'
import ShopModal from './components/ShopModal'
import TavylModal from './components/TavylModal'
import PrimerModal from './components/PrimerModal'
import QuestOfferModal from './components/QuestOfferModal'
import CraftingModal from './components/CraftingModal'
import QuestJournalModal from './components/QuestJournalModal'
import ReputationModal from './components/ReputationModal'
import ItemPickerModal from './components/ItemPickerModal'
import NpcPickerModal from './components/NpcPickerModal'
import AudioController from './components/AudioController'
import AudioToggle from './components/AudioToggle'
import ItemReceivedToast from './components/ItemReceivedToast'
import QuestAcceptedToast from './components/QuestAcceptedToast'
import QuestCompletedToast from './components/QuestCompletedToast'
import QuestProgressToast from './components/QuestProgressToast'
import RepChangeToast from './components/RepChangeToast'
import CombatEncounterHost from './components/CombatEncounterHost'
import SealAltarModal from './components/SealAltarModal'
import NpcDialoguePanel from './components/NpcDialoguePanel'
import CommandPrompt from './components/CommandPrompt'
import { PROMPTS, getPromptForCommand } from './data/commandPrompts'
import './App.css'

const NPC_CONTEXT_ITEMS = (name) => [
  { label: 'Look', icon: '👁', action: `look ${name}` },
  { label: 'Attack', icon: '⚔', action: `strike ${name}` },
  { label: 'Whisper', icon: '💬', action: 'whisper', kind: 'prompt', target: name },
  { label: 'Follow', icon: '🚶', action: `follow ${name}` },
]

const ITEM_CONTEXT_ITEMS = (name) => [
  { label: 'Look', icon: '👁', action: `look ${name}` },
  { label: 'Get', icon: '✋', action: `get ${name}` },
  { label: 'Drop', icon: '↓', action: `drop ${name}` },
  { label: 'Examine', icon: '🔍', action: `examine ${name}` },
]

const EXIT_CONTEXT_ITEMS = (dir) => [
  { label: `Go ${dir}`, icon: '🚪', action: dir },
]

function App() {
  const { connectionState, messages, oobState, latency, sendCommand: rawSendCommand, connect, disconnect, exitChargen, enterChargen, clearLastCharCreate, showCharacterSelect, dismissQuestOffer } =
    useEvennia()

  // Pending-dialogue state — declared early so sendCommand below
  // can call setPendingDialogue. Pops the NpcDialoguePanel modal
  // with a "considers your words" placeholder the moment the player
  // issues an `ask <npc>` command, so the click feels responsive even
  // before the AI reply arrives.
  const [pendingDialogue, setPendingDialogue] = useState(null)

  // Wrap sendCommand to detect `ask <npc>` syntax and pop the
  // NpcDialoguePanel modal with a placeholder immediately. The real
  // reply replaces it when the AI returns. All consumers go through
  // this wrapper.
  const sendCommand = useCallback((text) => {
    const trimmed = (text || '').trim()
    const askMatch = trimmed.match(/^ask\s+(.+?)\s*=\s*(.+)$/i)
      || trimmed.match(/^ask\s+(\S+)\s+(.+)$/i)
    if (askMatch) {
      setPendingDialogue({
        npc: askMatch[1].trim(),
        question: askMatch[2].trim(),
        channel: 'ask',
        ts: Date.now(),
      })
    }
    rawSendCommand(trimmed)
  }, [rawSendCommand])

  // ── Landing page gate ──
  // "/" shows the marketing landing page to logged-out visitors; the
  // login UI lives behind "/play" (or one click on PLAY NOW). Existing
  // authenticated sessions bypass this entirely — the auto-connect
  // effect below flips connectionState to 'connecting' and the landing
  // unmounts. No server routing changed, so OAuth redirect URIs and
  // old bookmarks keep working.
  const [gateEntered, setGateEntered] = useState(
    () => window.location.pathname.startsWith('/play')
  )
  const enterGate = useCallback(() => {
    if (!window.location.pathname.startsWith('/play')) {
      window.history.pushState({}, '', '/play')
    }
    setGateEntered(true)
  }, [])
  useEffect(() => {
    const onPop = () => setGateEntered(window.location.pathname.startsWith('/play'))
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  const inputRef = useRef(null)
  // Imperative ref into AudioController so AudioToggle in the header
  // can drive playback without prop-drilling through the whole tree.
  const audioRef = useRef(null)

  // ── Séance mode ──
  // When a ghost NPC (backend flags isGhost on the npc_dialogue
  // event) speaks, the whole UI shifts into a supernatural state
  // (`seance-active` on the app root). Each ghost line resets a 20s
  // timer; it also ends when the dialogue panel for the ghost closes.
  const [seanceActive, setSeanceActive] = useState(false)
  const seanceTimerRef = useRef(null)
  const endSeance = useCallback(() => {
    if (seanceTimerRef.current) clearTimeout(seanceTimerRef.current)
    seanceTimerRef.current = null
    setSeanceActive(false)
  }, [])
  useEffect(() => {
    const d = oobState.npcDialogue
    if (!d || !d.ts || !d.isGhost) return
    setSeanceActive(true)
    if (seanceTimerRef.current) clearTimeout(seanceTimerRef.current)
    seanceTimerRef.current = setTimeout(() => setSeanceActive(false), 20000)
  }, [oobState.npcDialogue?.ts])
  useEffect(() => () => {
    if (seanceTimerRef.current) clearTimeout(seanceTimerRef.current)
  }, [])


  // Auto-connect after OAuth redirect: when the page loads, ask the
  // backend whether we already have a Django session. If so, skip the
  // LoginScreen entirely and open the WebSocket — Evennia will see the
  // csessid and auto-puppet the player's character.
  const autoConnectAttemptedRef = useRef(false)
  useEffect(() => {
    if (autoConnectAttemptedRef.current) return
    // The landing page is the front door: never auto-connect (and so
    // skip the landing) until the visitor has actually entered the
    // gate at /play. Without this, anyone with a lingering session is
    // bounced straight past the marketing page into character select.
    if (!gateEntered) return
    if (connectionState !== 'disconnected') return
    autoConnectAttemptedRef.current = true
    fetch('/api/webclient_session/', { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data && data.authenticated) {
          const host = import.meta.env.VITE_GAME_HOST || window.location.hostname || 'localhost'
          const port = parseInt(
            import.meta.env.VITE_GAME_PORT ||
              window.location.port ||
              (window.location.protocol === 'https:' ? '443' : '80')
          )
          connect(host, port)
        }
      })
      .catch(() => { /* endpoint not deployed yet — show LoginScreen */ })
  }, [connectionState, connect, gateEntered])

  // Entity detail panel state
  const [selectedEntity, setSelectedEntity] = useState(null)
  // selectedEntity: { name: string, type: 'character'|'item'|'player' } or null

  // Context menu state
  const [contextMenu, setContextMenu] = useState(null)
  // contextMenu: { x: number, y: number, items: array } or null

  // Entity description captured from look commands
  const [entityDescription, setEntityDescription] = useState('')
  // Index where we last sent a look command — used to capture the next response
  const lookWatcherRef = useRef(null)
  // lookWatcherRef.current: { entityName: string, fromIndex: number } or null

  // World map modal
  const [worldMapOpen, setWorldMapOpen] = useState(false)

  // Equip modal
  const [equipOpen, setEquipOpen] = useState(false)
  // Character sheet modal
  const [charSheetOpen, setCharSheetOpen] = useState(false)
  // Admin panel
  const [adminOpen, setAdminOpen] = useState(false)
  // Shop modal
  const [shopOpen, setShopOpen] = useState(false)
  const [tavylOpen, setTavylOpen] = useState(false)
  const [primerOpen, setPrimerOpen] = useState(false)
  const [craftingOpen, setCraftingOpen] = useState(false)
  const [questJournalOpen, setQuestJournalOpen] = useState(false)
  const [reputationOpen, setReputationOpen] = useState(false)
  // Generic item picker (for Give-to-NPC flow). When set, ItemPickerModal
  // opens; clicking an item runs onPick(item) and closes the picker.
  const [itemPicker, setItemPicker] = useState(null)
  // itemPicker: { title, subtitle, onPick: (item) => void } or null

  // NPC picker — pops a list of NPCs in the current room. Used by the
  // EquipModal "Give" flow: pick item first, then pick recipient.
  const [npcPicker, setNpcPicker] = useState(null)
  // npcPicker: { title, subtitle, onPick: (npcName) => void } or null
  // Auto-open the Tavyl modal whenever a fresh tavyl_state event arrives.
  const lastTavylTsRef = useRef(0)
  useEffect(() => {
    const ts = oobState.tavylState?.ts
    if (ts && ts !== lastTavylTsRef.current) {
      lastTavylTsRef.current = ts
      setTavylOpen(true)
    }
  }, [oobState.tavylState])
  // Auto-open the Primer modal whenever a fresh primer_data event arrives.
  const lastPrimerTsRef = useRef(0)
  useEffect(() => {
    const ts = oobState.primerData?.ts
    if (ts && ts !== lastPrimerTsRef.current) {
      lastPrimerTsRef.current = ts
      setPrimerOpen(true)
    }
  }, [oobState.primerData])
  // Auto-open the Equip/Inventory modal when the player types `inv`.
  const lastInventoryOpenTsRef = useRef(0)
  useEffect(() => {
    const ts = oobState.inventoryOpen?.ts
    if (ts && ts !== lastInventoryOpenTsRef.current) {
      lastInventoryOpenTsRef.current = ts
      setEquipOpen(true)
    }
  }, [oobState.inventoryOpen])

  // Auto-open the Crafting modal when crafting_data arrives.
  const lastCraftingTsRef = useRef(0)
  useEffect(() => {
    const ts = oobState.craftingData?.ts
    if (ts && ts !== lastCraftingTsRef.current) {
      lastCraftingTsRef.current = ts
      setCraftingOpen(true)
    }
  }, [oobState.craftingData])

  // Auto-open Quest Journal / Reputation when the player types
  // `quest` / `rep` in chat. Matches the inventoryOpen pattern.
  const lastQuestOpenTsRef = useRef(0)
  useEffect(() => {
    const ts = oobState.questJournalOpen?.ts
    if (ts && ts !== lastQuestOpenTsRef.current) {
      lastQuestOpenTsRef.current = ts
      setQuestJournalOpen(true)
    }
  }, [oobState.questJournalOpen])
  const lastRepOpenTsRef = useRef(0)
  useEffect(() => {
    const ts = oobState.reputationOpen?.ts
    if (ts && ts !== lastRepOpenTsRef.current) {
      lastRepOpenTsRef.current = ts
      setReputationOpen(true)
    }
  }, [oobState.reputationOpen])

  // Fire __room_meta__ on initial puppet & any character change so the
  // contextual buttons and topic chips populate without requiring the
  // player to first walk between rooms.
  const lastCharNameRef = useRef('')
  useEffect(() => {
    if (connectionState !== 'connected') return
    const charName = oobState.characterName
    if (charName && charName !== lastCharNameRef.current) {
      lastCharNameRef.current = charName
      // Short delay so the character's location is stable on the server.
      setTimeout(() => sendCommand('__room_meta__'), 300)
      // Also pull the room graph once so the minimap has data on login
      // (room_meta keeps the live position fresh after this).
      setTimeout(() => sendCommand('__map_ui__'), 500)
    }
  }, [oobState.characterName, connectionState, sendCommand])

  // Friendly command-input prompt modal
  const [commandPrompt, setCommandPrompt] = useState(null)
  // commandPrompt: { title, label, placeholder, icon, submitLabel, buildCommand } or null

  const openPrompt = useCallback((promptDef) => {
    setCommandPrompt(promptDef)
  }, [])

  const closePrompt = useCallback(() => {
    setCommandPrompt(null)
  }, [])

  const handlePromptSubmit = useCallback((finalCommand) => {
    sendCommand(finalCommand)
    setCommandPrompt(null)
  }, [sendCommand])

  const injectCommand = (text) => {
    if (inputRef.current) {
      inputRef.current.setValue(text)
      inputRef.current.focus()
    }
  }

  const lookTimeoutRef = useRef(null)

  const handleEntityClick = useCallback((name, type) => {
    setSelectedEntity({ name, type })
    setEntityDescription('')
    // Refresh per-room NPC metadata whenever an NPC is clicked — cheap
    // insurance that contextual buttons and topic chips populate even
    // if the room-change detector missed the last transition.
    if (type === 'npc' || type === 'character') {
      sendCommand('__room_meta__')
    }
    // Mark the current message index — anything new after this is the look response.
    // +1 to skip the echo message that sendCommand adds synchronously.
    lookWatcherRef.current = { entityName: name, fromIndex: messages.length + 1 }
    sendCommand(`look ${name}`)
    // After 1.5s, stop accumulating — clear the watcher so the effect
    // stops re-running. If nothing was captured, show a fallback.
    if (lookTimeoutRef.current) clearTimeout(lookTimeoutRef.current)
    lookTimeoutRef.current = setTimeout(() => {
      if (lookWatcherRef.current) {
        lookWatcherRef.current = null
        setEntityDescription((prev) => prev || 'No description available.')
      }
    }, 1500)
  }, [sendCommand, messages.length])

  // Watch for the entity look response and capture it as description.
  // Evennia sends the look response as MULTIPLE separate text messages
  // (name, description, level, value, durability — each as its own
  // frame). We accumulate all non-system messages that arrive after
  // the look command until the 2-second timeout fires, then combine
  // them into a single description string.
  useEffect(() => {
    const watcher = lookWatcherRef.current
    if (!watcher) return
    if (messages.length <= watcher.fromIndex) return

    const parts = []
    const namePattern = watcher.entityName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

    for (let i = watcher.fromIndex; i < messages.length; i++) {
      const msg = messages[i]
      if (!msg || msg.type === 'system') continue
      const raw = (msg.content || '').replace(/<[^>]*>/g, '').trim()
      if (!raw) continue

      let cleaned = raw
        // Strip "EntityName(#id)" prefix
        .replace(new RegExp(`^${namePattern}(-\\d+)?\\s*\\(#\\d+\\)\\s*`, 'i'), '')
        .replace(/^[A-Za-z][^\n]{0,40}\(#\d+\)\s*/, '')
      // Strip entity name without (#id)
      cleaned = cleaned.replace(new RegExp(`^${namePattern}(-\\d+)?\\s*`, 'i'), '')
      // Fix concatenated text joins
      cleaned = cleaned
        .replace(/([a-z])([A-Z])/g, '$1\n$2')
        .replace(/(\.)([A-Z])/g, '$1\n$2')
        .replace(/(\d)([A-Z])/g, '$1\n$2')
      cleaned = cleaned.trim()
      if (cleaned) parts.push(cleaned)
    }

    if (parts.length > 0) {
      setEntityDescription(parts.join('\n'))
    }
  }, [messages])

  const handleEntityContextMenu = useCallback((e, name, type) => {
    e.preventDefault()
    let items
    if (type === 'character' || type === 'npc' || type === 'player') {
      items = NPC_CONTEXT_ITEMS(name)
    } else {
      items = ITEM_CONTEXT_ITEMS(name)
    }
    setContextMenu({ x: e.clientX, y: e.clientY, items })
  }, [])

  const handleExitContextMenu = useCallback((e, dir) => {
    e.preventDefault()
    setContextMenu({ x: e.clientX, y: e.clientY, items: EXIT_CONTEXT_ITEMS(dir) })
  }, [])

  const handleContextMenuSelect = useCallback((action, kind, item) => {
    if (kind === 'prompt') {
      // Look up the friendly prompt definition; for whisper/tell we need
      // a target-aware prompt factory.
      const promptKey = action
      let promptDef = null
      if (typeof PROMPTS[promptKey] === 'function' && item?.target) {
        promptDef = PROMPTS[promptKey](item.target)
      } else if (typeof PROMPTS[promptKey] === 'object') {
        promptDef = PROMPTS[promptKey]
      }
      if (promptDef) {
        setCommandPrompt(promptDef)
        return
      }
    }
    if (kind === 'inject') {
      injectCommand(action)
    } else {
      sendCommand(action)
    }
  }, [sendCommand])

  const handleContextMenuClose = useCallback(() => {
    setContextMenu(null)
  }, [])

  // EquipModal give flow: item is already chosen, ask for the recipient.
  // We open the NpcPickerModal scoped to the current room. Selecting
  // an NPC fires `give <item> = <npc>` and re-fetches inventory so the
  // EquipModal updates without needing to be reopened.
  const handleGiveFromEquipModal = useCallback((item) => {
    setNpcPicker({
      title: `GIVE ${item.name.toUpperCase()} TO...`,
      subtitle: 'Pick a recipient in this room.',
      onPick: (npcName) => {
        sendCommand(`give ${item.name} = ${npcName}`)
        setNpcPicker(null)
        setTimeout(() => sendCommand('__equip_ui__'), 600)
      },
    })
  }, [sendCommand])

  // Give flow: open ItemPicker with the NPC name baked into the title.
  // Selecting an item fires `give <item> = <npc>`. The server's existing
  // CmdGive routes through quest_deliver + npc_rep_on_gift hooks, so
  // quest progress and rep all kick in automatically.
  const handleGiveToNpc = useCallback((npcName) => {
    setItemPicker({
      title: `GIVE TO ${npcName.toUpperCase()}`,
      subtitle: 'Pick an item from your pack to hand over.',
      onPick: (item) => {
        sendCommand(`give ${item.name} = ${npcName}`)
        setItemPicker(null)
      },
    })
  }, [sendCommand])

  // When a walk-in is accepted, the four other walk-in offers stop
  // being valid (your origin is your origin). Strip every queued
  // walk-in offer alongside the one we just accepted so we don't pop
  // a Cirque modal right after the player picked Ship.
  const dismissOnAccept = useCallback((offer) => {
    if (offer.key && offer.key.startsWith('walkin_')) {
      ;(oobState.questOffers || [])
        .filter(o => o.key && o.key.startsWith('walkin_'))
        .forEach(o => dismissQuestOffer(o.key))
    } else {
      dismissQuestOffer(offer.key)
    }
  }, [oobState.questOffers, dismissQuestOffer])

  const handleDetailPanelClose = useCallback(() => {
    setSelectedEntity(null)
    setEntityDescription('')
    lookWatcherRef.current = null
  }, [])

  // Auto-close DetailPanel when the player moves to a new room.
  // Detect by watching for new messages containing "Exits:" which
  // indicates a room description (from movement or `look`). Only
  // close if the panel is open and the message wasn't triggered by
  // our own look-watcher (which also produces room-like output).
  const prevMsgCountRef = useRef(messages.length)
  useEffect(() => {
    if (!selectedEntity) return
    if (messages.length <= prevMsgCountRef.current) {
      prevMsgCountRef.current = messages.length
      return
    }
    // Check new messages for room description markers
    let sawRoomChange = false
    for (let i = prevMsgCountRef.current; i < messages.length; i++) {
      const msg = messages[i]
      if (!msg || msg.type === 'system') continue
      const raw = (msg.content || '').replace(/<[^>]*>/g, '')
      if (/Exits?:/i.test(raw) && !lookWatcherRef.current) {
        // New room — close the detail panel and refresh NPC metadata
        // (so contextual buttons like Play Tavyl / Browse appear for
        // dealers / merchants in the new room).
        setSelectedEntity(null)
        setEntityDescription('')
        sawRoomChange = true
        break
      }
    }
    if (sawRoomChange) {
      // Slight delay to let the server finalize move state.
      setTimeout(() => sendCommand('__room_meta__'), 100)
    }
    prevMsgCountRef.current = messages.length
  }, [messages, selectedEntity, sendCommand])

  const isConnected = connectionState === 'connected'
  const isConnecting = connectionState === 'connecting'

  const statusLabel = { connected: 'CONNECTED', connecting: 'CONNECTING', disconnected: 'OFFLINE' }[connectionState]

  // "Title screen" = pre-puppet. The Forsaken Gate loops here; once
  // the player ic's into a character, the in-game playlist takes over.
  const atTitleScreen =
    !isConnected ||
    oobState.atCharacterSelect ||
    oobState.inChargen ||
    !oobState.characterName

  return (
    <div className={`app-container${seanceActive ? ' seance-active' : ''}`}>

      {/* Séance vignette — mist closing in from the edges while a
          ghost speaks. Always mounted so opacity can transition. */}
      <div className="seance-vignette" aria-hidden="true" />
      {oobState.damageFlash && (
        <div
          key={oobState.damageFlash.ts}
          className={`damage-flash${oobState.damageFlash.absorbed ? ' absorbed' : ''}`}
          aria-hidden="true"
        />
      )}

      {/* Background music — single global <audio>, controlled by the
          header toggle via audioRef. Mounted at the app level so a
          full re-render doesn't restart the track. */}
      <AudioController ref={audioRef} atTitleScreen={atTitleScreen} />

      {/* ── Landing page ── */}
      {/* Marketing one-pager for logged-out visitors at "/". The game
          header is suppressed while it shows; PLAY pushes /play and
          reveals the LoginScreen. */}
      {!isConnected && !isConnecting && !gateEntered && (
        <LandingPage onPlay={enterGate} />
      )}

      {/* ── Header ── */}
      <header className="app-header">
        <div className="app-header-title">
          <img src="/art/eldritch-logo.png" alt="Eldritch" className="app-header-logo" />
        </div>
        <div className="app-header-rule" />
        <div className="app-header-status">
          <div className={`status-dot ${connectionState}`} />
          <span className={`status-label ${connectionState}`}>{statusLabel}</span>
          {latency !== null && isConnected && (
            <span className="status-latency">{latency}ms</span>
          )}
          <AudioToggle audioRef={audioRef} atTitleScreen={atTitleScreen} />
          {isConnected && (
            <button className="header-disconnect-btn" onClick={disconnect} title="Disconnect">✕</button>
          )}
        </div>
      </header>

      {/* ── Login ── */}
      {!isConnected && !isConnecting && gateEntered && (
        <LoginScreen connectionState={connectionState} onConnect={connect} />
      )}

      {/* ── Connecting ── */}
      {isConnecting && (
        <div className="app-connecting">
          <div className="app-connecting-text">Entering the void...</div>
        </div>
      )}

      {/* ── Character Select ── */}
      {/* Shown after authentication, before puppeting a character.
          Auto-dismissed when an account_info OOB event arrives confirming
          puppet success (which only happens after `ic <name>`). */}
      {isConnected && oobState.atCharacterSelect && !oobState.inChargen && (
        <CharacterSelect
          sendCommand={sendCommand}
          lastCharCreate={oobState.lastCharCreate}
          clearLastCharCreate={clearLastCharCreate}
        />
      )}

      {/* ── Chargen Wizard ── */}
      {isConnected && !oobState.atCharacterSelect && oobState.inChargen && (
        <ChargenWizard
          sendCommand={sendCommand}
          onExit={exitChargen}
          viewMode={oobState.chargenViewMode || false}
          isAdmin={oobState.isAdmin}
          characterName={oobState.characterName}
          characterSkills={oobState.characterSkills || {}}
        />
      )}

      {/* ── Main Game UI ── */}
      {isConnected && !oobState.atCharacterSelect && !oobState.inChargen && (
        <div className="app-body">
          {/* Left sidebar: commands */}
          <CommandSidebar
            availableCommands={oobState.availableCommands}
            inCombat={oobState.inCombat}
            myTurn={oobState.myTurn}
            selectedEntity={selectedEntity}
            onCommandClick={injectCommand}
            onPrompt={openPrompt}
            sendCommand={sendCommand}
            onEquip={() => setEquipOpen(true)}
            onShop={
              oobState.availableCommands?.some(c => c.key === 'browse')
                ? () => setShopOpen(true)
                : undefined
            }
            onCrafting={
              oobState.availableCommands?.some(c => c.key === '__crafting_ui__')
                ? () => sendCommand('__crafting_ui__')
                : undefined
            }
          />

          {/* Center column:
                - RoomView (top, flex: 1; holds description + 3 columns)
                - CombatTracker (only during combat)
                - ActionToolbar (selected entity actions; sits just
                  above the input bar)
                - CommandInput (bottom, fixed height) */}
          <div className="app-main">
            <RoomView
              messages={messages}
              onCommand={sendCommand}
              onEntityClick={handleEntityClick}
              onEntityContextMenu={handleEntityContextMenu}
              onExitContextMenu={handleExitContextMenu}
              inspectSlot={selectedEntity ? (
                <DetailPanel
                  entityName={selectedEntity.name}
                  entityType={selectedEntity.type}
                  onClose={handleDetailPanelClose}
                  sendCommand={sendCommand}
                  injectCommand={injectCommand}
                  onPrompt={openPrompt}
                  onGive={handleGiveToNpc}
                  description={entityDescription}
                  npcMeta={oobState.roomNpcMeta?.[selectedEntity.name?.toLowerCase()] || null}
                  playerSilver={oobState.purse?.silver || 0}
                />
              ) : null}
            />
            {oobState.inCombat && <CombatTracker oobState={oobState} />}
            <ActionToolbar
              entity={selectedEntity}
              npcMeta={oobState.roomNpcMeta?.[selectedEntity?.name?.toLowerCase()] || null}
              playerSilver={oobState.purse?.silver || 0}
              sendCommand={sendCommand}
              onPrompt={openPrompt}
              onGive={handleGiveToNpc}
              onInspect={() => { /* clicking the entity card already opens DetailPanel; no-op */ }}
              onClose={() => setSelectedEntity(null)}
            />
            <div className="app-log-area">
              {/* Scene log — the chronological scrollback of speech,
                  command echoes, combat lines, and system responses.
                  Without it, typed commands appear to do nothing:
                  RoomView only re-renders on full room looks, and
                  OOB toasts only carry quest/item events. */}
              <GameOutput
                messages={messages}
                inCombat={oobState.inCombat}
                onCommand={sendCommand}
              />
              <CommandInput
                ref={inputRef}
                onSend={sendCommand}
                availableCommands={oobState.availableCommands}
                disabled={false}
              />
            </div>
          </div>

          {/* Right sidebar: always CharacterStatus now. The Inspect
              UI moved off the rail and is rendered as a modal below
              (DetailPanel is now a centered overlay). The bottom
              ActionToolbar handles entity-specific actions. */}
          <CharacterStatus
            oobState={oobState}
            connectionState={connectionState}
            sendCommand={sendCommand}
            onChargen={enterChargen}
            onWorldMap={() => setWorldMapOpen(true)}
            onCharSheet={() => setCharSheetOpen(true)}
            onQuestJournal={() => setQuestJournalOpen(true)}
            onReputation={() => setReputationOpen(true)}
            onAdmin={oobState.isAdmin ? () => setAdminOpen(true) : undefined}
            onSwitchCharacter={() => {
              sendCommand('ooc')
              setTimeout(() => showCharacterSelect(), 300)
            }}
          />
        </div>
      )}

      {/* Inspect inline panel is rendered INSIDE RoomView via the
          inspectSlot prop above (replaces the room description area
          when an entity is selected). Keeping a single render path
          avoids duplicate mounts. */}

      {/* Context menu overlay */}
      {contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          items={contextMenu.items}
          onSelect={handleContextMenuSelect}
          onClose={handleContextMenuClose}
        />
      )}

      {/* World map modal */}
      <WorldMapModal
        open={worldMapOpen}
        onClose={() => setWorldMapOpen(false)}
        sendCommand={sendCommand}
        mapData={oobState.mapData}
      />

      {/* Equip modal */}
      {equipOpen && (
        <EquipModal
          onClose={() => setEquipOpen(false)}
          sendCommand={sendCommand}
          inventoryData={oobState.inventoryData}
          onGiveRequest={handleGiveFromEquipModal}
        />
      )}

      {/* Character sheet modal */}
      {charSheetOpen && (
        <CharSheetModal
          onClose={() => setCharSheetOpen(false)}
          sendCommand={sendCommand}
          charsheetData={oobState.charsheetData}
        />
      )}

      {/* Shop modal */}
      {shopOpen && (
        <ShopModal
          onClose={() => setShopOpen(false)}
          sendCommand={sendCommand}
          shopData={oobState.shopData}
        />
      )}

      {/* Tavyl modal */}
      {tavylOpen && (
        <TavylModal
          open={tavylOpen}
          onClose={() => setTavylOpen(false)}
          sendCommand={sendCommand}
          tavylState={oobState.tavylState}
        />
      )}

      {/* Traveler's Primer modal */}
      {primerOpen && (
        <PrimerModal
          open={primerOpen}
          onClose={() => setPrimerOpen(false)}
          primerData={oobState.primerData}
        />
      )}

      {/* Unified Crafting modal (blacksmith / bowyer / artificer /
          gunsmith / alchemy tabs). */}
      {craftingOpen && (
        <CraftingModal
          onClose={() => setCraftingOpen(false)}
          sendCommand={sendCommand}
          craftingData={oobState.craftingData}
        />
      )}

      {/* Quest journal — active / available-here / completed with
          per-quest accept/abandon buttons. Opens via CharacterStatus. */}
      {questJournalOpen && (
        <QuestJournalModal
          onClose={() => setQuestJournalOpen(false)}
          sendCommand={sendCommand}
          questLog={oobState.questLog}
        />
      )}

      {/* Reputation viewer — faction standing + per-NPC memories. */}
      {reputationOpen && (
        <ReputationModal
          onClose={() => setReputationOpen(false)}
          sendCommand={sendCommand}
          reputationData={oobState.reputationData}
        />
      )}

      {/* Item picker — generic inventory chooser. Powers the
          DetailPanel "Give" flow (NPC chosen first, then item). */}
      {itemPicker && (
        <ItemPickerModal
          title={itemPicker.title}
          subtitle={itemPicker.subtitle}
          onPick={itemPicker.onPick}
          onClose={() => setItemPicker(null)}
          inventoryData={oobState.inventoryData}
          sendCommand={sendCommand}
        />
      )}

      {/* NPC picker — recipient chooser. Powers the EquipModal "Give"
          flow (item chosen first, then NPC). Reads roomNpcMeta for
          the in-room recipient list. */}
      {npcPicker && (
        <NpcPickerModal
          title={npcPicker.title}
          subtitle={npcPicker.subtitle}
          roomNpcMeta={oobState.roomNpcMeta}
          onPick={npcPicker.onPick}
          onClose={() => setNpcPicker(null)}
        />
      )}

      {/* Quest offer modal — shows pending offers one at a time.
          Suppressed when NpcDialoguePanel is currently displaying
          the same offer inline (avoids stacking two modals over
          each other for the same quest). The dialogue modal is
          considered the primary surface for offers from an NPC the
          player is talking to.

          Branching quests (offer.outcomes) use onAcceptOutcome which
          sends `quest accept <title> / <outcome_key>`. Non-branching
          quests use the single Accept button. */}
      {(() => {
        const offers = oobState.questOffers || []
        if (offers.length === 0) return null
        const dialogueNpc = (oobState.npcDialogue?.npc || '').toLowerCase()
        const top = offers[0]
        const handledByDialogue =
          dialogueNpc && (top.giver || '').toLowerCase() === dialogueNpc
        if (handledByDialogue) return null
        return (
          <QuestOfferModal
            open={true}
            offer={top}
            onAccept={() => {
              sendCommand(`quest accept ${top.title}`)
              dismissOnAccept(top)
            }}
            onAcceptOutcome={(outcomeKey) => {
              sendCommand(`quest accept ${top.title} / ${outcomeKey}`)
              dismissOnAccept(top)
            }}
            onDecline={() => dismissQuestOffer(top.key)}
            onClose={() => dismissQuestOffer(top.key)}
          />
        )
      })()}

      {/* Item-received toast — NPC gift notification */}
      <ItemReceivedToast item={oobState.itemReceived} />

      {/* Quest accepted / completed confirmation toasts */}
      <QuestAcceptedToast quest={oobState.questAccepted} />
      <QuestCompletedToast quest={oobState.questCompleted} />
      <QuestProgressToast progress={oobState.questProgress} />
      <RepChangeToast change={oobState.repChange} />

      {/* Combat encounter opt-in — fires when entering a room with
          aggressive NPCs so the player isn't shoved into a fight. */}
      <CombatEncounterHost
        encounter={oobState.combatEncounter}
        onCommand={sendCommand}
        onHold={() => {}}
      />

      {/* Wardstone Hall puzzle — the four-rune Altar of Seals. Pops
          when the player enters the Wardstone Hall and on every
          successful placement. */}
      <SealAltarModal
        altar={oobState.sealAltar}
        sendCommand={sendCommand}
      />

      {/* NPC dialogue panel — rich reply + topic chips */}
      <NpcDialoguePanel
        dialogue={oobState.npcDialogue}
        pendingDialogue={pendingDialogue}
        sendCommand={sendCommand}
        questOffers={oobState.questOffers}
        onAcceptOffer={(offer) => {
          sendCommand(`quest accept ${offer.title}`)
          dismissOnAccept(offer)
        }}
        onAcceptOfferOutcome={(offer, outcomeKey) => {
          sendCommand(`quest accept ${offer.title} / ${outcomeKey}`)
          dismissOnAccept(offer)
        }}
        onDeclineOffer={(offer) => dismissQuestOffer(offer.key)}
        onClose={() => {
          // Closing a ghost's dialogue panel ends the séance early.
          if (oobState.npcDialogue?.isGhost) endSeance()
        }}
      />


      {/* Admin panel — only for admin users */}
      {adminOpen && (
        <AdminPanel onClose={() => setAdminOpen(false)} />
      )}

      {/* Friendly command input prompt modal */}
      <CommandPrompt
        prompt={commandPrompt}
        onSubmit={handlePromptSubmit}
        onCancel={closePrompt}
      />

    </div>
  )
}

export default App
