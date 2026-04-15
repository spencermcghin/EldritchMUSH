"""
Duel — wagered 1v1 combat.

Two combatants each stake coin. The first to fall to 0 bleed_points
(incapacitated / "bleeding") yields. The winner takes both stakes and
fires quest_duel_win against the loser.

State lives on each combatant:
  char.db.duel = {
      "opponent": <opponent.key>,
      "opponent_dbref": <opponent.id>,
      "wager": <int>,
      "wager_coin": "silver" | "gold",
      "room_id": <room.id>,
  }

Payout is triggered from commands/combatant.takeDamage when the
losing side's bleed_points reaches 0. This file owns `duel <npc>`
(opens a duel with a willing NPC dealer) and `resolve_duel()` (the
function combatant.py calls on yield).
"""
from evennia import Command
from evennia.objects.models import ObjectDB
from evennia.utils.spawner import spawn


COIN_TO_SILVER = {"copper": 0.1, "silver": 1, "gold": 20}


def _purse(char, coin):
    return getattr(char.db, coin, 0) or 0


def _pay(char, coin, amount):
    setattr(char.db, coin, _purse(char, coin) + amount)


def _charge(char, coin, amount):
    bal = _purse(char, coin)
    if bal < amount:
        return False
    setattr(char.db, coin, bal - amount)
    return True


def _get_npc_in_room(caller, name):
    if not caller.location:
        return None
    return caller.search(name, location=caller.location, quiet=True)


def resolve_duel(loser):
    """Called from combatant.takeDamage when a combatant's bleed_points
    hits 0. If that combatant was in a duel, pay out, fire quest hook,
    spawn any defeat drops, and clear the state on both sides.
    """
    duel = loser.attributes.get("duel", default=None)
    if not duel:
        return
    opp_id = duel.get("opponent_dbref")
    if not opp_id:
        _clear(loser, None)
        return
    try:
        opponent = ObjectDB.objects.get(id=int(opp_id))
    except Exception:
        _clear(loser, None)
        return
    wager = int(duel.get("wager", 0) or 0)
    coin = duel.get("wager_coin", "silver")

    # Winner takes both stakes (their own returned + loser's forfeited)
    total = wager * 2
    _pay(opponent, coin, total)

    # Broadcast and notify
    room = loser.location or opponent.location
    if room:
        room.msg_contents(
            f"|y⚔ {opponent.key} wins the duel — {total} {coin} taken from the table.|n"
        )
    try:
        opponent.msg(f"|gYou win the Dance of Dragons and take {total} {coin}.|n")
        loser.msg(f"|rYou yield. You've lost your stake of {wager} {coin}.|n")
    except Exception:
        pass

    # Quest hook (only fires if the WINNER is a player character)
    if getattr(opponent, "has_account", False):
        try:
            from commands.quests import quest_duel_win
            quest_duel_win(opponent, loser.key)
        except Exception:
            pass

    # Defeat drops — NPCs can declare items they surrender on loss
    drops = loser.attributes.get("duel_defeat_drops", default=None) or []
    for proto_key in drops:
        try:
            items = spawn(proto_key)
            if items:
                items[0].move_to(opponent, quiet=True)
                opponent.msg(
                    f"|y{loser.key} surrenders |w{items[0].key}|y to you.|n"
                )
        except Exception:
            pass

    _clear(loser, opponent)


def _clear(a, b):
    for ch in (a, b):
        if ch is None:
            continue
        try:
            ch.attributes.remove("duel")
        except Exception:
            pass


# ===========================================================================
# Commands
# ===========================================================================

class CmdDuel(Command):
    """
    Challenge an NPC duellist to a wagered match.

    Usage:
      duel <npc>                   — challenge at their listed stake
      duel yield                   — forfeit an active duel (you lose the wager)

    The NPC must be willing — their |wduel_ready|n flag must be set by
    the encounter. Both sides put the wager on the table up front;
    whoever falls to bleeding first yields and the winner takes the
    pot. Then `strike <npc>` as normal to begin the fight.
    """

    key = "duel"
    locks = "cmd:all()"
    help_category = "Combat"

    def func(self):
        caller = self.caller
        args = (self.args or "").strip()
        if not args:
            caller.msg("Duel who? `duel <npc>` or `duel yield`.")
            return
        if args.lower() == "yield":
            return self._yield()

        npc = _get_npc_in_room(caller, args)
        if not npc:
            caller.msg(f"You see no '{args}' here.")
            return
        if not npc.attributes.get("duel_ready", default=False):
            caller.msg(f"{npc.key} isn't taking challenges.")
            return
        if caller.attributes.get("duel", default=None):
            caller.msg("You're already in a duel. `duel yield` to forfeit it.")
            return
        if npc.attributes.get("duel", default=None):
            caller.msg(f"{npc.key} is already committed to another duel.")
            return

        wager = int(npc.attributes.get("duel_wager", default=1) or 1)
        coin = str(npc.attributes.get("duel_wager_coin", default="silver") or "silver")

        purse = _purse(caller, coin)
        if purse < wager:
            caller.msg(
                f"|400{npc.key} won't play unless you match the stake of "
                f"{wager} {coin}. You have {purse}.|n"
            )
            return
        if not _charge(caller, coin, wager):
            caller.msg(f"|400You can't cover the {wager} {coin} stake.|n")
            return

        # Stamp duel state on both sides — NPC pays its own stake
        # abstractly (it's already represented by duel_defeat_drops).
        info = {
            "opponent": npc.key,
            "opponent_dbref": npc.id,
            "wager": wager,
            "wager_coin": coin,
            "room_id": caller.location.id if caller.location else None,
        }
        caller.attributes.add("duel", info)
        npc.attributes.add("duel", {
            "opponent": caller.key,
            "opponent_dbref": caller.id,
            "wager": wager,
            "wager_coin": coin,
            "room_id": caller.location.id if caller.location else None,
        })

        caller.location.msg_contents(
            f"|y⚔ {caller.key} and {npc.key} set |w{wager} {coin}|y each on "
            f"the table. The Dance of Dragons begins. First to yield loses all.|n"
        )
        caller.msg(
            "|xStart the fight with |wstrike " + npc.key.lower() +
            "|x (or whatever maneuver you prefer). First to bleed yields.|n"
        )

    def _yield(self):
        caller = self.caller
        duel = caller.attributes.get("duel", default=None)
        if not duel:
            caller.msg("You're not in a duel.")
            return
        # Forfeit → treat as if we hit 0 bleed
        resolve_duel(caller)
        caller.msg("|rYou have yielded the duel.|n")
