# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combatant import Combatant

class CmdBattlefieldMedicine(Command):
    key = "medic"
    help_category = "mush"

    def __init__(self):
        self.target = None

    def parse(self):
        self.target = self.args.strip()

    def func(self):
        combatant = Combatant(self.caller)

        "This actually does things"
        # Check for correct command
        if not self.args:
            self.caller.msg("|430Usage: medic <target>|n")
            return

        if combatant.cantFight():
            combatant.message("|400You are too injured to act.|n")
            return

        # Get target if there is one
        target = self.caller.search(self.target)
        victim = Combatant(target)

        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        #TODO: This code is repeated.  FIND ME A REFACTOR!
        if target:
            if (combatant.caller in combatant.caller.location.db.combat_loop) or (
                    target in combatant.caller.location.db.combat_loop):
                loop = CombatLoop(combatant.caller, target)
                loop.resolveCommand()
            else:
                pass
        else:
            self.msg("|430Please designate an appropriate target.|n")

        if combatant.hasTurn():
            if combatant.battlefieldMedicine() and victim.body() is not None:
                # Use parsed args in combat loop. Handles turn order in combat.
                # Resolve medic command
                if victim.hasBody(3):
                    combatant.message(f"{victim.name} does not require the application of your healing skills.")
                elif victim.hasBody(1) or victim.hasBody(2):
                    # If not over 1, add points to total
                    victim.broadcast(f"|025{combatant.name} comes to {victim.name}'s rescue, healing {victim.name} for|n (|4301|n) |025body point.|n")
                    victim.addBody(1)

                    victim.message(f"|540Your new body value is:|n {victim.body()}|n")
                    # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                    if (combatant.caller in combatant.caller.location.db.combat_loop) or (
                            target in combatant.caller.location.db.combat_loop):
                        loop.combatTurnOff(combatant.caller)
                        loop.cleanup()
                    else:
                        return
                elif victim.body() <= 0:
                    combatant.broadcast(f"|025{combatant.name} comes to {victim.name}'s rescue, though they are too far gone.\n{victim.name} may require the aid of more sophisticated healing techniques.|n")
                    return
            else:
                combatant.message("|400You had better not try that.|n")
                return
        else:
            combatant.message("|430You need to wait until it is your turn before you are able to act.|n")
            return
