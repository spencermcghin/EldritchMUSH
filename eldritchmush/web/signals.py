"""
Signal handlers wired up by web/apps.py during app load.

Currently only one: when allauth creates a brand-new user via Google
OAuth, we make sure that user has an Evennia Character to puppet so
they land directly in-game without needing to type `charcreate` first.
The new character is dropped into the ChargenRoom — the React frontend
detects that and shows the ChargenWizard automatically (welcome
screen first, then archetype/skill selection, then `done` to exit).
"""
from allauth.account.signals import user_signed_up
from django.dispatch import receiver


@receiver(user_signed_up)
def create_character_for_new_oauth_user(sender, request, user, **kwargs):
    """
    Fired once, the first time a user signs up via any allauth flow
    (Google OAuth in our case). `user` is an AccountDB instance because
    Evennia sets AUTH_USER_MODEL = "accounts.AccountDB".

    The handler:
      1. Creates a Character keyed off the Google username
      2. Drops it into the ChargenRoom (so the frontend wizard fires)
      3. Falls back to the default START_LOCATION if no ChargenRoom exists
    """
    # Lazy imports — these depend on the Evennia/Django app registry
    # being fully loaded.
    from evennia.utils import create
    from evennia.objects.models import ObjectDB
    from django.conf import settings

    # If the account already has a puppetable character (e.g. they
    # somehow re-signed-up), bail out.
    existing = ObjectDB.objects.filter(db_account=user)
    if existing.exists():
        return

    # Pick a clean character name. allauth derives `username` from the
    # Google profile (display name or local-part of email). Strip
    # whitespace and capitalize for in-world readability.
    char_name = (user.username or "Wanderer").strip().split()[0].capitalize()

    # Try to find the ChargenRoom by typeclass — there should be exactly
    # one in the world. New players land there so the React frontend's
    # chargen detection fires and shows the ChargenWizard.
    chargen_room = None
    try:
        chargen_room = ObjectDB.objects.filter(
            db_typeclass_path="typeclasses.rooms.ChargenRoom"
        ).first()
    except Exception:
        pass

    # Fallback: parse settings.START_LOCATION (e.g. "#2") into a Room.
    fallback_room = None
    try:
        start_id = int(str(settings.START_LOCATION).lstrip("#"))
        fallback_room = ObjectDB.objects.filter(id=start_id).first()
    except Exception:
        pass

    spawn_room = chargen_room or fallback_room

    try:
        character = create.create_object(
            settings.BASE_CHARACTER_TYPECLASS,
            key=char_name,
            location=spawn_room,
            home=spawn_room,
        )
    except Exception as exc:
        print(f"[web.signals] Could not create character for {user.username}: {exc}")
        return

    # Link the character to the account so puppeting works.
    character.db_account = user
    character.save()
    user.db._playable_characters = [character]
    user.save()

    where = "ChargenRoom" if chargen_room else "starting room"
    print(
        f"[web.signals] Created Evennia character '{char_name}' for OAuth user "
        f"{user.username} in {where}"
    )
