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
        elif combatant.cantFight():
            combatant.message("|400You are too injured to act.|n")
            return

        victim = combatant.getVictim(self.target)

        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        if not victim:
            combatant.message("|430Please designate an appropriate target.|n")
            return

        loop = CombatLoop(combatant.caller, combatant.target)
        loop.resolveCommand()


        if combatant.hasTurn(f"|430You need to wait until it is your turn before you are able to act.|n"):
            if combatant.isArmed(f"|430Before you strike you must equip a melee weapon using the command equip <weapon name>.|n"):
                if victim.isAlive():
                    # Check if damage bonus comes from fayne or master_of_arms
                    attack_result = combatant.rollAttack()

                    if attack_result >= victim.av():
                        # if target has any more armor points left go through the damage subtractor
                        if victim.av():
                            combatant.broadcast(f"|025{combatant.name} strikes deftly|n (|020{attack_result}|n) |025at {victim.name} and hits|n (|400{victim.av()}|n), |025dealing|n (|430{combatant.getDamage()}|n) |025damage!|n")

                            # subtract damage from corresponding target stage (shield_value, armor, tough, body)
                            new_av = victim.takeDamage(combatant, combatant.getDamage())

                            victim.setAv(new_av)
                            victim.message(f"|430Your new total Armor Value is {victim.av()}:\nShield: {victim.getShield()}\nArmor Specialist: {victim.getArmorSpecialist()}\nArmor: {victim.getArmor()}\nTough: {victim.getTough()}|n")
                        else:
                            # Get damage result and damage for weapon type
                            shot_location = combatant.determineHitLocation(victim)

                            # No target armor so subtract from their body total and hit a limb.
                            combatant.message(f"|025{combatant.name} strikes deftly|n (|020{attack_result}|n) |025at {victim.name} and hits |n(|400{victim.av()}|n)|025, injuring their {shot_location} and dealing|n |430{combatant.getDamage()}|n |025damage!|n.")
                            # First torso shot always takes body to 0. Does not pass excess damage to bleed points.
                            if shot_location == "torso" and victim.body() > 0:
                                victim.takeFatalDamage(combatant)
                                self.caller.location.msg_contents(f"|025{victim.name()} has been fatally wounded and is bleeding profusely.|n")
                            else:
                                victim.takeDeath(combatant, combatant.getDamage())
                    else:
                        combatant.broadcast(f"|025{combatant.name} swings wildly|n (|400{attack_result}|n)|025, missing {victim.name}|n (|020{victim.av()}|n)")
                else:
                    combatant.message(f"|400{victim.name} is dead. You only further mutiliate their body.|n")
                    combatant.broadcast(f"|025{combatant.name} further mutilates the corpse of {victim.name}.|n")
                # Clean up
                # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                loop.combatTurnOff(self.caller)
                loop.cleanup()