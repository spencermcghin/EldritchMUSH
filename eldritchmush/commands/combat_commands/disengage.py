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

    def parse(self):

        self.combat_loop = self.caller.location.db.combat_loop
        self.caller_index = self.combat_loop.index(self.caller.key)

    def func(self):
        # Check if it is player's combat_turn
        if self.caller.db.combat_turn:
            # Check to see if caller is in combat loop:
            if self.caller.key in self.combat_loop:

                # Check if combatant is at last index before disengaging and then passing turn
                # Loop should never be less than 1 given cleanup step.
                if len(self.combat_loop) > 1 and len(self.combat_loop) == self.caller_index + 1:
                    # Get and hold next combatant value to move to next turn
                    first_combatant_str = self.combat_loop[0]
                    first_combatant_key = self.caller.search(first_combatant_str)
                    first_combatant_key.db.combat_turn = 1
                    # Remove caller from combat loop
                    self.combat_loop.remove(self.caller.key)
                    # Set combat_turn back to 1
                    self.caller.db.combat_turn = 1
                    self.msg("You have disengaged from combat.")
                    self.caller.location.msg_contents(f"{self.caller.key} breaks away from combat.")

                    # Run disengage_cleanup
                    self.disengage_cleanup()

                else:
                    # Go to next player instead and set combat_turn to 1
                    next_combatant_str = self.caller_index + 1
                    next_combatant_key = self.caller.search(next_combatant_str)
                    next_combatant_key.db.combat_turn = 1
                    # Remove caller from combat loop
                    self.combat_loop.remove(self.caller.key)
                    # Set combat_turn back to 1
                    self.caller.db.combat_turn = 1
                    first_combatant_key.msg("You have disengaged from combat.")
                    self.caller.location.msg_contents(f"{first_combatant_key} breaks away from combat.")

                    # Run disengage_cleanup
                    self.disengage_cleanup()

            else:
                self.msg(f"You are not part of the combat loop for {self.caller.location}.")
        else:
            self.caller.msg("You need to wait until it is your turn before you are able to act.")


    def disengage_cleanup(self):
        if len(combat_loop) == 1:
            # Remove remaining combatants from combat loop and prompt
            remaining_str = self.combat_loop.pop()
            remaining_key = self.caller.search(remaining_str)
            remaining_key.msg(f"Combat is over. You have been removed from the combat loop for {self.caller.location}")
            remaining_key.db.combat_turn = 1

        else:
            return
