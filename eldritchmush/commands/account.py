"""
Account-level command overrides.

The custom CmdCharCreate below subclasses Evennia's default
CmdCharCreate and forces newly-created characters to spawn in the
ChargenRoom (looked up by typeclass) so the React frontend's
ChargenWizard fires automatically. Falls back to settings.START_LOCATION
if no ChargenRoom exists.
"""
from django.conf import settings
from evennia.commands.default import account as default_account
from evennia.objects.models import ObjectDB
from evennia.utils import create, logger


class CmdCharCreate(default_account.CmdCharCreate):
    """
    create a new character

    Usage:
      charcreate <charname> [= desc]

    Create a new character. New characters are placed in the
    character creation room so you can choose your archetype and
    skills before being released into the world.
    """

    def func(self):
        account = self.account
        if not self.args:
            self.msg("Usage: charcreate <charname> [= description]")
            return
        key = self.lhs
        desc = self.rhs

        charmax = getattr(settings, "MAX_NR_CHARACTERS", 5)

        if not account.is_superuser and (
            account.db._playable_characters and len(account.db._playable_characters) >= charmax
        ):
            self.msg("You may only create a maximum of %i characters." % charmax)
            return

        typeclass = settings.BASE_CHARACTER_TYPECLASS

        if ObjectDB.objects.filter(db_typeclass_path=typeclass, db_key__iexact=key):
            self.msg("|rA character named '|w%s|r' already exists.|n" % key)
            return

        # Find the ChargenRoom — there should be exactly one. New
        # characters spawn there so the wizard fires.
        chargen_room = ObjectDB.objects.filter(
            db_typeclass_path="typeclasses.rooms.ChargenRoom"
        ).first()

        if chargen_room:
            start_location = chargen_room
            default_home = chargen_room
        else:
            start_location = ObjectDB.objects.get_id(settings.START_LOCATION)
            default_home = ObjectDB.objects.get_id(settings.DEFAULT_HOME)

        permissions = settings.PERMISSION_ACCOUNT_DEFAULT
        new_character = create.create_object(
            typeclass,
            key=key,
            location=start_location,
            home=default_home,
            permissions=permissions,
        )

        # Only allow creator (and developers) to puppet this char.
        new_character.locks.add(
            "puppet:id(%i) or pid(%i) or perm(Developer) or pperm(Developer);"
            "delete:id(%i) or perm(Admin)"
            % (new_character.id, account.id, account.id)
        )

        # Make sure _playable_characters exists and append.
        if account.db._playable_characters is None:
            account.db._playable_characters = []
        account.db._playable_characters.append(new_character)

        if desc:
            new_character.db.desc = desc
        elif not new_character.db.desc:
            new_character.db.desc = "A new soul, freshly arrived in the dark."

        self.msg(
            "Created new character %s. Use |wic %s|n to enter the game as this character."
            % (new_character.key, new_character.key)
        )
        logger.log_sec(
            "Character Created: %s (Caller: %s, IP: %s)."
            % (new_character, account, self.session.address)
        )
