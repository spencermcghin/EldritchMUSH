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
                # Get and hold next combatant value to move to next turn
                # TODO: Handle for player 
                next_combatant = combat_loop.index(self.caller.key) + 1
                next_comb_key = self.caller.search(combat_loop[next_combatant])
                # Remove from combat loop
                combat_loop.remove(self.caller.key)
                # Set combat_turn back to 1
                self.caller.db.combat_turn = 1
                # To disengage
                self.msg("|540You disengage from the attack.|n")
                self.caller.location.msg_contents(f"|015{self.caller} backs away and then disengages from the fight.|n")

                # Check to see if just one person left in loop. Remove if so and
                # set turn to 1
                if len(combat_loop) == 1:
                    combatant = combat_loop[0]
                    combat_loop.remove(combatant)
                    comb_key = self.caller.search(combatant)
                    comb_key.db.combat_turn = 1

                else:
                    # Go to the next combatant's turn
                    next_combatant.msg("Foo")


            else:
                self.msg(f"{self.caller.key}, you are not part of this location's combat loop.")

        else:

            self.msg("You need to wait until it is your turn before you are able to act.")
            return
