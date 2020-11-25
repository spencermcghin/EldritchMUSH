# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from ..combatant import Combatant

class CmdBattlefieldMedicine(Command):
    key = "medic"
    help_category = "mush"

    def __init__(self):
        self.target = None

    def parse(self):
        self.target = self.args.strip()

    def func(self):
        # Check for correct command
        if not self.args:
            self.caller.msg("|430Usage: medic <target>|n")
            return

        combatant = Combatant(self.caller)

        if combatant.cantFight:
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

        if not combatant.canFight:
            self.msg("|400You are too injured to act.|n")
            return

        if not combatant.hasChirurgeonsKit():
            combatant.message(f"|400You are out of materials in your Chirurgeon's kit.|n")
            return

        if combatant.hasTurn():
