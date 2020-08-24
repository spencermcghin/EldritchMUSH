# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper


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

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()


    def func(self):

        # Check for correct command
        # Target handling
        if not self.args:
            self.msg("|430Usage: strike <target>|n")
            return

        if self.args == self.caller:
            self.msg("|300You can't do that.|n")

        # Init combat helper class for logic
        h = Helper(self.caller)
        # Check for and error handle designated target
        target = self.caller.search(self.target)

        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        if target:
            loop = CombatLoop(self.caller, target)
            loop.resolveCommand()
        else:
            return

        # Run logic for strike command
        if self.caller.db.combat_turn:

            # Run rest of command logic after passing checks.

            # Return db stats needed to calc melee results
            combat_stats = h.getMeleeCombatStats(self.caller)

            # Check to see if player holding a weapon in either hand. Sunder removes weapon from player slot. Won't let you equip broken weapons.
            if combat_stats.get("right_slot", '') or combat_stats.get("left_slot", ''):

                # Check if damage bonus comes from fayne or master_of_arms
                die_result = h.fayneChecker(combat_stats.get("master_of_arms", 0), combat_stats.get("wylding_hand", 0))

                # Get damage result and damage for weapon type
                attack_result = (die_result + self.caller.db.weapon_level) - combat_stats.get("dmg_penalty", 0) - combat_stats.get("weakness", 0)
                damage = 2 if combat_stats.get("two_handed", False) else 1
                target_av = target.db.av
                shot_location = h.shotFinder(target.db.targetArray)

                # Compare caller attack_result to target av.
                if h.canFight(self.caller):
                    if h.isAlive(target):
                        # If attack_result > target av -> hit, else miss
                        if attack_result >= target_av:
                            # if target has any more armor points left go through the damage subtractor
                            if target_av:
                                self.caller.location.msg_contents(f"|025{self.caller.key} strikes deftly|n (|020{attack_result}|n) |025at {target.key} and hits|n (|300{target_av}|n), |025dealing|n |430{damage}|n |025damage!|n")
                                # subtract damage from corresponding target stage (shield_value, armor, tough, body)
                                new_av = h.damageSubtractor(damage, target, self.caller)
                                # Update target av to new av score per damageSubtractor
                                target.db.av = new_av
                                target.msg(f"|430Your new total Armor Value is {new_av}:\nShield: {target.db.shield}\nArmor Specialist: {target.db.armor_specialist}\nArmor: {target.db.armor}\nTough: {target.db.tough}|n")
                            else:
                                # No target armor so subtract from their body total and hit a limb.
                                self.caller.location.msg_contents(f"|025{self.caller.key} strikes deftly|n (|020{attack_result}|n) |025at {target.key} and hits |n(|300{target_av}|n)|025, injuring their {shot_location} and dealing|n |430{damage}|n |025damage!|n.")
                                # First torso shot always takes body to 0. Does not pass excess damage to bleed points.
                                if shot_location == "torso" and target.db.body > 0:
                                    target.db.body = 0
                                    self.caller.location.msg_contents(f"|025{target.key} has been fatally wounded and is bleeding profusely.|n")
                                else:
                                    h.deathSubtractor(damage, target, self.caller)
                        else:
                            self.caller.location.msg_contents(f"|025{self.caller.key} swings wildly|n |300{attack_result}|n|025, missing {target.key} |n|020{target_av}|n")
                    else:
                        self.msg(f"|300{target.key} is dead. You only further mutiliate their body.|n")
                        self.caller.location.msg_contents(f"|430{self.caller.key} further mutilates the corpse of {target.key}.|n")
                else:
                    self.msg("|300You are too injured to act.|n")
                # Clean up
                # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                loop.combatTurnOff(self.caller)
                loop.cleanup()
            else:
                 self.msg("|430Before you strike you must equip a melee weapon using the command equip <weapon name>.|n")
        else:
            self.msg("|430You need to wait until it is your turn before you are able to act.|n")
            return
