#!/bin/bash
set -e

cd /app

PORT=${PORT:-8080}

echo "=== Running database migrations ==="
evennia migrate --no-input

echo "=== Starting Evennia ==="
evennia start

echo "=== Waiting for Evennia WebSocket on port 4002 ==="
for i in $(seq 1 30); do
    if nc -z localhost 4002 2>/dev/null; then
        echo "    WebSocket ready."
        break
    fi
    sleep 1
done

echo "=== Configuring nginx on port $PORT ==="
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
            proxy_pass http://localhost:4002;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection \$connection_upgrade;
            proxy_set_header Host \$host;
            proxy_set_header Origin \$http_origin;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_read_timeout 86400;
            proxy_connect_timeout 10s;
        }
    }
}
NGINXCONF

nginx

echo "=== All services running ==="
tail -f /dev/null
