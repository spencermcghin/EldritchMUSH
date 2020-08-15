"""
Commands

Commands describe the input the account can do to the game.

"""
# Global imports
import random
from django.conf import settings
import re

# Local imports
from evennia import Command as BaseCommand
from evennia.prototypes import prototypes
from evennia.commands.default.muxcommand import MuxCommand
from evennia import default_cmds, utils, search_object, spawn
from evennia.utils import evtable
from commands.combat import Helper
from commands.fortunestrings import FORTUNE_STRINGS

_SEARCH_AT_RESULT = utils.object_from_module(settings.SEARCH_AT_RESULT)


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


class CmdGive(Command):
    """
    give away something to someone

    Usage:
      give (optional:<qty>) <inventory obj> <to||=> <target>

    Gives an items from your inventory to another character,
    placing it in their inventory.
    """

    key = "give"
    locks = "cmd:all()"
    arg_regex = r"\s|$"

    def parse(self):

        raw = self.args
        args = raw.strip()

        # Parse arguments
        self.args_list = args.split(" ")

        # Check for qty at first element in args list
        try:
            isInt = int(self.args_list[0])
        except ValueError:
            item = self.args_list[0]
            qty = None
        else:
            qty = int(self.args_list[0])
            item = self.args_list[1]

        self.target = self.args_list[-1]
        self.item = item
        self.qty = qty

    def func(self):

        # Get target and target handling
        if not self.args or not self.target:
            self.caller.msg("|540Usage: give <qty> <inventory object> to <target>|n\nNote - Quantity of an item is optional and only works on reosources or currency - ex: give 5 gold to Tom.")
            return

        target = self.caller.search(self.target)

        if target == self.caller:
            self.caller.msg(f"You keep {self.item} to yourself.")
            return

        """
        Check to see if given item is a resource before defaulting to caller inventory.
        """

        resource_dict = {"iron_ingots": ["iron", "ingots", "iron ingots"],
                          "refined_wood": ["refined", "wood", "refined wood"],
                          "leather": ["leather"],
                          "cloth": ["cloth"],
                          "gold": ["gold", "gold dragons"],
                          "silver": ["silver", "silver dragons"],
                          "copper": ["copper", "copper dragons"]}


        # Begin logic to check if item given is a resource or currency
        resource_array = [v for k, v in resource_dict.items()]
        flat_resource_array = [alias for alias_list in resource_array for alias in alias_list]

        # If the item is in the list of aliases, find its corresponding key.
        if self.item.lower() in flat_resource_array and self.qty is not None:
            item_db_key = [k for k, v in resource_dict.items() if self.item.lower() in v[:]]

            # Check to see if item qty exists as attribute value on caller.
            # Get qty by calling get method. Only thing calling this can be players, so will always have attribute.

            caller_item_qty = self.caller.attributes.get(item_db_key[0])
            if caller_item_qty >= self.qty:
                attribute = self.caller.attributes.get(item_db_key[0], return_obj=True)
                # Update target's corresponding attribute by self.qty.
                # Check to make sure target has attribute.
                try:
                    target_attribute = target.attributes.get(item_db_key[0], return_obj=True, raise_exception=True)
                # If not, throw an error.
                except AttributeError:
                    self.msg("|540You need to specify an appropriate target.|n")
                else:
                    attribute.value -= self.qty
                    target_attribute.value += self.qty
                    self.msg(f"You give {self.qty} {self.item} to {self.target}")
                    self.msg(f"You have {self.caller.attributes.get(item_db_key[0])} {self.item} left.")
            else:
                self.msg(f"|400You don't have enough {self.item}.|n")

        else:

            # Default give code
            to_give = self.caller.search(
                self.item,
                location=self.caller,
                nofound_string=f"|540You aren't carrying a {self.item}. If you want to give resources or currency please specify a quantity before the item. Ex: give 1 gold to Tom.|n" ,
                multimatch_string=f"|540You carry more than one {self.item}|n:" ,
            )

            if not (to_give and target):
                return

            if not to_give.location == self.caller:
                caller.msg("You are not holding %s." % to_give.key)
                return

            # calling at_before_give hook method
            if not to_give.at_before_give(self.caller, target):
                return

            # give object
            self.caller.msg("You give %s to %s." % (to_give.key, target.key))
            to_give.move_to(target, quiet=True)
            target.msg("%s gives you %s." % (self.caller.key, to_give.key))
            # Call the object script's at_give() method.
            to_give.at_give(self.caller, target)



class CmdEquip(Command):
    """Equip a weapon or shield

    Usage: equip <weapon, shield, or armor>

    Searches the callers inventory and puts the item in the right_slot if 1H, and then the left_slot
    if the character equips something else.
    If the item is denoted as 2H, it will occupy both slots.
    """

    key = "equip"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.item = self.args.strip()
        self.right_slot = self.caller.db.right_slot
        self.left_slot = self.caller.db.left_slot

    def func(self):
        if not self.item:
            self.caller.msg("|540Usage: equip <item>|n")
            return

        item = self.caller.search(self.item,
                                  location=self.caller,
                                  nofound_string=f"|540You aren't carrying a {self.item}.|n",
                                  multimatch_string=f"|540You carry more than one {self.item}|n:",
                                  )

        # Check if the item is of an a
        prototype = prototypes.search_prototype(item, require_single=True)

        try:
            prototype = prototypes.search_prototype(self.item, require_single=True)
        except KeyError:
            self.msg("Item not found, or more than one match. Please try again.")



        if item and item not in self.right_slot:
            if not item.db.broken:
                # Check if item is twohanded
                if item.db.twohanded:
                    if not self.right_slot and not self.left_slot:
                        self.right_slot.append(item)
                        self.left_slot.append(item)
                        # Send some messages
                        self.caller.location.msg_contents(f"{self.caller.key} equips their {item.key}.")
                        self.caller.msg(f"You have equipped your {item.key}")
                    else:
                        self.caller.msg(f"You can't equip the {item} unless you first unequip something.")
                        return
                # Check to see if right hand is empty.
                elif not self.right_slot:
                    self.right_slot.append(item)
                    # Send some messages
                    self.caller.location.msg_contents(f"{self.caller.key} equips their {item.key}.")
                    self.caller.msg(f"You have equipped your {item.key}")
                elif not self.left_slot:
                    self.left_slot.append(item)
                    # Send some messages
                    self.caller.location.msg_contents(f"{self.caller.key} equips their {item.key}.")
                    self.caller.msg(f"You have equipped your {item.key}")
                else:
                    self.caller.msg("You are carrying items in both hands.")
                    return
            else:
                self.caller.msg(f"{item} is broken and may not be equipped.")
        else:
            self.msg("|400You can't equip the same weapon twice.|n")


class CmdUnequip(Command):
    """Equip a weapon or shield

    Usage: unequip <weapon or shield>

    Searches the callers right or left slot.
    If item is denoted as 2H, remove from both slots.
    If item is not, remove it from the equipped slot.
    """

    key = "unequip"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.item = self.args.strip()
        self.right_slot = self.caller.db.right_slot
        self.left_slot = self.caller.db.left_slot

    def func(self):
        if not self.item:
            self.caller.msg("|540Usage: unequip <item>|n")
            return

        item = self.caller.search(self.item)

        if item:
            # Check if item is twohanded
            if item.db.twohanded:
                self.right_slot.remove(item)
                self.left_slot.remove(item)
            # Check to see if right hand is empty.
            elif item in self.right_slot:
                self.right_slot.remove(item)
            elif item in self.left_slot:
                self.left_slot.remove(item)
            else:
                self.caller.msg(f"You aren't carrying a {item}.")
                return

            self.caller.location.msg_contents(f"{self.caller.key} unequips their {item.key}.")
            self.caller.msg(f"You have unequipped your {item}.")
        else:
            self.caller.msg(f"Please be more specific.")


class SetArmorValue(Command):
    """Set the armor level of a character

    Usage: setarmorvalue <value>

    This sets the armor of the current character. This command is available to all characters.
    """

    key = "setarmorvalue"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setarmorvalue <value>|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            armor_value = int(self.args)
            # Error handling to keep from going below 0.
            if armor_value < 0:
                self.caller.msg("|400You may not set a value lower than 0.|n")
                return

        except ValueError:
            self.caller.msg(errmsg)
            return

        else:
            # Track hits by getting current armor value and looking at difference to return message.
            current_armor = self.caller.db.armor
            # at this point the argument is tested as valid. Let's set it.
            self.caller.db.armor = armor_value
            # Messages to emote that caller is taking damage
            if current_armor > armor_value:
                # Get amount of damage taken
                damage = current_armor - armor_value
                self.caller.location.msg_contents(f"|400{self.caller.key} takes {damage} damage to their armor.|n")

            if armor_value == 0:
                self.caller.msg("|400Your armor is now badly damaged and needs to be repaired.\nPlease see a blacksmith.|n")

            # Get vals for armor value calc
            tough = self.caller.db.tough
            shield_value = self.caller.db.shield_value if self.caller.db.shield == True else 0
            armor_specialist = 1 if self.caller.db.armor_specialist == True else 0

            # Add them up and set the curent armor value in the database
            currentArmorValue = armor_value + tough + shield_value + armor_specialist
            self.caller.db.av = currentArmorValue

            # Return armor value to console.
            self.caller.msg(f"|540Your current Armor Value is {currentArmorValue}:\nArmor: {armor_value}\nTough: {tough}\nShield: {shield_value}\nArmor Specialist: {armor_specialist}")


class SetTracking(Command):
    """Set the tracking of a character

    Usage: settracking <0-3>

    This sets the tracking of the current character. This can only be
    used during character generation.
    """

    key = "settracking"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: settracking <0-3>|n\n|400You must supply a number between 0 and 3.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            tracking = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= tracking <= 3):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.tracking = tracking
        self.caller.msg("|540Your Tracking was set to %i.|n" % tracking)



class SetPerception(Command):
    """Set the perception of a character

    Usage: setperception <0-3>

    This sets the perception of the current character. This can only be
    used during character generation.
    """

    key = "setperception"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setperception <0-3>|n\n|400You must supply a number between 0 and 3.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            perception = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= perception <= 3):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.perception = perception
        self.caller.msg("|540Your Perception was set to %i.|n" % perception)


class SetMasterOfArms(Command):
    """Set the tracking of a character

    Usage: setmasterofarms <0-3>

    This sets the master of arms of the current character. This is available to all characters.
    """

    key = "setmasterofarms"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setmasterofarms <0-3>|n\n|400You must supply a number between 0 and 3.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            master_of_arms = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= master_of_arms <= 3):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.master_of_arms = master_of_arms
        self.caller.msg("|540Your Master of Arms was set to %i.|n" % master_of_arms)


class SetTough(Command):
    """Set the tough of a character

    Usage: settough <value>

    This sets the tough of the current character. This is available to all characters.
    """

    key = "settough"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: settough <value>|n\n|400You must supply a number 0 or greater.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            tough = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return

        if tough < 0:
            self.caller.msg(errmsg)
        else:
            # at this point the argument is tested as valid. Let's set it.
            self.caller.db.tough = tough
            self.caller.msg("|540Your Tough was set to %i.|n" % tough)

            # Get armor value objects
            armor = self.caller.db.armor
            tough = self.caller.db.tough
            shield_value = self.caller.db.shield_value if self.caller.db.shield == True else 0
            armor_specialist = 1 if self.caller.db.armor_specialist == True else 0

            # Add them up and set the curent armor value in the database
            currentArmorValue = armor + tough + shield_value + armor_specialist
            self.caller.db.av = currentArmorValue

            # Return armor value to console.
            self.caller.msg(f"|540Your current Armor Value is {currentArmorValue}:\nArmor: {armor}\nTough: {tough}\nShield: {shield_value}\nArmor Specialist: {armor_specialist}|n")


class SetShieldValue(Command):
    """Set the shield value of a shield item.

    Usage: setshieldvalue <value>

    Available to all characters. Adds to total Armor Value db object.
    """
    key = "setshieldvalue"
    help_category = "mush"

    def func(self):
        """Performs the command"""
        errmsg = "|540Usage: setshieldvalue <value>|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            shield_value = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return

        # Error handling to keep from going below 0.
        if shield_value < 0:
            self.caller.msg("|540Usage: setshieldvalue <value>|n\n|400You may not set a value lower than 0.|n")
        elif shield_value == 0:
            self.caller.msg("|400Your shield is now badly damaged and needs to be repaired.\nPlease see a blacksmith.|n")
            zero_av = self.caller.db.armor + self.caller.db.tough + self.caller.db.shield_value + self.caller.db.armor_specialist
            self.caller.msg(f"|540Your current Armor Value is {zero_av}:\nArmor: {self.caller.db.armor}\nTough: {self.caller.db.tough}\nShield: {self.caller.db.shield_value}\nArmor Specialist: {self.caller.db.armor_specialist}|n")
        else:
            # at this point the argument is tested as valid. Let's set it.
            self.caller.db.shield_value = shield_value
            self.caller.msg("|540Your Shield Value was set to %i.|n" % shield_value)

            # Get armor value objects
            shield_value = self.caller.db.shield_value if self.caller.db.shield == True else 0
            armor_specialist = self.caller.db.armor_specialist
            armor = self.caller.db.armor
            tough = self.caller.db.tough

            # Add them up and set the curent armor value in the database
            currentArmorValue = armor + tough + shield_value + armor_specialist
            self.caller.db.av = currentArmorValue

            # Return armor value to console.
            self.caller.msg(f"|540Your current Armor Value is {currentArmorValue}:\nArmor: {armor}\nTough: {tough}\nShield: {shield_value}\nArmor Specialist: {armor_specialist}|n")

class SetBody(Command):
    """Set the body of a character

    Usage: setbody <value>

    This sets the body of the current character. This is available to all characters.
    """

    key = "setbody"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setbody <value>|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            body = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return

        # Error handling to keep from going below -6.
        if body < -6:
            self.caller.msg("|540Usage: setbody <value>|n\n|400You may not set a value lower than -6.|n")
        elif body > 3:
            self.caller.msg("|540Usage: setbody <value>|n\n|400You may not set a value higher than 3.|n")
        else:
            current_body = self.caller.db.body

            # at this point the argument is tested as valid. Let's set it.
            self.caller.db.body = body
            self.caller.msg("|540Your Body was set to %i.|n" % body)
            if current_body > body:
                damage = current_body - body
                self.caller.location.msg_contents(f"|400{self.caller.key} takes {damage} damage to their body.|n")
            if body == 0:
                self.caller.location.msg_contents(f"|400{self.caller.key} is now bleeding profusely from many wounds.|n")

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
        errmsg = "|540Usage: setarmorspecialist <0 or 1>|n\n|400You must supply a value between 0 and 1.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            armor_specialist = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return

        # Extending range for knight ability
        if not (0 <= armor_specialist <= 1):
            self.caller.msg(errmsg)
        else:
            self.caller.db.armor_specialist = armor_specialist

            # Get armor value objects
            armor = self.caller.db.armor
            tough = self.caller.db.tough
            shield_value = self.caller.db.shield_value if self.caller.db.shield == True else 0

            # Add them up and set the curent armor value in the database
            currentArmorValue = armor + tough + shield_value + armor_specialist
            self.caller.db.av = currentArmorValue

            # Return armor value to console.
            self.caller.msg(f"|540Your current Armor Value is {currentArmorValue}:\nArmor: {armor}\nTough: {tough}\nShield: {shield_value}\nArmor Specialist: {armor_specialist}|n")

class SetWyldingHand(Command):
    """Set the wylding hand level of a character

    Usage: setwyldinghand <0-3>

    This sets the wylding hand level of the current character. This can only be
    used during character generation.
    """

    key = "setwyldinghand"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setwyldinghand <0-3>|n\n|400You must supply a number between 0 and 3.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            wyldinghand = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= wyldinghand <= 3):
            self.caller.msg(errmsg)
        else:
            # at this point the argument is tested as valid. Let's set it.
            self.caller.db.wyldinghand = wyldinghand
            self.caller.msg(f"Your level of Wylding Hand was set to {wyldinghand}")

class SetResilience(Command):
    """Set the resilience level of a character

    Usage: setresilience <0 - 3>

    This sets the resilience level of the current character. This can only be
    used during character generation.
    """

    key = "setresilience"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setresilience <0 - 3>|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            resilience = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.resilience = resilience
        # Add one point to total bleed points per level.
        self.caller.db.bleed_points += resilience
        self.caller.msg("Your Resilience level was set to %i." % resilience)


class SetWeaponValue(Command):
    """Set the weapon level of a character

    Usage: setweaponvalue <0 - 4>

    This sets the weapon level of the current character. This can only be
    used during character generation.
    """

    key = "setweaponvalue"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setweaponvalue <0 - 4>|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            weapon_value = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.weapon_level = weapon_value
        self.caller.msg("Your Weapon Value was set to %i." % weapon_value)


class SetBow(Command):
    """Set the bow property of a character

    Usage: setbow <0/1>

    This sets the bow of the current character. This can be used at any time during the game.
    """

    key = "setbow"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setbow <0/1>|n\n|400You must supply a value of either 0 or 1.|n"
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
        else:
            # Bow/melee error handling
            if hasMelee:
                self.caller.msg("|540Before using a bow, you must first unequip your melee weapon using the command setmelee 0.|n")
            else:
                self.caller.db.bow = bow

                # Quippy message when setting a shield as 0 or 1.
                if bow:
                    self.caller.msg("|030You have equipped your bow.|n")
                    self.caller.location.msg_contents(f"|230{self.caller.key} has equipped their bow.|n")
                else:
                    self.caller.msg("|400You have unequipped your bow.|n")
                    self.caller.location.msg_contents(f"|230{self.caller.key} unequips their bow.|n")


class SetMelee(Command):
    """Set the melee property of a character

    Usage: setmelee <0/1>

    This sets the melee of the current character. This can be used at any time during the game.
    """

    key = "setmelee"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setmelee <0/1>|n\n|400You must supply a value of 0 or 1.|n"
        hasBow = self.caller.db.bow
        hasWeapon = self.caller.db.weapon_level

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
                self.caller.msg("|540Before using a melee weapon, you must first unequip your bow using the command setbow 0.|n")
            else:
                self.caller.db.melee = melee

                # Quippy message when setting a weapon as 0 or 1.
                if melee and hasWeapon:
                    self.caller.msg("|030You are now ready to fight.|n")
                    self.caller.location.msg_contents(f"|230{self.caller.key} has equipped their weapon.|n")
                elif melee and not hasWeapon:
                    self.caller.location.msg_contents(f"|230{self.caller.key} assumes a defensive posture.")
                elif not melee and hasWeapon:
                    self.caller.location.msg_contents(f"|230{self.caller.key} sheathes their weapon.|n")
                else:
                    self.caller.location.msg_contents(f"|230{self.caller.key} relaxes their defensive posture.|n")


class SetResist(Command):
    """Set the resist level of a character

    Usage: setresist <0,1,2,3,4,5>

    This sets the resist level of the current character. This can only be
    used during character generation.
    """

    key = "setresist"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setresist <0-5>|n\n|400You must supply a number between 0 and 5.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            resist = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= resist <= 5):
            self.caller.msg(errmsg)
        else:
            # at this point the argument is tested as valid. Let's set it.
            self.caller.db.resist = resist
            self.caller.msg("Your resist level was set to %i." % resist)


class SetDisarm(Command):
    """Set the disarm level of a character

    Usage: setdisarm <0,1,2,3,4,5>

    This sets the disarm level of the current character. This can only be
    used during character generation.
    """

    key = "setdisarm"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setdisarm <0-5>|n\n|400You must supply a number between 0 and 5.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            disarm = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= disarm <= 5):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.disarm = disarm
        self.caller.msg("Your disarm level was set to %i." % disarm)


class SetCleave(Command):
    """Set the cleave level of a character

    Usage: setcleave <0,1,2,3,4,5>

    This sets the cleave level of the current character. This can only be
    used during character generation.
    """

    key = "setcleave"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setcleave <0-5>|n\n|400You must supply a number between 0 and 5.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            cleave = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= cleave <= 5):
            self.caller.msg(errmsg)
        else:
            # at this point the argument is tested as valid. Let's set it.
            self.caller.db.cleave = cleave
            self.caller.msg("Your cleave level was set to %i." % cleave)


class SetStun(Command):
    """Set the stun level of a character

    Usage: setstun <0,1,2,3,4,5>

    This sets the stun level of the current character. This can only be
    used during character generation.
    """

    key = "setstun"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setstun <0-5>|n\n|400You must supply a number between 0 and 5.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            stun = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= stun <= 5):
            self.caller.msg(errmsg)
        else:
            # at this point the argument is tested as valid. Let's set it.
            self.caller.db.stun = stun
            self.caller.msg("Your stun level was set to %i." % stun)


class SetSunder(Command):
    """Set the stun level of a character

    Usage: setsunder <0,1,2,3,4,5>

    This sets the stun level of the current character. This can only be
    used during character generation.
    """

    key = "setsunder"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setsunder <0-5>|n\n|400You must supply a number between 0 and 5.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            sunder = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= sunder <= 5):
            self.caller.msg(errmsg)
        else:
            # at this point the argument is tested as valid. Let's set it.
            self.caller.db.sunder = sunder
            self.caller.msg("Your sunder level was set to %i." % sunder)


class SetStagger(Command):
    """Set the stagger level of a character

    Usage: setstun <0,1,2,3,4,5>

    This sets the stagger level of the current character. This can only be
    used during character generation.
    """

    key = "setstagger"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setstagger <0-5>|n\n|400You must supply a number between 0 and 5.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            stagger = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= stagger <= 5):
            self.caller.msg(errmsg)
        else:
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
        errmsg = "|540Usage: setshield <0/1>|n\n|400You must supply a value of 0 or 1.|n"
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
        else:
            self.caller.db.shield = shield

            # Quippy message when setting a shield as 0 or 1.
            if shield:
                self.caller.msg("|030You now have a shield.|n")
                self.caller.location.msg_contents(f"|230{self.caller.key} equips their shield.|n")
            else:
                self.caller.msg("|400You have unequipped or lost your shield.|n")
                self.caller.location.msg_contents(f"|230{self.caller.key} unequips their shield.|n")

            # Get armor value objects
            armor = self.caller.db.armor
            tough = self.caller.db.tough
            shield_value = self.caller.db.shield_value if self.caller.db.shield == True else 0
            armor_specialist = 1 if self.caller.db.armor_specialist is 1 else 0

            # Add them up and set the curent armor value in the database
            currentArmorValue = armor + tough + shield_value + armor_specialist
            self.caller.db.av = currentArmorValue

            # Return armor value to console.
            self.caller.msg(f"|540Your current Armor Value is {currentArmorValue}:\nArmor: {armor}\nTough: {tough}\nShield: {shield_value}\nArmor Specialist: {armor_specialist}|n")


class SetTwoHanded(Command):
    """Set the two handed weapon status of a character

    Usage: settwohander <0,1>

    This sets the two handed weapon status of the current character.
    """

    key = "settwohanded"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: settwohanded <0/1>|n\n|400You must supply a value of either 0 or 1.|n"
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
        else:
            # at this point the argument is tested as valid. Let's set it.
            self.caller.db.twohanded = twohanded

            if twohanded:
                self.caller.msg("|030Your have equipped a two-handed melee weapon.|n")
            else:
                self.caller.msg("|400You have unequipped a two-handed melee weapon.|n")


"""
General commands
"""

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
        # No args error handler
        if not self.args or not self.rhs:
            self.caller.msg("Usage: @perception level key = description")
            return

        # Get level of perception
        try:
            level = int(self.args[0])

        except:
            self.caller.msg("|540Usage: @perception level key = description|n")

        else:
            if level in (1,2,3):
                # Get perception setting objects
                equals = self.args.index("=")
                object = str(self.args[1:equals]).strip()
            if not object:
                self.caller.msg("|400Nothing here by that name or description|n")
                return
            # if not hasattr(self.obj, "set_perception"):
            #     self.caller.msg("Perception cannot be set on %s." % self.obj)
            #     return
            # self.obj = object
            looking_at_obj = self.caller.search(
                object,
                # note: excludes room/room aliases
                # look for args in room and on self
                # candidates=self.caller.location.contents + self.caller.contents,
                use_nicks=True,
                quiet=True,
            )
            if looking_at_obj:
                self.obj = looking_at_obj[0]
                # self.caller.msg(f"You are looking at {self.obj}")
                # Set the perception object in the database
                self.obj.set_perception(self.obj, level, self.rhs)
                # Message to admin for confirmation.
                self.caller.msg(f"|540Perception set on {self.obj.name}\nLevel: {level}\nDescription: {self.rhs}|n")
            else:
                self.caller.msg("|400Search didn't return anything.|n")

class CmdTracking(default_cmds.MuxCommand):
    """
    sets a detail on a room
    Usage:
        @tracking <level> <key> = <description>
        @tracking <level> <key>;<alias>;... = description
    Example:
        @tracking 1 walls = The walls are covered in ...
        @tracking 3 castle;ruin;tower = The distant ruin ...
    This sets a "perception" on the object this command is defined on
    . This detail can be accessed with
    the TutorialRoomLook command sitting on TutorialRoom objects (details
    are set as a simple dictionary on the room). This is a Builder command.
    We custom parse the key for the ;-separator in order to create
    multiple aliases to the detail all at once.
    """

    key = "@tracking"
    locks = "cmd:perm(Builder)"
    help_category = "mush"


    def func(self):
        """
        All this does is to check if the object has
        the set_perception method and uses it.
        """
        errmsg = "|540Usage: @tracking level key = description|n"

        if not self.args or not self.rhs:
            self.caller.msg(errmsg)
            return

        # Get level of perception
        try:
            level = int(self.args[0])

        except:
            self.caller.msg(errmsg)

        else:
            if level in (1,2,3):
                # Get perception setting objects
                equals = self.args.index("=")
                object = str(self.args[1:equals]).strip()
            if not object:
                self.caller.msg("|400Nothing here by that name or description|n")
                return
            # if not hasattr(self.obj, "set_perception"):
            #     self.caller.msg("Perception cannot be set on %s." % self.obj)
            #     return
            # self.obj = object
            looking_at_obj = self.caller.search(
                object,
                # note: excludes room/room aliases
                # look for args in room and on self
                # candidates=self.caller.location.contents + self.caller.contents,
                use_nicks=True,
                quiet=True,
            )
            if looking_at_obj:
                self.obj = looking_at_obj[0]
                # self.caller.msg(f"You are looking at {self.obj}")
                # Set the perception object in the database
                self.obj.set_tracking(self.obj, level, self.rhs)
                # Message to admin for confirmation.
                self.caller.msg(f"|540Tracking set on {self.obj.name}\nLevel: {level}\nDescription: {self.rhs}|n")
            else:
                self.caller.msg("|400Search didn't return anything.|n")


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


"""
Carnival commands
"""
# Fortune teller in Carnival
class CmdPull(Command):
    """
    Usage: pull crank

    Should get a fortune from the Artessa machine in the room. Command tied to room only.
    """

    key = "pull"

    def func(self):
        # Try and find caller key in fortuneStrings. If found, return fortune Value
        # Remove it from the fortuneString dict
        # If not found return a default fortune string
        args = self.args

        err_msg = "|540Usage: pull crank|n"
        fortuneStrings = ["|540Unknow all that you think you know.|n",
                          "|540You have what many want, though you still want more.|n",
                          "|540Who is the little brother.|n",
                          "|540I am not who they say I am.|n",
                          "|540Can you help me?|n",
                          "|540Be careful in the hall of mirrors. The cats are friends. Do not let the child catch them, for he is cruel.|n",
                          "|540Nothing here is as it seems.|n",
                          "|540Did you see them set up? Did you see any of it?|n",
                          "|540Who are the Bordello Brothers|n",
                          "|540Where is this place?|n",
                          "|540Please...|n"
                          ]

        if not self.args:
            self.caller.msg(err_msg)
            return
        try:
            args == "crank"
        except ValueError:
            self.caller.msg(err_msg)
            return
        else:
            fortune = random.choice(fortuneStrings)
            self.caller.msg(fortune)


class CmdThrow(Command):
    """
    Usage: throw dagger

    Should get a fortune from the Artessa machine in the room. Command tied to room only.
    """

    key = "throw"

    def func(self):
        # Try and find caller key in fortuneStrings. If found, return fortune Value
        # Remove it from the fortuneString dict
        # If not found return a default fortune string
        h = Helper()
        args = self.args

        err_msg = "|540Usage: throw dagger|n"

        # Generate dc for target.
        target_dc = random.randint(1,6)

        # Generate throw result
        master_of_arms = self.caller.db.master_of_arms
        die_result = h.masterOfArms(master_of_arms)

        if not self.args:
            self.caller.msg(err_msg)
            return
        try:
            args == "dagger"
        except ValueError:
            self.caller.msg(err_msg)
            return
        else:
            if die_result > target_dc:
                # If the caller has done this before they will always get a skull ticket. Update their pariticpant status in the db as 1.
                # If the caller has not done this before, they should get a result from the random ticket chance.
                # Check the database to make sure that the jester ticket hasn't been chosen yet.
                # If a player gets the random jester ticket from this booth, it should log the entry in the database and not allow it to be generated again.
                self.caller.location.msg_contents(f"|230{self.caller.key} picks up a dagger from the table, takes aim, and hurls the dagger downfield striking true.|n")
            else:
                self.caller.location.msg_contents(f"|230{self.caller.key} picks up a dagger from the table, takes aim, and hurls the dagger downfield wide of the target.|n")


class CmdStart(Command):
    """
    Usage: start

    Returns someone back to the start of the maze.
    """

    key = "start"

    def func(self):
        # Try and find caller key in fortuneStrings. If found, return fortune Value
        # Remove it from the fortuneString dict
        # If not found return a default fortune string

        # Generate throw result
        self.caller.msg(f"|/|540Giving up so soon, {self.caller.name}? You were doing so well. Be sure to try again soon.|n|/|230You notice a door open up where before there was none. Stepping through it, you find yourself back in the foyer of the strange maze.|n|/")
        maze_foyer = self.caller.search('#449')
        self.caller.move_to(maze_foyer)



class CmdPushButton(Command):
    """
    Usage: push button

    Pushes button on the box in each carnival attraction.
    Generates either a jester or skull card object. Each box only has one jester card with a 1/30 chance to draw it.
    Once the jester card has been drawn, update the corresponding database entry to True for the box object.
    If anyone tries to push the button once a winner has been chosen, only skull tickets are generated.
    """

    key = "push button"
    aliases = ["push", "button", "press button"]
    locks = "cmd:all()"

    def func(self):
        """
        Push the button. Check the database for a winner.
        If none, there's 1/30 chance you'll draw the jester card.
        If drawn, update entry with hasWinner = 1. Drop card object with description of jester on it.
        If not, player gets a skull ticket.
        """
        hasWinner = self.obj.db.hasWinner

        # Commands to generate tickets
        button_emote = f"|230{self.caller} pushes the button. After a brief pause, a ticket pops up from a small slit on the top of the box.|n"
        get_ticket_emote = "|540A ticket pops up from a small slit in the top of the box.|n\n|540Use the |nget ticket|540 command to pick it up|n\n|540Use the |nlook ticket|540 command to examine it.|n"

        # If the player has already pressed the button on this particular box, nothing happens.
        if self.caller in self.obj.db.characters:
            self.caller.msg(f"|540\"I'm sorry {self.caller},\" a mysterious voice whispers. \"You've already played my little game... I would very much like it if your friends played. You could try your luck in another tent...\" The voice seemed to come from the wooden box, but how is difficult to tell.|n")

        # If the box counter is under thirty and there is no winner yet...
        elif self.obj.db.counter < 30 and not hasWinner:
            draw = random.randint(1,30)
            self.obj.db.counter += 1
            if draw == 30:
                self.obj.db.hasWinner = True
                self.dropCard("grinning skull")
            else:
                self.dropCard("sinister looking jester")

        # If the box counter is over thirty and there is no winner yet...
        elif self.obj.db.counter >= 30 and not hasWinner:
            self.obj.db.hasWinner = True
            self.obj.db.counter += 1
            self.dropCard("grinning skull")

        # If the box counter is over thirty and the winning ticket has already been given out...
        else:
            self.obj.db.counter += 1
            self.dropCard("sinister looking jester")

    def dropCard(self, cardType):
        # Commands to generate tickets
        button_emote = f"|230{self.caller} pushes the button. After a brief pause, a ticket pops up from a small slit on the top of the box.|n"
        get_ticket_emote = "|540A ticket pops up from a small slit in the top of the box.|n\n|540Use the |nget ticket|540 command to pick it up|n\n|540Use the |nlook ticket|540 command to examine it.|n"

        # Drop a ticket object with a skull description
        self.caller.msg(get_ticket_emote)
        self.caller.location.msg_contents(button_emote)
        self.obj.db.characters.append(self.caller)
        # Call spawner
        ticket = spawn({"key": "A Small Paper Ticket", "desc": "|yThis is a small, rectangular slip of stained paper. On one side is the faded black and white stamp of a " + cardType + ".", "location": self.caller.location, "aliases": ["ticket", "small ticket"]})


class CmdSwing(Command):
    """
    Usage: swing hammer

    Swings hammer at the Hammer attraction.
    """

    key = "swing"

    def func(self):
        # Try and find caller key in fortuneStrings. If found, return fortune Value
        # Remove it from the fortuneString dict
        # If not found return a default fortune string
        h = Helper()
        args = self.args

        err_msg = "|540Usage: swing hammer|n"

        # Generate dc for target.
        target_dc = random.randint(1,6)

        # Generate throw result
        master_of_arms = self.caller.db.master_of_arms
        wyldinghand = self.caller.db.wyldinghand

        if master_of_arms:
            die_result = h.masterOfArms(master_of_arms)
        elif wyldinghand:
            die_result = h.wyldingHand(wyldinghand)
        else:
            die_result = random.randint(1, 4)

        if not self.args:
            self.caller.msg(err_msg)
            return
        try:
            args == "hammer"
        except ValueError:
            self.caller.msg(err_msg)
            return
        else:
            if die_result > (target_dc * 2):
                self.caller.location.msg_contents(f"|/|230{self.caller.key} picks up the hammer, hoists it over their head and brings it down upon the heavy wooden board, sending the metal pin up and up, until it hits the rusty bell. The sound it makes is a rather anti-climatic, hollow clang.|n|/")

            elif die_result == target_dc:
                self.caller.location.msg_contents(f"|/|230{self.caller.key} picks up the hammer, hoists it over their head and brings it down upon the heavy wooden board. The metal pin climbs up towards the rusty bell but falls short, just before reaching the top.|n|/")

            else:
                self.caller.location.msg_contents(f"|/|230{self.caller.key} picks up the hammer, hoists it over their head and brings it down upon the heavy wooden board. The metal pin climbs up towards the rusty bell but falls short, well before reaching the top.|n|/")
"""
Healing commands
"""

class CmdMedicine(Command):
    key = "medicine"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):
        "This actually does things"
        # Check for correct command
        if not self.args:
            self.caller.msg("|540Usage: medicine <target>|n")
            return

        target = self.caller.search(self.target)

        if not target:
            self.caller.msg("|400There is nothing here by that description.|n")
            return

        # Get caller level of medicine and emote how many points the caller will heal target that round.
        # May not increase targets body past 1
        # Only works on targets with body <= 0

        target_body = target.db.body
        medicine = self.caller.db.medicine

        # Check for skill and object is valid type.
        if medicine and target_body is not None:

            if (- 3 <= target_body <= 0):
                # Return message to area and caller
                if target == self.caller:
                    self.caller.location.msg_contents(f"|230{self.caller} pulls bandages and ointments from their bag, and starts to mend their wounds.|n\n|540{self.caller} heals |n|020{medicine}|n |540body points per round as long as their work remains uninterrupted.|n")
                    # Check to see if caller would go over 1 body with application of skill.
                    if (self.caller.db.body + medicine) > 1:
                        # If so set body to 1
                        self.caller.db.body = 1
                        self.caller.msg(f"|540Your new body value is:|n {self.caller.db.body}|n")
                    else:
                        # If not over 1, add points to total
                        self.caller.db.body += medicine
                        self.caller.msg(f"|540Your new body value is:|n {self.caller.db.body}|n")
                    # Check to see if weakness set. If not, set it.
                    if not self.caller.db.weakness:
                        self.caller.db.weakness = 1

                elif target != self.caller:
                    self.caller.location.msg_contents(f"|230{self.caller.key} comes to {target.key}'s rescue, healing {target.key}.|n\n|540{self.caller.key} heals {target.key} for|n |020{medicine}|n |540body points per round as long as their work remains uninterrupted.|n")
                    if (target.db.body + medicine) > 1:
                        # If so set body to 1
                        target.db.body = 1
                        target.msg(f"|540Your new body value is:|n {target.db.body}|n")
                        # Check to see if weakness set. If not, set it.
                    else:
                        # If not over 1, add points to total
                        target.db.body += medicine
                        target.msg(f"|540Your new body value is:|n {target.db.body}|n")
                    # Check to see if weakness set. If not, set it.
                    if not target.db.weakness:
                        target.db.weakness = 1


            # Handle when target is too fargone to apply medicine
            elif (-6 <= target_body <= -4):
                if target == self.caller:
                    self.caller.msg(f"|400{self.caller} You are too fargone to attempt this action.|n")
                elif target != self.caller:
                    self.caller.location.msg_contents(f"|230{self.caller.key} comes to {target.key}'s rescue, though they are too fargone.\n{target.key} may require the aid of more advanced chiurgical techniques.|n")

            elif target_body >= 1:
                self.caller.msg(f"|230{target.key} doesn't require the application of your chiurgical skills. They seem to be healthy enough.|n")

            else:
                self.caller.msg("|540Better not. You aren't quite that skilled.|n")

        else:
            self.caller.msg("|400You had better not try that.|n")


class CmdChirurgery(Command):
    """Performs the chiurgeon skill.
    Restores a character to 3 body points, and removes the weakness state.
    """

    key = "heal"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):
        "This actually does things"
        # Check for correct command
        if not self.args:
            self.caller.msg("|540Usage: heal <target>|n")
            return

        target = self.caller.search(self.target)

        if not target:
            self.caller.msg("|540There is nothing here by that description.|n")
            return

        # Get target body and BM to validate target and caller has skill.
        target_body = target.db.body
        chirurgeon = self.caller.db.chirurgeon
        weakness = target.db.weakness

        # Condition = body cant be below -6 or above 3

        if chirurgeon and target_body is not None:
            # Return message to area and caller
            if target == self.caller:

                if (target.db.body + 1) > 3 and not weakness:
                    self.caller.msg(f"|230{target.key} doesn't require the application of your chiurgical skills. They seem to be healthy enough.|n")

                elif (target.db.body + 1) > 3 and weakness:
                    self.caller.location.msg_contents(f"|230{self.caller.name} examines {target.key}'s body, taking studious notes of their injuries. {self.caller.name} dons gloves, a leather mask, and a ruddy leather apron, before picking up their first instrument and beginning the delicate procedure.|n")
                    self.caller.db.weakness = 0
                    self.caller.msg(f"|540The weakness condition has been removed.")

                else:
                    self.caller.location.msg_contents(f"|230{self.caller.name} examines {target.key}'s body, taking studious notes of their injuries. {self.caller.name} dons gloves, a leather mask, and a ruddy leather apron, before picking up their first instrument and beginning the delicate procedure.|n")
                    self.caller.db.weakness = 0
                    self.caller.db.body = 3
                    self.caller.msg(f"|540The weakness condition has been removed.\nYour new body value is:|n {self.caller.db.body}|n")


            elif target != self.caller:

                if (target.db.body + 1) > 3 and not weakness:
                    self.caller.msg(f"|230{target.key} doesn't require the application of your chiurgical skills. They seem to be healthy enough.|n")

                elif target.db.body < -6:
                    target.location.msg_contents(f"|230{self.caller.key} comes to {target.key}'s rescue, though they are too fargone.|n")

                else:
                    target.location.msg_contents(f"|230{self.caller.name} examines {target.key}'s body, taking studious notes of their injuries. {self.caller.name} dons gloves, a leather mask, and a ruddy leather apron, before picking up their first instrument and beginning the delicate procedure.|n")
                    target.db.body = 3
                    target.db.weakness = 0
                    target.msg(f"|540The weakness condition has been removed.\nYour new body value is:|n {target.db.body}|n")

        else:
            self.caller.msg("|400You had better not try that.|n")


class SetStabilize(Command):
    """Set the stun level of a character

    Usage: setstabilize <0,1,2,3>

    This sets the stabilize level of the current character. This can only be
    used during character generation.
    """

    key = "setstabilize"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setstabilize <0-3>|n\n|400You must supply a number between 0 and 3.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            stabilize = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return

        if not (0 <= stabilize <= 3):
            self.caller.msg(errmsg)
        else:
            # at this point the argument is tested as valid. Let's set it.
            self.caller.db.stabilize = stabilize
            self.caller.msg(f"Your stabilize level was set to {stabilize}")


class SetMedicine(Command):
    """Set the medicine level of a character

    Usage: setmedicine <0,1,2,3>

    This sets the medicine level of the current character. This can only be
    used during character generation.
    """

    key = "setmedicine"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setmedicine <0-3>|n\n|400You must supply a number between 0 and 3.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            medicine = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return

        if not (0 <= medicine <= 3):
            self.caller.msg(errmsg)
        else:
            # at this point the argument is tested as valid. Let's set it.
            self.caller.db.medicine = medicine
            self.caller.msg(f"Your medicine level was set to {medicine}")


class SetBattleFieldMedicine(Command):
    """Set the battlefieldmedicine level of a character

    Usage: setmedic <0,1>

    This sets the medicine level of the current character. This can only be
    used during character generation.
    """

    key = "setmedic"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setmedic <0/1>|n\n|400You must supply a number of either 0 or 1.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            battlefieldmedicine = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if battlefieldmedicine not in (0,1):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.battlefieldmedicine = battlefieldmedicine

        if battlefieldmedicine:
            self.caller.msg("|030You have activated the battlefield medicine ability.|n")
        else:
            self.caller.msg("|400You have deactivated the battlefield medicine ability.|n")


class SetChirurgeon(Command):
    """Activate the chirurgery ability.

    Usage: setchirurgeon <0,1>

    This sets the medicine level of the current character. This can only be
    used during character generation.
    """

    key = "setchirurgeon"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setchirurgeon <0/1>|n\n|400You must supply a number of either 0 or 1.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            chirurgeon = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if chirurgeon not in (0,1):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.chirurgeon = chirurgeon

        if chirurgeon:
            self.caller.msg("|030You have activated the chirurgeon ability.|n")
        else:
            self.caller.msg("|400You have deactivated the chirurgeon ability.|n")



"""
Knight skills
"""

class SetBattleFieldCommander(Command):
    """Set the battlefield commander level of a character

    Usage: setbattlefieldcommander <0,1,2,3>

    This sets the battlefield commander level of the current character. This can only be
    used during character generation.
    """

    key = "setbattlefieldcommander"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setbattlefieldcommander <0-3>|n\n|400You must supply a number between 0 and 3.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            battlefieldcommander = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= battlefieldcommander <= 3):
            self.caller.msg(errmsg)
        else:
            # at this point the argument is tested as valid. Let's set it.
            self.caller.db.battlefieldcommander = battlefieldcommander
            self.caller.msg(f"Your battlefield commander was set to {battlefieldcommander}")


class SetRally(Command):
    """Set the rally level of a knight character

    Usage: setrally <0,1,2,3>

    This sets the rally level of the current character. This can only be
    used during character generation.
    """

    key = "setrally"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setrally <0-3>|n\n|400You must supply a number between 0 and 3.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            rally = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= rally <= 3):
            self.caller.msg(errmsg)
        else:
            # at this point the argument is tested as valid. Let's set it.
            self.caller.db.rally = rally
            self.caller.msg(f"Your rally was set to {rally}")


"""
Effects status commands
"""

class SetWeakness(Command):
    """
    Sets the weakness status on a character. If set to 0, it also sets activemartialskill in db to 0.
    Likewise, if set to 1, it also sets activemartialskills to 1.
    """

    key = "setweakness"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|540Usage: setweakness <0/1>|n\n|400You must supply a number of either 0 or 1.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            weakness = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if weakness not in (0,1):
            self.caller.msg(errmsg)
        else:
            # at this point the argument is tested as valid. Let's set it.
            self.caller.db.weakness = weakness

            if weakness:
                self.caller.db.activemartialskill = 0
                self.caller.msg("|400You have become weakened, finding it difficult to run or use your active martial skills.|n\n|540As long as you are weakened you may not run or use active martial skills.|n")
            else:
                self.caller.db.activemartialskill = 1
                self.caller.msg("|030Your weakened state has subsided.|n\n|540You may now run and use your active martial skills.|n")

class CharSheet(Command):
    """
    Prints out the character's sheet and current status.
    """

    key = "charsheet"
    aliases = ["sheet", "char sheet", "character sheet", "view sheet"]
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):

        # target = self.caller.search(self.target)

        if self.target == "self" or self.target == "me" or not self.target:
            status_table = evtable.EvTable("|540Status|n", "|540Value|n",
                table = [
                    [
                        "Body",
                        "Weapon Value",
                        "Melee Weapon Equipped",
                        "Two-handed Equipped",
                        "Bow Equipped",
                        "Armor Value"
                    ],
                    [
                        self.caller.db.body,
                        self.caller.db.weapon_level,
                        self.caller.db.melee,
                        self.caller.db.twohanded,
                        self.caller.db.bow,
                        self.caller.db.av
                    ]
                ],
                border = "cells")
            active_marshall_table = evtable.EvTable("|540Active Marshall Skills|n", "|540Available|n",
                table = [
                    [
                        "Resist",
                        "Disarm",
                        "Stun",
                        "Stagger",
                        "Sunder",
                        "Cleave"
                    ],
                    [
                        self.caller.db.resist,
                        self.caller.db.disarm,
                        self.caller.db.stun,
                        self.caller.db.stagger,
                        self.caller.db.sunder,
                        self.caller.db.cleave
                    ]
                ],
                border = "cells")
            pass_marshall_table = evtable.EvTable("|540Passive Marshall Skills|n", "|540Level|n",
                table = [
                    [
                        "Shield",
                        "Tough",
                        "Armor",
                        "Master of Arms",
                        "Armor Specialist"
                    ],
                    [
                        self.caller.db.shield,
                        self.caller.db.tough,
                        self.caller.db.armor,
                        self.caller.db.master_of_arms,
                        self.caller.db.armor_specialist
                    ]
                ],
                border = "cells")

            generalist_table = evtable.EvTable("|540Generalist Skills|n", "|540Level|n",
                table = [
                    [
                        "Perception",
                        "Tracking",
                        "Medicine"
                    ],
                    [
                        self.caller.db.perception,
                        self.caller.db.tracking,
                        self.caller.db.medicine
                    ]
                ],
                border = "cells")

            profession_table = evtable.EvTable("|540Profession Skills|n", "|540Level|n",
                table = [
                    [
                        "Stabilize",
                        "Battlefield Medicine",
                        "Rally",
                        "Battlefield Commander",
                        "Wylding Hand"
                    ],
                    [
                        self.caller.db.stabilize,
                        self.caller.db.battlefieldmedicine,
                        self.caller.db.rally,
                        self.caller.db.battlefieldcommander,
                        self.caller.db.wyldinghand
                    ]
                ],
                border = "cells")

            status_table.reformat_column(0, width=30, align="l")
            status_table.reformat_column(1, width=15, align="c")
            active_marshall_table.reformat_column(0, width=30, align="l")
            active_marshall_table.reformat_column(1, width=15, align="c")
            pass_marshall_table.reformat_column(0, width=30, align="l")
            pass_marshall_table.reformat_column(1, width=15, align="c")
            generalist_table.reformat_column(0, width=30, align="l")
            generalist_table.reformat_column(1, width=15, align="c")
            profession_table.reformat_column(0, width=30, align="l")
            profession_table.reformat_column(1, width=15, align="c")
            self.caller.msg(status_table)
            self.caller.msg(active_marshall_table)
            self.caller.msg(pass_marshall_table)
            self.caller.msg(generalist_table)
            self.caller.msg(profession_table)
        else:
            self.caller.msg("|540Usage: charsheet|n\n|400You can only see your own character sheet.|n")

class CharStatus(Command):
    """
    Prints out the character's relevant status information.
    """

    key = "charstatus"
    aliases = ["status", "char status", "character status", "view status"]
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):
        # target = self.caller.search(self.target)

        if self.target == "self" or self.target == "me" or not self.target:
            status_table = evtable.EvTable("|540Status|n", "|540Value|n",
                table = [
                    [
                        "Shield",
                        "Armor",
                        "Armor Specialist",
                        "Tough",
                        "Body",
                        "Weapon Value",
                        "Melee Weapon Equipped",
                        "Two-handed Equipped",
                        "Bow Equipped",
                        "Armor Value"
                    ],
                    [
                        self.caller.db.shield,
                        self.caller.db.armor,
                        self.caller.db.armor_specialist,
                        self.caller.db.tough,
                        self.caller.db.body,
                        self.caller.db.weapon_level,
                        self.caller.db.melee,
                        self.caller.db.twohanded,
                        self.caller.db.bow,
                        self.caller.db.av
                    ]
                ],
                border = "cells")

            status_table.reformat_column(0, width=30, align="l")
            status_table.reformat_column(1, width=15, align="c")
            self.caller.msg(status_table)
        else:
            self.caller.msg("|540Usage: charstatus|n\n|400You can only see your own character status.|n")

class CmdDiagnose(Command):
    """
    Prints out the character's relevant status information.
    """

    key = "diagnose"
    aliases = ["dia", "check"]
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):

        caller = self.caller

        if self.target == caller or self.target == "me" or self.target == '':
            message = ""
            body = caller.db.body
            bleed_points = caller.db.bleed_points
            death_points = caller.db.death_points

            if body >= 3:
                message += "|230You are in tiptop shape!|n"
            elif 0 < body < 3:
                message += "|540You're a little roughed up and bruised, but not bleeding. It might be worth looking for someone versed in medicine before you go looking for a fight.|n"
            elif body <= 0 and bleed_points:
                message += "|400You're bleeding to death. You cannot move from your immediate area or use active marshal skills.|n"
            elif death_points:
                message += "|400You're dying. You can't do anything except lay there and hope someone comes to help.|n"
            else:
                message += "|400You are dead.|n"

            caller.msg(message)

        else:
            target = caller.search(self.target)
            if not target:
                caller.msg("|540Usage: diagnose <target>|n\n|400Your target wasn't found. Please try again.|n")

            elif not caller.db.medicine:
                caller.msg("|540Sorry, but you don't have the Medicine skill so you can't diagnose other characters.|n")

            else:
                message = ""
                target_body = target.db.body
                target_bleed_points = target.db.bleed_points
                target_death_points = target.db.death_points

                if body >= 3:
                    message += "|230" + target.key + " is in tiptop shape and doesn't need any healing.|n"
                elif 0 < target_body < 3:
                    message += "|540" + target.key + " is a little roughed up and bruised, but not bleeding. They could use some tending before heading into a fight.|n"
                elif body <= 0 and target_bleed_points:
                    message += "|400" + target.key + " is bleeding to death. They cannot move from their immediate position or use active marshal skills.|n"
                elif target_death_points:
                    message += "|400" + target.key + " is dying. They need to be stabilized as soon as possible.|n"
                else:
                    message += "|400" + target.key + " is dead."

                caller.msg(message)

"""
Random Encounter Commands
"""

class CmdTouchAltar(Command):

        key = "touch"
        help_category = "mush"

        ALTAR_STRINGS = [
        "|/|230Touching the stone altar, you see a hand on your shoulder, its wrinkled fingers tipped in rotting fingernails, cracked and bleeding. One by one it removes its stinking fingers from your shoulder and slides slowly forward. Forward, forward until it penetrates the stone. As it does, another similarly grotesque hand reaches out for you from the stone. Frozen, you try to pull your hand away but are unable. Just before the hand wraps around your throat, you faint, coming to, doing whatever it was you were doing, remembering only a terrible feeling and nothing of your actions related to the vision. Whether it was real or not is impossible to tell. Who would believe you anyway?|n|/",
        "|/|230You touch the stone and begin to feel happy. Looking up, you see someone who looks startlingly like you staring back at you. They begin to smile widely at you...wider, wider until it seems that its cheeks will come right off of its hideously grinning face. And in fact, that is what happens. Flesh tears from your cheeks, taking with it the rest of the skin from your face, until you are nothing more than a terrible grinning skull. You snap out of your trance and recall a terrible memory that you can’t quite put your finger on. Whether it was real or not is impossible to tell, though you feel your face and nothing seems to be out of place, or bleeding for that matter. Who would believe you anyway?|n|/",
        f"|/|230As you touch the stone, you feel control leave from your body. Your arms and legs feel like dead weights attached to your body. All sounds now seemed far away. Were you talking to someone just now? Where were you? Who were you? You hear a voice begin to softly whisper your name from just over your left shoulder. Did you imagine it? Now your right. This is certainly no dream. For a second it feels like many hands are all pulling you slowly backwards. Then it stops. Your name again. Again. Again. And then in a rush you snap out of your trance to the sound of someone calling your name. Whether it was real or not is impossible to tell. Who would believe you anyway?|n|/",
        "|/|230You look into the mirror. You begin to feel euphorically dizzy, as though you’ve had too much wine. The world begins to spin around you and things go black. You wake up. Lying in bed you come to in a domicile you recognize as your home. From beyond the door to your room can be heard the uproarious din of a party. Music, voices, the sound of plates and cups scraping the tables. Though as you listen for a while, another sound begins to weave and crawl its way around the others. Whispers. Chattering. What was it? Lifting the sheets you set your feet upon the floor, crossing the small chamber to the bedroom door.  Slowly twisting the knob you pull the handle. Beyond the threshold it is as though you are staring into a mirror, your own perplexed expression looking back at you. But then it smiles. And it is then you realize that the face in the mirror is not yours at all. It opens its mouth as though to scream though no sounds comes out. You wake up. What was that? What are these strange memories of silent screams? Would that anyone were to believe your story, what could be done about it?|n|/",
        "|/|230Touching the altar, your head is suddenly filled with the sound of many people screaming all at once. Men, women, children. Looking deep into the woods, you can see that there are myriad humanoid shapes disappearing in and out of the trees. These are the spirits of this place. This is their graveyard. You wake up. What was that? Were these pitiful creatures really there? Who would believe you if you said something anyway?|n|/"
        ]


        def parse(self):
            "Very trivial parser"
            self.target = self.args.strip()

        def func(self):
            "This performs the actual command"
            errmsg = "|540Usage: touch altar|n"

            if not self.args:
                self.caller.msg(errmsg)
                return

            target = self.caller.search(self.target)

            if not target:
                self.caller.msg(errmsg)
                return

            if target == self.caller:
                self.caller.msg(f"|400{self.caller}, you can't do that!|n")
                return

            message = random.choice(self.ALTAR_STRINGS)
            self.caller.location.msg_contents(f"|/|230{self.caller} approaches the altar, putting their hand on top of the smooth stone...|n|/")
            self.caller.msg(message)
