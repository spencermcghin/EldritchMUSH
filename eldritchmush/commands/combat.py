from evennia import Command
from evennia import CmdSet
from evennia import default_cmds
from evennia import create_script
from commands import command

import random

class Helper():
    """
    Class for general combat helper commands.
    """

    def masterOfArms(self, level):
        """
        Returns die result based on master of arms level
        """
        if level == 0:
            die_result = random.randint(1,6)
        elif level == 1:
            die_result = random.randint(1,10)
        elif level == 2:
            die_result = random.randint(1,6) + random.randint(1,6)
        elif level == 3:
            die_result = random.randint(1,8) + random.randint(1,8)

        return die_result

    def wyldingHand(self, level):
        """
        Returns die result based on wylding hand level
        """
        if level == 0:
            die_result = random.randint(1,6)
        elif level == 1:
            die_result = random.randint(1,10)
        elif level == 2:
            die_result = random.randint(1,6) + random.randint(1,6)
        elif level == 3:
            die_result = random.randint(1,8) + random.randint(1,8)

        return die_result

    def shotFinder(self, targetArray):
        """
        Rolls a number between 1 and 5 and then maps it to an area of the body for the hit
        """
        # Roll a d5 and then map the result to the targetArray.
        # Return the value from the target array and remove it from the current character's targetArray value in the db

        # Roll random number
        result = random.randint(0,5)

        # Get part of body based on targetArray input
        target = targetArray[result]

        return target

    def bodyChecker(self, bodyScore):
        """
        Just checks amount of body and applies penalty based on number character is down.
        """
        if bodyScore >= 3:
            damage_penalty = 0
        elif bodyScore == 2:
            damage_penalty = 1
        elif bodyScore == 1:
            damage_penalty = 2
        elif bodyScore == 0:
            damage_penalty = 3
        elif bodyScore == -1:
            damage_penalty = 4
        elif bodyScore == -2:
            damage_penalty = 5
        elif bodyScore == -3:
            damage_penalty = 6
            return
        else:
            damage_penalty = 0

        return damage_penalty

    def weaknessChecker(self, hasWeakness):
        """
        Checks to see if caller has weakness and then applies corresponding penalty.
        """
        attack_penalty = 2 if hasWeakness else 0

        return attack_penalty

    def damageSubtractor(self, damage, target):
        """
        Takes attack type of caller and assigns damage based on target stats.
        """
        # Build the target av objects
        target_shield_value = target.db.shield_value  # Applied conditionally
        target_armor = target.db.armor
        target_tough = target.db.tough
        target_body = target.db.body
        target_armor_specialist = target.db.armor_specialist
        target_armor_value = target.db.av

        # Apply damage in order
        if target_shield_value:
            # Get value of shield damage to check if it's under 0. Need to pass
            # this on to armor
            shield_damage = target_shield_value - damage
            if shield_damage < 0:
                # Check if damage would make shield go below 0
                damage = abs(shield_damage)
                # Set shield_value to 0
                target.db.shield_value = 0
                # Recalc and set av with new shield value
            else:
                target.db.shield_value = shield_damage
                damage = 0

        if target_armor_specialist and damage:
            # Get value of damage
            armor_specialist_damage = target_armor_specialist - damage
            if armor_specialist_damage < 0:
                damage = abs(armor_specialist_damage)
                target.db.armor_specialist = 0
            else:
                target.db.armor_specialist = armor_specialist_damage
                damage = 0

        if target_armor and damage:
            # Get value of damage
            armor_damage = target_armor - damage
            if armor_damage < 0:
                damage = abs(armor_damage)
                target.db.armor = 0
            else:
                target.db.armor = armor_damage
                test = target_shield_value + target.db.armor + target_tough + target_armor_specialist
                damage = 0

        if target_tough and damage:
            tough_damage = target_tough - damage
            if tough_damage < 0:
                damage = abs(tough_damage)
                target.db.tough = 0
            else:
                target.db.tough = tough_damage
                damage = 0

        else:
            body_damage = target_body - damage
            if body_damage < 0:
                damage = abs(body_damage)
                target.db.body = 0
            else:
                target.db.body = body_damage

        new_av = self.updateArmorValue(target.db.shield_value, target.db.armor, target.db.tough, target.db.armor_specialist)
        return new_av

    def updateArmorValue(self, shieldValue, armor, tough, armorSpecialist):
        armor_value = shieldValue + armor + tough + armorSpecialist

        return armor_value




"""
Basic Combat commands
"""

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
        h = Helper()

        # Check for correct command
        if not self.args:
            self.caller.msg("|yUsage: strike <target>|n")
            return

        target = self.caller.search(self.target)

        if not target:
            self.caller.msg("|yUsage: strike <target>|n")
            return

        if target == self.caller:
            self.caller.msg(f"|r{self.caller}, quit hitting yourself!|n")
            return


        # Get hasMelee for character to check that they've armed themselves.
        hasMelee = self.caller.db.melee

        # Vars for attack_result logic
        master_of_arms = self.caller.db.master_of_arms
        weapon_level = self.caller.db.weapon_level
        wylding_hand = self.caller.db.wylding_hand

        # Get die result based on master of arms level
        if not hasMelee:
            self.caller.msg("|yBefore you strike you must equip a melee weapon using the command setmelee 1.")
        else:
            # Return die roll based on level in master of arms or wylding hand.
            if wylding_hand:
                die_result = h.wyldingHand(wylding_hand)
            else:
                die_result = h.masterOfArms(master_of_arms)

            weakness = h.weaknessChecker(self.caller.db.weakness)
            dmg_penalty = h.bodyChecker(self.caller.db.body)

            # Get damage result and damage for weapon type
            attack_result = (die_result + weapon_level) - dmg_penalty - weakness
            damage = 2 if self.caller.db.twohanded == True else 1
            target_av = target.db.av
            shot_location = h.shotFinder(target.db.targetArray)

            # Compare caller attack_result to target av.
            # If attack_result > target av -> hit, else miss
            if attack_result >= target_av:
                # if target has any more armor points left go through the damage subtractor
                if target_av:
                    self.caller.location.msg_contents(f"|b{self.caller.key} strikes deftly|n (|g{attack_result}|n) |bat {target.key} and hits|n (|r{target_av}|n), |bdealing|n |y{damage}|n |bdamage!|n")
                    # subtract damage from corresponding target stage (shield_value, armor, tough, body)
                    new_av = h.damageSubtractor(damage, target)
                    # Update target av to new av score per damageSubtractor
                    target.db.av = new_av
                    target.msg(f"|yYour new total Armor Value is {new_av}:\nShield: {target.db.shield}\nArmor Specialist: {target.db.armor_specialist}\nArmor: {target.db.armor}\nTough: {target.db.tough}|n")
                else:
                    # No target armor so subtract from their body total and hit a limb. Add logic from handler above. Leave in body handler in combat handler.
                    self.caller.location.msg_contents(f"|b{self.caller.key} strikes deftly|n (|g{attack_result}|n) |bat {target.key} and hits |n(|r{target_av}|n)|b, injuring their {shot_location} and dealing|n |y{damage}|n |bdamage!|n.")
                    if shot_location == "torso":
                        target.db.body = 0
                        self.caller.location.msg_contents(f"|b{target.key} has been fatally wounded and is now bleeding to death. They will soon be unconscious.|n")
                    else:
                        target.db.body -= damage
                        target.msg(f"|rYou {shot_location} is now injured and have taken |n|y{damage}|n|r points of damage.|n")
                        # Send a message to the target, letting them know their body values
                        target.msg(f"|yYour new body value is {target.db.body}|n")
                        if -3 <= target.db.body <= 0:
                            target.msg("|yYou are bleeding profusely from many wounds and can no longer use any active martial skills.\nYou may only use the limbs that have not been injured.|n")
                        elif target.db.body <= -4:
                            target.msg("|rYou are now unconscious and can no longer move of your own volition.|n")
            else:
                self.caller.location.msg_contents(f"|b{self.caller.key} swings wildly|n |r{attack_result}|n|b, missing {target.key} |n|g{target_av}|n")

class CmdKill(Command):
    """
    issues a finishing action

    Usage:

    kill <target>

    This will calculate an attack score based on your weapon and master of arms level.
    """

    key = "kill"
    aliases = ["finish"]
    help_category = "combat"


    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()


    def func(self):
        # Init combat helper class for logic
        h = Helper()

        # Check for correct command
        if not self.args:
            self.caller.msg("|yUsage: kill <target>|n")
            return

        target = self.caller.search(self.target)

        if not target:
            self.caller.msg("|yUsage: kill <target>|n")
            return

        if target == self.caller:
            self.caller.msg(f"|r{self.caller}, please don't kill yourself.|n")
            return


        # Get hasMelee for character to check that they've armed themselves.
        hasMelee = self.caller.db.melee
        hasBow = self.caller.db.bow

        # Vars for attack_result logic
        master_of_arms = self.caller.db.master_of_arms
        weapon_level = self.caller.db.weapon_level
        wylding_hand = self.caller.db.wylding_hand

        # Get die result based on master of arms level
        if not hasMelee or not hasBow:
            self.caller.msg("|yBefore you strike you must prepare for combat by using the command setmelee 1 or setbow 1.")
        else:
            # Return die roll based on level in master of arms or wylding hand.
            if wylding_hand:
                die_result = h.wyldingHand(wylding_hand)
            else:
                die_result = h.masterOfArms(master_of_arms)

            weakness = h.weaknessChecker(self.caller.db.weakness)
            dmg_penalty = h.bodyChecker(self.caller.db.body)

            # Get damage result and damage for weapon type
            attack_result = (die_result + weapon_level) - dmg_penalty - weakness
            damage = 2 if self.caller.db.twohanded == True else 1
            target_body = target.db.body

            # Return message to area and caller

            if target.db.body <= 0:
                target.db.body = -4
                self.caller.location.msg_contents(f"|b{self.caller.key} raises their weapon and drives it straight down into {target.key}, ending them.|n")
                self.caller.location.msg_contents(f"|y{target.key} is now dying.")
                target.msg(f"|rYou are now dying and will lose 1 point per round if in combat.|n")
            else:
                self.caller.msg(f"|y{self.caller.key}, you cannot attmept to kill your opponent until they are at 0 body or lower.|n")


class CmdShoot(Command):
    """
    issues a shoot command if armed with a bow.

    Usage:

    shoot <target>

    This will calculate an attack score based on your weapon and master of arms level.
    """

    key = "shoot"
    help_category = "mush"


    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):
        # Init combat helper
        h = Helper()

        # Get weapon level to add to attack
        wylding_hand = self.caller.db.wylding_hand
        weapon_level = self.caller.db.weapon_level
        master_of_arms = self.caller.db.master_of_arms
        hasBow = self.caller.db.bow
        hasMelee = self.caller.db.melee
        bow_penalty = 2

        if not self.args:
            self.caller.msg("|yUsage: shoot <target>|n")
            return

        target = self.caller.search(self.target)

        if not target:
            self.caller.msg("|rThere is nothing here that matches that description.|n")
            return

        if target == self.caller:
            self.caller.msg(f"|r{self.caller}, quit hitting yourself!|n")
            return

        if not hasBow:
            self.caller.msg("|yBefore you can shoot, you must first equip your bow using the command setbow 1.")
        elif hasMelee:
            self.caller.msg("|yBefore you can shoot, you must first unequip your melee weapon using the command setmelee 0.")
        else:

            # Return die roll based on level in master of arms or wylding hand.
            if wylding_hand:
                die_result = h.wyldingHand(wylding_hand)
            else:
                die_result = h.masterOfArms(master_of_arms)

            # Get final attack result and damage
            weakness = h.weaknessChecker(self.caller.db.weakness)
            dmg_penalty = h.bodyChecker(self.caller.db.body)
            attack_result = (die_result + weapon_level) - dmg_penalty - bow_penalty - weakness
            shot_location = h.shotFinder(target.db.targetArray)

            # Compare caller attack_result to target av.
            # If attack_result > target av -> hit, else miss
            if attack_result > target.db.av:
                self.caller.location.msg_contents(f"|b{self.caller.key} lets loose an arrow |n(|g{attack_result}|n)|b straight for {target.key}'s {shot_location} and hits|n (|r{target.db.av}|n), |bdealing|n |y2|n |bdamage!|n")
                if shot_location == "torso":
                    target.db.body = 0
                    self.caller.location.msg_contents(f"|b{target.key} has been fatally wounded and is now bleeding to death. They will soon be unconscious.|n")
                else:
                    target.db.body -= 2
                    target.msg(f"|rYou {shot_location} is now injured and have taken |n|y2l|n|r points of damage.|n")
                    # Send a message to the target, letting them know their body values
                    target.msg(f"|yYour new body value is {target.db.body}|n")
                    if -3 <= target.db.body <= 0:
                        target.msg("|yYou are bleeding profusely from many wounds and can no longer use any active martial skills.\nYou may only use the limbs that have not been injured.|n")
                    elif target.db.body <= -4:
                        target.msg("|rYou are now unconscious and can no longer move of your own volition.|n")
            else:
                # No target armor so subtract from their body total and hit a limb. Add logic from handler above. Leave in body handler in combat handler.
                self.caller.location.msg_contents(f"|b{self.caller.key} lets loose an arrow ({attack_result}) at {target.key}, but it misses.")



"""
Active Martial Skills
"""


class CmdCleave(Command):
    """
    Issues a cleave command.

    Usage:

    cleave <target>

    This will calculate an attack score based on your weapon and master of arms level.
    """

    key = "cleave"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):
        h = Helper()
        "Get level of master of arms for base die roll. Levels of gear give a flat bonus of +1/+2/+3."
        # Get weapon level to add to attack
        weapon_level = self.caller.db.weapon_level
        master_of_arms = self.caller.db.master_of_arms
        hasBow = self.caller.db.bow
        hasMelee = self.caller.db.melee
        wylding_hand = self.caller.db.wyldinghand
        cleavesRemaining = self.caller.db.cleave

        if not self.args:
            self.caller.msg("|yUsage: cleave <target>|n")
            return

        target = self.caller.search(self.target)

        if not target:
            self.caller.msg("|rThere is nothing here that matches that description.|n")
            return

        if target == self.caller:
            self.caller.msg(f"|rDon't cleave yourself {self.caller}!|n")
            return

        # Check for weakness on character
        weakness = h.weaknessChecker(self.caller.db.weakness)

        # Check for equip proper weapon type or weakness
        if weakness:
            self.caller.msg("|rYou are too weak to use this attack.|n")
        elif hasBow:
            self.caller.msg("|yBefore you can attack, you must first unequip your bow using the command setbow 0.|n")
        elif not hasMelee:
            self.caller.msg("|yBefore you can attack, you must first equip a weapon using the command setmelee 1.|n")
        else:
            if cleavesRemaining > 0:
            # Return die roll based on level in master of arms or wylding hand.
                if wylding_hand:
                    die_result = h.wyldingHand(wylding_hand)
                else:
                    die_result = h.masterOfArms(master_of_arms)

                # Decrement amount of cleaves from amount in database
                self.caller.db.cleave -= 1

                # Get final attack result and damage
                dmg_penalty = h.bodyChecker(self.caller.db.body)
                attack_result = (die_result + weapon_level) - dmg_penalty
                shot_location = h.shotFinder(target.db.targetArray)

                # Return attack result message
                self.caller.location.msg_contents(f"|b{self.caller.key} strikes with great ferocity and cleaves {target.key}'s {shot_location}!|n\n|y{self.caller.key}'s attack result is:|n |g{attack_result}|n |yand deals|n |r2|n |ydamage on a successful hit.|n")
            else:
                self.caller.msg("|rYou have 0 cleaves remaining.")


class CmdResist(Command):
    """
    Issues a resist command.

    Usage:

    resist

    This will issue a resist command that adds one to your body, and decrements one from a character's available resists.
    """

    key = "resist"
    help_category = "mush"

    def func(self):
        h = Helper()

        "Get level of master of arms for base die roll. Levels of gear give a flat bonus of +1/+2/+3."
        resistsRemaining = self.caller.db.resist
        master_of_arms = self.caller.db.master_of_arms
        wylding_hand = self.caller.db.wyldinghand
        weapon_level = self.caller.db.weapon_level

        # Check for weakness on character
        weakness = h.weaknessChecker(self.caller.db.weakness)

        # Check for equip proper weapon type or weakness
        if weakness:
            self.caller.msg("|rYou are too weak to use this attack.|n")
        elif resistsRemaining > 0:
        # Return die roll based on level in master of arms or wylding hand.
            if wylding_hand:
                die_result = h.wyldingHand(wylding_hand)
            else:
                die_result = h.masterOfArms(master_of_arms)

            # Decrement amount of cleaves from amount in database
            self.caller.db.resist -= 1

            # Get final attack result and damage
            weakness = h.weaknessChecker(self.caller.db.weakness)
            dmg_penalty = h.bodyChecker(self.caller.db.body)
            attack_result = (die_result + weapon_level) - dmg_penalty - weakness

            # Return attack result message
            self.caller.location.msg_contents(f"|b{self.caller.key} tries to resist the brunt of the attack!|n\n|yIf attack roll is successful, {self.caller.key} negates the effects of the attack and any damage.|n\n|y{self.caller.key}'s attack result is:|n |g{attack_result}|n")
        else:
            self.caller.msg("|yYou have 0 resists remaining.")


class CmdDisarm(Command):
    """
    Issues a disarm command.

    Usage:

    disarm <target>

    This will issue a disarm command that reduces the next amount of damage taken by master of arms level.
    """

    key = "disarm"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):
            h = Helper()

            "Get level of master of arms for base die roll. Levels of gear give a flat bonus of +1/+2/+3."
            disarmsRemaining = self.caller.db.disarm
            master_of_arms = self.caller.db.master_of_arms
            hasBow = self.caller.db.bow
            hasMelee = self.caller.db.melee
            weapon_level = self.caller.db.weapon_level
            wylding_hand = self.caller.db.wyldinghand

            if not self.args:
                self.caller.msg("|yUsage: disarm <target>|n")
                return

            target = self.caller.search(self.target)

            if not target:
                self.caller.msg("|rThere is nothing here that matches that description.|n")
                return

            if target == self.caller:
                self.caller.msg(f"|rDon't disarm yourself {self.caller}!|n")
                return

            # Check for weakness on character
            weakness = h.weaknessChecker(self.caller.db.weakness)

            # Check for equip proper weapon type or weakness
            if weakness:
                self.caller.msg("|rYou are too weak to use this attack.|n")
            elif hasBow:
                self.caller.msg("|yBefore you can attack, you must first unequip your bow using the command setbow 0.")
            elif not hasMelee:
                self.caller.msg("|yBefore you can attack, you must first equip a melee weapon using the command setmelee 1.")
            else:
                if disarmsRemaining > 0:
                # Return die roll based on level in master of arms or wylding hand.
                    if wylding_hand:
                        die_result = h.wyldingHand(wylding_hand)
                    else:
                        die_result = h.masterOfArms(master_of_arms)

                    # Decrement amount of disarms from amount in database
                    self.caller.db.disarm -= 1

                    # Get final attack result and damage
                    weakness = h.weaknessChecker(self.caller.db.weakness)
                    dmg_penalty = h.bodyChecker(self.caller.db.body)
                    attack_result = (die_result + weapon_level) - dmg_penalty - weakness

                    # Return attack result message
                    self.caller.location.msg_contents(f"|b{self.caller.key} tries to counter the next attack by disarming {target.key} for the round.|n\n|y{self.caller.key} may reduce the next amount of damage taken by {master_of_arms}")
                else:
                    self.caller.msg("|rYou have 0 disarms remaining.")


class CmdStun(Command):
    """
    Issues a stun command.

    Usage:

    stun <target>

    This will issue a stun command that denotes a target of an attack will lose their next turn if they are hit.
    """

    key = "stun"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()


    def func(self):
            h = Helper()

            "Get level of master of arms for base die roll. Levels of gear give a flat bonus of +1/+2/+3."
            stunsRemaining = self.caller.db.stun
            master_of_arms = self.caller.db.master_of_arms
            hasBow = self.caller.db.bow
            hasMelee = self.caller.db.melee
            weapon_level = self.caller.db.weapon_level
            wylding_hand = self.caller.db.wyldinghand

            if not self.args:
                self.caller.msg("|yUsage: stun <target>|n")
                return

            target = self.caller.search(self.target)

            if not target:
                self.caller.msg("|rThere is nothing here that matches that description.|n")
                return

            if target == self.caller:
                self.caller.msg(f"|rDon't stun yourself {self.caller}!|n")
                return

            # Check for weakness on character
            weakness = h.weaknessChecker(self.caller.db.weakness)

            # Check for equip proper weapon type or weakness
            if weakness:
                self.caller.msg("|rYou are too weak to use this attack.|n")
            elif hasBow:
                self.caller.msg("|yBefore you can attack, you must first unequip your bow using the command setbow 0.")
            elif not hasMelee:
                self.caller.msg("|yBefore you can attack, you must first equip a melee weapon using the command setmelee 1.")
            else:
                if stunsRemaining > 0:
                # Return die roll based on level in master of arms or wylding hand.
                    if wylding_hand:
                        die_result = h.wyldingHand(wylding_hand)
                    else:
                        die_result = h.masterOfArms(master_of_arms)

                    # Decrement amount of disarms from amount in database
                    self.caller.db.stun -= 1

                    # Get final attack result and damage
                    weakness = h.weaknessChecker(self.caller.db.weakness)
                    dmg_penalty = h.bodyChecker(self.caller.db.body)
                    attack_result = (die_result + weapon_level) - dmg_penalty - weakness

                    # Return attack result message
                    self.caller.location.msg_contents(f"|b{self.caller.key} goes to stun {self.target} such that they're unable to attack for a moment.|n\n|y{self.target.key} may not attack next round if {attack_result} is a successful hit.|n")
                else:
                    self.caller.msg("|rYou have 0 stuns remaining.|n")


class CmdStagger(Command):
    """
    Issues a stagger command.

    Usage:

    stagger <target>

    This will calculate an attack score based on your weapon and master of arms level.
    """

    key = "stagger"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

        if not self.target:
            self.caller.msg("|yUsage: stagger <target>|n")
            return

    def func(self):
        h = Helper()

        "Get level of master of arms for base die roll. Levels of gear give a flat bonus of +1/+2/+3."
        master_of_arms = self.caller.db.master_of_arms
        hasBow = self.caller.db.bow
        hasMelee = self.caller.db.melee
        staggersRemaining = self.caller.db.stagger
        weapon_level = self.caller.db.weapon_level
        wylding_hand = self.caller.db.wyldinghand

        target = self.caller.search(self.target)

        if not target:
            self.caller.msg("|rThere is nothing here that matches that description.|n")
            return

        if target == self.caller:
            self.caller.msg(f"|rDon't stagger yourself {self.caller}!|n")
            return

        # Check for equip proper weapon type
        # Check for weakness on character
        weakness = h.weaknessChecker(self.caller.db.weakness)

        # Check for equip proper weapon type or weakness
        if weakness:
            self.caller.msg("|rYou are too weak to use this attack.|n")
        elif hasBow:
            self.caller.msg("|yBefore you can attack, you must first unequip your bow using the command setbow 0.")
        elif not hasMelee:
            self.caller.msg("|yBefore you can attack, you must first equip a weapon using the command setmelee 1.")
        else:
            if staggersRemaining > 0:
            # Return die roll based on level in master of arms or wylding hand.
                if wylding_hand:
                    die_result = h.wyldingHand(wylding_hand)
                else:
                    die_result = h.masterOfArms(master_of_arms)

                # Decrement amount of cleaves from amount in database
                self.caller.db.stagger -= 1

                # Get final attack result and damage
                weakness = h.weaknessChecker(self.caller.db.weakness)
                dmg_penalty = h.bodyChecker(self.caller.db.body)
                attack_result = (die_result + weapon_level) - dmg_penalty - weakness

                # Return attack result message
                self.caller.location.msg_contents(f"|b{self.caller.key} strikes a devestating blow, attempt to set {self.target} off their guard!|n\n|y{self.caller.key}'s attack result is: {attack_result}, dealing 2 damage on a successful hit.|n")
            else:
                self.caller.msg("|rYou have 0 staggers remaining.|n")


class CmdDisengage(Command):
    """
    disengage from an enemy

    Usage:
      disengage

    Disengages from the given target.
    """
    key = "disengage"
    aliases = ["disengage", "escape", "flee"]
    help_category = "combat"

    def func(self):
        "Implements the command"
        # To disengage
        self.caller.msg("|yYou disengage from the attack.|n")
        self.caller.location.msg_contents(f"|b{self.caller} backs away and then disengages from the fight.|n")

"""
Knight commands
"""

class CmdBattlefieldCommander(Command):
    """
    Usage: bolster <speech>

    Use the bolster command followed by a speech to give all in the room 1 tough.
    """
    key = "bolster"
    aliases = ["battlefieldcommander"]
    help_category = "combat"

    def parse(self):
        "Very trivial parser"
        self.speech = self.args.strip()

    def func(self):
        if not self.args:
            self.caller.msg("|yUsage: bolster <target>|n")
            return

        bolsterRemaining = self.caller.db.battlefieldcommander

        if bolsterRemaining > 0:
            self.caller.location.msg_contents(f"|bAmidst the chaos of the fighting, {self.caller.key} shouts so all can hear,|n |r{self.speech}|n.\n|yEveryone in the room may now add 1 Tough to their av, using the command settough #|n |r(Should be one more than your current value).|n")
            self.caller.db.battlefieldcommander -= 1
        else:
            self.caller.msg("|rYou have no uses of your battlefield commander ability remaining.|n")

class CmdRally(Command):
    """
    Usage: rally <speech>

    Use the rally command followed by a speech to remove a fear effect from those in the room.
    """
    key = "rally"
    help_category = "combat"

    def parse(self):
        "Very trivial parser"
        self.speech = self.args.strip()

    def func(self):
        if not self.args:
            self.caller.msg("|yUsage: rally <speech>|n")
            return

        rallyRemaining = self.caller.db.rally

        if rallyRemaining > 0:
            self.caller.location.msg_contents(f"|b{self.caller.key} shouts so all can hear,|n |r{self.speech}|n.\n|yEveryone in the room now feels unafraid. Cancel the fear effect.|n")
            self.caller.db.rally -= 1
        else:
            self.caller.msg("|rYou have no uses of your rally ability remaining.|n")
