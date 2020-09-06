# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper
from evennia import utils
from typeclasses.npc import Npc

class CmdSunder(Command):
    """
    Issues a sunder command.

    Usage:

    sunder <target>

    This will calculate an attack score based on your weapon and master of arms level.
    """

    key = "sunder"
    help_category = "mush"

    def __init__(self):
        self.target = None

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
        target = self.caller.search(self.target)

        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        if target:
            loop = CombatLoop(self.caller, target)
            loop.resolveCommand()
        else:
            return

        # Run logic for cleave command
        if self.caller.db.combat_turn:

            combat_stats = h.getMeleeCombatStats(self.caller)
            target_stats = h.getMeleeCombatStats(target)
            right_hand_item = combat_stats.get("right_slot", None)
            left_hand_item = combat_stats.get("left_slot", None)
            sundersRemaining = self.caller.db.sunder

            if right_hand_item and right_hand_item == left_hand_item:
                if sundersRemaining > 0:

                    die_result = h.fayneChecker(combat_stats.get("master_of_arms", 0), combat_stats.get("wylding_hand", 0))

                    # Get damage result and damage for weapon type
                    attack_result = (die_result + self.caller.db.weapon_level) - combat_stats.get("dmg_penalty", 0) - combat_stats.get("weakness", 0)
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
                                        if target_stats.get("right_slot", None):
                                            # Get item and material value for right slot.
                                            item_key = self.caller.search(target.db.right_slot[0], location=target)
                                            slot = target.db.right_slot
                                        elif target_stats.get("left_slot", None):
                                            # Get item and material value for right slot.
                                            item_key = self.caller.search(target.db.left_slot[0], location=target)
                                            slot = target.db.left_slot

                                        if item_key:
                                            item_mv = item_key.db.material_value

                                            # Decrement one from material value.
                                            # Check to make sure it won't go below 0.'
                                            item_mv -= 1
                                            if item_mv <= 0:
                                                item_mv = 0
                                                item_key.db.broken = True
                                                # Remove slot
                                                slot.remove(item_key)
                                                display_string = "with great ferocity and sunders"

                                                # If two handed, remove from both slots
                                                if item_key.db.twohanded:
                                                    target.db.left_slot.clear()
                                                    target.db.right_slot.clear()

                                            else:
                                                display_string = "with great ferocity and damages"

                                            self.caller.location.msg_contents(f"|025{self.caller.key} strikes|n (|020{attack_result}|n) |025{display_string} {target.key}'s {item_key.key}|n (|400{target.db.av})|025.|n")

                                        # Do damage resolution block
                                        elif target_av:
                                            # subtract damage from corresponding target stage (shield_value, armor, tough, body)
                                            new_av = h.damageSubtractor(damage, target, self.caller)
                                            # Update target av to new av score per damageSubtractor
                                            target.db.av = new_av
                                            self.caller.location.msg_contents(f"|025{self.caller.key} strikes with great ferocity|n (|020{attack_result}|n) |025at {target.key} and hits|n (|400{target_av}|n), |025dealing|n |430{damage}|n |025damage!|n")
                                            target.msg(f"|430Your new total Armor Value is {new_av}:\nShield: {target.db.shield}\nArmor Specialist: {target.db.armor_specialist}\nArmor: {target.db.armor}\nTough: {target.db.tough}|n")
                                        else:
                                            self.caller.location.msg_contents(f"|025{self.caller.key} strikes with great ferocity|n (|020{attack_result}|n) |025at {target.key}'s {shot_location} and hits|n (|400{target_av}|n), |025dealing|n |430{damage}|n |025damage!|n")
                                            # First torso shot always takes body to 0. Does not pass excess damage to bleed points.
                                            if shot_location == "torso" and target.db.body > 0:
                                                target.db.body = 0
                                                self.caller.location.msg_contents(f"|025{target.key} has been fatally wounded and is now bleeding to death. They will soon be unconscious.|n")
                                            else:
                                                h.deathSubtractor(damage, target, self.caller)

                                        # Decrement amount of cleaves from amount in database
                                        self.caller.db.sunder -= 1
                                    else:
                                        self.caller.location.msg_contents(f"|025{self.caller.key} strikes a devastating blow at {target.key}, but misses.|n")
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
                        self.msg("|400You are too injured to act.|n")

                else:
                    self.caller.msg("|400You have 0 sunders remaining or do not have the skill.\nPlease choose another action.|n")
            else:
                self.msg("|430Before you attack you must equip a two-handed weapon using the command equip <weapon name>.|n")
                return
        else:
            self.msg("|430You need to wait until it is your turn before you are able to act.|n")
            return
