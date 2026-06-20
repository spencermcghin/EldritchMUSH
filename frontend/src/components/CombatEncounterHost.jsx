import { useEffect, useState } from 'react'
import CombatEncounterPanel from './CombatEncounterPanel'

/**
 * CombatEncounterHost — lifecycle wrapper that turns the opt-in
 * `combat_encounter_prompt` OOB event into the graphical
 * CombatEncounterPanel. This replaces the old text CombatEncounterModal:
 * walk into a room with hostiles and you face a framed antagonist
 * portrait (its `art_key` resolves to a bestiary plate). Engage with an
 * action button or Flee to hold back.
 *
 * Scope note: this surfaces the encounter and hands off to the existing
 * combat loop on engage (the panel dismisses, the text CombatTracker
 * takes over). Feeding the panel LIVE in-combat HP / turn order so it
 * persists as a sustained face-off is a follow-up — see
 * docs/combat-encounter-graphical.md.
 *
 * Props:
 *   encounter — { room, hostiles: [{name, desc, isBoss, artKey, tier}], ts } | null
 *   onCommand — (cmd: string) => void   sends a raw game command
 *   onHold    — () => void              dismissed without engaging
 */
export default function CombatEncounterHost({ encounter, onCommand, onHold }) {
  const [open, setOpen] = useState(false)
  const [current, setCurrent] = useState(null)

  useEffect(() => {
    if (!encounter || !encounter.ts) return
    setCurrent(encounter)
    setOpen(true)
  }, [encounter?.ts])

  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (e.key === 'Escape') dismiss() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open])

  const dismiss = () => {
    setOpen(false)
    if (onHold) onHold()
  }

  const engage = (actionKey, name) => {
    setOpen(false)
    if (onCommand) onCommand(`${actionKey} ${name}`)
  }

  if (!open || !current?.hostiles?.length) return null

  const hostiles = current.hostiles
  const primary = hostiles.find((h) => h.isBoss) || hostiles[0]
  const also = hostiles.filter((h) => h !== primary).map((h) => ({ name: h.name }))

  const enc = {
    name: primary.name,
    desc: primary.desc,
    artKey: primary.artKey,
    isBoss: !!primary.isBoss,
    // The player's move: choose an action to engage, or Flee to hold back.
    myTurn: true,
    also,
  }

  return (
    <CombatEncounterPanel
      encounter={enc}
      onAction={(key) => engage(key, primary.name)}
      onFlee={dismiss}
      onTargetOther={(name) => engage('strike', name)}
    />
  )
}
