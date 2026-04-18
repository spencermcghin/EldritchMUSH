"""
Learn / Recipes / Herbalist Commands

CmdLearn       — memorize a recipe from a schematic scroll in inventory.
CmdRecipes     — display all known alchemy recipes.
CmdHerbs       — browse an NPC herbalist's reagent stock.
CmdBuyHerb     — purchase reagents from an NPC herbalist.
CmdBuyRecipe   — purchase a recipe scroll from an NPC recipe seller.
"""

from evennia import Command, spawn
from evennia.prototypes import prototypes as proto_utils
from evennia.utils import evtable


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reagent_summary(proto):
    """Return a human-readable ingredient list from an alchemy prototype."""
    reagents = {}
    for i in range(1, 6):
        rn = proto.get(f"reagent_{i}")
        rq = proto.get(f"reagent_{i}_qty", 0)
        if rn and rq > 0:
            reagents[rn] = reagents.get(rn, 0) + rq
    if not reagents:
        return "None"
    return ", ".join(f"{name} x{qty}" for name, qty in sorted(reagents.items()))


# ---------------------------------------------------------------------------
# CmdLearn
# ---------------------------------------------------------------------------

class CmdLearn(Command):
    """
    Learn a recipe from a schematic scroll.

    Usage:
      learn <scroll>

    Reads a recipe schematic scroll in your inventory, learns the recipe,
    and destroys the scroll.  The recipe is permanently added to your
    recipe book.

    Example:
      learn recipe: blade oil
    """

    key = "learn"
    aliases = ["study"]
    locks = "cmd:all()"
    help_category = "Crafting"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("|430Usage: learn <scroll name>|n")
            return

        # Search inventory for the named item
        item = caller.search(args, location=caller)
        if not item:
            return

        recipe_key = item.db.recipe_key
        if not recipe_key:
            caller.msg(f"|400{item.key} is not a recipe schematic.|n")
            return

        # Initialize known_recipes if needed
        known = caller.db.known_recipes
        if not isinstance(known, set):
            known = set()

        recipe_key_upper = recipe_key.upper()
        if recipe_key_upper in known:
            caller.msg(
                f"|430You already know the recipe for {item.key.replace('Recipe: ', '')}.|n"
            )
            return

        # Learn the recipe
        known.add(recipe_key_upper)
        caller.db.known_recipes = known

        # Remove the scroll
        scroll_name = item.key
        item.delete()

        caller.msg(
            f"|230You carefully study the schematic and commit it to memory.|n\n"
            f"|gRecipe learned: |w{scroll_name}|n"
        )
        if caller.location:
            caller.location.msg_contents(
                f"|230{caller.key} studies a scroll intently, then nods "
                f"with satisfaction as the parchment crumbles to dust.|n",
                exclude=caller,
            )


# ---------------------------------------------------------------------------
# CmdRecipes
# ---------------------------------------------------------------------------

class CmdRecipes(Command):
    """
    View your known alchemy recipes.

    Usage:
      recipes

    Shows all recipes you have learned, along with their required
    ingredients.  Learn new recipes by using |wlearn <scroll>|n on a
    recipe schematic scroll.
    """

    key = "recipes"
    aliases = ["recipe book", "schematics"]
    locks = "cmd:all()"
    help_category = "Crafting"

    def func(self):
        caller = self.caller
        known = caller.db.known_recipes
        if not isinstance(known, set) or not known:
            caller.msg(
                "|430You have not learned any recipes yet.|n\n"
                "|xFind or buy recipe schematics and use |wlearn <scroll>|x to memorize them.|n"
            )
            return

        lines = ["|y=== Your Recipe Book ===|n\n"]

        for rkey in sorted(known):
            # Try to look up the alchemy prototype
            results = proto_utils.search_prototype(rkey)
            if not results:
                lines.append(f"|w{rkey}|n  |x(prototype not found)|n")
                continue
            proto = results[0]
            name = proto.get("key", rkey)
            level = proto.get("level", "?")
            stype = proto.get("substance_type", "unknown").title()
            ingredients = _reagent_summary(proto)
            effect = proto.get("effect", "")
            if effect and len(effect) > 80:
                effect = effect[:77] + "..."

            lines.append(f"|w{name}|n  |x(Level {level} {stype})|n")
            lines.append(f"  |430Requires:|n {ingredients}")
            if effect:
                lines.append(f"  |xEffect: {effect}|n")
            lines.append("")

        caller.msg("\n".join(lines))


# ---------------------------------------------------------------------------
# CmdHerbs — browse an NPC herbalist's reagent stock
# ---------------------------------------------------------------------------

class CmdHerbs(Command):
    """
    Browse a herbalist's reagent stock.

    Usage:
      herbs
      herbs <npc name>

    Lists all reagents sold by a herbalist NPC in the current room,
    along with their price in silver.
    """

    key = "herbs"
    aliases = ["browse herbs"]
    locks = "cmd:all()"
    help_category = "Crafting"

    def func(self):
        caller = self.caller
        arg = self.args.strip()

        # Find NPCs in room with reagent_shop attribute
        sellers = [
            obj for obj in caller.location.contents
            if obj != caller and obj.attributes.has("reagent_shop")
        ]

        if arg:
            sellers = [s for s in sellers if arg.lower() in s.key.lower()]

        if not sellers:
            caller.msg("|430There are no herbalists here.|n")
            return
        if len(sellers) > 1:
            names = ", ".join(s.key for s in sellers)
            caller.msg(f"|430Please specify which herbalist: {names}|n")
            return

        seller = sellers[0]
        stock = seller.attributes.get("reagent_shop") or {}

        if not stock:
            caller.msg(f"|430{seller.key} has nothing for sale right now.|n")
            return

        lines = [f"\n|y=== {seller.key}'s Herbs ===|n\n"]
        lines.append(f"|w{'Reagent':<25} {'Price (silver)':<16}|n")
        lines.append("|w" + "-" * 41 + "|n")

        for reagent_name, price in sorted(stock.items()):
            lines.append(f"|w{reagent_name:<25}|n |g{price} silver|n")

        lines.append(
            f"\n|xType: |wbuy herb <reagent> from {seller.key.split()[0].lower()}|n "
            f"|xto purchase.|n"
        )
        caller.msg("\n".join(lines))


# ---------------------------------------------------------------------------
# CmdBuyHerb — purchase reagents from a herbalist NPC
# ---------------------------------------------------------------------------

class CmdBuyHerb(Command):
    """
    Buy a reagent from a herbalist NPC.

    Usage:
      buy herb <reagent name>
      buy herb <reagent name> from <npc name>

    Purchases one unit of the named reagent and adds it to your
    reagent inventory.  Costs silver.

    Example:
      buy herb sayge
      buy herb dragon's eye from thalia
    """

    key = "buy herb"
    aliases = ["buyherb", "purchase herb"]
    locks = "cmd:all()"
    help_category = "Crafting"

    def parse(self):
        self.reagent_name = ""
        self.seller_name = ""
        if " from " in self.args.lower():
            parts = self.args.split(" from ", 1)  # preserve case for reagent
            self.reagent_name = parts[0].strip()
            self.seller_name = parts[1].strip().lower()
        else:
            self.reagent_name = self.args.strip()

    def func(self):
        caller = self.caller

        if not self.reagent_name:
            caller.msg("|430Usage: buy herb <reagent name> [from <npc>]|n")
            return

        # Find herbalist NPC(s)
        sellers = [
            obj for obj in caller.location.contents
            if obj != caller and obj.attributes.has("reagent_shop")
        ]
        if self.seller_name:
            sellers = [s for s in sellers if self.seller_name in s.key.lower()]

        if not sellers:
            caller.msg("|430There are no herbalists here.|n")
            return
        if len(sellers) > 1:
            names = ", ".join(s.key for s in sellers)
            caller.msg(f"|430Please specify which herbalist: {names}|n")
            return

        seller = sellers[0]
        stock = seller.attributes.get("reagent_shop") or {}

        # Match reagent name (case-insensitive)
        matched_name = None
        matched_price = 0
        for rname, rprice in stock.items():
            if self.reagent_name.lower() == rname.lower():
                matched_name = rname
                matched_price = rprice
                break

        if not matched_name:
            # Try partial match
            for rname, rprice in stock.items():
                if self.reagent_name.lower() in rname.lower():
                    matched_name = rname
                    matched_price = rprice
                    break

        if not matched_name:
            caller.msg(
                f"|430{seller.key} doesn't sell '{self.reagent_name}'.|n\n"
                f"|xType |wherbs|x to see available stock.|n"
            )
            return

        # Check funds
        silver = caller.db.silver or 0
        if silver < matched_price:
            caller.msg(
                f"|400You can't afford {matched_name}. "
                f"It costs {matched_price} silver; you have {silver} silver.|n"
            )
            return

        # Complete transaction
        caller.db.silver -= matched_price
        reagents = caller.db.reagents or {}
        reagents[matched_name] = reagents.get(matched_name, 0) + 1
        caller.db.reagents = reagents

        caller.msg(
            f"|gYou pay {matched_price} silver and receive 1x |w{matched_name}|g.|n"
        )
        if caller.location:
            caller.location.msg_contents(
                f"|025{caller.key} purchases herbs from {seller.key}.|n",
                exclude=caller,
            )


# ---------------------------------------------------------------------------
# CmdBuyRecipe — purchase recipe scrolls from an NPC recipe seller
# ---------------------------------------------------------------------------

class CmdBuyRecipe(Command):
    """
    Buy a recipe scroll from an NPC who sells schematics.

    Usage:
      buy recipe <recipe name>
      buy recipe <recipe name> from <npc name>

    Purchases a recipe scroll and places it in your inventory.
    Use |wlearn <scroll>|n afterwards to memorize the recipe.

    Example:
      buy recipe blade oil
      buy recipe blade oil from marta
    """

    key = "buy recipe"
    aliases = ["buyrecipe", "purchase recipe"]
    locks = "cmd:all()"
    help_category = "Crafting"

    def parse(self):
        self.recipe_name = ""
        self.seller_name = ""
        if " from " in self.args.lower():
            parts = self.args.split(" from ", 1)
            self.recipe_name = parts[0].strip()
            self.seller_name = parts[1].strip().lower()
        else:
            self.recipe_name = self.args.strip()

    def func(self):
        caller = self.caller

        if not self.recipe_name:
            caller.msg("|430Usage: buy recipe <recipe name> [from <npc>]|n")
            return

        # Find NPCs with recipe_shop
        sellers = [
            obj for obj in caller.location.contents
            if obj != caller and obj.attributes.has("recipe_shop")
        ]
        if self.seller_name:
            sellers = [s for s in sellers if self.seller_name in s.key.lower()]

        if not sellers:
            caller.msg("|430There is no one here selling recipe schematics.|n")
            return
        if len(sellers) > 1:
            names = ", ".join(s.key for s in sellers)
            caller.msg(f"|430Please specify which vendor: {names}|n")
            return

        seller = sellers[0]
        recipe_shop = seller.attributes.get("recipe_shop") or {}

        # Match recipe name (case-insensitive) — keys are prototype keys
        matched_key = None
        matched_price = 0
        recipe_lower = self.recipe_name.lower()

        for proto_key, price in recipe_shop.items():
            # Try matching against prototype key or the substance name
            if recipe_lower in proto_key.lower():
                matched_key = proto_key
                matched_price = price
                break
            # Also try looking up the prototype to match by display name
            results = proto_utils.search_prototype(proto_key)
            if results:
                scroll_name = results[0].get("key", "")
                # Strip "Recipe: " prefix for matching
                substance = scroll_name.replace("Recipe: ", "")
                if recipe_lower in substance.lower() or recipe_lower in scroll_name.lower():
                    matched_key = proto_key
                    matched_price = price
                    break

        if not matched_key:
            caller.msg(
                f"|430{seller.key} doesn't sell a recipe for '{self.recipe_name}'.|n\n"
                f"|xType |wbrowse recipes|x near the vendor to see available schematics.|n"
            )
            return

        # Look up the scroll prototype
        results = proto_utils.search_prototype(matched_key)
        if not results:
            caller.msg("|400Recipe scroll prototype not found. Report this to staff.|n")
            return
        proto = results[0]
        scroll_name = proto.get("key", matched_key)

        # Check funds
        silver = caller.db.silver or 0
        if silver < matched_price:
            caller.msg(
                f"|400You can't afford {scroll_name}. "
                f"It costs {matched_price} silver; you have {silver} silver.|n"
            )
            return

        # Spawn scroll into inventory
        spawned = spawn(proto, location=caller)
        if not spawned:
            caller.msg("|400Something went wrong spawning the scroll. Please report this.|n")
            return

        caller.db.silver -= matched_price
        caller.msg(
            f"|gYou pay {matched_price} silver and receive |w{scroll_name}|g.|n\n"
            f"|xUse |wlearn {scroll_name}|x to memorize it.|n"
        )
        if caller.location:
            caller.location.msg_contents(
                f"|025{caller.key} purchases a recipe scroll from {seller.key}.|n",
                exclude=caller,
            )


# ---------------------------------------------------------------------------
# CmdBrowseRecipes — list recipe scrolls for sale
# ---------------------------------------------------------------------------

class CmdBrowseRecipes(Command):
    """
    Browse recipe scrolls for sale.

    Usage:
      browse recipes
      browse recipes from <npc name>

    Lists all recipe schematics sold by a vendor in the current room.
    """

    key = "browse recipes"
    aliases = ["browse recipe", "recipe shop"]
    locks = "cmd:all()"
    help_category = "Crafting"

    def func(self):
        caller = self.caller
        arg = self.args.strip()

        sellers = [
            obj for obj in caller.location.contents
            if obj != caller and obj.attributes.has("recipe_shop")
        ]
        if arg:
            # strip "from " prefix if present
            name = arg.lower().replace("from ", "").strip()
            sellers = [s for s in sellers if name in s.key.lower()]

        if not sellers:
            caller.msg("|430There is no one here selling recipe schematics.|n")
            return
        if len(sellers) > 1:
            names = ", ".join(s.key for s in sellers)
            caller.msg(f"|430Please specify which vendor: {names}|n")
            return

        seller = sellers[0]
        recipe_shop = seller.attributes.get("recipe_shop") or {}

        if not recipe_shop:
            caller.msg(f"|430{seller.key} has no recipe schematics for sale.|n")
            return

        lines = [f"\n|y=== {seller.key}'s Recipe Schematics ===|n\n"]
        lines.append(f"|w{'Recipe':<35} {'Price (silver)':<16}|n")
        lines.append("|w" + "-" * 51 + "|n")

        for proto_key, price in sorted(recipe_shop.items()):
            results = proto_utils.search_prototype(proto_key)
            if not results:
                continue
            proto = results[0]
            name = proto.get("key", proto_key)
            lines.append(f"|w{name:<35}|n |g{price} silver|n")

        lines.append(
            f"\n|xType: |wbuy recipe <name> from "
            f"{seller.key.split()[0].lower()}|x to purchase.|n"
        )
        caller.msg("\n".join(lines))
