# Imports
import random
import time
import math

# Local imports
from evennia import Command, CmdSet, default_cmds, spawn, utils
from evennia.prototypes import prototypes
from commands import command
from commands.combatant import Combatant
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
            kit = self.caller.db.kit_slot[0] if self.caller.db.kit_slot else []
            kit_type = kit.db.type if kit else []
            kit_uses = kit.db.uses if kit else 0

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
                    # kit.db.uses -= 1

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
            item = self.caller.search(self.item,
                                      location=self.caller)
        except KeyError:
            self.msg("|430Item not found, or more than one match. Please try again.|n")
        else:
            if item:
                # Check that cooldown has expired.
                combatant = Combatant(self.caller)
                seconds_left = combatant.secondsUntilNextRepair(time.time())
                if seconds_left > 0:
                    combatant.message(f"|430You cannot use this ability for another {math.floor(seconds_left/60)} minutes and {seconds_left % 60} seconds.|n")
                    return

                item_lower = item.key.lower().replace(" ", "_")
                prototype = prototypes.search_prototype(item_lower, require_single=True)

                # Get search response
                prototype_data = prototype[0]

                # Get item attributes and who makes it.
                item_data = prototype_data['attrs']
                craft_source = item_data[0][1]

                # Make sure item has material value attribute.
                if item_data[9][0] == "material_value":
                    material_value = item_data[9][1]
                else:
                    self.msg(f"{item.key} cannot be repaired.")
                    return

                if craft_source in ("blacksmith", "bowyer", "gunsmith"):
                    # Set command time execution
                    now = time.time()
                    combatant.setRepairTimer(now)

                    # Reset stats
                    item.db.broken = False
                    item.db.patched = False
                    item.db.material_value = material_value
                    self.msg(f"You repair the {item}.")
                else:
                    self.msg("|430You cannot repair this item|n.")
            else:
                return
