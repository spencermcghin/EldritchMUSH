"""
Lightweight JSON endpoints used by the React frontend.
"""
from django.http import JsonResponse


def webclient_session(request):
    """
    Returns the Django session key and authenticated username for the
    current request. The React frontend calls this immediately on
    mount; if `authenticated` is true it appends `csessid` to the
    WebSocket URL so Evennia's webclient handler auto-puppets the
    user's character without needing a manual `connect user pass`.

    Always returns 200 — an unauthenticated session is a valid
    response (front end falls back to manual login).
    """
    # Force the session to exist so it has a key we can return.
    if not request.session.session_key:
        request.session.save()

    user = request.user
    return JsonResponse({
        "authenticated": bool(user.is_authenticated),
        "csessid": request.session.session_key,
        "username": user.username if user.is_authenticated else None,
    })
