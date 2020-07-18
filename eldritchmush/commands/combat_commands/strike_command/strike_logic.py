# Local imports
from commands.combat import Helper


class Strike:

    def runLogic(self, caller, target):
        # Init combat helper class for logic
        h = Helper()

        # Get hasMelee for character to check that they've armed themselves.
        hasMelee = caller.db.melee

        # Vars for attack_result logic
        master_of_arms = caller.db.master_of_arms
        weapon_level = h.weaponValue(caller.db.weapon_level)
        wylding_hand = caller.db.wylding_hand

        # Get die result based on master of arms level
        if not hasMelee:
            caller.msg("|540Before you strike you must equip a melee weapon using the command setmelee 1.")
        else:
            # Return die roll based on level in master of arms or wylding hand.
            if wylding_hand:
                die_result = h.wyldingHand(wylding_hand)
            else:
                die_result = h.masterOfArms(master_of_arms)

            weakness = h.weaknessChecker(caller.db.weakness)
            dmg_penalty = h.bodyChecker(caller.db.body)

            # Get damage result and damage for weapon type
            attack_result = (die_result + weapon_level) - dmg_penalty - weakness
            damage = 2 if caller.db.twohanded == True else 1
            target_av = target.db.av
            shot_location = h.shotFinder(target.db.targetArray)

            # Compare caller attack_result to target av.
            # If attack_result > target av -> hit, else miss
            if attack_result >= target_av:
                # if target has any more armor points left go through the damage subtractor
                if target_av:
                    caller.location.msg_contents(f"|015{caller.key} strikes deftly|n (|020{attack_result}|n) |015at {target.key} and hits|n (|400{target_av}|n), |015dealing|n |540{damage}|n |015damage!|n")
                    # subtract damage from corresponding target stage (shield_value, armor, tough, body)
                    new_av = h.damageSubtractor(damage, target)
                    # Update target av to new av score per damageSubtractor
                    target.db.av = new_av
                    target.msg(f"|540Your new total Armor Value is {new_av}:\nShield: {target.db.shield}\nArmor Specialist: {target.db.armor_specialist}\nArmor: {target.db.armor}\nTough: {target.db.tough}|n")
                else:
                    # No target armor so subtract from their body total and hit a limb. Add logic from handler above. Leave in body handler in combat handler.
                    caller.location.msg_contents(f"|015{caller.key} strikes deftly|n (|020{attack_result}|n) |015at {target.key} and hits |n(|400{target_av}|n)|015, injuring their {shot_location} and dealing|n |540{damage}|n |015damage!|n.")
                    if shot_location == "torso":
                        if target.db.body > 0:
                            target.db.body = 0
                            caller.location.msg_contents(f"|015{target.key} has been fatally wounded and is now bleeding to death. They will soon be unconscious.|n")
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
                caller.location.msg_contents(f"|015{caller.key} swings wildly|n |400{attack_result}|n|015, missing {target.key} |n|020{target_av}|n")
