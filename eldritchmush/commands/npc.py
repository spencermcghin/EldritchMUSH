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

    def func(self):
        errmsg = "Usage: createnpc <name>"
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


class CmdEditNPC(Command):
    """
    edit an existing NPC

    Usage:
      editnpc <name>[/<attribute> [= value]]

    Examples:
      editnpc mynpc/power = 5
      editnpc mynpc/power    - displays power value
      editnpc mynpc          - shows all editable
                                attributes and values

    This command edits an existing NPC. You must have
    permission to edit the NPC to use this.
    """
    key = "editnpc"
    aliases = ["editNPC"]
    locks = "cmd:not perm(nonpcs)"
    help_category = "mush"

    def parse(self):
        "We need to do some parsing here"
        args = self.args
        propname, propval = None, None
        if "=" in args:
            args, propval = [part.strip() for part in args.rsplit("=", 1)]
        if "/" in args:
            args, propname = [part.strip() for part in args.rsplit("/", 1)]
        # store, so we can access it below in func()
        self.name = args
        self.propname = propname
        # a propval without a propname is meaningless
        self.propval = propval if propname else None

    def func(self):
        "do the editing"

        allowed_propnames = ("master_of_arms",
                             "armor",
                             "tough",
                             "body",
                             "stabilize",
                             "medicine",
                             "battlefieldmedicine",
                             "melee",
                             "resist",
                             "disarm",
                             "cleave",
                             "sunder",
                             "stun",
                             "stagger",
                             "weapon_level",
                             "twohanded",
                             "wyldinghand",
                             "shield",
                             "bow",
                             "activemartialskill")

        caller = self.caller
        if not self.args or not self.name:
            caller.msg("Usage: editnpc name[/propname][=propval]")
            return
        npc = caller.search(self.name)
        if not npc:
            return
        if not npc.access(caller, "edit"):
            caller.msg("You cannot change this NPC.")
            return
        if not self.propname:
            # this means we just list the values
            output = "Properties of %s:" % npc.key
            for propname in allowed_propnames:
                propvalue = npc.attributes.get(propname, default="N/A")
                output += "\n %s = %s" % (propname, propvalue)
            caller.msg(output)
        elif self.propname not in allowed_propnames:
            caller.msg("You may only change %s." %
                              ", ".join(allowed_propnames))
        elif self.propval:
            # assigning a new propvalue
            # in this example, the properties are all integers...
            intpropval = int(self.propval)
            npc.attributes.add(self.propname, intpropval)
            caller.msg("Set %s's property '%s' to %s" %
                         (npc.key, self.propname, self.propval))
        else:
            # propname set, but not propval - show current value
            caller.msg("%s has property %s = %s" %
                         (npc.key, self.propname,
                          npc.attributes.get(self.propname, default="N/A")))


class CmdNPC(Command):
    """
    controls an NPC

    Usage:
        npc <name> = <command>

    This causes the npc to perform a command as itself. It will do so
    with its own permissions and accesses.
    """
    key = "npc"
    locks = "call:not perm(nonpcs)"
    help_category = "mush"

    def parse(self):
        "Simple split of the = sign"
        name, cmdname = None, None
        if "=" in self.args:
            name, cmdname = [part.strip()
                             for part in self.args.rsplit("=", 1)]
        self.name, self.cmdname = name, cmdname

    def func(self):
        "Run the command"
        caller = self.caller
        if not self.cmdname:
            caller.msg("Usage: npc <name> = <command>")
            return
        npc = caller.search(self.name)
        if not npc:
            return
        if not npc.access(caller, "edit"):
            caller.msg("You may not order this NPC to do anything.")
            return
        # send the command order
        npc.execute_cmd(self.cmdname, sessid=self.caller.sessid)
        caller.msg("You told %s to do '%s'." % (npc.key, self.cmdname))
        caller.msg(self.obj.msg)
