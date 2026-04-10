"""
EldritchMUSH custom Django app.

Holds the AppConfig + signal handlers that bootstrap server-side
behavior we layer on top of Evennia (currently: allauth signal
plumbing for Google OAuth account creation).

This package is intentionally NOT named `web` to avoid name shadowing
with whatever lives at sys.path[0] in the twistd subprocess on some
Python images, where `import_module('web.apps')` was failing even
though `find_spec('web')` resolved to /app/web/__init__.py correctly.
"""
