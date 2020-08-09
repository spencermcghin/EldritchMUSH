# Imports
import random

# Local imports
from evennia import Command
from evennia import CmdSet
from evennia import default_cmds
from commands import command
from world import prototypes
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
        if not self.item:
            self.msg(use_err_msg)
            return

        if not self.caller.db.blacksmith:
            self.msg("|400You are not trained in how to properly utilze a forge. Please find a blacksmith.|n")
            return


        # Spawn item and move to callers inventory
        blacksmith_item = spawn({f"key": "{self.item}",
                                  "location": self.caller.location})


        # Check for items in callers inventory.
        item_requirements = [
        self.caller.db.iron_ingots >= blacksmith_item.db.iron_ingots,
        self.caller.db.cloth >= blacksmith_item.db.cloth,
        self.caller.db.refined_wood >= blacksmith_item.db.refined_wood,
        self.caller.db.leather >= blacksmith_item.db.leather
        ]

        # Check that all conditions in above list are true.
        if all(item_requirements):
            self.msg(f"You forge a {self.item}")
            # Get required resources and decrement from player totals.
            self.caller.db.iron_ingots -= blacksmith_item.db.iron_ingots
            self.caller.db.cloth -= blacksmith_item.db.cloth
            self.caller.db.refined_wood -= blacksmith_item.db.refined_wood
            self.caller.db.leather -= blacksmith_item.db.leather

            # Give to blacksmith
            blacksmith_item.move_to(self.caller, quiet=True)

        else:
            self.msg(f"You don't have the required resources for a {self.item}")
            self.delete(blacksmith_item)
