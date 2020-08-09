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
        self.item = self.args.strip()

    def func(self):
        """
        Logic
        Caller executes command - forge iron medium weapon - done
        Error handle - if no item specified - done
        Error handle - character doesn't have skill - done
        Error handle against existing prototypes. Check prototype_parent - done
        Prompt user they can't make the item if not of their corresponding type. - done
        Check to see if the resources and schematic are in the inventory of the caller (holds())
        If so, remove resources from caller's inventory, spawn item and place in caller's inventory
        Put resources in forge object and then delete them.
        If not, prompt caller that they need additional resources.
        """
        use_err_msg = "|540Usage: forge <item>|n"

        # Do all checks
        if not self.item:
            self.msg(use_err_msg)
            return

        if not self.caller.db.blacksmith:
            self.msg("|400You are not trained in how to properly utilze a forge. Please find a blacksmith.|n")
            return

        if not self.item.db.prototype_parent = "BLACKSMITH" or "WEAPON":
            self.msg("|400You cannot create the requested item.|n")
            return

        # Check for items in callers inventory.
        item_requirements =

        if self.caller.holds(

        )
