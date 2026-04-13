"""
Lightweight JSON endpoints used by the React frontend.
"""
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


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
    from web.diag import diag_write

    # Force the session to exist so it has a key we can return.
    if not request.session.session_key:
        request.session.save()

    user = request.user
    diag_write(
        "webclient_session called",
        user_authenticated=user.is_authenticated,
        user_id=getattr(user, "id", None),
        session_key=request.session.session_key,
    )

    if user.is_authenticated:
        # Mirror what Evennia's built-in webclient login view does:
        # write the uid and a nonce into the Django session so the
        # WebSocket handshake can find them.
        existing_uid = request.session.get("webclient_authenticated_uid")
        existing_nonce = request.session.get("webclient_authenticated_nonce")
        diag_write(
            "webclient_session existing values",
            existing_uid=existing_uid,
            existing_nonce=existing_nonce,
            target_uid=user.id,
        )
        if existing_uid != user.id:
            request.session["webclient_authenticated_uid"] = user.id
            request.session["webclient_authenticated_nonce"] = random.randint(0, 10**6)
            request.session.save()
            diag_write(
                "webclient_session WROTE uid+nonce",
                uid=user.id,
                nonce=request.session["webclient_authenticated_nonce"],
                session_key=request.session.session_key,
            )
        else:
            diag_write("webclient_session uid already correct, skipped write")

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
    # Allauth-created accounts go through our CmdCharCreate which stores
    # characters in the _playable_characters Attribute (a list of Object
    # refs) but does NOT set the db_account FK on the Character row.
    # So we read from _playable_characters first, then fall back to the
    # db_account FK query for any legacy characters that may exist.
    from evennia.utils.utils import make_iter

    playable = []
    attr_chars = user.db._playable_characters if hasattr(user, "db") else None
    if attr_chars:
        playable = [c for c in make_iter(attr_chars) if c and hasattr(c, "id")]
    # Also pick up any characters linked via the FK that aren't already
    # in the attribute list (covers legacy accounts or manually linked chars).
    fk_chars = ObjectDB.objects.filter(db_account=user)
    seen_ids = {c.id for c in playable}
    for c in fk_chars:
        if c.id not in seen_ids:
            playable.append(c)

    for char in playable:
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


def _strip_ansi(text):
    """Strip Evennia ANSI color codes like |r, |025, |n, |R etc."""
    import re
    return re.sub(r'\|[a-zA-Z]|\|\d{3}|\|\[?\d+', '', text or '').strip()


def _is_admin(user):
    """Check if the Django user is a game admin (superuser, Admin, or Builder)."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.check_permstring("Admin") or user.check_permstring("Builder")
    except Exception:
        return False


def admin_all_characters(request):
    """
    Admin-only: returns ALL characters across all accounts with metadata
    including online/offline status, location, stats, and account info.
    """
    user = request.user
    if not _is_admin(user):
        return JsonResponse({"error": "Admin access required"}, status=403)

    from evennia.objects.models import ObjectDB
    from django.conf import settings

    typeclass = getattr(settings, "BASE_CHARACTER_TYPECLASS", "typeclasses.characters.Character")
    all_chars = ObjectDB.objects.filter(db_typeclass_path=typeclass)

    characters = []
    for char in all_chars:
        try:
            location = char.location
            location_name = location.key if location else "the void"
            in_chargen = False
            if location and "ChargenRoom" in (location.typeclass_path or ""):
                in_chargen = True

            # Online = has an active session (puppeted by someone)
            is_online = bool(char.has_account and char.sessions.count())

            # Account info
            account_name = None
            account_id = None
            if char.db_account:
                account_name = char.db_account.username
                account_id = char.db_account.id
            else:
                # Check _playable_characters on all accounts
                from evennia.accounts.models import AccountDB
                for acct in AccountDB.objects.all():
                    pcs = acct.db._playable_characters or []
                    if char in pcs:
                        account_name = acct.username
                        account_id = acct.id
                        break

            characters.append({
                "id": char.id,
                "name": _strip_ansi(char.key),
                "dbref": f"#{char.id}",
                "body": char.db.body if char.db.body is not None else 0,
                "totalBody": char.db.total_body if char.db.total_body is not None else 0,
                "av": char.db.av or 0,
                "location": _strip_ansi(location_name),
                "archetype": _archetype_for_character(char),
                "online": is_online,
                "inChargen": in_chargen,
                "accountName": account_name,
                "accountId": account_id,
                "created": char.db_date_created.isoformat() if char.db_date_created else None,
            })
        except Exception as exc:
            print(f"[api_views] Error serializing character {char.id}: {exc}")
            continue

    return JsonResponse({"characters": characters})


@require_http_methods(["POST"])
def admin_delete_character(request):
    """
    Admin-only: delete a character by ID.
    POST body: {"character_id": 123}
    """
    user = request.user
    if not _is_admin(user):
        return JsonResponse({"error": "Admin access required"}, status=403)

    try:
        data = json.loads(request.body)
        char_id = data.get("character_id")
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "Invalid request body"}, status=400)

    if not char_id:
        return JsonResponse({"error": "character_id required"}, status=400)

    from evennia.objects.models import ObjectDB

    try:
        char = ObjectDB.objects.get(id=char_id)
    except ObjectDB.DoesNotExist:
        return JsonResponse({"error": f"Character #{char_id} not found"}, status=404)

    # Remove from owner's _playable_characters
    try:
        from evennia.accounts.models import AccountDB
        for acct in AccountDB.objects.all():
            pcs = acct.db._playable_characters or []
            if char in pcs:
                pcs.remove(char)
                acct.db._playable_characters = pcs
                break
    except Exception:
        pass

    char_name = char.key
    char.delete()

    return JsonResponse({"success": True, "deleted": char_name})


def admin_all_accounts(request):
    """
    Admin-only: returns all accounts with their roles/permissions,
    online status, and character count.
    """
    user = request.user
    if not _is_admin(user):
        return JsonResponse({"error": "Admin access required"}, status=403)

    from evennia.accounts.models import AccountDB

    accounts = []
    for acct in AccountDB.objects.all():
        try:
            perms = list(acct.permissions.all()) if hasattr(acct, "permissions") else []
            # Count characters
            pcs = acct.db._playable_characters or []
            char_names = [getattr(c, "key", "?") for c in pcs if c]
            # Online = has connected sessions
            is_online = bool(acct.sessions.count()) if hasattr(acct, "sessions") else False

            accounts.append({
                "id": acct.id,
                "username": acct.username,
                "email": getattr(acct, "email", "") or "",
                "permissions": perms,
                "isSuperuser": acct.is_superuser,
                "isStaff": acct.is_staff,
                "online": is_online,
                "characterCount": len(char_names),
                "characters": char_names[:5],  # first 5
                "dateJoined": acct.date_joined.isoformat() if hasattr(acct, "date_joined") and acct.date_joined else None,
            })
        except Exception as exc:
            print(f"[api_views] Error serializing account {acct.id}: {exc}")

    # Available roles for the dropdown
    roles = ["Player", "Builder", "Admin", "Developer"]

    return JsonResponse({"accounts": accounts, "availableRoles": roles})


@require_http_methods(["POST"])
def admin_set_role(request):
    """
    Admin-only: add or remove a permission/role on an account.
    POST body: {"account_id": 123, "role": "Builder", "action": "add"|"remove"}
    """
    user = request.user
    if not _is_admin(user):
        return JsonResponse({"error": "Admin access required"}, status=403)

    try:
        data = json.loads(request.body)
        account_id = data.get("account_id")
        role = data.get("role")
        action = data.get("action", "add")
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "Invalid request body"}, status=400)

    if not account_id or not role:
        return JsonResponse({"error": "account_id and role required"}, status=400)

    valid_roles = ["Player", "Builder", "Admin", "Developer"]
    if role not in valid_roles:
        return JsonResponse({"error": f"Invalid role. Must be one of: {valid_roles}"}, status=400)

    from evennia.accounts.models import AccountDB
    try:
        acct = AccountDB.objects.get(id=account_id)
    except AccountDB.DoesNotExist:
        return JsonResponse({"error": f"Account #{account_id} not found"}, status=404)

    current_perms = list(acct.permissions.all())

    if action == "add":
        if role not in current_perms:
            acct.permissions.add(role)
        return JsonResponse({"success": True, "username": acct.username, "permissions": list(acct.permissions.all())})
    elif action == "remove":
        if role in current_perms:
            acct.permissions.remove(role)
        return JsonResponse({"success": True, "username": acct.username, "permissions": list(acct.permissions.all())})
    else:
        return JsonResponse({"error": "action must be 'add' or 'remove'"}, status=400)
