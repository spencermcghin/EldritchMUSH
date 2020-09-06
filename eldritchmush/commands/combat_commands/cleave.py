
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

    def __init__(self):
        self.target = None

    def parse(self):
        # Very trivial parser
        self.target = self.args.strip()

    def func(self):
        if not self.args:
            self.msg("|430Usage: cleave <target>|n")
            return

        combatant = self.caller

        # Init combat helper functions
        h = Helper(combatant)

        # Get target if there is one
        target = combatant.search(self.target)

        if target:
            loop = CombatLoop(combatant, target)
            loop.resolveCommand()
        else:
            return

        # Run logic for cleave command
        if combatant.db.combat_turn:

            combat_stats = h.getMeleeCombatStats(combatant)
            cleaves_remaining = combatant.db.cleave

            if combat_stats.get("two_handed", False):
                if cleaves_remaining > 0:

                    die_result = h.fayneChecker(combat_stats.get("master_of_arms", 0), combat_stats.get("wylding_hand", 0))

                    # Get damage result and damage for weapon type
                    attack_result = (die_result + combatant.db.weapon_level) - h.dmgPenalty() - h.weaknessPenalty()
                    damage = 2 if combat_stats.get("two_handed", False) else 1
                    target_av = target.db.av
                    shot_location = h.shotFinder(target.db.targetArray)

                    if h.canFight(combatant):
                        if h.isAlive(target):
                            if not h.weaknessPenalty():
                                    if attack_result >= target_av:

                                        combat_message = "|025{0} strikes|n (|020{1}|n) |025with great ferocity and cleaves {2}'s {3}|n (|400{4}|n)|025, dealing|n (|430{5}|n) |025damage|n".format(combatant.key, attack_result, target.key, shot_location, target_av, damage)

                                        # Decrement amount of cleaves from amount in database
                                        cleaves_remaining -= 1
                                        if shot_location == "torso" and target.db.body > 0:
                                            target.db.body = 0
                                            self.msg(f"|430{target.key} has been fatally wounded and is now bleeding to death. They will soon be unconscious.|n")
                                        else:
                                            h.deathSubtractor(damage, target, combatant)
                                    else:
                                        combat_message = "|025{0} swings ferociously|n (|030{1}|n) |025at {2}|n (|400{3}|n)|025, but misses.|n)".format(combatant.key,attack_result,target.key,target_av )
                                    
                                    # Clean up
                                    # Set combatant's combat_turn to 0. Can no longer use combat commands.
                                    loop.verboseEndTurn(combatant,combat_message)
                            else:
                                self.msg("|400You are too weak to use this attack.|n")
                        else:
                            self.msg(f"|430{target.key} is dead. You only further mutilate their body.|n")
                            combatant.location.msg_contents(f"|025{combatant.key} further mutilates the corpse of {target.key}.|n")
                    else:
                        self.msg("|400You are too injured to act.|n")
                else:
                    self.msg("|400You have 0 cleaves remaining or do not have the skill.\nPlease choose another action.")
            else:
                self.msg("|430Before you attack you must equip a two handed weapon using the command equip <weapon>.|n")
                return
        else:
            self.msg("|430You need to wait until it is your turn before you are able to act.|n")
            return
