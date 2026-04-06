#!/bin/bash
set -e

cd /app

echo "=== ENV: PORT=${PORT} (Railway-assigned port) ==="

echo "=== Running database migrations ==="
evennia migrate --no-input

echo "=== Starting Evennia (WebSocket on port ${PORT:-4002}) ==="
evennia start

echo "=== All services running ==="
tail -f /dev/null
