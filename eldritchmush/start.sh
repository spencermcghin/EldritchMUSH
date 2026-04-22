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
        # Django routes — admin, allauth (OAuth), and our JSON API
        # endpoints all need to be proxied to Evennia's HTTP server
        # on port 4001. Without this, nginx serves the React SPA's
        # index.html for these paths and the requests never reach Django.
        location /admin {
            proxy_pass http://127.0.0.1:4001;
            proxy_set_header Host \$host;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        }
        location /accounts {
            proxy_pass http://127.0.0.1:4001;
            proxy_set_header Host \$host;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        }
        location /api {
            proxy_pass http://127.0.0.1:4001;
            proxy_set_header Host \$host;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        }
        location /static {
            proxy_pass http://127.0.0.1:4001;
            proxy_set_header Host \$host;
        }
        location /media {
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
#
# Refuse to boot if ADMIN_PASSWORD is unset when the account does not
# already exist — a hard-coded default would leave the initial superuser
# with a guessable password.
echo "=== Pre-creating Account #1 ==="
python3 -c "
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.settings')
django.setup()
from evennia.accounts.models import AccountDB
from django.contrib.auth.hashers import make_password
if AccountDB.objects.filter(id=1).exists():
    print('Account #1 already exists')
else:
    password = os.environ.get('ADMIN_PASSWORD')
    if not password:
        sys.stderr.write(
            'REFUSING TO BOOT: Account #1 does not exist and ADMIN_PASSWORD '
            'is not set. Set ADMIN_PASSWORD (and optionally ADMIN_USERNAME, '
            'ADMIN_EMAIL) on the environment and redeploy.\n'
        )
        sys.exit(1)
    if len(password) < 12:
        sys.stderr.write(
            'REFUSING TO BOOT: ADMIN_PASSWORD must be at least 12 characters.\n'
        )
        sys.exit(1)
    username = os.environ.get('ADMIN_USERNAME', 'admin')
    email = os.environ.get('ADMIN_EMAIL', 'admin@eldritchmush.com')
    acct = AccountDB(id=1, username=username, email=email, is_superuser=True, is_staff=True)
    acct.password = make_password(password)
    acct.save()
    print(f'Account #1 created: {username}')
" || exit 1

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

# Grant elevated perms to configured accounts. Config-driven, comma-
# separated:
#   SUPERUSER_USERNAMES=name1,name2     (promoted to is_superuser)
#   ADMIN_USERNAMES=name1,name2         (granted Admin permstring)
# Empty env var = no promotions at boot. Registering a username you
# know is listed in these vars before the legit operator does is
# therefore not a takeover vector — but it's still on the operator to
# run those with known-real usernames only.
echo "=== Granting configured admin roles ==="
python3 -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.settings')
django.setup()
from evennia.accounts.models import AccountDB

def _split(env):
    return [x.strip() for x in (os.environ.get(env, '') or '').split(',') if x.strip()]

for uname in _split('SUPERUSER_USERNAMES'):
    try:
        acct = AccountDB.objects.get(username=uname)
    except AccountDB.DoesNotExist:
        print(f'{uname}: account not found yet')
        continue
    if not acct.is_superuser:
        acct.is_superuser = True
        acct.is_staff = True
        acct.save()
        print(f'{uname}: granted superuser')
    else:
        print(f'{uname}: already superuser')

for uname in _split('ADMIN_USERNAMES'):
    try:
        acct = AccountDB.objects.get(username=uname)
    except AccountDB.DoesNotExist:
        print(f'{uname}: account not found yet')
        continue
    perms = list(acct.permissions.all())
    if 'Admin' not in perms:
        acct.permissions.add('Admin')
        print(f'{uname}: granted Admin role')
    else:
        print(f'{uname}: already has Admin role')
" || echo "Warning: could not grant admin roles"

# Repair AccountDB rows whose db_typeclass_path was never set to the
# proper typeclass. This happens when allauth creates accounts via a
# raw AccountDB.save(), bypassing Evennia's create_account() helper.
# The row ends up bound to evennia.accounts.models.AccountDB — the raw
# Django model — which has none of the typeclass hook methods
# (at_pre_login, at_post_login, at_disconnect, at_post_puppet), so
# every login crashes inside sessionhandler.login() and the React
# CharacterSelect screen hangs after the user clicks Begin.
#
# This used to live in at_server_startstop.at_server_start() but the
# hook's print output was not appearing in Railway logs (likely buffered
# or written somewhere we can't see), so we run it inline here BEFORE
# `evennia start` to guarantee it runs and prints visibly.
echo "=== Repairing OAuth account typeclass bindings ==="
python3 -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.settings')
django.setup()
from django.conf import settings as dj_settings
from evennia.accounts.models import AccountDB

target = getattr(dj_settings, 'BASE_ACCOUNT_TYPECLASS', 'typeclasses.accounts.Account')
expected_cmdset = getattr(dj_settings, 'CMDSET_ACCOUNT', 'commands.default_cmdsets.AccountCmdSet')
total = AccountDB.objects.count()
broken = list(AccountDB.objects.exclude(db_typeclass_path=target))

if not broken:
    print(f'[typeclass_repair] All {total} account(s) already bound to {target}.')
else:
    print(f'[typeclass_repair] Found {len(broken)}/{total} account(s) needing repair.')
    repaired = 0
    for acct in broken:
        old_path = acct.db_typeclass_path
        try:
            acct.set_class_from_typeclass(typeclass_path=target)
            acct.save()
            repaired += 1
            print(f'[typeclass_repair] Fixed {acct.username} ({old_path or \"NULL\"} -> {target})')
        except Exception as exc:
            print(f'[typeclass_repair] FAILED to repair {acct.username}: {exc}')
    print(f'[typeclass_repair] Done: {repaired}/{len(broken)} accounts fixed.')

# Second-stage repair: even with the right typeclass binding, allauth-
# created accounts skipped Evennia's at_first_save() and never had
# basetype_setup() run, which is what attaches the AccountCmdSet to
# the account's persistent cmdset_storage. Without it, OOC commands
# (charcreate, ic, ooc) silently don't exist for the WS session — the
# text frame arrives, the dispatcher finds no matching command, and
# nothing happens.
#
# We can't use cmdset.add_default() here because it broadcasts the
# change via SESSIONS.sessions_from_account(), and we're running
# BEFORE 'evennia start' so SESSIONS is None. Instead we write
# directly to db_cmdset_storage via the model property setter, which
# is what add_default() ultimately does for the persistent path.
print('[cmdset_repair] Checking accounts for missing AccountCmdSet...')
fixed_cmdset = 0
fixed_attrs = 0
checked = 0
all_accts = AccountDB.objects.all()
for acct in all_accts:
    checked += 1
    try:
        # cmdset_storage is a list-style property derived from the
        # comma-separated db_cmdset_storage CharField. Empty/missing
        # means basetype_setup() never ran for this account.
        current_storage = acct.cmdset_storage or []
        if expected_cmdset not in current_storage:
            print(f'[cmdset_repair] {acct.username}: cmdset_storage={current_storage!r} -> attaching {expected_cmdset}')
            new_storage = list(current_storage) + [expected_cmdset]
            # Property setter writes to db_cmdset_storage and saves,
            # without touching SESSIONS — safe pre-Evennia-start.
            acct.cmdset_storage = new_storage
            fixed_cmdset += 1
        # _playable_characters attribute is set by at_account_creation();
        # if it's missing, the charcreate command will choke when it
        # tries to append to None.
        if acct.attributes.get('_playable_characters', default=None) is None:
            acct.attributes.add('_playable_characters', [])
            fixed_attrs += 1
    except Exception as exc:
        print(f'[cmdset_repair] FAILED on {getattr(acct, \"username\", \"?\")}: {exc}')
print(f'[cmdset_repair] Checked {checked} accounts; fixed cmdset on {fixed_cmdset}, _playable_characters on {fixed_attrs}.')

# Third-stage repair: backfill PERMISSION_ACCOUNT_DEFAULT (Player) on
# accounts whose permissions list is empty. Diag confirmed spencer2
# had perms=[] which silently rejected cmd:pperm(Player) locks
# (charcreate, plus several other Account-level commands). Ours OAuth
# signal handler grants this perm only on the user_signed_up signal,
# which fires once at signup; pre-existing accounts created before
# that code existed never had perms granted.
default_perm = getattr(dj_settings, 'PERMISSION_ACCOUNT_DEFAULT', 'Player')
if isinstance(default_perm, str):
    perm_list = [p.strip() for p in default_perm.split(',') if p.strip()]
else:
    perm_list = list(default_perm)
print(f'[perm_repair] Checking accounts for missing default permissions {perm_list}...')
fixed_perms = 0
checked_perms = 0
for acct in AccountDB.objects.all():
    checked_perms += 1
    try:
        current_perms = list(acct.permissions.all()) if hasattr(acct, 'permissions') else []
        missing = [p for p in perm_list if p not in current_perms]
        if missing:
            print(f'[perm_repair] {acct.username}: perms={current_perms!r} -> adding {missing!r}')
            for p in missing:
                acct.permissions.add(p)
            fixed_perms += 1
    except Exception as exc:
        print(f'[perm_repair] FAILED on {getattr(acct, \"username\", \"?\")}: {exc}')
print(f'[perm_repair] Checked {checked_perms} accounts; granted default perms to {fixed_perms}.')
" || echo "Warning: account repair failed (non-fatal)"

# Build the Mistvale (reboot campaign) world. Idempotent — skips
# anything already created. Only runs if MISTVALE_BUILD=1 to allow
# admins to gate the migration while testing.
if [ "${MISTVALE_BUILD:-0}" = "1" ]; then
    echo "=== Building Mistvale world ==="
    cd /app
    # -u forces unbuffered stdout so Railway logs show populate progress
    # in real time instead of dumping everything at process exit.
    python3 -u -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.settings')
django.setup()
exec(open('/app/world/populate_mistvale.py').read())
" || echo "Warning: Mistvale build failed (non-fatal)"
fi

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
