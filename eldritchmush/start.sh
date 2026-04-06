#!/bin/bash
set -e

cd /app

PORT=${PORT:-8080}

echo "=== Starting nginx on port $PORT (proxy to 127.0.0.1:4002 when ready) ==="
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
            proxy_pass http://127.0.0.1:4002;
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

echo "=== Running database migrations ==="
evennia migrate --no-input

# Auto-create superuser from env vars (errors here must NOT stop Evennia from starting)
if [ -n "$ADMIN_USERNAME" ] && [ -n "$ADMIN_PASSWORD" ]; then
    echo "=== Creating/verifying admin account: $ADMIN_USERNAME ==="
    cd /app/eldritchmush
    python manage.py shell -c "
import sys
try:
    from evennia.accounts.models import AccountDB
    from evennia.utils import create
    if not AccountDB.objects.filter(username='${ADMIN_USERNAME}').exists():
        acct = create.create_account('${ADMIN_USERNAME}', '${ADMIN_EMAIL:-admin@eldritchmush.com}', '${ADMIN_PASSWORD}', is_superuser=True)
        print('Admin account created: ${ADMIN_USERNAME}')
    else:
        print('Admin account already exists: ${ADMIN_USERNAME}')
except Exception as e:
    print('Warning: could not create admin account:', e, file=sys.stderr)
" || echo "Warning: admin account creation failed, continuing anyway"
    cd /app
fi

echo "=== Starting Evennia ==="
evennia start

echo "=== All services running ==="
tail -f /dev/null
