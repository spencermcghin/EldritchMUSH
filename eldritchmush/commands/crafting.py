# Imports
import random

# Local imports
from evennia import Command, CmdSet, default_cmds, spawn, utils
from evennia.prototypes import prototypes
from commands import command
from evennia.utils import evmenu

"""
Crafting Commands
"""

class CmdCraft(Command):

    key = "craft"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.item = self.args.strip()

    def func(self):

        if self.caller.db.blacksmith:
            pass
        elif self.caller.db.bowyer:
            pass
        elif self.caller.db.artificer:
            pass
        elif self.caller.db.gunsmith:
            pass
        else:
            self.msg(f"|400You don't have the proper skills to create a {self.item}.|n")
            return

        use_err_msg = "|430Usage: craft <item>|n"

        if not self.item:
            self.msg(use_err_msg)
            return

        # Search for designated prototypes
        try:
            prototype = prototypes.search_prototype(self.item, require_single=True)
        except KeyError:
            self.msg("|430Item not found, or more than one match. Please try again.|n")
        else:
            # Get search response
            prototype_data = prototype[0]

            # Get item attributes and who makes it.
            item_data = prototype_data['attrs']
            craft_source = item_data[0][1]

            # Check for correct kit in caller kit slot.
            kit = self.caller.db.kit_slot[0] if self.caller.db.kit_slot else None
            kit_type = kit.db.type if kit else None
            kit_uses = kit.db.uses if kit else None

            if not kit:
                self.msg(f"|430Please equip the kit needed to craft a {self.item}.")
                return

            if kit_uses <= 0 and (craft_source == kit_type):
                self.msg(f"|400Your {kit} is out of uses.|n")
                return

            # Passed checks. Make item.
            # Check for items in callers inventory.
            if craft_source == kit_type:
                character_resources = {
                "iron_ingots": self.caller.db.iron_ingots,
                "cloth": self.caller.db.cloth,
                "refined_wood": self.caller.db.refined_wood,
                "leather": self.caller.db.leather
                }

                # Get item requirements
                item_requirements = {
                "iron_ingots": item_data[2][1],
                "refined_wood": item_data[3][1],
                "leather": item_data[4][1],
                "cloth": item_data[5][1]
                }

                requirements_checker = [
                character_resources["iron_ingots"] >= item_requirements["iron_ingots"],
                character_resources["refined_wood"] >= item_requirements["refined_wood"],
                character_resources["leather"] >= item_requirements["leather"],
                character_resources["cloth"] >= item_requirements["cloth"]
                ]

                # Check that all conditions in above list are true.

                if all(requirements_checker) or self.caller.is_superuser:
                    self.msg(f"You craft a {self.item}")
                    # Get required resources and decrement from player totals.
                    self.caller.db.iron_ingots -= item_requirements["iron_ingots"]
                    self.caller.db.refined_wood -= item_requirements["refined_wood"]
                    self.caller.db.leather -= item_requirements["leather"]
                    self.caller.db.cloth -= item_requirements["cloth"]
                           #
                    item = spawn(prototype[0])
                    item[0].move_to(self.caller, quiet=True)

                    # Decrement the kit of one use.
                    kit.db.uses -= 1

                else:
                    self.msg(f"|400You don't have the required resources.|n")
            else:
                self.msg(f"|430Please equip the correct kit before attempting to craft your item.|n")
                return


class CmdRepair(Command):

    key = "repair"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.item = self.args.strip()

    def func(self):

        if self.caller.db.blacksmith:
            pass
        elif self.caller.db.bowyer:
            pass
        elif self.caller.db.artificer:
            pass
        elif self.caller.db.gunsmith:
            pass
        else:
            self.msg(f"|400You don't have the proper skills to repair a {self.item}.|n")
            return

        use_err_msg = "|430Usage: repair <item>|n"

        if not self.item:
            self.msg(use_err_msg)
            return

        # Search for designated prototypes
        try:
            item = self.caller.search(self.item, location=self.caller)
            item_lower = self.item.lower().replace(" ", "_")
            prototype = prototypes.search_prototype(item_lower, require_single=True)
        except KeyError:
            self.msg("|430Item not found, or more than one match. Please try again.|n")
        else:
            # Get search response
            prototype_data = prototype[0]

            # Get item attributes and who makes it.
            item_data = prototype_data['attrs']
            craft_source = item_data[0][1]
            material_value = item_data[9][1]

            if craft_source in ["blacksmith", "bowyer", "gunsmith"]:
                # item.db.broken = False
                # item.db.patched = False
                # item.db.material_value = material_value
                self.msg(item_data)
                self.msg(f"Craft source is {craft_source}")
            else:
                self.msg("Is artificer.")
