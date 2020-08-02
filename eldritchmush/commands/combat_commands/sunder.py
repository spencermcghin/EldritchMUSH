# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper

class CmdSunder(Command):
    """
    Issues a sunder command.

    Usage:

    sunder <target>

    This will calculate an attack score based on your weapon and master of arms level.
    """

    key = "sunder"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):

        if not self.target:
            self.caller.msg("|540Usage: sunder <target>|n")
            return

        # Init combat helper class for logic
        h = Helper(self.caller)

        # Check for and error handle designated target
        target = h.targetHandler(self.target)

        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        loop = CombatLoop(self.caller, target)
        loop.resolveCommand()

        # Run logic for strike command
        if self.caller.db.combat_turn:

            # Run rest of command logic after passing checks.

            # Return db stats needed to calc melee results
            combat_stats = h.getMeleeCombatStats(self.caller)

            # Get die result based on master of arms level
            if combat_stats.get("melee", 0):

                # Check if damage bonus comes from fayne or master_of_arms
                die_result = h.fayneChecker(combat_stats.get("master_of_arms", 0), combat_stats.get("wylding_hand", 0))

                # Get damage result and damage for weapon type
                attack_result = (die_result + combat_stats.get("weapon_level", 0)) - combat_stats.get("dmg_penalty", 0) - combat_stats.get("weakness", 0)
                damage = 2 if combat_stats.get("two_handed", 0) == True else 1
                target_av = target.db.av
                shot_location = h.shotFinder(target.db.targetArray)

        # Run logic for cleave command
        if self.caller.db.combat_turn:

            combat_stats = h.getMeleeCombatStats(self.caller)
            sundersRemaining = self.caller.db.sunder

            if combat_stats.get("melee", 0) or combat_stats.get("bow", 0):
                if sundersRemaining > 0:

                    die_result = h.fayneChecker(combat_stats.get("master_of_arms", 0), combat_stats.get("wylding_hand", 0))

                    # Get damage result and damage for weapon type
                    attack_result = (die_result + combat_stats.get("weapon_level", 0)) - combat_stats.get("dmg_penalty", 0) - combat_stats.get("weakness", 0)
                    damage = 2 if combat_stats.get("two_handed", 0) == True else 1
                    target_av = target.db.av
                    shot_location = h.shotFinder(target.db.targetArray)

                    # Do all the checks
                    if h.canFight(self.caller):
                        if h.isAlive(target):
                          if sundersRemaining > 0:
                            if not combat_stats.get("weakness", 0):
                                    if attack_result >= target.db.av:
                                        self.caller.location.msg_contents(f"|015{self.caller.key} strikes|n (|020{attack_result}|n) |015with great ferocity and sunders {target.key}'s weapon|n (|400{target.db.av}|n)|015, dealing|n |540{damage}|n |015damage|n.")
                                        # Check target left and right slots for items. Decrement material value from right and then left.
                                        # If no more items, subtract damage as normal.



                                        # Decrement amount of cleaves from amount in database
                                        self.caller.db.sunder -= 1
                                        if shot_location == "torso" and target.db.body > 0:
                                            target.db.body = 0
                                            self.caller.location.msg_contents(f"|015{target.key} has been fatally wounded and is now bleeding to death. They will soon be unconscious.|n")
                                        else:
                                            h.deathSubtractor(damage, target, self.caller)
                                    else:
                                        self.caller.location.msg_contents(f"|015{self.caller.key} strikes a devestating blow at {target.key}, but misses.|n")
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
                    self.caller.msg("|400You have 0 sunders remaining or do not have the skill.\nPlease choose another action.")
            else:
                self.msg("|540Before you attack you must equip a weapon using the command settwohanded 1 or setbow 1.")
                return
        else:
            self.msg("You need to wait until it is your turn before you are able to act.")
            return
