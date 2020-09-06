# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper
from evennia import utils
from typeclasses.npc import Npc

class CmdSkip(Command):
    """
    Pass on your turn while in combat.

    Usage:
      skip

    """
    key = "skip"
    help_category = "combat"

    def __init__(self):
        self.combat_loop = None

    def parse(self):

        self.combat_loop = self.caller.location.db.combat_loop

    def func(self):
        combatant = self.caller

        # Check if it is player's combat_turn
        if combatant.db.combat_turn:

            # Check to see if caller is in combat loop:
            if combatant in self.combat_loop:
                combatant.location.msg_contents(f"|025{self.caller.key} passes on their turn.|n")
                # Instantiate combat loop class
                loop = CombatLoop(self.caller, target=None)
                loop.cleanup()

            else:
                self.msg(f"|400You are not part of the combat loop for {self.caller.location}.|n")

        else:
            combatant.msg("|430You need to wait until it is your turn before you are able to act.|n")
