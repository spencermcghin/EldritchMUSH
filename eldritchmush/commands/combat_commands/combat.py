# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper
from evennia import utils
from typeclasses.npc import Npc

class CmdCombat(Command):
    """
    Lists current possible targets and their general status per the look command.

    Usage:
      combat

    Logic:
    1. Check to see if in combat loop for location.
    2. Else broadcast not in combat message.
    3. If in combat, get turn order, enemy names, and their general status.


    """
    key = "combat"
    aliases = ["targets", "combat status", "combat targets", "turn order", "enemies"]
    help_category = "combat"

    def parse(self):
        self.combat_loop = self.caller.location.db.combat_loop

    def func(self):
        # Check to see if caller is in combat loop:
        if self.caller in self.combat_loop:
            turn_order = self.combat_loop.index(self.caller) + 1
            enemies = [char for char in self.combat_loop if utils.inherits_from(char, Npc)]



        else:
            self.msg(f"|400You are not part of any combat for {self.caller.location}.|n")
