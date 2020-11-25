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
        self.db.sniper = 0
        self.db.armor = 0
        self.db.armor_specialist = 0
        self.db.tough = 0
        self.db.total_tough = 0
        self.db.body = 3
        self.db.total_body = 3
        self.db.av = 0
        self.db.resilience = 0
        self.db.influential = 0
        self.db.espionage = 0

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
        self.db.last_repair = 0

        # Entries for healing
        self.db.stabilize = 0
        self.db.medicine = 0
        self.db.battlefieldmedicine = 0
        self.db.chirurgeon = 0

        # Entries for skill proficencies
        self.db.gunner = 0
        self.db.archer = 0
        self.db.shields = 0
        self.db.melee_weapons = 0
        self.db.armor_proficiency = 0

        # Entries for status
        self.db.weakness = 0
        self.db.bleed_points = 3
        self.db.death_points = 3

        # Entries for combat
        self.db.melee = 0
        self.db.resist = 0
        self.db.total_resist = 0
        self.db.disarm = 0
        self.db.total_disarm = 0
        self.db.cleave = 0
        self.db.total_cleave = 0
        self.db.sunder = 0
        self.db.total_sunder = 0
        self.db.stun = 0
        self.db.total_stun = 0
        self.db.stagger = 0
        self.db.total_stagger = 0
        self.db.weapon_level = 0
        self.db.shield_value = 0
        self.db.twohanded = 0
        self.db.wyldinghand = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.is_aggressive = False
        self.db.skip_turn = False
        self.db.is_staggered = False

        # Char slots for equipping items
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.hand_slot = []
        self.db.foot_slot = []
        self.db.clothing_slot = []
        self.db.cloak_slot = []
        self.db.kit_slot = []
        self.db.arrow_slot = []
        self.db.bullet_slot = []

        # Entries for knights
        self.db.battlefieldcommander = 0
        self.db.rally = 0
        self.db.indomitable = 0

        # Entries for following
        self.db.isLeading = False
        self.db.leader = []
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
        self.db.arrows = 0


    def return_appearance(self, looker):
        """
        The return from this method is what
        looker sees when looking at this object.
        """
        text = super().return_appearance(looker)
        isBleeding = True if not self.db.body and self.db.bleed_points else False
        isDying = True if not self.db.bleed_points and not self.db.body else False

        # Return
        if isBleeding:
            return text + f"\n{self.key} |430is bleeding profusely from mutliple, serious wounds.|n"

        elif isDying:
            return text + f"\n{self.key} |430has succumbed to their injuries and is now unconscious.|n"

        else:
            return text

    def reset_stats(self):
        self.db.resist = self.db.total_resist
        self.db.disarm = self.db.total_disarm
        self.db.cleave = self.db.total_cleave
        self.db.sunder = self.db.total_sunder
        self.db.stun = self.db.total_stun
        self.db.stagger = self.db.total_stagger
        self.db.tough = self.db.total_tough

    # Changed for AI room response
    def at_after_move(self, source_location):
        """
        Default is to look around after a move
        Note:  This has been moved to room.at_object_receive
        """
        #self.execute_cmd('look')

        if (self.db.isLeading):
            for char in self.db.followers:
                if not char.db.in_combat and char.db.body > 0:
                    char.move_to(self.location)
                else:
                    char.db.isFollowing = False
                    char.db.leader = []
                    self.db.followers.remove(char)
                    tempList = list(self.db.followers)
                    if (len(tempList) == 0):
                        self.db.isLeading = False
                    self.msg("|430"+ char.key + " is no longer following you.|n")
                    char.msg("|430You are no longer following " + self.key + "|n")

        # If a follower performed a move away from the leader, they will be removed from the followers array and will
        # no longer be following the leader.
        if (self.db.isFollowing):

            leaderInRoom = self.search(self.db.leader)

            if not leaderInRoom:
                # Try removing them from the target's followers array.
                leader = self.search(self.db.leader, global_search=True)

                try:
                    leader.db.followers.remove(self)
                    tempList = list(leader.db.followers)
                    if (len(tempList) == 0):
                        leader.db.isLeading = False
                    self.msg("|430You are no longer following " + leader.key + "|n")
                    leader.msg("|430"+ self.key + " is no longer following you.|n")
                except ValueError:
                    self.msg("|430You are no longer following " + leader.key + "|n")

                self.db.isFollowing = False
                self.db.leader = []

        pass
