# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper

class CmdStabilize(Command):
    key = "stabilize"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):
        "This actually does things"
        # Check for correct command
        if not self.args:
            self.caller.msg("|540Usage: stabilize <target>|n")
            return

        target = self.caller.search(self.target)

        # Init combat helper functions
        h = Helper(self.caller)

        # Get target if there is one
        target = self.caller.search(self.target)
        caller = self.caller

        # Get caller level of stabilize and emote how many points the caller will heal target that round.
        # May not increase targets body past 1
        # Only works on targets with body <= 0
        target_body = target.db.body
        target_bleed_points = target.db.bleed_points
        target_death_points = target.db.death_points
        stabilize = self.caller.db.stabilize
        medicine = self.caller.db.medicine
        target_resilience = target.db.resilience

        # Go through combat loop logic
        loop = CombatLoop(caller, target)
        loop.resolveCommand()

        if caller.db.combat_turn:
            if h.canFight(caller):
                # Check to make sure caller has the skill.
                if medicine and target_body is not None:

                    if target_body and medicine:
                        # Return message to area and caller
                        if target == self.caller:
                            self.caller.location.msg_contents(f"|230{self.caller} pulls bandages and ointments from their bag, and starts to mend their wounds.|n")

                            # Check to see if caller would go over 1 body with application of skill.
                            if (self.caller.db.body + medicine) > 1:
                                # If so set body to 1
                                self.caller.db.body = 1
                                self.caller.msg(f"|540Your new body value is:|n {self.caller.db.body}|n")

                            else:
                                # If not over 1, add points to total
                                self.caller.db.body += medicine
                                self.caller.msg(f"|540Your new body value is:|n {self.caller.db.body}|n")

                            # Clean up in combat loop
                            loop.combatTurnOff(caller)
                            loop.cleanup()

                        # If target is someone else, do checks and apply healing.
                        elif target != self.caller and medicine:
                            target.location.msg_contents(f"|230{self.caller} pulls bandages and ointments from their bag, and starts to mend {target.key}'s wounds.|n")
                            if (target.db.body + medicine) > 1:
                                # If so set body to 1
                                target.db.body = 1
                                target.msg(f"|540Your new body value is:|n {target.db.body}|n")
                            else:
                                # If not over 1, add points to total
                                target.db.body += medicine
                                target.msg(f"|540Your new body value is:|n {target.db.body}|n")

                            # Clean up in combat loop
                            loop.combatTurnOff(caller)
                            loop.cleanup()

                elif target_bleed_points and medicine:
                        # Return message to area and caller
                        if target == self.caller:
                            self.caller.location.msg_contents(f"|230{self.caller} pulls bandages and ointments from their bag, and starts to mend their wounds.|n")

                            total_bleed_points = target_resilience + 3
                            new_bp_value = target_bleed_points + target_resilience + medicine
                            # Check to see if caller would go over 1 body with application of skill.
                            if new_bp_value > total_bleed_points:
                                # Set to max bleed_points
                                self.caller.db.bleed_points = total_bleed_points
                                # Add extra to body
                                excess_bp = new_bp_value - total_bleed_points
                                target_body += excess_bp
                                self.caller.msg(f"|540You are slowly starting to heal, and your wounds are on the mend.")

                            else:
                                # If not over 1, add points to total
                                target_bleed_points += medicine
                                self.caller.msg(f"|540You are slowly starting to heal, though it will take more time.")

                            # Clean up in combat loop
                            loop.combatTurnOff(caller)
                            loop.cleanup()


                        # If target is someone else, do checks and apply healing.
                        elif target != self.caller and medicine:
                            target.location.msg_contents(f"|230{self.caller} pulls bandages and ointments from their bag, and starts to mend {target.key}'s wounds.|n")
                            if (target.db.body + medicine) > 1:
                                # If so set body to 1
                                target.db.body = 1
                                target.msg(f"|540Your new body value is:|n {target.db.body}|n")
                            else:
                                # If not over 1, add points to total
                                target.db.body += medicine
                                target.msg(f"|540Your new body value is:|n {target.db.body}|n")

                            # Clean up in combat loop
                            loop.combatTurnOff(caller)
                            loop.cleanup()


                # Apply stabilize to other target
                elif target_death_points and stabilize:

                        # You can't stabilize yourself...
                        if target == self.caller:
                            self.caller.msg(f"|400{self.caller} You are too fargone to attempt this action.|n")
                        elif target != self.caller:
                            target.location.msg_contents(f"|230{self.caller.key} comes to {target.key}'s rescue, healing {target.key}.|n")

                            new_dp_total = target_death_points + stabilize
                            if new_dp_total > 3:
                                target_death_points = 3
                                # Add any excess to bleed_points
                                excess_dp = new_dp_total - 3
                                target_bleed_points += excess_dp
                            else:
                                target_death_points += stabilize

                            # Check to see if weakness set. If not, set it.
                            if not target.db.weakness:
                                target.db.weakness = 1

                            # Clean up in combat loop
                            loop.combatTurnOff(caller)
                            loop.cleanup()

                # Check to see if the target is already healed to max.
                elif target_body >= 1:
                    self.caller.msg(f"|230{target.key} doesn't require the application of your chiurgical skills. They seem to be healthy enough.|n")

                else:
                    self.caller.msg("|400You had better not try that.|n")
            else:
                caller.msg("You are too injured to act.")
                return
        else:
            caller.msg("You need to wait until it is your turn before you are able to act.")
            return
