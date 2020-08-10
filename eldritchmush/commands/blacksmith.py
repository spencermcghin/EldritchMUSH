# Imports
import random

# Local imports
from evennia import Command, CmdSet, default_cmds, spawn
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
        try:
            prototype = prototypes.search_prototype(self.item, require_single=True)
        except KeyError:
            self.msg("Item not found, or more than one match. Please try again.")
        else:
            # Check for items in callers inventory.
            character_resources = {
            "iron_ingots": self.caller.db.iron_ingots,
            "cloth": self.caller.db.cloth,
            "refined_wood": self.caller.db.refined_wood,
            "leather": self.caller.db.leather
            }

            # Get search response
            prototype_data = prototype[0]

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
            if all(requirements_checker) or self.caller.is_superuser():
                self.msg(f"You forge a {self.item}")
                # Get required resources and decrement from player totals.
                self.caller.db.iron_ingots -= item_requirements["iron_ingots"]
                self.caller.db.refined_wood -= item_requirements["refined_wood"]
                self.caller.db.leather -= item_requirements["leather"]
                self.caller.db.cloth -= item_requirements["cloth"]

                blacksmith_item = spawn(prototype[0])
                blacksmith_item[0].move_to(self.caller, quiet=True)

            else:
                self.msg(f"|400You don't have the required resources.|n")

# {'prototype_parent': 'WEAPON', 'key': 'Iron Medium Weapon', 'aliases': ['iron medium weapon',
# 'longsword', 'medium sword', 'mace', 'axe', 'hammer'], 'prototype_key': 'iron_medium_weapon',
# 'attrs': [('required_resources', 4, None, ''), ('iron_ingots', 2, None, ''), ('refined_wood', 1,
# None, ''), ('leather', 1, None, ''), ('damage', 1, None, ''), ('value_copper', 90, None, ''),
# ('value_silver', 9, None, ''), ('value_gold', 0.9, None, '')], 'prototype_tags': ['module'],
# 'prototype_locks': 'spawn:all();edit:all()', 'prototype_desc': ''}
