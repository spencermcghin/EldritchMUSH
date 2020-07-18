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
    """
    key = "disengage"
    aliases = ["disengage", "escape", "flee"]
    help_category = "combat"

    def func(self):
        "Implements the command"
        combat_loop = self.caller.location.db.combat_loop

        # Check if it is player's combat_turn
        if self.caller.db.combat_turn:

            # Check to see if they are in the combat loop for their current room
            if self.caller.key in combat_loop:
                # Remove from combat loop
                combat_loop.remove(self.caller.key)
                # Set combat_turn back to 1
                self.caller.db.combat_turn = 1
                # To disengage
                self.msg("|540You disengage from the attack.|n")
                self.caller.location.msg_contents(f"|015{self.caller} backs away and then disengages from the fight.|n")

            else:
                self.msg(f"{self.caller.key}, you are not part of this location's combat loop.")

        else:

            self.msg("You need to wait until it is your turn before you are able to act.")
            return
