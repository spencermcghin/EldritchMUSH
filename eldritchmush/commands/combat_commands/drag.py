# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper


class Drag(Command):

    """
    Drags immobile target out of combat or initiates a follow.
    If both of target's legs are injured, they will need to be healed or drug from combat.
    If player is between 4 - 6 body, they will need to be drug from combat.
    If caller and target are in a combat loop, they will have to disengage from combat at the same time.
    If caller is in loop but target is not, caller will need to exit the loop and then execute the command.
    If caller is not in loop but target is, target will be removed from loop.
    If caller and target are not in combat, command issues a follow.
    """

    key = "drag"
    help_category = "combat"
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
