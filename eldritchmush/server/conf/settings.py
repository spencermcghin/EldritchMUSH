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
# imports. Critical for processes like twistd (which boots the
# Evennia portal) that don't always pick up .pth-based entries.
import os as _os
import sys as _sys

_paths_to_add = ["/app"]
try:
    _derived = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    _paths_to_add.append(_derived)
except Exception:
    pass

for _p in _paths_to_add:
    if _p and _os.path.isdir(_p) and _p not in _sys.path:
        _sys.path.insert(0, _p)

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!
import os as _os_early

# Deploy environment identifier. Railway sets RAILWAY_ENVIRONMENT_NAME
# automatically (prod, uat). Local dev defaults to "local".
DEPLOY_ENV = _os_early.environ.get(
    "RAILWAY_ENVIRONMENT_NAME",
    _os_early.environ.get("DEPLOY_ENV", "local"),
).lower()

# Server identity — env-overridable so uat shows up distinctly in logs,
# the Evennia server headers, and the welcome screen.
SERVERNAME = _os_early.environ.get(
    "SERVERNAME",
    "eldritchmush" + ("" if DEPLOY_ENV in ("prod", "production", "local") else f"-{DEPLOY_ENV}"),
)

# Use the standard Django admin instead of Evennia's custom override.
# The custom override at /admin/ requires the evennia_admin.html template,
# which on some deployments isn't picked up correctly and 404s. The
# standard Django admin works out of the box and gives us full access
# to the Sites object (needed for allauth), AccountDB, ObjectDB, etc.
EVENNIA_ADMIN = False

# Multi-character mode: each Account can own multiple Characters and
# must explicitly puppet one with `ic <name>`. The React frontend's
# CharacterSelect screen handles the choice; new players use
# `charcreate <name>` to spawn a fresh body in the ChargenRoom.
MULTISESSION_MODE = 2
AUTO_PUPPET_ON_LOGIN = False
MAX_NR_CHARACTERS = 5

# Allowed hosts for Django. Comma-separated ALLOWED_HOSTS env var is
# merged with the per-env defaults below so adding a new domain in the
# Railway UI doesn't require a code change. Always includes localhost
# so the local dev server works without any env setup.
_default_hosts = [
    "eldritchmush-production.up.railway.app",
    "eldritchmush.com",
    "www.eldritchmush.com",
    "localhost",
    "127.0.0.1",
]
_env_hosts = [h.strip() for h in _os_early.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]
ALLOWED_HOSTS = sorted(set(_default_hosts + _env_hosts))

# Reverse-proxy / CSRF settings.
# Django runs behind nginx (which is behind Railway's edge proxy), so it
# sees requests as coming from 127.0.0.1 over HTTP. Without these
# settings, CSRF verification fails on every POST (admin login,
# allauth flows, etc.) because Django thinks the request origin is
# 127.0.0.1 but the form came from the public HTTPS URL.
_default_csrf_origins = [
    "https://eldritchmush-production.up.railway.app",
    "https://eldritchmush.com",
    "https://www.eldritchmush.com",
    "http://eldritchmush.com",
    "http://www.eldritchmush.com",
    "http://localhost:3000",
    "http://localhost:4001",
]
_env_csrf = [o.strip() for o in _os_early.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]
CSRF_TRUSTED_ORIGINS = sorted(set(_default_csrf_origins + _env_csrf))
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

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

# NOTE: We deliberately do NOT register a local Django app here.
# Twistd's portal subprocess fails to import any local package
# referenced in INSTALLED_APPS — find_spec succeeds but Django's
# import_module fails inside django.setup(), and we burned multiple
# rounds chasing it (sys.path injection in settings.py, .pth files,
# PYTHONPATH export in start.sh, package renames). The OAuth signal
# handler is wired up via a side-effect import in web/urls.py
# instead, which Django loads via ROOT_URLCONF after django.setup()
# has already completed. The signal only needs to fire on OAuth
# callbacks (which themselves go through web/urls.py), so loading
# order is guaranteed.

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
    # Force allauth to build callback URLs with https://. Twisted's
    # HTTP layer in front of Django doesn't always pass through the
    # X-Forwarded-Proto header that nginx sends, so Django thinks
    # the request is http and allauth builds an http:// callback URL,
    # which Google rejects with redirect_uri_mismatch.
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

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

######################################################################
# Env-var override for the Django SECRET_KEY. This takes precedence
# over any value set in secret_settings.py so that Railway (and any
# other container deploy where secret_settings.py isn't present) can
# supply the key via DJANGO_SECRET_KEY without a code change.
######################################################################
_env_secret_key = _os_early.environ.get("DJANGO_SECRET_KEY")
if _env_secret_key:
    SECRET_KEY = _env_secret_key
