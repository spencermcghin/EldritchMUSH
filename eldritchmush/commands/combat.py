from evennia import Command
from evennia import CmdSet
from evennia import default_cmds
from evennia import create_script
from commands import command

import random

Make a reaondom save

"""
These are attack commands
"""

class CmdStrike(Command):
    """
    issues an attack

    Usage:

    strike <target>

    This will calculate an attack score based on your weapon and master of arms level.
    """

    key = "strike"
    aliases = ["hit", "slash", "bash"]
    help_category = "combat"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()


    def func(self):
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
            # if master_of_arms == 0:
            #     die_result = random.randint(1,6)
            # elif master_of_arms == 1:
            #     die_result = random.randint(1,10)
            # elif master_of_arms == 2:
            #     die_result = random.randint(1,6) + random.randint(1,6)
            # elif master_of_arms == 3:
            #     die_result = random.randint(1,8) + random.randint(1,8)
            if wylding_hand:
                die_result = wyldingHand(wylding_hand)
            else:
                die_result = masterOfArms(master_of_arms)

            # Get final attack result
            attack_result = die_result + weapon_level

            # Get damage value based on weapon type
            damage = 2 if self.caller.db.twohanded == True else 1

            # Return message to area and caller
            string = f"|b{self.caller.key} strikes deftly at {target.key}!|n"

            self.caller.location.msg_contents(string)

            self.caller.msg(f"|bYou strike deftly at your target.|n\n|yYour attack result is:|n |g{attack_result}|n |yand deals|n |r{damage}|n |ydamage on a successful hit.|n")

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


class CmdShoot(Command):
    """
    issues a shoot command if armed with a bow.

    Usage:

    shoot

    This will calculate an attack score based on your weapon and master of arms level.
    """

    key = "shoot"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):
        master_of_arms = self.caller.db.master_of_arms
        hasBow = self.caller.db.bow
        hasMelee = self.caller.db.melee
        bow_penalty = 2

        if not self.args:
            self.caller.msg("Usage: shoot <target>")
            return

        target = self.caller.search(self.target)

        if not target:
            self.caller.msg("Usage: shoot <target>")
            return

        if target == self.caller:
            self.caller.msg(f"|r{self.caller}, quit hitting yourself!|n")
            return

        if not hasBow:
            self.caller.msg("|yBefore you can shoot, you must first equip your bow using the command setbow 1.")
        elif hasMelee:
            self.caller.msg("|yBefore you can shoot, you must first unequip your melee weapon using the command setmelee 0.")
        else:
            if master_of_arms == 0:
                die_result = random.randint(1,6)
            elif master_of_arms == 1:
                die_result = random.randint(1,10)
            elif master_of_arms == 2:
                die_result = random.randint(1,6) + random.randint(1,6)
            elif master_of_arms == 3:
                die_result = random.randint(1,8) + random.randint(1,8)

            self.caller.db.attack_result = die_result

            # Get weapon level to add to attack
            weapon_level = self.caller.db.weapon_level

            # Return message to area and caller
            string = f"|b{self.caller.key} lets loose an arrow straight for {target.key}!|n"

            self.caller.location.msg_contents(string)

            self.caller.msg(f"|bYou take aim and let loose an arrow.|n\n|yYour attack result is:|n |g{(die_result + weapon_level) - bow_penalty}|n |yand deals|n |r2|n |ydamage on a successful hit.|n")


class CmdCleave(Command):
    """
    Issues a cleave command.

    Usage:

    cleave

    This will calculate an attack score based on your weapon and master of arms level.
    """

    key = "cleave"
    help_category = "mush"

    def func(self):
            "Get level of master of arms for base die roll. Levels of gear give a flat bonus of +1/+2/+3."
            master_of_arms = self.caller.db.master_of_arms
            hasBow = self.caller.db.bow
            hasMelee = self.caller.db.melee
            cleavesRemaining = self.caller.db.cleave

            # Check for equip proper weapon type
            if hasBow:
                self.caller.msg("|yBefore you can attack, you must first unequip your bow using the command setbow 0.")
            elif not hasMelee:
                self.caller.msg("|yBefore you can attack, you must first equip a weapon using the command setmelee 1.")
            else:
                if cleavesRemaining > 0:
                    if master_of_arms == 0:
                        die_result = random.randint(1,6)
                    elif master_of_arms == 1:
                        die_result = random.randint(1,10)
                    elif master_of_arms == 2:
                        die_result = random.randint(1,6) + random.randint(1,6)
                    elif master_of_arms == 3:
                        die_result = random.randint(1,8) + random.randint(1,8)

                    self.caller.db.attack_result = die_result

                    # Get weapon level to add to attack
                    weapon_level = self.caller.db.weapon_level

                    # Decrement amount of cleaves from amount in database
                    self.caller.db.cleave -= 1

                    # Return attack result message
                    self.caller.msg(f"|rYou strike with great ferocity and cleave your foe!|n\n|gYour attack result is: {die_result + weapon_level}, dealing 2 damage and bypassing target Armor Value on a successful hit.|n\nRoll: {die_result}\nWeapon Level: {weapon_level}")
                else:
                    self.caller.msg("|yYou have 0 cleaves remaining. To add more please return to the chargen room.")


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
            "Get level of master of arms for base die roll. Levels of gear give a flat bonus of +1/+2/+3."
            resistsRemaining = self.caller.db.resist

            if resistsRemaining > 0:
                # Decrement amount of cleaves from amount in database
                self.caller.db.body += 1
                self.caller.db.resist -= 1

                # Return attack result message
                self.caller.msg(f"|rYou deftly manage to resist the brunt of the attack.|n\n|gNegate the effects of the last attack and gain a point of body.|n\nBody Point Total: {self.caller.db.body}")
            else:
                self.caller.msg("|yYou have 0 resists remaining. To add more please return to the chargen room.")

class CmdDisarm(Command):
    """
    Issues a disarm command.

    Usage:

    disarm

    This will issue a disarm command that reduces the next amount of damage taken by master of arms level.
    """

    key = "disarm"
    help_category = "mush"

    def func(self):
            "Get level of master of arms for base die roll. Levels of gear give a flat bonus of +1/+2/+3."
            disarmsRemaining = self.caller.db.disarm
            master_of_arms = self.caller.db.master_of_arms
            hasBow = self.caller.db.bow
            hasMelee = self.caller.db.melee

            # Check for equip proper weapon type
            if hasBow:
                self.caller.msg("|yBefore you can attack, you must first unequip your bow using the command setbow 0.")
            elif not hasMelee:
                self.caller.msg("|yBefore you can attack, you must first equip a melee weapon using the command setmelee 1.")
            else:
                if disarmsRemaining > 0:
                    # Decrement amount of disarms from amount in database
                    self.caller.db.disarm -= 1

                    # Return attack result message
                    self.caller.msg(f"|rYou counter the next attack by disarming your opponent for the round.|n\n|gReduce the next amount of damage taken by {master_of_arms}")
                else:
                    self.caller.msg("|yYou have 0 disarms remaining. To add more please return to the chargen room.")


class CmdStun(Command):
    """
    Issues a stun command.

    Usage:

    stun

    This will issue a stun command that denotes a target of an attack will lose their next turn if they are hit.
    """

    key = "stun"
    help_category = "mush"

    def func(self):
            "Get level of master of arms for base die roll. Levels of gear give a flat bonus of +1/+2/+3."
            stunsRemaining = self.caller.db.stun
            master_of_arms = self.caller.db.master_of_arms
            hasBow = self.caller.db.bow
            hasMelee = self.caller.db.melee

            # Check for equip proper weapon type
            if hasBow:
                self.caller.msg("|yBefore you can attack, you must first unequip your bow using the command setbow 0.")
            elif not hasMelee:
                self.caller.msg("|yBefore you can attack, you must first equip a melee weapon using the command setmelee 1.")
            else:
                if stunsRemaining > 0:
                    # Decrement amount of disarms from amount in database
                    self.caller.db.stun -= 1

                    # Return attack result message
                    self.caller.msg(f"|rYou're able to stun your opponent such that they're unable to attack for a moment.|n\n|gThe target of your attack may not attack next round.")
                else:
                    self.caller.msg("|yYou have 0 stuns remaining. To add more please return to the chargen room.")

class CmdStagger(Command):
    """
    Issues a stagger command.

    Usage:

    stagger

    This will calculate an attack score based on your weapon and master of arms level.
    """

    key = "stagger"
    help_category = "mush"

    def func(self):
            "Get level of master of arms for base die roll. Levels of gear give a flat bonus of +1/+2/+3."
            master_of_arms = self.caller.db.master_of_arms
            hasBow = self.caller.db.bow
            hasMelee = self.caller.db.melee
            staggersRemaining = self.caller.db.stagger

            # Check for equip proper weapon type
            if hasBow:
                self.caller.msg("|yBefore you can attack, you must first unequip your bow using the command setbow 0.")
            elif not hasMelee:
                self.caller.msg("|yBefore you can attack, you must first equip a weapon using the command setmelee 1.")
            else:
                if staggersRemaining > 0:
                    if master_of_arms == 0:
                        die_result = random.randint(1,6)
                    elif master_of_arms == 1:
                        die_result = random.randint(1,10)
                    elif master_of_arms == 2:
                        die_result = random.randint(1,6) + random.randint(1,6)
                    elif master_of_arms == 3:
                        die_result = random.randint(1,8) + random.randint(1,8)

                    self.caller.db.attack_result = die_result

                    # Get weapon level to add to attack
                    weapon_level = self.caller.db.weapon_level

                    # Decrement amount of cleaves from amount in database
                    self.caller.db.stagger -= 1

                    # Return attack result message
                    self.caller.msg(f"|rYou strike, setting your opponent off their guard!|n\n|gYour attack result is: {(die_result + weapon_level) - 2}, dealing 2 damage on a successful hit.|n\nRoll: {die_result}\nWeapon Level: {weapon_level}")
                else:
                    self.caller.msg("|yYou have 0 staggers remaining. To add more please return to the chargen room.")

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
        self.caller.msg("You disengage from the attack!")



"""
Combat command set
"""

class CombatCmdSet(CmdSet):
    key = "combat_cmdset"
    mergetype = "Replace"
    priority = 10
    no_exits = True

    def at_cmdset_creation(self):
        self.add(default_cmds.CmdPose())
        self.add(default_cmds.CmdSay())
        self.add(CmdShoot())
        self.add(CmdCleave())
        self.add(CmdResist())
        self.add(CmdDisarm())
        self.add(CmdStun())
        self.add(CmdStagger())
        self.add(CmdStrike())
        self.add(CmdDisengage())
        self.add(command.SetBow())
        self.add(command.SetMelee())
