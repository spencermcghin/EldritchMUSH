import { useRef, useState, useCallback, useEffect } from 'react'
import { useEvennia } from './hooks/useEvennia'
import LoginScreen from './components/LoginScreen'
import CharacterSelect from './components/CharacterSelect'
import GameOutput from './components/GameOutput'
import CombatTracker from './components/CombatTracker'
import CommandSidebar from './components/CommandSidebar'
import CharacterStatus from './components/CharacterStatus'
import DetailPanel from './components/DetailPanel'
import ContextMenu from './components/ContextMenu'
import CommandInput from './components/CommandInput'
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
import ItemReceivedToast from './components/ItemReceivedToast'
import QuestAcceptedToast from './components/QuestAcceptedToast'
import QuestCompletedToast from './components/QuestCompletedToast'
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
  const { connectionState, messages, oobState, latency, sendCommand, connect, disconnect, exitChargen, enterChargen, clearLastCharCreate, showCharacterSelect, dismissQuestOffer } =
    useEvennia()

  const inputRef = useRef(null)

  // Auto-connect after OAuth redirect: when the page loads, ask the
  // backend whether we already have a Django session. If so, skip the
  // LoginScreen entirely and open the WebSocket — Evennia will see the
  // csessid and auto-puppet the player's character.
  const autoConnectAttemptedRef = useRef(false)
  useEffect(() => {
    if (autoConnectAttemptedRef.current) return
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
  }, [connectionState, connect])

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

  return (
    <div className="app-container">

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
          {isConnected && (
            <button className="header-disconnect-btn" onClick={disconnect} title="Disconnect">✕</button>
          )}
        </div>
      </header>

      {/* ── Login ── */}
      {!isConnected && !isConnecting && (
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

          {/* Center: room view on top, log + input on bottom */}
          <div className="app-main">
            <RoomView
              messages={messages}
              onCommand={sendCommand}
              onEntityClick={handleEntityClick}
              onEntityContextMenu={handleEntityContextMenu}
              onExitContextMenu={handleExitContextMenu}
            />
            {oobState.inCombat && <CombatTracker oobState={oobState} />}
            <div className="app-log-area">
              <GameOutput messages={messages} onCommand={sendCommand} />
              <CommandInput
                ref={inputRef}
                onSend={sendCommand}
                availableCommands={oobState.availableCommands}
                disabled={false}
              />
            </div>
          </div>

          {/* Right sidebar: character status or detail panel */}
          {selectedEntity ? (
            <DetailPanel
              entityName={selectedEntity.name}
              entityType={selectedEntity.type}
              onClose={handleDetailPanelClose}
              sendCommand={sendCommand}
              injectCommand={injectCommand}
              onPrompt={openPrompt}
              description={entityDescription}
              npcMeta={oobState.roomNpcMeta?.[selectedEntity.name?.toLowerCase()] || null}
              playerSilver={oobState.purse?.silver || 0}
            />
          ) : (
            <CharacterStatus
              oobState={oobState}
              connectionState={connectionState}
              sendCommand={sendCommand}
              onChargen={enterChargen}
              onWorldMap={() => setWorldMapOpen(true)}
              onCharSheet={() => setCharSheetOpen(true)}
              onAdmin={oobState.isAdmin ? () => setAdminOpen(true) : undefined}
              onSwitchCharacter={() => {
                sendCommand('ooc')
                setTimeout(() => showCharacterSelect(), 300)
              }}
            />
          )}
        </div>
      )}

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

      {/* Quest offer modal — shows pending offers one at a time.
          Branching quests (offer.outcomes) use onAcceptOutcome which
          sends `quest accept <title> / <outcome_key>`. Non-branching
          quests use the single Accept button. */}
      {oobState.questOffers?.length > 0 && (
        <QuestOfferModal
          open={true}
          offer={oobState.questOffers[0]}
          onAccept={() => {
            const offer = oobState.questOffers[0]
            sendCommand(`quest accept ${offer.title}`)
            dismissQuestOffer(offer.key)
          }}
          onAcceptOutcome={(outcomeKey) => {
            const offer = oobState.questOffers[0]
            sendCommand(`quest accept ${offer.title} / ${outcomeKey}`)
            dismissQuestOffer(offer.key)
          }}
          onDecline={() => dismissQuestOffer(oobState.questOffers[0].key)}
          onClose={() => dismissQuestOffer(oobState.questOffers[0].key)}
        />
      )}

      {/* Item-received toast — NPC gift notification */}
      <ItemReceivedToast item={oobState.itemReceived} />

      {/* Quest accepted / completed confirmation toasts */}
      <QuestAcceptedToast quest={oobState.questAccepted} />
      <QuestCompletedToast quest={oobState.questCompleted} />


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
