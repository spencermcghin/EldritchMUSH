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

# Ensure the game directory itself is on sys.path BEFORE any other
# imports. This matters for processes like twistd (which boots the
# Evennia portal) that don't pick up the .pth-based path entries used
# by the regular `evennia` CLI launcher. Without this, Django's
# INSTALLED_APPS would fail to import local app modules like
# `web.apps.WebAppConfig` during portal startup.
import os as _os
import sys as _sys
_GAME_DIR = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
if _GAME_DIR not in _sys.path:
    _sys.path.insert(0, _GAME_DIR)

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!
SERVERNAME = "eldritchmush"

# Multi-character mode: each Account can own multiple Characters and
# must explicitly puppet one with `ic <name>`. The React frontend's
# CharacterSelect screen handles the choice; new players use
# `charcreate <name>` to spawn a fresh body in the ChargenRoom.
MULTISESSION_MODE = 2
AUTO_PUPPET_ON_LOGIN = False
MAX_NR_CHARACTERS = 5

# Allowed hosts for Django — Railway internal + custom domain
ALLOWED_HOSTS = [
    "eldritchmush-production.up.railway.app",
    "eldritch-mud.com",
    "www.eldritch-mud.com",
    "localhost",
    "127.0.0.1",
]

# Evennia's WebSocket server runs on 4002 (default).
# nginx routes /websocket → 4002 and everything else → 4001 (HTTP proxy).
# Do NOT set WEBSOCKET_CLIENT_PORT = 4001 here — that would create a second
# TCP listener on 4001, conflicting with the Portal's HTTP proxy (also on 4001).


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
# django-allauth (Google OAuth) — optional dependency
######################################################################
# Allows players to sign in with Google. Wrapped in try/except so the
# server still boots if django-allauth isn't installed (e.g. fresh
# clone without `pip install django-allauth`). When allauth IS
# installed, the OAuth callback creates a real Evennia AccountDB row
# (allauth respects AUTH_USER_MODEL = "accounts.AccountDB"), and the
# React frontend's CharacterSelect screen handles puppeting.

# Always register the local web app so its signal handlers + URL
# routes load. The signal handler itself imports allauth lazily and
# fails-soft if it's missing.
INSTALLED_APPS = list(INSTALLED_APPS) + [
    "web.apps.WebAppConfig",
]

try:
    import allauth  # noqa: F401
    _allauth_available = True
except ImportError:
    _allauth_available = False
    print("[settings] django-allauth not installed — Google sign-in disabled. "
          "Run `pip install django-allauth[socialaccount]` to enable.")

if _allauth_available:
    INSTALLED_APPS = list(INSTALLED_APPS) + [
        "allauth",
        "allauth.account",
        "allauth.socialaccount",
        "allauth.socialaccount.providers.google",
    ]

    # allauth >=0.56 requires AccountMiddleware in MIDDLEWARE — without
    # it the AppConfig.ready() raises ImproperlyConfigured at boot.
    # Append rather than replace so we don't clobber Evennia's defaults.
    MIDDLEWARE = list(MIDDLEWARE) + [
        "allauth.account.middleware.AccountMiddleware",
    ]

    # Allauth uses Django's auth backends — keep ModelBackend so
    # username/password login still works as a fallback.
    AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
        "allauth.account.auth_backends.AuthenticationBackend",
    ]

    # Allauth account behavior
    ACCOUNT_EMAIL_VERIFICATION = "none"
    ACCOUNT_LOGIN_METHODS = {"username", "email"}
    ACCOUNT_SIGNUP_FIELDS = ["email*", "username*"]
    SOCIALACCOUNT_AUTO_SIGNUP = True
    SOCIALACCOUNT_LOGIN_ON_GET = True

    LOGIN_REDIRECT_URL = "/"
    ACCOUNT_LOGOUT_REDIRECT_URL = "/"

    # Pull OAuth client credentials from env vars first (Railway), then
    # fall back to local oauth_secrets.py (gitignored).
    _google_client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
    _google_client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "")
    if not _google_client_id or not _google_client_secret:
        try:
            from server.conf.oauth_secrets import (
                GOOGLE_OAUTH_CLIENT_ID as _google_client_id,
                GOOGLE_OAUTH_CLIENT_SECRET as _google_client_secret,
            )
        except ImportError:
            print("[settings] oauth_secrets.py not found and no env vars set — "
                  "Google sign-in will fail until credentials are configured.")

    SOCIALACCOUNT_PROVIDERS = {
        "google": {
            "APP": {
                "client_id": _google_client_id,
                "secret": _google_client_secret,
                "key": "",
            },
            "SCOPE": ["profile", "email"],
            "AUTH_PARAMS": {"access_type": "online"},
        },
    }

######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")
