from evennia import create_object
from evennia import Command


class CmdCreateNPC(Command):
    """
    create a new npc

    Usage: createnpc <name>

    Creates a new, named NPC. The NPC will start with default character attributes
    as defined in the Character class.
    """
    key = "createnpc"
    aliases = ["createNPC", "+createnpc", "+createNPC"]
    locks = "call:not perm(nonpcs)"
    help_category = "mush"
    errmsg = "Usage: createnpc <name>"

    def func(self):
        "create the object and name it"
        caller = self.caller
        # Error handling
        if not self.args:
            caller.msg(errmsg)
            return
        if not caller.location:
            # May not create npc when OOC
            caller.msg("You must be in a location to build an npc.")
            return

        # make name always start with capital letter
        name = self.args.strip().capitalize()
        # create npc in caller's location
        npc = create_object("characters.Character",
                      key=name,
                      location=caller.location,
                      locks="edit:id(%i) and perm(Builders);call:false()" % caller.id)
        # announce
        message = "%s created the NPC '%s'."
        caller.msg(message % ("You", name))
