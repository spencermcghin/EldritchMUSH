# Local imports
from evennia import Command, utils
from world.combat_loop import CombatLoop
from typeclasses.npc import Npc
from commands.combatant import Combatant

class CmdDisarm(Command):
    """
    Issues a disarm command.

    Usage:

    disarm <target>

    This will issue a disarm command that reduces the next amount of damage taken by master of arms level.
    """

    key = "disarm"
    help_category = "combat"

    def __init__(self):
        self.target = None

    def parse(self):
        # Very trivial parser
        self.target = self.args.strip()

    def func(self):
        combatant = Combatant(self.caller)

        if not self.args:
            self.caller.msg("|430Usage: disarm <target>|n")
            return

        if combatant.cantFight:
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

        #TODO: Right now the loop on Disarm and Sunder look almost identical.  I feel like you probably want something different?
        if combatant.hasTurn(f"|430You need to wait until it is your turn before you are able to act.|n"):
            if combatant.isArmed(f"|430Before you attack you must equip a weapon using the command equip <weapon>.|n"):
                if not combatant.hasWeakness(f"|400You are too weak to use this attack.|n"):
                    if combatant.hasDisarmsRemaining(f"|400You have 0 disarms remaining or do not have the skill.\nPlease choose another action.|n"):
                        if not combatant.inventory.hasBow() or combatant.hasSniper():
                            if not victim.hasTwoHandedWeapon():
                                if victim.isAlive:
                                    maneuver_difficulty = 2
                                    attack_result = combatant.rollAttack(maneuver_difficulty)
                                    if attack_result >= victim.av:
                                        # Check for NPC calling the command and pick a new command if so.
                                        # TODO: Spence - Why shouldn't NPCs use Disarm?
                                        if utils.inherits_from(self.caller, Npc) and combatant.isTwoHanded():
                                            self.caller.execute_cmd(f"strike {target.key}")
                                            return


                                        combatant.decreaseDisarms(1)

                                        shot_location = combatant.determineHitLocation(victim)
                                        victim.takeDamage(combatant, combatant.getDamage(), shot_location)

                                        victim.reportAv()

                                        if not victim.resistsAttack():
                                            victim.message(f"|430You have been disarmed. Your next turn will be skipped.|n")
                                            victim.disarm()
                                            combatant.broadcast(f"|025{combatant.name} nimbly strikes|n (|020{attack_result}|n) |025with a deft maneuver and disarms {victim.name}|n (|400{victim.av}|n)|025, striking them in the {shot_location} and dealing|n (|430{combatant.getDamage()}|n) |025damage|n.")
                                        else:
                                            combatant.broadcast(
                                                f"|025{combatant.name} nimbly strikes|n (|020{attack_result}|n) |025, striking them in the {shot_location} and dealing|n (|430{combatant.getDamage()}|n) |025damage|n. {combatant.name} attempts to disarm {victim.name}, but {victim.name} Resists the attempt")

                                    else:
                                        combatant.broadcast(f"|025{combatant.name} swings deftly,|n (|020{attack_result}|n) |025attempting to disarm {victim.name}, but misses|n (|400{victim.av}|n)|025.|n")
                                else:
                                    combatant.message(f"|430{victim.name} is dead. You only further mutilate their body.|n")
                                    combatant.broadcast(f"|025{combatant.name} further mutilates the corpse of {victim.name}.|n")
                            else:
                                combatant.message(f"|430You cannot disarm a two-handed weapon. Please try another attack.|n")
                                combatant.broadcast(
                                    f"|025{combatant.name} tries to disarm {victim.name}|025, but cannot disarm a 2-handed weapon!|n")
                            # Clean up
                            # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                            loop.combatTurnOff(self.caller)
                            loop.cleanup()
                        else:
                            combatant.message(f"|430To use Disarm with a bow equipped you must have the Sniper skill|n")
