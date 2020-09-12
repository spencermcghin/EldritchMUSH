# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combatant import Combatant


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

        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        if target:
            if (combatant.caller in combatant.caller.location.db.combat_loop) or (target in combatant.caller.location.db.combat_loop):
                loop = CombatLoop(combatant.caller, target)
                loop.resolveCommand()
        else:
            self.msg("|430Please designate an appropriate target.|n")
            return

        if combatant.hasTurn():
            # Anything from this level on, consumes the users turn.  Learn to Diagnose!
            if combatant.hasChirurgeonsKit():
                if not victim.hasBody(3):
                    if victim.hasMoreBodyThan(0):
                        if combatant.battlefieldMedicine():
                            # Victim is at 1 or 2 body, apply Battlefield_Medicine
                            victim.addBody(1)
                            combatant.useChirurgeonsKit()

                            victim.broadcast(
                                f"|025{combatant.name} comes to {victim.name}'s rescue, healing {victim.name} for|n (|4301|n) |025body point.|n")
                            victim.message(f"|540Your new body value is:|n {victim.body()}|n")
                        else:
                            victim.broadcast(
                                f"|025{combatant.name} tries to aid {victim.name} but they are not skilled enough to benefit them further.|n")
                            combatant.message(f"|025You can help {victim.name} no more.|n");
                    elif victim.atMaxBleedPoints() and victim.body() == 0:
                        # Check which skills get applied at 0 bleed and body
                        if combatant.battlefieldMedicine() or combatant.stabilize() or combatant.medicine():
                            victim.broadcast(f"|025{combatant.name} performs some minor healing techniques and provides|n (|4301|n) |025points of aid to {victim.name}.|n")
                            victim.addBody(1)
                            combatant.useChirurgeonsKit()
                        else:
                            victim.broadcast(
                                f"|025{combatant.name} tries to aid {victim.name} but with no training they are unable to help.|n")
                    elif victim.isAtMaxDeathPoints() and not victim.atMaxBleedPoints():
                        if combatant.stabilize() or combatant.medicine():
                            amount_to_heal = combatant.medicine()
                            if combatant.stabilize() > combatant.medicine():
                                amount_to_heal = combatant.stabilize()

                            if amount_to_heal > victim.missingBleedPoints():
                                victim.setBody(1)
                                victim.resetBleedPoints()
                                combatant.useChirurgeonsKit()
                                combatant.broadcast(
                                    f"|025{combatant.name} performs some minor healing techniques and provides|n (|430{amount_to_heal}|n) |025points of aid to {victim.name}.  {victim.name} returns to the fight, but weakened|n")
                            else:
                                victim.addBleedPoints(combatant.medicine())
                                combatant.useChirurgeonsKit()
                                combatant.broadcast(
                                    f"|025{combatant.name} performs some minor healing techniques and provides|n (|430{amount_to_heal}|n) |025points of aid to {victim.name}.|n")
                        else:
                            combatant.message(f"|400You are not skilled enough.|n")
                            victim.broadcast(
                                f"|025{combatant.name} tries to stop {victim.name} from bleeding, but is unable to|n")
                    elif victim.hasDeathPoints(1) or victim.hasDeathPoints(2):
                        if combatant.stabilize():
                            combatant.broadcast(f"|025{combatant.name} performs advanced healing techniques and provides|n (|430{combatant.stabilize()}|n) |025 points of aid to {victim.name}.|n")
                            if combatant.stabilize() > victim.missingDeathPoints():
                                remaining_healing = combatant.stabilize() - victim.missingDeathPoints()
                                victim.setDeathPoints(3)
                                victim.addBleedPoints(remaining_healing)
                                combatant.useChirurgeonsKit()
                                
                                combatant.message(f"|400You are able to stop {victim.name} from dying, but they are still bleeding out!.|n")
                            else:
                                victim.addDeathPoints(combatant.stabilize())
                                combatant.useChirurgeonsKit()
                        else:
                            combatant.message(f"|400{victim.name}'s injuries are beyond your skill as a healer.|n")
                            victim.broadcast(
                                f"|025{combatant.name} tries to stop {victim.name} from dying, but is unable to|n")
                    else:
                        combatant.message(f"{victim.name} |025is too fargone to administer further healing.|n")
                else:
                    combatant.message(f"{victim.name} does not require the application of your healing skills.|n")
                    combatant.broadcast( f"|025{combatant.name} tries to aid {victim.name} but they are uninjured!|n")
            else:
                combatant.message(f"You are out of materials in your Chirurgeon's kit|n")
                combatant.broadcast(f"|025{combatant.name} tries to aid {victim.name} but does not have the supplies to do so.|n")

            # Clean up in combat loop
            if (combatant.caller in combatant.caller.location.db.combat_loop) or (target in combatant.caller.location.db.combat_loop):
                loop.combatTurnOff(combatant.caller)
                loop.cleanup()
            else:
                return
        else:
            combatant.message("|430You need to wait until it is your turn before you are able to act.|n")
            return
