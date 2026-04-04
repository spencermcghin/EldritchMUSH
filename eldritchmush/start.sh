#!/bin/bash
set -e

cd /app

PORT=${PORT:-8080}

echo "=== Configuring nginx on port $PORT ==="
cat > /etc/nginx/nginx.conf << NGINXCONF
events { worker_connections 1024; }
http {
    server {
        listen ${PORT};

        location /health {
            return 200 "OK\n";
            add_header Content-Type text/plain;
        }

        location / {
            proxy_pass http://127.0.0.1:4002;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_read_timeout 86400;
        }
    }
}
NGINXCONF

nginx

echo "=== Running database migrations ==="
evennia migrate --no-input

echo "=== Starting Evennia ==="
evennia start

echo "=== All services running ==="
tail -f /dev/null
