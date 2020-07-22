# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper

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
        h = Helper(self.caller)

        # Run logic for strike command
        if self.caller.db.combat_turn:

            # Return db stats needed to calc melee results
            combat_stats = h.getMeleeCombatStats(self.caller)

            # Get die result based on master of arms level
            if combat_stats.get("melee", 0):
                self.caller.msg("|540Before you can shoot, you must first unequip your melee weapon using the command setmelee 0.")
                return

            elif not combat_stats.get("bow", 0):
                self.caller.msg("|540Before you can shoot, you must first equip your bow using the command setbow 1.")
                return

            else:
                # Check for and error handle designated target
                target = h.targetHandler(self.target)
                
                # Use parsed args in combat loop
                loop = CombatLoop(self.caller, target)
                loop.resolveCommand()

                # Get damage result and damage for weapon type
                attack_result = (die_result + combat_stats.get("weapon_level", 0)) - combat_stats.get("dmg_penalty", 0) - combat_stats.get("weakness", 0) - combat_stats.get("bow_penalty", 0)
                target_av = target.db.av
                shot_location = h.shotFinder(target.db.targetArray)

                # Compare caller attack_result to target av.
                # If attack_result > target av -> hit, else miss
                if attack_result >= target.db.av:
                    self.caller.location.msg_contents(f"|015{self.caller.key} lets loose an arrow |n(|020{attack_result}|n)|015 straight for {target.key}'s {shot_location} and hits|n (|400{target.db.av}|n), |015dealing|n |5401|n |015damage!|n")
                    if shot_location == "torso":
                        if target.db.body > 0:
                            target.db.body = 0
                            self.caller.location.msg_contents(f"|015{target.key} has been fatally wounded and is now bleeding to death. They will soon be unconscious.|n")
                        else:
                            target.db.body -= 1
                            target.msg(f"|540Your new body value is {target.db.body}|n")
                    else:
                        target.db.body -= 1
                        target.msg(f"|400You {shot_location} is now injured and have taken |n|5402l|n|400 points of damage.|n")
                        # Send a message to the target, letting them know their body values
                        target.msg(f"|540Your new body value is {target.db.body}|n")
                        if -3 <= target.db.body <= 0:
                            target.msg("|540You are bleeding profusely from many wounds and can no longer use any active martial skills.\nYou may only use the limbs that have not been injured.|n")
                            target.location.msg_contents(f"|015{target.key} is bleeding profusely from many wounds and will soon lose consciousness.|n")
                        elif target.db.body <= -4:
                            target.msg("|400You are now unconscious and can no longer move of your own volition.|n")
                            target.location.msg_contents(f"|015{target.key} does not seem to be moving.|n")
                else:
                    # No target armor so subtract from their body total and hit a limb. Add logic from handler above. Leave in body handler in combat handler.
                    self.caller.location.msg_contents(f"|015{self.caller.key} lets loose an arrow |n(|400{attack_result}|n)|015 at {target.key}|n(|020{target.db.av}|n)|015, but it misses.|n")

                # Clean up
                # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                loop.combatTurnOff(self.caller)
                loop.cleanup()

        else:
            self.msg("You need to wait until it is your turn before you are able to act.")
            return
