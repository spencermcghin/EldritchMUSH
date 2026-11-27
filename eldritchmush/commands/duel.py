"""
Duel — wagered 1v1 combat.

Two combatants each stake coin. The first to fall to 0 bleed_points
(incapacitated / "bleeding") yields. The winner takes both stakes (an
NPC's share at most once a day per player). A player's first win against
a given NPC also fires quest_duel_win and hands over duel_defeat_drops.

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
from evennia import Command, spawn
from evennia.objects.models import ObjectDB


COIN_TO_SILVER = {"copper": 0.1, "silver": 1, "gold": 20}

# An NPC never pays a real stake, and `medicine` can heal it back up, so an
# unlimited payout let a player farm the same duellist for coin. A player is
# paid the NPC's share at most once per real day per NPC; any other win just
# returns their own stake.
NPC_REWARD_COOLDOWN = 24 * 60 * 60

# A duel nobody finishes stops blocking the NPC after this long.
DUEL_TIMEOUT = 10 * 60


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
    """Return a single match for `name` in the caller's room, or None.

    quiet=True makes search() return a LIST. This helper returned it
    unwrapped, so every caller then did npc.attributes.get(...) on a list
    and raised AttributeError — `duel <anyone>` tracebacked without
    exception, making the whole duel system unreachable. (An unknown name
    returned an empty list, which is falsy, so only the valid-target path
    ever crashed.)
    """
    if not caller.location:
        return None
    matches = caller.search(name, location=caller.location, quiet=True)
    if isinstance(matches, (list, tuple)):
        return matches[0] if matches else None
    return matches


def _now():
    import time
    return time.time()


def _last_activity(duel):
    try:
        return max(float(duel.get("started_ts") or 0), float(duel.get("last_ts") or 0))
    except (TypeError, ValueError, AttributeError):
        return 0


def _in_combat_loop(char):
    """True if `char` is in its room's combat loop right now."""
    if char is None:
        return False
    room = getattr(char, "location", None)
    try:
        loop = room.attributes.get("combat_loop", default=None) if room else None
    except Exception:
        loop = None
    return bool(loop) and char in loop


def touch_duel(char):
    """Record duel activity on `char` and its opponent (called on each hit)."""
    duel = char.attributes.get("duel", default=None)
    if not duel:
        return
    now = _now()
    sides = [char]
    try:
        sides.append(ObjectDB.objects.get(id=int(duel.get("opponent_dbref"))))
    except Exception:
        pass
    for ch in sides:
        d = ch.attributes.get("duel", default=None)
        if d:
            d = dict(d)
            d["last_ts"] = now
            ch.attributes.add("duel", d)


def _is_expired(duel, holder=None):
    """True if this duel has lapsed.

    A duel lapses only when nothing has happened in it for DUEL_TIMEOUT
    (started_ts, refreshed to last_ts on every hit) AND neither duellist is
    in a combat loop. A fight still going, however long, never lapses.
    Duels stamped before started_ts existed count as idle.
    """
    last = _last_activity(duel)
    if last and (_now() - last) <= DUEL_TIMEOUT:
        return False
    if holder is not None:
        if _in_combat_loop(holder):
            return False
        try:
            other = ObjectDB.objects.get(id=int(duel.get("opponent_dbref")))
        except Exception:
            other = None
        if _in_combat_loop(other):
            return False
    return True


def _abandon(char):
    """Clear an expired duel on `char` and its opponent.

    Walking away from a duel counts as yielding: the stake already on the
    table is not returned. Refunding it would let a player who is losing
    simply wait out the timer instead of paying up.
    """
    duel = char.attributes.get("duel", default=None)
    if not duel:
        return
    other = None
    try:
        other = ObjectDB.objects.get(id=int(duel.get("opponent_dbref")))
    except Exception:
        other = None
    wager = int(duel.get("wager", 0) or 0)
    coin = duel.get("wager_coin", "silver")
    for ch in (char, other):
        if ch is None or not getattr(ch, "has_account", False):
            continue
        if ch.attributes.get("duel", default=None):
            try:
                ch.msg(f"|xYour unfinished duel has lapsed and counts as a "
                       f"yield. Your {wager} {coin} stake stays on the table.|n")
            except Exception:
                pass
    _clear(char, other)


def _npc_reward_ready(winner, npc):
    """True (and records the payout) if `winner` may take `npc`'s share."""
    ledger = dict(winner.attributes.get("duel_npc_rewards", default=None) or {})
    key = str(npc.id)
    now = _now()
    try:
        last = float(ledger.get(key) or 0)
    except (TypeError, ValueError):
        last = 0
    if last and (now - last) < NPC_REWARD_COOLDOWN:
        return False
    ledger[key] = now
    winner.attributes.add("duel_npc_rewards", ledger)
    return True


def _record_first_win(winner, npc):
    """True the first time `winner` beats `npc` in a duel, and records it.

    Stored on the player as db.duel_npc_first_wins = {npc_id: timestamp}.
    """
    wins = dict(winner.attributes.get("duel_npc_first_wins", default=None) or {})
    key = str(npc.id)
    if key in wins:
        return False
    wins[key] = _now()
    winner.attributes.add("duel_npc_first_wins", wins)
    return True


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

    # Winner takes both stakes (their own returned + loser's forfeited).
    # Against an NPC the second stake is minted (the NPC never paid it), so
    # a player beating an NPC gets it only once per NPC_REWARD_COOLDOWN.
    npc_loser = not getattr(loser, "has_account", False)
    player_winner = getattr(opponent, "has_account", False)
    if player_winner and npc_loser and not _npc_reward_ready(opponent, loser):
        total = wager
        try:
            opponent.msg(
                f"|x{loser.key} has already paid out to you today. You take "
                f"back only your own stake.|n")
        except Exception:
            pass
    else:
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

    # Defeat drops and the quest tick come once per player per NPC: the
    # first win only. They used to fire on every win, so quest items such
    # as SIGNED_OBAN_CONTRACT and LANTON_VETERAN_COIN could be duplicated
    # by beating the same NPC again (medicine heals it for a rematch).
    # Later wins still pay coin under the NPC_REWARD_COOLDOWN cap above.
    first_win = True
    if player_winner and npc_loser:
        first_win = _record_first_win(opponent, loser)

    # Quest hook (only fires if the WINNER is a player character)
    if first_win and getattr(opponent, "has_account", False):
        try:
            from commands.quests import quest_duel_win
            quest_duel_win(opponent, loser.key)
        except Exception:
            pass

    # Defeat drops — NPCs can declare items they surrender on loss.
    # We also fire item_received so the frontend toast confirms the
    # handoff visually; players should never wonder whether they
    # actually got the thing the game said they did.
    from world.npc_gifts import announce_item_drop
    drops = (loser.attributes.get("duel_defeat_drops", default=None) or []) if first_win else []
    for proto_key in drops:
        try:
            items = spawn(proto_key)
            if items:
                items[0].move_to(opponent, quiet=True)
                opponent.msg(
                    f"|y{loser.key} surrenders |w{items[0].key}|y to you.|n"
                )
                if getattr(opponent, "has_account", False):
                    announce_item_drop(opponent, items[0], from_source_name=loser.key)
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

    Only your first win against an NPC earns its surrendered items and
    quest credit. Beating the same NPC again within a day returns only
    your own stake.
    A duel with no fighting for 10 minutes lapses and counts as a yield.
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
        mine = caller.attributes.get("duel", default=None)
        if mine and _is_expired(mine, caller):
            _abandon(caller)
            mine = None
        if mine:
            caller.msg("You're already in a duel. `duel yield` to forfeit it.")
            return
        theirs = npc.attributes.get("duel", default=None)
        if theirs and _is_expired(theirs, npc):
            # Abandoned: free the NPC for everyone else.
            _abandon(npc)
            theirs = None
        if theirs:
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
            "started_ts": _now(),
        }
        caller.attributes.add("duel", info)
        npc.attributes.add("duel", {
            "opponent": caller.key,
            "opponent_dbref": caller.id,
            "wager": wager,
            "wager_coin": coin,
            "room_id": caller.location.id if caller.location else None,
            "started_ts": info["started_ts"],
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
