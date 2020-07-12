# Local imports
from evennia import Command
from commands.combat_commands import Helper
from commands.combat_commands.strike import *
from world.combat_loop import CombatLoop


class CmdStrike(Command):
    """
    issues an attack

    Usage:

    strike <target>

    This will calculate an attack score based on your weapon and master of arms level.
    """

    key = "strike"
    aliases = ["hit", "slash", "bash", "punch"]
    help_category = "combat"



    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

        # Check for correct command
        if not self.args:
            self.caller.msg("|540Usage: strike <target>|n")
            return

        # Check for designated target
        target = self.caller.search(self.target)

        if not target:
            self.caller.msg("|540Usage: strike <target>|n")
            return

        # Error handling for
        if target == self.caller:
            self.caller.msg(f"|400{self.caller}, quit hitting yourself!|n")
            return

        # Error handling for non-character objects
        if target.db.body is None:
            self.caller.msg("|400You had better not try that.")
            return

        # Use parsed args in combat loop
        loop = CombatLoop(self.caller, target)
        loop.resolveCommand()


    def func(self):

        # Initialize strike logic with caller and target
        strike = Strike(self.caller, target)

        # Run logic for strike command
        if strike.caller.isTurn():
            strike.runLogic()
        else:
            strike.caller.msg("You need to wait until it is your turn before you are able to act.")
            return

        # Clean up
        # Set caller's combat_turn to 0. Can no longer use combat commands.
        loop.combatTurnOff(strike.caller)

        # Check for number of elements in the combat loop
        if loop.getLoopLength() > 1:
            # Get character at next index and set their combat_round to 1
            nextTurn = loop.gotoNext()
            loop.combatTurnOn(nextTurn)
            nextTurn.msg(f"{nextTurn.key}, it's now your turn. Please enter a combat command, or disengage from combat.")
        else:
            loop.removeFromLoop(self.caller)
            strike.caller.msg(f"Combat is over. You have been removed from the combat loop for {loop.current_room}.")
            # Change callers combat_turn to 1 so they can attack again.
            strike.combatTurnOn(strike.caller)
