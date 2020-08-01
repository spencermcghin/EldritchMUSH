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

        # Go through combat loop logic
        loop = CombatLoop(caller, target)
        loop.resolveCommand()

        if caller.db.combat_turn:
            if h.canFight(caller):
                if battlefieldmedicine and target_body is not None:
                    # Use parsed args in combat loop. Handles turn order in combat.
                    # Resolve medic command
                    if 1 <= target.db.body <= 3:
                        # Return message to area and caller
                        if target == caller:
                            # Check to see if caller would go over 1 body with application of skill.
                            if (caller.db.body + 1) > 3:
                                # If so set body to 1
                                caller.db.body = 3
                                caller.msg(f"|230{target.key} doesn't require the application of your chiurgical skills. They seem to be healthy enough.|n")
                                return
                            else:
                                # If not over 1, add points to total
                                caller.location.msg_contents(f"|230{self.caller} pulls bandages and ointments from their bag, and starts to mend their wounds.|n\n|540{caller} heals |n|0201|n |540body points.|n")
                                caller.db.body += 1
                                caller.msg(f"|540Your new body value is:|n {caller.db.body}|n")
                                # Clean up
                                # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                                loop.combatTurnOff(caller)
                                loop.cleanup()

                        elif target != caller:
                            if (target.db.body + 1) > 3:
                                # If so set body to 1
                                target.db.body = 3
                                caller.msg(f"|230{target.key} doesn't require the application of your chiurgical skills. They seem to be healthy enough.|n")
                                return
                            else:
                                # If not over 1, add points to total
                                target.location.msg_contents(f"|230{caller.key} comes to {target.key}'s rescue, healing {target.key} for|n |0201|n |230body point.|n")
                                target.db.body += 1
                                target.msg(f"|540Your new body value is:|n {target.db.body}|n")
                                # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                                loop.combatTurnOff(self.caller)
                                loop.cleanup()

                    elif target.db.body <= 0:
                        caller.location.msg_contents(f"|230{caller.key} comes to {target.key}'s rescue, though they are too fargone.\n{target.key} may require the aid of more sophisticated healing techniques.|n")
                        return
                else:
                    caller.msg("|400You had better not try that.|n")
                    return
            else:
                caller.msg("You are too injured to act.")
                return
        else:
            caller.msg("You need to wait until it is your turn before you are able to act.")
            return
