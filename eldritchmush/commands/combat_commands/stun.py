# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combatant import Combatant



class CmdStun(Command):
    """
    Issues a stun command.

    Usage:

    stun <target>

    This will issue a stun command that makes a target skip their turn, with a -1 penalty to attack.
    """

    key = "stun"
    help_category = "mush"

    def __init__(self):
        self.target = None

    def parse(self):
        self.target = self.args.strip()

    def func(self):
        combatant = Combatant(self.caller)

        # Check for correct command
        if not self.args:
            self.caller.msg("|430Usage: stun <target>|n")
            return

        if combatant.cantFight():
            combatant.message("|400You are too injured to act.|n")
            return

        # Get target if there is one
        target = self.caller.search(self.target)

        if not target:
            combatant.message("|430Please designate an appropriate target.|n")
            return

        victim = Combatant(target)
        loop = CombatLoop(combatant.caller, target)
        loop.resolveCommand()

        #TODO: Should we add a check here to see if the victim is already stunned? What happens then?
        if combatant.hasTurn(f"|430You need to wait until it is your turn before you are able to act.|n"):
            if combatant.isArmed(f"|430Before you attack you must equip a weapon using the command equip <weapon>.|n"):
                if combatant.hasStunsRemaining(f"|400You have 0 stuns remaining or do not have the skill.\nPlease choose another action.|n"):
                    if not combatant.hasWeakness(f"|400You are too weak to use this attack.|n"):
                        if victim.isAlive():
                            attack_result = combatant.rollAttack()
                            if attack_result >= victim.av():
                                victim.stun()
                                combatant.decreaseStuns(1)
                                combatant.broadcast(f"|025{combatant.name} lines up behind {victim.name} and strikes|n (|025{attack_result}|n)|025, stunning them momentarily|n (|400{victim.av()}|n)|025.|n")
                            else:
                                combatant.broadcast(f"|025{combatant.name} (|020{attack_result}|n) |025lines up behind {victim.name}|n (|400{victim.av()}|n)|025, but misses their opportunity to stun them.|n")
                        else:
                            combatant.message(f"|400{victim.name} is dead. You only further mutilate their body.|n")
                            combatant.broadcast(f"|025{combatant.name} further mutilates the corpse of {victim.name}.|n")

                        # Clean up
                        # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                        loop.combatTurnOff(self.caller)
                        loop.cleanup()
