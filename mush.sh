#!/usr/bin/env bash
# EldritchMUSH — start/stop/status/reload helper
# Usage: ./mush.sh [start|stop|status|reload]
#
# All evennia commands require the venv bin in PATH so twistd resolves.

VENV="/home/user/eldritchenv"
GAME_DIR="$(cd "$(dirname "$0")/eldritchmush" && pwd)"
export PATH="$VENV/bin:$PATH"

CMD="${1:-status}"

cd "$GAME_DIR" || { echo "ERROR: game dir not found at $GAME_DIR"; exit 1; }

case "$CMD" in
  start)
    echo "Starting EldritchMUSH..."
    "$VENV/bin/evennia" start
    echo ""
    echo "  React UI  →  http://localhost:3000"
    echo "  Web client →  http://localhost:4001"
    echo "  MUD (telnet) →  localhost:4000"
    echo ""
    echo "Start the React UI separately:"
    echo "  cd frontend && npm run dev"
    ;;
  stop)
    "$VENV/bin/evennia" stop
    ;;
  reload)
    "$VENV/bin/evennia" reload
    ;;
  status)
    "$VENV/bin/evennia" status
    ;;
  shell)
    "$VENV/bin/evennia" shell
    ;;
  migrate)
    "$VENV/bin/evennia" migrate
    ;;
  *)
    echo "Usage: $0 [start|stop|status|reload|shell|migrate]"
    exit 1
    ;;
esac
