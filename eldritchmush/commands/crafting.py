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


CRAFTING_FEES = {0: 3, 1: 5, 2: 8, 3: 12}
LEVEL_LABELS = {0: "0", 1: "I", 2: "II", 3: "III"}

"""
Crafting Commands
"""

class CmdCraft(Command):
    """
    Craft an item at a workbench using raw materials.

    Usage:
      craft <item name>

    Available at: Artificer Workbench, Bowyer Workbench, Gunsmith Workbench.
    The items you can craft depend on your trained skill:
      artificer   — kits, clothing, accessories, locks
      bowyer      — bows, arrows
      gunsmith    — pistols, bullets

    Crafting fees (silver): Level 0=3, I=5, II=8, III=12

    Requires: appropriate skill >= item level, workbench, kit equipped, materials + silver fee.

    See also: forge, repair, brew
    """

    key = "craft"
    help_category = "Crafting"

    def parse(self):
        "Very trivial parser"
        self.item = self.args.strip()

    def func(self):
        caller = self.caller

        # Determine which craft skill the caller has
        craft_skill_name = None
        craft_skill_level = 0
        for skill in ("blacksmith", "bowyer", "artificer", "gunsmith"):
            val = getattr(caller.db, skill, 0) or 0
            if val > 0:
                craft_skill_name = skill
                craft_skill_level = val
                break

        if not craft_skill_name:
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
            return

        prototype_data = prototype[0]

        craft_source = prototype_data.get("craft_source", "")

        # Check for correct kit in caller kit slot.
        kit = caller.db.kit_slot[0] if caller.db.kit_slot else None
        kit_type = getattr(kit.db, "type", None) if kit else None
        kit_uses = getattr(kit.db, "uses", 0) if kit else 0

        if not kit:
            self.msg(f"|430Please equip the kit needed to craft a {self.item}.|n")
            return

        if kit_uses <= 0 and (craft_source == kit_type):
            self.msg(f"|400Your {kit} is out of uses.|n")
            return

        if craft_source != kit_type:
            self.msg(f"|430Please equip the correct kit before attempting to craft your item.|n")
            return

        # Skill-level gating
        item_level = prototype_data.get("level", 0)
        if craft_skill_level < item_level and not caller.is_superuser:
            label = LEVEL_LABELS.get(item_level, str(item_level))
            self.msg(
                f"|400Your {craft_skill_name.title()} skill (level {craft_skill_level}) is too low "
                f"to craft this item (requires level {label}).|n"
            )
            return

        # Crafting fee
        fee = CRAFTING_FEES.get(item_level, 5)
        silver = caller.db.silver or 0
        if silver < fee and not caller.is_superuser:
            self.msg(
                f"|400Crafting this item costs {fee} silver in crafting fees. "
                f"You only have {silver} silver.|n"
            )
            return

        character_resources = {
            "iron_ingots": caller.db.iron_ingots,
            "cloth": caller.db.cloth,
            "refined_wood": caller.db.refined_wood,
            "leather": caller.db.leather
        }

        item_requirements = {
            "iron_ingots": prototype_data.get("iron_ingots", 0),
            "refined_wood": prototype_data.get("refined_wood", 0),
            "leather": prototype_data.get("leather", 0),
            "cloth": prototype_data.get("cloth", 0)
        }

        requirements_checker = [
            character_resources["iron_ingots"] >= item_requirements["iron_ingots"],
            character_resources["refined_wood"] >= item_requirements["refined_wood"],
            character_resources["leather"] >= item_requirements["leather"],
            character_resources["cloth"] >= item_requirements["cloth"]
        ]

        if all(requirements_checker) or caller.is_superuser:
            # Deduct resources
            caller.db.iron_ingots -= item_requirements["iron_ingots"]
            caller.db.refined_wood -= item_requirements["refined_wood"]
            caller.db.leather -= item_requirements["leather"]
            caller.db.cloth -= item_requirements["cloth"]
            # Deduct crafting fee
            caller.db.silver -= fee

            item = spawn(prototype[0])
            item[0].move_to(caller, quiet=True)

            # Decrement kit uses
            kit.db.uses -= 1

            item_name = prototype_data.get("key", self.item)
            self.msg(f"|230You craft a |w{item_name}|230 (crafting fee: {fee} silver).|n")
            if caller.location:
                caller.location.msg_contents(
                    f"|230{caller.key} works carefully at the workbench, producing a {item_name}.|n",
                    exclude=caller,
                )
        else:
            self.msg(f"|400You don't have the required resources.|n")


class CmdRepair(Command):
    """
    Repair a damaged item at a crafting station.

    Usage:
      repair <item name>

    Fully restores a damaged or patched weapon/armor to its original
    material value.  Can be used at any crafting workbench by a character
    with the matching craft skill.

    Requires: matching skill (blacksmith/bowyer/etc.) >= 1, workbench in room.

    See also: craft, patch, forge
    """

    key = "repair"
    help_category = "Crafting"

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

                craft_source = prototype_data.get("craft_source", "")
                material_value = prototype_data.get("material_value")

                if not material_value:
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
