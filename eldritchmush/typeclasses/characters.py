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
        self.db.armor = 0
        self.db.armor_specialist = 0
        self.db.tough = 0
        self.db.body = 3
        self.db.av = 0
        self.db.resilience = 0

        # Entries for hit location system
        self.db.targetArray = ["torso", "torso", "right arm", "left arm", "right leg", "left leg"]
        self.db.right_arm = 1
        self.db.left_arm = 1
        self.db.right_leg = 1
        self.db.left_leg = 1
        self.db.torso = 1

        # Crafting attributes
        self.db.blacksmith = 0
        self.db.artificer = 0
        self.db.bowyer = 0
        self.db.gunsmith = 0
        self.db.alchemist = 0

        # Entries for healing
        self.db.stabilize = 0
        self.db.medicine = 0
        self.db.battlefieldmedicine = 0
        self.db.chiurgeon = 0

        # Entries for status effects
        self.db.weakness = 0
        self.db.bleed_points = 3
        self.db.death_points = 3

        # Entries for combat
        self.db.melee = 0
        self.db.resist = 0
        self.db.disarm = 0
        self.db.cleave = 0
        self.db.sunder = 0
        self.db.stun = 0
        self.db.stagger = 0
        self.db.weapon_level = 0
        self.db.shield_value = 0
        self.db.twohanded = 0
        self.db.wyldinghand = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.skip_turn = False
        self.db.battlefieldcommander = 0
        self.db.rally = 0
        # Entries for following
        self.db.isLeading = False
        self.db.leader = ""
        self.db.isFollowing = False
        self.db.followers = []
        # Entries for economy
        self.db.iron_ingots = 0
        self.db.refined_wood = 0
        self.db.leather = 0
        self.db.cloth = 0
        self.db.gold = 0
        self.db.silver = 0
        self.db.copper = 0


    def return_appearance(self, looker):
        """
        The return from this method is what
        looker sees when looking at this object.
        """
        text = super().return_appearance(looker)
        isBleeding = True if self.bleed_points else False
        isDying = True if not self.bleed_points else False

        # Check to see if player is fighting.
        if self in self.location.db.combat_loop:
            combat_string = f"{self.key} is currently in the midst of combat."

        # Return
        if isBleeding:
            return text + f"\n|400{self.key} is bleeding profusely from mutliple, serious wounds.|n"

        elif isDying:
            return text + f"\n|400{self.key} has succumbed to their injuries and is now unconscious.|n"

        else:
            return text + f"\n{combat_loop}"

    # Changed for AI room response
    def at_after_move(self, source_location):
        """
        Default is to look around after a move
        Note:  This has been moved to room.at_object_receive
        """
        #self.execute_cmd('look')
        pass

    def at_post_unpuppet(self, account):
        
        # Notify all followers that they are no longer following this character.
        if (self.db.isLeading == True):
            for char in self.db.followers:
                charFollower = self.search(char, global_search=True)
                if (charFollower):
                    charFollower.db.leader = ""
                    charFollower.db.isFollowing = False
                    charFollower.msg("|540You are no longer following " + self.key + ".|n")
        
        # Remove this character from the followers array of their Leader, if they were following one.
        if (self.db.leader != ""):
            charLeader = self.search(self.db.leader, global_search=True)
            # Remove the character from the Leader's followers array
            if (charLeader):
                try:      
                    charLeader.db.followers.remove(self.key)
                    if (charLeader.db.followers.len() == 0):
                        charLeader.db.isLeader = False
                    charLeader.msg("|540"+ self.key + " is no longer following you.|n")
                except ValueError:
                    self.msg("|540You are no longer following " + target.key + "|n")
        
        # Clean up all db values.
        self.db.leader = ""
        self.db.isLeading = False
        self.db.isFollowing = False
        self.db.followers = []