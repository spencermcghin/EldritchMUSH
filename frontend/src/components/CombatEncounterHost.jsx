import { useEffect, useMemo, useRef, useState } from 'react'
import CombatEncounterPanel from './CombatEncounterPanel'

/**
 * CombatEncounterHost — lifecycle owner of the graphical combat surface.
 *
 * It runs the panel in two modes off the live OOB state, and transitions
 * between them seamlessly:
 *
 *   1. PROMPT mode — the `combat_encounter_prompt` OOB fired (you walked
 *      into a room with hostiles but aren't engaged yet). The panel shows
 *      the framed antagonist and "engage or flee". Clicking an action
 *      sends e.g. `strike <name>`, which starts the real combat loop.
 *
 *   2. LIVE mode — `inCombat` is true. The SAME panel now reflects live
 *      state: antagonist HP from `combatantHp`, the full `combatTurnOrder`
 *      rail with per-combatant HP and the current turn, action buttons
 *      enabled only on the player's turn (`myTurn`), SLAIN/zeroes when the
 *      foe drops. On `combat_end` (`inCombat` false) it dismisses cleanly.
 *
 * The prompt is the ENTRY: engage -> combat_start -> the same mounted
 * panel flips to live mode without a remount. Flee in live mode sends
 * `disengage`; flee in prompt mode just holds back (dismiss).
 *
 * State the panel is driven from (all from useEvennia's oobState):
 *   inCombat        — bool, live-mode gate
 *   combatTurnOrder — [name, ...]  ordered, index 0 is whose turn it is
 *   combatantHp     — { name: 0..100 }
 *   myTurn          — bool, actions enabled only when true
 *   characterName   — the player's own name (everyone else is a foe)
 *   combatEncounter — walk-in prompt { room, hostiles:[{name,desc,isBoss,artKey,tier}], ts }
 *
 * Antagonist identity: in the turn order every name that isn't
 * `characterName` is a foe; the "primary" foe driving the portrait is the
 * first foe in the order, enriched with desc/artKey/isBoss from the
 * remembered walk-in hostiles where the names match.
 *
 * Props:
 *   oobState  — the full live OOB state object from useEvennia
 *   onCommand — (cmd: string) => void   sends a raw game command
 *   onHold    — () => void              prompt dismissed without engaging
 */
export default function CombatEncounterHost({ oobState, onCommand, onHold }) {
  const {
    combatEncounter,
    inCombat,
    combatTurnOrder = [],
    combatantHp = {},
    myTurn,
    characterName,
  } = oobState || {}

  // PROMPT mode is opt-in and dismissable; track whether the player has
  // dismissed the current prompt (keyed by ts).
  const [promptOpen, setPromptOpen] = useState(false)
  const promptTsRef = useRef(0)

  useEffect(() => {
    if (!combatEncounter || !combatEncounter.ts) return
    if (combatEncounter.ts === promptTsRef.current) return
    promptTsRef.current = combatEncounter.ts
    setPromptOpen(true)
  }, [combatEncounter?.ts])

  // Once we're actually in combat, the prompt is superseded by live mode.
  useEffect(() => {
    if (inCombat) setPromptOpen(false)
  }, [inCombat])

  // Remember the most recent hostiles list so live mode can enrich the
  // bare turn-order names with portrait art / desc / boss flag. Keyed by
  // lowercase name.
  const hostileMetaRef = useRef({})
  useEffect(() => {
    const hostiles = combatEncounter?.hostiles
    if (!hostiles || !hostiles.length) return
    const meta = { ...hostileMetaRef.current }
    for (const h of hostiles) {
      if (h?.name) meta[h.name.toLowerCase()] = h
    }
    hostileMetaRef.current = meta
  }, [combatEncounter?.ts])

  // ESC dismisses the prompt (not live combat — you must Flee/disengage).
  useEffect(() => {
    if (!promptOpen || inCombat) return
    const handler = (e) => {
      if (e.key === 'Escape') {
        setPromptOpen(false)
        if (onHold) onHold()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [promptOpen, inCombat, onHold])

  // ── Build the panel `encounter` from live state (preferred) or the
  //    walk-in prompt (entry). ──────────────────────────────────────
  const encounter = useMemo(() => {
    if (inCombat && combatTurnOrder.length > 0) {
      // LIVE: foes are everyone in the order who isn't the player.
      const foes = combatTurnOrder.filter((n) => n !== characterName)
      const primaryName = foes[0]
      const primaryMeta = primaryName
        ? hostileMetaRef.current[primaryName.toLowerCase()]
        : null

      // Per-combatant HP rail. combatantHp is a 0..100 percentage; the
      // panel's BloodBar takes hp/maxHp, so feed pct out of 100.
      const turnOrder = combatTurnOrder.map((n) => ({
        name: n,
        hp: combatantHp[n] ?? 100,
        maxHp: 100,
        isMe: n === characterName,
        isAntagonist: n !== characterName,
      }))

      return {
        name: primaryMeta?.name || primaryName || 'The Foe',
        desc: primaryMeta?.desc || '',
        artKey: primaryMeta?.artKey,
        isBoss: !!primaryMeta?.isBoss,
        hp: primaryName ? (combatantHp[primaryName] ?? 100) : 0,
        maxHp: 100,
        myTurn: !!myTurn,
        turnOrder,
        // Other foes besides the primary — selectable to re-target.
        also: foes.slice(1).map((n) => ({ name: n })),
        _live: true,
        _primaryName: primaryName,
      }
    }

    // PROMPT: the opt-in walk-in face-off.
    if (promptOpen && combatEncounter?.hostiles?.length) {
      const hostiles = combatEncounter.hostiles
      const primary = hostiles.find((h) => h.isBoss) || hostiles[0]
      return {
        name: primary.name,
        desc: primary.desc,
        artKey: primary.artKey,
        isBoss: !!primary.isBoss,
        // Player's move: choose an action to engage, or Flee to hold back.
        myTurn: true,
        also: hostiles.filter((h) => h !== primary).map((h) => ({ name: h.name })),
        _live: false,
        _primaryName: primary.name,
      }
    }

    return null
  }, [
    inCombat,
    combatTurnOrder,
    combatantHp,
    myTurn,
    characterName,
    promptOpen,
    combatEncounter?.ts,
  ])

  if (!encounter) return null

  const targetName = encounter._primaryName

  const handleAction = (actionKey) => {
    if (!targetName) return
    onCommand && onCommand(`${actionKey} ${targetName}`)
  }

  const handleTargetOther = (name) => {
    // Re-target a different hostile. In live mode this is a strike at the
    // new foe (which also shifts the loop's auto-target); in prompt mode
    // it engages that foe.
    onCommand && onCommand(`strike ${name}`)
  }

  const handleFlee = () => {
    if (encounter._live) {
      // Real retreat from the loop.
      onCommand && onCommand('disengage')
    } else {
      // Prompt-mode: just hold back, don't engage.
      setPromptOpen(false)
      if (onHold) onHold()
    }
  }

  return (
    <CombatEncounterPanel
      encounter={encounter}
      onAction={handleAction}
      onFlee={handleFlee}
      onTargetOther={handleTargetOther}
    />
  )
}
