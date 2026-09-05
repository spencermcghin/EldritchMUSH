# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper
from evennia import utils
from typeclasses.npc import Npc
from world.events import emit
from world.available_commands import push_available_commands

class CmdDisengage(Command):
    """
    Exit combat and remove yourself from the turn order.

    Usage:
      disengage

    Aliases: escape, flee, retreat

    Safely withdraws you from the current combat loop.  You can disengage
    even while bleeding — it is the only combat action available in that
    state.  Once disengaged you can move, seek healing, or re-engage later.

    Does NOT consume your combat turn (the loop advances normally after).

    See also: drag, medicine, chirurgery
    """
    key = "disengage"
    aliases = ["disengage", "escape", "flee", "retreat"]
    help_category = "Combat"

    def parse(self):
        self.combat_loop = self.caller.location.db.combat_loop

    def func(self):
        # Check if it is player's combat_turn
        if self.caller.db.combat_turn:

            # Check to see if caller is in combat loop:
            if self.caller in self.combat_loop:
                self.caller.location.msg_contents(f"{self.caller.key} |025breaks away from combat.|n")
                emit(self.caller.location, "combat_disengage", {"character": self.caller.key})
                # Note our slot BEFORE leaving, so the turn can be handed
                # on from the combatant ahead of us (same approach as drag).
                # Running cleanup() as a caller who is no longer in the loop
                # used to raise ValueError out of CombatLoop.isLast(),
                # freezing the fight for everyone still in it.
                my_index = self.combat_loop.index(self.caller)
                # Run cleanup to move to next target
                self.combat_loop.remove(self.caller)
                # Reset stats
                self.caller.db.in_combat = 0
                self.caller.db.combat_turn = 1
                push_available_commands(self.caller)

                # Check for only npcs remaining.
                loop_contents = [char for char in self.combat_loop if utils.inherits_from(char, Npc)]
                if len(loop_contents) == len(self.caller.location.db.combat_loop):
                    # Reset combat stats
                    for char in self.combat_loop:
                        char.db.combat_turn = 1
                        char.db.in_combat = 0
                    self.combat_loop.clear()
                    self.caller.location.msg_contents("|025Combat is now over.|n")
                    emit(self.caller.location, "combat_end", {"reason": "all_disengaged"})
                    return
                else:
                    # Hand the turn on from the slot before the one we
                    # vacated, so cleanup() runs as a caller still in the
                    # loop and the round order is preserved.
                    prev_char = self.combat_loop[(my_index - 1) % len(self.combat_loop)]
                    CombatLoop(prev_char).cleanup()

            else:
                self.msg(f"|400You are not part of the combat loop for {self.caller.location}.|n")

        else:
            self.caller.msg("|430You need to wait until it is your turn before you are able to act.|n")
