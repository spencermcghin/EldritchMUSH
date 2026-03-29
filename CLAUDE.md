# EldritchMUSH — CLAUDE.md

> AI assistant guide for the EldritchMUSH codebase. Read this before making any changes.

---

## Project Overview

**EldritchMUSH** is a text-based MUSH (Multi-User Shared Hallucination) game built on the **Evennia** framework — a Python/Django MUD engine. Players connect via a MUD client (port 4000) or a browser-based web client (port 4001).

- **Framework:** Evennia (Python, Django ORM under the hood)
- **Database:** SQLite (`eldritchmush/server/evennia.db3`)
- **Server name:** `eldritchmush`
- **Genre:** Dark fantasy / survival MUSH with turn-based combat

---

## Repository Structure

```
EldritchMUSH/
├── CLAUDE.md                     # This file
├── eldritchmush/                 # Main game directory (all game code lives here)
│   ├── commands/                 # All player/admin commands
│   │   ├── command.py            # Core commands — ~2959 lines, most gameplay logic
│   │   ├── combat.py             # High-level combat commands (BattlefieldCommander, Rally, Targets)
│   │   ├── combat_commands/      # Individual combat maneuvers (one file per action)
│   │   │   ├── chirurgery.py     # Advanced healing
│   │   │   ├── cleave.py         # AoE melee attack
│   │   │   ├── disarm.py         # Disarm opponent
│   │   │   ├── disengage.py      # Exit combat loop
│   │   │   ├── drag.py           # Drag incapacitated characters
│   │   │   ├── medicine.py       # Field medicine
│   │   │   ├── shoot.py          # Ranged attack
│   │   │   ├── skip.py           # Skip turn
│   │   │   ├── stagger.py        # Stagger opponent
│   │   │   ├── strike.py         # Basic melee attack
│   │   │   ├── stun.py           # Stun opponent
│   │   │   └── sunder.py         # Sunder armor/weapons
│   │   ├── alchemy.py            # CmdBrew, CmdReagents, CmdAddReagent (apothecary system)
│   │   ├── blacksmith.py         # CmdForge — smithing commands
│   │   ├── combatant.py          # Combatant mixin helpers
│   │   ├── crafting.py           # CmdCraft, CmdRepair
│   │   ├── default_cmdsets.py    # All CmdSet definitions — register commands here
│   │   ├── dice.py               # CmdDice — dice rolling
│   │   ├── fortunestrings.py     # Fortune machine flavor text
│   │   ├── inventory_helper.py   # Inventory display utilities
│   │   └── npc.py                # CmdCreateNPC, CmdEditNPC, CmdNPC (admin)
│   ├── typeclasses/              # Evennia typeclass definitions
│   │   ├── accounts.py           # Account typeclass
│   │   ├── channels.py           # Channel typeclass
│   │   ├── characters.py         # Player Character — all stats initialized here
│   │   ├── exits.py              # Exit typeclass
│   │   ├── npc.py                # NPC typeclass with AI — ~1085 lines
│   │   ├── objects.py            # Item/weapon/crafting station typeclasses; ConsumableObject, ApothecaryWorkbench
│   │   ├── rooms.py              # Room types (Room, WeatherRoom, MarketRoom, ChargenRoom) — ~613 lines
│   │   └── scripts.py            # Evennia scripts (timers, recurring tasks)
│   ├── world/                    # Game data and systems
│   │   ├── batch_cmds.ev         # Evennia batch commands for world building
│   │   ├── combat_loop.py        # Turn-based combat loop management
│   │   ├── prototypes.py         # Item/weapon/armor templates — ~1330 lines, 100+ items
│   │   ├── alchemy_prototypes.py # All 66 alchemical substance prototypes (levels 1-3)
│   │   ├── reagents.py           # Reagent definitions — 32 reagents with rarities
│   │   ├── reset.py              # World reset logic
│   │   └── rules.py              # Combat formulas (legacy — newer logic is in commands/)
│   ├── server/
│   │   ├── conf/
│   │   │   ├── settings.py       # Main Evennia settings (SERVERNAME, port overrides)
│   │   │   ├── secret_settings.py # Secret/local overrides — gitignored
│   │   │   ├── at_initial_setup.py
│   │   │   ├── at_server_startstop.py
│   │   │   └── connection_screens.py
│   │   └── logs/                 # Server logs
│   └── web/                      # Django/Evennia web interface
│       ├── static_overrides/     # Custom static files (override Evennia defaults here)
│       ├── template_overrides/   # Custom HTML templates
│       └── urls.py               # URL routing
└── evennia/                      # Evennia library — do NOT modify files here
```

---

## Development Environment

### Starting the Server

All `evennia` commands run from inside the `eldritchmush/` subdirectory:

```bash
cd eldritchmush/

evennia start        # Start server (MUD on :4000, web on :4001)
evennia stop         # Stop server
evennia reload       # Hot-reload Python code without dropping connections
evennia migrate      # Apply Django database migrations (run after model changes)
evennia shell        # Django shell with full Evennia context
```

### Connecting

- **MUD client:** `localhost:4000` (Telnet/MUD protocol)
- **Web client:** `http://localhost:4001`
- On first `evennia start`, create a superuser — this becomes the in-game admin/wizard account.

### In-Game Admin Commands (superuser only)

```
@reload              # Reload code (same as evennia reload from shell)
@spawn <PROTO_KEY>   # Spawn item from prototypes.py
@py <expression>     # Run arbitrary Python in-game
@objects             # List all database objects
@examine <obj>       # Inspect object and its db attributes
@set obj/attr = val  # Directly set an object attribute
@dig RoomName = exit,back   # Create a new room with exits
@typeclass obj = typeclasses.rooms.WeatherRoom  # Change typeclass
```

---

## Core Evennia Concepts

| Concept | Description |
|---------|-------------|
| **Typeclass** | Python class backed by a database row (Character, Room, Object, NPC, Exit) |
| **CmdSet** | A named group of Commands attached to a typeclass or room |
| **Command** | Class with `key`, `aliases`, `locks`, `help_category`, and `func()` |
| **`db.` attribute** | Persistent data on any object: `self.db.attr = value` |
| **Script** | Timer or event-driven task attached to an object |
| **Prototype** | Dict template used with `@spawn` to instantiate items |

---

## Character System

### Stats (`typeclasses/characters.py:at_object_creation`)

All stats are Evennia `db` attributes. They are **only set at character creation** — changes to defaults do not affect existing characters in the database.

```python
# Core survival
self.db.body = 3            # Hit points (base 3)
self.db.total_body = 3
self.db.av = 0              # Armor value (from equipped armor)
self.db.bleed_points = 3    # Points before entering bleeding state
self.db.death_points = 3    # Points before death

# Combat skills
self.db.master_of_arms = 0
self.db.tough = 0
self.db.armor_specialist = 0
self.db.resilience = 0
self.db.melee = 0
self.db.resist = 0
self.db.cleave = 0
self.db.disarm = 0
self.db.sunder = 0
self.db.stagger = 0
self.db.stun = 0

# Weapon proficiencies
self.db.melee_weapons = 0
self.db.archer = 0
self.db.gunner = 0
self.db.shields = 0

# Crafting skills
self.db.blacksmith = 0
self.db.artificer = 0
self.db.bowyer = 0
self.db.gunsmith = 0
self.db.alchemist = 0

# Healing skills
self.db.stabilize = 0
self.db.medicine = 0
self.db.battlefieldmedicine = 0
self.db.chirurgeon = 0

# Support skills
self.db.tracking = 0
self.db.perception = 0
self.db.influential = 0
self.db.espionage = 0

# Status effect flags
self.db.weakness = 0
self.db.fear = False
self.db.disease = False
self.db.poison = False
self.db.paralyze = False
self.db.sleep = False
```

### Hit Location System

```python
self.db.targetArray = ["torso", "torso", "right arm", "left arm", "right leg", "left leg"]
# 1 = functional, 0 = disabled/injured
self.db.right_arm = 1
self.db.left_arm = 1
self.db.right_leg = 1
self.db.left_leg = 1
self.db.torso = 1
```

### Equipment Slots

| Slot | Purpose |
|------|---------|
| `left_slot` / `right_slot` | Weapon hands (dual wielding supported) |
| `body_slot` | Body armor |
| `hand_slot` | Gloves/gauntlets |
| `foot_slot` | Footwear |
| `clothing_slot` | Clothing layer |
| `cloak_slot` | Cloak/cape |
| `kit_slot` | Utility kit |
| `arrow_slot` | Arrow ammunition |
| `bullet_slot` | Firearm ammunition |

---

## Combat System

### Turn-Based Loop (`world/combat_loop.py`)

1. A player issues a combat command → they are added to `room.db.combat_loop`
2. Their target is auto-added to the loop
3. Turn order is determined by position in the list
4. After each action resolves, the turn passes to the next combatant
5. Combatants are removed on death, disengage, or body ≤ 0

Every `Room` instance initializes `self.db.combat_loop = []` in `at_object_creation`.

### Combat Commands

| Command | File | Effect |
|---------|------|--------|
| `strike` | `combat_commands/strike.py` | Basic melee attack |
| `shoot` | `combat_commands/shoot.py` | Ranged attack (requires ammo in slot) |
| `cleave` | `combat_commands/cleave.py` | AoE melee |
| `disarm` | `combat_commands/disarm.py` | Knock weapon from target |
| `stagger` | `combat_commands/stagger.py` | Stagger target |
| `stun` | `combat_commands/stun.py` | Stun target |
| `sunder` | `combat_commands/sunder.py` | Damage target's armor/weapon |
| `disengage` | `combat_commands/disengage.py` | Exit combat (usable while bleeding) |
| `skip` | `combat_commands/skip.py` | Pass turn |
| `drag` | `combat_commands/drag.py` | Move an incapacitated character |
| `medicine` | `combat_commands/medicine.py` | Field heal |
| `chirurgery` | `combat_commands/chirurgery.py` | Advanced healing (requires chirurgeon skill) |

### Status States

| State | Condition | Effect |
|-------|-----------|--------|
| Bleeding | `bleed_points` depleted | Can only use `disengage` |
| Dying | `death_points` depleted | Cannot act; can be `drag`ged |
| Unconscious | `sleep == True` | Cannot act |
| Dead | `body ≤ 0` + no `death_points` | Removed from game |

---

## Item System

### Prototypes (`world/prototypes.py`)

Items are defined as Python dicts. Spawn in-game with `@spawn PROTOTYPE_KEY`. 100+ items defined.

```python
IRON_SWORD = {
    "key": "iron sword",
    "typeclass": "typeclasses.objects.Weapon",
    "desc": "A basic iron sword.",
    "db.weapon_type": "sword",
    "db.damage": 3,
    "db.tier": 1,
}
```

### Tiers

| Tier | Weapon Label | Armor Label |
|------|-------------|-------------|
| 0 | Small | Light |
| 1 | Medium | Medium |
| 2 | Large | Heavy |
| 3 | Great | Plate |
| 4 | Legendary | Legendary |

---

## Crafting System

### Stations and Commands

| Station (object) | CmdSet | Commands Available |
|-----------------|--------|-------------------|
| Forge | `BlacksmithCmdSet` | `forge`, `craft`, `repair` |
| Artificer Workbench | `CrafterCmdSet` | `craft`, `repair` |
| Bowyer Workbench | `CrafterCmdSet` | `craft`, `repair` |
| Gunsmith Workbench | `CrafterCmdSet` | `craft`, `repair` |
| Apothecary Workbench | `ApothecaryWorkbenchCmdSet` | `brew` |

Crafting station objects have their CmdSet attached in `typeclasses/objects.py`. Commands become available when a player is in the same room as the station.

### Alchemy System (`commands/alchemy.py`)

Alchemists brew consumable substances at an **Apothecary Workbench** object (`typeclasses.objects.ApothecaryWorkbench`). The system is skill-gated:

| Alchemist Level | Brews |
|----------------|-------|
| 1 | Level 1 substances only |
| 2 | Level 1–2 substances |
| 3 | Level 1–3 substances |

**Requirements to brew:**
- `alchemist` skill ≥ substance level
- Apothecary Kit equipped in `kit_slot` (`kit.db.type == "apothecary"`, `kit.db.uses > 0`)
- Required reagents present in `caller.db.reagents` (a `{name: qty}` dict)

**Substance types:** Apotheca, Poison, Drug (66 recipes total in `world/alchemy_prototypes.py`).

**Prototype fields** (all alchemy prototypes have `craft_source = "apothecary"`):
```python
{
    "key": "blade oil",
    "typeclass": "typeclasses.objects.ConsumableObject",
    "craft_source": "apothecary",
    "substance_type": "Apotheca",
    "level": 1,
    "qty_produced": 2,
    "effect": "Weapon coated gains +1 damage for 1 combat.",
    "reagent_1": "Sayge", "reagent_1_qty": 2,
    "reagent_2": "Crow Feather", "reagent_2_qty": 1,
    ...
}
```

**Reagents** (`world/reagents.py`): 32 named reagents with descriptions and rarities (Common, Uncommon, Rare, Loot Drop, Black Market). Stored on characters as `self.db.reagents = {"Sayge": 3, ...}`.

**Commands:**
- `brew <substance name>` — brew at a workbench (requires skill, kit, reagents)
- `reagents` — display your reagent inventory
- `addreagent <name> = <qty>` — staff command (Builder+) to give reagents to yourself

**Output typeclass:** `ConsumableObject` — stores `substance_type`, `level`, `effect`, `craft_source`, `value` on `db`; `return_appearance()` shows effect/type/level/value to the looker.

### Resources

- **Materials:** `iron_ingots`, `refined_wood`, `leather`, `cloth`
- **Currency:** `gold`, `silver`, `copper`
- **Ammunition:** `arrows`, `bullets`
- **Reagents:** stored in `char.db.reagents` dict (not physical inventory items)

---

## World Structure

### Room Types (`typeclasses/rooms.py`)

| Class | Approx. Count | Purpose |
|-------|---------------|---------|
| `Room` | 46 | Standard room |
| `WeatherRoom` | 8 | Outdoor rooms with weather tick messages |
| `MarketRoom` | 2 | Trading/marketplace areas |
| `ChargenRoom` | 1 | Character creation — uses `ChargenCmdset` |

### Key Locations

- Tavern (main hall, office, kitchen)
- Marketplace & Maker's Hollow
- The Docks
- Field areas (multiple)
- Eastern/Western Cabins
- Old Road (north/south)
- Crossroads
- Raven's Rest Graveyard

**World totals (last audit):** ~57 rooms, ~120 exits, 8 player characters

---

## NPC System (`typeclasses/npc.py`)

- Custom `Npc` typeclass (~1085 lines)
- AI triggered via `at_char_entered()` hook when a player enters the room
- Following/leadership mechanics for NPCs and players
- Admin NPC commands (`CmdCreateNPC`, `CmdEditNPC`, `CmdNPC`) live in `commands/npc.py` and are registered in `AccountCmdSet` — superuser only

---

## Command Sets Reference (`commands/default_cmdsets.py`)

| CmdSet | Attached To | Key Commands |
|--------|-------------|--------------|
| `CharacterCmdSet` | `Character` typeclass | All combat, inventory, social, healing commands; also `reagents` |
| `AccountCmdSet` | `Account` typeclass | `createnpc`, `editnpc`, `npc`, `addreagent` |
| `ChargenCmdset` | `ChargenRoom` room | All `Set*` skill selection commands including `SetAlchemist` |
| `RoomCmdSet` | All `Room` instances (default) | `perception`, `tracking` |
| `BlacksmithCmdSet` | Forge objects | `forge`, `craft`, `repair` |
| `CrafterCmdSet` | Workbench objects | `craft`, `repair` |
| `ApothecaryWorkbenchCmdSet` | Apothecary Workbench objects | `brew` |

---

## Key Conventions

### Adding a New Command

1. Write the command class (in an appropriate file under `commands/`):

   ```python
   from evennia import Command

   class CmdFoo(Command):
       key = "foo"
       aliases = ["f"]
       locks = "cmd:all()"
       help_category = "Combat"  # Combat, Crafting, General, etc.

       def func(self):
           self.caller.msg("You did foo.")
   ```

2. Import and register in `commands/default_cmdsets.py` in the appropriate CmdSet:

   ```python
   from commands.myfile import CmdFoo
   # inside the CmdSet's at_cmdset_creation():
   self.add(CmdFoo())
   ```

3. Reload: `evennia reload` from shell, or `@reload` in-game.

### Adding a New Character Stat

1. Add `self.db.stat_name = default_value` in `typeclasses/characters.py:at_object_creation()`
2. **Important:** This only applies to newly created characters. Migrate existing characters via `@py`:
   ```
   @py [ch.db.stat_name = 0 for ch in evennia.search_object("*", typeclass="typeclasses.characters.Character")]
   ```

### Adding a New Item Prototype

1. Add a dict to `world/prototypes.py` with a unique all-caps key
2. Spawn in-game: `@spawn PROTOTYPE_KEY`

### Adding a New Room Type

1. Subclass `Room` (or another room type) in `typeclasses/rooms.py`
2. Override `at_object_creation()` to add CmdSets or attributes, and `return_appearance()` for custom display
3. Change an existing room's typeclass in-game: `@typeclass here = typeclasses.rooms.MyNewRoom`

### Evennia Patterns

```python
# Persistent attribute access
self.db.attr_name           # read
self.db.attr_name = value   # write

# Messaging
self.caller.msg("text")                        # to the command caller
self.caller.location.msg_contents("text")      # broadcast to room
target.msg("text")                             # to a specific object

# Evennia color codes (ANSI)
"|r" red   "|g" green   "|y" yellow   "|b" blue   "|w" white   "|n" reset
"|R" bright red   "|G" bright green   "|W" bright white

# Searching
self.caller.search("sword")                    # search caller's location
evennia.search_object("key", typeclass="...")  # global search
```

---

## Configuration

| File | Purpose |
|------|---------|
| `eldritchmush/server/conf/settings.py` | Main settings (SERVERNAME, ports, installed apps) |
| `eldritchmush/server/conf/secret_settings.py` | Local overrides — **gitignored, never commit** |
| `eldritchmush/server/evennia.db3` | SQLite database — **gitignored, never commit** |

Default ports: **4000** (MUD protocol), **4001** (web/Django)

---

## Development Priorities

### Priority 1 — Content Expansion
- More enemy NPC types (currently only "zombie" exists in the database)
- Quest system with tracking, objectives, and rewards
- More craftable items: consumables, special ammo, unique legendaries
- Basic shops in the Marketplace

### Priority 2 — Balance & Polish
- Combat tuning (damage formulas, status effect duration and interaction)
- Economy balancing (resource spawn rates, crafting costs vs. loot value)
- Healing vs. damage balance testing
- Help text for every command (`help_category` and docstrings)

### Priority 3 — New Features
- **Magic system** — `SetWyldingHand` hook exists in `ChargenCmdset`, needs full implementation
- Faction/guild system with reputation
- Advanced crafting: item quality levels, enchanting, recipe discovery
- Weather effects on gameplay (WeatherRooms already tick, effects need wiring)
- Social systems: reputation, player housing, gambling

### Priority 4 — Technical
- Web interface enhancements (Evennia Django templates in `web/template_overrides/`)
- Admin item spawner and NPC controller UI
- Combat log improvements and better error messages
- Expanded NPC AI behavior trees

---

## Web Frontend (Planned)

Evennia's built-in web server (`eldritchmush/web/`) is the fastest path to a browser interface. Extend it by:

- **Templates:** `web/template_overrides/` (override Evennia's Django templates)
- **Static files:** `web/static_overrides/` (CSS, JS, images)
- **URL routes:** `web/urls.py`

A richer standalone frontend (React/Vue + WebSocket) is also planned. The visual design system uses a dark parchment aesthetic with the following palette:

```css
--primary-dark:   #1a1a1a   /* Deep black backgrounds */
--primary-medium: #2d2d2d   /* Card backgrounds */
--accent-gold:    #d4af37   /* Wax stamp gold */
--accent-blood:   #8b0000   /* Combat/danger */
--text-light:     #e8e8e8   /* Primary text */
--text-aged:      #c9b899   /* Parchment-like secondary text */
```

Art assets (banners, item cards, wax stamps, creature art, faction art) are stored in the project's Google Drive repository.

---

## Common Pitfalls

- **Never modify files inside `evennia/`** — that is the upstream library. Always override via typeclasses and settings.
- **`at_object_creation()` runs only once.** Changing default stat values won't affect existing database objects. Use `@py` or a migration script to update them.
- **CmdSet priority conflicts** — if two CmdSets define a command with the same key, the higher-priority set wins. Check for collisions when adding new commands.
- **`evennia reload` is sufficient** for most code changes. Only restart fully (`evennia stop && evennia start`) when changing `settings.py` or installing new Python packages.
- **Prototype keys must be globally unique** — duplicate keys cause `@spawn` to behave unpredictably.
- **SQLite has no row-level locking** — avoid bulk write scripts that bypass the ORM; use Evennia's `utils.delay` or management commands for batch operations.
