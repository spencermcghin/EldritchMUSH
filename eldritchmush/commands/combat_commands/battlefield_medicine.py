# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper
from commands.combat_commands.battlefield_med_handler import HealingHandler


class CmdBattlefieldMedicine(Command):
    key = "medic"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):
        "This actually does things"
        # Check for correct command
        if not self.args:
            self.caller.msg("|540Usage: medic <target>|n")
            return

        # Init combat helper functions
        h = Helper(self.caller)

        # Get target if there is one
        target = self.caller.search(self.target)
        caller = self.caller

        # Get target body and BM to validate target and caller has skill.
        target_body = target.db.body
        battlefieldmedicine = caller.db.battlefieldmedicine

        if caller.db.combat_turn:
            if battlefieldmedicine and target_body is not None:

                # Use parsed args in combat loop. Handles turn order in combat.
                loop = CombatLoop(self.caller, target)
                loop.resolveCommand()

                # Resolve medic command
                handler = HealingHandler()
                handler.resolve_healing()

            else:
                self.caller.msg("|400You had better not try that.|n")

        else:
            self.msg("You need to wait until it is your turn before you are able to act.")
            return
