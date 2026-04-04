#!/bin/bash
set -e

cd /app

echo "=== Running database migrations ==="
evennia migrate --no-input

echo "=== Starting Evennia ==="
evennia start

echo "=== Server started, tailing logs ==="
# Keep container alive
mkdir -p server/logs
tail -f server/logs/server.log server/logs/portal.log 2>/dev/null &
TAIL_PID=$!

# Wait for either process to exit
wait $TAIL_PID
