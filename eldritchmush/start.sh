#!/bin/bash
set -e

cd /app

PORT=${PORT:-8080}

echo "=== Running database migrations ==="
evennia migrate --no-input

echo "=== Starting Evennia (WebSocket on 127.0.0.1:4002) ==="
evennia start

echo "=== Waiting for Evennia WebSocket ==="
for i in $(seq 1 30); do
    if nc -z 127.0.0.1 4002 2>/dev/null; then
        echo "    Ready."
        break
    fi
    sleep 1
done

echo "=== Starting nginx on port $PORT -> 127.0.0.1:4002 ==="
cat > /etc/nginx/nginx.conf << NGINXCONF
events { worker_connections 1024; }
http {
    map \$http_upgrade \$connection_upgrade {
        default upgrade;
        ''      close;
    }
    server {
        listen ${PORT};
        location / {
            proxy_pass http://127.0.0.1:4002;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection \$connection_upgrade;
            proxy_set_header Host \$host;
            proxy_read_timeout 86400;
        }
    }
}
NGINXCONF

nginx -t && nginx

echo "=== All services running ==="
tail -f /dev/null
