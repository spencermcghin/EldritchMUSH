
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
            self.caller.msg("|430Usage: cleave <target>|n")
            return

        # Init combat helper functions
        h = Helper(self.caller)

        # Get target if there is one
        target = self.caller.search(self.target)

        if target:
            loop = CombatLoop(self.caller, target)
            loop.resolveCommand()
        else:
            return

        # Run logic for cleave command
        if self.caller.db.combat_turn:

            combat_stats = h.getMeleeCombatStats(self.caller)
            right_hand_item = combat_stats.get("right_slot", None)
            left_hand_item = combat_stats.get("left_slot", None)
            cleavesRemaining = self.caller.db.cleave

            if combat_stats.get("two_handed", False):
                if cleavesRemaining > 0:

                    die_result = h.fayneChecker(combat_stats.get("master_of_arms", 0), combat_stats.get("wylding_hand", 0))

                    # Get damage result and damage for weapon type
                    attack_result = (die_result + self.caller.db.weapon_level) - combat_stats.get("dmg_penalty", 0) - combat_stats.get("weakness", 0)
                    damage = 2 if combat_stats.get("two_handed", False) else 1
                    target_av = target.db.av
                    shot_location = h.shotFinder(target.db.targetArray)

                    if h.canFight(self.caller):
                        if h.isAlive(target):
                            if not combat_stats.get("weakness", 0):
                                    if attack_result >= target.db.av:
                                        self.caller.location.msg_contents(f"|025{self.caller.key} strikes|n (|020{attack_result}|n) |025with great ferocity and cleaves {target.key}'s {shot_location}|n (|300{target.db.av}|n)|025, dealing|n (|430{damage}|n) |025damage|n.")
                                        # Decrement amount of cleaves from amount in database
                                        self.caller.db.cleave -= 1
                                        if shot_location == "torso" and target.db.body > 0:
                                            target.db.body = 0
                                            self.caller.location.msg_contents(f"|025{target.key} has been fatally wounded and is now bleeding to death. They will soon be unconscious.|n")
                                        else:
                                            h.deathSubtractor(damage, target, self.caller)
                                    else:
                                        self.caller.location.msg_contents(f"|025{self.caller.key} swings ferociously at {target.key}, but misses.|n")
                                    # Clean up
                                    # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                                    loop.combatTurnOff(self.caller)
                                    loop.cleanup()
                            else:
                                self.caller.msg("|300You are too weak to use this attack.|n")
                        else:
                            self.msg(f"{target.key} is dead. You only further mutiliate their body.")
                            self.caller.location.msg_contents(f"|025{self.caller.key} further mutilates the corpse of {target.key}.|n")
                    else:
                        self.msg("|300You are too injured to act.|n")
                else:
                    self.caller.msg("|300You have 0 cleaves remaining or do not have the skill.\nPlease choose another action.")
            else:
                self.msg("|430Before you attack you must equip a weapon using the command equip <weapon>.|n")
                return
        else:
            self.msg("|430You need to wait until it is your turn before you are able to act.|n")
            return
