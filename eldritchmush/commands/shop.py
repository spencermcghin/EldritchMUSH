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


def _base_buy_price(proto):
    """Return base buy price in silver from a prototype dict (no rep modifier)."""
    if proto.get("value_silver"):
        return int(proto["value_silver"])
    if proto.get("value_copper"):
        return max(1, int(proto["value_copper"]) // 10)
    return 1


def _base_sell_price(item):
    """Return base sell price (50% of value) from a spawned item object."""
    val = item.db.value_silver or 0
    if not val:
        val = (item.db.value_copper or 0) // 10
    return max(1, int(val) // 2)


def _rep_with(char, merchant):
    """Lookup char.db.npc_rep[merchant.key.lower()][rep] (default 0)."""
    try:
        rep_db = char.db.npc_rep or {}
        entry = rep_db.get((merchant.key or "").lower())
        if entry:
            return int(entry.get("rep", 0) or 0)
    except Exception:
        pass
    return 0


def _buy_multiplier(rep):
    """Markup/discount on a merchant's BUY price (what the player pays)
    based on the player's npc_rep with that merchant. Returns None to
    refuse the sale entirely (rep is too low — won't deal with you)."""
    if rep <= -10:
        return None
    if rep <= -5:
        return 1.25
    if rep < 0:
        return 1.10
    if rep < 5:
        return 1.00
    if rep < 10:
        return 0.92
    return 0.85


def _sell_multiplier(rep):
    """Multiplier on a player's SELL value (what the merchant pays out).
    Returns None if rep too low — merchant won't take their goods."""
    if rep <= -10:
        return None
    if rep <= -5:
        return 0.30
    if rep < 0:
        return 0.40
    if rep < 5:
        return 0.50  # legacy default
    if rep < 10:
        return 0.55
    return 0.60


def _buy_price(proto, char=None, merchant=None):
    """Final buy price after rep modifier. Returns None if the merchant
    refuses (rep ≤ -10)."""
    base = _base_buy_price(proto)
    if char is None or merchant is None:
        return base
    mult = _buy_multiplier(_rep_with(char, merchant))
    if mult is None:
        return None
    return max(1, int(round(base * mult)))


def _sell_price(item, char=None, merchant=None):
    """Final sell payout after rep modifier. Returns None if the
    merchant refuses to buy from this character (rep ≤ -10)."""
    val = item.db.value_silver or 0
    if not val:
        val = (item.db.value_copper or 0) // 10
    if char is None or merchant is None:
        return _base_sell_price(item)
    mult = _sell_multiplier(_rep_with(char, merchant))
    if mult is None:
        return None
    return max(1, int(round(int(val) * mult)))


def _merchants_in_room(caller):
    """All merchant objects in the caller's current room."""
    return [
        obj for obj in caller.location.contents
        if obj != caller and obj.db.shop_inventory is not None
    ]


def _resolve_merchant(caller, name=""):
    """Resolve a single merchant in the caller's room.

    Returns (merchant, error_msg) — exactly one of the two is None.
    Never dead-ends on ambiguity: if several merchants match (e.g.
    duplicate-keyed merchants in the same room), prefer an exact key
    match, otherwise quietly take the first candidate. This mirrors the
    quiet take-first search idiom used by CmdGet/strike/shoot.
    """
    merchants = _merchants_in_room(caller)
    if not merchants:
        return None, "|430There are no merchants here.|n"
    if name:
        name_l = name.strip().lower()
        matches = [m for m in merchants if name_l in (m.key or "").lower()]
        if not matches:
            return None, f"|430You don't see a merchant named '{name}' here.|n"
        exact = [m for m in matches if (m.key or "").lower() == name_l]
        return (exact[0] if exact else matches[0]), None
    # Bare command with one or more merchants present: take the first.
    return merchants[0], None


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

        merchant, err = _resolve_merchant(caller, arg)
        if err:
            caller.msg(err)
            return

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
            price = _buy_price(proto, char=caller, merchant=merchant)
            if price is None:
                # Merchant refuses to deal with this character.
                price_str = "|r—|n"
            else:
                price_str = f"{price} silver"
            desc = proto.get("desc", "")
            if desc and len(desc) > 50:
                desc = desc[:47] + "..."
            lines.append(f"|w{name:<35}|n |g{price_str}|n")
            if desc:
                lines.append(f"  |x{desc}|n")

        lines.append("\n|xType: buy <item> from <merchant> to purchase.|n")

        # If other merchants share the room, mention them rather than
        # ever raising a multimatch wall.
        others = [m for m in _merchants_in_room(caller) if m != merchant]
        if others:
            names = ", ".join(m.key for m in others)
            lines.append(f"|xAlso trading here: {names}. Use: browse <merchant name>|n")

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
        merchant, err = _resolve_merchant(caller, self.merchant_name)
        if err:
            caller.msg(err)
            return

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
        price = _buy_price(proto, char=caller, merchant=merchant)
        item_name = proto.get("key", matched_key)

        if price is None:
            caller.msg(
                f"|430{merchant.key} eyes you coldly and refuses to sell. "
                f"Mend your standing first.|n"
            )
            return

        # Check funds
        silver = caller.db.silver or 0
        if silver < price:
            caller.msg(f"|400You can't afford {item_name}. It costs {price} silver; you have {silver} silver.|n")
            return

        # Spawn item into caller's inventory. Note: spawn() ignores a
        # `location` kwarg, so move the spawned object explicitly.
        spawned = spawn(proto)
        if not spawned:
            caller.msg("|400Something went wrong spawning the item. Please report this.|n")
            return
        for obj in spawned:
            obj.location = caller

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

        # Find item in inventory — quiet search, take the first match so
        # stacked identical items never raise Evennia's multimatch prompt.
        matches = caller.search(self.item_name, location=caller, quiet=True)
        if not matches:
            caller.msg(f"|430You aren't carrying '{self.item_name}'.|n")
            return
        item = matches[0]

        # Find merchant
        merchant, err = _resolve_merchant(caller, self.merchant_name)
        if err:
            caller.msg(err)
            return

        price = _sell_price(item, char=caller, merchant=merchant)
        item_name = item.key

        if price is None:
            caller.msg(
                f"|430{merchant.key} won't take a thing from your hand. "
                f"You've worn out your welcome here.|n"
            )
            return
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
