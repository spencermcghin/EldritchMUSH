# Local imports
from evennia import Command
from commands.combat_commands.strike_command.strike_logic import Strike
from world.combat_loop import CombatLoop
from commands.combat import Helper


class CmdStrike(Command):
    """
    issues an attack

    Usage:

    strike <self.target>

    This will calculate an attack score based on your weapon and master of arms level.
    """

    key = "strike"
    aliases = ["hit", "slash", "bash", "punch"]
    help_category = "combat"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

        # Check for correct command
        if not self.args:
            self.caller.msg("|540Usage: strike <target>|n")
            return

        # Check for designated self.target
        target = self.caller.search(self.target)

        if not self.target:
            self.caller.msg("|540Usage: strike <target>|n")
            return

        # Error handling for
        if self.target == self.caller:
            self.caller.msg(f"|400{self.caller.key}, quit hitting yourself!|n")
            return

        # Error handling for non-character objects
        if self.target.db.body is None:
            self.caller.msg("|400You had better not try that.")
            return


    def func(self):

        # Use parsed args in combat loop
        loop = CombatLoop(self.caller, self.target)
        loop.resolveCommand()


        # Run logic for strike command
        if self.caller.db.combat_turn:
            # Init combat helper class for logic
            h = Helper()

            # Get hasMelee for character to check that they've armed themselves.
            hasMelee = self.caller.db.melee

            # Vars for attack_result logic
            master_of_arms = self.caller.db.master_of_arms
            weapon_level = h.weaponValue(self.caller.db.weapon_level)
            wylding_hand = self.caller.db.wylding_hand

            # Get die result based on master of arms level
            if not hasMelee:
                self.caller.msg("|540Before you strike you must equip a melee weapon using the command setmelee 1.")
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
                target_av = self.target.db.av
                shot_location = h.shotFinder(self.target.db.targetArray)

                # Compare self.caller attack_result to self.target av.
                # If attack_result > self.target av -> hit, else miss
                if attack_result >= target_av:
                    # if self.target has any more armor points left go through the damage subtractor
                    if target_av:
                        self.caller.location.msg_contents(f"|015{self.caller.key} strikes deftly|n (|020{attack_result}|n) |015at {self.target.key} and hits|n (|400{self.target_av}|n), |015dealing|n |540{damage}|n |015damage!|n")
                        # subtract damage from corresponding self.target stage (shield_value, armor, tough, body)
                        new_av = h.damageSubtractor(damage, self.target)
                        # Update self.target av to new av score per damageSubtractor
                        self.target.db.av = new_av
                        self.target.msg(f"|540Your new total Armor Value is {new_av}:\nShield: {self.target.db.shield}\nArmor Specialist: {self.target.db.armor_specialist}\nArmor: {self.target.db.armor}\nTough: {self.target.db.tough}|n")
                    else:
                        # No self.target armor so subtract from their body total and hit a limb. Add logic from handler above. Leave in body handler in combat handler.
                        self.caller.location.msg_contents(f"|015{self.caller.key} strikes deftly|n (|020{attack_result}|n) |015at {self.target.key} and hits |n(|400{self.target_av}|n)|015, injuring their {shot_location} and dealing|n |540{damage}|n |015damage!|n.")
                        if shot_location == "torso":
                            if self.target.db.body > 0:
                                self.target.db.body = 0
                                self.caller.location.msg_contents(f"|015{self.target.key} has been fatally wounded and is now bleeding to death. They will soon be unconscious.|n")
                            else:
                                self.target.db.body -= damage
                                self.target.msg(f"|540Your new body value is {self.target.db.body}|n")
                        else:
                            self.target.db.body -= damage
                            self.target.msg(f"|400You {shot_location} is now injured and have taken |n|540{damage}|n|400 points of damage.|n")
                            # Send a message to the self.target, letting them know their body values
                            self.target.msg(f"|540Your new body value is {self.target.db.body}|n")
                            if -3 <= self.target.db.body <= 0:
                                self.target.msg("|540You are bleeding profusely from many wounds and can no longer use any active martial skills.\nYou may only use the limbs that have not been injured.|n")
                                self.target.location.msg_contents(f"|015{self.target.key} is bleeding profusely from many wounds and will soon lose consciousness.|n")
                            elif self.target.db.body <= -4:
                                self.target.msg("|400You are now unconscious and can no longer move of your own volition.|n")
                                self.target.location.msg_contents(f"|015{self.target.key} does not seem to be moving.|n")
                else:
                    self.caller.location.msg_contents(f"|015{self.caller.key} swings wildly|n |400{attack_result}|n|015, missing {self.target.key} |n|020{self.target_av}|n")
        else:
            self.caller.msg("You need to wait until it is your turn before you are able to act.")
            return

        # Clean up
        # Set self.caller's combat_turn to 0. Can no longer use combat commands.
        loop.combatTurnOff(self.caller)

        # Check for number of elements in the combat loop
        if loop.getLoopLength() > 1:
            # Get character at next index and set their combat_round to 1
            nextTurn = loop.gotoNext()
            loop.combatTurnOn(nextTurn)
            nextTurn.msg(f"{nextTurn.key}, it's now your turn. Please enter a combat command, or disengage from combat.")
        else:
            loop.removeFromLoop(self.caller)
            self.caller.msg(f"Combat is over. You have been removed from the combat loop for {loop.current_room}.")
            # Change self.callers combat_turn to 1 so they can attack again.
            strike.combatTurnOn(self.caller)
