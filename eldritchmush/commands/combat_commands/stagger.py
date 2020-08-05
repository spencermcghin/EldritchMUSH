# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper

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
            self.caller.msg("|540Usage: stagger <target>|n")
            return

    def func(self):
        h = Helper()

        "Get level of master of arms for base die roll. Levels of gear give a flat bonus of +1/+2/+3."
        master_of_arms = self.caller.db.master_of_arms
        hasBow = self.caller.db.bow
        hasMelee = self.caller.db.melee
        staggersRemaining = self.caller.db.stagger
        weapon_level = h.weaponValue(self.caller.db.weapon_level)
        hasTwoHanded = self.caller.db.twohanded
        stagger_penalty = 2

        wylding_hand = self.caller.db.wyldinghand

        target = self.caller.search(self.target)

        if not target:
            self.caller.msg("|400There is nothing here that matches that description.|n")
            return

        if target == self.caller:
            self.caller.msg(f"|400Don't stagger yourself {self.caller}, silly!|n")
            return

        if target.db.body is None:
            self.caller.msg("|400You had better not try that.")
            return

        # Check for equip proper weapon type
        # Check for weakness on character
        weakness = h.weaknessChecker(self.caller.db.weakness)

        # Check for equip proper weapon type or weakness
        if weakness:
            self.caller.msg("|400You are too weak to use this attack.|n")
        elif hasBow:
            self.caller.msg("|540Before you can attack, you must first unequip your bow using the command setbow 0.")
        elif not hasMelee or not hasTwoHanded:
            self.caller.msg("|540Before you can attack, you must first equip a weapon using the command setmelee 1 or settwohanded 1.")
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
                attack_result = (die_result + weapon_level) - dmg_penalty - weakness - stagger_penalty

                # Return attack result message
                if attack_result > target.db.av:
                    self.caller.location.msg_contents(f"|015{self.caller.key}|n (|020{attack_result}|n) |015staggers {target.key}|n (|400{target.db.av}|n) |015, putting them off their guard.|n")
                    # subtract damage from corresponding target stage (shield_value, armor, tough, body)
                    new_av = h.damageSubtractor(2, target)
                    # Update target av to new av score per damageSubtractor
                    target.db.av = new_av
                    target.msg(f"|540Your new total Armor Value is {new_av}:\nShield: {target.db.shield}\nArmor Specialist: {target.db.armor_specialist}\nArmor: {target.db.armor}\nTough: {target.db.tough}|n")

                elif attack_result < target.db.av:
                    self.caller.location.msg_contents(f"|015{self.caller.key} attempts|n (|400{attack_result}|n)|015 to stagger {target.key}|n (|020{target.db.av}|n)|015, but fumbles their attack.|n")
            else:
                self.caller.msg("|400You have 0 staggers remaining or do not have the skill.|n")
