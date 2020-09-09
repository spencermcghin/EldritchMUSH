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

        if not h.canFight(self.caller):
            caller.msg("|400You are too injured to act.|n")
            return

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
            if (caller in caller.location.db.combat_loop) or (target in caller.location.db.combat_loop):
                loop = CombatLoop(caller, target)
                loop.resolveCommand()
            else:
                pass
        else:
            self.msg("|430Please designate an appropriate target.|n")

        if caller.db.combat_turn:
            if medicine:
                # Check to see if the target is already healed to max.
                if target_body >= 1:
                    self.caller.msg(f"|025You can help {target.key} no more.|n")
                    return

                else:
                    """
                    Get max bleed points.
                    1. If target has max bleed points and 0 body, heal up to 1 body.
                    2. elif: target has under max bleed points, add caller medicine level in bleed points and excess to body, up to 1.
                    3. else target is out of bleed points, prompt that you can't heal target.
                    """
                    new_bp_value = target_total_bleed_points + target_resilience + medicine
                    if (target.db.bleed_points == target_total_bleed_points) and target_body == 0:
                        target.db.body += 1
                        caller.location.msg_contents(f"|025{caller.key} performs some minor healing techniques and provides|n (|4301|n) |025points of aid to {target.key}.|n")

                    elif (target.db.bleed_points < target_total_bleed_points) and target.db.bleed_points > 0:
                        if new_bp_value > target_total_bleed_points:
                            # Set to max bleed_points
                            target.db.bleed_points = target_total_bleed_points
                            # Add extra to body
                            excess_bp = new_bp_value - target_total_bleed_points
                            if excess_bp + target_body > 1:
                                # current body = 0
                                # bleed points = 2
                                # heal for 3
                                target.db.body = 1
                                caller.location.msg_contents(f"|025{caller.key} performs some minor healing techniques and provides|n (|430{medicine}|n) |025points of aid to {target.key} (up to 1 body).|n")
                            else:
                                target.db.body += excess_bp
                        else:
                            target.db.bleed_points += medicine
                    else:
                        caller.msg(f"|400{target.key}'s injuries are beyond your skill as a healer.|n")
                        return
            else:
                self.msg("|400You are not skilled enough.|n")

            # Clean up in combat loop
            if (caller in caller.location.db.combat_loop) or (target in caller.location.db.combat_loop):
                loop.combatTurnOff(caller)
                loop.cleanup()
            else:
                return
        else:
            caller.msg("|430You need to wait until it is your turn before you are able to act.|n")
            return
