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

    def __init__(self):
        self.target = None

    def parse(self):
        self.target = self.args.strip()

    def func(self):
        # Check for correct command
        # Target handling


        if not self.args:
            self.msg("|430Usage: shoot <target>|n")
            return

        if self.args == self.caller:
            self.msg("|400You can't do that.|n")

        # Init combat helper class for logic
        h = Helper(self.caller)

        if not h.canFight(self.caller):
            caller.msg("|400You are too injured to act.|n")
            return

        # Check for and error handle designated target
        target = self.caller.search(self.target)

        # Pass all checks now execute command.
        # Use parsed args in combat loop. Handles turn order in combat.
        if target:
            loop = CombatLoop(self.caller, target)
            loop.resolveCommand()
        else:
            return

        # Run logic for strike command
        if self.caller.db.combat_turn:

            # Return db stats needed to calc melee results
            combat_stats = h.getMeleeCombatStats(self.caller)

            if combat_stats.get("bow", False):
                    # Check if damage bonus comes from fayne or master_of_arms
                    die_result = h.fayneChecker(combat_stats.get("master_of_arms", 0), combat_stats.get("wylding_hand", 0))

                    # Get damage result
                    attack_result = (die_result + self.caller.db.weapon_level) - combat_stats.get("dmg_penalty", 0) - combat_stats.get("weakness", 0) - combat_stats.get("bow_penalty", 0)
                    target_av = target.db.av
                    shot_location = h.shotFinder(target.db.targetArray)
                    bow_damage = combat_stats.get("bow_damage", 0)

                    # Compare caller attack_result to target av.
                    # If attack_result > target av -> hit, else miss
                    if h.isAlive(target):
                        if attack_result >= target.db.av:
                            self.caller.location.msg_contents(f"|025{self.caller.key} lets loose an arrow|n (|020{attack_result}|n)|025 straight for {target.key}'s {shot_location} and hits|n (|400{target.db.av}|n), |025dealing|n (|430{bow_damage}|n) |025damage!|n")
                            if shot_location == "torso" and target.db.body > 0:
                                target.db.body = 0
                                self.caller.location.msg_contents(f"|025{target.key} has been fatally wounded and is now bleeding to death.|n")
                            else:
                                h.deathSubtractor(bow_damage, target, self.caller)
                            # # Remove an arrow from their current count.
                            # self.caller.db.arrows -= 1
                            # self.msg(f"|430You now have {self.db.arrows} arrows.|n")
                        else:
                            # No target armor so subtract from their body total and hit a limb. Add logic from handler above. Leave in body handler in combat handler.
                            self.caller.location.msg_contents(f"|025{self.caller.key} lets loose an arrow|n (|020{attack_result}|n)|025 at {target.key}|n (|400{target.db.av}|n)|025, but it misses.|n")
                        # Clean up
                        # Set self.caller's combat_turn to 0. Can no longer use combat commands.
                        loop.combatTurnOff(self.caller)
                        loop.cleanup()

                    else:
                        self.msg(f"|400{target.key} is dead. You only further mutiliate their body.|n")
                        self.caller.location.msg_contents(f"|025{self.caller.key} further mutilates the corpse of {target.key}|n")

            else:
                self.msg("|430You need to equip a bow before you are able to shoot, using the command equip <bow name>.|n")

        else:
            self.msg("|430You need to wait until it is your turn before you are able to act.|n")
            return
