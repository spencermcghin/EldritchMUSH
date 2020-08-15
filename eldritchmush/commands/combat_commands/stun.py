# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper



class CmdStun(Command):
    """
    Issues a stun command.

    Usage:

    disarm <target>

    This will issue a stun command that makes a target skip their turn, with a -1 penalty to attack.
    """

    key = "stun"
    help_category = "mush"

    def parse(self):
        "Very trivial parser"
        self.target = self.args.strip()

    def func(self):
        if not self.args:
            self.caller.msg("|540Usage: stun <target>|n")
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
            stunsRemaining = self.caller.db.stun

            if combat_stats.get("melee", 0) or combat_stats.get("bow", 0):
                if stunsRemaining > 0:

                    die_result = h.fayneChecker(combat_stats.get("master_of_arms", 0), combat_stats.get("wylding_hand", 0))

                    # Get damage result and damage for weapon type
                    attack_result = (die_result + self.caller.db.weapon_level) - combat_stats.get("dmg_penalty", 0) - combat_stats.get("weakness", 0) - combat_stats.get("stun_penalty", 0)
                    damage = 2 if combat_stats.get("two_handed", 0) == True else 1
                    target_av = target.db.av
                    shot_location = h.shotFinder(target.db.targetArray)

                    if h.canFight(self.caller):
                        if h.isAlive(target):
                            if not combat_stats.get("weakness", 0):
                                    if attack_result >= target.db.av:
                                        # Decrement amount of cleaves from amount in database
                                        self.caller.db.stun -= 1
                                        # Set disarmed flag on target
                                        target.db.skip_turn = True
                                        # Resolve damage
                                        # Stun status message to target
                                        self.caller.location.msg_contents(f"|015{self.caller.key} lines up behind {target.key} and strikes|n (|020{attack_result}|n)|015, stunning them momentarily|n (|400{target.db.av}|n)|015.|n")

                                    else:
                                        self.caller.location.msg_contents(f"|015{self.caller.key} lines up behind (|020{attack_result}|n) |015 {target.key}, but misses their opportunity to stun them.|n (|400{target.db.av}|n)|n")
                                    # Clean up
                                    # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                                    loop.combatTurnOff(self.caller)
                                    loop.cleanup()
                            else:
                                self.caller.msg("|400You are too weak to use this attack.|n")
                        else:
                            self.msg(f"{target.key} is dead. You only further mutiliate their body.")
                            self.caller.location.msg_contents(f"{self.caller.key} further mutilates the corpse of {target.key}.")
                    else:
                        self.msg("You are too injured to act.")
                else:
                    self.caller.msg("|400You have 0 stuns remaining or do not have the skill.\nPlease choose another action.")
            else:
                self.msg("|540Before you attack you must equip a weapon using the command setmelee 1 or setbow 1.")
                return
        else:
            self.msg("You need to wait until it is your turn before you are able to act.")
            return
