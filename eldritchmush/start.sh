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
# DJANGO_SUPERUSER_* env vars allow non-interactive superuser creation during migrate
export DJANGO_SUPERUSER_USERNAME="${ADMIN_USERNAME:-admin}"
export DJANGO_SUPERUSER_PASSWORD="${ADMIN_PASSWORD:-changeme}"
export DJANGO_SUPERUSER_EMAIL="${ADMIN_EMAIL:-admin@eldritchmush.com}"
# Disable set -e here: Evennia's initial setup exits non-zero when no TTY for
# superuser prompt, which would kill the script before our account creation runs
set +e
evennia migrate --no-input
set -e

# Create admin account if not already present
if [ -n "$ADMIN_USERNAME" ] && [ -n "$ADMIN_PASSWORD" ]; then
    echo "=== Creating/verifying admin account: $ADMIN_USERNAME ==="
    evennia shell -c "
import sys
try:
    from evennia.accounts.models import AccountDB
    from django.contrib.auth.hashers import make_password
    if not AccountDB.objects.filter(id=1).exists():
        acct = AccountDB(
            id=1,
            username='${ADMIN_USERNAME}',
            email='${ADMIN_EMAIL:-admin@eldritchmush.com}',
            is_superuser=True,
            is_staff=True,
        )
        acct.password = make_password('${ADMIN_PASSWORD}')
        acct.save()
        print('Admin account created with id=1: ${ADMIN_USERNAME}')
    else:
        print('Admin account (id=1) already exists')
except Exception as e:
    print('Warning: could not create admin account:', e, file=sys.stderr)
" || echo "Warning: admin account creation failed, continuing anyway"
fi

echo "=== Starting Evennia ==="
# Disable set -e so evennia start failure doesn't kill the container
set +e
evennia start
EVENNIA_EXIT=$?
set -e

if [ $EVENNIA_EXIT -ne 0 ]; then
    echo "ERROR: evennia start failed with exit code $EVENNIA_EXIT — check logs above"
    echo "Keeping container alive for debugging..."
fi

echo "=== All services running ==="
tail -f /dev/null
