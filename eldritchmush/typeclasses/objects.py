"""
Object

The Object is the "naked" base class for things in the game world.

Note that the default Character, Room and Exit does not inherit from
this Object, but from their respective default implementations in the
evennia library. If you want to use this class as a parent to change
the other types, you can do so by adding this as a multiple
inheritance.

"""
from evennia import DefaultObject, utils
from commands.default_cmdsets import BoxCmdSet, BlacksmithCmdSet, CrafterCmdSet
import random


class Object(DefaultObject):
    """
    This is the root typeclass object, implementing an in-game Evennia
    game object, such as having a location, being able to be
    manipulated or looked at, etc. If you create a new typeclass, it
    must always inherit from this object (or any of the other objects
    in this file, since they all actually inherit from BaseObject, as
    seen in src.object.objects).

    The BaseObject class implements several hooks tying into the game
    engine. By re-implementing these hooks you can control the
    system. You should never need to re-implement special Python
    methods, such as __init__ and especially never __getattribute__ and
    __setattr__ since these are used heavily by the typeclass system
    of Evennia and messing with them might well break things for you.


    * Base properties defined/available on all Objects

     key (string) - name of object
     name (string)- same as key
     dbref (int, read-only) - unique #id-number. Also "id" can be used.
     date_created (string) - time stamp of object creation

     account (Account) - controlling account (if any, only set together with
                       sessid below)
     sessid (int, read-only) - session id (if any, only set together with
                       account above). Use `sessions` handler to get the
                       Sessions directly.
     location (Object) - current location. Is None if this is a room
     home (Object) - safety start-location
     has_account (bool, read-only)- will only return *connected* accounts
     contents (list of Objects, read-only) - returns all objects inside this
                       object (including exits)
     exits (list of Objects, read-only) - returns all exits from this
                       object, if any
     destination (Object) - only set if this object is an exit.
     is_superuser (bool, read-only) - True/False if this user is a superuser

    * Handlers available

     aliases - alias-handler: use aliases.add/remove/get() to use.
     permissions - permission-handler: use permissions.add/remove() to
                   add/remove new perms.
     locks - lock-handler: use locks.add() to add new lock strings
     scripts - script-handler. Add new scripts to object with scripts.add()
     cmdset - cmdset-handler. Use cmdset.add() to add new cmdsets to object
     nicks - nick-handler. New nicks with nicks.add().
     sessions - sessions-handler. Get Sessions connected to this
                object with sessions.get()
     attributes - attribute-handler. Use attributes.add/remove/get.
     db - attribute-handler: Shortcut for attribute-handler. Store/retrieve
            database attributes using self.db.myattr=val, val=self.db.myattr
     ndb - non-persistent attribute handler: same as db but does not create
            a database entry when storing data

    * Helper methods (see src.objects.objects.py for full headers)

     search(ostring, global_search=False, attribute_name=None,
             use_nicks=False, location=None, ignore_errors=False, account=False)
     execute_cmd(raw_string)
     msg(text=None, **kwargs)
     msg_contents(message, exclude=None, from_obj=None, **kwargs)
     move_to(destination, quiet=False, emit_to_obj=None, use_destination=True)
     copy(new_key=None)
     delete()
     is_typeclass(typeclass, exact=False)
     swap_typeclass(new_typeclass, clean_attributes=False, no_default=True)
     access(accessing_obj, access_type='read', default=False)
     check_permstring(permstring)

    * Hooks (these are class methods, so args should start with self):

     basetype_setup()     - only called once, used for behind-the-scenes
                            setup. Normally not modified.
     basetype_posthook_setup() - customization in basetype, after the object
                            has been created; Normally not modified.

     at_object_creation() - only called once, when object is first created.
                            Object customizations go here.
     at_object_delete() - called just before deleting an object. If returning
                            False, deletion is aborted. Note that all objects
                            inside a deleted object are automatically moved
                            to their <home>, they don't need to be removed here.

     at_init()            - called whenever typeclass is cached from memory,
                            at least once every server restart/reload
     at_cmdset_get(**kwargs) - this is called just before the command handler
                            requests a cmdset from this object. The kwargs are
                            not normally used unless the cmdset is created
                            dynamically (see e.g. Exits).
     at_pre_puppet(account)- (account-controlled objects only) called just
                            before puppeting
     at_post_puppet()     - (account-controlled objects only) called just
                            after completing connection account<->object
     at_pre_unpuppet()    - (account-controlled objects only) called just
                            before un-puppeting
     at_post_unpuppet(account) - (account-controlled objects only) called just
                            after disconnecting account<->object link
     at_server_reload()   - called before server is reloaded
     at_server_shutdown() - called just before server is fully shut down

     at_access(result, accessing_obj, access_type) - called with the result
                            of a lock access check on this object. Return value
                            does not affect check result.

     at_before_move(destination)             - called just before moving object
                        to the destination. If returns False, move is cancelled.
     announce_move_from(destination)         - called in old location, just
                        before move, if obj.move_to() has quiet=False
     announce_move_to(source_location)       - called in new location, just
                        after move, if obj.move_to() has quiet=False
     at_after_move(source_location)          - always called after a move has
                        been successfully performed.
     at_object_leave(obj, target_location)   - called when an object leaves
                        this object in any fashion
     at_object_receive(obj, source_location) - called when this object receives
                        another object

     at_traverse(traversing_object, source_loc) - (exit-objects only)
                              handles all moving across the exit, including
                              calling the other exit hooks. Use super() to retain
                              the default functionality.
     at_after_traverse(traversing_object, source_location) - (exit-objects only)
                              called just after a traversal has happened.
     at_failed_traverse(traversing_object)      - (exit-objects only) called if
                       traversal fails and property err_traverse is not defined.

     at_msg_receive(self, msg, from_obj=None, **kwargs) - called when a message
                             (via self.msg()) is sent to this obj.
                             If returns false, aborts send.
     at_msg_send(self, msg, to_obj=None, **kwargs) - called when this objects
                             sends a message to someone via self.msg().

     return_appearance(looker) - describes this object. Used by "look"
                                 command by default
     at_desc(looker=None)      - called by 'look' whenever the
                                 appearance is requested.
     at_get(getter)            - called after object has been picked up.
                                 Does not stop pickup.
     at_drop(dropper)          - called when this object has been dropped.
     at_say(speaker, message)  - by default, called if an object inside this
                                 object speaks

     """


    def set_perception(self, perceptionkey, level, description):
        """
        This sets a perception on the room.
        Args:
            perceptionkey (str): The detail identifier to add (for
                aliases you need to add multiple keys to the
                same description). Case-insensitive.
            level (int): Level of the perception needed to access the information.
            description (str): The text to return when looking
                at the given perceptionkey.
        """
        if self.db.perception_details:
            if perceptionkey in self.db.perception_details:
                self.db.perception_details[perceptionkey].append((level, description))
            else:
                self.db.perception_details.update({perceptionkey: [(level, description)]})
        else:
            self.db.perception_details = {perceptionkey: [(level, description)]}

    def return_perception(self, perceptionkey, perceptionlevel):
        """
        This looks for an Attribute "obj_perception" and possibly
        returns the value of it.
        Args:
            perceptionkey (str): The perception detail being looked at. This is
                case-insensitive.
        """

        look_results = []

        if self.db.perception_details:
            perception_details = self.db.perception_details.get(perceptionkey, None)
            for details in perception_details:
                if details[0] <= perceptionlevel:
                    look_results.append(details[1])
            return look_results
        else:
            return

    def return_appearance(self, looker):
        string = super().return_appearance(looker)

        object = self
        # Set value of perception/tracking key for returning values.
        looker_perception = looker.db.perception
        # Returns list of messages if anything
        object_perception_results = self.return_perception(object, looker_perception)

        if object_perception_results:
            perception_message = f"|015Perception|n - After careful inspection of the {object}, you discover the following:"
            results = [string, perception_message]

            for perception_result in object_perception_results:
                results.append(perception_result)
            for result in results:
                looker.msg(f"|430{result}|n\n\n")
        else:
            return string


    # def at_pre_unpuppet(self):

    #     # Notify all followers that they are no longer following this character.
    #     if (self.db.isLeading == True):
    #         for char in self.db.followers:
    #             charFollower = self.search(char, global_search=True)
    #             if (charFollower):
    #                 charFollower.db.leader = []
    #                 charFollower.db.isFollowing = False
    #                 charFollower.msg("|540You are no longer following " + self.key + ".|n")

    #     # Remove this character from the followers array of their Leader, if they were following one.
    #     if (self.db.leader != []):
    #         charLeader = self.search(self.db.leader, global_search=True)
    #         # Remove the character from the Leader's followers array
    #         if (charLeader):
    #             try:
    #                 charLeader.db.followers.remove(self.key)
    #                 tempList = list(charLeader.db.followers)
    #                 if (len(tempList) == 0):
    #                     charLeader.db.isLeader = False
    #                 charLeader.msg("|540"+ self.key + " is no longer following you.|n")
    #             except ValueError:
    #                 self.msg("|540You are no longer following " + charLeader.key + "|n")

    #     # Clean up all db values.
    #     self.db.leader = []
    #     self.db.isLeading = False
    #     self.db.isFollowing = False
    #     self.db.followers = []

    #     pass


"""
Carnival - Ticket Box
"""

class ObjTicketBox(DefaultObject):
    """
    Available command:

    push button

    """
    def at_object_creation(self):
        "Called when object is first created"
        # Maintain state of object
        self.db.hasWinner = False
        self.db.characters = []
        self.db.counter = 0
        self.locks.add("get:false()")
        self.db.desc = "\n|yThis is a large wooden box, carved with filigree and inlaid at odd places with ruddy, fake looking gems. On the top of the box is a small black button. Just beneath this button is a small, tarnished bronze plaque that reads, 'Push Me for a Smile'|n\n|rOOG - Usage: push button|n"

        # Add command set for interacting with box
        self.cmdset.add_default(BoxCmdSet, permanent=True)

class ObjJesterTicket(DefaultObject):
    """
    Object that simply generates a description
    based on the result from a box button push.
    """

    def at_object_creation(self):
        self.db.desc = "|yThis is a small, rectangular slip of stained paper. On one side is the black and white stamp of a sinister looking jester."
        return

class ObjSkullTicket(DefaultObject):
    """
    Object that simply generates a description
    based on the result from a box button push.
    """

    def at_object_creation(self):
        self.db.desc = "|yThis is a small, rectangular slip of stained paper. On one side is the faded black and white stamp of a grinning skull."
        return


"""
Crafting Objects
"""

class Forge(DefaultObject):
    """
    Available commands:

    forge <item>
    repair <item>
    """

    def at_object_creation(self):
        "Called when object is first created"
        # Maintain state of object
        self.locks.add("get:false()")
        self.db.blacksmith_text = "|430Usage: \nforge <item>\nrepair <item>\nEnter the item name with underscores as in, iron_medium_weapon.|n"
        self.db.desc = "\nThis is a large forge as is used by a blacksmith in their trade. Metal items are heated here, until they are pliable enough to be molded and shaped by a mighty hammer and the smith's labor."

    def return_appearance(self, looker):
        string = super().return_appearance(looker)
        if looker.db.blacksmith:
            string += f"\n\n{self.db.blacksmith_text}"
        return string


class BowyerWorkbench(DefaultObject):
    """
    Available commands:

    craft <item>
    repair <item>
    """

    def at_object_creation(self):
        "Called when object is first created"
        # Maintain state of object
        self.locks.add("get:false()")
        self.db.desc = "\nThis is a large workshop used by bowyers in their trade. Here wood is hewn, shaped, and laminated to become a masterfully crafted instrument of death. So too, are thin shafts wittled, their ends bound in a waxed string that to them binds the delicate feathers of a bird."
        self.db.bowyer_text = "|430Usage: \ncraft <item>\nrepair <item>\nEnter the item name with underscores as in, masterwork_bow.|n"

    def return_appearance(self, looker):
        string = super().return_appearance(looker)
        if looker.db.bowyer:
            string += f"\n\n{self.db.bowyer_text}"
        return string

class ArtificerWorkbench(DefaultObject):
    """
    Available commands:

    craft <item>
    repair <item>
    """

    def at_object_creation(self):
        "Called when object is first created"
        # Maintain state of object
        self.locks.add("get:false()")
        self.db.desc = "\nThis is a large workshop used by artificers in their trade. Here raw materials are wrought into core components for all manner of masterfully crafted items. Clothing, tools, and other various and sundry items pour out from behind these walls, and onto the stone and earth streets, or into the wagons of world-traveling traders."
        self.db.artificer_text = "|430Usage: \ncraft <item>\nEnter the item name with underscores as in, fine_clothing.|n"

    def return_appearance(self, looker):
        string = super().return_appearance(looker)
        if looker.db.artificer:
            string += f"\n\n{self.db.artificer_text}"
        return string

class GunsmithWorkbench(DefaultObject):
    """
    Available commands:

    craft <item>
    repair <item>
    """

    def at_object_creation(self):
        "Called when object is first created"
        # Maintain state of object
        self.locks.add("get:false()")
        self.db.desc = "\nThis is a large workshop used by gunsmiths in their trade. Metal and wood are expertly crafted and shaped into the core components of black-powder pistols. Many barrels of water surround the small structure given its penchant for setting alight."
        self.db.gunsmith_text = "|430Usage: \ncraft <item>\nrepair <item>\nEnter the item name with underscores as in, masterwork_pistol.|n"

    def return_appearance(self, looker):
        string = super().return_appearance(looker)
        if looker.db.gunsmith:
            string += f"\n\n{self.db.gunsmith_text}"
        return string

class BlacksmithObject(DefaultObject):

    def at_object_creation(self):
        self.db.level = 0
        self.db.required_resources = 0
        self.db.iron_ingots = 0
        self.db.cloth =  0
        self.db.refined_wood = 0
        self.db.leather = 0
        self.db.value_copper = 0
        self.db.value_silver = 0
        self.db.value_gold = 0
        self.db.patched = False

class WeaponObject(BlacksmithObject):
    def at_object_creation(self):
        self.db.damage = 0
        self.db.broken = False
        self.db.twohanded = False
        self.db.trait_one = []
        self.db.trait_two = []
        self.db.trait_three = []
        self.db.patched = False

    def return_appearance(self, looker):
        string = super().return_appearance(looker)
        # Show desc and other objects inside
        looker.msg(f"{string}\n")

        level = self.db.level

        if self.db.arrow_slot:
            looker.msg(f"|430This quiver contains {self.db.quantity} arrows.|n")

        looker.msg(f"|430Level: {level}|n")

        looker.msg(f"|430Value - Silver Dragons: {self.db.value_silver}|n")

        if self.db.material_value:
            looker.msg(f"|430Durability (sunders received before broken): {self.db.material_value}|n")


class ArtificerObject(DefaultObject):
    def at_object_creation(self):
        self.db.uses = 0
        self.db.level = 0
        self.db.required_resources = 0
        self.db.iron_ingots = 0
        self.db.cloth =  0
        self.db.refined_wood = 0
        self.db.leather = 0
        self.db.value_copper = 0
        self.db.value_silver = 0
        self.db.value_gold = 0

    def return_appearance(self, looker):
        string = super().return_appearance(looker)

        # Show desc and other objects inside
        looker.msg(f"{string}\n")

        level = self.db.level

        if self.db.uses:
            looker.msg(f"|430This {self.key} has {self.db.uses} remaining.|n")

        if self.db.resist:
            looker.msg(f"|430{self.key} grant the wearer an additional {self.db.resist} resist(s).|n")

        if self.db.influential:
            looker.msg(f"|430{self.key} grant the wearer an additional {self.db.influential} point(s) of influential.|n")

        if self.db.espionage:
            looker.msg(f"|430{self.key} grants the wearer an additional {self.db.espionage} point(s) of espionage.|n")


        looker.msg(f"|430Level: {level}|n")

        looker.msg(f"|430Value - Silver Dragons: {self.db.value_silver}|n")

"""
Storage Objects
This is the base class type for an object that contains resources as attributes, i.e. gold, refined wood, etc...
"""

class Container(DefaultObject):
    """
    Contains entries for resources and currency to support the economic system.
    """
    def at_object_creation(self):
        self.db.is_locked = False
        self.db.gold = 0
        self.db.silver = 0
        self.db.copper = 0
        self.db.iron_ingots = 0
        self.db.refined_wood = 0
        self.db.leather = 0
        self.db.cloth = 0

    def return_appearance(self, looker):
        # Get desc and default text for object.
        string = super().return_appearance(looker)

        # Get values for db entries.
        gold = self.db.gold
        silver = self.db.silver
        copper = self.db.copper
        iron_ingots = self.db.iron_ingots
        refined_wood = self.db.refined_wood
        leather = self.db.leather
        cloth = self.db.cloth

        # Show desc and other objects inside
        looker.msg(f"{string}\n")

        if gold:
            looker.msg(f"|540Gold|n: {gold}\n")

        if silver:
            looker.msg(f"|=tSilver|n: {silver}\n")

        if copper:
            looker.msg(f"|310Copper|n: {copper}\n")

        if iron_ingots:
            looker.msg(f"|=kIron|n: {iron_ingots}\n")

        if refined_wood:
            looker.msg(f"|210Wood|n: {refined_wood}\n")

        if leather:
            looker.msg(f"|322Leather|n: {leather}\n")

        if cloth:
            looker.msg(f"|020Cloth|n: {cloth}")
