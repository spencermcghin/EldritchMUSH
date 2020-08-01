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

        # Use parsed args in combat loop
        loop = CombatLoop(self.caller, target)
        loop.resolveCommand()

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

                # Check if damage bonus comes from fayne or master_of_arms
                die_result = h.fayneChecker(combat_stats.get("master_of_arms", 0), combat_stats.get("wylding_hand", 0))

                # Get damage result
                attack_result = (die_result + combat_stats.get("weapon_level", 0)) - combat_stats.get("dmg_penalty", 0) - combat_stats.get("weakness", 0) - combat_stats.get("bow_penalty", 0)
                target_av = target.db.av
                shot_location = h.shotFinder(target.db.targetArray)
                bow_damage = 1

                # Compare caller attack_result to target av.
                # If attack_result > target av -> hit, else miss
                if h.canFight(self.caller):
                    if h.isAlive(target):
                        if attack_result >= target.db.av:
                            self.caller.location.msg_contents(f"|015{self.caller.key} lets loose an arrow |n(|020{attack_result}|n)|015 straight for {target.key}'s {shot_location} and hits|n (|400{target.db.av}|n), |015dealing|n |5401|n |015damage!|n")
                            if shot_location == "torso" and target.db.body > 0:
                                target.db.body = 0
                                self.caller.location.msg_contents(f"|015{target.key} has been fatally wounded and is now bleeding to death. They will soon be unconscious.|n")
                            else:
                                h.deathSubtractor(bow_damage, target, self.caller)
                        else:
                            # No target armor so subtract from their body total and hit a limb. Add logic from handler above. Leave in body handler in combat handler.
                            self.caller.location.msg_contents(f"|015{self.caller.key} lets loose an arrow at {target.key}|n(|020{target.db.av}|n)|015, but it misses.|n")
                    else:
                        self.msg(f"{target.key} is dead. You only further mutiliate their body.")
                        self.caller.location.msg_contents(f"{self.caller.key} further mutilates the corpse of {target.key}.")
                else:
                    self.msg("You are too injured to act.")
                # Clean up
                # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                loop.combatTurnOff(self.caller)
                loop.cleanup()
        else:
            self.msg("You need to wait until it is your turn before you are able to act.")
            return
