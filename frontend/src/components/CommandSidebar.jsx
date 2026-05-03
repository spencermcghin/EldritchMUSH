import { getPromptForCommand } from '../data/commandPrompts'
import './CommandSidebar.css'

// Always-available commands (no skill required).
// Note: `charsheet` and `inventory` (`equip`) are intentionally NOT
// listed here because the right-hand CharacterStatus panel already
// has dedicated buttons for them — listing them on the left would
// duplicate that surface.
const ALWAYS_COMMANDS = [
  { key: 'look', label: 'Look', args_hint: '', category: 'Exploration' },
  { key: 'say', label: 'Say', args_hint: '<message>', category: 'Social' },
  { key: 'emote', label: 'Emote', args_hint: '<action>', category: 'Social' },
  { key: 'who', label: 'Who', args_hint: '', category: 'General' },
  // Help: leave args_hint blank so a click fires `help` directly
  // (the bare command lists topics). To browse a specific topic, the
  // player can still type `help <topic>` in the input bar.
  { key: 'help', label: 'Help', args_hint: '', category: 'General' },
]

// Combat commands — only shown when in combat
const COMBAT_COMMANDS = [
  { key: 'strike', label: 'Strike', args_hint: '<target>', category: 'Combat' },
  { key: 'shoot', label: 'Shoot', args_hint: '<target>', category: 'Combat' },
  { key: 'cleave', label: 'Cleave', args_hint: '', category: 'Combat' },
  { key: 'disarm', label: 'Disarm', args_hint: '<target>', category: 'Combat' },
  { key: 'stagger', label: 'Stagger', args_hint: '<target>', category: 'Combat' },
  { key: 'stun', label: 'Stun', args_hint: '<target>', category: 'Combat' },
  { key: 'sunder', label: 'Sunder', args_hint: '<target>', category: 'Combat' },
  { key: 'skip', label: 'Skip Turn', args_hint: '', category: 'Combat' },
  { key: 'disengage', label: 'Disengage', args_hint: '', category: 'Combat' },
]

// Skill-gated commands — only shown if character has the relevant skill.
// Crafting (forge/craft/brew) is no longer here: it's a single contextual
// "Crafting" button wired up via the onCrafting prop, driven by the
// server's available_commands OOB event (only shown at a matching
// station). Repair / reagents likewise come from the server.
const SKILL_COMMANDS = [
  { key: 'medicine', label: 'Medicine', args_hint: '<target>', category: 'Healing', requireSkill: 'medicine' },
  { key: 'chirurgery', label: 'Chirurgery', args_hint: '<target>', category: 'Healing', requireSkill: 'chirurgeon' },
]

// Shop commands — only shown when the server's available_commands OOB
// event includes them (i.e. when a Merchant is in the room). Removed
// from the hardcoded static list; the server pushes these dynamically.

const CATEGORY_ORDER = ['Combat', 'Healing', 'Alchemy', 'Crafting', 'Shop', 'Exploration', 'Social', 'General']

function buildCommandList(inCombat, characterSkills) {
  const cmds = []

  // Combat commands only when fighting
  if (inCombat) {
    cmds.push(...COMBAT_COMMANDS)
  }

  // Skill-gated commands
  for (const cmd of SKILL_COMMANDS) {
    if (cmd.requireSkill && characterSkills[cmd.requireSkill]) {
      cmds.push(cmd)
    } else if (cmd.requireAny && cmd.requireAny.some(s => characterSkills[s])) {
      cmds.push(cmd)
    }
  }

  // Context commands (shop) — only shown via OOB available_commands
  // from the server, not hardcoded. Removed from the static list.

  // Always-available
  cmds.push(...ALWAYS_COMMANDS)

  return cmds
}

function groupCommands(commands) {
  const groups = {}
  for (const cmd of commands) {
    const cat = cmd.category || 'General'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(cmd)
  }
  const sorted = {}
  for (const cat of CATEGORY_ORDER) {
    if (groups[cat]) sorted[cat] = groups[cat]
  }
  for (const cat of Object.keys(groups)) {
    if (!sorted[cat]) sorted[cat] = groups[cat]
  }
  return sorted
}

// Commands that take a single target (creature/character) and benefit from
// the click-to-target shortcut. When the player has selected an entity in
// the room view, clicking these fires `${cmd} ${entity.name}` directly —
// no naming-collision modal. Falls through to the prompt modal otherwise.
const TARGETED_COMMANDS = new Set([
  'strike', 'shoot', 'disarm', 'stagger', 'stun', 'sunder',
  'medicine', 'chirurgery',
])

// Map a command key to the entity types it can validly target. Combat
// verbs only target NPCs / characters / players; healing verbs likewise.
const TARGET_TYPES_FOR = {
  strike: ['npc', 'character', 'player'],
  shoot: ['npc', 'character', 'player'],
  disarm: ['npc', 'character', 'player'],
  stagger: ['npc', 'character', 'player'],
  stun: ['npc', 'character', 'player'],
  sunder: ['npc', 'character', 'player'],
  medicine: ['character', 'player'],
  chirurgery: ['character', 'player'],
}

function isValidTargetFor(cmdKey, entity) {
  if (!entity) return false
  const allowed = TARGET_TYPES_FOR[cmdKey]
  if (!allowed) return false
  return allowed.includes(entity.type)
}

function CommandEntry({ cmd, onClick, onPrompt, sendCommand, selectedEntity }) {
  const targetable = TARGETED_COMMANDS.has(cmd.key)
  const validTarget = targetable && isValidTargetFor(cmd.key, selectedEntity)

  const handleClick = () => {
    // Click-to-target: if the player has a valid entity selected and
    // this is a targeted command, fire it directly. Eliminates name
    // collisions like "the nethermancer" vs "nethermancer".
    if (validTarget && sendCommand) {
      sendCommand(`${cmd.key} ${selectedEntity.name}`)
      return
    }
    // If this command needs input, prefer the friendly prompt modal
    const promptDef = getPromptForCommand(cmd.key)
    if (cmd.args_hint && promptDef && onPrompt && typeof promptDef === 'object') {
      onPrompt(promptDef)
      return
    }
    // Commands with no args fire immediately
    if (!cmd.args_hint && sendCommand) {
      sendCommand(cmd.key)
      return
    }
    // Fallback: inject into the input box
    const text = cmd.args_hint ? `${cmd.key} ` : cmd.key
    onClick(text)
  }

  // Show the resolved target on the button when one is selected, so the
  // player can see exactly who their click will hit.
  const argsDisplay = validTarget
    ? `→ ${selectedEntity.name}`
    : cmd.args_hint

  return (
    <div
      className={`cmd-entry cmd-enabled${validTarget ? ' cmd-has-target' : ''}`}
      onClick={handleClick}
    >
      <span className="cmd-arrow">›</span>
      <span className="cmd-key">{cmd.label || cmd.key}</span>
      {argsDisplay && (
        <span className="cmd-args">{argsDisplay}</span>
      )}
    </div>
  )
}

export default function CommandSidebar({ availableCommands, inCombat, myTurn, onCommandClick, onPrompt, sendCommand, onEquip, onShop, onCrafting, characterSkills = {}, selectedEntity = null }) {
  const commands = buildCommandList(inCombat, characterSkills)

  // Merge server-pushed contextual commands (repair, reagents, etc.) into
  // the list. The "__crafting_ui__" descriptor is consumed by App.jsx to
  // toggle the onCrafting callback, so we skip it here.
  //
  // Defensive filter: Combat-category commands only appear when actually
  // in combat. The server already gates this in world/available_commands.py
  // but we double-check on the frontend so any stale loop state on the
  // server can't surface combat options outside of fights.
  const serverCmds = (availableCommands || []).filter(c => {
    if (!c.key || c.key === '__crafting_ui__') return false
    if (commands.some(x => x.key === c.key)) return false
    if (!inCombat && (c.category || '').toLowerCase() === 'combat') return false
    return true
  })
  commands.push(...serverCmds)

  const groups = groupCommands(commands)

  return (
    <aside className="cmd-sidebar panel panel-decorated">
      <div className="cmd-sidebar-header">
        <span className="cinzel cmd-sidebar-title">COMMANDS</span>
      </div>

      {inCombat && (
        <div className={`combat-banner ${myTurn ? 'my-turn' : 'waiting'}`}>
          {myTurn ? <span>YOUR TURN</span> : <span>WAITING...</span>}
        </div>
      )}

      <div className="cmd-sidebar-body">
        {/* Special action buttons */}
        {onEquip && (
          <div className="cmd-category">
            <div className="cmd-category-header cinzel">Equipment</div>
            <div className="cmd-category-list">
              <div className="cmd-entry cmd-enabled cmd-equip-btn" onClick={onEquip}>
                <span className="cmd-arrow">›</span>
                <span className="cmd-key">Equip / Unequip</span>
              </div>
              {onShop && (
                <div className="cmd-entry cmd-enabled" onClick={onShop}>
                  <span className="cmd-arrow">›</span>
                  <span className="cmd-key">Shop / Trade</span>
                </div>
              )}
              {onCrafting && (
                <div className="cmd-entry cmd-enabled" onClick={onCrafting}>
                  <span className="cmd-arrow">›</span>
                  <span className="cmd-key">Crafting</span>
                </div>
              )}
            </div>
          </div>
        )}

        {Object.entries(groups).map(([category, cmds]) => (
          <div key={category} className="cmd-category">
            <div className="cmd-category-header cinzel">{category}</div>
            <div className="cmd-category-list">
              {cmds.map((cmd) => (
                <CommandEntry
                  key={cmd.key}
                  cmd={cmd}
                  onClick={onCommandClick}
                  onPrompt={onPrompt}
                  sendCommand={sendCommand}
                  selectedEntity={selectedEntity}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="cmd-sidebar-footer">
        <span className="cmd-footer-text">✦ ─── ✦ ─── ✦</span>
      </div>
    </aside>
  )
}
