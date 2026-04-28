import { useState, useCallback, useRef, useEffect } from 'react'

const MAX_RECONNECT_DELAY = 10000
const BASE_RECONNECT_DELAY = 500
const MAX_COMBAT_LOG = 10
const MAX_MESSAGES = 500

let msgIdCounter = 0
function nextId() {
  return ++msgIdCounter
}

function classifyMessage(text) {
  const t = text.toLowerCase()
  if (
    t.includes('strike') ||
    t.includes('shoots') ||
    t.includes('hits') ||
    t.includes('misses') ||
    t.includes('damage') ||
    t.includes('combat') ||
    t.includes('bleed') ||
    t.includes('dying') ||
    t.includes('cleave') ||
    t.includes('disarm') ||
    t.includes('stagger') ||
    t.includes('stun') ||
    t.includes('sunder')
  ) {
    return 'combat'
  }
  if (
    t.includes('error') ||
    t.includes('huh?') ||
    t.includes("you can't") ||
    t.includes('you cannot') ||
    t.includes('invalid')
  ) {
    return 'error'
  }
  return 'game'
}

export function useEvennia() {
  const [connectionState, setConnectionState] = useState('disconnected')
  const [messages, setMessages] = useState([])
  const [oobState, setOobState] = useState({
    availableCommands: [],
    isAdmin: false,
    inCombat: false,
    combatTurnOrder: [],
    myTurn: false,
    combatLog: [],
    characterName: '',
    // Character stats parsed from game text or OOB
    body: null,
    totalBody: null,
    bleedPoints: null,
    deathPoints: null,
    av: 0,
    purse: { silver: 0, gold: 0, copper: 0 },
    tavylState: null,
    primerData: null,
    inventoryOpen: null,
    questOffers: [],
    itemReceived: null,
    questAccepted: null,
    questCompleted: null,
    questProgress: null,
    npcDialogue: null,
    // Per-room NPC metadata pushed via __room_meta__ event.
    // Keyed by lowercase NPC name → { dbref, isTavylDealer, isMerchant, hasAi }
    roomNpcMeta: {},
    statusFlags: {
      bleeding: false,
      dying: false,
      unconscious: false,
    },
    equipment: {
      rightHand: null,
      leftHand: null,
      body: null,
    },
    // HP tracking for combatants (key: name, value: { hp: 0-100 })
    combatantHp: {},
    // Chargen room detection
    inChargen: false,
    chargenViewMode: false,
    // Current character's skill levels (populated from server when available)
    characterSkills: {},
    // Structured inventory data from the server's inventory_list OOB event.
    inventoryData: null,
    // Structured charsheet data from the server's charsheet_data OOB event.
    charsheetData: null,
    // Structured shop data from the server's shop_data OOB event.
    shopData: null,
    // Room graph data for the interactive map.
    mapData: null,
    // Structured crafting data from the server's crafting_data OOB event.
    // Multi-tab payload for the unified CraftingModal (blacksmith, bowyer,
    // artificer, gunsmith, alchemy).
    craftingData: null,
    // True when we're authenticated but haven't yet puppeted a character.
    // Drives the CharacterSelect screen.
    atCharacterSelect: false,
    // Result of the most recent `charcreate` attempt. Set by the
    // character_created / character_create_failed OOB events emitted
    // from commands/account.py CmdCharCreate. The CharacterSelect
    // screen reads this to know whether to fire `ic <name>`, surface
    // an error, or refresh the list.
    //   { status: 'pending' | 'success' | 'error',
    //     name?: string, reason?: string, code?: string, ts: number }
    lastCharCreate: null,
  })

  // Timestamp (ms) of the last manual exit from chargen. Used to
  // suppress chargen room auto-detection for a short window so a stale
  // room description doesn't re-trigger the wizard immediately.
  const chargenExitedAtRef = useRef(0)

  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const reconnectDelayRef = useRef(BASE_RECONNECT_DELAY)
  // Default host/port — when co-located (Railway), use same origin; else env vars or localhost
  const defaultHost = import.meta.env.VITE_GAME_HOST || window.location.hostname || 'localhost'
  const defaultPort = parseInt(import.meta.env.VITE_GAME_PORT || (window.location.port || (window.location.protocol === 'https:' ? '443' : '80')))
  const connectionParamsRef = useRef({ host: defaultHost, port: defaultPort })
  const shouldReconnectRef = useRef(false)
  const pingIntervalRef = useRef(null)
  const pingStartRef = useRef(null)
  const [latency, setLatency] = useState(null)
  // Manual-login credentials queued for after the WS opens (cleared after send)
  const pendingLoginRef = useRef(null)

  const addMessage = useCallback((type, content, raw = '') => {
    setMessages((prev) => {
      const next = [
        ...prev,
        { id: nextId(), type, content, timestamp: Date.now(), raw },
      ]
      return next.length > MAX_MESSAGES ? next.slice(next.length - MAX_MESSAGES) : next
    })
  }, [])

  const parseCharacterName = useCallback((text) => {
    // "Your name is Aldric" or "Welcome, Aldric."
    let m = text.match(/your name is ([A-Za-z]+)/i)
    if (m) return m[1]
    m = text.match(/welcome(?:,| back,)?\s+([A-Za-z]+)/i)
    if (m) return m[1]
    return null
  }, [])

  const parseStats = useCallback((text) => {
    // Try to parse charsheet output
    const updates = {}
    let m

    m = text.match(/body[:\s]+(\d+)\s*\/\s*(\d+)/i)
    if (m) { updates.body = parseInt(m[1]); updates.totalBody = parseInt(m[2]) }

    m = text.match(/bleed[:\s]+(\d+)/i)
    if (m) updates.bleedPoints = parseInt(m[1])

    m = text.match(/death[:\s]+(\d+)/i)
    if (m) updates.deathPoints = parseInt(m[1])

    m = text.match(/armor value[:\s]+(\d+)/i)
    if (!m) m = text.match(/\bav[:\s]+(\d+)/i)
    if (m) updates.av = parseInt(m[1])

    return Object.keys(updates).length > 0 ? updates : null
  }, [])

  const handleOobEvent = useCallback((eventType, args, kwargs) => {
    setOobState((prev) => {
      const next = { ...prev }

      switch (eventType) {
        case 'available_commands': {
          next.availableCommands = kwargs.commands || []
          break
        }
        case 'account_info': {
          next.isAdmin = !!kwargs.is_admin
          if (kwargs.character) {
            next.characterName = kwargs.character
            // account_info is emitted from at_post_puppet — receiving
            // a character name means the player has successfully
            // puppeted, so dismiss the CharacterSelect screen.
            next.atCharacterSelect = false
          }
          break
        }
        case 'character_created': {
          next.lastCharCreate = {
            status: 'success',
            name: kwargs.name || '',
            dbref: kwargs.dbref || '',
            ts: Date.now(),
          }
          break
        }
        case 'character_create_failed': {
          next.lastCharCreate = {
            status: 'error',
            reason: kwargs.reason || 'Character creation failed.',
            code: kwargs.code || 'unknown',
            ts: Date.now(),
          }
          break
        }
        case 'inventory_list': {
          next.inventoryData = {
            items: kwargs.items || [],
            slots: kwargs.slots || {},
            ts: Date.now(),
          }
          break
        }
        case 'charsheet_data': {
          next.charsheetData = { ...kwargs, ts: Date.now() }
          break
        }
        case 'shop_data': {
          next.shopData = { ...kwargs, ts: Date.now() }
          break
        }
        case 'map_data': {
          next.mapData = { ...kwargs, ts: Date.now() }
          break
        }
        case 'crafting_data': {
          next.craftingData = { ...kwargs, ts: Date.now() }
          break
        }
        case 'character_stats': {
          if (kwargs.character) next.characterName = kwargs.character
          if (typeof kwargs.body === 'number') next.body = kwargs.body
          if (typeof kwargs.total_body === 'number') next.totalBody = kwargs.total_body
          if (typeof kwargs.bleed_points === 'number') next.bleedPoints = kwargs.bleed_points
          if (typeof kwargs.death_points === 'number') next.deathPoints = kwargs.death_points
          if (typeof kwargs.av === 'number') next.av = kwargs.av
          if (kwargs.status) next.statusFlags = { ...prev.statusFlags, ...kwargs.status }
          if (kwargs.equipment) next.equipment = { ...prev.equipment, ...kwargs.equipment }
          if (kwargs.purse) next.purse = { ...prev.purse, ...kwargs.purse }
          break
        }
        case 'tavyl_state': {
          // Mirror the entire payload onto tavylState so the modal can
          // re-render. ts is added so React notices the change even if
          // payload structure is identical between turns.
          next.tavylState = { ...kwargs, ts: Date.now() }
          break
        }
        case 'primer_data': {
          // Traveler's Primer modal payload. Auto-opens via App.jsx
          // effect that watches primerData.ts.
          next.primerData = { ...kwargs, ts: Date.now() }
          break
        }
        case 'inventory_open': {
          // Signal to auto-open the equip/inventory modal. Fired by
          // the server when the player types `inv`/`inventory`/`i`.
          next.inventoryOpen = { ts: Date.now() }
          break
        }
        case 'quest_offer': {
          // Append pending quest offers — App.jsx dequeues them one
          // at a time into the QuestOfferModal.
          const incoming = Array.isArray(kwargs.offers) ? kwargs.offers : []
          const existing = prev.questOffers || []
          const existingKeys = new Set(existing.map(o => o.key))
          const additions = incoming.filter(o => !existingKeys.has(o.key))
          next.questOffers = [...existing, ...additions]
          break
        }
        case 'item_received': {
          // Transient toast showing that an NPC gave the player
          // something. `ts` changes per event so App.jsx effect fires.
          next.itemReceived = {
            itemName: kwargs.itemName || kwargs.item_name,
            fromNpc: kwargs.fromNpc || kwargs.from_npc || '',
            desc: kwargs.desc || '',
            ts: Date.now(),
          }
          break
        }
        case 'quest_accepted': {
          // Confirmation toast after `quest accept` succeeds. Brief —
          // just enough to confirm the commit without spamming chat.
          next.questAccepted = {
            title: kwargs.title || '',
            giver: kwargs.giver || '',
            outcomeLabel: kwargs.outcomeLabel || kwargs.outcome_label || '',
            ts: Date.now(),
          }
          break
        }
        case 'quest_completed': {
          // Celebratory summary toast when a quest finishes — shows
          // outcome label, silver, items, faction rep deltas, and any
          // per-NPC rep deltas (NPC memory v2).
          next.questCompleted = {
            title: kwargs.title || '',
            outcomeLabel: kwargs.outcomeLabel || kwargs.outcome_label || '',
            silver: kwargs.silver || 0,
            items: Array.isArray(kwargs.items) ? kwargs.items : [],
            reagents: kwargs.reagents || {},
            factionRep: kwargs.factionRep || kwargs.faction_rep || {},
            npcRep: kwargs.npcRep || kwargs.npc_rep || {},
            ts: Date.now(),
          }
          break
        }
        case 'quest_progress': {
          // Objective tick — subtle inline pulse, not a full toast.
          next.questProgress = {
            key: kwargs.key || '',
            desc: kwargs.desc || '',
            current: Number(kwargs.current) || 0,
            qty: Number(kwargs.qty) || 0,
            done: !!kwargs.done,
            ts: Date.now(),
          }
          break
        }
        case 'npc_dialogue': {
          // Rich NPC reply — opens a dialogue modal with topic chips.
          // Successive replies replace/append. `channel` distinguishes
          // ask (public), whisper (private), say (public).
          next.npcDialogue = {
            channel: kwargs.channel || 'ask',
            npc: kwargs.npc || '',
            npcDbref: kwargs.npcDbref || kwargs.npc_dbref || '',
            npcDesc: kwargs.npcDesc || kwargs.npc_desc || '',
            question: kwargs.question || '',
            reply: kwargs.reply || '',
            topics: Array.isArray(kwargs.topics) ? kwargs.topics : [],
            ts: Date.now(),
          }
          break
        }
        case 'room_meta': {
          // Index NPCs by lowercase name for fast lookup in DetailPanel.
          // Also include alias keys so e.g. "hegga" matches the
          // Quartermaster.
          const meta = {}
          for (const npc of (kwargs.npcs || [])) {
            const entry = {
              name: npc.name,
              dbref: npc.dbref,
              isTavylDealer: !!npc.isTavylDealer,
              tavylStake: Number(npc.tavylStake) || 1,
              isMerchant: !!npc.isMerchant,
              hasAi: !!npc.hasAi,
              topics: Array.isArray(npc.topics) ? npc.topics : [],
            }
            meta[(npc.name || '').toLowerCase()] = entry
            for (const a of (npc.aliases || [])) {
              meta[(a || '').toLowerCase()] = entry
            }
          }
          next.roomNpcMeta = meta
          break
        }
        case 'combat_start': {
          const combatants = kwargs.combatants || []
          const turnOrder = kwargs.turn_order || combatants
          next.inCombat = true
          next.combatTurnOrder = turnOrder
          // Initialize all combatants at 100% HP
          const hp = {}
          combatants.forEach((c) => { hp[c] = 100 })
          next.combatantHp = hp
          next.myTurn = turnOrder[0] === prev.characterName
          const entry = { id: nextId(), type: 'start', text: 'Combat begins!', ts: Date.now() }
          next.combatLog = [entry, ...prev.combatLog].slice(0, MAX_COMBAT_LOG)
          break
        }
        case 'combat_join': {
          const combatants = kwargs.combatants || []
          const turnOrder = kwargs.turn_order || combatants
          next.inCombat = true
          next.combatTurnOrder = turnOrder
          const newHp = { ...prev.combatantHp }
          combatants.forEach((c) => { if (!newHp[c]) newHp[c] = 100 })
          next.combatantHp = newHp
          next.myTurn = turnOrder[0] === prev.characterName
          break
        }
        case 'combat_end': {
          next.inCombat = false
          next.combatTurnOrder = []
          next.myTurn = false
          next.combatantHp = {}
          const entry = {
            id: nextId(),
            type: 'end',
            text: kwargs.reason ? `Combat ends: ${kwargs.reason}` : 'Combat ends.',
            ts: Date.now(),
          }
          next.combatLog = [entry, ...prev.combatLog].slice(0, MAX_COMBAT_LOG)
          break
        }
        case 'turn_change': {
          const turnOrder = kwargs.turn_order || prev.combatTurnOrder
          next.combatTurnOrder = turnOrder
          next.myTurn = kwargs.character === prev.characterName
          break
        }
        case 'combat_hit': {
          const { attacker, target, damage, location, weapon, roll, target_av } = kwargs
          // Reduce target HP by damage (rough %)
          const newHp = { ...prev.combatantHp }
          if (target && newHp[target] !== undefined) {
            newHp[target] = Math.max(0, newHp[target] - (damage || 1) * 10)
          }
          next.combatantHp = newHp
          const text = `⚔ ${attacker} strikes ${target} for ${damage} dmg${location ? ` [${location}]` : ''}`
          const entry = { id: nextId(), type: 'hit', text, ts: Date.now() }
          next.combatLog = [entry, ...prev.combatLog].slice(0, MAX_COMBAT_LOG)
          break
        }
        case 'combat_miss': {
          const { attacker, target, reason } = kwargs
          const text = `✕ ${attacker} misses ${target}${reason ? ` (${reason})` : ''}`
          const entry = { id: nextId(), type: 'miss', text, ts: Date.now() }
          next.combatLog = [entry, ...prev.combatLog].slice(0, MAX_COMBAT_LOG)
          break
        }
        case 'combat_disengage': {
          const { character } = kwargs
          const text = `${character} disengages from combat`
          const entry = { id: nextId(), type: 'disengage', text, ts: Date.now() }
          next.combatLog = [entry, ...prev.combatLog].slice(0, MAX_COMBAT_LOG)
          // Remove from HP tracking
          const newHp = { ...prev.combatantHp }
          delete newHp[character]
          next.combatantHp = newHp
          break
        }
        case 'character_bleed': {
          const { character } = kwargs
          if (character === prev.characterName) {
            next.statusFlags = { ...prev.statusFlags, bleeding: true }
          }
          const entry = { id: nextId(), type: 'bleed', text: `🩸 ${character} is bleeding`, ts: Date.now() }
          next.combatLog = [entry, ...prev.combatLog].slice(0, MAX_COMBAT_LOG)
          break
        }
        case 'character_dying': {
          const { character } = kwargs
          if (character === prev.characterName) {
            next.statusFlags = { ...prev.statusFlags, dying: true }
          }
          const entry = { id: nextId(), type: 'dying', text: `☠ ${character} is dying`, ts: Date.now() }
          next.combatLog = [entry, ...prev.combatLog].slice(0, MAX_COMBAT_LOG)
          break
        }
        default:
          break
      }
      return next
    })
  }, [])

  const processFrame = useCallback(
    (data) => {
      // Evennia webclient protocol: each message is a flat 3-element JSON array
      //   ["cmd", args, kwargs]
      // e.g. ["text", ["Hello!"], {}] or ["pong", [], {}]
      let parsed
      try {
        parsed = JSON.parse(data)
      } catch {
        addMessage('system', `[Malformed frame: ${data}]`)
        return
      }

      if (!Array.isArray(parsed) || parsed.length < 1) return

      const cmd = parsed[0]
      const args = parsed[1] ?? []
      const kwargs = parsed[2] ?? {}

      if (cmd === 'text') {
        const text = Array.isArray(args) ? args[0] || '' : args
        if (typeof text === 'string' && text.length > 0) {
          const type = classifyMessage(text)
          addMessage(type, text, text)

          const charName = parseCharacterName(text)
          if (charName) {
            setOobState((prev) => ({ ...prev, characterName: charName }))
          }

          const stats = parseStats(text)
          if (stats) {
            setOobState((prev) => ({ ...prev, ...stats }))
          }

          // Chargen room detection — only trigger on the specific ChargenRoom
          // name "The Threshold" or its exact description text. Previous logic
          // matched any text containing "chargen" which was way too broad —
          // it re-triggered the wizard when looking at rooms or items that
          // happened to contain that word (e.g. a room named "Chargenit").
          const stripped = text.replace(/<[^>]*>/g, '').toLowerCase()
          const recentlyExited = Date.now() - chargenExitedAtRef.current < 3000
          if (!recentlyExited && (
            stripped.includes('the threshold') && stripped.includes('mirrored pool')
          )) {
            setOobState((prev) => prev.inChargen ? prev : { ...prev, inChargen: true, chargenViewMode: false })
          }
        }
      } else if (cmd === 'event') {
        const eventType = kwargs.type || (Array.isArray(args) && args[0])
        if (eventType) {
          handleOobEvent(eventType, args, kwargs)
        }
      } else {
        const text = Array.isArray(args) && args[0]
        if (text && typeof text === 'string') {
          addMessage('system', text, text)
        }
      }
    },
    [addMessage, handleOobEvent, parseCharacterName, parseStats]
  )

  const connect = useCallback((host = 'localhost', port = 4002, credentials = null) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    connectionParamsRef.current = { host, port }
    shouldReconnectRef.current = true
    setConnectionState('connecting')

    // Stash manual-login credentials for after the WS opens.
    if (credentials && credentials.username && credentials.password) {
      pendingLoginRef.current = credentials
    }

    // Step 1: ask the Django backend for our session key (csessid).
    // If the user is already authenticated via Google OAuth, this also
    // tells us their username so we can skip the manual login dance.
    // Same-origin so the session cookie rides along automatically.
    const fetchCsessid = async () => {
      try {
        const resp = await fetch('/api/webclient_session/', { credentials: 'include' })
        if (resp.ok) {
          const data = await resp.json()
          return data
        }
      } catch (err) {
        // Endpoint not yet deployed (older builds) — fall through.
      }
      return { authenticated: false, csessid: null, username: null }
    }

    fetchCsessid().then((session) => {
      const isSecure = window.location.protocol === 'https:'
      const protocol = isSecure ? 'wss:' : 'ws:'
      const portStr = (port === 443 || port === 80) ? '' : `:${port}`
      // Evennia's webclient handler reads the csessid from the WS URL
      // query string and uses it to look up the Django session.
      const csessidQuery = session.csessid ? `?${session.csessid}` : ''
      const url = `${protocol}//${host}${portStr}/websocket${csessidQuery}`

      let ws
      try {
        ws = new WebSocket(url)
      } catch (err) {
        setConnectionState('disconnected')
        addMessage('error', `Failed to create WebSocket: ${err.message}`)
        return
      }

      wsRef.current = ws

      ws.onopen = () => {
        setConnectionState('connected')
        reconnectDelayRef.current = BASE_RECONNECT_DELAY

        if (session.authenticated && session.username) {
          addMessage('system', `Welcome back, ${session.username}.`)
          // Authenticated via Django session (OAuth or shared cookie).
          // Under MULTISESSION_MODE=2 we don't auto-puppet, so show
          // the CharacterSelect screen.
          setOobState((prev) => ({ ...prev, atCharacterSelect: true }))
        } else if (pendingLoginRef.current) {
          // Manual login flow — fire `connect user pass` automatically.
          const { username, password } = pendingLoginRef.current
          pendingLoginRef.current = null
          ws.send(JSON.stringify(['text', [`connect ${username} ${password}`], {}]))
          addMessage('system', `Connecting as ${username}...`)
          // Optimistically show the CharacterSelect screen — if the
          // login fails, the screen will surface an error from
          // /api/account/characters/ which returns authenticated:false.
          setTimeout(() => {
            setOobState((prev) => ({ ...prev, atCharacterSelect: true }))
          }, 600)
        } else {
          addMessage('system', `Connected to ${url}. Type connect <username> <password> to log in.`)
        }

        // Keepalive: send an empty text command every 25s to prevent
        // Railway's edge proxy from closing idle WebSocket connections.
        const sendKeepalive = () => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(['text', [''], {}]))
          }
        }
        pingIntervalRef.current = setInterval(sendKeepalive, 25000)
      }

      ws.onmessage = (event) => {
        processFrame(event.data)
      }

      ws.onerror = () => {
        addMessage('error', 'WebSocket error. Connection may be unavailable.')
      }

      ws.onclose = () => {
        setConnectionState('disconnected')
        clearInterval(pingIntervalRef.current)
        pingIntervalRef.current = null

        if (shouldReconnectRef.current) {
          const delay = reconnectDelayRef.current
          addMessage('system', `Connection lost. Reconnecting in ${Math.round(delay / 1000)}s...`)
          reconnectDelayRef.current = Math.min(delay * 2, MAX_RECONNECT_DELAY)
          reconnectTimeoutRef.current = setTimeout(() => {
            const { host, port } = connectionParamsRef.current
            connect(host, port)
          }, delay)
        }
      }
    })
  }, [addMessage, processFrame])

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false
    clearInterval(pingIntervalRef.current)
    pingIntervalRef.current = null
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setConnectionState('disconnected')
    setOobState((prev) => ({ ...prev, atCharacterSelect: false, characterName: '' }))
    addMessage('system', 'Disconnected from server.')
  }, [addMessage])

  // Commands that change room contents — after these, auto-send `look`
  // so the room entity list refreshes in RoomView.
  const _ROOM_CHANGING_CMDS = /^(get|drop|give|put|pick up)\b/i

  const sendCommand = useCallback((text) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      addMessage('error', 'Not connected to server.')
      return
    }
    const frame = JSON.stringify(['text', [text], {}])
    wsRef.current.send(frame)
    // Echo command to output
    addMessage('system', `> ${text}`)

    // Auto-refresh room view after item manipulation commands. A short
    // delay lets the server process the command before we request the
    // updated room description.
    if (_ROOM_CHANGING_CMDS.test(text.trim())) {
      setTimeout(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify(['text', ['look'], {}]))
        }
      }, 400)
    }
  }, [addMessage])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      shouldReconnectRef.current = false
      clearInterval(pingIntervalRef.current)
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
      if (wsRef.current) wsRef.current.close()
    }
  }, [])

  const exitChargen = useCallback(() => {
    chargenExitedAtRef.current = Date.now()
    setOobState((prev) => ({ ...prev, inChargen: false, chargenViewMode: false }))
  }, [])

  const clearLastCharCreate = useCallback(() => {
    setOobState((prev) => (prev.lastCharCreate ? { ...prev, lastCharCreate: null } : prev))
  }, [])

  const enterChargen = useCallback((viewMode = true) => {
    setOobState((prev) => ({ ...prev, inChargen: true, chargenViewMode: viewMode }))
  }, [])

  const showCharacterSelect = useCallback(() => {
    setOobState((prev) => ({ ...prev, atCharacterSelect: true, characterName: '' }))
  }, [])

  const dismissQuestOffer = useCallback((questKey) => {
    setOobState((prev) => ({
      ...prev,
      questOffers: (prev.questOffers || []).filter(o => o.key !== questKey),
    }))
  }, [])

  return {
    connectionState,
    messages,
    oobState,
    latency,
    sendCommand,
    connect,
    disconnect,
    exitChargen,
    enterChargen,
    clearLastCharCreate,
    showCharacterSelect,
    dismissQuestOffer,
  }
}
