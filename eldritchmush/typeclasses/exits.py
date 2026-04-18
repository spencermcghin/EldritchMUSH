"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""
from evennia import DefaultExit


class Exit(DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects except
    they defines the `destination` property. It also does work in the
    following methods:

     basetype_setup() - sets default exit locks (to change, use `at_object_creation` instead).
     at_cmdset_get(**kwargs) - this is called when the cmdset is accessed and should
                              rebuild the Exit cmdset along with a command matching the name
                              of the Exit object. Conventionally, a kwarg `force_init`
                              should force a rebuild of the cmdset, this is triggered
                              by the `@alias` command when aliases are changed.
     at_failed_traverse() - gives a default error message ("You cannot
                            go there") if exit traversal fails and an
                            attribute `err_traverse` is not defined.

    Relevant hooks to overload (compared to other types of Objects):
        at_traverse(traveller, target_loc) - called to do the actual traversal and calling of the other hooks.
                                            If overloading this, consider using super() to use the default
                                            movement implementation (and hook-calling).
        at_after_traverse(traveller, source_loc) - called by at_traverse just after traversing.
        at_failed_traverse(traveller) - called by at_traverse if traversal failed for some reason. Will
                                        not be called if the attribute `err_traverse` is
                                        defined, in which case that will simply be echoed.
    """

    def at_object_creation(self):
        self.locks.add("traverse:attr(in_combat, 0)")

        return


class QuestGatedExit(Exit):
    """Exit that requires a specific quest to be active or completed.

    Set `db.required_quest` to the quest key (e.g. "rescue_blacksmith").
    Set `db.gate_message` to a custom rejection message (optional).

    Players without the quest active/completed see the exit but can't
    traverse — they get a lore-flavored rejection instead.
    """

    def at_traverse(self, traversing_object, target_location, **kwargs):
        quest_key = self.attributes.get("required_quest", default=None)
        if quest_key and hasattr(traversing_object, "db"):
            # Admins/builders bypass the gate
            account = getattr(traversing_object, "account", None)
            if account and (account.is_superuser or account.check_permstring("Builder")):
                return super().at_traverse(traversing_object, target_location, **kwargs)

            quests = traversing_object.db.quests or {}
            state = quests.get(quest_key)
            if not state or state.get("status") not in ("active", "completed"):
                msg = self.attributes.get("gate_message", default=None)
                if not msg:
                    msg = (
                        "|400The path is unclear and overgrown. You'd need "
                        "a reason — and directions — to push through.|n"
                    )
                traversing_object.msg(msg)
                return
        return super().at_traverse(traversing_object, target_location, **kwargs)
