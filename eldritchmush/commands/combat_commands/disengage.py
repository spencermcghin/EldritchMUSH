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
                self.caller.location.msg_contents(f"{self.combat_loop}")
                self.combat_loop.remove(self.caller)
                loop.cleanup()

                # # Check if combatant is at last index before disengaging and then passing turn
                # # Loop should never be less than 1 given cleanup step.
                # if len(self.combat_loop) > 1 and len(self.combat_loop) == self.caller_index + 1:
                #     # Get and hold next combatant value to move to next turn
                #     first_combatant_str = self.combat_loop[0]
                #     first_combatant_key = self.caller.search(first_combatant_str)
                #     first_combatant_key.db.combat_turn = 1
                #     # Remove caller from combat loop and set status
                #     self.combat_loop.remove(self.caller)
                #     self.caller.db.in_combat = 0
                #     # Set combat_turn back to 1
                #     self.caller.db.combat_turn = 1
                #     self.msg("You have disengaged from combat.")
                #     self.caller.location.msg_contents(f"{self.caller.key} breaks away from combat.")
                #
                #     # Prompt for next turn
                #     first_combatant_key.location.msg_contents(f"It is now {first_combatant_key}'s turn.")
                #
                #     # # Run disengage_cleanup
                #     # self.disengage_cleanup()
                #
                # # Accounts for caller being anywhere else in the loop, besides last
                # else:
                #     # Go to next player instead and set combat_turn to 1
                #     next_combatant_str = self.combat_loop[self.caller_index + 1]
                #     next_combatant_key = self.caller.search(next_combatant_str)
                #     next_combatant_key.db.combat_turn = 1
                #     # Remove caller from combat loop
                #     self.combat_loop.remove(self.caller)
                #     self.caller.db.in_combat = 0
                #     # Set combat_turn back to 1
                #     self.caller.db.combat_turn = 1
                #     self.msg("You have disengaged from combat.")
                #     self.caller.location.msg_contents(f"{self.caller.key} breaks away from combat.")
                #
                #     # Prompt for next turn
                #     next_combatant_key.location.msg_contents(f"It is now {next_combatant_key}'s turn.")

                    # # Run disengage_cleanup
                    # self.disengage_cleanup()

            else:
                self.msg(f"You are not part of the combat loop for {self.caller.location}.")

        else:
            self.caller.msg("You need to wait until it is your turn before you are able to act.")


    # def disengage_cleanup(self):
    #     if len(self.combat_loop) == 1:
    #         self.caller.location.msg_contents("if in disengage cleanup.")
    #         # Remove remaining combatants from combat loop and prompt
    #         # Messages
    #         remaining_key = self.caller.search(self.combat_loop[0])
    #         remaining_key.location.msg_contents(f"{remaining_key} breaks away from combat.")
    #         remaining_key.msg(f"Combat is over. You have been removed from the combat loop for {self.caller.location}")
    #         # Actions
    #         self.combat_loop.remove(remaining_key)
    #         remaining_key.db.combat_turn = 1
    #         remaining_key.db.in_combat = 0
    #
    #     else:
    #         if self.getLoopLength() > 1:
    #             # If no character at next index (current character is last),
    #             # go back to beginning of combat_loop and prompt character for input.
    #             nextCharacter = self.goToFirst() if self.isLast() else self.goToNext()
    #
    #             # Iterate through combat_loop until finding a character w/out the skip_turn flag set.
    #             while nextCharacter.db.skip_turn or self.isDying(nextCharacter):
    #                 # Turn off the skip_turn flag and then try to go to the next character in the loop
    #                 nextCharacter.db.skip_turn = False
    #                 nextCharacter.location.msg_contents(f"{nextCharacter.key} is unable to act this round.")
    #                 try:
    #                     # Try going to the next character based on the character that had skip_turn active
    #                     nextTurn = self.combat_loop.index(nextCharacter) + 1
    #                     nextCharacter = self.caller.search(self.combat_loop[nextTurn])
    #
    #                 except IndexError:
    #                     nextCharacter = self.caller.search(self.combat_loop[0])
    #
    #             self.combatTurnOn(nextCharacter)
    #             nextCharacter.location.msg_contents(f"It is now {nextCharacter.key}'s turn.")
    #
    #             ###### NPC Turn Resolver ######
    #             # Check to see if the character is an npc. If so run it's random command generator
    #             if utils.inherits_from(nextCharacter, Npc):
    #                 # Hook into the npcs command generator.
    #                 targets = [target for target in self.combat_loop if target.has_account]
    #                 # Pick a random target from the loops possible targets
    #                 if targets:
    #                     random_target = random.choice(targets)
    #                     # If character target, attack a random one.
    #                     nextCharacter.at_char_entered(random_target)
    #                 else:
    #                     # If no non-NPC targets, disengage
    #                     nextCharacter.execute_cmd("disengage")
    #
    #         else:
    #             self.removeFromLoop(self.caller)
    #             self.caller.db.in_combat = 0
    #             self.caller.location.msg_contents(f"Combat is now over for {loop.current_room}.")
    #             # Change self.callers combat_turn to 1 so they can attack again.
    #             self.combatTurnOn(self.caller)
