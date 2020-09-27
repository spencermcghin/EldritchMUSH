# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combatant import Combatant

class CmdStrike(Command):
    """
    issues an attack

    Usage:

    strike <target>

    This will calculate an attack score based on your weapon and master of arms level.
    """

    key = "strike"
    aliases = ["hit", "slash", "bash", "punch"]
    help_category = "combat"

    def __init__(self):
        self.target = None

    def parse(self):
        self.target = self.args.strip()


    def func(self):
        combatant = Combatant(self.caller)

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

        victim = combatant.getVictim(self.target)

        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        if not victim:
            combatant.message("|430Please designate an appropriate target.|n")
            return

        if not self.target.db.bleed_points:
            combatant.message(f"{victim.name} |400is dead. You only further mutiliate their body.|n")
            combatant.broadcast(f"{combatant.name} |025further mutilates the corpse of|n {victim.name}|025.|n")
            return

        loop = CombatLoop(combatant.caller, combatant.target)
        loop.resolveCommand()


        if combatant.hasTurn(f"|430You need to wait until it is your turn before you are able to act.|n"):
            if combatant.isArmed(f"|430Before you strike you must equip a melee weapon using the command equip <weapon name>.|n"):
                if victim.isAlive:
                    # Check if damage bonus comes from fayne or master_of_arms
                    attack_result = combatant.rollAttack()
                    shot_location = combatant.determineHitLocation(victim)

                    if attack_result >= victim.av:
                        if not victim.blocksWithShield(shot_location):
                            # Get damage result and damage for weapon type
                            combatant.broadcast(
                            f"{combatant.name} |025strikes deftly|n (|020{attack_result}|n) |025at|n {victim.name} |025and hits|n (|400{victim.av}|n), |025dealing|n (|430{combatant.getDamage()}|n) |025damage!|n")
                            victim.takeDamage(combatant, combatant.getDamage(), shot_location)
                            victim.reportAv()
                        else:
                            combatant.broadcast(
                            f"|025{combatant.name} strikes deftly|n (|020{attack_result}|n) |025at {victim.name} and hits|n (|400{victim.av}|n), |025but|n {victim.name} |025blocks with their shield.|n")
                    else:
                        combatant.broadcast(f"|025{combatant.name} swings wildly|n (|400{attack_result}|n)|025, missing|n {victim.name} (|020{victim.av}|n)|025.|n")
                else:
                    combatant.message(f"{victim.name} |400is dead. You only further mutiliate their body.|n")
                    combatant.broadcast(f"{combatant.name} |025further mutilates the corpse of {victim.name}.|n")
                # Clean up
                # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                loop.combatTurnOff(self.caller)
                loop.cleanup()
