# EldritchMUSH Web Client

A React frontend for EldritchMUSH — connecting to the Evennia game server via WebSocket. Dark fantasy aesthetic inspired by Mork Borg and medieval manuscripts, with vintage 80s CRT phosphor glow.

---

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

Opens at **http://localhost:3000**. The Evennia server must be running (`cd eldritchmush && evennia start`) with the WebSocket on port 4002.

Once the client connects, type `connect <username> <password>` in the command input to log in — same as any MUD client.

## Build for Production

```bash
npm run build    # outputs to dist/
npm run preview  # preview the production build
```

---

## Architecture

```
Browser (React)                    Evennia Server
─────────────────                  ──────────────
  useEvennia.js  ── WebSocket ──►  port 4002
       │              4002
       │
       ├─ text messages ──► GameOutput (ANSI color rendering)
       ├─ OOB events ────► CombatTracker, CommandSidebar, CharacterStatus
       └─ sendCommand() ──► [["text", ["strike zombie"], {}]]
```

### Evennia Protocol

All messages are JSON arrays of tuples:

| Direction | Format | Example |
|-----------|--------|---------|
| Server → Client (text) | `[["text", ["content"], {}]]` | `[["text", ["\|025You enter the tavern.\|n"], {}]]` |
| Server → Client (OOB) | `[["event", [], {payload}]]` | `[["event", [], {"type": "combat_hit", "damage": 2}]]` |
| Client → Server | `[["text", ["command"], {}]]` | `[["text", ["strike zombie"], {}]]` |

### OOB Event Types

The server emits structured JSON events that drive the UI panels:

| Event | Triggers | UI Update |
|-------|----------|-----------|
| `available_commands` | Room change, equip/unequip, combat state | CommandSidebar refreshes |
| `combat_start` | First attack in a room | CombatTracker appears |
| `combat_end` | Last combatant leaves loop | CombatTracker hides |
| `turn_change` | Turn advances | Sidebar banner + tracker highlight |
| `combat_hit` | Attack lands | Tracker HP bars drain, hit feed |
| `combat_miss` | Attack misses | Hit feed shows miss reason |
| `combat_disengage` | Player flees combat | Combatant removed from tracker |
| `character_bleed` | Bleed threshold crossed | CharacterStatus badge + red bar |
| `character_dying` | Death threshold crossed | CharacterStatus badge |

---

## Components

```
src/
├── main.jsx                     # React 18 entry point
├── App.jsx / App.css            # Root layout (3-column + header)
├── hooks/
│   └── useEvennia.js            # WebSocket lifecycle, message parsing, OOB state
├── utils/
│   └── ansiParser.js            # Evennia |r|g|025 color codes → React spans
└── components/
    ├── LoginScreen.jsx/.css     # Pre-connection screen
    ├── GameOutput.jsx/.css      # Scrollable message log + CRT scanlines
    ├── CombatTracker.jsx/.css   # Turn order, HP bars, hit feed
    ├── CommandSidebar.jsx/.css  # Context-aware command list
    ├── CharacterStatus.jsx/.css # HP/bleed/death bars, equipment, status tags
    └── CommandInput.jsx/.css    # Terminal prompt with history + tab completion
```

### LoginScreen
Gothic title in UnifrakturMaguntia with gold glow, animated rune border, host/port inputs. After connecting, reminds the player to type `connect <user> <pass>`.

### GameOutput
Renders the scrollable game text log. Parses Evennia ANSI color codes (`|r`, `|430`, `|025`, etc.) into styled spans. CRT scanline overlay via CSS `::after`. Auto-scrolls to bottom unless the user scrolls up to read history.

### CombatTracker
Only visible during combat. Pulsing blood-red header, turn-order list with HP bars that drain as `combat_hit` events arrive, "YOUR TURN" gold banner, and a feed of the last 3 combat events.

### CommandSidebar
Shows available commands grouped by category (Combat, Healing, Crafting, Shop, General, etc.). Starts with sensible defaults; replaced live when the server pushes `available_commands` OOB events. Disabled commands show strikethrough with a tooltip explaining why. Click any enabled command to inject it into the input bar.

### CharacterStatus
Right-side panel with HP / bleed / death point bars (color shifts at thresholds), armor value, equipment slots, and animated status badges (COMBAT, BLEEDING, DYING).

### CommandInput
Terminal-style `›` prompt. Supports command history (Up/Down arrows, 100 entries), Tab completion from the current available commands list, and click-to-inject from the sidebar.

---

## Design System

### Palette

| Variable | Hex | Usage |
|----------|-----|-------|
| `--void` | `#0a0807` | Deepest background |
| `--surface` | `#141210` | Panel backgrounds |
| `--parchment` | `#1e1a14` | Warm card surfaces |
| `--accent-gold` | `#d4af37` | Headers, loot, items |
| `--accent-blood` | `#8b0000` | Combat, danger |
| `--blood-bright` | `#cc2211` | Active combat indicator |
| `--neon-warn` | `#c9ff00` | Critical warnings (sparse) |
| `--phosphor` | `#00e5a0` | Terminal green glow |
| `--text-light` | `#e8e4d0` | Primary text |
| `--text-aged` | `#9a8266` | Secondary/dimmed |
| `--border` | `#2e2418` | Panel borders |

### Typography

| Font | Usage |
|------|-------|
| UnifrakturMaguntia | Game title / logo |
| Cinzel | Section headers, category labels |
| Share Tech Mono | All game output (monospace terminal) |
| Barlow Condensed | UI labels, buttons, status text |

### Animations

| Name | Effect |
|------|--------|
| `flicker` | Subtle brightness oscillation |
| `pulse-blood` | Pulsing red glow for combat |
| `fade-in` | Message entry animation |
| `scanline` | Moving CRT scanline sweep |
| `glow-gold` | Oscillating gold text glow |
| `blink-cursor` | Terminal cursor blink |

---

## Development

### Prerequisites
- Node.js 18+
- Evennia server running (`cd eldritchmush && evennia start`)

### Ports
| Service | Port |
|---------|------|
| React dev server | 3000 |
| Evennia MUD | 4000 |
| Evennia web | 4001 |
| Evennia WebSocket | 4002 |

### Adding New OOB Events

1. Emit from the server in Python:
   ```python
   from world.events import emit
   emit(room, "my_event", {"key": "value"})
   ```

2. Handle in `useEvennia.js` — add a case to the OOB event dispatcher.

3. Consume in a component via the state passed down from `App.jsx`.
