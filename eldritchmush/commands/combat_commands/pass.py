# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper
from evennia import utils
from typeclasses.npc import Npc

class CmdPass(Command):
    """
    Pass on your turn while in combat.

    Usage:
      pass

    """
    key = "pass"
    help_category = "combat"

    def parse(self):

        self.combat_loop = self.caller.location.db.combat_loop

    def func(self):
        # Check if it is player's combat_turn
        if self.caller.db.combat_turn:

            # Check to see if caller is in combat loop:
            if self.caller in self.combat_loop:
                self.caller.location.msg_contents(f"{self.caller.key} passes their turn.")
                # Instantiate combat loop class
                loop = CombatLoop(self.caller, target=None)
                loop.cleanup()

            else:
                self.msg(f"|300You are not part of the combat loop for {self.caller.location}.|n")

        else:
            self.caller.msg("|430You need to wait until it is your turn before you are able to act.|n")
