# Imports
import random

# Local imports
from evennia import Command
from evennia import CmdSet
from evennia import default_cmds
from commands import command
from world import prototypes


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
        """
        Logic
        Caller executes command - forge iron medium weapon - done
        Error handle - if no item specified - done
        Error handle - character doesn't have skill - done
        Error handle against existing prototypes. Check prototype_parent - done
        Prompt user they can't make the item if not of their corresponding type. - done
        Check to see if the resources and schematic are in the inventory of the caller - done
        If so, remove resources from caller's inventory - done
        Spawn item and place in caller's inventory - done
        If not, prompt caller that they need additional resources. - done
        """
        use_err_msg = "|540Usage: forge <item>|n"

        # Do all checks
        if not self.item:
            self.msg(use_err_msg)
            return

        if not self.caller.db.blacksmith:
            self.msg("|400You are not trained in how to properly utilze a forge. Please find a blacksmith.|n")
            return

        if not self.item.db.prototype_parent == "BLACKSMITH" or "WEAPON":
            self.msg("|400You cannot create the requested item. Please find a blacksmith.|n")
            return

        # Check for items in callers inventory.
        item_requirements = [
        self.caller.db.iron_ingots >= self.item.db.iron_ingots,
        self.caller.db.cloth >= self.item.db.cloth,
        self.caller.db.refined_wood >= self.item.db.refined_wood,
        self.caller.db.leather >= self.item.db.leather
        ]

        # Check that all conditions in above list are true.
        if all(item_requirements):
            self.msg(f"You forge a {self.item}")
            # Get required resources and decrement from player totals.
            self.caller.db.iron_ingots -= self.item.db.iron_ingots
            self.caller.db.cloth -= self.item.db.cloth
            self.caller.db.refined_wood -= self.item.db.refined_wood
            self.caller.db.leather -= self.item.db.leather

            # Spawn item and move to callers inventory
            blacksmith_item = spawn({f"key": "{self.item}",
                                      "location": self.caller.location})

            blacksmith_item.move_to(self.caller, quiet=True)

        else:
            self.msg(f"You don't have the required resources for a {self.item}")
