# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper

class CmdDisengage(Command):
    """
    disengage from an enemy

    Usage:
      disengage

    Disengages from a fight.

    Logic:
    1. Get next player turn in loop.
    2.


    """
    key = "disengage"
    aliases = ["disengage", "escape", "flee"]
    help_category = "combat"

    def parse(self):

        self.combat_loop = self.caller.location.db.combat_loop
        self.caller_index = self.combat_loop.index(self.caller)

    def func(self):
        # Check if it is player's combat_turn
        if self.caller.db.combat_turn:

            # Check to see if caller is in combat loop:
            if self.caller in self.combat_loop:
                self.caller.location.msg_contents(f"{self.caller.key} breaks away from combat.")
                # Instantiate combat loop class
                loop = CombatLoop(self.caller, target=None)
                # Run cleanup to move to next target
                self.caller.location.msg_contents(f"{self.caller.key} removed.")
                self.combat_loop.remove(self.caller)
                self.caller.location.msg_contents(f"{self.combat_loop}")
                loop.cleanup()

            else:
                self.msg(f"You are not part of the combat loop for {self.caller.location}.")

        else:
            self.caller.msg("You need to wait until it is your turn before you are able to act.")
