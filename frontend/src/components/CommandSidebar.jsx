import './CommandSidebar.css'

// Default commands shown before OOB data arrives
const DEFAULT_COMMANDS = [
  { key: 'look', label: 'Look', args_hint: '', category: 'Exploration', enabled: true },
  { key: 'inventory', label: 'Inventory', args_hint: '', category: 'General', enabled: true },
  { key: 'charsheet', label: 'Char Sheet', args_hint: '', category: 'General', enabled: true },
  { key: 'strike', label: 'Strike', args_hint: '<target>', category: 'Combat', enabled: false, reason: 'Not in combat' },
  { key: 'shoot', label: 'Shoot', args_hint: '<target>', category: 'Combat', enabled: false, reason: 'Not in combat' },
  { key: 'cleave', label: 'Cleave', args_hint: '', category: 'Combat', enabled: false, reason: 'Not in combat' },
  { key: 'disarm', label: 'Disarm', args_hint: '<target>', category: 'Combat', enabled: false, reason: 'Not in combat' },
  { key: 'stagger', label: 'Stagger', args_hint: '<target>', category: 'Combat', enabled: false, reason: 'Not in combat' },
  { key: 'stun', label: 'Stun', args_hint: '<target>', category: 'Combat', enabled: false, reason: 'Not in combat' },
  { key: 'sunder', label: 'Sunder', args_hint: '<target>', category: 'Combat', enabled: false, reason: 'Not in combat' },
  { key: 'skip', label: 'Skip Turn', args_hint: '', category: 'Combat', enabled: false, reason: 'Not in combat' },
  { key: 'disengage', label: 'Disengage', args_hint: '', category: 'Combat', enabled: false, reason: 'Not in combat' },
  { key: 'medicine', label: 'Medicine', args_hint: '<target>', category: 'Healing', enabled: true },
  { key: 'chirurgery', label: 'Chirurgery', args_hint: '<target>', category: 'Healing', enabled: true },
  { key: 'brew', label: 'Brew', args_hint: '<substance>', category: 'Alchemy', enabled: true },
  { key: 'reagents', label: 'Reagents', args_hint: '', category: 'Alchemy', enabled: true },
  { key: 'browse', label: 'Browse', args_hint: '[<merchant>]', category: 'Shop', enabled: true },
  { key: 'buy', label: 'Buy', args_hint: '<item> from <merchant>', category: 'Shop', enabled: true },
  { key: 'sell', label: 'Sell', args_hint: '<item> to <merchant>', category: 'Shop', enabled: true },
  { key: 'forge', label: 'Forge', args_hint: '<recipe>', category: 'Crafting', enabled: true },
  { key: 'craft', label: 'Craft', args_hint: '<recipe>', category: 'Crafting', enabled: true },
  { key: 'repair', label: 'Repair', args_hint: '<item>', category: 'Crafting', enabled: true },
  { key: 'say', label: 'Say', args_hint: '<message>', category: 'General', enabled: true },
  { key: 'emote', label: 'Emote', args_hint: '<action>', category: 'General', enabled: true },
  { key: 'who', label: 'Who', args_hint: '', category: 'General', enabled: true },
  { key: 'help', label: 'Help', args_hint: '[<topic>]', category: 'General', enabled: true },
]

const CATEGORY_ORDER = ['Combat', 'Healing', 'Alchemy', 'Crafting', 'Shop', 'Exploration', 'General']

function groupCommands(commands) {
  const groups = {}
  for (const cmd of commands) {
    const cat = cmd.category || 'General'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(cmd)
  }
  // Sort by defined order
  const sorted = {}
  for (const cat of CATEGORY_ORDER) {
    if (groups[cat]) sorted[cat] = groups[cat]
  }
  // Append any unknown categories
  for (const cat of Object.keys(groups)) {
    if (!sorted[cat]) sorted[cat] = groups[cat]
  }
  return sorted
}

function CommandEntry({ cmd, onClick }) {
  const handleClick = () => {
    if (!cmd.enabled) return
    const text = cmd.args_hint ? `${cmd.key} ` : cmd.key
    onClick(text)
  }

  return (
    <div
      className={`cmd-entry ${cmd.enabled ? 'cmd-enabled' : 'cmd-disabled'}`}
      onClick={handleClick}
      title={!cmd.enabled && cmd.reason ? cmd.reason : undefined}
    >
      <span className="cmd-arrow">{cmd.enabled ? '›' : ' '}</span>
      <span className="cmd-key">{cmd.label || cmd.key}</span>
      {cmd.args_hint && (
        <span className="cmd-args">{cmd.args_hint}</span>
      )}
      {!cmd.enabled && cmd.reason && (
        <span className="cmd-reason" title={cmd.reason}>✕</span>
      )}
    </div>
  )
}

export default function CommandSidebar({ availableCommands, inCombat, myTurn, onCommandClick }) {
  const commands = availableCommands.length > 0 ? availableCommands : DEFAULT_COMMANDS
  const groups = groupCommands(commands)

  return (
    <aside className="cmd-sidebar panel panel-decorated">
      <div className="cmd-sidebar-header">
        <span className="cinzel cmd-sidebar-title">COMMANDS</span>
      </div>

      {/* Combat status banner */}
      {inCombat && (
        <div className={`combat-banner ${myTurn ? 'my-turn' : 'waiting'}`}>
          {myTurn ? (
            <span>⚔ YOUR TURN</span>
          ) : (
            <span>⏳ WAITING...</span>
          )}
        </div>
      )}

      <div className="cmd-sidebar-body">
        {Object.entries(groups).map(([category, cmds]) => (
          <div key={category} className="cmd-category">
            <div className="cmd-category-header cinzel">{category}</div>
            <div className="cmd-category-list">
              {cmds.map((cmd) => (
                <CommandEntry
                  key={cmd.key}
                  cmd={cmd}
                  onClick={onCommandClick}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Decorative footer */}
      <div className="cmd-sidebar-footer">
        <span className="cmd-footer-text">✦ ─── ✦ ─── ✦</span>
      </div>
    </aside>
  )
}
