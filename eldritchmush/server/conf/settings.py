r"""
Evennia settings file.

The available options are found in the default settings file found
here:

/home/ubuntu/eldritch/evennia/evennia/settings_default.py

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

If you want to share your game dir, including its settings, you can
put secret game- or server-specific settings in secret_settings.py.

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!
SERVERNAME = "eldritchmush"

# Allowed hosts for Django — Railway internal + custom domain
ALLOWED_HOSTS = [
    "eldritchmush-production.up.railway.app",
    "eldritch-mud.com",
    "www.eldritch-mud.com",
    "localhost",
    "127.0.0.1",
]

# WebSocket port — nginx proxies from Railway's PORT to Evennia's web server
WEBSOCKET_CLIENT_PORT = 4001


######################################################################
# Database — use Railway Volume for persistence if available
######################################################################
import os

######################################################################
# Patch Evennia's create_superuser to work non-interactively.
# check_database() in evennia_launcher calls create_superuser() with
# interactive=True hardcoded. In a non-TTY env (Railway/Docker) this
# recurses infinitely. We replace it with a direct DB write using env vars.
######################################################################
def _patch_evennia_superuser():
    _username = os.environ.get("ADMIN_USERNAME")
    _password = os.environ.get("ADMIN_PASSWORD")
    _email = os.environ.get("ADMIN_EMAIL", "admin@eldritchmush.com")
    if not _username or not _password:
        return
    try:
        from evennia.server import evennia_launcher
        from django.contrib.auth.hashers import make_password

        def _create_superuser_noninteractive():
            from evennia.accounts.models import AccountDB
            if not AccountDB.objects.filter(id=1).exists():
                acct = AccountDB(
                    id=1,
                    username=_username,
                    email=_email,
                    is_superuser=True,
                    is_staff=True,
                )
                acct.password = make_password(_password)
                acct.save()
                print(f"[settings] Created Account #1: {_username}")

        evennia_launcher.create_superuser = _create_superuser_noninteractive
        print("[settings] Patched evennia_launcher.create_superuser for non-TTY deployment")
    except Exception as exc:
        print(f"[settings] Warning: could not patch create_superuser: {exc}")

_patch_evennia_superuser()

_volume_path = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "")
if _volume_path:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(_volume_path, "evennia.db3"),
        }
    }
    # Also persist server logs to the volume
    LOG_DIR = os.path.join(_volume_path, "logs")
    os.makedirs(LOG_DIR, exist_ok=True)
    SERVER_LOG_FILE = os.path.join(LOG_DIR, "server.log")
    PORTAL_LOG_FILE = os.path.join(LOG_DIR, "portal.log")
    HTTP_LOG_FILE = os.path.join(LOG_DIR, "http_requests.log")

######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")
