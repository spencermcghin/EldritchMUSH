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
        use_err_msg = "|540Usage: craft <item>|n"

        # Do all checks
        if not self.caller.db.bowyer or not self.caller.db.artificer:
            self.msg("|400You are not trained in how to properly operate these tools. Please find a crafter.|n")
            return

        if not self.item:
            self.msg(use_err_msg)
            return

        # Search for designated prototypes
        try:
            prototype = prototypes.search_prototype(self.item, require_single=True)
        except KeyError:
            self.msg("Item not found, or more than one match. Please try again.")
        else:
            # Get search response
            prototype_data = prototype[0]

            # Check for items in callers inventory.
            character_resources = {
            "iron_ingots": self.caller.db.iron_ingots,
            "cloth": self.caller.db.cloth,
            "refined_wood": self.caller.db.refined_wood,
            "leather": self.caller.db.leather
            }

            # Get item requirements
            item_data = prototype_data['attrs']
            item_requirements = {
            "iron_ingots": item_data[1][1],
            "refined_wood": item_data[2][1],
            "leather": item_data[3][1],
            "cloth": item_data[4][1]
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

                blacksmith_item = spawn(prototype[0])
                blacksmith_item[0].move_to(self.caller, quiet=True)

            else:
                self.msg(f"|400You don't have the required resources.|n")
