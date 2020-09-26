# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combatant import Combatant

class CmdShoot(Command):
    """
    issues a shoot command if armed with a bow.

    Usage:

    shoot <target>

    This will calculate an attack score based on your weapon and master of arms level.
    """

    key = "shoot"
    help_category = "combat"

    def __init__(self):
        self.target = None

    def parse(self):
        self.target = self.args.strip()

    def func(self):
        combatant = Combatant(self.caller)
        # Check for correct command
        # Target handling


        # Check for correct command
        # Target handling
        if not self.args:
            self.msg("|430Usage: strike <target>|n")
            return
        elif self.args == self.caller:
            self.msg("|400You can't do that.|n")
            return
        elif combatant.cantFight:
            combatant.message("|400You are too injured to act.|n")
            return
        elif not combatant.inventory.hasArrowsEquipped:
            combatant.message("|430Please equip arrows to use your bow.|n")
            return
        elif not combatant.inventory.hasArrowsLeft:
            combatant.message("|400You are all out of arrows.|n")
            return


        victim = combatant.getVictim(self.target)

        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        if not victim:
            combatant.message("|430Please designate an appropriate target.|n")
            return

        if not victim.db.bleed_points:
            combatant.message(f"{victim.name} |400is dead. You only further mutiliate their body.|n")
            combatant.broadcast(f"{combatant.name} |025further mutilates the corpse of|n {victim.name}|025.|n")
            return

        loop = CombatLoop(combatant.caller, combatant.target)
        loop.resolveCommand()

        if combatant.hasTurn(f"|430You need to wait until it is your turn before you are able to act.|n"):
            if combatant.inventory.hasBow("|430You need to equip a bow before you are able to shoot, using the command equip <bow name>.|n"):
                if victim.isAlive:
                    bow_penalty = 2
                    bow_damage = 1

                    attack_result = combatant.rollAttack(bow_penalty)
                    shot_location = combatant.determineHitLocation(victim)

                    if attack_result >= victim.av:
                        combatant.inventory.useArrows(1)

                        if not victim.blocksWithShield(shot_location):
                            # Get damage result and damage for weapon type
                            victim.takeDamage(combatant, combatant.getDamage(), shot_location, skip_av_damage)
                            combatant.broadcast(f"{combatant.name} |025lets loose an arrow|n (|020{attack_result}|n)|025 straight for|n {victim.name}|025's {shot_location} and hits|n (|400{victim.av}|n), |025dealing|n (|430{bow_damage}|n) |025damage!|n")
                        else:
                            combatant.broadcast(
                                f"{combatant.name} |025lets loose an arrow|n (|020{attack_result}|n)|025 straight for|n {victim.name}'s |025{shot_location} and hits|n (|400{victim.av}|n)|025, but|n {victim.name} |025is able to raise their shield to block!|n")

                        combatant.message(f"|430You have {combatant.inventory.arrowQuantity} arrows left.")
                        # Clean up
                        # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                        loop.combatTurnOff(self.caller)
                        loop.cleanup()

                else:
                    combatant.message(f"{victim.name} |400is dead. You only further mutiliate their body.|n")
                    combatant.broadcast(f"{combatant.name} |025further mutilates the corpse of|n {victim.name}|025.|n")
