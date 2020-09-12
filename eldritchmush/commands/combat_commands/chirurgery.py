# Local imports
from evennia import Command
from commands.combatant import Combatant

# imports
import time
import math

class CmdChirurgery(Command):
    key = "restore"
    help_category = "mush"

    def __init__(self):
        self.target = None

    def parse(self):
        self.target = self.args.strip()

    def func(self):
        # Check for correct command
        if not self.args:
            self.caller.msg("|430Usage: restore <target>\nThis command has a 15 minute cooldown.|n")
            return

        combatant = Combatant(self.caller)

        if combatant.cantFight():
            combatant.message("|400You are too injured to act.|n")
            return

        # Get target if there is one
        target = self.caller.search(self.target)
        victim = Combatant(target)

        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        if target:
            if victim.inCombat() or combatant.inCombat():
                combatant.message("|430You can't perform this action while you or the target are in combat.|n")
                return
        else:
            combatant.message("|430Please designate an appropriate target.|n")
            return

        # Check for cooldown
        now = time.time()

        seconds_left = combatant.secondsUntilNextChirurgery(time.time())
        if combatant.chirurgeon() and seconds_left > 0:
            combatant.message(f"|430You cannot use this ability for another {math.floor(seconds_left/60)} minutes and {seconds_left % 60} seconds.|n")
            return
        elif combatant.chirurgeon():
            """
            Set death_points, bleed_points, body, and tough back to maximum.
            Set weakness attr to 0
            """
            # Set target stats
            victim.setBody(3)
            victim.setDeathPoints(3)
            victim.removeWeakness()
            victim.resetTough()
            victim.resetBleedPoints()

            # Set command time execution
            combatant.setChirurgeryTimer(now)

            combatant.message(f"After some time and many delicate procedures, you skillfully heal {victim.name}")
            victim.message(f"You have been restored to your full measure of health thanks to {target.name}'s skillful application of the healing arts.")
        else:
            self.msg("|400You are not skilled enough.|n")

