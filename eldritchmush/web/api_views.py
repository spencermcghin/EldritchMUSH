"""
Lightweight JSON endpoints used by the React frontend.
"""
from django.http import JsonResponse


def webclient_session(request):
    """
    Returns the Django session key and authenticated username for the
    current request. The React frontend calls this immediately on
    mount; if `authenticated` is true it appends `csessid` to the
    WebSocket URL so Evennia's webclient handler picks up the session.

    Always returns 200 — an unauthenticated session is a valid
    response (front end falls back to manual login).

    CRITICAL: this endpoint also injects two Evennia-specific keys
    into the Django session: `webclient_authenticated_uid` and
    `webclient_authenticated_nonce`. Evennia's portal webclient.py
    looks these up by csessid when a WebSocket connects, and ONLY
    marks the WebSocket session as logged in if both are present.
    Allauth (Google OAuth) sets `request.user` but never touches the
    Evennia-specific keys, so without this injection the WebSocket
    session stays unauthenticated, lands in UnloggedinCmdSet, and
    `charcreate` (and every other Account-level command) is silently
    dropped because UnloggedinCmdSet doesn't define them.
    """
    import random

    # Force the session to exist so it has a key we can return.
    if not request.session.session_key:
        request.session.save()

    user = request.user
    if user.is_authenticated:
        # Mirror what Evennia's built-in webclient login view does:
        # write the uid and a nonce into the Django session so the
        # WebSocket handshake can find them.
        existing_uid = request.session.get("webclient_authenticated_uid")
        if existing_uid != user.id:
            request.session["webclient_authenticated_uid"] = user.id
            request.session["webclient_authenticated_nonce"] = random.randint(0, 10**6)
            request.session.save()

    return JsonResponse({
        "authenticated": bool(user.is_authenticated),
        "csessid": request.session.session_key,
        "username": user.username if user.is_authenticated else None,
    })


def _archetype_for_character(char):
    """
    Best-effort guess at the character's primary archetype based on
    skill levels. Used purely for the CharacterSelect display — not
    authoritative game state. Returns a friendly label or None.
    """
    candidates = [
        ("Soldier", char.db.tough or 0),
        ("Knight", char.db.battlefieldcommander or 0),
        ("Vigil", char.db.vigil or 0),
        ("Chirurgeon", char.db.chirurgeon or 0),
        ("Alchemist", char.db.alchemist or 0),
        ("Blacksmith", char.db.blacksmith or 0),
        ("Bowyer", char.db.bowyer or 0),
        ("Gunsmith", char.db.gunsmith or 0),
        ("Artificer", char.db.artificer or 0),
        ("Master of Arms", char.db.master_of_arms or 0),
        ("Sniper", char.db.sniper or 0),
        ("Espionage", char.db.espionage or 0),
        ("Influential", char.db.influential or 0),
    ]
    candidates.sort(key=lambda c: c[1], reverse=True)
    if candidates and candidates[0][1] > 0:
        return candidates[0][0]
    return None


def account_characters(request):
    """
    Returns the list of playable characters for the authenticated
    account, with enough metadata to render rich CharacterSelect cards.

    Response shape:
    {
        "authenticated": true,
        "characters": [
            {
                "name": "Spencer",
                "dbref": "#42",
                "body": 3,
                "total_body": 3,
                "av": 2,
                "location": "The Tavern",
                "archetype": "Soldier",
                "last_played": "2026-04-09T12:34:56Z" | null,
                "in_chargen": false
            },
            ...
        ]
    }
    """
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"authenticated": False, "characters": []})

    # Lazy import — avoids touching the Evennia model layer at module
    # import time (which can race with Django app loading).
    from evennia.objects.models import ObjectDB

    characters = []
    # AccountDB stores playable characters two ways: as the db_account FK
    # on each Character, and via the _playable_characters attribute. We
    # query by FK because it's authoritative.
    qs = ObjectDB.objects.filter(db_account=user)

    for char in qs:
        try:
            location = char.location
            location_name = location.key if location else "the void"
            in_chargen = False
            if location and "ChargenRoom" in (location.typeclass_path or ""):
                in_chargen = True

            characters.append({
                "name": char.key,
                "dbref": f"#{char.id}",
                "body": char.db.body if char.db.body is not None else 0,
                "total_body": char.db.total_body if char.db.total_body is not None else 0,
                "av": char.db.av or 0,
                "location": location_name,
                "archetype": _archetype_for_character(char),
                "last_played": char.db_date_created.isoformat() if char.db_date_created else None,
                "in_chargen": in_chargen,
            })
        except Exception as exc:
            print(f"[api_views] Error serializing character {char.id}: {exc}")
            continue

    return JsonResponse({
        "authenticated": True,
        "characters": characters,
    })
