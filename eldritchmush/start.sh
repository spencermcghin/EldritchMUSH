#!/bin/bash
set -e

cd /app

echo "=== Running database migrations ==="
evennia migrate --no-input

echo "=== Starting Evennia ==="
evennia start

echo "=== Evennia running, keeping container alive ==="
# tail -f /dev/null keeps the container alive indefinitely
tail -f /dev/null
