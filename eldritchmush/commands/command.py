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
from commands import combat
from commands.fortunestrings import FORTUNE_STRINGS
from evennia import default_cmds, utils, search_object, spawn
from evennia.prototypes import prototypes
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils import evtable
from typeclasses import objects

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
"""
Utility commands
"""
class CmdGet(Command):
    """
    pick up something

    Usage:
      get (optional:<qty>) <obj> <from||=> <target>

    Picks up an object from your location and puts it in
    your inventory.
    """

    key = "get"
    aliases = "grab"
    locks = "cmd:all()"
    arg_regex = r"\s|$"

    def parse(self):

        args = self.args.strip()

        # Check for qty at first element in args list
        try:
            self.args_list = args.split(" ")
            isInt = int(self.args_list[0])
        except ValueError:
            item = self.args
            qty = None
        else:
            qty = int(self.args_list[0])
            item = self.args_list[1]

        self.target = self.args_list[-1]
        self.item = item
        self.qty = qty

    def func(self):
        """implements the command."""

        """
        Check to see if given item is a resource before defaulting to caller inventory.
        """

        if not self.args or not self.target:
            self.caller.msg("|430Usage: get <qty> <object> from <target> or get <object>|n\nNote - Quantity of an item is optional and only works on reosources or currency - ex: get 5 gold from chest.")
            return

        target = self.caller.search(self.target, location=self.caller.location)

        if target == self.caller:
            self.caller.msg(f"You keep {self.item} to yourself.")
            return

        resource_dict = {"iron_ingots": ["iron", "ingots", "iron ingots"],
                          "refined_wood": ["refined", "wood", "refined wood"],
                          "leather": ["leather"],
                          "cloth": ["cloth"],
                          "gold": ["gold", "gold dragons"],
                          "silver": ["silver", "silver dragons"],
                          "copper": ["copper", "copper dragons"],
                          "arrows": ["arrows"]}


        # Begin logic to check if item given is a resource or currency
        resource_array = [v for k, v in resource_dict.items()]
        flat_resource_array = [alias for alias_list in resource_array for alias in alias_list]

        # If the item is in the list of aliases, find its corresponding key.
        if self.item.lower() in flat_resource_array and self.qty is not None:
            item_db_key = [k for k, v in resource_dict.items() if self.item.lower() in v[:]]

            # Check to see if item qty exists as attribute value on caller.
            # Get qty by calling get method. Only thing calling this can be players, so will always have attribute.
            caller_item_qty = self.caller.attributes.get(item_db_key[0], return_obj=True)

            if caller_item_qty.value >= 0:
                attribute = self.caller.attributes.get(item_db_key[0], return_obj=True)
                # Update target's corresponding attribute by self.qty.
                # Check to make sure target has attribute.
                try:
                    target_attribute = target.attributes.get(item_db_key[0], return_obj=True, raise_exception=True)
                # If not, throw an error.
                except AttributeError:
                    self.msg("|430You need to specify an appropriate target.|n")
                else:
                    if not target.access(self.caller, "get") or target.has_account:
                        if target.db.get_err_msg:
                            self.msg(target.db.get_err_msg)
                        else:
                            self.msg("|400You can't get that.|n")
                        return

                    elif (target_attribute.value - self.qty) < 0:
                        self.msg("|400You can't get that amount.|n")
                    else:
                        self.msg(f"You get {self.qty} {self.item} from the {target}")
                        target_attribute.value -= self.qty
                        caller_item_qty.value += self.qty
        else:

            if target:
                if not target.access(self.caller, "get"):
                    if target.db.get_err_msg:
                        self.msg(target.db.get_err_msg)
                    else:
                        self.msg("|400You can't get that.|n")
                    return

                # calling at_before_get hook method
                if not target.at_before_get(self.caller):
                    return

                target.move_to(self.caller, quiet=True)
                self.caller.msg("You pick up %s." % target.name)
                self.caller.location.msg_contents("%s picks up %s." % (self.caller.name, target.name), exclude=self.caller)
                # calling at_get hook method
                target.at_get(self.caller)
            else:
                return

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
            self.caller.msg("|430Usage: give <qty> <inventory object> to <target>|n\nNote - Quantity of an item is optional and only works on reosources or currency - ex: give 5 gold to Tom.")
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
                    self.msg("|430You need to specify an appropriate target.|n")
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
                nofound_string=f"|430You aren't carrying a {self.item}. If you want to give resources or currency please specify a quantity before the item. Ex: give 1 gold to Tom.|n" ,
                multimatch_string=f"|430You carry more than one {self.item}|n:" ,
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
        h = combat.Helper(self.caller)

        if not self.item:
            self.caller.msg("|430Usage: equip <item>|n")
            return

        item = self.caller.search(self.item, location=self.caller)

        # Check if the item is of armor type
        item_lower = item.key.lower().replace(" ", "_") if item else return

        try:
            prototype = prototypes.search_prototype(item_lower, require_single=True)
        except KeyError:
            self.msg(f"You are not carrying a {item}.")
        else:
        # Get search response
            prototype_data = prototype[0]

            # Get item attributes and who makes it.
            item_data = prototype_data['attrs']

            indexOfRequired = next((i for i, v in enumerate(item_data) if v[0] == "required_skill"), None)

            # Do some skill checks
            if indexOfRequired:
                required_skill = item_data[indexOfRequired][1]

                if required_skill == "gunner" and not self.caller.db.gunner:
                    self.msg(f"You lack the skill in Firearms to use {item.key}.")
                    return
                elif required_skill == "archer" and not self.caller.db.archer:
                    self.msg(f"You lack the skill in Archery to use {item.key}.")
                    return
                elif required_skill == "shields" and not self.caller.db.shields:
                    self.msg(f"You lack the skill in Shields to use {item.key}.")
                    return
                elif required_skill == "melee_weapons" and not self.caller.db.melee_weapons:
                    self.msg(f"You lack the skill in Melee Weapons to use {item.key}.")
                    return
                elif required_skill == "armor_proficiency" and not self.caller.db.armor_proficiency:
                    self.msg(f"You lack the skill in Armor to use {item.key}.")
                    return

            # Equip gloves and add resists
            if item.db.hand_slot and not self.caller.db.hand_slot:
                self.caller.db.hand_slot.append(item)

                # Add extra points from indomitable if armor still has material_value
                if item.db.resist > 0:
                    self.caller.db.resist += item.db.resist

                self.msg(f"You don {item.key}.")
                self.caller.location.msg_contents(f"|025{self.caller.key} equips their {item.key}.|n")

            # Equip boots and add resists
            elif item.db.foot_slot and not self.caller.db.foot_slot:
                self.caller.db.foot_slot.append(item)

                # Add extra points from indomitable if armor still has material_value
                if item.db.resist:
                    self.caller.db.resist += item.db.resist

                self.msg(f"You don {item.key}.")
                self.caller.location.msg_contents(f"|025{self.caller.key} equips their {item.key}.|n")

            # Equip kit. Corresponding skill should reference the number of uses left.
            elif item.db.kit_slot and not self.caller.db.kit_slot:
                self.caller.db.kit_slot.append(item)

                self.msg(f"You equip a {item.key} with {item.db.uses} uses left.")

            # Equip arrows. Corresponding skill should reference the number of uses left.
            elif item.db.arrow_slot and not self.caller.db.arrow_slot:
                self.caller.db.arrow_slot.append(item)

                self.msg(f"You equip a quiver with {item.db.quantity} arrows left.")

            # Equip arrows. Corresponding skill should reference the number of uses left.
            elif item.db.bullet_slot and not self.caller.db.bullet_slot:
                self.caller.db.bullet_slot.append(item)

                self.msg(f"You equip a bundle of {item.db.quantity} bullets.")

            # Equip clothing. Add to character's influential skill.
            elif item.db.clothing_slot and not self.caller.db.clothing_slot:
                self.caller.db.clothing_slot.append(item)

                if item.db.influential:
                    self.caller.db.influential += item.db.influential

                self.msg(f"You put on the {item.key}.")

            # Equip clothing. Add to character's influential skill.
            elif item.db.cloak_slot and not self.caller.db.cloak_slot:
                self.caller.db.cloak_slot.append(item)

                if item.db.espionage:
                    self.caller.db.espionage += item.db.espionage

                self.msg(f"You put on the {item.key}.")

            # Equip armor
            elif item.db.is_armor and not self.caller.db.body_slot:
                self.caller.db.body_slot.append(item)
                self.caller.db.armor = item.db.material_value

                # Add extra points from indomitable if armor still has material_value
                if item.db.material_value > 0 and self.caller.db.indomitable:
                    self.caller.db.armor += self.caller.db.indomitable

                self.msg(f"You don {item.key}.")
                self.caller.location.msg_contents(f"|025{self.caller.key} equips their {item.key} armor.|n")

                # Get vals for armor value calc
                armor_value = self.caller.db.armor
                indomitable = self.caller.db.indomitable
                tough = self.caller.db.tough
                armor_specialist = 1 if self.caller.db.armor_specialist == True else 0

                # Add them up and set the curent armor value in the database
                currentArmorValue = armor_value + tough + armor_specialist + indomitable
                self.caller.db.av = currentArmorValue

                # Return armor value to console.
                self.caller.msg(f"|430Your current Armor Value is {currentArmorValue}:\nArmor: {armor_value}\nTough: {tough}\nArmor Specialist: {armor_specialist}\nIndomitable: {indomitable}|n")

            # For weapons/shields
            elif item and item not in self.right_slot:
                if not item.db.broken:
                    # Check if item is twohanded
                    if item.db.twohanded:
                        if not self.right_slot and not self.left_slot:
                            self.right_slot.append(item)
                            self.left_slot.append(item)

                            # Add weapon bonus
                            weapon_bonus = h.weaponValue(item.db.level)
                            self.caller.db.weapon_level = weapon_bonus

                            # Send some messages
                            self.caller.location.msg_contents(f"|025{self.caller.key} equips their {item.key}.|n")
                            self.caller.msg(f"You have equipped your {item.key}")
                        else:
                            self.caller.msg(f"|430You can't equip the {item} unless you first unequip something.|n")
                            return
                    # Check to see if right hand is empty.
                    elif not self.right_slot and (item.db.is_shield or item.db.damage):
                        self.caller.location.msg_contents(f"|025{self.caller.key} equips their {item.key}.|n")

                        if item.db.is_shield:
                            self.right_slot.append(item)
                        else:
                            # Add weapon bonus
                            self.right_slot.append(item)
                            weapon_bonus = h.weaponValue(item.db.level)
                            self.caller.db.weapon_level = weapon_bonus

                    elif not self.left_slot and (item.db.is_shield or item.db.damage):
                        self.caller.location.msg_contents(f"|025{self.caller.key} equips their {item.key}.|n")

                        if item.db.is_shield:
                            self.left_slot.append(item)
                        else:
                            # Add weapon bonus
                            self.left_slot.append(item)
                            weapon_bonus = h.weaponValue(item.db.level)
                            self.caller.db.weapon_level = weapon_bonus

                    else:
                        self.caller.msg("|430You are already carrying an item in that slot.|n")
                        return
                else:
                    self.caller.msg(f"|400{item} is broken and may not be equipped.|n")
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
            self.caller.msg("|430Usage: unequip <item>|n")
            return

        item = self.caller.search(self.item, location=self.caller)

        if item:
            # Check if item is twohanded and is held.
            if item.db.twohanded and (item in self.right_slot):
                self.right_slot.remove(item)
                self.left_slot.remove(item)
                self.caller.db.weapon_level = 0

            elif self.caller.db.cloak_slot and item in self.caller.db.cloak_slot:
                # Unequip cloak and remove associated espionage points.
                self.caller.db.cloak_slot.remove(item)
                self.caller.db.espionage -= item.db.espionage

            elif self.caller.db.arrow_slot and item in self.caller.db.arrow_slot:
                # Unequip arrows.
                self.caller.db.arrow_slot.remove(item)

            elif self.caller.db.bullet_slot and item in self.caller.db.bullet_slot:
                # Unequip bullets.
                self.caller.db.bullet_slot.remove(item)

            elif self.caller.db.clothing_slot and item in self.caller.db.clothing_slot:
                # Unequip clothing and remove associated influential points.
                self.caller.db.clothing_slot.remove(item)
                self.caller.db.influential -= item.db.influential

            elif self.caller.db.kit_slot and item in self.caller.db.kit_slot:
                # Unequip kit.
                self.caller.db.kit_slot.remove(item)

            elif self.caller.db.hand_slot and item in self.caller.db.hand_slot:
                # Unequip gloves and remove associated resists.
                self.caller.db.hand_slot.remove(item)
                self.caller.db.resist -= item.db.resist

            elif self.caller.db.foot_slot and item in self.caller.db.foot_slot:
                # Unequip boots and remove associated resists.
                self.caller.db.foot_slot.remove(item)
                self.caller.db.resist -= item.db.resist

            # Check to see if right hand is empty.
            elif self.caller.db.body_slot and item in self.caller.db.body_slot:
                self.caller.db.body_slot.remove(item)
                # Item is armor, decrement from av
                self.caller.db.armor = 0
                # Get vals for armor value calc
                armor_value = self.caller.db.armor
                tough = self.caller.db.tough
                armor_specialist = 1 if self.caller.db.armor_specialist == True else 0
                # Add them up and set the curent armor value in the database
                currentArmorValue = armor_value + tough + armor_specialist
                self.caller.db.av = currentArmorValue
                # Return armor value to console.
                self.caller.msg(f"|430Your current Armor Value is {currentArmorValue}:\nArmor: {armor_value}\nTough: {tough}\nArmor Specialist: {armor_specialist}|n")

            elif self.right_slot and item in self.right_slot:
                self.right_slot.remove(item)

                if item.db.damage > 0:
                    self.caller.db.weapon_level = 0

            elif self.left_slot and item in self.left_slot:
                self.left_slot.remove(item)

                if item.db.damage > 0:
                    self.caller.db.weapon_level = 0

            else:
                self.caller.msg(f"|430You aren't carrying a {item}.|n")
                return

            self.caller.msg(f"You have unequipped your {item}.")
        else:
            self.caller.msg(f"Please be more specific.")

"""
Chargen Skill Setters
"""
class SetBlacksmith(Command):
    """Set the blacksmith level of a character

    Usage: setblacksmith <0-3>

    This can only be used during character generation.
    """

    key = "setblacksmith"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|430Usage: setblacksmith <0-3>|n\n|400You must supply a number between 0 and 3.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            blacksmith = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= blacksmith <= 5):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.blacksmith = blacksmith
        self.caller.msg("|430Your Blacksmith level was set to %i.|n" % blacksmith)

class SetArtificer(Command):
    """Set the artificer level of a character

    Usage: setartificer <0-3>

    This can only be used during character generation.
    """

    key = "setartificer"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|430Usage: setartificer <0-3>|n\n|400You must supply a number between 0 and 3.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            artificer = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= artificer <= 5):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.artificer = artificer
        self.caller.msg("|430Your Artificer level was set to %i.|n" % artificer)

class SetBowyer(Command):
    """Set the bowyer level of a character

    Usage: setbowyer <0-3>

    This can only be used during character generation.
    """

    key = "setbowyer"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|430Usage: setbowyer <0-3>|n\n|400You must supply a number between 0 and 3.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            bowyer = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= bowyer <= 5):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.bowyer = bowyer
        self.caller.msg("|430Your Bowyer level was set to %i.|n" % bowyer)

class SetGunsmith(Command):
    """Set the gunsmith level of a character

    Usage: setgunsmith <0-3>

    This can only be used during character generation.
    """

    key = "setgunsmith"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|430Usage: setgunsmith <0-3>|n\n|400You must supply a number between 0 and 3.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            gunsmith = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= gunsmith <= 5):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.gunsmith = gunsmith
        self.caller.msg("|430Your Gunsmith level was set to %i.|n" % gunsmith)

class SetAlchemist(Command):
    """Set the alchemist level of a character

    Usage: setalchemist <0-3>

    This can only be used during character generation.
    """

    key = "setalchemist"
    help_category = "mush"

    def func(self):
        errmsg = "|430Usage: setalchemist <0-3>|n\n|400You must supply a number between 0 and 3.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            alchemist = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= alchemist <= 5):
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.alchemist = alchemist
        self.caller.msg("|430Your Alchemist level was set to %i.|n" % alchemist)

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
        errmsg = "|430Usage: settracking <0-3>|n\n|400You must supply a number between 0 and 3.|n"
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
        self.caller.msg("|430Your Tracking was set to %i.|n" % tracking)

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
        errmsg = "|430Usage: setperception <0-3>|n\n|400You must supply a number between 0 and 3.|n"
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
        self.caller.msg("|430Your Perception was set to %i.|n" % perception)

class SetMasterOfArms(Command):
    """Set the tracking of a character

    Usage: setmasterofarms <0-3>

    This sets the master of arms of the current character. This is available to all characters.
    """

    key = "setmasterofarms"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|430Usage: setmasterofarms <0-3>|n\n|400You must supply a number between 0 and 3.|n"
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
        self.caller.msg("|430Your Master of Arms was set to %i.|n" % master_of_arms)

class SetTough(Command):
    """Set the tough of a character

    Usage: settough <value>

    This sets the tough of the current character. This is available to all characters.
    """

    key = "settough"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|430Usage: settough <value>|n\n|400You must supply a number 0 or greater.|n"
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
            self.caller.db.total_tough = tough
            self.caller.msg("|430Your Tough was set to %i.|n" % tough)

            # Get armor value objects
            armor = self.caller.db.armor
            tough = self.caller.db.tough
            armor_specialist = 1 if self.caller.db.armor_specialist == True else 0
            indomitable = self.caller.db.indomitable

            # Add them up and set the curent armor value in the database
            currentArmorValue = armor + tough + armor_specialist + indomitable
            self.caller.db.av = currentArmorValue

            # Return armor value to console.
            self.caller.msg(f"|430Your current Armor Value is {currentArmorValue}:\nArmor: {armor}\nTough: {tough}\nArmor Specialist: {armor_specialist}|n")

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
        errmsg = "|430Usage: setarmorspecialist <0 or 1>|n\n|400You must supply a value between 0 and 1.|n"
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
            indomitable = self.caller.db.indomitable

            # Add them up and set the curent armor value in the database
            currentArmorValue = armor + tough + armor_specialist + indomitable
            self.caller.db.av = currentArmorValue

            # Return armor value to console.
            self.caller.msg(f"|430Your current Armor Value is {currentArmorValue}:\nArmor: {armor}\nTough: {tough}\nArmor Specialist: {armor_specialist}\nIndomitable: {indomitable}|n")

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
        errmsg = "|430Usage: setwyldinghand <0-3>|n\n|400You must supply a number between 0 and 3.|n"
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
        errmsg = "|430Usage: setresilience <0 - 3>|n"
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
        errmsg = "|430Usage: setresist <0-5>|n\n|400You must supply a number between 0 and 5.|n"
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
            self.caller.db.total_resist = resist
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
        errmsg = "|430Usage: setdisarm <0-5>|n\n|400You must supply a number between 0 and 5.|n"
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
        self.caller.db.total_disarm = disarm
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
        errmsg = "|430Usage: setcleave <0-5>|n\n|400You must supply a number between 0 and 5.|n"
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
            self.caller.db.total_cleave = cleave
            self.caller.msg("Your cleave level was set to %i." % cleave)

class SetGunner(Command):
    """Set the Gunner level of a character

    Usage: setgunner <0 - 1>

    This sets the Gunner level of the current character. This can only be
    used during character generation.
    """

    key = "setgunner"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|430Usage: setgunner <0 - 1>|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            gunner = int(self.args)
            if gunner > 1:
                gunner = 1

            if gunner < 0:
                gunner = 0
        except ValueError:
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.gunner = gunner

        self.caller.msg("Your Gunner level was set to %i." % gunner)

class SetSniper(Command):
    """Set the Sniper level of a character

    Usage: setsniper <0 - 1>

    This sets the Gunner level of the current character. This can only be
    used during character generation.
    """

    key = "setsniper"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|430Usage: setsniper <0 - 1>|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            sniper = int(self.args)
            if sniper > 1:
                sniper = 1

            if sniper < 0:
                sniper = 0
        except ValueError:
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.sniper = sniper

        self.caller.msg("Your Sniper level was set to %i." % sniper)

class SetArcher(Command):
    """Set the Archer level of a character

    Usage: setarcher <0 - 1>

    This sets the Archer level of the current character. This can only be
    used during character generation.
    """

    key = "setarcher"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|430Usage: setarcher <0 - 1>|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            archer = int(self.args)
            if archer > 1:
                archer = 1

            if archer < 0:
                archer = 0
        except ValueError:
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.archer = archer

        self.caller.msg("Your Archer level was set to %i." % archer)

class SetShields(Command):
    """Set the Shields level of a character

    Usage: setshields <0 - 1>

    This sets the Shields level of the current character. This can only be
    used during character generation.
    """

    key = "setshields"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|430Usage: setshields <0 - 1>|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            shields = int(self.args)
            if shields > 1:
                shields = 1

            if shields < 0:
                shields = 0
        except ValueError:
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.shields = shields

        self.caller.msg("Your Shields level was set to %i." % shields)

class SetMeleeWeapons(Command):
    """Set the Melee Weapons level of a character

    Usage: setmeleeweapons <0 - 1>

    This sets the Shields level of the current character. This can only be
    used during character generation.
    """

    key = "setmeleeweapons"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|430Usage: setmeleeweapons <0 - 1>|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            meleeweapons = int(self.args)
            if meleeweapons > 1:
                meleeweapons = 1

            if meleeweapons < 0:
                meleeweapons = 0
        except ValueError:
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.melee_weapons = meleeweapons

        self.caller.msg("Your Melee Weapons level was set to %i." % meleeweapons)

class SetArmorProficiency(Command):
    """Set the Melee Weapons level of a character

    Usage: setmeleeweapons <0 - 1>

    This sets the Shields level of the current character. This can only be
    used during character generation.
    """

    key = "setarmorproficiency"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|430Usage: setarmorproficiency <0 - 1>|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            armorproficiency = int(self.args)
            if armorproficiency > 1:
                armorproficiency = 1

            if armorproficiency < 0:
                armorproficiency = 0
        except ValueError:
            self.caller.msg(errmsg)
            return
        # at this point the argument is tested as valid. Let's set it.
        self.caller.db.armor_proficiency = armorproficiency

        self.caller.msg("Your Armor Proficiency level was set to %i." % armorproficiency)

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
        errmsg = "|430Usage: setstun <0-5>|n\n|400You must supply a number between 0 and 5.|n"
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
            self.caller.db.total_stun = stun
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
        errmsg = "|430Usage: setsunder <0-5>|n\n|400You must supply a number between 0 and 5.|n"
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
            self.caller.db.total_sunder = sunder
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
        errmsg = "|430Usage: setstagger <0-5>|n\n|400You must supply a number between 0 and 5.|n"
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
            self.caller.db.total_stagger = stagger
            self.caller.msg("Your stagger level was set to %i." % stagger)

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
            self.caller.msg("|430Usage: @perception level key = description|n")

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
                self.caller.msg(f"|430Perception set on {self.obj.name}\nLevel: {level}\nDescription: {self.rhs}|n")
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
        errmsg = "|430Usage: @tracking level key = description|n"

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
                self.caller.msg(f"|430Tracking set on {self.obj.name}\nLevel: {level}\nDescription: {self.rhs}|n")
            else:
                self.caller.msg("|400Search didn't return anything.|n")


class CmdOpen(Command):
    """Open a container object

    Usage: open <object>

    Searches for object. If not an object of type container, caller can't open.
    If is container, then caller can open.
    """

    key = "open"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.item = self.args.strip()

    def func(self):

        if not self.item:
            self.caller.msg("|430Usage: open <item>|n")
            return

        item = self.caller.search(self.item)

        if not utils.inherits_from(item, objects.Container):
            self.msg(f"You cannot open the {item}.")
            return
        else:
            # Get values for db entries.
            gold = item.db.gold
            silver = item.db.silver
            copper = item.db.copper
            iron_ingots = item.db.iron_ingots
            refined_wood = item.db.refined_wood
            leather = item.db.leather
            cloth = item.db.cloth

            self.msg(f"This {item} contains the following:\n")

            if gold:
                self.msg(f"|540Gold|n: {gold}\n")

            if silver:
                self.msg(f"|=tSilver|n: {silver}\n")

            if copper:
                self.msg(f"|310Copper|n: {copper}\n")

            if iron_ingots:
                self.msg(f"|=kIron|n: {iron_ingots}\n")

            if refined_wood:
                self.msg(f"|210Wood|n: {refined_wood}\n")

            if leather:
                self.msg(f"|320Leather|n: {leather}\n")

            if cloth:
                self.msg(f"|020Cloth|n: {cloth}")



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

        err_msg = "|430Usage: pull crank|n"
        fortuneStrings = ["|430Unknow all that you think you know.|n",
                          "|430You have what many want, though you still want more.|n",
                          "|430Who is the little brother.|n",
                          "|430I am not who they say I am.|n",
                          "|430Can you help me?|n",
                          "|430Be careful in the hall of mirrors. The cats are friends. Do not let the child catch them, for he is cruel.|n",
                          "|430Nothing here is as it seems.|n",
                          "|430Did you see them set up? Did you see any of it?|n",
                          "|430Who are the Bordello Brothers|n",
                          "|430Where is this place?|n",
                          "|430Please...|n"
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

        err_msg = "|430Usage: throw dagger|n"

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
        self.caller.msg(f"|/|430Giving up so soon, {self.caller.name}? You were doing so well. Be sure to try again soon.|n|/|230You notice a door open up where before there was none. Stepping through it, you find yourself back in the foyer of the strange maze.|n|/")
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
        get_ticket_emote = "|430A ticket pops up from a small slit in the top of the box.|n\n|430Use the |nget ticket|430 command to pick it up|n\n|430Use the |nlook ticket|430 command to examine it.|n"

        # If the player has already pressed the button on this particular box, nothing happens.
        if self.caller in self.obj.db.characters:
            self.caller.msg(f"|430\"I'm sorry {self.caller},\" a mysterious voice whispers. \"You've already played my little game... I would very much like it if your friends played. You could try your luck in another tent...\" The voice seemed to come from the wooden box, but how is difficult to tell.|n")

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
        get_ticket_emote = "|430A ticket pops up from a small slit in the top of the box.|n\n|430Use the |nget ticket|430 command to pick it up|n\n|430Use the |nlook ticket|430 command to examine it.|n"

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

        err_msg = "|430Usage: swing hammer|n"

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
Set Skill Related Attributes
"""
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
        errmsg = "|430Usage: setstabilize <0-3>|n\n|400You must supply a number between 0 and 3.|n"
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
        errmsg = "|430Usage: setmedicine <0-3>|n\n|400You must supply a number between 0 and 3.|n"
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
        errmsg = "|430Usage: setmedic <0/1>|n\n|400You must supply a number of either 0 or 1.|n"
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
        errmsg = "|430Usage: setchirurgeon <0/1>|n\n|400You must supply a number of either 0 or 1.|n"
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
        errmsg = "|430Usage: setbattlefieldcommander <0-3>|n\n|400You must supply a number between 0 and 3.|n"
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
        errmsg = "|430Usage: setrally <0-3>|n\n|400You must supply a number between 0 and 3.|n"
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

class SetIndomitable(Command):
    """Set the indomitable level of a knight character

    Usage: setindomitable <0,1,2,3>

    This sets the indomitable level of the current character. This can only be
    used during character generation.
    """

    key = "setindomitable"
    help_category = "mush"

    def func(self):
        "This performs the actual command"
        errmsg = "|430Usage: setindombitable <0-3>|n\n|400You must supply a number between 0 and 3.|n"
        if not self.args:
            self.caller.msg(errmsg)
            return
        try:
            indomitable = int(self.args)
        except ValueError:
            self.caller.msg(errmsg)
            return
        if not (0 <= indomitable <= 3):
            self.caller.msg(errmsg)
        else:
            # at this point the argument is tested as valid. Let's set it.
            self.caller.db.indomitable = indomitable
            self.caller.msg(f"Your indomitable level was set to {indomitable}")

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
        errmsg = "|430Usage: setweakness <0/1>|n\n|400You must supply a number of either 0 or 1.|n"
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
                self.caller.msg("|400You have become weakened, finding it difficult to run or use your active martial skills.|n\n|430As long as you are weakened you may not run or use active martial skills.|n")
            else:
                self.caller.db.activemartialskill = 1
                self.caller.msg("|030Your weakened state has subsided.|n\n|430You may now run and use your active martial skills.|n")

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

        right_slot = self.caller.db.right_slot[0] if self.caller.db.right_slot else "Empty"
        left_slot = self.caller.db.left_slot[0] if self.caller.db.left_slot else "Empty"
        body_slot = self.caller.db.body_slot[0] if self.caller.db.body_slot else "Empty"

        if self.target == "self" or self.target == "me" or not self.target:
            status_table = evtable.EvTable("|430Status|n", "|430Value|n",
                table = [
                    [
                        "Body",
                        "Weapon Bonus",
                        "Right Slot",
                        "Left Slot",
                        "Armor",
                        "Armor Value"
                    ],
                    [
                        self.caller.db.body,
                        self.caller.db.weapon_level,
                        right_slot,
                        left_slot,
                        body_slot,
                        self.caller.db.av
                    ]
                ],
                border = "cells")
            active_marshall_table = evtable.EvTable("|430Active Marshall Skills|n", "|430Available|n",
                table = [
                    [
                        "Disarm",
                        "Stun",
                        "Stagger",
                        "Sunder",
                        "Cleave"
                    ],
                    [

                        self.caller.db.disarm,
                        self.caller.db.stun,
                        self.caller.db.stagger,
                        self.caller.db.sunder,
                        self.caller.db.cleave
                    ]
                ],
                border = "cells")
            pass_marshall_table = evtable.EvTable("|430Passive Marshall Skills|n", "|430Level|n",
                table = [
                    [
                        "Resist",
                        "Tough",
                        "Armor",
                        "Master of Arms",
                        "Armor Specialist",
                        "Sniper"
                    ],
                    [
                        self.caller.db.resist,
                        self.caller.db.tough,
                        self.caller.db.armor,
                        self.caller.db.master_of_arms,
                        self.caller.db.armor_specialist,
                        self.caller.db.sniper
                    ]
                ],
                border = "cells")

            generalist_table = evtable.EvTable("|430Generalist Skills|n", "|430Level|n",
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

            proficiency_table = evtable.EvTable("|430Proficiencies|n", "|430Level|n",
                                               table=[
                                                   [
                                                       "Gunner",
                                                        "Archer",
                                                        "Shield",
                                                        "Melee Weapons",
                                                        "Armor Proficiency"
                                                   ],
                                                   [
                                                       self.caller.db.gunner,
                                                       self.caller.db.archer,
                                                       self.caller.db.shields,
                                                       self.caller.db.melee_weapons,
                                                       self.caller.db.armor_proficiency
                                                   ]
                                               ],
                                               border="cells")

            profession_table = evtable.EvTable("|430Profession Skills|n", "|430Level|n",
                table = [
                    [
                        "Stabilize",
                        "Battlefield Medicine",
                        "Chirurgeon",
                        "Rally",
                        "Battlefield Commander",
                        "Wylding Hand"
                    ],
                    [
                        self.caller.db.stabilize,
                        self.caller.db.battlefieldmedicine,
                        self.caller.db.chirurgeon,
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
            proficiency_table.reformat_column(0, width=30, align="l")
            proficiency_table.reformat_column(1, width=15, align="c")
            profession_table.reformat_column(0, width=30, align="l")
            profession_table.reformat_column(1, width=15, align="c")

            self.caller.msg(status_table)
            self.caller.msg(active_marshall_table)
            self.caller.msg(pass_marshall_table)
            self.caller.msg(generalist_table)
            self.caller.msg(proficiency_table)
            self.caller.msg(profession_table)
        else:
            self.caller.msg("|430Usage: charsheet|n\n|400You can only see your own character sheet.|n")

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

        # Make item objects for printing
        # Right and left hand objects
        right_item = self.caller.db.right_slot[0] if self.caller.db.right_slot else ''
        right_item_mv = right_item.db.material_value if right_item else "Empty"
        left_item = self.caller.db.left_slot[0] if self.caller.db.left_slot else ''
        left_item_mv = left_item.db.material_value if left_item else "Empty"

        # Combat turns
        # Callers turn
        location_combat_loop = self.caller.location.db.combat_loop
        in_loop = True if self.caller in location_combat_loop else False
        combat_turn = (location_combat_loop.index(self.caller) + 1) if in_loop else "Not in combat"
        # Turn order
        current_turn = [combatant for combatant in location_combat_loop if combatant.db.combat_turn and in_loop]
        current_turn_value = current_turn[0] if current_turn else "No active combat"


        if self.target == "self" or self.target == "me" or not self.target:
            status_table = evtable.EvTable("|430Status|n", "|430Value|n",
                table = [
                    [
                        "Armor",
                        "Armor Value",
                        "Armor Specialist",
                        "Tough",
                        "Body",
                        "Cleave",
                        "Sunder",
                        "Stagger",
                        "Disarm",
                        "Resist",
                        "Right Item Durability",
                        "Left Item Durability",
                        "Combat Order",
                        "Current Turn"
                    ],
                    [
                        self.caller.db.armor,
                        self.caller.db.av,
                        self.caller.db.armor_specialist,
                        self.caller.db.tough,
                        self.caller.db.body,
                        self.caller.db.cleave,
                        self.caller.db.sunder,
                        self.caller.db.stagger,
                        self.caller.db.disarm,
                        self.caller.db.resist,
                        right_item_mv,
                        left_item_mv,
                        combat_turn,
                        current_turn_value
                    ]
                ],
                border = "cells")

            status_table.reformat_column(0, width=30, align="l")
            status_table.reformat_column(1, width=15, align="c")
            self.caller.msg(status_table)
        else:
            self.caller.msg("|430Usage: charstatus|n\n|400You can only see your own character status.|n")

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
                message += "|430You're a little roughed up and bruised, but not bleeding. It might be worth looking for someone versed in medicine before you go looking for a fight.|n"
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
                caller.msg("|430Usage: diagnose <target>|n\n|400Your target wasn't found. Please try again.|n")

            elif not caller.db.medicine:
                caller.msg("|430Sorry, but you don't have the Medicine skill so you can't diagnose other characters.|n")

            else:
                message = ""
                target_body = target.db.body
                target_bleed_points = target.db.bleed_points
                target_death_points = target.db.death_points

                if target_body >= 3:
                    message += "|230" + target.key + " is in tiptop shape and doesn't need any healing.|n"
                elif 0 < target_body < 3:
                    message += "|430" + target.key + " is a little roughed up and bruised, but not bleeding. They could use some tending before heading into a fight.|n"
                elif target_body <= 0 and target_bleed_points:
                    message += "|400" + target.key + " is bleeding to death. They cannot move from their immediate position or use active marshal skills.|n"
                elif target_death_points:
                    message += "|400" + target.key + " is dying. They need to be stabilized as soon as possible.|n"
                else:
                    message += "|400" + target.key + " is dead."

                caller.msg(message)

"""
General gameplay commands
"""
class CmdPatch(Command):
    """
    Looks in a character's inventory for the object they want to patch.

    Usage: patch <item name>

    Arg handle
    Search for item to be repaired in char inventory.
    If not there, char doesn't have it.
    If there, search in prototypes for max material value.
    If not there, item is not a prototype.
    If in prototypes, check to see if it's under its max material_value.
    If so, set to max value and then delete the patch kit.
    If not, the item doesn't need to be repaired. Prompt and do nothing.
    """

    key = "patch"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.item = self.args.strip()

    def func(self):
        use_err_msg = "|430Usage: patch <item>|n"

        # Do all checks
        if not self.item:
            self.msg(use_err_msg)
            return

        # Format item for searching in prototypes.
        # Adds underscores to make prototype search happy.
        prototyped_string = self.item
        if prototyped_string.find(" "):
            prototyped_string = self.item.replace(' ', '_')

        # Search for item in char inventory
        inv_item = self.caller.search(self.item,
                                      location=self.caller,
                                      nofound_string=f"|400{self.item} not found.|n",
                                      multimatch_string="|430Your search has more than one result. Please be more specific.|n")

        patch_kit = self.caller.search("1-patch kit",
                                       location=self.caller,
                                       nofound_string="You are not carrying any patch kits.",
                                       multimatch_string="|430Your search has more than one result. Please be more specific.|n")

        if inv_item and patch_kit:
            # Search for designated prototypes
            try:
                prototype = prototypes.search_prototype(prototyped_string, require_single=True)
            except KeyError:
                self.msg("This item cannot be patched or you have entered an incorrect spelling.")
            else:
                # Get prototype attributes
                item_attrs = prototype[0]["attrs"]
                # Check if the item has been patched already.
                if inv_item.db.patched:
                    self.msg(f"{inv_item} has been patched already. You will have to take it to a blacksmith to be repaired.")
                    return
                # Material value should always be 9th element in attrs array.
                item_material_value = item_attrs[9][1]
                # Check to see if target item has a lower material value, meaning it's taken damage.
                mv_diff = item_material_value - inv_item.db.material_value
                if mv_diff > 0:
                    # Item has been damaged. Set back to original material_value
                    inv_item.db.material_value = item_material_value
                    inv_item.db.patched = True
                    inv_item.db.broken = False
                    patch_kit.delete()
                    self.msg(f"You crudely repair your {inv_item}. It will need to be taken to a blacksmith should it fail again.")
                else:
                    self.msg(f"Your {inv_item} is not in need of repair.")
        else:
            return

class CmdFollow(Command):
    """
    Follows the targeted character.
    This needs to copy the commands of another character, but only if those commands are
    movement related.x
    """

    key = "follow"
    aliases = ["chase"]
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):
        caller = self.caller

        # If the character attempts to call follow on themselves...
        if self.target == "self" or self.target == "me":
            caller.msg("|430Usage: follow <target>|n\n|400You can't follow yourself. Please select a different target.|n")

        # If they didn't specify a target...
        elif not self.target:
            caller.msg("|430Usage: follow <target>|n\n|400Please specify a target for the follow command.|n")

        elif caller.db.in_combat:
            caller.msg("|430Usage: follow <target>|n\n|400You are currently in combat and cannot follow another character.|n")

        elif caller.db.body <= 0:
            caller.msg("|430Usage: follow <target>|n\n|400You are currently too weak to move beyond your immediate surroundings, and thus cannot follow another character out of here. You must seek medical attention.|n")

        # If their isFollowing attribute is already set to true...
        elif caller.db.isFollowing == True:

            # If their leader attribute is blank, there must have been an issue. Set their isFollowing attribue to False and tell
            # them to start over.
            if (caller.db.leader == []):
                caller.msg("|430Usage: follow <target>|n\n|400It appears you may have already been following someone, but the original target was lost. Try executing the follow command on your new target again.|n")
                caller.db.isFollowing = False
            # Otherwise, let them know they are already following someone.
            else:
                caller.msg("|430Usage: follow <target>|n\n|400You're already following " + caller.db.leader.key + ". Unfollow them first, then follow a new leader.|n")

        # If all is well...
        else:
            """
            Add the name of the Leader to the follower
            Add the name of the follower to the Leader's follower array
            Set the Leader to true if not already
            Set the Follower to true
            """

            target = caller.search(self.target)

            # If the target wasn't found within the room they are in...
            if not target:
                caller.msg("|430Usage: follow <target>|n\n|400Your target wasn't found within your vicinity. You must be in the same area as your target.|n")
            else:
                # First try to find the target within the follower's followers array (is the leader already following you?)
                try:
                    leaderIndex = caller.db.followers.index(target)

                    # If the leader is already following the character, then they cannot follow them; the leader must unfollow them first.
                    caller.msg("|430Usage: follow <target>|n\n|400" + target.key + " is following you, which means that you cannot follow them. Ask them to unfollow you first, then try again.|n")

                # If the leader is not following them, then try adding them to the leader's followers array.
                except ValueError:
                    try:
                        # Attempt to find the caller's key in the target's followers array.
                        followerIndex = target.db.followers.index(caller)

                        # If they were found in the target's follower array, then they were already following them.
                        # Set the caller's leader attribute to the target key, and the isFollowing attribute to True.
                        if followerIndex:
                            caller.msg("|430Usage: follow <target>|n\n|400You are already following " + target.key + ".|n")
                            caller.db.leader = target
                            caller.db.isFollowing = True

                    # If the caller's key was not in the target's followers array, then add them to the array, set the
                    # target's isLeading to true if it was not already, and let the target and caller know that it was
                    # a success.
                    except ValueError:
                        target.db.followers.append(caller)
                        target.db.isLeading = True
                        caller.db.leader = target
                        caller.db.isFollowing = True
                        caller.msg("|430You are now following " + target.key + "|n")
                        target.msg("|430"+ caller.key + " is now following you.|n")

class CmdUnfollow(Command):
    """
    Unfollows the targeted character.
    """

    key = "unfollow"
    aliases = ["stop following", "stopfollowing", "stop chasing", "stopchasing"]
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):

        """
        Remove the follower from the Leader's follower array
        If there are no more followers in the leader's array, set the Leader to false
        Remove the leader's name from the follower
        Set the Follower to false
        """
        # target = self.caller.search(self.target)
        caller = self.caller

        # If the character attempts to call unfollow on themselves...
        if self.target == "self" or self.target == "me":
            caller.msg("|430Usage: unfollow <target>|n\n|400You can't unfollow yourself. Please select a different target.|n")

        # If they didn't specify a target...
        elif not self.target:
            caller.msg("|430Usage: unfollow <target>|n\n|400Please specify a target for the unfollow command.|n")

        # If their isFollowing attribute is already set to false...
        elif caller.db.isFollowing == False:

            target = caller.search(self.target, global_search=True)

            # If their leader attribute is not blank, there must have been an issue. Set their leader attribute to blank and make
            # sure they were removed from the target's followers array.
            if (caller.db.leader != []):

                # If their leader value is equal to the target that they selected
                if (caller.db.leader == target):
                    # Try removing them from the target's followers array.
                    try:
                        target.db.followers.remove(caller)
                        tempList = list(target.db.followers)
                        if (len(tempList) == 0):
                            target.db.isLeading = False
                        caller.msg("|430You are no longer following " + target.key + "|n")
                        target.msg("|430"+ caller.key + " is no longer following you.|n")
                    except ValueError:
                        caller.msg("|430You are no longer following " + target.key + "|n")
                    caller.db.leader = []

                # Else, the user should be told that they were not following the selected target
                else:
                    caller.msg("|430Usage: unfollow <target>|n\n|400It appears that you were following " + caller.db.leader.key + " and not " + target.key + ". Try unfollowing the former. If you think that there is an error, you can try unfollowforce <target> with the original target you specified.|n")

            # Otherwise, let them know they were not following anyone to begin with.
            else:
                caller.msg("|430Usage: unfollow <target>|n\n|400You weren't following anyone. If you think this is an error, you can try unfollowforce <target> to ensure you are removed as a follower from another character.|n")

        # If all is well...
        else:
            """
            Remove the name of the Leader to from the follower
            Remove the name of the follower from the Leader's follower array
            Set the Leader to false if the follower was the last character in their follower array
            Set the Follower to false
            """

            target = caller.search(self.target, global_search=True)

            # If the target wasn't found in the game...
            if not target:
                caller.msg("|430Usage: unfollow <target>|n\n|400Your target wasn't found. Please try again. For this command, you may need to be explicit. For example, if you are trying to unfollow 'Balthazar Bordello', you may need to type out his full name and not just 'Balthazar'.|n")
            elif (caller.db.leader != target):
                caller.msg("|430Usage: unfollow <target>|n\n|400It appears that you were following " + caller.db.leader.key + " and not " + target.key + ". Try unfollowing the former. If you think that there is an error, you can try unfollowforce <target> with the original target you specified.|n")
            else:
                try:
                    # Attempt to remove the follower from the leader's followers array.
                    target.db.followers.remove(caller)
                    tempList = list(target.db.followers)
                    if (len(tempList) == 0):
                        target.db.isLeading = False
                    caller.msg("|430You are no longer following " + target.key + "|n")
                    target.msg("|430"+ caller.key + " is no longer following you.|n")

                # If the caller's key was not in the target's followers array, then add them to the array, set the
                # target's isLeading to true if it was not already, and let the target and caller know that it was
                # a success.
                except ValueError:
                    caller.msg("|430You are no longer following " + target.key + "|n")

                # Reset the caller's leader and isFollowing values.
                caller.db.leader = []
                caller.db.isFollowing = False

class CmdUnfollowForce(Command):
    """
    Unfollows the targeted character, even if that character was not designated as the caller's leader.
    Essentially serves as an error handler if the character is mistakenly part of a leader's followers array.
    """

    key = "unfollowforce"
    aliases = ["unfollow force", "unfollow hard", "unfollowhard", "unfollowreset", "unfollow reset"]
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):

        """
        Remove the follower from the Leader's follower array
        If there are no more followers in the leader's array, set the Leader to false
        Remove the leader's name from the follower
        Set the Follower to false
        """
        # target = self.caller.search(self.target)
        caller = self.caller

        # If the character attempts to call unfollowforce on themselves...
        if self.target == "self" or self.target == "me":
            caller.msg("|430Usage: unfollowforce <target>|n\n|400You can't unfollow yourself. Please select a different target.|n")

        # If they didn't specify a target...
        elif not self.target:
            caller.msg("|430Usage: unfollowforce <target>|n\n|400Please specify a target for the unfollow command.|n")

        # If their isFollowing attribute is already set to false...
        else:

            target = caller.search(self.target, global_search=True)

            # Try removing them from the target's followers array.
            try:
                target.db.followers.remove(caller)
                tempList = list(target.db.followers)
                if (len(tempList) == 0):
                    target.db.isLeading = False
                caller.msg("|430You are no longer following " + target.key + "|n")
                target.msg("|430"+ caller.key + " is no longer following you.|n")
            except ValueError:
                caller.msg("|430You are no longer following " + target.key + "|n")

class CmdFollowStatus(Command):
    """
    Prints out the character's follow related information.
    """

    key = "followstatus"
    aliases = ["followstat", "follow status", "folstat", "follow stat", "fol stat"]
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):
        # target = self.caller.search(self.target)

        if (self.caller.db.leader == []):
            leader = "None"
        else:
            leader = self.caller.db.leader.key

        if self.target == "self" or self.target == "me" or not self.target:
            status_table = evtable.EvTable("|430Status|n", "|430Value|n",
                table = [
                    [
                        "Currently Following",
                        "Your Leader",
                        "Currently Leading",
                    ],
                    [
                        self.caller.db.isFollowing,
                        leader,
                        self.caller.db.isLeading
                    ]
                ],
                border = "cells")

            status_table.reformat_column(0, width=25, align="l")
            status_table.reformat_column(1, width=30, align="c")

            followerList = list(self.caller.db.followers)
            followerRows = []
            if (len(followerList) == 0):
                followerRows.append("None")
            else:
                for char in self.caller.db.followers:
                    followerRows.append(char.key)

            follower_table = evtable.EvTable("|430Followers|n",
                table = [
                    followerRows
                ],
                border = "cells")

            follower_table.reformat_column(0, width=30, align="l")

            self.caller.msg(status_table)
            self.caller.msg(follower_table)
        else:
            self.caller.msg("|430Usage: followstatus|n\n|400You can only see your own follow status.|n")

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
            errmsg = "|430Usage: touch altar|n"

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
