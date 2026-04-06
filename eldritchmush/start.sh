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
# at_initial_setup.py creates admin account (id=1) from ADMIN_USERNAME/ADMIN_PASSWORD
# Evennia exits non-zero when no TTY for superuser prompt — ignore that exit code
evennia migrate --no-input || true

echo "=== Starting Evennia ==="
evennia start || true

echo "=== All services running ==="
tail -f /dev/null
