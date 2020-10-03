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
    help_category = "combat"

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

        if combatant.cantFight:
            combatant.message("|400You are too injured to act.|n")
            return

        # Get target if there is one
        # Check for and error handle designated target
        target = self.caller.search(self.target)

        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        if not target:
            combatant.message("|430Please designate an appropriate target.|n")
            return

        victim = combatant.getVictim(self.target)

        if not target.db.bleed_points:
            combatant.message(f"{victim.name} |400is dead. You only further mutiliate their body.|n")
            combatant.broadcast(f"{combatant.name} |025further mutilates the corpse of|n {victim.name}|025.|n")
            return

        loop = CombatLoop(combatant.caller, combatant.target)
        loop.resolveCommand()

        #TODO: Currently Disarm does Damage and Stun doesnt.  Is that intended?
        if combatant.hasTurn(f"|430You need to wait until it is your turn before you are able to act.|n"):
            if combatant.isArmed(f"|430Before you attack you must equip a weapon using the command equip <weapon>.|n"):
                if combatant.hasStunsRemaining(f"|400You have 0 stuns remaining or do not have the skill.\nPlease choose another action.|n"):
                    if not combatant.hasWeakness(f"|400You are too weak to use this attack.|n"):
                        if victim.isAlive:
                            maneuver_difficulty = 1
                            attack_result = combatant.rollAttack(maneuver_difficulty)
                            if attack_result >= victim.av:
                                victim.stun()
                                combatant.decreaseStuns(1)
                                combatant.broadcast(f"{combatant.name} |025lines up behind|n {victim.name} |025and strikes|n (|020{attack_result}|n)|025, stunning them momentarily|n (|400{victim.av}|n)|025.|n")
                            else:
                                combatant.broadcast(f"{combatant.name} (|020{attack_result}|n) |025lines up behind|n {victim.name} (|400{victim.av}|n)|025, but misses their opportunity to stun them.|n")
                        else:
                            combatant.message(f"{victim.name} |400is dead. You only further mutilate their body.|n")
                            combatant.broadcast(f"{combatant.name} |025further mutilates the corpse of|n {victim.name}.|n")

                        # Clean up
                        # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                        loop.combatTurnOff(self.caller)
                        loop.cleanup()
