# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper

class CmdSunder(Command):
    """
    Issues a sunder command.

    Usage:

    sunder <target>

    This will calculate an attack score based on your weapon and master of arms level.
    """

    key = "sunder"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):

        if not self.target:
            self.caller.msg("|540Usage: sunder <target>|n")
            return

        # Init combat helper class for logic
        h = Helper(self.caller)

        # Check for and error handle designated target
        target = h.targetHandler(self.target)

        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        loop = CombatLoop(self.caller, target)
        loop.resolveCommand()

        # Run logic for strike command
        if self.caller.db.combat_turn:

            # Run rest of command logic after passing checks.

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



        "Get level of master of arms for base die roll. Levels of gear give a flat bonus of +1/+2/+3."
        master_of_arms = self.caller.db.master_of_arms
        hasBow = self.caller.db.bow
        hasTwoHanded = self.caller.db.twohanded
        sundersRemaining = self.caller.db.sunder
        weapon_level = h.weaponValue(self.caller.db.weapon_level)

        wylding_hand = self.caller.db.wyldinghand

        # Check for equip proper weapon type
        # Check for weakness on character
        weakness = h.weaknessChecker(self.caller.db.weakness)
        target_av = target.db.av

        # Check for equip proper weapon type or weakness
        if weakness:
            self.caller.msg("|400You are too weak to use this attack.|n")
        elif hasBow:
            self.caller.msg("|540Before you can attack, you must first unequip your bow using the command setbow 0.")
        elif not hasTwoHanded:
            self.caller.msg("|540Before you can attack, you must first equip a two handed weapon using the command settwohanded 1.")
        else:
            if sundersRemaining > 0:
            # Return die roll based on level in master of arms or wylding hand.
                if wylding_hand:
                    die_result = h.wyldingHand(wylding_hand)
                else:
                    die_result = h.masterOfArms(master_of_arms)

                # Decrement amount of cleaves from amount in database
                self.caller.db.sunder -= 1

                # Get final attack result and damage
                weakness = h.weaknessChecker(self.caller.db.weakness)
                dmg_penalty = h.bodyChecker(self.caller.db.body)
                attack_result = (die_result + weapon_level) - dmg_penalty - weakness
                shot_location = h.shotFinder(target.db.targetArray)

                # Return attack result message
                if attack_result >= (target_av - target_penalty):
                    # if target has any more armor points left go through the damage subtractor
                    if target_av:
                        self.caller.location.msg_contents(f"|015{self.caller.key} sunders|n (|020{attack_result}|n) |015at {target.key} and hits|n (|400{target_av}|n), |015dealing|n |5402|n |015damage!|n")
                        # subtract damage from corresponding target stage (shield_value, armor, tough, body)
                        new_av = h.damageSubtractor(2, target)
                        # Update target av to new av score per damageSubtractor
                        target.db.av = new_av
                        target.msg(f"|540Your new total Armor Value is {new_av}:\nShield: {target.db.shield}\nArmor Specialist: {target.db.armor_specialist}\nArmor: {target.db.armor}\nTough: {target.db.tough}|n")
                    else:
                        # No target armor so subtract from their body total and hit a limb. Add logic from handler above. Leave in body handler in combat handler.
                        self.caller.location.msg_contents(f"|015{self.caller.key} strikes deftly|n (|020{attack_result}|n) |015at {target.key} and hits |n(|400{target_av}|n)|015, injuring their {shot_location} and dealing|n |5402|n |015damage!|n.")
                        if shot_location == "torso":
                            if target.db.body > 0:
                                target.db.body = 0
                                self.caller.location.msg_contents(f"|015{target.key} has been fatally wounded and is now bleeding to death. They will soon be unconscious.|n")
                            else:
                                target.db.body -= 2
                                target.msg(f"|540Your new body value is {target.db.body}|n")
                        else:
                            target.db.body -= 2
                            target.msg(f"|400You {shot_location} is now injured and have taken |n|5402|n|400 points of damage.|n")
                            # Send a message to the target, letting them know their body values
                            target.msg(f"|540Your new body value is {target.db.body}|n")
                            if -3 <= target.db.body <= 0:
                                target.msg("|540You are bleeding profusely from many wounds and can no longer use any active martial skills.\nYou may only use the limbs that have not been injured.|n")
                                target.location.msg_contents(f"|015{target.key} is bleeding profusely from many wounds and will soon lose consciousness.|n")
                            elif target.db.body <= -4:
                                target.msg("|400You are now unconscious and can no longer move of your own volition.|n")
                                target.location.msg_contents(f"|015{target.key} does not seem to be moving.|n")
                else:
                    self.caller.location.msg_contents(f"|015{self.caller.key} swings wildly|n |400{attack_result}|n|015, |015missing {target.key}|n")
            else:
               self.caller.msg("|400You have 0 sunders remaining or do not have the skill.|n")
