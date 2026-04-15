"""
Url definition file to redistribute incoming URL requests to django
views. Search the Django documentation for "URL dispatcher" for more
help.

"""
from django.urls import re_path as url, include, path
from django.contrib import admin

# default evennia patterns
from evennia.web.urls import urlpatterns

from web.api_views import (
    webclient_session, account_characters,
    admin_all_characters, admin_delete_character,
    admin_all_accounts, admin_set_role, admin_approve_character,
    npc_audit_log,
)
from web.diag import diag_view

# Side-effect import: connects OAuth signal handlers. Must happen
# AFTER django.setup() (we're guaranteed that here because URL
# routing only fires post-setup) and BEFORE any OAuth callback can
# arrive (also guaranteed because the callback URL itself is in
# this file).
from web import oauth_signals  # noqa: F401

# eventual custom patterns. Anything we put here is prepended to
# Evennia's defaults, so our routes win on conflicts.
custom_patterns = [
    # Mount the standard Django admin explicitly at /admin/. Evennia's
    # website urls.py conditionally mounts it, but the route was
    # 404ing on Railway — bypassing the conditional with our own
    # explicit mount makes the admin reliably reachable.
    path("admin/", admin.site.urls),
    # JSON endpoints used by the React frontend
    path("api/webclient_session/", webclient_session, name="webclient_session"),
    path("api/account/characters/", account_characters, name="account_characters"),
    # Admin-only endpoints
    path("api/admin/characters/", admin_all_characters, name="admin_all_characters"),
    path("api/admin/delete-character/", admin_delete_character, name="admin_delete_character"),
    path("api/admin/accounts/", admin_all_accounts, name="admin_all_accounts"),
    path("api/admin/set-role/", admin_set_role, name="admin_set_role"),
    path("api/admin/approve-character/", admin_approve_character, name="admin_approve_character"),
    # Admin-only NPC conversation audit log. Shows recent AI NPC turns
    # with flags for banned-phrase hits, moderation flags, rate limits,
    # and LLM errors. See world/ai_safety.py for the log format.
    path("api/admin/npc-audit/", npc_audit_log, name="npc_audit_log"),
    # Diagnostic log viewer — visit /api/diag/ in a browser to read the
    # tail of /data/diag.log. Used to debug Railway log capture issues
    # where Evennia server stdout/server.log isn't being collected.
    path("api/diag/", diag_view, name="diag_view"),
]

# Mount allauth URLs only if django-allauth is installed. Defensive so
# the server boots even on environments without the optional dep.
try:
    import allauth  # noqa: F401
    custom_patterns.append(path("accounts/", include("allauth.urls")))
except ImportError:
    pass

# this is required by Django.
urlpatterns = custom_patterns + urlpatterns
