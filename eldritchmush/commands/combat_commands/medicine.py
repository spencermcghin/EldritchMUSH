# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Combatant


class CmdMedicine(Command):
    key = "heal"
    help_category = "mush"

    def __init__(self):
        self.target = None

    def parse(self):
        self.target = self.args.strip()

    def func(self):
        # Check for correct command
        if not self.args:
            self.caller.msg("|430Usage: heal <target>|n")
            return

        combatant = Combatant(self.caller)


        if combatant.cantFight():
            combatant.message("|400You are too injured to act.|n")
            return

        # Get target if there is one
        target = self.caller.search(self.target)
        victim = Combatant(target)

        # Get caller level of stabilize and emote how many points the caller will heal target that round.
        # May not increase targets body past 1
        # Only works on targets with body <= 0
        #target_body = target.db.body
        #target_bleed_points = target.db.bleed_points
        #target_death_points = target.db.death_points
        #medicine = caller.db.medicine
        #target_resilience = target.db.resilience
        #target_total_bleed_points = target_resilience + 3

        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        if target:
            if (combatant.caller in combatant.caller.location.db.combat_loop) or (target in combatant.caller.location.db.combat_loop):
                loop = CombatLoop(combatant.caller, target)
                loop.resolveCommand()
            else:
                pass
        else:
            self.msg("|430Please designate an appropriate target.|n")

        if combatant.hasTurn():
            if combatant.medicine():
                # Check to see if the target is already healed to max.
                if victim.hasMoreBodyThan(0):
                    combatant.message(f"|025You can help {victim.name()} no more.|n")
                    return

                else:
                    """
                    Get max bleed points.
                    1. If target has max bleed points and 0 body, heal up to 1 body.
                    2. elif: target has under max bleed points, add caller medicine level in bleed points and excess to body, up to 1.
                    3. else target is out of bleed points, prompt that you can't heal target.
                    """
                    new_bp_value = victim.totalBleedPoints() + victim.resilience() + combatant.medicine()

                    if victim.atMaxBleedPoints() and victim.body() == 0:
                        victim.addBody(1)
                        combatant.broadcast(f"|025{combatant.name()} performs some minor healing techniques and provides|n (|4301|n) |025points of aid to {victim.name()}.|n")
                    elif victim.hasBleedPoints() and (victim.bleedPoints() < victim.totalBleedPoints()):
                        if new_bp_value > victim.totalBleedPoints():
                            # Set to max bleed_points
                            victim.setBleedPoints(victim.totalBleedPoints())

                            #This section feels like it could/should be refactored and might be missing an output?
                            # Add extra to body
                            excess_bp = new_bp_value - victim.totalBleedPoints()
                            if excess_bp + victim.body() > 1:
                                # current body = 0
                                # bleed points = 2
                                # heal for 3
                                victim.setBody(1)
                                combatant.broadcast(f"|025{combatant.name()} performs some minor healing techniques and provides|n (|430{combatant.medicine()}|n) |025points of aid to {victim.name()} (up to 1 body).|n")
                            else:
                                combatant.debugMessage(f"|400Unimplemented Message 1|n")
                                victim.addBody(excess_bp)
                        else:
                            combatant.debugMessage(f"|400Unimplemented Message 2|n")
                            victim.addBleedPoints(combatant.medicine())
                    else:
                        combatant.message(f"|400{target.key}'s injuries are beyond your skill as a healer.|n")
                        return
            else:
                combatant.message("|400You are not skilled enough.|n")

            # Clean up in combat loop
            #TODO: Probably can move to a helper function!
            if (combatant.caller in combatant.caller.location.db.combat_loop) or (target in combatant.caller.location.db.combat_loop):
                loop.combatTurnOff(combatant.caller)
                loop.cleanup()
            else:
                return
        else:
            combatant.message("|430You need to wait until it is your turn before you are able to act.|n")
            return
