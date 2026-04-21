import { getPromptForCommand } from '../data/commandPrompts'
import './CommandSidebar.css'

// Always-available commands (no skill required)
const ALWAYS_COMMANDS = [
  { key: 'look', label: 'Look', args_hint: '', category: 'Exploration' },
  { key: 'inventory', label: 'Inventory', args_hint: '', category: 'General' },
  { key: 'charsheet', label: 'Char Sheet', args_hint: '', category: 'General' },
  { key: 'say', label: 'Say', args_hint: '<message>', category: 'Social' },
  { key: 'emote', label: 'Emote', args_hint: '<action>', category: 'Social' },
  { key: 'who', label: 'Who', args_hint: '', category: 'General' },
  { key: 'help', label: 'Help', args_hint: '[<topic>]', category: 'General' },
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

function CommandEntry({ cmd, onClick, onPrompt, sendCommand }) {
  const handleClick = () => {
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

  return (
    <div className="cmd-entry cmd-enabled" onClick={handleClick}>
      <span className="cmd-arrow">›</span>
      <span className="cmd-key">{cmd.label || cmd.key}</span>
      {cmd.args_hint && (
        <span className="cmd-args">{cmd.args_hint}</span>
      )}
    </div>
  )
}

export default function CommandSidebar({ availableCommands, inCombat, myTurn, onCommandClick, onPrompt, sendCommand, onEquip, onShop, onCrafting, characterSkills = {} }) {
  const commands = buildCommandList(inCombat, characterSkills)

  // Merge server-pushed contextual commands (repair, reagents, etc.) into
  // the list. The "__crafting_ui__" descriptor is consumed by App.jsx to
  // toggle the onCrafting callback, so we skip it here.
  const serverCmds = (availableCommands || []).filter(c =>
    c.key && c.key !== '__crafting_ui__' && !commands.some(x => x.key === c.key)
  )
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
