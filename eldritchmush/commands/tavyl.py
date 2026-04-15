"""
Tavyl command set — play the canonical Eldritch tavern card game.

Players sit at a Tavyl table with a dealer NPC (Mab the Gambler is the
canonical dealer at the Broken Oar, but any NPC with db.tavyl_dealer = True
will work). The dealer holds the GAME STATE on db.tavyl_table. Players
sit by spending the stake (default 1 silver). A two-player game runs
between the player and the dealer-as-AI-opponent.

Commands:
  tavyl                       — game help / status if at a table
  tavyl sit <dealer>          — sit down at a dealer's table; deals you in
  tavyl hand                  — list cards in your hand
  tavyl play <card>           — play a card from your hand (executes effect)
  tavyl draw                  — end your turn by drawing one Fate card
  tavyl pass                  — end your turn without playing or drawing
                                (same effect as Veiled Lady; only legal as
                                a "decline to act" within your turn)
  tavyl status                — table state: hand sizes, deck size, alive
  tavyl log                   — recent game events
  tavyl leave                 — fold and leave the table

Cards are real inventory items (typeclasses.objects.TavylCard) so you
can `look <card>` to read its effect. Played cards are deleted.
"""
import random
from evennia import Command
from evennia.objects.models import ObjectDB
from evennia.utils import create as _create

from world import tavyl as _t


# ===========================================================================
# Helpers
# ===========================================================================

def _find_dealer_in_room(caller):
    """Return the AI dealer NPC in the caller's room, or None."""
    if not caller.location:
        return None
    for obj in caller.location.contents:
        if obj.attributes.get("tavyl_dealer", default=False):
            return obj
    return None


def _find_player_seat(caller):
    """Return the table/dealer the caller is currently seated at, or None."""
    if not caller.location:
        return None
    for obj in caller.location.contents:
        table = obj.attributes.get("tavyl_table", default=None)
        if not table:
            continue
        if str(caller.id) in table.get("players", []):
            return obj
    return None


def _spawn_card_to(player, card_type):
    """Create a TavylCard inventory item for the given card_type."""
    from world.tavyl import card_display_name
    name = card_display_name(card_type)
    card = _create.create_object(
        "typeclasses.objects.TavylCard",
        key=name.lower(),
        location=player,
    )
    card.db.card_type = card_type
    card.aliases.add(card_type)
    # Also alias the second word ("seeress", "raven") for ease.
    bare = card_type.replace("_", " ")
    if bare != card_type:
        card.aliases.add(bare)
    return card


def _delete_one_card_in_inv(player, card_type):
    """Find and delete one inventory TavylCard matching card_type."""
    for item in player.contents:
        if (item.typeclass_path == "typeclasses.objects.TavylCard"
                and item.db.card_type == card_type):
            item.delete()
            return True
    return False


def _clear_player_cards(player):
    """Remove all TavylCard items from a player's inventory (game ended)."""
    for item in list(player.contents):
        if item.typeclass_path == "typeclasses.objects.TavylCard":
            item.delete()


def _materialize_hand(player, table):
    """Sync the player's inventory cards to match table['hands'][player_dbref]."""
    pid = str(player.id)
    target = list(table["hands"].get(pid, []))
    # Remove existing
    _clear_player_cards(player)
    # Spawn fresh
    for ct in target:
        _spawn_card_to(player, ct)


def _broadcast(dealer, line):
    """Tell the room the result of a Tavyl action."""
    if dealer.location:
        dealer.location.msg_contents(f"|c[Tavyl]|n {line}")


def push_tavyl_state(player, dealer):
    """Send a tavyl_state OOB event to the player's session(s).

    Includes the player's hand (with effect text), opponent hand
    sizes, deck/crypt counts, whose turn, alive list, and recent log.
    Frontend's TavylModal listens for this event.
    """
    if not player or not dealer:
        return
    table = dealer.attributes.get("tavyl_table", default=None)
    if not table:
        return
    pid = str(player.id)
    raw_hand = list(table.get("hands", {}).get(pid, []))
    hand = []
    for ct in raw_hand:
        hand.append({
            "type": ct,
            "name": _t.card_display_name(ct),
            "effect": _t.card_effect_text(ct),
        })
    players_payload = []
    for p_id in table.get("players", []):
        p_obj = _player_obj(table, p_id)
        players_payload.append({
            "id": p_id,
            "name": p_obj.key if p_obj else p_id,
            "handSize": len(table.get("hands", {}).get(p_id, [])),
            "alive": p_id in table.get("alive", []),
            "isYou": p_id == pid,
            "isDealer": p_id == str(dealer.id),
        })
    payload = {
        "type": "tavyl_state",
        "dealer": dealer.key,
        "stake": table.get("stake", 1),
        "yourTurn": table.get("current") == pid,
        "currentPlayer": (
            _player_obj(table, table["current"]).key if table.get("current") else None
        ),
        "fateDeckSize": len(table.get("fate_deck", [])),
        "cryptSize": len(table.get("crypt", [])),
        "direction": table.get("direction", 1),
        "alive": table.get("alive", []),
        "players": players_payload,
        "yourHand": hand,
        "log": list(table.get("log", []))[-10:],
    }
    try:
        for sess in player.sessions.all():
            sess.msg(event=payload)
    except Exception:
        pass


def _resolve_pestilence(dealer, table, victim_obj, pestilence_drawer):
    """Caller drew a Pestilence — auto-defend with Bonesman if held, else
    eliminate. Returns True if the victim survived (Bonesman played)."""
    pid = str(victim_obj.id)
    hand = table["hands"].get(pid, [])
    if _t.BONESMAN in hand:
        # Auto-play Bonesman
        _t.play_card(table, pid, _t.BONESMAN)
        # Also discard the Pestilence (it was just drawn into hand by draw_one)
        _t.play_card(table, pid, _t.PESTILENCE)
        _t.add_log(table, f"{victim_obj.key} plays Bonesman to cure the Pestilence!")
        _broadcast(dealer, f"|y{victim_obj.key} plays The Bonesman, curing the Pestilence!|n")
        _materialize_hand(victim_obj, table)
        return True
    else:
        _t.eliminate(table, pid)
        _clear_player_cards(victim_obj)
        _t.add_log(table, f"{victim_obj.key} drew Pestilence with no Bonesman — eliminated!")
        _broadcast(dealer, f"|r{victim_obj.key} drew Pestilence with no Bonesman — eliminated!|n")
        return False


def _player_obj(table, dbref_str):
    """Resolve a dbref string back to its ObjectDB instance."""
    try:
        return ObjectDB.objects.get(id=int(dbref_str))
    except Exception:
        return None


def _push_to_all_humans(dealer):
    """Call push_tavyl_state for every human player at the dealer's table."""
    table = dealer.attributes.get("tavyl_table", default=None)
    if not table:
        return
    for pid in table.get("players", []):
        if pid == str(dealer.id):
            continue
        obj = _player_obj(table, pid)
        if obj and getattr(obj, "db_account_id", None):
            push_tavyl_state(obj, dealer)


# ===========================================================================
# Dealer AI (Mab plays for the house)
# ===========================================================================

def _dealer_take_turn(dealer):
    """The dealer (NPC) plays its turn against the player. Greedy AI:
       - If holding Pestilence somehow, dump it on someone else via Knight/Assassin.
       - Otherwise play a useful action card if it favors the dealer.
       - Then draw to end turn.
    """
    table = dict(dealer.attributes.get("tavyl_table", default=None) or {})
    if not table or not table.get("started"):
        return
    pid = str(dealer.id)
    if pid not in table["alive"]:
        return
    if table["current"] != pid:
        return

    hand = table["hands"].get(pid, [])
    opponents = [_player_obj(table, o) for o in _t.opponents_of(table, pid)]
    opponents = [o for o in opponents if o]
    target = opponents[0] if opponents else None

    # Strategy: ditch threats first, then draw.
    plays = []

    # If hand is large (>= 6), consider playing a Knight or Assassin to
    # force opponent to draw — increases their chance of Pestilence.
    if target and len(hand) >= 6:
        if _t.ASSASSIN in hand:
            plays.append((_t.ASSASSIN, target))
        elif _t.KNIGHT in hand:
            plays.append((_t.KNIGHT, target))
        elif _t.MERCHANT in hand:
            plays.append((_t.MERCHANT, target))

    # Always consider a Trader if it'd give a peek at opponent's hand.
    elif target and _t.TRADER in hand and random.random() < 0.4:
        plays.append((_t.TRADER, target))

    # Resolve the planned plays
    for card_type, t_obj in plays:
        _t.play_card(table, pid, card_type)
        _t.add_log(table, f"{dealer.key} plays {_t.card_display_name(card_type)}.")
        _broadcast(dealer, f"|c{dealer.key}|n plays |y{_t.card_display_name(card_type)}|n.")
        _apply_effect(dealer, table, dealer, card_type, target=t_obj)
        if _t.is_over(table):
            return

    # End turn by drawing.
    drawn = _t.draw_one(table, pid)
    if drawn is None:
        _t.add_log(table, f"{dealer.key}: deck exhausted.")
        _broadcast(dealer, f"The Fate deck is empty. {dealer.key} ends the turn.")
    elif drawn == _t.PESTILENCE:
        _broadcast(dealer, f"|c{dealer.key}|n draws |rThe Pestilence!|n")
        _resolve_pestilence(dealer, table, dealer, dealer)
    else:
        _broadcast(dealer, f"|c{dealer.key}|n draws a card.")

    # Persist
    dealer.attributes.add("tavyl_table", table)

    # Pass to next player
    if not _t.is_over(table):
        _t.next_player(table)
        dealer.attributes.add("tavyl_table", table)
        _broadcast(dealer, f"It is now {_player_obj(table, table['current']).key}'s turn.")


# ===========================================================================
# Effect resolver
# ===========================================================================

def _apply_effect(dealer, table, player_obj, card_type, target=None):
    """Apply the in-game effect of a played card. Some effects need a
    target; others are no-args."""
    pid = str(player_obj.id)

    if card_type == _t.SEERESS:
        # Peek at top of deck. Player only — automated (peek and reorder).
        if table["fate_deck"]:
            top = table["fate_deck"][-1]
            _t.add_log(table, f"{player_obj.key} peeks at the top of the Fate deck.")
            try:
                player_obj.msg(
                    f"|x(Seeress: the next card on the Fate deck is "
                    f"|y{_t.card_display_name(top)}|x.)|n"
                )
            except Exception:
                pass

    elif card_type == _t.RAVEN:
        table["direction"] *= -1
        _t.add_log(table, f"Play order reverses.")
        _broadcast(dealer, "|y(The order of play reverses.)|n")
        # Raven also ends turn without drawing — handled by caller skipping draw

    elif card_type == _t.RESURRECTION:
        # Pull last card from Crypt back to player's hand
        if table["crypt"]:
            recovered = table["crypt"].pop()
            table["hands"].setdefault(pid, []).append(recovered)
            _t.add_log(table, f"{player_obj.key} resurrects {_t.card_display_name(recovered)} from the Crypt.")
            _materialize_hand(player_obj, table)

    elif card_type == _t.VEILED_LADY:
        # Skip turn without drawing — handled by caller skipping draw
        _t.add_log(table, f"{player_obj.key} skips the turn.")

    elif card_type == _t.ASSASSIN:
        if target:
            tid = str(target.id)
            for _ in range(2):
                drawn = _t.draw_one(table, tid)
                if drawn == _t.PESTILENCE:
                    _broadcast(dealer, f"|c{target.key}|n draws |rThe Pestilence!|n")
                    survived = _resolve_pestilence(dealer, table, target, target)
                    if not survived:
                        return
            _materialize_hand(target, table)
            _t.add_log(table, f"{player_obj.key}'s Assassin forces {target.key} to draw two.")

    elif card_type == _t.TRADER:
        if target:
            tid = str(target.id)
            t_hand = table["hands"].get(tid, [])
            if t_hand:
                taken = random.choice(t_hand)
                t_hand.remove(taken)
                table["hands"].setdefault(pid, []).append(taken)
                _t.add_log(table, f"{player_obj.key} steals a card from {target.key}.")
                _materialize_hand(target, table)
                _materialize_hand(player_obj, table)

    elif card_type == _t.KNIGHT:
        # Opponent to your left draws one
        left = _t.left_of(table, pid)
        if left:
            left_obj = _player_obj(table, left)
            drawn = _t.draw_one(table, left)
            if drawn == _t.PESTILENCE:
                _broadcast(dealer, f"|c{left_obj.key}|n draws |rThe Pestilence!|n")
                _resolve_pestilence(dealer, table, left_obj, left_obj)
            else:
                _t.add_log(table, f"{player_obj.key}'s Knight forces {left_obj.key} to draw.")
                _materialize_hand(left_obj, table)

    elif card_type == _t.MERCHANT:
        # Opponent gives you a card of THEIR choice. AI chooses randomly
        # (not optimally, since they're being asked to give).
        if target:
            tid = str(target.id)
            t_hand = table["hands"].get(tid, [])
            if t_hand:
                # If target is dealer or no UI, auto-pick least useful
                given = t_hand[0] if target.attributes.get("tavyl_dealer", default=False) else random.choice(t_hand)
                t_hand.remove(given)
                table["hands"].setdefault(pid, []).append(given)
                _t.add_log(table, f"{target.key} hands a card to {player_obj.key}.")
                _materialize_hand(target, table)
                _materialize_hand(player_obj, table)

    elif card_type == _t.KING:
        _t.add_log(table, f"{player_obj.key} plays The King — last action cancelled.")
        _broadcast(dealer, f"|y(The King cancels the previous effect.)|n")
        # Simplified: King's full mechanic (cancel any played card) is
        # complex with a history stack. For MVP we declare cancellation;
        # state was already mutated. Future: track an undo log.


# ===========================================================================
# Commands
# ===========================================================================

class CmdTavyl(Command):
    """Tavyl card game — sit, play, draw, leave.

    Usage:
      tavyl                  — show this help (or status if at a table)
      tavyl sit <dealer>     — sit at a dealer's table (costs the stake)
      tavyl hand             — list cards in your hand
      tavyl play <card>      — play a card from your hand
      tavyl draw             — end your turn by drawing a Fate card
      tavyl pass             — pass without acting (effective Veiled Lady)
      tavyl status           — table state
      tavyl log              — recent game log
      tavyl leave            — fold and leave the table

    Cards in your hand are real items — `look <card>` to read its effect.
    """
    key = "tavyl"
    aliases = ["cards"]
    locks = "cmd:all()"
    help_category = "Social"

    def func(self):
        caller = self.caller
        args = (self.args or "").strip()
        if not args:
            seat = _find_player_seat(caller)
            if seat:
                return self._show_status(seat)
            return self._show_help()

        parts = args.split(None, 1)
        sub = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""

        if sub == "sit":
            return self._sit(rest)
        if sub == "hand":
            return self._hand()
        if sub == "play":
            return self._play(rest)
        if sub == "draw":
            return self._draw()
        if sub == "pass":
            return self._pass()
        if sub == "status":
            seat = _find_player_seat(caller)
            return self._show_status(seat) if seat else caller.msg("You're not at a table.")
        if sub == "log":
            return self._log()
        if sub == "leave":
            return self._leave()
        return self._show_help()

    def _show_help(self):
        self.caller.msg(self.__doc__)

    # -------- sit ---------------------------------------------------------
    def _sit(self, dealer_name):
        caller = self.caller
        if dealer_name:
            dealer = caller.search(dealer_name, location=caller.location)
            if not dealer:
                return
        else:
            dealer = _find_dealer_in_room(caller)
            if not dealer:
                caller.msg("There's no Tavyl dealer in this room.")
                return
        if not dealer.attributes.get("tavyl_dealer", default=False):
            caller.msg(f"{dealer.key} doesn't run a Tavyl table.")
            return
        existing = dealer.attributes.get("tavyl_table", default=None)
        if existing and existing.get("started") and not _t.is_over(existing):
            if str(caller.id) in existing.get("players", []):
                # Player is already seated — re-sync their hand and re-push
                # the state so the modal opens (or re-opens) with the live
                # game instead of rejecting them.
                caller.msg(
                    f"|gYou're already at {dealer.key}'s table. "
                    f"Resuming your hand…|n"
                )
                _materialize_hand(caller, existing)
                push_tavyl_state(caller, dealer)
                return
            caller.msg(f"{dealer.key}'s table is already in play. Wait for the next round.")
            return

        stake = dealer.attributes.get("tavyl_stake", default=1) or 1
        purse = caller.db.silver or 0
        if purse < stake:
            caller.msg(f"|400You need {stake} silver to sit. You have {purse}.|n")
            return
        caller.db.silver = purse - stake

        # Start a 2-player game: caller vs dealer
        players = [str(caller.id), str(dealer.id)]
        random.shuffle(players)  # random first player
        table = _t.new_table(players, stake=stake)
        dealer.attributes.add("tavyl_table", table)
        _materialize_hand(caller, table)
        # Dealer keeps no inventory cards (held abstractly in table["hands"]).
        first = _player_obj(table, table["current"])
        _broadcast(dealer, f"A new game of Tavyl begins between {caller.key} and {dealer.key}. {first.key} plays first.")
        caller.msg(
            f"|gYou pay {stake} silver and sit at {dealer.key}'s table. "
            f"You're dealt 9 cards (one Bonesman, eight Fate). |yType "
            f"|wtavyl hand|y to see them.|n"
        )

        # Initial state push so the modal can render immediately.
        _push_to_all_humans(dealer)

        # If dealer goes first, take their turn now
        if table["current"] == str(dealer.id):
            _dealer_take_turn(dealer)
            _push_to_all_humans(dealer)

    # -------- hand --------------------------------------------------------
    def _hand(self):
        caller = self.caller
        seat = _find_player_seat(caller)
        if not seat:
            caller.msg("You're not at a Tavyl table.")
            return
        table = seat.attributes.get("tavyl_table", default=None) or {}
        hand = table.get("hands", {}).get(str(caller.id), [])
        if not hand:
            caller.msg("Your hand is empty.")
            return
        # Show as a numbered list grouped by type
        from collections import Counter
        counts = Counter(hand)
        lines = ["|yYour Tavyl hand:|n"]
        for ct in sorted(counts.keys()):
            n = counts[ct]
            name = _t.card_display_name(ct)
            suffix = f" x{n}" if n > 1 else ""
            lines.append(f"  • |w{name}|n{suffix}")
        lines.append("")
        lines.append("|x(`look <card name>` to read effect; `tavyl play <card>` to play.)|n")
        caller.msg("\n".join(lines))

    # -------- play --------------------------------------------------------
    def _play(self, args):
        caller = self.caller
        seat = _find_player_seat(caller)
        if not seat:
            caller.msg("You're not at a Tavyl table.")
            return
        table = dict(seat.attributes.get("tavyl_table", default=None) or {})
        if not table or not table.get("started"):
            caller.msg("No active game.")
            return
        if table["current"] != str(caller.id):
            caller.msg("It's not your turn.")
            return

        if not args:
            caller.msg("Play which card? `tavyl play <card name>`")
            return

        # Parse card name + optional target
        # Format: "tavyl play <card>" or "tavyl play <card> on <target>"
        target = None
        if " on " in args:
            cardpart, _, targpart = args.partition(" on ")
            cardpart = cardpart.strip()
            target = caller.search(targpart.strip(), location=caller.location)
            if not target:
                return
        else:
            cardpart = args.strip()

        # Resolve card name to a card_type in hand
        cardpart_norm = cardpart.lower().replace("the ", "").replace(" ", "_").strip()
        hand = table["hands"].get(str(caller.id), [])
        match = None
        for ct in hand:
            if ct == cardpart_norm or _t.card_display_name(ct).lower() == f"the {cardpart.lower()}" \
                    or _t.card_display_name(ct).lower() == cardpart.lower():
                match = ct
                break
        if not match:
            caller.msg(f"|400You don't have a '{cardpart}' to play.|n")
            return

        # Targeted cards
        targeted = {_t.ASSASSIN, _t.TRADER, _t.MERCHANT}
        if match in targeted and not target:
            opps = _t.opponents_of(table, str(caller.id))
            if len(opps) == 1:
                target = _player_obj(table, opps[0])
            else:
                caller.msg(f"That card needs a target. Try `tavyl play {cardpart} on <target>`.")
                return

        # Bonesman is normally only played defensively (handled in
        # _resolve_pestilence). Refuse premature play.
        if match == _t.BONESMAN:
            caller.msg("|xYou keep the Bonesman in your hand — it cures Pestilence when drawn.|n")
            return
        if match == _t.PESTILENCE:
            caller.msg("|xPestilence is not played voluntarily.|n")
            return

        _t.play_card(table, str(caller.id), match)
        _t.add_log(table, f"{caller.key} plays {_t.card_display_name(match)}.")
        _broadcast(seat, f"|g{caller.key}|n plays |y{_t.card_display_name(match)}|n.")
        _apply_effect(seat, table, caller, match, target=target)
        _materialize_hand(caller, table)
        seat.attributes.add("tavyl_table", table)

        _push_to_all_humans(seat)
        if _t.is_over(table):
            self._finish(seat, table)
            return

        # Some cards end the turn without drawing (Raven, Veiled Lady)
        if match in (_t.RAVEN, _t.VEILED_LADY):
            _t.next_player(table)
            seat.attributes.add("tavyl_table", table)
            _broadcast(seat, f"It is now {_player_obj(table, table['current']).key}'s turn.")
            self._maybe_dealer_turn(seat)
            return

        caller.msg("|x(You may play more cards or `tavyl draw` to end your turn.)|n")

    # -------- draw --------------------------------------------------------
    def _draw(self):
        caller = self.caller
        seat = _find_player_seat(caller)
        if not seat:
            caller.msg("You're not at a Tavyl table.")
            return
        table = dict(seat.attributes.get("tavyl_table", default=None) or {})
        if table["current"] != str(caller.id):
            caller.msg("It's not your turn.")
            return
        drawn = _t.draw_one(table, str(caller.id))
        if drawn is None:
            caller.msg("|xThe Fate deck is empty.|n")
        elif drawn == _t.PESTILENCE:
            _broadcast(seat, f"|g{caller.key}|n draws |rThe Pestilence!|n")
            _resolve_pestilence(seat, table, caller, caller)
        else:
            caller.msg(f"|x(You drew |y{_t.card_display_name(drawn)}|x.)|n")
            _materialize_hand(caller, table)
        seat.attributes.add("tavyl_table", table)

        if _t.is_over(table):
            self._finish(seat, table)
            return

        _t.next_player(table)
        seat.attributes.add("tavyl_table", table)
        _broadcast(seat, f"It is now {_player_obj(table, table['current']).key}'s turn.")
        _push_to_all_humans(seat)
        self._maybe_dealer_turn(seat)

    # -------- pass --------------------------------------------------------
    def _pass(self):
        caller = self.caller
        seat = _find_player_seat(caller)
        if not seat:
            caller.msg("You're not at a Tavyl table.")
            return
        table = dict(seat.attributes.get("tavyl_table", default=None) or {})
        if table["current"] != str(caller.id):
            caller.msg("It's not your turn.")
            return
        _t.add_log(table, f"{caller.key} passes the turn.")
        _broadcast(seat, f"|g{caller.key}|n passes the turn.")
        _t.next_player(table)
        seat.attributes.add("tavyl_table", table)
        _broadcast(seat, f"It is now {_player_obj(table, table['current']).key}'s turn.")
        _push_to_all_humans(seat)
        self._maybe_dealer_turn(seat)

    # -------- status / log / leave ---------------------------------------
    def _show_status(self, seat):
        caller = self.caller
        table = seat.attributes.get("tavyl_table", default=None) or {}
        lines = [f"|yTavyl table at {seat.key} (stake {table.get('stake',1)} silver)|n"]
        for pid in table.get("players", []):
            obj = _player_obj(table, pid)
            n = len(table["hands"].get(pid, []))
            alive = pid in table.get("alive", [])
            cur = "*" if table.get("current") == pid else " "
            status = "alive" if alive else "ELIMINATED"
            lines.append(f"  {cur} {obj.key if obj else pid}: {n} cards [{status}]")
        lines.append(f"  Fate deck: {len(table.get('fate_deck', []))} cards remaining")
        lines.append(f"  Crypt: {len(table.get('crypt', []))} cards discarded")
        caller.msg("\n".join(lines))

    def _log(self):
        caller = self.caller
        seat = _find_player_seat(caller)
        if not seat:
            caller.msg("You're not at a Tavyl table.")
            return
        table = seat.attributes.get("tavyl_table", default=None) or {}
        log = table.get("log", [])
        if not log:
            caller.msg("No game events yet.")
            return
        caller.msg("|yRecent Tavyl events:|n\n  " + "\n  ".join(log))

    def _leave(self):
        caller = self.caller
        seat = _find_player_seat(caller)
        if not seat:
            caller.msg("You're not at a Tavyl table.")
            return
        table = dict(seat.attributes.get("tavyl_table", default=None) or {})
        _t.eliminate(table, str(caller.id))
        _clear_player_cards(caller)
        _t.add_log(table, f"{caller.key} leaves the table.")
        _broadcast(seat, f"|g{caller.key}|n folds and leaves the table.")
        if _t.is_over(table):
            self._finish(seat, table)
            return
        seat.attributes.add("tavyl_table", table)

    # -------- finish ------------------------------------------------------
    def _finish(self, seat, table):
        winner_pid = _t.winner(table)
        winner_obj = _player_obj(table, winner_pid) if winner_pid else None
        if winner_obj:
            pot = table.get("stake", 1) * len(table.get("players", []))
            winner_obj.db.silver = (winner_obj.db.silver or 0) + pot
            _broadcast(seat, f"|y{winner_obj.key} wins the round and takes the {pot} silver pot!|n")
            _t.add_log(table, f"{winner_obj.key} wins the round.")
            try:
                winner_obj.msg(f"|gYou collect {pot} silver from the pot.|n")
            except Exception:
                pass
        else:
            _broadcast(seat, "|x(Tavyl ends with no winner.)|n")
        # Clear table state and player cards
        for pid in table.get("players", []):
            obj = _player_obj(table, pid)
            if obj:
                _clear_player_cards(obj)
        seat.attributes.remove("tavyl_table")

    # -------- dealer auto-turn -------------------------------------------
    def _maybe_dealer_turn(self, seat):
        table = seat.attributes.get("tavyl_table", default=None) or {}
        if not table or _t.is_over(table):
            return
        if table["current"] == str(seat.id):
            _dealer_take_turn(seat)
            _push_to_all_humans(seat)
            # After dealer plays, advance to caller again if still in game
            table = seat.attributes.get("tavyl_table", default=None) or {}
            if table and not _t.is_over(table):
                cur = _player_obj(table, table["current"])
                if cur:
                    self.caller.msg(f"|x(It is now {cur.key}'s turn.)|n")
            elif table:
                self._finish(seat, table)
