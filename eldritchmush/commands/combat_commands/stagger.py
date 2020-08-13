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

    def func(self):
        if not self.target:
            self.caller.msg("|430Usage: stagger <target>|n")
            return

        # Instantiate helper function class
        h = Helper(self.caller)

        # Check for and error handle designated target
        target = h.targetHandler(self.target)

        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        loop = CombatLoop(self.caller, target)
        loop.resolveCommand()

        # Run logic for cleave command
        if self.caller.db.combat_turn:

            combat_stats = h.getMeleeCombatStats(self.caller)
            staggersRemaining = self.caller.db.stagger

            if combat_stats.get("right_slot", '') or combat_stats.get("left_slot", ''):
                if staggersRemaining > 0:

                    die_result = h.fayneChecker(combat_stats.get("master_of_arms", 0), combat_stats.get("wylding_hand", 0))

                    # Get damage result and damage for weapon type
                    attack_result = (die_result + combat_stats.get("weapon_level", 0)) - combat_stats.get("dmg_penalty", 0) - combat_stats.get("weakness", 0) - combat_stats.get("stagger_penalty", 0)
                    damage = combat_stats.get("stagger_damage", 0)
                    target_av = target.db.av
                    shot_location = h.shotFinder(target.db.targetArray)

                    # Do all the checks
                    if h.canFight(self.caller):
                        if h.isAlive(target):
                          if staggersRemaining > 0:
                            if not combat_stats.get("weakness", 0):
                                    if attack_result >= target.db.av:
                                        self.caller.location.msg_contents(f"|025{self.caller.key} strikes|n (|020{attack_result}|n) |025with a powerful blow to the {shot_location} and puts {target.key} off of their footing (|300{target.db.av}|n)|025, dealing {damage} damage.|n")
                                        # Do damage resolution block
                                        if target_av:
                                            # subtract damage from corresponding target stage (shield_value, armor, tough, body)
                                            new_av = h.damageSubtractor(damage, target, self.caller)
                                            # Update target av to new av score per damageSubtractor
                                            target.db.av = new_av
                                            target.msg(f"|430Your new total Armor Value is {new_av}:\nShield: {target.db.shield}\nArmor Specialist: {target.db.armor_specialist}\nArmor: {target.db.armor}\nTough: {target.db.tough}|n")
                                        else:
                                            # First torso shot always takes body to 0. Does not pass excess damage to bleed points.
                                            if shot_location == "torso" and target.db.body > 0:
                                                target.db.body = 0
                                                self.caller.location.msg_contents(f"|025{target.key} has been fatally wounded and is bleeding to death. They will soon be unconscious.|n")
                                            else:
                                                h.deathSubtractor(damage, target, self.caller)

                                        # Decrement amount of cleaves from amount in database
                                        self.caller.db.sunder -= 1
                                    else:
                                        self.caller.location.msg_contents(f"|025{self.caller.key} strikes with a powerful blow at {target.key}, but misses.|n")
                                    # Clean up
                                    # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                                    loop.combatTurnOff(self.caller)
                                    loop.cleanup()
                            else:
                                self.caller.msg("|300You are too weak to use this attack.|n")
                        else:
                            self.msg(f"{target.key} is dead. You only further mutiliate their body.")
                            self.caller.location.msg_contents(f"{self.caller.key} further mutilates the corpse of {target.key}.")
                    else:
                        self.msg("You are too injured to act.")
                else:
                    self.caller.msg("|300You have 0 staggers remaining or do not have the skill.\nPlease choose another action.")
            else:
                self.msg("|430Before you attack you must equip a weapon using the command setmelee 1 or setbow 1.")
                return
        else:
            self.msg("You need to wait until it is your turn before you are able to act.")
            return
