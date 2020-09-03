# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper

class CmdResist(Command):
    """
    Issues a resist command.

    Usage:

    resist

    This will issue a resist command that adds one to your body or tough, and decrements one from a character's available resists.
    """

    key = "resist"
    help_category = "mush"

    def func(self):
        h = Helper()

        "Get level of master of arms for base die roll. Levels of gear give a flat bonus of +1/+2/+3."
        resistsRemaining = self.caller.db.resist
        master_of_arms = self.caller.db.master_of_arms
        wylding_hand = self.caller.db.wyldinghand
        weapon_level = h.weaponValue(self.caller.db.weapon_level)
        caller = self.caller

        # Check for weakness on character
        weakness = h.weaknessChecker(self.caller.db.weakness)

        if target:
            loop = CombatLoop(self.caller, target)
            loop.resolveCommand()
        else:
            return

        if caller.db.combat_turn:
            if h.canFight(caller):
                if resistsRemaining:
                    # Check to see if the target is already healed to max.
                    if caller.db.tough == caller.db.total_tough:
                        self.caller.msg(f"|430You are at maximum tough and body points.|n")
                        return

                    if caller.db.tough < caller.db.total_tough and target.db.body == 3:
                        caller.db.tough +=1
                        

                    elif target.db.body < 3:
                        caller.db.body += 1

                    caller.location.msg_contents(f"{caller.key} resist the brunt of the attack.")
                    caller.msg("You recover")

                else:
                    self.msg("|400You have 0 resists remaining or do not have the skill.\nPlease choose another action.|n")
            else:
                caller.msg("|400You are too injured to act.|n")
                return

            # Clean up in combat loop
            if (caller in caller.location.db.combat_loop) or (target in caller.location.db.combat_loop):
                loop.combatTurnOff(caller)
                loop.cleanup()
            else:
                return
        else:
            caller.msg("|430You need to wait until it is your turn before you are able to act.|n")
            return
