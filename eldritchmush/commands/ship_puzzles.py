"""Puzzle commands for the Ship walk-in arc.

Three room-attached puzzles drive three sub-quests of walkin_ship:

  Cargo Hold (typeclasses.rooms.Room):
    BucketPuzzleCmdSet
      - fill <bucket>            fill named bucket to its capacity
      - pour <bucket> <bucket>   pour from one bucket into another
      - empty <bucket>           dump a bucket
      - help buckets             show the current state + usage

  Doomed Ship's Deck:
    KnotPuzzleCmdSet
      - tie <knot> on <mast>     tie a named knot on a named mast
    ConstellationPuzzleCmdSet
      - chart <constellation> <direction>

The puzzles store their state on the room (`room.db.bucket_state`,
`room.db.knots_tied`, `room.db.stars_charted`). When a player solves
one, the matching quest objective ticks via quest_explore.
"""

from evennia import Command, CmdSet


# ────────────────────────────────────────────────────────────────────
# BUCKET PUZZLE — Cargo Hold
#
# Three buckets, capacities 8 / 5 / 3 litres. Start empty. Goal: any
# bucket contains exactly 4 litres. Classic Die-Hard puzzle.
#
# Solution path:
#   fill 8  → pour 8 5 → pour 5 3 → empty 3 → pour 5 3 → pour 8 5 →
#   pour 5 3      (5L bucket now holds 4L)
# (Other paths exist; we win on first 4L sighted anywhere.)
# ────────────────────────────────────────────────────────────────────

BUCKET_CAP = {"8": 8, "5": 5, "3": 3}


def _bucket_state(room):
    """Return the room's per-bucket fill, initialising if missing."""
    state = room.db.bucket_state
    if not state or set(state.keys()) != {"8", "5", "3"}:
        state = {"8": 0, "5": 0, "3": 0}
        room.db.bucket_state = state
    return state


def _bucket_state_line(state):
    return (
        f"|w[ 8L: {state['8']}L | 5L: {state['5']}L | 3L: {state['3']}L ]|n"
    )


def _check_bucket_win(room, caller):
    """If any bucket holds exactly 4L and this player is on the quest,
    tick the objective and reset the state."""
    state = _bucket_state(room)
    if 4 in state.values():
        room.msg_contents(
            f"|yA bucket reads exactly four litres. {caller.key} has "
            f"measured what the engineer needed.|n"
        )
        # Reset so other players can solve too.
        room.db.bucket_state = {"8": 0, "5": 0, "3": 0}
        try:
            from commands.quests import quest_explore
            quest_explore(caller, "plugged hull")
        except Exception:
            pass
        return True
    return False


class CmdFillBucket(Command):
    """Fill a bucket to its capacity.

    Usage: fill <bucket>      (where <bucket> is 8, 5, or 3)
    """
    key = "fill"
    locks = "cmd:all()"
    help_category = "Ship"

    def func(self):
        arg = (self.args or "").strip().lower().replace("l", "").replace("litre", "")
        if arg not in BUCKET_CAP:
            self.caller.msg("|rUse: fill 8 / fill 5 / fill 3|n")
            return
        room = self.caller.location
        state = _bucket_state(room)
        state[arg] = BUCKET_CAP[arg]
        room.db.bucket_state = state
        self.caller.msg(
            f"You fill the {arg}-litre bucket. {_bucket_state_line(state)}"
        )
        _check_bucket_win(room, self.caller)


class CmdPourBucket(Command):
    """Pour one bucket into another. Stops when source is empty or
    destination is full — whichever happens first.

    Usage: pour <from> <to>      (each is 8, 5, or 3)
    """
    key = "pour"
    locks = "cmd:all()"
    help_category = "Ship"

    def func(self):
        parts = (self.args or "").strip().lower().replace("into", " ").split()
        parts = [p.replace("l", "").replace("litre", "") for p in parts if p]
        if len(parts) != 2 or any(p not in BUCKET_CAP for p in parts):
            self.caller.msg("|rUse: pour <from> <to>  e.g. pour 8 5|n")
            return
        src, dst = parts
        if src == dst:
            self.caller.msg("|rYou can't pour a bucket into itself.|n")
            return
        room = self.caller.location
        state = _bucket_state(room)
        avail = state[src]
        room_in_dst = BUCKET_CAP[dst] - state[dst]
        moved = min(avail, room_in_dst)
        state[src] -= moved
        state[dst] += moved
        room.db.bucket_state = state
        self.caller.msg(
            f"You pour {moved}L from the {src}-litre bucket into the "
            f"{dst}-litre. {_bucket_state_line(state)}"
        )
        _check_bucket_win(room, self.caller)


class CmdEmptyBucket(Command):
    """Empty a bucket back into the sea (or onto the deck).

    Usage: empty <bucket>     (8, 5, or 3)
    """
    key = "empty"
    locks = "cmd:all()"
    help_category = "Ship"

    def func(self):
        arg = (self.args or "").strip().lower().replace("l", "").replace("litre", "")
        if arg not in BUCKET_CAP:
            self.caller.msg("|rUse: empty 8 / empty 5 / empty 3|n")
            return
        room = self.caller.location
        state = _bucket_state(room)
        state[arg] = 0
        room.db.bucket_state = state
        self.caller.msg(
            f"You empty the {arg}-litre bucket. {_bucket_state_line(state)}"
        )


class CmdHelpBuckets(Command):
    """Show the bucket puzzle state and commands."""
    key = "help buckets"
    aliases = ["buckets"]
    locks = "cmd:all()"
    help_category = "Ship"

    def func(self):
        room = self.caller.location
        state = _bucket_state(room)
        self.caller.msg(
            f"|wThree buckets:|n 8, 5, and 3 litres. Goal: measure "
            f"exactly 4 litres.\n"
            f"  |wfill <bucket>|n        fill to capacity\n"
            f"  |wpour <from> <to>|n     pour between buckets\n"
            f"  |wempty <bucket>|n       dump it out\n"
            f"Current: {_bucket_state_line(state)}"
        )


class BucketPuzzleCmdSet(CmdSet):
    """Attached to the Cargo Hold room."""
    key = "BucketPuzzleCmdSet"
    priority = 1

    def at_cmdset_creation(self):
        self.add(CmdFillBucket())
        self.add(CmdPourBucket())
        self.add(CmdEmptyBucket())
        self.add(CmdHelpBuckets())


# ────────────────────────────────────────────────────────────────────
# KNOT PUZZLE — Ship's Deck
#
# Four masts, each requires a specific knot. The Chief Engineer's
# syllabus item describes the mapping. Players type:
#   tie <knot> on <mast>
# When all four masts have their correct knot, the objective ticks.
# ────────────────────────────────────────────────────────────────────

KNOT_MAPPING = {
    "mainmast":   "bowline",
    "foremast":   "sheet bend",
    "mizzenmast": "clove hitch",
    "bowsprit":   "figure eight",
}
KNOT_ALIASES = {  # normalize input forms
    "sheet-bend": "sheet bend", "sheetbend": "sheet bend",
    "clove": "clove hitch", "clove-hitch": "clove hitch",
    "figure-eight": "figure eight", "figure 8": "figure eight",
    "fig 8": "figure eight",
    "main": "mainmast", "fore": "foremast", "mizzen": "mizzenmast",
    "main mast": "mainmast", "fore mast": "foremast",
    "mizzen mast": "mizzenmast", "bow sprit": "bowsprit",
}


def _norm(s):
    s = (s or "").strip().lower()
    return KNOT_ALIASES.get(s, s)


class CmdTieKnot(Command):
    """Tie a knot on one of the four masts.

    Usage: tie <knot> on <mast>
      Example: tie bowline on mainmast

    The Chief Engineer's syllabus (on the deck) lists the correct
    knot for each mast.
    """
    key = "tie"
    locks = "cmd:all()"
    help_category = "Ship"

    def func(self):
        # Parse "tie <knot> on <mast>"
        raw = (self.args or "").strip().lower()
        if " on " not in raw:
            self.caller.msg("|rUse: tie <knot> on <mast>  e.g. tie bowline on mainmast|n")
            return
        knot_raw, mast_raw = raw.split(" on ", 1)
        knot = _norm(knot_raw)
        mast = _norm(mast_raw)
        if mast not in KNOT_MAPPING:
            self.caller.msg(
                f"|rThere is no mast called '{mast_raw.strip()}'. The "
                f"masts are: mainmast, foremast, mizzenmast, bowsprit.|n"
            )
            return
        room = self.caller.location
        tied = dict(room.db.knots_tied or {})
        if KNOT_MAPPING[mast] != knot:
            self.caller.msg(
                f"|rYou attempt to tie a {knot} on the {mast}, but the "
                f"rope slips loose. Wrong knot for this mast.|n"
            )
            return
        if tied.get(mast):
            self.caller.msg(
                f"|yThe {mast} already has a proper {knot} on it.|n"
            )
            return
        tied[mast] = knot
        room.db.knots_tied = tied
        remaining = [m for m in KNOT_MAPPING if not tied.get(m)]
        self.caller.msg(
            f"|gYou tie a {knot} on the {mast}. The rigging holds.|n  "
            f"|540({len(tied)}/4 masts secured.)|n"
        )
        # Quest tick — one tick per mast.
        try:
            from commands.quests import quest_explore
            quest_explore(self.caller, "knots tied")
        except Exception:
            pass
        if not remaining:
            room.msg_contents(
                f"|yAll four masts hold. The rigging is whole again — "
                f"{self.caller.key} can be heard cursing thanks at it.|n"
            )
            # Reset so other players can also experience the puzzle.
            room.db.knots_tied = {}


class KnotPuzzleCmdSet(CmdSet):
    key = "KnotPuzzleCmdSet"
    priority = 1

    def at_cmdset_creation(self):
        self.add(CmdTieKnot())


# ────────────────────────────────────────────────────────────────────
# CONSTELLATION PUZZLE — Ship's Deck
#
# Four Annwyn constellations, each belongs to one cardinal direction.
# Players type:
#   chart <constellation> <direction>
# When all four are charted correctly, the objective ticks.
# ────────────────────────────────────────────────────────────────────

CONSTELLATION_MAPPING = {
    "drowned crown":    "north",
    "broken oar":       "south",
    "hollow tree":      "east",
    "stag of the deep": "west",
}
CONSTELLATION_ALIASES = {
    "crown": "drowned crown", "the drowned crown": "drowned crown",
    "oar": "broken oar", "the broken oar": "broken oar",
    "tree": "hollow tree", "the hollow tree": "hollow tree",
    "stag": "stag of the deep", "the stag": "stag of the deep",
    "stag of deep": "stag of the deep",
    "n": "north", "s": "south", "e": "east", "w": "west",
}


def _norm_star(s):
    s = (s or "").strip().lower()
    return CONSTELLATION_ALIASES.get(s, s)


class CmdChartStar(Command):
    """Chart a constellation to a cardinal direction.

    Usage: chart <constellation> <direction>
      Example: chart drowned crown north

    The constellation chart on the deck shows which star-cluster sits
    over which heading on the Annwyn side of the Mists.
    """
    key = "chart"
    locks = "cmd:all()"
    help_category = "Ship"

    def func(self):
        raw = (self.args or "").strip().lower()
        if not raw:
            self.caller.msg("|rUse: chart <constellation> <direction>|n")
            return
        # Last word is direction; remainder is the constellation name.
        parts = raw.rsplit(" ", 1)
        if len(parts) != 2:
            self.caller.msg("|rUse: chart <constellation> <direction>|n")
            return
        const_raw, dir_raw = parts
        const = _norm_star(const_raw)
        direction = _norm_star(dir_raw)
        if const not in CONSTELLATION_MAPPING:
            self.caller.msg(
                f"|rNo such constellation: '{const_raw}'. The four are: "
                f"the Drowned Crown, the Broken Oar, the Hollow Tree, "
                f"the Stag of the Deep.|n"
            )
            return
        if direction not in ("north", "south", "east", "west"):
            self.caller.msg("|rDirection must be north, south, east, or west.|n")
            return
        room = self.caller.location
        charted = dict(room.db.stars_charted or {})
        if CONSTELLATION_MAPPING[const] != direction:
            self.caller.msg(
                f"|rThe navigator shakes his head. The {const} does not "
                f"sit over {direction} in these skies.|n"
            )
            return
        if charted.get(const):
            self.caller.msg(f"|yThe {const} is already charted.|n")
            return
        charted[const] = direction
        room.db.stars_charted = charted
        self.caller.msg(
            f"|gThe {const} sits over {direction}. The navigator scratches "
            f"the mark on the chart.|n  |540({len(charted)}/4 constellations "
            f"charted.)|n"
        )
        try:
            from commands.quests import quest_explore
            quest_explore(self.caller, "stars charted")
        except Exception:
            pass
        if len(charted) == 4:
            room.msg_contents(
                f"|yThe course is set. Nosaj nods grimly and turns the "
                f"wheel — {self.caller.key} has read the wrong stars and "
                f"read them right.|n"
            )
            room.db.stars_charted = {}


class ConstellationPuzzleCmdSet(CmdSet):
    key = "ConstellationPuzzleCmdSet"
    priority = 1

    def at_cmdset_creation(self):
        self.add(CmdChartStar())
