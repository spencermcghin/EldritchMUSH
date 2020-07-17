# Local imports
from evennia import Command
from commands.combat_commands.strike_command.strike_logic import Strike
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

        # Init combat helper class for logic
        h = Helper(self.caller)

        # Check for correct command
        if not self.args:
            self.msg("|540Usage: strike <target>|n")
            return

        # Check for and error handle designated target
        target = h.targetHandler(self.target)

        # Use parsed args in combat loop
        loop = CombatLoop(self.caller, self.target)
        loop.resolveCommand()

        # Run logic for strike command
        if self.caller.db.combat_turn:

            # Return db stats needed to calc melee results
            combat_stats = h.getMeleeCombatStats(self.caller)

            # Get die result based on master of arms level
            if combat_stats.get("melee", 0):

                # Check if damage bonus comes from fayne or master_of_arms
                die_result = h.fayneChecker(combat_stats.get("master_of_arms", 0), combat_stats.get("wylding_hand", 0))

                # Get damage result and damage for weapon type
                attack_result = (die_result + combat_stats.get("weapon_level", 0)) - combat_stats.get("dmg_penalty", 0) - combat_stats.get("weakness", 0)
                damage = 2 if combat_stats.get("two_handed", 0) == True else 1
                target_av = target.db.av
                shot_location = h.shotFinder(target.db.targetArray)

                # Compare caller attack_result to target av.
                # If attack_result > target av -> hit, else miss
                if attack_result >= target_av:
                    # if target has any more armor points left go through the damage subtractor
                    if target_av:
                        self.caller.location.msg_contents(f"|015{self.caller.key} strikes deftly|n (|020{attack_result}|n) |015at {target.key} and hits|n (|400{target_av}|n), |015dealing|n |540{damage}|n |015damage!|n")
                        # subtract damage from corresponding target stage (shield_value, armor, tough, body)
                        new_av = h.damageSubtractor(damage, target)
                        # Update target av to new av score per damageSubtractor
                        target.db.av = new_av
                        target.msg(f"|540Your new total Armor Value is {new_av}:\nShield: {target.db.shield}\nArmor Specialist: {target.db.armor_specialist}\nArmor: {target.db.armor}\nTough: {target.db.tough}|n")
                    else:
                        # No target armor so subtract from their body total and hit a limb. Add logic from handler above. Leave in body handler in combat handler.
                        self.caller.location.msg_contents(f"|015{self.caller.key} strikes deftly|n (|020{attack_result}|n) |015at {target.key} and hits |n(|400{target_av}|n)|015, injuring their {shot_location} and dealing|n |540{damage}|n |015damage!|n.")
                        if shot_location == "torso":
                            if target.db.body > 0:
                                target.db.body = 0
                                self.caller.location.msg_contents(f"|015{target.key} has been fatally wounded and is now bleeding to death. They will soon be unconscious.|n")
                            else:
                                target.db.body -= damage
                                target.msg(f"|540Your new body value is {target.db.body}|n")
                        else:
                            target.db.body -= damage
                            target.msg(f"|400You {shot_location} is now injured and have taken |n|540{damage}|n|400 points of damage.|n")
                            # Send a message to the target, letting them know their body values
                            target.msg(f"|540Your new body value is {target.db.body}|n")
                            if -3 <= target.db.body <= 0:
                                target.msg("|540You are bleeding profusely from many wounds and can no longer use any active martial skills.\nYou may only use the limbs that have not been injured.|n")
                                target.location.msg_contents(f"|015{target.key} is bleeding profusely from many wounds and will soon lose consciousness.|n")
                            elif target.db.body <= -4:
                                target.msg("|400You are now unconscious and can no longer move of your own volition.|n")
                                target.location.msg_contents(f"|015{target.key} does not seem to be moving.|n")

                else:
                    self.caller.location.msg_contents(f"|015{self.caller.key} swings wildly|n |400{attack_result}|n|015, missing {target.key} |n|020{target_av}|n")

                # Clean up
                # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                loop.combatTurnOff(self.caller)
                loop.cleanup()

            else:
                 self.msg("|540Before you strike you must equip a melee weapon using the command setmelee 1.")
        else:
            self.msg("You need to wait until it is your turn before you are able to act.")
            return
