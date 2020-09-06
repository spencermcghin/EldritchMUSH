# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper

# imports
import time

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

        # Init combat helper functions
        h = Helper(self.caller)

        # Get target if there is one
        target = self.caller.search(self.target)
        caller = self.caller

        chirurgeon = caller.db.chirurgeon
        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        if target:
            target_in_combat = True if target.db.in_combat else False
            caller_in_combat = True if caller.db.in_combat else False
            if caller_in_combat or target_in_combat:
                self.msg("|430You can't perform this action while you or the target are in combat.|n")
                return
            else:
                pass
        else:
            self.msg("|430Please designate an appropriate target.|n")
            return

        # Check for cooldown
        now = time.time()
        if hasattr(self, "last_chirurgery") and now - self.last_chirurgery < (15 * 60):
            message = "|430You cannot use this ability yet.|n"
            self.caller.msg(message)
            return

        if h.canFight(caller):
            if chirurgeon:
                """
                Set death_points, bleed_points, body, and tough back to maximum.
                Set weakness attr to 0
                """
                # Set target stats
                target.db.body = 3
                target.db.bleed_points = 3 + target.db.resilience
                target.db.death_points = 3
                target.db.tough = target.db.total_tough
                target.db.weakness = 0

                # Set command time execution
                self.last_chirurgery = now

                self.msg(f"After some time and many delicate procedures, you skillfully heal {target.key}")
                target.msg(f"You have been restored to your full measure of health thanks to {caller.key}'s skillful application of the healing arts.")
            else:
                self.msg("|400You are not skilled enough.|n")
        else:
            caller.msg("|400You are too injured to act.|n")
            return
