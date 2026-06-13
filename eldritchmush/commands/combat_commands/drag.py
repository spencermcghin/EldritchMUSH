# Local imports
from evennia import Command
from world.combat_loop import CombatLoop
from commands.combat import Helper


class Drag(Command):

    """
    Drag an incapacitated ally out of danger so they can be healed.

    Usage:
      drag <target> <exit>
      drag <target> = <exit>

    Hauls a downed character (bleeding out or dying) through an exit,
    taking you both to the adjacent room — the battlefield rescue.

    - The target must be unable to move on their own (out of bleed
      points).
    - If you are in combat, this is your action for the turn: you can
      only drag on your turn, and dragging pulls BOTH of you out of
      the fight. There is no pursuit.
    - Out of combat, you simply carry them through.

    See also: disengage, heal, chirurgery
    """

    key = "drag"
    help_category = "Combat"

    def parse(self):
        args = (self.args or "").strip()
        self.target_name = ""
        self.exit_name = ""
        if "=" in args:
            self.target_name, _, self.exit_name = args.partition("=")
        elif " " in args:
            # Last word is the exit; everything before it is the target.
            self.target_name, _, self.exit_name = args.rpartition(" ")
        else:
            self.target_name = args
        self.target_name = self.target_name.strip()
        self.exit_name = self.exit_name.strip()

    def func(self):
        caller = self.caller

        if not self.target_name or not self.exit_name:
            self.msg("|430Usage: drag <target> <exit>  (e.g. drag "
                     "edwin north)|n")
            return

        h = Helper(caller)
        if not h.canFight(caller):
            self.msg("|400You are too injured to drag anyone.|n")
            return

        # Resolve the body being dragged.
        target = caller.search(self.target_name, quiet=True)
        if isinstance(target, (list, tuple)):
            target = target[0] if target else None
        if not target or target.location != caller.location:
            self.msg("|430There is no one here by that name to drag.|n")
            return
        if target == caller:
            self.msg("|400You can't drag yourself — try an exit.|n")
            return
        if (target.db.bleed_points or 0) > 0:
            self.msg(f"|430{target.key} can still move under their own "
                     f"power — they don't need dragging.|n")
            return

        # Resolve the exit.
        exit_obj = None
        for obj in caller.location.contents:
            if not getattr(obj, "destination", None):
                continue
            names = [obj.key.lower()] + [a.lower() for a in obj.aliases.all()]
            if self.exit_name.lower() in names:
                exit_obj = obj
                break
        if not exit_obj:
            self.msg(f"|430There is no exit '{self.exit_name}' here.|n")
            return
        destination = exit_obj.destination

        room = caller.location
        loop_list = room.db.combat_loop or []
        in_combat = caller in loop_list

        # In combat, dragging is your turn — same opt-in rule as
        # disengage. It removes BOTH of you from the loop.
        if in_combat:
            if not caller.db.combat_turn:
                self.msg("|430You need to wait until it is your turn "
                         "before you can drag them clear.|n")
                return
            my_index = loop_list.index(caller)
            for char in (caller, target):
                if char in loop_list:
                    loop_list.remove(char)
                char.db.in_combat = 0
                char.db.combat_turn = 1
            if len(loop_list) <= 1:
                for char in list(loop_list):
                    char.db.combat_turn = 1
                    char.db.in_combat = 0
                loop_list.clear()
                room.msg_contents(
                    f"|430Combat is now over for the {room}.|n")
            else:
                # Hand the turn on from the slot before our old one.
                prev_char = loop_list[(my_index - 1) % len(loop_list)]
                CombatLoop(prev_char).cleanup()
        else:
            # Never haul someone INTO an active fight's bookkeeping —
            # just make sure both parties are flagged clear.
            caller.db.in_combat = 0
            target.db.in_combat = 0

        room.msg_contents(
            f"|025{caller.key} hooks their arms under {target.key} "
            f"and drags them away through the {exit_obj.key}, leaving "
            f"a dark smear behind.|n")
        target.move_to(destination, quiet=True)
        caller.move_to(destination, quiet=True)
        destination.msg_contents(
            f"|025{caller.key} backs in through the door, dragging "
            f"the limp form of {target.key} to what they hope is "
            f"safety.|n")
        caller.msg(f"|540You drag {target.key} clear. Now heal them — "
                   f"quickly.|n")
        if hasattr(target, "msg"):
            target.msg(f"|540{caller.key} drags you out of the "
                       f"fight.|n")
        try:
            from world import telemetry
            telemetry.incr("combat.drags")
        except Exception:
            pass
