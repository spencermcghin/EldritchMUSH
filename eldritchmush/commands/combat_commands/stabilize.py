# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combatant import Combatant

class CmdStabilize(Command):
    key = "stabilize"
    help_category = "mush"

    def __init__(self):
        self.target = None

    def parse(self):
        self.target = self.args.strip()

    def func(self):
        combatant = Combatant(self.caller)

        # Check for correct command
        if not self.args:
            self.caller.msg("|430Usage: stabilize <target>|n")
            return

        if combatant.cantFight():
            combatant.message("|400You are too injured to act.|n")
            return

        # Get target if there is one
        target = self.caller.search(self.target)
        victim = Combatant(target)

        # Get caller level of stabilize and emote how many points the caller will heal target that round.
        # May not increase targets body past 1
        # Only works on targets with body <= 0
        #target_body = victim.body
        #target_bleed_points = victim.bleed_points
        #target_death_points = victim.death_points
        #stabilize = caller.db.stabilize
        #medicine = caller.db.medicine
        #target_resilience = victim.resilience
        #target_total_bleed_points = target_resilience + 3
        #new_bp_value = target_total_bleed_points + target_resilience + medicine

        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        #TODO: This code is repeated.  FIND ME A REFACTOR!
        if target:
            if (combatant.caller in combatant.caller.location.db.combat_loop) or (
                    target in combatant.caller.location.db.combat_loop):
                loop = CombatLoop(combatant.caller, target)
                loop.resolveCommand()
        else:
            self.msg("|430Please designate an appropriate target.|n")
            return

        #TODO: Spence Review - This originally used medicine AND stabilize but I changed it to just use stabilize.  Is that wrong?
        if combatant.hasTurn(f"|430You need to wait until it is your turn before you are able to act.|n"):
            if combatant.hasStabilize(f"|400You are not skilled enough.|n"):
                # Check to see if the target is already healed to max.
                if victim.body() >= 1:
                    combatant.message(f"|025You can help {victim.name} no more.|n")
                    return

                    """
                    Get max bleed points.
                    1. If target has max bleed points and 0 body, heal up to 1 body.
                    2. elif: target has under max bleed points, add caller medicine level in bleed points and excess to body, up to 1.
                    3. else target is out of bleed points, prompt that you can't heal target.
                    """
                elif victim.atMaxBleedPoints() and victim.body() == 0:
                        victim.addBody(1)
                        victim.broadcast(f"|025{combatant.name} performs some minor healing techniques and provides|n (|4301|n) |025points of aid to {victim.name}.|n")
                elif victim.isAtMaxDeathPoints() and not victim.atMaxBleedPoints():
                    combatant.message(f"|025{combatant.name} performs some minor healing techniques and provides|n (|430{combatant.medicine()}|n) |025points of aid to {victim.name}.|n")
                    if combatant.stabilize() > victim.missingBleedPoints():
                        victim.setBody(1)
                        victim.resetBleedPoints()
                    else:
                        victim.addBleedPoints(combatant.medicine())
                elif victim.hasDeathPoints(1) or victim.hasDeathPoints(2):
                    combatant.message(f"|025{combatant.name} performs advanced healing techniques and provides|n (|430{combatant.stabilize()}|n) |025 points of aid to {victim.name}.|n")
                    if combatant.stabilize() > victim.missingDeathPoints():
                        remaining_healing = combatant.stabilize() - victim.missingDeathPoints()
                        victim.setDeathPoints(3)
                        victim.addBleedPoints(remaining_healing)
                    else:
                        victim.addDeathPoints(combatant.stabilize())
                else:
                    combatant.message(f"{victim.name} |025is too fargone to administer further healing.|n")

                if (combatant.caller in combatant.caller.location.db.combat_loop) or (
                        target in combatant.caller.location.db.combat_loop):
                    loop.combatTurnOff(caller)
                    loop.cleanup()