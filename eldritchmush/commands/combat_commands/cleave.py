
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
        if not self.args:
            self.caller.msg("|540Usage: cleave <target>|n")
            return

        # Init combat helper functions
        h = Helper(self.caller)

        # Get target if there is one
        target = self.caller.search(self.target)

        # Run logic for cleave command
        if self.caller.db.combat_turn:

            combat_stats = h.getMeleeCombatStats(self.caller)
            cleavesRemaining = self.caller.db.cleave

            if combat_stats.get("melee", 0) or combat_stats.get("bow", 0):

                loop = CombatLoop(self.caller, target)
                loop.resolveCommand()

                die_result = h.fayneChecker(combat_stats.get("master_of_arms", 0), combat_stats.get("wylding_hand", 0))

                # Get damage result and damage for weapon type
                attack_result = (die_result + combat_stats.get("weapon_level", 0)) - combat_stats.get("dmg_penalty", 0) - combat_stats.get("weakness", 0)
                damage = 2 if combat_stats.get("two_handed", 0) == True else 1
                target_av = target.db.av
                shot_location = h.shotFinder(target.db.targetArray)

                if h.canFight(self.caller):
                    if h.isAlive(target):
                        if not combat_stats.get("weakness", 0):
                            if cleavesRemaining > 0:
                                if attack_result >= target.db.av:
                                    self.caller.location.msg_contents(f"|015{self.caller.key} strikes|n (|020{attack_result}|n) |015with great ferocity and cleaves {target.key}'s {shot_location}|n (|400{target.db.av}|n)|015! dealing|n |540{damage}|n |015damage|n.")
                                    # Decrement amount of cleaves from amount in database
                                    self.caller.db.cleave -= 1
                                    if shot_location == "torso" and target.db.body > 0:
                                        target.db.body = 0
                                        self.caller.location.msg_contents(f"|015{target.key} has been fatally wounded and is now bleeding to death. They will soon be unconscious.|n")
                                    else:
                                        h.deathSubtractor(damage, target, self.caller)
                                else:
                                    self.caller.location.msg_contents(f"|015{self.caller.key} swings ferociously at {target.key}, but misses.|n")
                            else:
                                self.caller.msg("|400You have 0 cleaves remaining or do not have the skill.")
                        else:
                            self.caller.msg("|400You are too weak to use this attack.|n")
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
                self.msg("|540Before you attack you must equip a weapon using the command settwohanded 1 or setbow 1.")
                return
        else:
            self.msg("You need to wait until it is your turn before you are able to act.")
            return
