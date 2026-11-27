# Imports
import random

# Local imports
from evennia import Command, CmdSet, default_cmds, spawn, utils
from evennia.prototypes import prototypes
from world.prototype_values import proto_int, proto_str
from commands import command
from evennia.utils import evmenu


CRAFTING_FEES = {0: 3, 1: 5, 2: 8, 3: 12}
LEVEL_LABELS = {0: "0", 1: "I", 2: "II", 3: "III"}

"""
Crafting Commands
"""

class CmdForge(Command):
    """
    Forge a metal weapon or piece of armor at a forge.

    Usage:
      forge <item name>

    Available at: Forge (Maker's Hollow).  Uses iron ingots from your
    inventory to create weapons and armor.  Higher blacksmith skill levels
    unlock higher tier recipes.

    Crafting fees (silver): Level 0=3, I=5, II=8, III=12

    Examples:
      forge iron medium weapon
      forge hardened iron shield

    Requires: blacksmith skill >= item level, forge in room, materials + silver fee.

    See also: craft, repair, patch
    """

    key = "forge"
    help_category = "Crafting"

    def parse(self):
        "Very trivial parser"
        self.item = self.args.strip()

    def func(self):
        use_err_msg = "|540Usage: forge <item>|n"

        if not self.caller.db.blacksmith:
            self.msg("|400You are not trained in how to properly utilize a forge. Please find a blacksmith.|n")
            return

        if not self.item:
            self.msg(use_err_msg)
            return

        # Search for designated prototypes
        try:
            prototype = prototypes.search_prototype(self.item, require_single=True)
        except KeyError:
            self.msg("Item not found, or more than one match. Please try again.")
            return

        prototype_data = prototype[0]

        # Skill-level gating. Read via proto_int: search_prototype() returns
        # the NORMALIZED prototype, where these values live in an `attrs`
        # list, so a plain .get() saw 0 for every field — no skill gate, a
        # flat level-0 fee, and zero material cost on every item.
        item_level = proto_int(prototype_data, "level", 0)
        blacksmith_level = self.caller.db.blacksmith or 0
        if blacksmith_level < item_level and not self.caller.is_superuser:
            label = LEVEL_LABELS.get(item_level, str(item_level))
            self.msg(
                f"|400Your Blacksmith skill (level {blacksmith_level}) is too low "
                f"to forge this item (requires level {label}).|n"
            )
            return

        # Crafting fee
        fee = CRAFTING_FEES.get(item_level, 5)
        silver = self.caller.db.silver or 0
        if silver < fee and not self.caller.is_superuser:
            self.msg(
                f"|400Forging this item costs {fee} silver in crafting fees. "
                f"You only have {silver} silver.|n"
            )
            return

        character_resources = {
            "iron_ingots": self.caller.db.iron_ingots,
            "cloth": self.caller.db.cloth,
            "refined_wood": self.caller.db.refined_wood,
            "leather": self.caller.db.leather
        }

        item_requirements = {
            "iron_ingots": proto_int(prototype_data, "iron_ingots", 0),
            "refined_wood": proto_int(prototype_data, "refined_wood", 0),
            "leather": proto_int(prototype_data, "leather", 0),
            "cloth": proto_int(prototype_data, "cloth", 0)
        }

        requirements_checker = [
            character_resources["iron_ingots"] >= item_requirements["iron_ingots"],
            character_resources["refined_wood"] >= item_requirements["refined_wood"],
            character_resources["leather"] >= item_requirements["leather"],
            character_resources["cloth"] >= item_requirements["cloth"]
        ]

        if all(requirements_checker) or self.caller.is_superuser:
            # Deduct resources
            self.caller.db.iron_ingots -= item_requirements["iron_ingots"]
            self.caller.db.refined_wood -= item_requirements["refined_wood"]
            self.caller.db.leather -= item_requirements["leather"]
            self.caller.db.cloth -= item_requirements["cloth"]
            # Deduct crafting fee
            self.caller.db.silver -= fee

            blacksmith_item = spawn(prototype[0])
            blacksmith_item[0].move_to(self.caller, quiet=True)

            item_name = prototype_data.get("key", self.item)
            self.msg(f"|230You forge a |w{item_name}|230 (crafting fee: {fee} silver).|n")
            if self.caller.location:
                self.caller.location.msg_contents(
                    f"|230{self.caller.key} works the forge, producing a {item_name}.|n",
                    exclude=self.caller,
                )
        else:
            self.msg(f"|400You don't have the required resources.|n")
