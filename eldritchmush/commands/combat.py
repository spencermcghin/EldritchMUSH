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
            self.caller.msg("Usage: strike <target>")
            return

        target = self.caller.search(self.target)

        if not target:
            self.caller.msg("Usage: strike <target>")
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

            # Return message to area and caller
            if target.db.av:
                self.caller.location.msg_contents(f"|b{self.caller.key} strikes deftly at {target.key}!|n\n|yTheir attack result is:|n |g{attack_result}|n |yand deals|n |r{damage}|n |ydamage on a successful hit.|n")
            else:
                self.caller.location.msg_contents(f"|b{self.caller.key} strikes deftly at {target.key}'s {shot_location}!|n\n|yTheir attack result is:|n |g{attack_result}|n |yand deals|n |r{damage}|n |ydamage on a successful hit.|n")

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
            self.caller.msg("Usage: kill <target>")
            return

        target = self.caller.search(self.target)

        if not target:
            self.caller.msg("Usage: kill <target>")
            return

        if target == self.caller:
            self.caller.msg(f"|r{self.caller}, please don't kill yourself.|n")
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
            target_body = target.db.body

            # Return message to area and caller
            if not target.db.body:
                self.caller.location.msg_contents(f"|b{self.caller.key} raises their weapon and attempts a killing blow on {target.key}.|n\n|yTheir attack result is:|n |g{attack_result}.|n")
            else:
                self.caller.msg(f"|y{self.caller.key}, you cannot kill your opponent until they are at 0 body or lower.|n")


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
            self.caller.msg("Usage: shoot <target>")
            return

        target = self.caller.search(self.target)

        if not target:
            self.caller.msg("There is nothing here that matches that description.")
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

            # Return message to area and caller
            self.caller.location.msg_contents(f"|b{self.caller.key} lets loose an arrow straight for {target.key}'s {shot_location}!|n\n|yTheir attack result is:|n |g{attack_result}|n |yand deals|n |r2|n |ydamage on a successful hit.|n")




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
            self.caller.msg("Usage: cleave <target>")
            return

        target = self.caller.search(self.target)

        if not target:
            self.caller.msg("There is nothing here that matches that description.")
            return

        if target == self.caller:
            self.caller.msg(f"|rDon't cleave yourself {self.caller}!|n")
            return

        # Check for weakness on character
        weakness = h.weaknessChecker(self.caller.db.weakness)

        # Check for equip proper weapon type or weakness
        if weakness:
            self.caller.msg("|yYou are too weak to use this attack.|n")
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
                self.caller.location.msg_contents(f"|b{self.caller.key} strikes with great ferocity and cleaves {target.key}'s {shot_location}!|n\n|yTheir attack result is:|n |g{attack_result}|n |yand deals|n |r2|n |ydamage on a successful hit.|n")
            else:
                self.caller.msg("|yYou have 0 cleaves remaining.")


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
            self.caller.msg("|yYou are too weak to use this attack.|n")
        elif resistsRemaining > 0:
        # Return die roll based on level in master of arms or wylding hand.
            if wylding_hand:
                die_result = h.wyldingHand(wylding_hand)
            else:
                die_result = h.masterOfArms(master_of_arms)

            # Decrement amount of cleaves from amount in database
            self.caller.db.resist -= 1

            # Get final attack result and damage
            weakness = h.weaknessChecker(self.caller.db.weakness, self.caller.cmdstring)
            dmg_penalty = h.bodyChecker(self.caller.db.body)
            attack_result = (die_result + weapon_level) - dmg_penalty - weakness

            # Return attack result message
            self.caller.location.msg_contents(f"|b{self.caller.key} tries to resist the brunt of the attack!|n\n|yIf attack roll is successful, they negate the effects of the attack and any damage.|n\n|yTheir attack result is:|n |g{attack_result}|n")
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

            if not self.args:
                self.caller.msg("Usage: disarm <target>")
                return

            target = self.caller.search(self.target)

            if not target:
                self.caller.msg("There is nothing here that matches that description.")
                return

            if target == self.caller:
                self.caller.msg(f"|rDon't disarm yourself {self.caller}!|n")
                return

            # Check for weakness on character
            weakness = h.weaknessChecker(self.caller.db.weakness)

            # Check for equip proper weapon type or weakness
            if weakness:
                self.caller.msg("|yYou are too weak to use this attack.|n")
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
                    weakness = h.weaknessChecker(self.caller.db.weakness, self.caller.cmdstring)
                    dmg_penalty = h.bodyChecker(self.caller.db.body)
                    attack_result = (die_result + weapon_level) - dmg_penalty - weakness

                    # Return attack result message
                    self.caller.location.msg_contents(f"|b{self.caller.key} tries to counter the next attack by disarming {target.key} for the round.|n\n|yReduce the next amount of damage taken by {master_of_arms}")
                else:
                    self.caller.msg("|yYou have 0 disarms remaining.")


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

            # Check for weakness on character
            weakness = h.weaknessChecker(self.caller.db.weakness)

            # Check for equip proper weapon type or weakness
            if weakness:
                self.caller.msg("|yYou are too weak to use this attack.|n")
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
                    weakness = h.weaknessChecker(self.caller.db.weakness, self.caller.cmdstring)
                    dmg_penalty = h.bodyChecker(self.caller.db.body)
                    attack_result = (die_result + weapon_level) - dmg_penalty - weakness

                    # Return attack result message
                    self.caller.location.msg_contents(f"|b{self.caller.key} goes to stun {target.key} such that they're unable to attack for a moment.|n\n|y{target.key} may not attack next round if {attack_result} is a successful hit.|n")
                else:
                    self.caller.msg("|yYou have 0 stuns remaining.|n")


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

    def func(self):
        h = Helper()

        "Get level of master of arms for base die roll. Levels of gear give a flat bonus of +1/+2/+3."
        master_of_arms = self.caller.db.master_of_arms
        hasBow = self.caller.db.bow
        hasMelee = self.caller.db.melee
        staggersRemaining = self.caller.db.stagger
        weapon_level = self.caller.db.weapon_level


        # Check for equip proper weapon type
        # Check for weakness on character
        weakness = h.weaknessChecker(self.caller.db.weakness)

        # Check for equip proper weapon type or weakness
        if weakness:
            self.caller.msg("|yYou are too weak to use this attack.|n")
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
                weakness = h.weaknessChecker(self.caller.db.weakness, self.cmdstring)
                dmg_penalty = h.bodyChecker(self.caller.db.body)
                attack_result = (die_result + weapon_level) - dmg_penalty - weakness

                # Return attack result message
                self.caller.location.msg_contents(f"|b{self.caller.key} strikes a devestating blow, attempt to set {target.key} off their guard!|n\n|y{self.caller.key}'s attack result is: {attack_result}, dealing 2 damage on a successful hit.|n")
            else:
                self.caller.msg("|yYou have 0 staggers remaining.")


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
        self.caller.msg("You disengage from the attack!")

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
            self.caller.msg("Usage: bolster <target>")
            return

        bolsterRemaining = self.caller.db.battlefieldcommander

        if bolsterRemaining > 0:
            self.caller.location.msg_contents(f"|bAmidst the chaos of the fighting, {self.caller.key} shouts so all can hear,|n |r{self.speech}|n.\n|yEveryone in the room may now add 1 Tough to their av, using the command settough #|n |r(Should be one more than your current value).|n")
            self.caller.db.battlefieldcommander -= 1
        else:
            self.caller.msg("|yYou have no uses of your battlefield commander ability remaining.|n")

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
            self.caller.msg("Usage: rally <speech>")
            return

        rallyRemaining = self.caller.db.rally

        if rallyRemaining > 0:
            self.caller.location.msg_contents(f"|b{self.caller.key} shouts so all can hear,|n |r{self.speech}|n.\n|yEveryone in the room now feels unafraid. Cancel the fear effect.|n")
            self.caller.db.rally -= 1
        else:
            self.caller.msg("|yYou have no uses of your rally ability remaining.|n")
