# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper


class Drag(Command):

    """
    Drag an incapacitated ally or corpse to safety.

    Usage:
      drag <target>

    Moves a dying or immobile character out of the combat area.  The target
    must be unable to move on their own (both legs injured, dying, or body ≤ 0).

    - If both you and the target are in combat, you must both disengage first.
    - If only you are in combat, disengage then drag.
    - If neither is in combat, drag initiates a temporary follow.

    Requires: target must be incapacitated (cannot drag a conscious fighter).
    Does not consume a combat turn by itself.

    See also: disengage, medicine, restore
    """

    key = "drag"
    help_category = "Combat"
    def __init__(self):
        self.target = None

    def parse(self):
        self.target = self.args.strip()


    def func(self):
        # Init combat helper class for logic
        h = Helper(self.caller)

        # Check for correct command
        if not self.args:
            self.msg("|540Usage: drag <target>|n")
            return

        # Check for and error handle designated target
        target = h.targetHandler(self.target)

        pass
