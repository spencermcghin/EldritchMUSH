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
        h = Helper(self.caller)

        if not h.canFight(self.caller):
            caller.msg("|400You are too injured to act.|n")
            return

        resistsRemaining = self.caller.db.resist
        caller = self.caller
        weakness = h.weaknessChecker(caller.db.weakness)

        # Reconcile against combat loop to get turn.
        loop = CombatLoop(caller, target=None)
        loop.resolveCommand()

        if caller.db.combat_turn:
            if resistsRemaining:
                # Check to see if the target is already healed to max.
                if caller.db.tough == caller.db.total_tough:
                    self.caller.msg(f"|430You are at maximum tough and body points.|n")
                    return

                # Check which stat point to add back.
                if (caller.db.tough < caller.db.total_tough) and caller.db.body >= 3:
                    caller.db.tough +=1
                    result = "1 tough"
                else:
                    caller.db.body += 1
                    result = "1 body"

                # canFight will catch the rest.
                caller.db.resist -= 1
                caller.location.msg_contents(f"|025{caller.key} resists the brunt of the attack and recovers {result}.|n")
                # End turn and clean up
                loop.combatTurnOff(caller)
                loop.cleanup()

            else:
                self.msg("|400You have 0 resists remaining or do not have the skill.\nPlease choose another action.|n")
                return
        else:
            caller.msg("|430You need to wait until it is your turn before you are able to act.|n")
            return
