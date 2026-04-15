"""
Tavyl — the canonical Eldritch tavern card game.

Source: World Development/Card Game/Tavyl Rules.pdf (Drive).

Object: be the last player to survive the Pestilence. Each turn you may
play any number of cards from your hand (executing their effects), then
end your turn by drawing one card from the Fate deck. If you draw
Pestilence, you must play a Bonesman to cancel it or you're eliminated.

Cards (action cards, 4 copies each in the Fate deck):
  SEERESS    — Look at the top of the Fate deck; place it back anywhere.
  RAVEN      — Reverse play order; end your turn without drawing.
  RESURRECTION — Return a card from the Crypt to your hand.
  VEILED LADY  — Skip your turn without drawing.
  ASSASSIN   — Choose an opponent; they draw two.
  TRADER     — Take a random card from an opponent's hand.
  KNIGHT     — The opponent to your left draws a card.
  MERCHANT   — Choose an opponent; they give you a card of THEIR choice.
  KING       — Cancel any card EXCEPT Bonesman or Pestilence.

Special cards:
  PESTILENCE — N-1 in the deck (one less than the number of players).
               Drawing it eliminates you unless you play a Bonesman.
  BONESMAN   — Each player starts with one. Cancels a Pestilence.

Two-player MUSH version: each player starts with a Bonesman + 8 cards
in hand; the Fate deck contains 1 Pestilence + 32 action cards minus
the dealt hands.

This module owns the GAME STATE; commands/tavyl.py provides the player
interface; typeclasses/objects.TavylCard is the inventory-item form.
"""
import random
import time

# Card type constants
PESTILENCE  = "pestilence"
BONESMAN    = "bonesman"
SEERESS     = "seeress"
RAVEN       = "raven"
RESURRECTION = "resurrection"
VEILED_LADY = "veiled_lady"
ASSASSIN    = "assassin"
TRADER      = "trader"
KNIGHT      = "knight"
MERCHANT    = "merchant"
KING        = "king"

ACTION_CARDS = [
    SEERESS, RAVEN, RESURRECTION, VEILED_LADY,
    ASSASSIN, TRADER, KNIGHT, MERCHANT, KING,
]

CARD_INFO = {
    PESTILENCE: {
        "name": "The Pestilence",
        "effect": (
            "Drawing this eliminates you from the game unless you play a "
            "Bonesman to cancel its effect."
        ),
    },
    BONESMAN: {
        "name": "The Bonesman",
        "effect": "Cure a Pestilence. Play to cancel a Pestilence.",
    },
    SEERESS: {
        "name": "The Seeress",
        "effect": (
            "Look at the top card of the Fate deck and place it back into "
            "the deck in any position you choose."
        ),
    },
    RAVEN: {
        "name": "The Raven",
        "effect": "Reverse the order of play and end your turn without drawing.",
    },
    RESURRECTION: {
        "name": "The Resurrection",
        "effect": "Return a card from the Crypt to your hand.",
    },
    VEILED_LADY: {
        "name": "The Veiled Lady",
        "effect": "Skip your turn without drawing a card.",
    },
    ASSASSIN: {
        "name": "The Assassin",
        "effect": "Choose an opponent. They must draw two cards.",
    },
    TRADER: {
        "name": "The Trader",
        "effect": "Choose a card at random from an opponent's hand.",
    },
    KNIGHT: {
        "name": "The Knight",
        "effect": "The opponent to your left must draw a card.",
    },
    MERCHANT: {
        "name": "The Merchant",
        "effect": (
            "Choose an opponent. They must give you a card from their hand "
            "of their choosing."
        ),
    },
    KING: {
        "name": "The King",
        "effect": "Cancel the effect of any card except Bonesman or Pestilence.",
    },
}


def build_fate_deck(num_players):
    """Build the shuffled Fate deck for a game with `num_players`.

    - 4 copies of each action card
    - (num_players - 1) Pestilence cards
    Bonesman cards are NOT in the deck — each player gets one in their
    starting hand instead.
    """
    deck = []
    for ct in ACTION_CARDS:
        deck.extend([ct] * 4)
    deck.extend([PESTILENCE] * max(1, num_players - 1))
    random.shuffle(deck)
    return deck


def card_display_name(card_type):
    return CARD_INFO.get(card_type, {}).get("name", card_type.title())


def card_effect_text(card_type):
    return CARD_INFO.get(card_type, {}).get("effect", "")


# ---------------------------------------------------------------------------
# Game state on a "table" (the dealer NPC carries it on db.tavyl_table).
# Schema:
#   {
#     "players":   [<dbref-strings>],   # turn order
#     "hands":     {<dbref>: [<card_type>, ...]},
#     "fate_deck": [<card_type>, ...],
#     "crypt":     [<card_type>, ...],
#     "current":   <dbref>,             # whose turn
#     "direction": 1 or -1,             # 1=clockwise (left), -1=reversed
#     "alive":     [<dbref>, ...],
#     "stake":     int (silver),
#     "started":   bool,
#     "log":       [str, ...]           # last 20 game events for `tavyl log`
#   }
# ---------------------------------------------------------------------------

INITIAL_HAND_SIZE = 8
MAX_LOG = 20


def new_table(players, stake=1):
    """Initialize a fresh Tavyl game state for the given player dbrefs."""
    deck = build_fate_deck(len(players))
    hands = {}
    for p in players:
        hands[p] = [BONESMAN] + [deck.pop() for _ in range(INITIAL_HAND_SIZE)]
    return {
        "players": list(players),
        "hands": hands,
        "fate_deck": deck,
        "crypt": [],
        "current": players[0],
        "direction": 1,
        "alive": list(players),
        "stake": int(stake),
        "started": True,
        "log": [f"A new game of Tavyl begins. Stakes: {stake} silver."],
        "started_ts": int(time.time()),
    }


def add_log(table, line):
    table["log"] = (table.get("log") or []) + [line]
    table["log"] = table["log"][-MAX_LOG:]


def next_player(table):
    """Advance the current-player pointer by direction, skipping eliminated."""
    if not table["alive"]:
        return None
    idx = table["players"].index(table["current"])
    n = len(table["players"])
    for _ in range(n):
        idx = (idx + table["direction"]) % n
        cand = table["players"][idx]
        if cand in table["alive"]:
            table["current"] = cand
            return cand
    return None


def left_of(table, player):
    """The 'opponent to your left' — next in current direction."""
    if player not in table["players"]:
        return None
    idx = table["players"].index(player)
    n = len(table["players"])
    for _ in range(n):
        idx = (idx + table["direction"]) % n
        cand = table["players"][idx]
        if cand in table["alive"] and cand != player:
            return cand
    return None


def opponents_of(table, player):
    return [p for p in table["alive"] if p != player]


def draw_one(table, player):
    """Player draws one from the top of the Fate deck.

    Returns the drawn card_type (or None if deck empty). Caller is
    responsible for handling Pestilence after the draw (check hand for
    Bonesman; eliminate or auto-defend).
    """
    if not table["fate_deck"]:
        return None
    card = table["fate_deck"].pop()
    table["hands"].setdefault(player, []).append(card)
    return card


def play_card(table, player, card_type):
    """Move a card from player's hand into the Crypt. Returns True if
    the card was in their hand and was moved.

    Effect resolution is the caller's responsibility — this function
    just handles the ledger.
    """
    hand = table["hands"].get(player, [])
    if card_type not in hand:
        return False
    hand.remove(card_type)
    table["crypt"].append(card_type)
    return True


def eliminate(table, player):
    """Remove a player from `alive` and discard their hand to the Crypt."""
    if player in table["alive"]:
        table["alive"].remove(player)
    hand = table["hands"].get(player, [])
    table["crypt"].extend(hand)
    table["hands"][player] = []


def is_over(table):
    return len(table["alive"]) <= 1


def winner(table):
    return table["alive"][0] if len(table["alive"]) == 1 else None
