# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper

class CmdMedicine(Command):
    key = "heal"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):
        "This actually does things"
        # Check for correct command
        if not self.args:
            self.caller.msg("|430Usage: heal <target>|n")
            return

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
        medicine = caller.db.medicine
        target_resilience = target.db.resilience
        target_total_bleed_points = target_resilience + 3

        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        if target:
            loop = CombatLoop(caller, target)
            loop.resolveCommand()
        else:
            return

        if caller.db.combat_turn:
            if h.canFight(caller) and medicine:
                # Return message to area and caller
                if not target_bleed_points:
                    self.caller.msg(f"|300{target.key}'s injuries are beyond your skill as a healer.|n")
                    return

                # Check to see if the target is already healed to max.
                elif target_body >= 1:
                    self.caller.msg(f"|025{target.key} doesn't require the application of your chiurgical skills. They seem to be healthy enough.|n")
                    return

                else:
                    """
                    Get max bleed points.
                    1. If target has max bleed points and 0 body, heal up to 1 body.
                    2. elif: target has under max bleed points, add caller medicine level in bleed points and excess to body, up to 1.
                    3. else target is out of bleed points, prompt that you can't heal target.
                    """
                    new_bp_value = target_total_bleed_points + target_resilience + medicine
                    if (target.db.bleed_points == target_total_bleed_points) and not target_body:
                        target_body += 1
                        caller.location.msg_contents(f"|025{caller.key} performs some minor healing techniques and provides aid to {target.key}.|n")

                    elif (target.db.bleed_points < target_total_bleed_points):
                        if new_bp_value > target_total_bleed_points:
                            # Set to max bleed_points
                            target_bleed_points = target_total_bleed_points
                            # Add extra to body
                            excess_bp = new_bp_value - target_total_bleed_points
                            if excess_bp + target_body > 1:
                                target_body = 1
                            else:
                                target_body += excess_bp
                        else:
                            target_bleed_points += medicine
                            caller.msg(f"|430You are slowly starting to heal, and your wounds are on the mend.")
                    else:
                        caller.msg(f"|300{target.key}'s injuries are beyond your skill as a healer.|n")
                        return

            else:
                caller.msg("|300You are too injured to act.|n")
                return

                # Clean up in combat loop
                loop.combatTurnOff(caller)
                loop.cleanup()
        else:
            caller.msg("|430You need to wait until it is your turn before you are able to act.|n")
            return
