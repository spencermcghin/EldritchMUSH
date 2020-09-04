# Local imports
from evennia import Command, utils
from world.combat_loop import CombatLoop
from commands.combat import Helper
from typeclasses.npc import Npc


class CmdDisarm(Command):
    """
    Issues a disarm command.

    Usage:

    disarm <target>

    This will issue a disarm command that reduces the next amount of damage taken by master of arms level.
    """

    key = "disarm"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):
        if not self.args:
            self.caller.msg("|430Usage: disarm <target>|n")
            return

        # Init combat helper functions
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
            disarmsRemaining = self.caller.db.disarm

            # Check to see if player holding a weapon in either hand. Sunder removes weapon from player slot. Won't let you equip broken weapons.
            if combat_stats.get("right_slot", '') or combat_stats.get("left_slot", ''):
                if disarmsRemaining > 0:

                    die_result = h.fayneChecker(combat_stats.get("master_of_arms", 0), combat_stats.get("wylding_hand", 0))

                    # Get damage result and damage for weapon type
                    attack_result = (die_result + self.caller.db.weapon_level) - combat_stats.get("dmg_penalty", 0) - combat_stats.get("weakness", 0) - combat_stats.get("disarm_penalty", 0)
                    damage = 2 if combat_stats.get("two_handed", False) else 1
                    target_av = target.db.av
                    shot_location = h.shotFinder(target.db.targetArray)

                    if h.canFight(self.caller):
                        if h.isAlive(target):
                            if not combat_stats.get("weakness", 0):
                                right_item = self.caller.search(target.db.right_slot[0], location=target)

                                # Check for NPC calling the command and pick a new command if so.
                                if utils.inherits_from(self.caller, Npc):
                                    self.caller.location.msg_contents("NPC caught exception.")
                                    self.caller.command_picker(target=target)
                                    return

                                if not right_item.db.twohanded:
                                    if attack_result >= target.db.av:
                                        # Decrement amount of cleaves from amount in database
                                        self.caller.db.disarm -= 1
                                        # Set disarmed flag on target
                                        target.db.skip_turn = True
                                        # Resolve damage
                                        if target_av:
                                            self.caller.location.msg_contents(f"|025{self.caller.key} nimbly strikes|n (|020{attack_result}|n) |025with a deft maneuver and disarms {target.key}|n (|400{target.db.av}|n)|025, dealing|n (|430{damage}|n) |025damage|n.")
                                            new_av = h.damageSubtractor(damage, target, self.caller)
                                            # Update target av to new av score per damageSubtractor
                                            target.db.av = new_av
                                            target.msg(f"|430Your new total Armor Value is {new_av}:\nShield: {target.db.shield}\nArmor Specialist: {target.db.armor_specialist}\nArmor: {target.db.armor}\nTough: {target.db.tough}|n")
                                        else:
                                            # No target armor so subtract from their body total and hit a limb.
                                            self.caller.location.msg_contents(f"|025{self.caller.key} nimbly strikes|n (|020{attack_result}|n) |025with a deft maneuver and disarms {target.key}|n (|400{target.db.av}|n)|025, striking them in the {shot_location} and dealing|n (|430{damage}|n) |025damage|n.")
                                            if shot_location == "torso" and target.db.body > 0:
                                                target.db.body = 0
                                                self.caller.location.msg_contents(f"|025{target.key} has been fatally wounded and is now bleeding to death. They will soon be unconscious.|n")
                                            else:
                                                h.deathSubtractor(damage, target, self.caller)
                                        # Disarm status message to target
                                        target.msg("|430You have been disarmed. Your next turn will be skipped.|n")

                                    else:
                                        self.caller.location.msg_contents(f"|025{self.caller.key} swings deftly,|n (|020{attack_result}|n) |025attempting to disarm {target.key}, but misses|n (|400{target.db.av}|n)|025.|n")
                                    # Clean up
                                    # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                                    loop.combatTurnOff(self.caller)
                                    loop.cleanup()

                                else:
                                    self.msg(f"|430You cannot disarm a two-handed weapon. Please try another attack.|n")
                            else:
                                self.caller.msg("|400You are too weak to use this attack.|n")
                        else:
                            self.msg(f"|430{target.key} is dead. You only further mutiliate their body.|n")
                            self.caller.location.msg_contents(f"|025{self.caller.key} further mutilates the corpse of {target.key}.|n")
                    else:
                        self.msg("|400You are too injured to act.|n")
                else:
                    self.caller.msg("|400You have 0 disarms remaining or do not have the skill.\nPlease choose another action.")
            else:
                self.msg("|430Before you attack you must equip a weapon using the command equip <weapon>|n")
                return
        else:
            self.msg("|430You need to wait until it is your turn before you are able to act.|n")
            return
