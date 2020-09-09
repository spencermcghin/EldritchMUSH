# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper

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
            self.caller.msg("|430Usage: medic <target>|n")
            return

        # Init combat helper functions
        h = Helper(self.caller)

        if not h.canFight(self.caller):
            caller.msg("|400You are too injured to act.|n")
            return

        # Get target if there is one
        target = self.caller.search(self.target)
        caller = self.caller

        # Get target body and BM to validate target and caller has skill.
        target_body = target.db.body
        battlefield_medicine = caller.db.battlefieldmedicine

        # Go through combat loop logic
        if target:
            if (caller in caller.location.db.combat_loop) or (target in caller.location.db.combat_loop):
                loop = CombatLoop(caller, target)
                loop.resolveCommand()
            else:
                pass
        else:
            self.msg("|430Please designate an appropriate target.|n")

        if caller.db.combat_turn:
            if battlefield_medicine and target_body is not None:
                # Use parsed args in combat loop. Handles turn order in combat.
                # Resolve medic command
                if target.db.body == 3:
                    self.msg(f"{target.key} does not require the application of your healing skills.")
                elif 1 <= target.db.body < 3:
                    # If not over 1, add points to total
                    target.location.msg_contents(f"|025{caller.key} comes to {target.key}'s rescue, healing {target.key} for|n (|4301|n) |025body point.|n")
                    target.db.body += 1
                    target.msg(f"|540Your new body value is:|n {target.db.body}|n")
                    # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                    if (caller in caller.location.db.combat_loop) or (target in caller.location.db.combat_loop):
                        loop.combatTurnOff(caller)
                        loop.cleanup()
                    else:
                        return
                elif target.db.body <= 0:
                    caller.location.msg_contents(f"|025{caller.key} comes to {target.key}'s rescue, though they are too fargone.\n{target.key} may require the aid of more sophisticated healing techniques.|n")
                    return
            else:
                caller.msg("|400You had better not try that.|n")
                return
        else:
            caller.msg("|430You need to wait until it is your turn before you are able to act.|n")
            return
