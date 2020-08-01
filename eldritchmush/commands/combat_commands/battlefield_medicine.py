# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper
from battlefield_medicine.battlefield_med_handler import HealingHandler


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

        if target.key in target.location.db.combat_loop:
            """
            If target of skill is in combat, use loop to resolve command and insert caller into loop.
            Will need to wait until it is callers turn to act.

            """
            caller.msg(f"You try to heal {target.key}, but they are currently engaged in combat.")
            loop = CombatLoop(caller, target)
            loop.resolveCommand()

            # Apply healing skills accordingly
            healing_handler = HealingHandler(caller, target)
            healing_handler.resolve_healing()

        else:
            if battlefieldmedicine and target_body is not None:

                # Apply healing skills accordingly
                healing_handler = HealingHandler(caller, target)
                healing_handler.resolve_healing()

            else:
                self.caller.msg("|400You had better not try that.|n")
