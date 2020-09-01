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
            self.caller.msg("|430Usage: stabilize <target>|n")
            return

        # Init combat helper functions
        h = Helper(self.caller)

        # Check for and error handle designated target
        target = self.caller.search(self.target)

        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
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
        target_total_bleed_points = target_resilience + 3
        new_bp_value = target_total_bleed_points + target_resilience + medicine


        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        if target:
            if (caller in caller.location.db.combat_loop) or (target in caller.location.db.combat_loop):
                loop = CombatLoop(caller, target)
                loop.resolveCommand()
            else:
                pass
        else:
            self.msg("|430Please designate an appropriate target.|n")

        if caller.db.combat_turn:
            if h.canFight(caller):
                if stabilize:
                    # Check to see if the target is already healed to max.
                    if target_body >= 1:
                        self.caller.msg(f"|025You can help {target.key} no more.|n")
                        return

                        """
                        Get max bleed points.
                        1. If target has max bleed points and 0 body, heal up to 1 body.
                        2. elif: target has under max bleed points, add caller medicine level in bleed points and excess to body, up to 1.
                        3. else target is out of bleed points, prompt that you can't heal target.
                        """
                    elif (target.db.bleed_points == target_total_bleed_points) and target_body == 0:
                            target.db.body += 1
                            caller.location.msg_contents(f"|025{caller.key} performs some minor healing techniques and provides|n (|4301|n) |025points of aid to {target.key}.|n")

                    elif (target.db.bleed_points < target_total_bleed_points) and target.db.death_points >= 3:
                        caller.location.msg_contents(f"|025{caller.key} performs some minor healing techniques and provides|n (|430{medicine}|n) |025points of aid to {target.key} (up to 1 body).|n")
                        if new_bp_value > target_total_bleed_points:
                            # Set to max bleed_points
                            target.db.bleed_points = target_total_bleed_points
                            # Add extra to body
                            excess_bp = new_bp_value - target_total_bleed_points
                            if excess_bp + target_body > 1:
                                target.db.body = 1
                            else:
                                target.db.body += excess_bp
                        else:
                            target.db.bleed_points += medicine

                    elif target_death_points == 3 and target_bleed_points == 0:
                        caller.location.msg_contents(f"|025{caller.key} performs advanced healing techniques and provides|n (|430{stabilize}|n) |025points of aid to {target.key}.|n")
                        target.db.bleed_points += stabilize

                    elif (1 <= target_death_points <= 3):
                        caller.location.msg_contents(f"|025{caller.key} performs advanced healing techniques and provides|n (|430{stabilize}|n) |025 points of aid to {target.key}.|n")
                        new_dp_value = target_death_points + stabilize
                        if new_dp_value > 3:
                            # Set to max death_points
                            target.db.death_points = 3
                            # Add extra to bleed_points
                            excess_dp = new_dp_value - 3
                            target.db.bleed_points += excess_dp
                        else:
                            target.db.death_points += stabilize

                    else:
                        self.msg(f"{target.key} |025is too fargone to administer further healing.|n")
                else:
                    self.msg("|400You are not skilled enough.|n")
            else:
                caller.msg("|400You are too injured to act.|n")
                return

            if (caller in caller.location.db.combat_loop) or (target in caller.location.db.combat_loop):
                loop.combatTurnOff(caller)
                loop.cleanup()
            else:
                return
        else:
            caller.msg("|430You need to wait until it is your turn before you are able to act.|n")
            return
