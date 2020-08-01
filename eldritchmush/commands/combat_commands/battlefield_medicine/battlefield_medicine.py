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

        # Get target body and BM to validate target and caller has skill.
        target_body = target.db.body
        battlefieldmedicine = self.caller.db.battlefieldmedicine

        if target in target.location.db.combat_loop:
            """
            If target of skill is in combat, check to see if it's callers turn
            """


        else:
            if battlefieldmedicine and target_body is not None:

                if 1 <= target_body <= 3:
                    # Return message to area and caller
                    if target == self.caller:
                        # Check to see if caller would go over 1 body with application of skill.
                        if (self.caller.db.body + 1) > 3:
                            # If so set body to 1
                            self.caller.db.body = 3
                            self.caller.msg(f"|230{target.key} doesn't require the application of your chiurgical skills. They seem to be healthy enough.|n")
                        else:
                            # If not over 1, add points to total
                            self.caller.location.msg_contents(f"|230{self.caller} pulls bandages and ointments from their bag, and starts to mend their wounds.|n\n|540{self.caller} heals |n|0201|n |540body point per round as long as their work remains uninterrupted.|n")
                            self.caller.db.body += 1
                            self.caller.msg(f"|540Your new body value is:|n {self.caller.db.body}|n")

                    elif target != self.caller:
                        if (target.db.body + 1) > 3:
                            # If so set body to 1
                            target.db.body = 3
                            self.caller.msg(f"|230{target.key} doesn't require the application of your chiurgical skills. They seem to be healthy enough.|n")
                        else:
                            # If not over 1, add points to total
                            target.location.msg_contents(f"|230{self.caller.key} comes to {target.key}'s rescue, healing {target.key} for|n |0201|n |230body point.|n")
                            target.db.body += 1
                            target.msg(f"|540Your new body value is:|n {target.db.body}|n")

                elif target_body <= 0:
                    self.caller.location.msg_contents(f"|230{self.caller.key} comes to {target.key}'s rescue, though they are too fargone.\n{target.key} may require the aid of more advanced chiurgical techniques.|n")

            else:
                self.caller.msg("|400You had better not try that.|n")
