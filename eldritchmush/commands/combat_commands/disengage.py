# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper
from evennia import utils
from typeclasses.npc import Npc

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
                self.caller.location.msg_contents(f"|025{self.caller.key} breaks away from combat.|n")
                # Instantiate combat loop class
                loop = CombatLoop(self.caller, target=None)
                # Run cleanup to move to next target
                self.combat_loop.remove(self.caller)
                # Reset stats
                self.caller.db.in_combat = 0
                self.caller.db.combat_turn = 1

                # Check for only npcs remaining.
                loop_contents = [char for char in self.combat_loop if utils.inherits_from(char, Npc)]
                if len(loop_contents) == len(self.caller.location.db.combat_loop):
                    # Reset combat stats
                    for char in self.combat_loop:
                        char.db.combat_turn = 1
                        char.db.in_combat = 0
                    self.combat_loop.clear()
                    self.caller.location.msg_contents("|025Combat is now over.|n")
                    return
                else:
                    loop.cleanup()

            else:
                self.msg(f"|400You are not part of the combat loop for {self.caller.location}.|n")

        else:
            self.caller.msg("|430You need to wait until it is your turn before you are able to act.|n")
