"""
Commands

Commands describe the input the account can do to the game.

"""
# Global imports
import random
from django.conf import settings

# Local imports
from evennia import Command as BaseCommand
from evennia import default_cmds, utils, search_object


_SEARCH_AT_RESULT = utils.object_from_module(settings.SEARCH_AT_RESULT)


# from evennia import default_cmds


class Command(BaseCommand):
    """
    Inherit from this if you want to create your own command styles
    from scratch.  Note that Evennia's default commands inherits from
    MuxCommand instead.

    Note that the class's `__doc__` string (this text) is
    used by Evennia to create the automatic help entry for
    the command, so make sure to document consistently here.

    Each Command implements the following methods, called
    in this order (only func() is actually required):
        - at_pre_cmd(): If this returns anything truthy, execution is aborted.
        - parse(): Should perform any extra parsing needed on self.args
            and store the result on self.
        - func(): Performs the actual work.
        - at_post_cmd(): Extra actions, often things done after
            every command, like prompts.

    """

    pass


# -------------------------------------------------------------
#
# The default commands inherit from
#
#   evennia.commands.default.muxcommand.MuxCommand.
#
# If you want to make sweeping changes to default commands you can
# uncomment this copy of the MuxCommand parent and add
#
#   COMMAND_DEFAULT_CLASS = "commands.command.MuxCommand"
#
# to your settings file. Be warned that the default commands expect
# the functionality implemented in the parse() method, so be
# careful with what you change.
#
# -------------------------------------------------------------

# from evennia.utils import utils
#
#
# class MuxCommand(Command):
#     """
#     This sets up the basis for a MUX command. The idea
#     is that most other Mux-related commands should just
#     inherit from this and don't have to implement much
#     parsing of their own unless they do something particularly
#     advanced.
#
#     Note that the class's __doc__ string (this text) is
#     used by Evennia to create the automatic help entry for
#     the command, so make sure to document consistently here.
#     """
#     def has_perm(self, srcobj):
#         """
#         This is called by the cmdhandler to determine
#         if srcobj is allowed to execute this command.
#         We just show it here for completeness - we
#         are satisfied using the default check in Command.
#         """
#         return super().has_perm(srcobj)
#
#     def at_pre_cmd(self):
#         """
#         This hook is called before self.parse() on all commands
#         """
#         pass
#
#     def at_post_cmd(self):
#         """
#         This hook is called after the command has finished executing
#         (after self.func()).
#         """
#         pass
#
#     def parse(self):
#         """
#         This method is called by the cmdhandler once the command name
#         has been identified. It creates a new set of member variables
#         that can be later accessed from self.func() (see below)
#
#         The following variables are available for our use when entering this
#         method (from the command definition, and assigned on the fly by the
#         cmdhandler):
#            self.key - the name of this command ('look')
#            self.aliases - the aliases of this cmd ('l')
#            self.permissions - permission string for this command
#            self.help_category - overall category of command
#
#            self.caller - the object calling this command
#            self.cmdstring - the actual command name used to call this
#                             (this allows you to know which alias was used,
#                              for example)
#            self.args - the raw input; everything following self.cmdstring.
#            self.cmdset - the cmdset from which this command was picked. Not
#                          often used (useful for commands like 'help' or to
#                          list all available commands etc)
#            self.obj - the object on which this command was defined. It is often
#                          the same as self.caller.
#
#         A MUX command has the following possible syntax:
#
#           name[ with several words][/switch[/switch..]] arg1[,arg2,...] [[=|,] arg[,..]]
#
#         The 'name[ with several words]' part is already dealt with by the
#         cmdhandler at this point, and stored in self.cmdname (we don't use
#         it here). The rest of the command is stored in self.args, which can
#         start with the switch indicator /.
#
#         This parser breaks self.args into its constituents and stores them in the
#         following variables:
#           self.switches = [list of /switches (without the /)]
#           self.raw = This is the raw argument input, including switches
#           self.args = This is re-defined to be everything *except* the switches
#           self.lhs = Everything to the left of = (lhs:'left-hand side'). If
#                      no = is found, this is identical to self.args.
#           self.rhs: Everything to the right of = (rhs:'right-hand side').
#                     If no '=' is found, this is None.
#           self.lhslist - [self.lhs split into a list by comma]
#           self.rhslist - [list of self.rhs split into a list by comma]
#           self.arglist = [list of space-separated args (stripped, including '=' if it exists)]
#
#           All args and list members are stripped of excess whitespace around the
#           strings, but case is preserved.
#         """
#         raw = self.args
#         args = raw.strip()
#
#         # split out switches
#         switches = []
#         if args and len(args) > 1 and args[0] == "/":
#             # we have a switch, or a set of switches. These end with a space.
#             switches = args[1:].split(None, 1)
#             if len(switches) > 1:
#                 switches, args = switches
#                 switches = switches.split('/')
#             else:
#                 args = ""
#                 switches = switches[0].split('/')
#         arglist = [arg.strip() for arg in args.split()]
#
#         # check for arg1, arg2, ... = argA, argB, ... constructs
#         lhs, rhs = args, None
#         lhslist, rhslist = [arg.strip() for arg in args.split(',')], []
#         if args and '=' in args:
#             lhs, rhs = [arg.strip() for arg in args.split('=', 1)]
#             lhslist = [arg.strip() for arg in lhs.split(',')]
#             rhslist = [arg.strip() for arg in rhs.split(',')]
#
#         # save to object properties:
#         self.raw = raw
#         self.switches = switches
#         self.args = args.strip()
#         self.arglist = arglist
#         self.lhs = lhs
#         self.lhslist = lhslist
#         self.rhs = rhs
#         self.rhslist = rhslist
#
#         # if the class has the account_caller property set on itself, we make
#         # sure that self.caller is always the account if possible. We also create
#         # a special property "character" for the puppeted object, if any. This
#         # is convenient for commands defined on the Account only.
#         if hasattr(self, "account_caller") and self.account_caller:
#             if utils.inherits_from(self.caller, "evennia.objects.objects.DefaultObject"):
#                 # caller is an Object/Character
#                 self.character = self.caller
#                 self.caller = self.caller.account
#             elif utils.inherits_from(self.caller, "evennia.accounts.accounts.DefaultAccount"):
#                 # caller was already an Account
#                 self.character = self.caller.get_puppet(self.session)
#             else:
#                 self.character = None

class SetArmor(Command):
    """Set the armor level of a character

    Usage: setarmor <0-3>

    This sets the armor of the current character. This can only be
    used during character generation.
    """

    key = "setarmor"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "You must supply a number between 1 and 5."
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            armor = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= armor <= 3):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        if armor == 0:
            self.caller.db.armor = 2
        elif armor == 1:
            self.caller.db.armor = 3
        elif armor == 2:
            self.caller.db.armor = 4
        elif armor == 3:
            self.caller.db.armor = 5

        # Get vals for armor value calc
        tough = self.caller.db.tough
        shield = 1 if self.caller.db.shield == True else 0
        armor_specialist = 1 if self.caller.db.armor_specialist == True else 0

        # Add them up and set the curent armor value in the database
        currentArmorValue = armor + tough + shield + armor_specialist
        self.caller.db.av = currentArmorValue

        # Return armor value to console.
        self.caller.msg(f"|gYour current Armor Value is {currentArmorValue}:\nArmor: {armor}\nTough: {tough}\nShield: {shield}\nArmor Specialist: {armor_specialist}")


class SetTracking(Command):
    """Set the tracking of a character

    Usage: settracking <1-3>

    This sets the tracking of the current character. This can only be
    used during character generation.
    """

    key = "settracking"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "You must supply a number between 1 and 3."
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            tracking = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (1 <= tracking <= 3):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.tracking = tracking
        self.caller.msg("Your Tracking was set to %i." % tracking)



class SetPerception(Command):
    """Set the perception of a character

    Usage: setperception<1-3>

    This sets the perception of the current character. This can only be
    used during character generation.
    """

    key = "setperception"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "You must supply a number between 1 and 3."
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            perception = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (1 <= perception <= 3):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.perception = perception
        self.caller.msg("Your Perception was set to %i." % perception)


class SetMasterOfArms(Command):
    """Set the tracking of a character

    Usage: setmasterofarms <1-3>

    This sets the master of arms of the current character. This can only be
    used during character generation.
    """

    key = "setmasterofarms"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "You must supply a number between 1 and 3."
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            master_of_arms = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (1 <= master_of_arms <= 3):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.master_of_arms = master_of_arms
        self.caller.msg("Your Master of Arms was set to %i." % master_of_arms)

class SetTough(Command):
    """Set the tough of a character

    Usage: settough <1-5>

    This sets the tough of the current character. This can only be
    used during character generation.
    """

    key = "settough"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "You must supply a number between 1 and 3."
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            tough = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (1 <= tough <= 5):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.tough = tough
        self.caller.msg("Your Tough was set to %i." % tough)

        # Get armor value objects
        armor = self.caller.db.armor
        tough = self.caller.db.tough
        shield = 1 if self.caller.db.shield == True else 0
        armor_specialist = 1 if self.caller.db.armor_specialist == True else 0

        # Add them up and set the curent armor value in the database
        currentArmorValue = armor + tough + shield + armor_specialist
        self.caller.db.av = currentArmorValue

        # Return armor value to console.
        self.caller.msg(f"Your current Armor Value is {currentArmorValue}:\nArmor: {armor}\nTough: {tough}\nShield: {shield}\nArmor Specialist: {armor_specialist}")

class SetBody(Command):
    """Set the body of a character

    Usage: setbody <1-3>

    This sets the tough of the current character. This can only be
    used during character generation.
    """

    key = "setbody"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "You must supply a number between 1 and 3."
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            body = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (1 <= body <= 3):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.body = body
        self.caller.msg("Your Body was set to %i." % body)

class SetArmorSpecialist(Command):
    """Set the armor specialist property of a character

    Usage: setarmorspecialist <0/1>

    This sets the armor specialist of the current character. This can only be
    used during character generation.
    """

    key = "setarmorspecialist"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "You must supply a value of 0 or 1."
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            armor_specialist = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if armor_specialist not in (0,1):
            self.caller.msg(errmsg)
            return

        self.caller.db.armor_specialist = armor_specialist

        # Get armor value objects
        armor = self.caller.db.armor
        tough = self.caller.db.tough
        shield = 1 if self.caller.db.shield is 1 else 0
        armor_specialist = 1 if self.caller.db.armor_specialist is 1 else 0

        # Add them up and set the curent armor value in the database
        currentArmorValue = armor + tough + shield + armor_specialist
        self.caller.db.av = currentArmorValue

        # Return armor value to console.
        self.caller.msg(f"Your current Armor Value is {currentArmorValue}:\nArmor: {armor}\nTough: {tough}\nShield: {shield}\nArmor Specialist: {armor_specialist}")

class SetWyldingHand(Command):
    """Set the wylding hand level of a character

    Usage: setwyldinghand <1-3>

    This sets the wylding hand level of the current character. This can only be
    used during character generation.
    """

    key = "setwyldinghand"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "You must supply a number between 1 and 3."
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            wyldinghand = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (1 <= wyldinghand <= 3):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.wyldinghand = wyldinghand
        self.caller.msg(f"Your level of Wylding Hand was set to {wyldinghand}")


class SetWeaponLevel(Command):
    """Set the weapon level of a character

    Usage: setweapon <1,2,3>

    This sets the weapon level of the current character. This can only be
    used during character generation.
    """

    key = "setweaponlevel"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "You must supply a number between 1 and 3."
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            weapon_level = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (1 <= weapon_level <= 3):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.weapon_level = weapon_level
        self.caller.msg("Your weapon level was set to %i." % weapon_level)


class SetBow(Command):
    """Set the bow property of a character

    Usage: setbow <0/1>

    This sets the bow of the current character. This can be used at any time during the game.
    """

    key = "setbow"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "You must supply a value of 0 or 1."
        hasMelee = self.caller.db.melee

        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            bow = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if bow not in (0,1):
            self.caller.msg(errmsg)
            return
        else:
            # Bow/melee error handling
            if hasMelee:
                self.caller.msg("Before using a bow, you must first unequip your melee weapon using the command setmelee 0.")
            else:
                self.caller.db.bow = bow

                # Quippy message when setting a shield as 0 or 1.
                if bow:
                    self.caller.msg("You have equipped your bow.")
                else:
                    self.caller.msg("You have unequipped your bow.")



class SetMelee(Command):
    """Set the melee property of a character

    Usage: setmelee <0/1>

    This sets the melee of the current character. This can be used at any time during the game.
    """

    key = "setmelee"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "You must supply a value of 0 or 1."
        hasBow = self.caller.db.bow

        # Check for valid arguments
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            melee = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if melee not in (0,1):
            self.caller.msg(errmsg)
        else:
            # Bow/melee error handling
            if hasBow:
                self.caller.msg("Before using a melee weapon, you must first unequip your bow using the command setbow 0.")
            else:
                self.caller.db.melee = melee

                # Quippy message when setting a shield as 0 or 1.
                if melee:
                    self.caller.msg("You have equipped your melee weapon.")
                else:
                    self.caller.msg("You have unequipped your melee weapon.")


class SetResist(Command):
    """Set the resist level of a character

    Usage: setresist <1,2,3,4,5>

    This sets the resist level of the current character. This can only be
    used during character generation.
    """

    key = "setresist"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "You must supply a number between 1 and 5."
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            resist = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (1 <= resist <= 5):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.resist = resist
        self.caller.msg("Your resist level was set to %i." % resist)


class SetDisarm(Command):
    """Set the disarm level of a character

    Usage: setdisarm <1,2,3>

    This sets the disarm level of the current character. This can only be
    used during character generation.
    """

    key = "setdisarm"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "You must supply a number between 1 and 5."
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            disarm = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (1 <= disarm <= 5):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.disarm = disarm
        self.caller.msg("Your disarm level was set to %i." % disarm)


class SetCleave(Command):
    """Set the cleave level of a character

    Usage: setcleave <1,2,3>

    This sets the cleave level of the current character. This can only be
    used during character generation.
    """

    key = "setcleave"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "You must supply a number between 1 and 5."
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            cleave = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (1 <= cleave <= 5):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.cleave = cleave
        self.caller.msg("Your cleave level was set to %i." % cleave)

class SetStun(Command):
    """Set the stun level of a character

    Usage: setstun <1,2,3,4,5>

    This sets the stun level of the current character. This can only be
    used during character generation.
    """

    key = "setstun"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "You must supply a number between 1 and 5."
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            stun = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (1 <= stun <= 3):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.stun = stun
        self.caller.msg("Your stun level was set to %i." % stun)


class SetStagger(Command):
    """Set the stagger level of a character

    Usage: setstun <1,2,3,4,5>

    This sets the stagger level of the current character. This can only be
    used during character generation.
    """

    key = "setstagger"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "You must supply a number between 1 and 5."
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            stagger = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (1 <= stagger <= 5):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.stagger = stagger
        self.caller.msg("Your stagger level was set to %i." % stagger)


"""
Combat settings
"""

class SetShield(Command):
    """Set the shield property of a character

    Usage: setshield <0/1>

    This sets the shield of the current character. This can only be
    used during character generation.
    """

    key = "setshield"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "You must supply a value of 0 or 1."
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            shield = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if shield not in (0,1):
            self.caller.msg(errmsg)
            return

        self.caller.db.shield = shield

        # Quippy message when setting a shield as 0 or 1.
        if shield:
            self.caller.msg("You now have a shield.")
        else:
            self.caller.msg("You have unequipped or lost your shield.")

        # Get armor value objects
        armor = self.caller.db.armor
        tough = self.caller.db.tough
        shield = 1 if self.caller.db.shield is 1 else 0
        armor_specialist = 1 if self.caller.db.armor_specialist is 1 else 0

        # Add them up and set the curent armor value in the database
        currentArmorValue = armor + tough + shield + armor_specialist
        self.caller.db.av = currentArmorValue

        # Return armor value to console.
        self.caller.msg(f"Your current Armor Value is {currentArmorValue}:\nArmor: {armor}\nTough: {tough}\nShield: {shield}\nArmor Specialist: {armor_specialist}")


class SetTwoHanded(Command):
    """Set the two handed weapon status of a character

    Usage: settwohander <0,1>

    This sets the two handed weapon status of the current character.
    """

    key = "settwohanded"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "Usage: settwohanded <0/1>"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            twohanded = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if twohanded not in (0,1):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.twohanded = twohanded

        if twohanded:
            self.caller.msg("Your have equipped a two-handed melee weapon.")
        else:
            self.caller.msg("You have unequipped a two-handed melee weapon.")

"""
General commands
"""

class CmdInspect(default_cmds.MuxCommand):
    """
    looks at the room and on details
    Usage:
        inspect <obj>
        inspect <room detail>
        inspect *<account>
    Observes your location, details at your location or objects
    in your vicinity.
    Tutorial: This is a child of the default Look command, that also
    allows us to look at perception and tracking attrs in the room.  These details are
    things to examine and offers some extra description without
    actually having to be actual database objects. It uses the
    return_perception() hook on the Room class for this.
    """

    # we don't need to specify key/locks etc, this is already
    # set by the parent.
    help_category = "mush"
    key = "inspect"

    def func(self):
        """
        Handle the inspecting. This is a copy of the default look
        code except for adding in the details.
        """
        caller = self.caller
        args = self.args
        errmsg = "Usage: inspect <thing>"


        if args:
            # we use quiet=True to turn off automatic error reporting.
            # This tells search that we want to handle error messages
            # ourself. This also means the search function will always
            # return a list (with 0, 1 or more elements) rather than
            # result/None.
            looking_at_obj = caller.search(
                args,
                # note: excludes room/room aliases
                candidates=caller.location.contents + caller.contents,
                use_nicks=True,
                quiet=True,
            )
            if len(looking_at_obj) != 1:
                # no target found or more than one target found (multimatch)
                # look for a detail that may match

                perception_level = caller.db.perception

                perception = self.obj.return_perception(args, perception_level)

                if perception:
                    self.caller.msg(perception)
                    return
                else:
                    # no detail found, delegate our result to the normal
                    # error message handler.
                    _SEARCH_AT_RESULT(looking_at_obj, caller, args)
                    return
            else:
                # we found a match, extract it from the list and carry on
                # normally with the look handling.
                looking_at_obj = looking_at_obj[0]

        else:
            # looking_at_obj = caller.location
            # if not looking_at_obj:
            #     caller.msg("You have nothing to inspect!")
            #     return
            self.caller.msg(errmsg)
            return

        if not hasattr(looking_at_obj, "return_appearance"):
            # this is likely due to us having an account instead
            looking_at_obj = looking_at_obj.character
        if not looking_at_obj.access(caller, "view"):
            caller.msg("Could not find '%s'." % args)
            return
        # get object's appearance
        caller.msg(looking_at_obj.return_appearance(caller))
        # the object's at_desc() method.
        looking_at_obj.at_desc(looker=caller)
        return


class CmdPerception(default_cmds.MuxCommand):
    """
    sets a detail on a room
    Usage:
        @perception <level> <key> = <description>
        @perception <level> <key>;<alias>;... = description
    Example:
        @perception 1 walls = The walls are covered in ...
        @perception 3 castle;ruin;tower = The distant ruin ...
    This sets a "perception" on the object this command is defined on
    . This detail can be accessed with
    the TutorialRoomLook command sitting on TutorialRoom objects (details
    are set as a simple dictionary on the room). This is a Builder command.
    We custom parse the key for the ;-separator in order to create
    multiple aliases to the detail all at once.
    """

    key = "@perception"
    locks = "cmd:perm(Builder)"
    help_category = "mush"

    def func(self):
        """
        All this does is to check if the object has
        the set_perception method and uses it.
        """
        if not self.args or not self.rhs:
            self.caller.msg("Usage: @perception level key = description")
            return
        if not hasattr(self.obj, "set_perception"):
            self.caller.msg("Perception cannot be set on %s." % self.obj)
            return

        # Get level of perception
        # TODO: Error handle perception level
        level = int(self.args[0])


        # Get perception setting objects
        equals = self.args.index("=")
        key = str(self.args[1:equals]).strip()

        # for key in self.lhs.split(";"):
        #     # loop over all aliases, if any (if not, this will just be
        #     # the one key to loop over)
        self.obj.set_perception(key, level, self.rhs)

        self.caller.msg(f"Perception {level} set on {key}: {self.rhs}")


class CmdSmile(Command):
    """
    A smile command

    Usage:
      smile [at] [<someone>]
      grin [at] [<someone>]

    Smiles to someone in your vicinity or to the room
    in general.

    (This initial string (the __doc__ string)
    is also used to auto-generate the help
    for this command)
    """

    key = "smile"
    aliases = ["smile at", "grin", "grin at"]
    locks = "cmd:all()"
    help_category = "General"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):
        "This actually does things"
        caller = self.caller

        if not self.target or self.target == "here":
            string = f"{caller.key} smiles"
        else:
            target = caller.search(self.target)
            if not target:
                return
            string = f"{caller.key} smiles at {target.key}"

        caller.location.msg_contents(string)
