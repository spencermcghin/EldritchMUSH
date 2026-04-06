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
