# EldritchMUSH — developer commands
#
#   make dev         — first-time setup (venv, deps, migrate)
#   make server      — start Evennia server (foreground)
#   make frontend    — start vite dev (foreground)
#   make reload      — hot-reload server code
#   make stop        — stop everything
#   make migrate     — apply Django migrations
#   make seed        — idempotent world build (populate_mistvale.py)
#   make playtest    — run Python smoke harness
#   make playtest-ui — run Playwright UI harness (crafting-modal scenario)
#   make logs        — tail Evennia + portal logs
#   make clean       — remove venv, node_modules (nuclear)
#
# Convention: every target assumes you've already run `make dev` once.

VENV        := .venv
PY          := $(VENV)/bin/python
EVENNIA     := $(VENV)/bin/evennia
GAME_DIR    := eldritchmush
FRONTEND    := frontend
UI_HARNESS  := .claude/skills/playtest/ui
PYTHON_BIN  := /opt/homebrew/opt/python@3.11/bin/python3.11

.PHONY: dev server frontend reload stop migrate seed playtest playtest-ui logs clean help

help:
	@awk 'BEGIN{FS=" — "} /^# +make / {print $$0}' Makefile | sed 's/^# *//'

# First-time setup. Idempotent: re-running just re-verifies.
dev: $(VENV) $(FRONTEND)/node_modules $(UI_HARNESS)/node_modules
	cd $(GAME_DIR) && ../$(EVENNIA) migrate
	@echo ""
	@echo "Dev env ready. Next:"
	@echo "  make server      # in one terminal"
	@echo "  make frontend    # in another terminal"
	@echo "  open http://localhost:3000"

$(VENV):
	$(PYTHON_BIN) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip wheel
	$(VENV)/bin/pip install -r $(GAME_DIR)/requirements.txt

$(FRONTEND)/node_modules:
	cd $(FRONTEND) && npm install

$(UI_HARNESS)/node_modules:
	cd $(UI_HARNESS) && npm install
	cd $(UI_HARNESS) && npx playwright install chromium

server:
	cd $(GAME_DIR) && ../$(EVENNIA) start

frontend:
	cd $(FRONTEND) && npm run dev

reload:
	cd $(GAME_DIR) && ../$(EVENNIA) reload

stop:
	-cd $(GAME_DIR) && ../$(EVENNIA) stop
	-kill $$(lsof -tiTCP:3000 2>/dev/null) 2>/dev/null || true

migrate:
	cd $(GAME_DIR) && ../$(EVENNIA) migrate

# Run populate_mistvale.py — creates rooms, NPCs, canon tags, etc.
# Idempotent: existing objects are updated, not duplicated.
seed:
	cd $(GAME_DIR) && ../$(PY) -u -c "\
import os, django; \
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.settings'); \
django.setup(); \
exec(open('world/populate_mistvale.py').read())"

playtest:
	cd $(GAME_DIR) && ../$(EVENNIA) shell --command "\
import sys; sys.path.insert(0, '../.claude/skills/playtest'); \
from playtest import Harness; \
h = Harness(); \
h.run_scenario('crafting-modal'); \
h.teardown()"

playtest-ui:
	@if [ -z "$$PLAYTEST_USER" ]; then echo "export PLAYTEST_USER and PLAYTEST_PASS first"; exit 1; fi
	cd $(UI_HARNESS) && node playtest-ui.mjs crafting-modal

logs:
	tail -F $(GAME_DIR)/server/logs/server.log $(GAME_DIR)/server/logs/portal.log

clean:
	rm -rf $(VENV) $(FRONTEND)/node_modules $(UI_HARNESS)/node_modules
