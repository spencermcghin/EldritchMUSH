#!/bin/bash
set -e

cd /app

# Export PYTHONPATH so every child process — including the twistd
# subprocess that boots Evennia's portal — has /app on sys.path.
# Without this, twistd's sys.path[0] becomes /usr/local/bin (the
# script's own directory) and local Django apps like eldritch_app
# fail to import during django.setup() in portal.py.
export PYTHONPATH="/app:${PYTHONPATH:-}"

PORT=${PORT:-8080}

echo "=== Starting nginx on port $PORT ==="
cat > /etc/nginx/nginx.conf << NGINXCONF
events { worker_connections 1024; }
http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
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
        # Evennia admin and API endpoints
        location /admin {
            proxy_pass http://127.0.0.1:4001;
            proxy_set_header Host \$host;
        }
        # Serve React frontend for everything else
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files \$uri \$uri/ /index.html;
        }
    }
}
NGINXCONF

nginx

# Ensure volume directory exists for persistent storage
if [ -n "$RAILWAY_VOLUME_MOUNT_PATH" ]; then
    echo "=== Using persistent volume at $RAILWAY_VOLUME_MOUNT_PATH ==="
    mkdir -p "$RAILWAY_VOLUME_MOUNT_PATH/logs"

    # Seed the volume with the baked-in db3 if no database exists yet,
    # or if FORCE_DB_SEED=1 is set (to replace a stale/empty db).
    # This copies the world data (rooms, NPCs, items, etc.) from the repo
    # so the deploy starts with the full game world intact.
    SHOULD_SEED=0
    if [ ! -f "$RAILWAY_VOLUME_MOUNT_PATH/evennia.db3" ]; then
        SHOULD_SEED=1
        echo "=== No database on volume — will seed ==="
    elif [ "${FORCE_DB_SEED:-0}" = "1" ]; then
        SHOULD_SEED=1
        echo "=== FORCE_DB_SEED=1 — replacing existing database ==="
    else
        echo "=== Existing database found on volume — skipping seed ==="
    fi

    if [ "$SHOULD_SEED" = "1" ]; then
        if [ -f /app/server/evennia.db3 ]; then
            echo "=== Seeding volume with baked-in evennia.db3 ==="
            cp /app/server/evennia.db3 "$RAILWAY_VOLUME_MOUNT_PATH/evennia.db3"
            echo "=== Database seeded ($(ls -lh "$RAILWAY_VOLUME_MOUNT_PATH/evennia.db3" | awk '{print $5}')) ==="
        else
            echo "=== No baked-in db3 found at /app/server/evennia.db3 — starting fresh ==="
        fi
    fi
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

# Update the django.contrib.sites Site object so allauth uses the
# correct domain when generating OAuth callback URLs. Override
# SITE_DOMAIN env var if you want a different domain.
echo "=== Configuring Site domain for allauth ==="
python3 -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.settings')
django.setup()
from django.contrib.sites.models import Site
domain = os.environ.get('SITE_DOMAIN', 'eldritchmush-production.up.railway.app')
name = os.environ.get('SITE_NAME', 'EldritchMUSH')
site, created = Site.objects.update_or_create(
    pk=1,
    defaults={'domain': domain, 'name': name},
)
action = 'created' if created else 'updated'
print(f'Site #1 {action}: domain={site.domain} name={site.name}')
" || echo "Warning: could not configure Site"

# Grant superuser to spencer_admin if the account exists
echo "=== Granting superuser to spencer_admin ==="
python3 -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.settings')
django.setup()
from evennia.accounts.models import AccountDB
try:
    acct = AccountDB.objects.get(username='spencer_admin')
    if not acct.is_superuser:
        acct.is_superuser = True
        acct.is_staff = True
        acct.save()
        print('spencer_admin granted superuser')
    else:
        print('spencer_admin already superuser')
except AccountDB.DoesNotExist:
    print('spencer_admin account not found yet')
" || echo "Warning: could not grant superuser"

echo "=== Starting Evennia ==="
# Kill any lingering Evennia processes from previous start attempts
evennia stop 2>/dev/null || true
sleep 2
fuser -k 4001/tcp 4002/tcp 4005/tcp 4006/tcp 2>/dev/null || true
sleep 1

# Stream Evennia's server and portal logs live to Docker stdout so errors are visible
LOGDIR="${RAILWAY_VOLUME_MOUNT_PATH}/logs"
touch "$LOGDIR/server.log" "$LOGDIR/portal.log" 2>/dev/null || true
tail -F "$LOGDIR/server.log" 2>/dev/null | sed 's/^/[server] /' &
tail -F "$LOGDIR/portal.log" 2>/dev/null | sed 's/^/[portal] /' &

# Run evennia start in the background — the launcher blocks indefinitely
# waiting for an AMP status reply that may never come in Docker.
evennia start 2>&1 &

# Wait for both Portal (4002 WebSocket) AND Server (4005 internal web) to be up.
echo "=== Waiting for Evennia to be ready ==="
for i in $(seq 1 150); do
    portal_up=0
    server_up=0
    nc -z 127.0.0.1 4002 2>/dev/null && portal_up=1
    nc -z 127.0.0.1 4005 2>/dev/null && server_up=1
    if [ $portal_up -eq 1 ] && [ $server_up -eq 1 ]; then
        echo "=== Evennia is fully up! (Portal+Server ready after ${i}x2s) ==="
        break
    fi
    echo "  waiting... portal=$portal_up server=$server_up ($i/150)"
    sleep 2
done

echo "=== All services running ==="
tail -f /dev/null
