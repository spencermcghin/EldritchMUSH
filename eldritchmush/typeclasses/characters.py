"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
from evennia import DefaultCharacter


class Character(DefaultCharacter):
    """
    The Character defaults to reimplementing some of base Object's hook methods with the
    following functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead).
    at_after_move(source_location) - Launches the "look" command after every move.
    at_post_unpuppet(account) -  when Account disconnects from the Character, we
                    store the current location in the pre_logout_location Attribute and
                    move it to a None-location so the "unpuppeted" character
                    object does not need to stay on grid. Echoes "Account has disconnected"
                    to the room.
    at_pre_puppet - Just before Account re-connects, retrieves the character's
                    pre_logout_location Attribute and move it back on the grid.
    at_post_puppet - Echoes "AccountName has entered the game" to the room.

    """

    def at_object_creation(self):
        "This is called when object is first created, only."
        # Entries for general stats
        self.db.tracking = 0
        self.db.perception = 0
        self.db.master_of_arms = 0
        self.db.armor = 2
        self.db.armor_specialist = 0
        self.db.tough = 0
        self.db.body = 3
        self.db.av = 2

        # Entries for hit location system
        self.db.targetArray = ["torso", "torso", "right arm", "left arm", "right leg", "left leg"]
        self.db.right_arm = 1
        self.db.left_arm = 1
        self.db.right_leg = 1
        self.db.left_leg = 1
        self.db.torso = 1

        # Entries for healing
        self.db.stabilize = 0

        # Entries for status effects
        self.db.weakness = 0

        # Entries for combat
        self.db.melee = 0
        self.db.resist = 0
        self.db.disarm = 0
        self.db.cleave = 0
        self.db.sunder = 0
        self.db.stun = 0
        self.db.stagger = 0
        self.db.weapon_level = 0
        self.db.twohanded = 0
        self.db.wyldinghand = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1


    # def get_abilities(self):
    #     """
    #     Simple access method to return ability
    #     scores as a tuple (str,agi,mag)
    #     """
    #     return self.db.strength, self.db.agility, self.db.magic
