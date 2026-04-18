"""
Alchemy Commands

Implements the Apothecary crafting system per the Eldritch player's guide.

Skill gating:
  alchemist level 1 — may brew Level 1 substances
  alchemist level 2 — may brew Level 1-2 substances
  alchemist level 3 — may brew Level 1-3 substances

Requirements to brew:
  - Alchemist skill >= substance level
  - Apothecary Kit equipped in kit_slot (kit.db.type == "apothecary", uses > 0)
  - Required reagents present in caller.db.reagents (a dict of {name: qty})

Reagents are stored on the character as:
  caller.db.reagents = {"Sayge": 3, "Dragon's Eye": 2, ...}

Staff may use addreagent to distribute reagents to characters.
"""

from evennia import Command
from evennia import spawn
from evennia.prototypes import prototypes
from evennia.utils import evtable


class CmdBrew(Command):
    """
    Brew an alchemical substance at an Apothecary workbench.

    Usage: brew <substance name>

    Requires the Alchemist skill at a level matching the substance tier,
    an Apothecary Kit equipped in your kit slot, and the required reagents.

    Level 1 alchemist: Level 1 substances only
    Level 2 alchemist: Level 1-2 substances
    Level 3 alchemist: Level 1-3 substances

    Examples:
      brew blade oil
      brew anamnesis decoction
      brew grizzly's decoction
    """

    key = "brew"
    help_category = "mush"

    def parse(self):
        self.item = self.args.strip()

    def func(self):
        caller = self.caller

        if not caller.db.alchemist:
            caller.msg("|400You do not have the Alchemist skill.|n")
            return

        if not self.item:
            caller.msg("|430Usage: brew <substance name>|n")
            return

        # Look up alchemy prototype
        try:
            prototype = prototypes.search_prototype(self.item, require_single=True)
        except KeyError:
            caller.msg(
                "|430Substance not found, or more than one match. "
                "Check the name and try again.|n"
            )
            return

        proto_data = prototype[0]

        if proto_data.get("craft_source") != "apothecary":
            caller.msg(f"|400{self.item.title()} is not an alchemical substance.|n")
            return

        substance_name = proto_data.get("key", self.item.title())
        level = proto_data.get("level", 1)

        # Recipe gating — player must know the recipe (superusers bypass)
        if not caller.is_superuser:
            proto_key = proto_data.get("prototype_key", "").upper()
            known = caller.db.known_recipes
            if not isinstance(known, set):
                known = set()
            if proto_key not in known and substance_name.lower() not in {r.lower() for r in known}:
                caller.msg(
                    f"|400You don't know the recipe for {substance_name}. "
                    f"Find or buy the schematic first.|n"
                )
                return
        qty_produced = proto_data.get("qty_produced", 1)

        # Skill level check
        alchemist_level = caller.db.alchemist or 0
        if alchemist_level < level:
            caller.msg(
                f"|400Your Alchemist skill (level {alchemist_level}) is too low to brew "
                f"{substance_name} (requires level {level}).|n"
            )
            return

        # Kit check — must have an Apothecary Kit in kit_slot
        kit = caller.db.kit_slot[0] if caller.db.kit_slot else None
        if not kit:
            caller.msg("|430You need an Apothecary Kit equipped to brew substances.|n")
            return

        kit_type = getattr(kit.db, "type", None)
        if kit_type != "apothecary":
            caller.msg(f"|430You need an Apothecary Kit equipped, not a {kit.key}.|n")
            return

        kit_uses = getattr(kit.db, "uses", 0)
        if kit_uses <= 0:
            caller.msg(f"|400Your {kit.key} is out of uses.|n")
            return

        # Reagent checks — aggregate across all reagent slots
        reagents = caller.db.reagents or {}
        required = {}
        for i in range(1, 6):
            r_name = proto_data.get(f"reagent_{i}")
            r_qty = proto_data.get(f"reagent_{i}_qty", 0)
            if r_name and r_qty > 0:
                required[r_name] = required.get(r_name, 0) + r_qty

        missing = []
        for r_name, r_qty in required.items():
            have = reagents.get(r_name, 0)
            if have < r_qty:
                missing.append(f"{r_name} (need {r_qty}, have {have})")

        if missing and not caller.is_superuser:
            caller.msg(
                "|400You are missing the following reagents:|n\n  "
                + "\n  ".join(f"|430{m}|n" for m in missing)
            )
            return

        # All checks passed — consume reagents, use kit, spawn items
        if not caller.is_superuser:
            for r_name, r_qty in required.items():
                reagents[r_name] = reagents.get(r_name, 0) - r_qty
            caller.db.reagents = reagents

        kit.db.uses -= 1

        for _ in range(qty_produced):
            item = spawn(proto_data)
            item[0].move_to(caller, quiet=True)

        dose_word = "dose" if qty_produced == 1 else "doses"
        caller.msg(
            f"|230You carefully brew {qty_produced} {dose_word} of |430{substance_name}|n|230.|n"
        )
        if caller.location:
            caller.location.msg_contents(
                f"|230{caller.key} works carefully over their apothecary kit, "
                f"producing a batch of {substance_name}.|n",
                exclude=caller,
            )


class CmdReagents(Command):
    """
    Display your current reagent inventory.

    Usage:
      reagents

    Aliases: reagent inventory, reagentinv

    Lists all reagents you currently carry along with their quantities.
    Reagents are used at an Apothecary Workbench to brew alchemical
    substances.  They are stored separately from regular inventory items.

    See also: brew, addreagent (staff)
    """

    key = "reagents"
    aliases = ["reagent inventory", "reagentinv"]
    help_category = "Crafting"

    def func(self):
        caller = self.caller
        reagents = caller.db.reagents or {}
        stocked = sorted((name, qty) for name, qty in reagents.items() if qty > 0)

        if not stocked:
            caller.msg("|430You have no reagents in your inventory.|n")
            return

        table = evtable.EvTable("|430Reagent|n", "|430Qty|n", border="cells")
        for name, qty in stocked:
            table.add_row(name, qty)

        caller.msg(f"|230Reagent Inventory:|n\n{table}")


class CmdAddReagent(Command):
    """
    Add reagents to a character's inventory (staff only).

    Usage: addreagent <reagent name> = <amount>
           addreagent/to <character name>/<reagent name> = <amount>

    Examples:
      addreagent Sayge = 3
      addreagent Dragon's Eye = 5
    """

    key = "addreagent"
    locks = "cmd:perm(Builder)"
    help_category = "mush"

    def parse(self):
        if "=" in self.args:
            name_part, amount_part = self.args.split("=", 1)
            self.reagent_name = name_part.strip()
            try:
                self.amount = int(amount_part.strip())
            except ValueError:
                self.amount = 0
        else:
            self.reagent_name = ""
            self.amount = 0

    def func(self):
        if not self.reagent_name or self.amount <= 0:
            self.caller.msg("|430Usage: addreagent <reagent name> = <amount>|n")
            return

        target = self.caller
        reagents = target.db.reagents or {}
        reagents[self.reagent_name] = reagents.get(self.reagent_name, 0) + self.amount
        target.db.reagents = reagents
        self.caller.msg(
            f"|230Added {self.amount}x |430{self.reagent_name}|n|230 "
            f"to {target.key}'s reagents.|n"
        )
