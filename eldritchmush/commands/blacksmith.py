# Imports
import random

# Local imports
from evennia import Command, CmdSet, default_cmds
from evennia.prototypes import prototypes
from commands import command
from evennia.utils import evmenu



"""
Crafting Commands
"""

class CmdForge(Command):

    key = "forge"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.item = self.args.strip()

    def func(self):
        use_err_msg = "|540Usage: forge <item>|n"

        # Do all checks
        if not self.caller.db.blacksmith:
            self.msg("|400You are not trained in how to properly utilze a forge. Please find a blacksmith.|n")
            return

        if not self.item:
            self.msg(use_err_msg)
            return

        # Search for designated prototypes
        found_prototype = True if prototypes.search_prototype(self.item, require_single=True) else False

        # Spawn item and move to callers inventory
        # try:
        if found_prototype:
            # blacksmith_item = spawn({"key": f"{found_prototype}"}, location=self.caller)

            self.msg(f"{self.item}")
        else:
            self.msg("Item not found. Please try again.")


        #     self.msg(f"{blacksmith_item}")
        # except Exception:
        #     self.msg("Please enter a valid item name.")
        #
        # else:
        #     self.msg("Foo")

        # if blacksmith_item:
        #     # Check for items in callers inventory.
        #     character_resources = {
        #     "iron_ingots": self.caller.db.iron_ingots,
        #     "cloth": self.caller.db.cloth,
        #     "refined_wood": self.caller.db.refined_wood,
        #     "leather": self.caller.db.leather
        #     }
        #
        #     # Get item requirements
        #     item_requirements = {
        #     "iron_ingots": blacksmith_item.db.iron_ingots,
        #     "cloth": blacksmith_item.db.cloth,
        #     "refined_wood": blacksmith_item.db.refined_wood,
        #     "leather": blacksmith_item.db.leather
        #     }
        #
        #     requirements_checker = [
        #     character_resources["iron_ingots"] >= item_requirements["iron_ingots"],
        #     character_resources["cloth"] >= item_requirements["cloth"],
        #     character_resources["refined_wood"] >= item_requirements["refined_wood"],
        #     character_resources["leather"] >= item_requirements["leather"]
        #     ]
        #
        #     # Check that all conditions in above list are true.
        #     if all(requirements_checker):
        #         self.msg(f"You forge a {self.item}")
        #         # Get required resources and decrement from player totals.
        #         self.caller.db.iron_ingots -= item_requirements["iron_ingots"]
        #         self.caller.db.cloth -= item_requirements["cloth"]
        #         self.caller.db.refined_wood -= item_requirements["refined_wood"]
        #         self.caller.db.leather -= item_requirements["leather"]
        #
        #         # Give to blacksmith
        #         blacksmith_item.move_to(self.caller, quiet=True)
        #
        #     else:
        #         self.msg(f"You don't have the required resources for a {self.item}")
        #         self.delete(blacksmith_item)
