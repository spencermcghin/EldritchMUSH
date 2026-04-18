"""
Herbalist shop — buy reagents directly into your reagent pouch.

Works with any NPC that has `db.reagent_shop` set to a dict of
{reagent_name: price_in_silver}. The `herbs` command browses;
`buy herb <name>` purchases and adds to char.db.reagents.
"""
from evennia import Command


def _find_herbalist(caller):
    """Return the first NPC in the room with a reagent_shop, or None."""
    if not caller.location:
        return None
    for obj in caller.location.contents:
        if obj == caller:
            continue
        if obj.attributes.get("reagent_shop", default=None):
            return obj
    return None


class CmdHerbs(Command):
    """
    Browse an herbalist's stock of reagents.

    Usage:
      herbs                  — list available reagents and prices
      buy herb <name>        — purchase a reagent (added to your pouch)
      buy herb <name> <qty>  — purchase multiple

    Requires an herbalist NPC in the room.
    """
    key = "herbs"
    aliases = ["reagent shop", "herb shop"]
    locks = "cmd:all()"
    help_category = "Crafting"

    def func(self):
        caller = self.caller
        herbalist = _find_herbalist(caller)
        if not herbalist:
            caller.msg("|400There is no herbalist here.|n")
            return

        shop = herbalist.attributes.get("reagent_shop", default={}) or {}
        if not shop:
            caller.msg(f"|c{herbalist.key}|n has nothing to sell right now.")
            return

        lines = [
            f"\n|y╔═══════════ {herbalist.key.upper()}'S HERBS ═══════════╗|n",
        ]
        for reagent, price in sorted(shop.items()):
            # Show player's current stock
            current = (caller.db.reagents or {}).get(reagent, 0)
            stock_str = f" |540(you have {current})|n" if current else ""
            lines.append(f"|y║|n  |w{reagent:<24}|n {price:>3} silver{stock_str}")
        lines.append("|y╚══════════════════════════════════════════╝|n")
        lines.append("|540Type |wbuy herb <name>|540 to purchase.|n")
        caller.msg("\n".join(lines))


class CmdBuyHerb(Command):
    """
    Purchase a reagent from an herbalist.

    Usage:
      buy herb <name>
      buy herb <name> <qty>

    The reagent is added directly to your reagent pouch.
    """
    key = "buy herb"
    aliases = ["purchase herb", "buy reagent"]
    locks = "cmd:all()"
    help_category = "Crafting"

    def func(self):
        caller = self.caller
        args = (self.args or "").strip()
        if not args:
            caller.msg("Buy which herb? `buy herb <name>` or `herbs` to browse.")
            return

        herbalist = _find_herbalist(caller)
        if not herbalist:
            caller.msg("|400There is no herbalist here.|n")
            return

        shop = herbalist.attributes.get("reagent_shop", default={}) or {}

        # Parse optional quantity at the end: "buy herb Sayge 3"
        parts = args.rsplit(None, 1)
        qty = 1
        herb_name = args
        if len(parts) == 2 and parts[1].isdigit():
            herb_name = parts[0]
            qty = max(1, int(parts[1]))

        # Case-insensitive match
        matched = None
        for reagent in shop:
            if reagent.lower() == herb_name.lower():
                matched = reagent
                break
        if not matched:
            # Partial match
            for reagent in shop:
                if herb_name.lower() in reagent.lower():
                    matched = reagent
                    break
        if not matched:
            caller.msg(f"|400{herbalist.key} doesn't sell '{herb_name}'.|n")
            return

        price = shop[matched] * qty
        purse = caller.db.silver or 0
        if purse < price:
            caller.msg(
                f"|400You need {price} silver for {qty}x {matched}. "
                f"You have {purse}.|n"
            )
            return

        caller.db.silver = purse - price
        if not caller.db.reagents:
            caller.db.reagents = {}
        caller.db.reagents[matched] = caller.db.reagents.get(matched, 0) + qty

        caller.msg(
            f"|gYou purchase {qty}x |w{matched}|g from {herbalist.key} "
            f"for {price} silver. Added to your reagent pouch.|n"
        )
        caller.location.msg_contents(
            f"|g{caller.key}|n buys herbs from |c{herbalist.key}|n.",
            exclude=[caller],
        )
