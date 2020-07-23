
# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper

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
        weapon_level = h.weaponValue(self.caller.db.weapon_level)

        master_of_arms = self.caller.db.master_of_arms
        hasBow = self.caller.db.bow
        hasMelee = self.caller.db.melee
        wylding_hand = self.caller.db.wyldinghand
        cleavesRemaining = self.caller.db.cleave
        hasTwoHanded = self.caller.db.twohanded

        if not self.args:
            self.caller.msg("|540Usage: cleave <target>|n")
            return

        target = self.caller.search(self.target)

        if not target:
            self.caller.msg("|400There is nothing here that matches that description.|n")
            return

        if target == self.caller:
            self.caller.msg(f"|400Don't cleave yourself {self.caller}!|n")
            return

        if target.db.body is None:
            self.caller.msg("|400You had better not try that.")
            return

        # Check for weakness on character
        weakness = h.weaknessChecker(self.caller.db.weakness)

        # Check for equip proper weapon type or weakness
        if weakness:
            self.caller.msg("|400You are too weak to use this attack.|n")
        elif hasBow:
            self.caller.msg("|540Before you can attack, you must first unequip your bow using the command setbow 0.|n")
        elif not hasTwoHanded:
            self.caller.msg("|540Before you can attack, you must first equip a weapon using the command settwohanded 1.|n")
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

                if attack_result >= target.db.av:
                    self.caller.location.msg_contents(f"|015{self.caller.key} strikes|n (|020{attack_result}|n) |015with great ferocity and cleaves {target.key}'s {shot_location}|n (|400{target.db.av}|n)|015! dealing|n |5402|n |015damage|n.")
                    if shot_location == "torso":
                        if target.db.body > 0:
                            target.db.body = 0
                            self.caller.location.msg_contents(f"|015{target.key} has been fatally wounded and is now bleeding to death. They will soon be unconscious.|n")
                        else:
                            target.db.body -= 2
                            target.msg(f"|540Your new body value is {target.db.body}|n")
                    else:
                        target.db.body -= 2
                        target.msg(f"|400You {shot_location} is now injured and have taken |n|5402l|n|400 points of damage.|n")
                        # Send a message to the target, letting them know their body values
                        target.msg(f"|540Your new body value is {target.db.body}|n")
                        if -3 <= target.db.body <= 0:
                            target.location.msg_contents(f"|015{target.key} is bleeding profusely from many wounds and will soon lose consciousness.|n")
                            target.msg("|540You are bleeding profusely from many wounds and can no longer use any active martial skills.\nYou may only use the limbs that have not been injured.|n")
                        elif target.db.body <= -4:
                            target.msg("|400You are now unconscious and can no longer move of your own volition.|n")
                            target.location.msg_contents(f"|015{target.key} does not seem to be moving.|n")
                else:
                    # No target armor so subtract from their body total and hit a limb. Add logic from handler above. Leave in body handler in combat handler.
                    self.caller.location.msg_contents(f"|015{self.caller.key} strikes with great ferocity|n (|400{attack_result}|n)|015 at {target.key}|n(|020{target.db.av}|n)|015, but it misses.|n")
            else:
                self.caller.msg("|400You have 0 cleaves remaining or do not have the skill.")
