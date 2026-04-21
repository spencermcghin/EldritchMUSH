---
name: playtest
description: Autonomously exercise EldritchMUSH features server-side before the user logs in. Drives a superuser test character through scripted commands + OOB events, then reports broken paths. Use when the user says something like "playtest the crafting UI" or "make sure <feature> still works before I try it".
---

# playtest — autonomous smoke-test harness

You are testing EldritchMUSH feature paths before the user joins the game. The goal is to catch Python exceptions, missing prototypes, broken OOB dispatch, and basic logic errors **server-side**, so when the user logs in they don't hit something obviously broken.

There are two harnesses:

1. **Python harness** (`playtest.py`) — drives the game engine directly, no browser. Fast, catches server-side bugs, but cannot see the UI.
2. **Playwright UI harness** (`ui/playtest-ui.mjs`) — drives a headless Chromium through the real web client. Slower, but produces screenshots and catches actual UI bugs.

**Default to the Python harness first** — it's 10× faster and catches most regressions. Escalate to the UI harness only when you need to verify the frontend actually renders the payload correctly (modals, tabs, button states).

### What the Python harness verifies
- commands resolve and don't raise
- OOB handlers (`__crafting_ui__`, `__craft_item__`, `__shop_ui__`, etc.) return well-formed event payloads
- room/NPC/object references that features depend on actually exist
- no new tracebacks appear in `server/logs/server.log`, `portal.log`, or `/data/diag.log`

### What the UI harness verifies
- login flow works
- sidebar buttons appear in the right contexts
- modals open, tabs switch, recipes render
- catches browser `console.error` + `pageerror` events
- produces PNG screenshots at each step you can `Read` to eyeball

## How to run

The harness lives at `.claude/skills/playtest/playtest.py`. It runs inside Evennia's Django context — no network calls, no telnet. It reads/writes the live DB, so:

- **Do not run destructive scenarios on production.** The harness creates a persistent `Playtester` character and can mutate inventory/stats.
- **Preferred:** start the local server first (`cd eldritchmush && evennia start`) so logs stream, then run scenarios.

### The `evennia shell --cmd` incantation

```bash
cd eldritchmush
evennia shell --cmd "
import sys
sys.path.insert(0, '../.claude/skills/playtest')
from playtest import Harness, SCENARIOS
h = Harness()
try:
    h.run_scenario('crafting-modal')
finally:
    h.teardown()
"
```

That prints a step-by-step trace ending in `PASS` or `FAIL`. Exceptions land in the trace as `EXCEPTION: ...` and any new tracebacks scraped from the log files are dumped at the end.

### Ad-hoc exploration

For a feature that doesn't have a pre-baked scenario, drive the harness directly:

```bash
evennia shell --cmd "
import sys; sys.path.insert(0, '../.claude/skills/playtest')
from playtest import Harness
h = Harness()
print(h.run('look'))
print(h.run_oob('__crafting_ui__'))
# goto a room
from evennia import search_object
r = search_object('Ironhaven Forge')
if r: h.char.move_to(r[0], quiet=True)
print(h.run_oob('__crafting_ui__'))
h.teardown()
"
```

`h.run(cmd)` = text command, returns stdout as string. `h.run_oob(cmd)` = routes through the `text` inputfunc (where custom OOB handlers like `__crafting_ui__` live), returns `{"text": [...], "events": [...]}`.

## Workflow for a playtest request

1. **Understand the feature surface.** Look at what the user last changed (recent commits, open files) or ask what they want covered. Feature ≠ whole game — keep it focused.
2. **Pick or add a scenario.** Check `SCENARIOS` in `playtest.py`. If nothing fits, add a new entry — a list of `("cmd"|"oob"|"goto"|"assert", ...)` tuples. Keep it to <15 steps; longer scenarios hide failures.
3. **Start the server if it isn't already up.**
   ```bash
   cd eldritchmush && evennia start  # idempotent
   ```
4. **Run the scenario.** Use the `evennia shell --cmd` incantation above.
5. **If it fails:** read the trace. `EXCEPTION` lines point at a Python error (stack trace included). `!!` on a step means that step tripped a check (exception, `|400` error color, empty payload, etc.). New tracebacks in server logs are shown at the end.
6. **Triage, don't fix-from-memory.** If the failure is in code you last touched, read the file at the line number before editing. If the failure is in code you haven't touched, tell the user — don't speculate.
7. **Report concisely.** "Scenario `crafting-modal` passed. Tabs rendered for all 5 skills. No new tracebacks." Or: "Failed at step 3 (`__craft_item__ IRON_MEDIUM_WEAPON`) — `KeyError: 'kit_slot'` in `crafting_ui.py:112`. Full trace: ..."

## Building new scenarios

Add entries to `SCENARIOS` at the bottom of `playtest.py`. Step types:

| step | args | meaning |
|------|------|---------|
| `cmd` | `"look"` | run a text command via `execute_cmd` |
| `oob` | `"__crafting_ui__"` | route through the inputfunc text handler |
| `goto` | `"Ironhaven Forge"` | teleport the tester to a room by key |
| `assert` | `"look", "Crafter's"` | run the probe command, fail if needle isn't in output |

Write scenarios that **cover the path a player would take**, not just the handler. e.g. for the crafting modal: goto the room, invoke `__crafting_ui__`, assert a tab for that skill appears in events, then invoke `__craft_item__ <KEY>` and assert the item lands in inventory.

## Common gotchas

- **Prototype keys are case-sensitive** for Evennia's spawner — use UPPERCASE (`IRON_MEDIUM_WEAPON`, not lowercase).
- **OOB handlers expect stripped, lowercased input** in `inputfuncs.py`. `h.run_oob("__Crafting_UI__")` will not match.
- **Superuser bypass** — the `Playtester` character has `Developer` permission, so skill gates, recipe-knowledge gates, and material checks are bypassed in many handlers. Tests should still exercise the logic; if a handler has a `is_superuser` shortcut, note in your report that the non-SU path wasn't tested.
- **`evennia shell` vs `evennia shell --cmd`** — the `--cmd` variant runs and exits; the bare command opens an interactive REPL. The harness is designed for `--cmd`.
- **Server state persists** — if the tester ends up bleeding, dead, or in combat from a previous run, teleport them back to the Crafter's Quarter at the start of the next scenario. `goto` does this.

## UI harness (Playwright + headless Chromium)

The UI harness lives at `.claude/skills/playtest/ui/`. It launches a
real headless browser, logs in through the live frontend, drives the
React UI, and dumps screenshots you can `Read` back.

### One-time setup (already done on this machine)

- `brew install node` + `brew install --cask google-chrome`
- `python3.11 -m venv .venv && .venv/bin/pip install -r eldritchmush/requirements.txt`
- `.venv/bin/evennia migrate`
- Playtester account created (see credentials below), character puppeted,
  skills/materials/recipes granted
- `cd frontend && npm install`
- `cd .claude/skills/playtest/ui && npm install && npx playwright install chromium`

### Known quirks patched in this repo

- `server/conf/inputfuncs.py` — direct-dispatch workaround for `ic` and
  `ooc` (same pattern as the `charcreate` workaround). Without this,
  the account-level cmdhandler never routes to `CmdIC.func()` and
  puppet clicks silently fail.
- `frontend/vite.config.js` — proxies `/api`, `/accounts`, `/admin`,
  and `/websocket` through to Evennia on :4001/:4002 so Django session
  cookies ride along with REST + WS.

### Authentication

Two paths depending on how the user signs in:

**Google OAuth (default for this project):**
OAuth cannot be automated headlessly. Run a one-time interactive setup:

```bash
cd .claude/skills/playtest/ui
node playtest-ui.mjs setup-auth
```

A visible Chrome window opens. User clicks the Google button, completes
sign-in, and waits for the game UI to load. Cookies + localStorage are
saved to `auth-state.json` (gitignored). All future runs reuse that
session headlessly.

If the saved session expires (Google session cookies eventually die),
re-run `setup-auth`. The script detects auth failure on the next run
and prints a clear error.

**Username/password fallback (for local/dev accounts):**
```bash
export PLAYTEST_USER='<name>'
export PLAYTEST_PASS='<password>'
```

**Other env vars:**
```bash
# optional — which character to puppet on the select screen (default: Aethel)
export PLAYTEST_CHARACTER='Aethel'
# optional override — defaults auto-detect vite 5173 then evennia 4001
export PLAYTEST_URL='http://localhost:5173'
```

### Prereqs before a run

1. Venv activated (it's at repo root): `source .venv/bin/activate`
2. Game server up: `cd eldritchmush && evennia start` (or `evennia reload`)
3. Frontend up: `cd frontend && npm run dev` (vite @ :3000, proxies `/api`, `/admin`, `/accounts`, `/websocket` through to Evennia)

The `Playtester` character is pre-provisioned with Developer perms, all
crafting skills at level 3, all materials stocked, and a handful of
known recipes. It lives in `The Crafter's Quarter`. Teleport via
`@tel #<dbref>` in scenarios — room dbrefs after populate:

| Room | dbref |
|------|-------|
| The Crafter's Quarter | #2054 |
| Ironhaven Forge | #2078 |
| The Back Alley | #2058 |

### Run a scenario

```bash
cd .claude/skills/playtest/ui
node playtest-ui.mjs crafting-modal
```

Screenshots land in `.claude/skills/playtest/ui/screenshots/` as
`<scenario>-<step>.png`. Read them with the `Read` tool to actually see
what rendered.

### Built-in UI scenarios

| scenario | what it does |
|---|---|
| `login` | Log in, screenshot the post-login view |
| `crafting-modal` | Teleport to Crafter's Quarter → click Crafting → snap each tab + detail panel |
| `crafting-ironhaven` | Teleport to Ironhaven Forge → open modal (Richter gunsmith shop) |
| `crafting-docks` | Teleport to The Back Alley → open modal (Rourke smuggler) |

Add more inside the `SCENARIOS` object in `playtest-ui.mjs`. Each is a
function `(page) => Promise<void>` that runs AFTER login + character
select. Use `snap(page, 'name')` to save a screenshot at any checkpoint.

### Interpreting UI results

Exit 0 = PASS. Non-zero = FAIL with the error printed. Always check:

- Any `console.error` / `pageerror` logged at the end — those are
  JS runtime bugs the React app hit during the run.
- The `99-failure.png` screenshot if the run failed — shows what was
  on screen when it broke.
- That the tab count / recipe count in the screenshots matches what
  the backend should push.

When a screenshot is useful for the user, `Read` it and describe what
you see concretely ("5 tabs: Blacksmith / Bowyer / Artificer / Gunsmith
/ Alchemy. Blacksmith tab selected, 34 recipes listed under Level 0
and 1 headers, 'Iron Medium Weapon' selected in detail panel showing
Iron Ingots 2/N and Refined Wood 1/N").

## When NOT to use this

- Balance questions (damage formulas, economy) — needs a human loop.
- Anything that requires a live multiplayer interaction.

For those, tell the user explicitly: "I can't verify this from here."
