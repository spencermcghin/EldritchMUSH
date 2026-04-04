"""
Shop Commands

Implements the merchant/shop system for EldritchMUSH.

Players interact with Merchant NPCs (or shop objects) in the same room:
  browse [<merchant>]        -- list items the merchant sells with prices
  buy <item> from <merchant> -- purchase an item (costs silver)
  sell <item> to <merchant>  -- sell an item from inventory (50% buy price)

Merchants store their inventory as a list of prototype keys in db.shop_inventory.
Prices come from the prototype's value_silver field (or value_copper / 100).

Currency: characters use db.silver (silver dragons) as the primary shop currency.
"""

from evennia import Command
from evennia import spawn
from evennia.prototypes import prototypes as proto_utils


def _get_proto(key):
    """Return the first prototype dict matching key (case-insensitive), or None."""
    key_lower = key.strip().lower()
    results = proto_utils.search_prototype(key_lower)
    if results:
        return results[0]
    # Fallback: try exact uppercase key
    results = proto_utils.search_prototype(key.upper())
    if results:
        return results[0]
    return None


def _buy_price(proto):
    """Return buy price in silver from a prototype dict."""
    if proto.get("value_silver"):
        return int(proto["value_silver"])
    if proto.get("value_copper"):
        return max(1, int(proto["value_copper"]) // 10)
    return 1


def _sell_price(item):
    """Return sell price in silver (50% of value) from a spawned item object."""
    val = item.db.value_silver or 0
    if not val:
        val = (item.db.value_copper or 0) // 10
    return max(1, int(val) // 2)


def _find_merchant(caller, merchant_name):
    """Search current room for a merchant NPC matching name."""
    matches = [
        obj for obj in caller.location.contents
        if obj != caller and obj.db.shop_inventory is not None
        and merchant_name.lower() in obj.key.lower()
    ]
    return matches[0] if len(matches) == 1 else (matches if matches else None)


class CmdBrowse(Command):
    """
    Browse a merchant's wares.

    Usage:
      browse
      browse <merchant name>

    Lists all items sold by the merchant in the current room, along with
    their buy price in silver dragons. If there is only one merchant in
    the room, you may omit their name.
    """

    key = "browse"
    aliases = ["shop"]
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        caller = self.caller
        arg = self.args.strip()

        # Find merchant(s) in room
        merchants = [
            obj for obj in caller.location.contents
            if obj != caller and obj.db.shop_inventory is not None
        ]

        if not merchants:
            caller.msg("|430There are no merchants here.|n")
            return

        if arg:
            merchants = [m for m in merchants if arg.lower() in m.key.lower()]
            if not merchants:
                caller.msg(f"|430You don't see a merchant named '{arg}' here.|n")
                return

        if len(merchants) > 1:
            names = ", ".join(m.key for m in merchants)
            caller.msg(f"|430Please specify a merchant: {names}|n")
            return

        merchant = merchants[0]
        inventory = merchant.db.shop_inventory or []

        if not inventory:
            caller.msg(f"|430{merchant.key} has nothing for sale at the moment.|n")
            return

        lines = [f"\n|y=== {merchant.key}'s Wares ===|n\n"]
        lines.append(f"|w{'Item':<35} {'Price (silver)':<16}|n")
        lines.append("|w" + "-" * 51 + "|n")

        for proto_key in inventory:
            proto = _get_proto(proto_key)
            if not proto:
                continue
            name = proto.get("key", proto_key)
            price = _buy_price(proto)
            desc = proto.get("desc", "")
            if desc and len(desc) > 50:
                desc = desc[:47] + "..."
            lines.append(f"|w{name:<35}|n |g{price} silver|n")
            if desc:
                lines.append(f"  |x{desc}|n")

        lines.append("\n|xType: buy <item> from <merchant> to purchase.|n")
        caller.msg("\n".join(lines))


class CmdBuy(Command):
    """
    Buy an item from a merchant.

    Usage:
      buy <item name> from <merchant name>
      buy <item name>          (if only one merchant is present)

    Purchases the named item from a merchant in the current room. The cost
    is deducted from your silver dragons (db.silver).

    Example:
      buy iron sword from blacksmith
      buy healing potion
    """

    key = "buy"
    locks = "cmd:all()"
    help_category = "General"

    def parse(self):
        self.item_name = ""
        self.merchant_name = ""
        if " from " in self.args.lower():
            parts = self.args.lower().split(" from ", 1)
            self.item_name = parts[0].strip()
            self.merchant_name = parts[1].strip()
        else:
            self.item_name = self.args.strip()

    def func(self):
        caller = self.caller

        if not self.item_name:
            caller.msg("|430Usage: buy <item> from <merchant>|n")
            return

        # Find merchant
        merchants = [
            obj for obj in caller.location.contents
            if obj != caller and obj.db.shop_inventory is not None
        ]
        if self.merchant_name:
            merchants = [m for m in merchants if self.merchant_name in m.key.lower()]

        if not merchants:
            caller.msg("|430There are no merchants here.|n")
            return
        if len(merchants) > 1:
            names = ", ".join(m.key for m in merchants)
            caller.msg(f"|430Please specify which merchant: {names}|n")
            return

        merchant = merchants[0]
        inventory = merchant.db.shop_inventory or []

        # Find the prototype in merchant's inventory
        item_lower = self.item_name.lower()
        matched_key = None
        for proto_key in inventory:
            proto = _get_proto(proto_key)
            if proto and item_lower in proto.get("key", "").lower():
                matched_key = proto_key
                break

        if not matched_key:
            caller.msg(f"|430{merchant.key} doesn't sell '{self.item_name}'.|n  Type |wbrowse {merchant.key}|n to see available wares.")
            return

        proto = _get_proto(matched_key)
        price = _buy_price(proto)
        item_name = proto.get("key", matched_key)

        # Check funds
        silver = caller.db.silver or 0
        if silver < price:
            caller.msg(f"|400You can't afford {item_name}. It costs {price} silver; you have {silver} silver.|n")
            return

        # Spawn item into caller's inventory
        spawned = spawn(proto, location=caller)
        if not spawned:
            caller.msg("|400Something went wrong spawning the item. Please report this.|n")
            return

        caller.db.silver -= price
        caller.msg(f"|gYou pay {price} silver and receive |w{item_name}|g.|n")
        caller.location.msg_contents(
            f"|025{caller.name} purchases {item_name} from {merchant.key}.|n",
            exclude=caller
        )


class CmdSell(Command):
    """
    Sell an item to a merchant.

    Usage:
      sell <item name> to <merchant name>
      sell <item name>          (if only one merchant is present)

    Sells an item from your inventory to a merchant in the current room.
    You receive half the item's base value in silver dragons.

    Example:
      sell iron sword to blacksmith
      sell worn boots
    """

    key = "sell"
    locks = "cmd:all()"
    help_category = "General"

    def parse(self):
        self.item_name = ""
        self.merchant_name = ""
        if " to " in self.args.lower():
            parts = self.args.lower().split(" to ", 1)
            self.item_name = parts[0].strip()
            self.merchant_name = parts[1].strip()
        else:
            self.item_name = self.args.strip()

    def func(self):
        caller = self.caller

        if not self.item_name:
            caller.msg("|430Usage: sell <item> to <merchant>|n")
            return

        # Find item in inventory
        item = caller.search(self.item_name, location=caller)
        if not item:
            return

        # Find merchant
        merchants = [
            obj for obj in caller.location.contents
            if obj != caller and obj.db.shop_inventory is not None
        ]
        if self.merchant_name:
            merchants = [m for m in merchants if self.merchant_name in m.key.lower()]

        if not merchants:
            caller.msg("|430There are no merchants here.|n")
            return
        if len(merchants) > 1:
            names = ", ".join(m.key for m in merchants)
            caller.msg(f"|430Please specify which merchant: {names}|n")
            return

        merchant = merchants[0]
        price = _sell_price(item)
        item_name = item.key

        if price == 0:
            caller.msg(f"|430{merchant.key} has no interest in {item_name}.|n")
            return

        # Complete the transaction
        caller.db.silver = (caller.db.silver or 0) + price
        item.delete()
        caller.msg(f"|gYou sell |w{item_name}|g to {merchant.key} for {price} silver.|n")
        caller.location.msg_contents(
            f"|025{caller.name} sells {item_name} to {merchant.key}.|n",
            exclude=caller
        )
