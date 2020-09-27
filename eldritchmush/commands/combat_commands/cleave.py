
# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combatant import Combatant

class CmdCleave(Command):
    """
    Issues a cleave command.

    Usage:

    cleave <target>

    This will calculate an attack score based on your weapon and master of arms level.
    """

    key = "cleave"
    help_category = "combat"

    def __init__(self):
        self.target = None

    def parse(self):
        # Very trivial parser
        self.target = self.args.strip()

    def func(self):
        combatant = Combatant(self.caller)

        if not self.args:
            self.msg("|430Usage: cleave <target>|n")
            return

        if combatant.cantFight:
            combatant.message("|400You are too injured to act.|n")
            return

        # Get target if there is one
        target = self.caller.search(self.target)

        if not target:
            combatant.message("|430Please designate an appropriate target.|n")
            return

        if not self.target.db.bleed_points:
            combatant.message(f"{victim.name} |400is dead. You only further mutiliate their body.|n")
            combatant.broadcast(f"{combatant.name} |025further mutilates the corpse of|n {victim.name}|025.|n")
            return

        victim = Combatant(target)
        loop = CombatLoop(combatant.caller, target)
        loop.resolveCommand()

        if combatant.hasTurn(f"|430You need to wait until it is your turn before you are able to act.|n"):
            if combatant.isArmed(f"|430Before you attack you must equip a weapon using the command equip <weapon>.|n"):
                if not combatant.hasWeakness(f"|400You are too weak to use this attack.|n"):
                        if combatant.hasCleavesRemaining(
                                f"|400You have 0 cleaves remaining or do not have the skill.\nPlease choose another action."):
                            if combatant.hasTwoHandedWeapon(
                                    f"|430Before you attack you must equip a two handed weapon using the command equip <weapon>.|n"):
                                if victim.isAlive:
                                    #TODO: Spence sanity check - Cleave has no difficulty?
                                    maneuver_difficulty = 0
                                    attack_result = combatant.rollAttack(maneuver_difficulty)
                                    if attack_result >= victim.av:
                                        shot_location = combatant.determineHitLocation(victim)
                                        if not victim.blocksWithShield(shot_location):
                                            combatant.decreaseCleaves(1)
                                            if not victim.resistsAttack():
                                                skip_av_damage = True
                                                victim.takeDamage(combatant, combatant.getDamage(), shot_location, skip_av_damage)

                                                combatant.broadcast(f"|025{combatant.name} strikes|n (|020{attack_result}|n) |025with great ferocity and cleaves {victim.name}'s {shot_location}|n (|400{victim.av}|n)|025, dealing|n (|430{combatant.getDamage()}|n) |025damage|n.")
                                            else:
                                                combatant.broadcast(
                                                    f"|025{combatant.name} strikes|n (|020{attack_result}|n) |025with great ferocity and cleaves {victim.name}'s {shot_location}|n but {victim.name} |025Resists the attack with grim determination.|n")
                                        else:
                                            combatant.broadcast(
                                                f"|025{combatant.name} strikes|n (|020{attack_result}|n) |025with great ferocity and cleaves {victim.name}'s {shot_location}|n (|400{victim.av}|n)|025, however {victim.name} manages to block the blow with their shield!|n.")
                                    else:
                                        combatant.broadcast(f"|025{combatant.name} swings ferociously|n (|030{attack_result}|n) |025at {victim.name}|n (|400{victim.av}|n)|025, but misses.|n")
                                else:
                                    self.msg(f"|430{target.key} is dead. You only further mutiliate their body.|n")
                                    combatant.location.msg_contents(f"|025{combatant.key} further mutilates the corpse of {target.key}.|n")

                                # Clean up
                                # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                                loop.combatTurnOff(self.caller)
                                loop.cleanup()
