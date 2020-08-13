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
            self.caller.msg("|430Usage: sunder <target>|n")
            return

        # Init combat helper class for logic
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
            target_stats = h.getMeleeCombatStats(target)
            sundersRemaining = self.caller.db.sunder

            if self.caller.db.right_slot and self.caller.db.left_slot:
                if sundersRemaining > 0:

                    die_result = h.fayneChecker(combat_stats.get("master_of_arms", 0), combat_stats.get("wylding_hand", 0))

                    # Get damage result and damage for weapon type
                    attack_result = (die_result + combat_stats.get("weapon_level", 0)) - combat_stats.get("dmg_penalty", 0) - combat_stats.get("weakness", 0)
                    damage = 2 if combat_stats.get("two_handed", False) else 1
                    target_av = target.db.av
                    shot_location = h.shotFinder(target.db.targetArray)

                    # Do all the checks
                    if h.canFight(self.caller):
                        if h.isAlive(target):
                          if sundersRemaining > 0:
                            if not combat_stats.get("weakness", 0):
                                    if attack_result >= target.db.av:

                                        # Check target left and right slots for items. Decrement material value from right and then left.
                                        # If no more items, subtract damage as normal.
                                        if target_stats.get("right_slot", ''):
                                            # Get item and material value for right slot.
                                            right_item = self.caller.search(target.db.right_slot[0], location=target)
                                            right_mv = right_item.db.material_value
                                                # Decrement one from material value.
                                            # Check to make sure it won't go below 0.
                                            if right_mv - 1 < 0:
                                                right_mv = 0
                                                right_item.db.broken = True
                                                # Remove item from slot. Player won't be able to requip it.
                                                target.db.right_slot.remove(right_item)
                                                self.caller.location.msg_contents(f"|025{self.caller.key} strikes|n (|020{attack_result}|n) |025with great ferocity and sunders {target.key}'s {right_item.key}|n (|300{target.db.av}|n)|025, breaking it.|n")
                                            else:
                                                right_mv -= 1
                                                self.caller.location.msg_contents(f"|025{self.caller.key} strikes|n (|020{attack_result}|n) |025with great ferocity and damages {target.key}'s {right_item.key}|n (|300{target.db.av})|025.|n")

                                        elif target_stats.get("left_slot", ''):
                                            # Get item and material value for right slot.
                                            left_item = self.caller.search(target.db.left_slot[0])
                                            left_mv = left_item.db.material_value
                                            # Decrement one from material value
                                            if left_mv - 1 < 0:
                                                left_mv = 0
                                                left_item.db.broken = True
                                                target.db.left_slot.remove(left_item)
                                                self.caller.location.msg_contents(f"|025{self.caller.key} strikes|n (|020{attack_result}|n) |025with great ferocity and sunders {target.key}'s {left_item.key}|n (|300{target.db.av}|n)|025, breaking it.|n")
                                            else:
                                                right_mv -= 1
                                                self.caller.location.msg_contents(f"|025{self.caller.key} strikes|n (|020{attack_result}|n) |025with great ferocity and damages {target.key}'s {left_item.key}|n (|300{target.db.av}|n)|025.|n")

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
                                                self.caller.location.msg_contents(f"|025{target.key} has been fatally wounded and is now bleeding to death. They will soon be unconscious.|n")
                                            else:
                                                h.deathSubtractor(damage, target, self.caller)

                                        # Decrement amount of cleaves from amount in database
                                        self.caller.db.sunder -= 1
                                    else:
                                        self.caller.location.msg_contents(f"|025{self.caller.key} strikes a devestating blow at {target.key}, but misses.|n")
                                    # Clean up
                                    # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                                    loop.combatTurnOff(self.caller)
                                    loop.cleanup()
                            else:
                                self.caller.msg("|430You are too weak to use this attack.|n")
                        else:
                            self.msg(f"{target.key} is dead. You only further mutiliate their body.")
                            self.caller.location.msg_contents(f"{self.caller.key} further mutilates the corpse of {target.key}.")
                    else:
                        self.msg("|300You are too injured to act.|n")

                else:
                    self.caller.msg("|300You have 0 sunders remaining or do not have the skill.\nPlease choose another action.|n")
            else:
                self.msg("|430Before you attack you must equip a two-handed weapon using the command equip <weapon name>.|n")
                return
        else:
            self.msg("|430You need to wait until it is your turn before you are able to act.|n")
            return
