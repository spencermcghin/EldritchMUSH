#!/bin/bash
set -e

cd /app

PORT=${PORT:-8080}

echo "=== Starting nginx on port $PORT ==="
cat > /etc/nginx/nginx.conf << NGINXCONF
events { worker_connections 1024; }
http {
    access_log /dev/stdout;
    error_log /dev/stderr;

    map \$http_upgrade \$connection_upgrade {
        default upgrade;
        ''      close;
    }
    server {
        listen ${PORT};
        location /health {
            return 200 "OK\n";
            add_header Content-Type text/plain;
        }
        # WebSocket connections go to Evennia's dedicated WS server (port 4002)
        location /websocket {
            proxy_pass http://127.0.0.1:4002;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection \$connection_upgrade;
            proxy_set_header Host \$host;
            proxy_read_timeout 3600s;
            proxy_send_timeout 3600s;
            proxy_connect_timeout 10s;
        }
        # Everything else (HTTP, Evennia web client, admin) → HTTP proxy (port 4001)
        location / {
            proxy_pass http://127.0.0.1:4001;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection \$connection_upgrade;
            proxy_set_header Host \$host;
            proxy_read_timeout 3600s;
            proxy_send_timeout 3600s;
            proxy_connect_timeout 10s;
        }
    }
}
NGINXCONF

nginx

# Ensure volume directory exists for persistent storage
if [ -n "$RAILWAY_VOLUME_MOUNT_PATH" ]; then
    echo "=== Using persistent volume at $RAILWAY_VOLUME_MOUNT_PATH ==="
    mkdir -p "$RAILWAY_VOLUME_MOUNT_PATH/logs"
else
    echo "=== WARNING: No volume mounted — database will be lost on redeploy ==="
fi

echo "=== Running database migrations ==="
evennia migrate --no-input || true

# Create Account id=1 BEFORE evennia start.
# check_database() in evennia_launcher.py does AccountDB.objects.get(id=1) and
# if not found, recursively calls create_superuser() which crashes in non-TTY.
# We must pre-create the account so check_database() passes immediately.
echo "=== Pre-creating Account #1 ==="
python3 -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.settings')
django.setup()
from evennia.accounts.models import AccountDB
from django.contrib.auth.hashers import make_password
username = os.environ.get('ADMIN_USERNAME', 'admin')
password = os.environ.get('ADMIN_PASSWORD', 'changeme123!')
email = os.environ.get('ADMIN_EMAIL', 'admin@eldritchmush.com')
if not AccountDB.objects.filter(id=1).exists():
    acct = AccountDB(id=1, username=username, email=email, is_superuser=True, is_staff=True)
    acct.password = make_password(password)
    acct.save()
    print(f'Account #1 created: {username}')
else:
    print('Account #1 already exists')
" || echo "Warning: could not pre-create Account #1"

echo "=== Starting Evennia ==="
# Kill any lingering Evennia processes from previous start attempts
evennia stop 2>/dev/null || true
sleep 2
fuser -k 4001/tcp 4002/tcp 4005/tcp 4006/tcp 2>/dev/null || true
sleep 1

# evennia start's wait_for_status_reply has no timeout — it hangs forever if
# the Server subprocess takes too long to signal readiness (common in Docker).
# Use timeout(1) to cap the launcher at 120s; Portal+Server subprocesses are
# already detached and keep running after the launcher exits.
timeout 120 evennia start 2>&1 || true

# Wait up to 120s for Evennia's WebSocket port (4002) to actually accept connections
echo "=== Waiting for Evennia to be ready ==="
for i in $(seq 1 60); do
    if nc -z 127.0.0.1 4002 2>/dev/null; then
        echo "=== Evennia is up (port 4002 open) ==="
        break
    fi
    echo "  waiting... ($i/60)"
    sleep 2
done

echo "=== All services running ==="
tail -f /dev/null
