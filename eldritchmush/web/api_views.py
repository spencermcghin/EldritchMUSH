"""
Lightweight JSON endpoints used by the React frontend.
"""
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
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

    Note: this is a GET with session-mutation side effects (writes
    the nonce on first call / on uid change). SameSite=Lax cookies
    block cross-site GETs from triggering it, and the write is
    guarded by `existing_uid != user.id`. A full POST + CSRF
    conversion is a deferred followup — it requires changing the
    frontend to POST with the CSRF token and is tracked in the
    security audit as M2.
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


def _is_staff(user):
    """Read-only staff check: superuser, Admin, or Builder.

    Use this ONLY for endpoints that disclose data but do not mutate
    state. Any endpoint that can change permissions, delete entities,
    or bulk-mutate must use `_is_admin_or_super()` instead — Builders
    are content-moderation staff, not privileged operators.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.check_permstring("Admin") or user.check_permstring("Builder")
    except Exception:
        return False


def _is_admin_or_super(user):
    """Strict check: superuser or Admin permission only.

    Builder is explicitly excluded — Builders moderate content but
    cannot grant roles, delete accounts/characters, or run destructive
    admin operations. Use this for any mutation endpoint.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.check_permstring("Admin")
    except Exception:
        return False


# Legacy alias kept for any caller we might have missed in this pass.
# New code should pick `_is_staff` (read) or `_is_admin_or_super`
# (mutation) explicitly.
_is_admin = _is_staff


def npc_audit_log(request):
    """Superuser/Admin only: return the last N NPC conversation records
    as JSON. Builders are excluded — this log contains raw player
    messages, which are PII.

    Query params:
      limit=int (default 200, max 1000)

    Response:
      {"records": [ {ts, npc, char, account, msg, reply, flags}, ... ]}

    The `msg` and `reply` fields are truncated server-side to 120
    characters before being returned, so accidental disclosure via
    the moderation UI is bounded even if a future perm-check regresses.
    """
    user = request.user
    if not _is_admin_or_super(user):
        return JsonResponse({"error": "admin_required"}, status=403)
    try:
        limit = min(int(request.GET.get("limit", "200")), 1000)
    except ValueError:
        limit = 200
    try:
        from world.ai_safety import read_audit_tail
        records = read_audit_tail(limit=limit)
    except Exception:
        # Don't leak paths / stack info to the client.
        try:
            from web.diag import diag_write
            import traceback
            diag_write("npc_audit_log read failed", tb=traceback.format_exc())
        except Exception:
            pass
        return JsonResponse({"error": "log_read_failed"}, status=500)

    # Truncate msg/reply to cap the damage if a record contains very
    # long text (prompt-injection attempts, long rants, etc.). The full
    # log file is still readable on disk for superusers via the diag
    # view plus SSH, so this is a defense-in-depth trim, not a secret.
    def _clip(s, n=120):
        if not isinstance(s, str):
            return s
        return s if len(s) <= n else s[:n] + "…"

    clipped = []
    for rec in records:
        if isinstance(rec, dict):
            rec = dict(rec)  # copy — don't mutate the source
            if "msg" in rec:
                rec["msg"] = _clip(rec["msg"])
            if "reply" in rec:
                rec["reply"] = _clip(rec["reply"])
        clipped.append(rec)
    return JsonResponse({"records": clipped, "count": len(clipped)})


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
                "approvalStatus": char.attributes.get("approval_status", default="none"),
                "rejectionReason": char.attributes.get("rejection_reason", default=""),
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
    if not _is_admin_or_super(user):
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


# ---------------------------------------------------------------------------
# Legacy purge — remove non-admin accounts, their characters, and any
# legacy NPCs still kicking around.
# ---------------------------------------------------------------------------
# Evennia stores permissions lowercased ("admin", "builder", "developer")
# even when added as "Admin" etc. Keep both in lowercase for comparison.
ADMIN_PERMS = {"admin", "builder", "developer"}


def _is_admin_account(acct):
    """Account is admin if superuser or has Admin/Builder/Developer perm.

    Case-insensitive compare — Evennia stores perms lowercase regardless
    of how they were added.
    """
    try:
        if acct.is_superuser:
            return True
        perms = {str(p).lower() for p in acct.permissions.all()}
    except Exception:
        return False
    return bool(perms & ADMIN_PERMS)


@require_http_methods(["POST"])
def admin_bulk_delete_characters(request):
    """Admin-only: delete multiple characters in one request.

    POST body: {"character_ids": [1, 2, 3]}

    Cleans up _playable_characters references on every account for
    each deleted character. Returns {deleted: [{id, name}], errors:
    [{id, error}], count}.
    """
    user = request.user
    if not _is_admin_or_super(user):
        return JsonResponse({"error": "admin_required"}, status=403)
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    ids = data.get("character_ids") or []
    if not isinstance(ids, list) or not ids:
        return JsonResponse({"error": "character_ids must be a non-empty list"}, status=400)

    from evennia.accounts.models import AccountDB
    from evennia.objects.models import ObjectDB

    deleted = []
    errors = []
    for char_id in ids:
        try:
            char = ObjectDB.objects.get(id=char_id)
        except ObjectDB.DoesNotExist:
            errors.append({"id": char_id, "error": "not found"})
            continue
        try:
            # Clean _playable_characters on every account — O(accounts)
            # per character, but n is small and this keeps the schema
            # consistent.
            for acct in AccountDB.objects.all():
                pcs = acct.db._playable_characters or []
                new_pcs = [c for c in pcs if c and getattr(c, "pk", None) != char.pk]
                if len(new_pcs) != len(pcs):
                    acct.db._playable_characters = new_pcs
            name = char.key
            char.delete()
            deleted.append({"id": char_id, "name": name})
        except Exception as exc:
            errors.append({"id": char_id, "error": str(exc)})

    return JsonResponse({
        "success": True,
        "deleted": deleted,
        "errors": errors,
        "count": len(deleted),
    })


@require_http_methods(["POST"])
def admin_purge_legacy(request):
    """Admin-only: purge legacy accounts, characters, and NPCs.

    POST body: {"mode": "preview" | "execute"}

    Deletion rules (both modes return the same candidate lists):
      - Accounts: delete if NOT an admin account (no superuser, no
        Admin/Builder/Developer perm). Caller's own account is always
        preserved even if criteria match.
      - Characters: delete all characters owned by accounts scheduled
        for deletion. Also delete characters with no owning account
        (orphans) if they are not tied to an admin account via the
        _playable_characters list.
      - NPCs: delete Npc typeclass instances that do NOT have
        `ai_personality` set (our scripted Gateway roster is preserved;
        anything without that attribute is legacy scaffolding).

    Returns:
      {
        "mode": "preview"|"executed",
        "accounts": [{"id": N, "username": "..."}],
        "characters": [{"id": N, "name": "..."}],
        "npcs": [{"id": N, "name": "..."}],
        "counts": {"accounts": N, "characters": N, "npcs": N},
      }
    """
    user = request.user
    if not _is_admin_or_super(user):
        return JsonResponse({"error": "admin_required"}, status=403)

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        data = {}
    mode = data.get("mode", "preview")
    if mode not in ("preview", "execute"):
        return JsonResponse({"error": "mode must be preview or execute"}, status=400)

    from evennia.accounts.models import AccountDB
    from evennia.objects.models import ObjectDB

    # 1. Identify legacy accounts — non-admin accounts. Never include
    #    the caller's own account, even if it somehow matched.
    doomed_accounts = []
    for acct in AccountDB.objects.all():
        if acct.id == getattr(user, "id", None):
            continue
        if _is_admin_account(acct):
            continue
        doomed_accounts.append(acct)

    # 2. Characters to delete: anything owned by a doomed account,
    #    plus orphaned characters (no db_account AND not in any admin's
    #    _playable_characters list).
    char_typeclass = "typeclasses.characters.Character"
    doomed_account_ids = {a.id for a in doomed_accounts}
    admin_playable_pks = set()
    for acct in AccountDB.objects.all():
        if _is_admin_account(acct):
            for c in (acct.db._playable_characters or []):
                if c:
                    admin_playable_pks.add(c.pk)

    doomed_characters = []
    for char in ObjectDB.objects.filter(db_typeclass_path=char_typeclass):
        # Owned by a doomed account?
        if char.db_account_id and char.db_account_id in doomed_account_ids:
            doomed_characters.append(char)
            continue
        # Orphan check: no account FK and not in any admin's playable list
        if not char.db_account_id and char.pk not in admin_playable_pks:
            # Double-check it's not in a DOOMED account's list either
            # (those get cleaned when the account is deleted anyway, so
            # we only want REAL orphans here)
            claimed = False
            for acct in AccountDB.objects.all():
                pcs = acct.db._playable_characters or []
                if any(getattr(c, "pk", None) == char.pk for c in pcs if c):
                    claimed = True
                    break
            if not claimed:
                doomed_characters.append(char)

    # 3. NPCs to delete: typeclasses.npc.Npc (and subclasses) without
    #    ai_personality set. The whitelist purge already cleaned rooms;
    #    this catches any NPCs still in canonical rooms that aren't
    #    part of our scripted roster.
    doomed_npcs = []
    for npc in ObjectDB.objects.filter(
        db_typeclass_path__startswith="typeclasses.npc"
    ):
        if npc.attributes.get("ai_personality", default=None):
            continue
        doomed_npcs.append(npc)

    payload = {
        "mode": "preview",
        "accounts": [{"id": a.id, "username": a.username} for a in doomed_accounts],
        "characters": [{"id": c.id, "name": c.key} for c in doomed_characters],
        "npcs": [{"id": n.id, "name": n.key, "location": getattr(n.location, "key", None)} for n in doomed_npcs],
        "counts": {
            "accounts": len(doomed_accounts),
            "characters": len(doomed_characters),
            "npcs": len(doomed_npcs),
        },
    }

    if mode == "preview":
        # Include a hint that execute mode needs confirm_token so the
        # React UI can render the correct two-step flow without a
        # dedicated probe endpoint.
        payload["confirm_token_required"] = True
        return JsonResponse(payload)

    # Defense-in-depth: refuse to delete any account that holds an
    # admin permstring (Admin / Builder / Developer) even if the
    # _is_admin_account() check somehow missed it. Catches case-skew
    # or partial-data regressions that would otherwise drop a staff
    # account into `doomed_accounts`.
    for acct in list(doomed_accounts):
        try:
            if _is_admin_account(acct):
                return JsonResponse(
                    {
                        "error": "refuse_admin_in_doomed",
                        "blocked_account": {"id": acct.id, "username": acct.username},
                    },
                    status=400,
                )
        except Exception:
            # If we can't verify, refuse rather than proceed.
            return JsonResponse(
                {"error": "perm_check_failed", "account_id": getattr(acct, "id", None)},
                status=500,
            )

    # Require a confirm_token round-trip from the preview response.
    # The token value itself is irrelevant — the point is that the
    # caller must do preview first, read the counts, and opt in by
    # echoing any non-empty string back. Prevents a single-shot
    # execute call from ever being generated by accident.
    confirm_token = data.get("confirm_token")
    if not confirm_token or not isinstance(confirm_token, str):
        return JsonResponse(
            {"error": "confirm_token_required",
             "hint": "Call with mode=preview first, then include a non-empty confirm_token string."},
            status=400,
        )

    # Execute — actually delete.
    deleted = {"accounts": 0, "characters": 0, "npcs": 0}
    errors = []

    # Delete NPCs first (no cascade concerns)
    for npc in doomed_npcs:
        try:
            npc.delete()
            deleted["npcs"] += 1
        except Exception as exc:
            errors.append(f"npc {npc.id}: {exc}")

    # Delete characters (clean up any _playable_characters refs first)
    for char in doomed_characters:
        try:
            for acct in AccountDB.objects.all():
                pcs = acct.db._playable_characters or []
                new_pcs = [c for c in pcs if c and getattr(c, "pk", None) != char.pk]
                if len(new_pcs) != len(pcs):
                    acct.db._playable_characters = new_pcs
            char.delete()
            deleted["characters"] += 1
        except Exception as exc:
            errors.append(f"char {char.id}: {exc}")

    # Delete accounts last
    for acct in doomed_accounts:
        try:
            acct.delete()
            deleted["accounts"] += 1
        except Exception as exc:
            errors.append(f"account {acct.id}: {exc}")

    payload["mode"] = "executed"
    payload["deleted"] = deleted
    payload["errors"] = errors
    return JsonResponse(payload)


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
    Superuser / Admin only: add or remove a permission/role on an
    account. POST body: {"account_id": 123, "role": "Builder",
    "action": "add"|"remove"}

    Rules:
      - Only superusers can grant or revoke Admin or Developer. Admin
        users can only manage Builder/Player.
      - The caller cannot mutate their own role — self-escalation and
        self-demotion both return 400.
    """
    user = request.user
    if not _is_admin_or_super(user):
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

    # Block self-targeting. Without this, a compromised or overzealous
    # Admin could demote themselves by mistake, and any future logic
    # that accepts the role directly without the full _is_admin_or_super
    # check would risk letting Builder self-promote.
    if int(account_id) == getattr(user, "id", None):
        return JsonResponse(
            {"error": "Cannot change your own role"}, status=400
        )

    # Admin/Developer may only be granted or revoked by a superuser.
    if role in ("Admin", "Developer") and not user.is_superuser:
        return JsonResponse(
            {"error": "Only superusers can grant or revoke Admin/Developer"},
            status=403,
        )

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


@require_http_methods(["POST"])
def admin_approve_character(request):
    """
    Admin-only: approve or reject a character.
    POST body: {"character_id": 123, "action": "approve"|"reject", "reason": "..."}
    """
    user = request.user
    if not _is_admin(user):
        return JsonResponse({"error": "Admin access required"}, status=403)

    try:
        data = json.loads(request.body)
        char_id = data.get("character_id")
        action = data.get("action")  # "approve" or "reject"
        reason = data.get("reason", "")
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "Invalid request body"}, status=400)

    if not char_id or action not in ("approve", "reject"):
        return JsonResponse({"error": "character_id and action (approve/reject) required"}, status=400)

    from evennia.objects.models import ObjectDB
    try:
        char = ObjectDB.objects.get(id=char_id)
    except ObjectDB.DoesNotExist:
        return JsonResponse({"error": f"Character #{char_id} not found"}, status=404)

    approved = action == "approve"

    if approved:
        char.attributes.add("approval_status", "approved")
        # Whisk them through the Mists. Preferred landing: Mistgate
        # (the Annwyn side of the crossing). Fallbacks: Mystvale South
        # Gate, then START_LOCATION. This makes approval feel like Soap
        # leading the bearer across.
        try:
            from django.conf import settings as dj_settings
            location = char.location
            destination = None
            for lookup_key in ("The Mistgate", "Mystvale South Gate"):
                destination = ObjectDB.objects.filter(db_key=lookup_key).first()
                if destination:
                    break
            if not destination:
                start_id = getattr(dj_settings, "START_LOCATION", 2)
                destination = ObjectDB.objects.get_id(start_id)
            # Only auto-teleport if they're on the Arnesse side (Gateway
            # zone) or still in the ChargenRoom. Don't move characters
            # already in the Annwyn — they might be mid-scene.
            safe_to_move = False
            if location:
                tcp = location.typeclass_path or ""
                if "ChargenRoom" in tcp:
                    safe_to_move = True
                z = location.attributes.get("zone", default="")
                if z == "Gateway":
                    safe_to_move = True
            if destination and safe_to_move:
                char.move_to(destination, quiet=True)
                try:
                    char.msg(
                        "|gSoap's hand closes on your shoulder. The mists "
                        "rise around you — cold, sweet, full of distant "
                        "voices — and when they clear, the tall hat is "
                        "gone, and the wet stone of the Mistgate lies "
                        "under your boots. You have arrived.|n"
                    )
                except Exception:
                    pass
        except Exception:
            pass
    else:
        char.attributes.add("approval_status", "rejected")
        char.attributes.add("rejection_reason", reason)

    # Find player email and send notification
    try:
        from evennia.accounts.models import AccountDB
        from world.email import send_approval_notification
        player_email = None
        for acct in AccountDB.objects.all():
            pcs = acct.db._playable_characters or []
            if char in pcs:
                player_email = getattr(acct, "email", None)
                break
        if player_email:
            send_approval_notification(player_email, char.key, approved, reason)
    except Exception as exc:
        print(f"[admin_approve] Email failed: {exc}")

    return JsonResponse({
        "success": True,
        "character": char.key,
        "status": "approved" if approved else "rejected",
    })
