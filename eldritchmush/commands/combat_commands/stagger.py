# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combatant import Combatant

class CmdStagger(Command):
    """
    Issues a stagger command.

    Usage:

    stagger <target>

    This will calculate an attack score based on your weapon and master of arms level.
    """

    key = "stagger"
    help_category = "combat"

    def __init__(self):
        self.target = None

    def parse(self):
        self.target = self.args.strip()

    def func(self):
        combatant = Combatant(self.caller)

        if not self.target:
            self.caller.msg("|430Usage: stagger <target>|n")
            return

        if combatant.cantFight:
            combatant.message("|400You are too injured to act.|n")
            return

        # Get target if there is one
        target = self.caller.search(self.target)

        if not target:
            combatant.message("|430Please designate an appropriate target.|n")
            return

        victim = combatant.getVictim(self.target)

        if not target.db.bleed_points:
            combatant.message(f"|400{victim.name} is dead. You only further mutiliate their body.|n")
            combatant.broadcast(f"|025{combatant.name} further mutilates the corpse of {victim.name}.|n")
            return

        loop = CombatLoop(combatant.caller, target)
        loop.resolveCommand()

        if combatant.hasTurn(f"|430You need to wait until it is your turn before you are able to act.|n"):
            if combatant.isArmed(f"|430Before you attack you must equip a weapon using the command equip <weapon>.|n"):
                    if not combatant.hasWeakness(f"|400You are too weak to use this attack.|n"):
                        if combatant.hasStaggersRemaining(
                            f"|400You have 0 staggers remaining or do not have the skill.\nPlease choose another action.|n"):
                            if not combatant.inventory.hasBow() or combatant.hasSniper():
                                if victim.isAlive:
                                    maneuver_difficulty = 2
                                    attack_result = combatant.rollAttack(maneuver_difficulty)
                                    if attack_result >= victim.av:
                                        combatant.decreaseStaggers(1)

                                        shot_location = combatant.determineHitLocation(victim)
                                        victim.message(
                                            f"|430You have been staggered. You suffer a penalty on your next attack|n")

                                        if not victim.blocksWithShield(shot_location):

                                            if not victim.resistsAttack():
                                                combatant.broadcast(f"{combatant.name} |025strikes|n (|020{attack_result}|n) |025with a powerful blow to the {shot_location} and staggering|n {victim.name} |025out of their footing|n (|400{victim.av}|n)|025, and dealing|n (|430{combatant.getStaggerDamage()}|n) |025damage.|n")
                                                victim.stagger()
                                                victim.takeDamage(combatant, combatant.getStaggerDamage(), shot_location)
                                                victim.reportAv()
                                            else:
                                                combatant.broadcast(f"{combatant.name} |025strikes|n (|020{attack_result}|n) |025with a powerful blow to the {shot_location}|n (|400{victim.av}|n)|025, and dealing|n (|430{combatant.getStaggerDamage()}|n) |025damage.|n {victim.name} Resists being staggered by the powerful attack.|n")

                                        else:
                                            if not victim.resistsAttack():
                                                victim.stagger()
                                                combatant.broadcast(
                                                    f"{combatant.name} |025strikes|n (|020{attack_result}|n) |025with a powerful blow to the {shot_location} but|n {victim.name} |025manages to block with their shield.  However|n {victim.name} |025is still staggered by the powerful attack.|n")
                                            else:
                                                combatant.broadcast(
                                                    f"{combatant.name} |025strikes|n (|020{attack_result}|n) |025with a powerful blow to the {shot_location} but|n {victim.name} |025manages to block with their shield,|n {victim.name} |025also Resists being staggered by the powerful attack.|n")
                                else:
                                    combatant.message(f"{victim.name} |430is dead. You only further mutilate their body.|n")
                                    combatant.broadcast(f"{combatant.name} |025further mutilates the corpse of|n {victim.name}.|n")

                                # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                                loop.combatTurnOff(self.caller)
                                loop.cleanup()
                            else:
                                combatant.message(
                                    f"|430To use Stagger with a bow equipped you must have the Sniper skill|n")
