
# Local imports
from typeclasses.characters import Character
from evennia.prototypes import prototypes
from evennia import create_object, spawn, utils
# from commands.combat import Helper

# Imports
import random


class Npc(Character):
    """
    A NPC typeclass which extends the character class.
    """

    def at_char_entered(self, character):
        """
         A simple is_aggressive check.
         Can be expanded upon later.
        """
        pass

    def on_switch(self):
        self.db.is_aggressive = True

    def off_switch(self):
        self.db.is_aggressive = False


class GreenMeleeSoldierOneHanded(Npc):
    """
    Generic solider NPC
    """
    def at_object_creation(self):
        "This is called when object is first created, only."
        # Entries for general stats
        self.db.master_of_arms = 1
        self.db.sniper = 1
        self.db.armor = 0
        self.db.armor_specialist = 1
        self.db.tough = 1
        self.db.body = 3
        self.db.av = 0
        self.db.resilience = 1
        self.db.indomitable = 0
        self.db.perception = 0
        self.db.tracking = 0

        # Entries for hit location system
        self.db.targetArray = ["torso", "torso", "right arm", "left arm", "right leg", "left leg"]
        self.db.right_arm = 1
        self.db.left_arm = 1
        self.db.right_leg = 1
        self.db.left_leg = 1
        self.db.torso = 1

        # Entries for status effects
        self.db.weakness = 0
        self.db.bleed_points = 3
        self.db.death_points = 3

        # Entries for skill proficencies
        self.db.gunner = 1
        self.db.archer = 1
        self.db.shields = 1
        self.db.melee_weapons = 1
        self.db.armor_proficiency = 1

        # Entries for combat
        self.db.resist = 0
        self.db.disarm = 1
        self.db.cleave = 0
        self.db.sunder = 0
        self.db.stun = 0
        self.db.stagger = 1
        self.db.weapon_level = 0
        self.db.shield_value = 0
        self.db.wyldinghand = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.is_aggressive = False
        self.db.skip_turn = False
        self.db.is_staggered = False

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

        # Clear inventory
        self.remove_equipment()

    def remove_equipment(self):
        inventory = self.contents
        [obj.delete() for obj in inventory]

    def make_equipment(self):
        prototype = prototypes.search_prototype("iron_medium_weapon", require_single=True)
        armor_prototype = prototypes.search_prototype("iron_coat_of_plates", require_single=True)
        shield_prototype = prototypes.search_prototype("iron_shield", require_single=True)
        # Get prototype data
        longsword_data = prototype[0]
        armor_data = armor_prototype[0]
        shield_data = shield_prototype[0]
        # Spawn item using data
        weapon_item = spawn(longsword_data)
        armor_item = spawn(armor_data)
        shield_item = spawn(shield_data)
        # Move item to caller's inventory
        weapon_item[0].move_to(self, quiet=True)
        armor_item[0].move_to(self, quiet=True)
        shield_item[0].move_to(self, quiet=True)
        # Equip items
        self.execute_cmd('equip iron medium weapon')
        self.execute_cmd('equip iron coat of plates')
        self.execute_cmd('equip iron shield')


    def at_char_entered(self, character):
        # Do stuff to equip your character
        # Choose a random command and run it
        if self.db.is_aggressive and self.db.bleed_points:
            inventory = self.contents
            weapons = [item for item in inventory if item.db.damage]

            if len(weapons) == 0:
                self.make_equipment()

            command = self.command_picker(character)
            self.execute_cmd(command)
        else:
            return


    def command_picker(self, target):
        """
        When it is this npcs turn to act they will pick from their available combat commands at random.
        1. Create dict of command key and self.db.<active_martial_skill_att> -> "stun": combat_stats.get(self.db.stun, 0).
        Need to import Helper to make this work.
        2. Every time the at_char_entered command fires, this is what happens:
        3. Generate array of possible commands as ["strike", other values are made by calling the combat_bank keys based on value != 0]
        4. Choose a random element of the array and execute_cmd
        """
        # Form execute_cmd template, choosing from random commands
        # helper = Helper(self)
        # combat_bank = helper.activeMartialCounter(self)
        amSkills = {
        "stun": self.db.stun,
        "disarm": self.db.disarm,
        "sunder": self.db.sunder,
        "stagger": self.db.stagger,
        "cleave": self.db.cleave
        }

        # Generate an array of possible commands.
        ams_commands = [(command,)*value for command, value in amSkills.items() if value != 0]
        flat_ams_commands = [attack for groups in ams_commands for attack in groups]
        # Add free command to list
        flat_ams_commands.append("strike")
        # Choose random command
        chosen_command = random.choice(flat_ams_commands)
        # Catch exceptions to running active martial skills - weakness condition
        # Make sure npc is equipped:

        if not self.db.right_slot or self.db.left_slot:
            self.execute_cmd('equip iron medium weapon')
            pass

        # Random command is strike. Run it, else check to make sure npc can run an active martial skill w/o exception.
        if chosen_command not in amSkills:
            if not target.db.bleed_points:
                action_string = 'disengage'
            else:
                action_string = chosen_command + ' ' + target.key
        else:
            # If target is in dying count, disengage, else run free combat command.
            if not target.db.bleed_points:
                action_string = 'disengage'
            else:
                chosen_command = 'strike' if self.db.weakness else chosen_command
                # Establish command string
                action_string = chosen_command + ' ' + target.key

        return action_string


class GreenMeleeSoldierTwoHanded(GreenMeleeSoldierOneHanded):
    """
    Generic solider NPC
    """
    def at_object_creation(self):
        "This is called when object is first created, only."
        # Entries for general stats
        self.db.master_of_arms = 1
        self.db.armor = 0
        self.db.armor_specialist = 1
        self.db.tough = 1
        self.db.body = 3
        self.db.av = 0
        self.db.resilience = 1
        self.db.indomitable = 0
        self.db.perception = 0
        self.db.tracking = 0

        # Entries for hit location system
        self.db.targetArray = ["torso", "torso", "right arm", "left arm", "right leg", "left leg"]
        self.db.right_arm = 1
        self.db.left_arm = 1
        self.db.right_leg = 1
        self.db.left_leg = 1
        self.db.torso = 1

        # Entries for status effects
        self.db.weakness = 0
        self.db.bleed_points = 3
        self.db.death_points = 3

        # Entries for combat
        self.db.resist = 0
        self.db.disarm = 0
        self.db.cleave = 1
        self.db.sunder = 1
        self.db.stun = 0
        self.db.stagger = 0
        self.db.weapon_level = 0
        self.db.shield_value = 0
        self.db.wyldinghand = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.is_aggressive = False
        self.db.skip_turn = False
        self.db.melee_weapons = 1
        self.db.armor_proficiency = 1

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

        # Clear inventory
        self.remove_equipment()

    def remove_equipment(self):
        inventory = self.contents
        [obj.delete() for obj in inventory]

    def make_equipment(self):
        prototype = prototypes.search_prototype("iron_large_weapon", require_single=True)
        armor_prototype = prototypes.search_prototype("iron_coat_of_plates", require_single=True)
        # Get prototype data
        large_data = prototype[0]
        armor_data = armor_prototype[0]
        # Spawn item using data
        weapon_item = spawn(large_data)
        armor_item = spawn(armor_data)
        # Move item to caller's inventory
        weapon_item[0].move_to(self, quiet=True)
        armor_item[0].move_to(self, quiet=True)
        # Equip items
        self.execute_cmd('equip iron large weapon')
        self.execute_cmd('equip iron coat of plates')


    def at_char_entered(self, character):
        # Do stuff to equip your character
        # Choose a random command and run it
        if self.db.is_aggressive and self.db.bleed_points:
            inventory = self.contents
            weapons = [item for item in inventory if item.db.damage]

            if len(weapons) == 0:
                self.make_equipment()

            command = self.command_picker(character)
            self.execute_cmd(command)
        else:
            return


    def command_picker(self, target):
        """
        When it is this npcs turn to act they will pick from their available combat commands at random.
        1. Create dict of command key and self.db.<active_martial_skill_att> -> "stun": combat_stats.get(self.db.stun, 0).
        Need to import Helper to make this work.
        2. Every time the at_char_entered command fires, this is what happens:
        3. Generate array of possible commands as ["strike", other values are made by calling the combat_bank keys based on value != 0]
        4. Choose a random element of the array and execute_cmd
        """
        # Form execute_cmd template, choosing from random commands
        # helper = Helper(self)
        # combat_bank = helper.activeMartialCounter(self)
        amSkills = {
        "stun": self.db.stun,
        "disarm": self.db.disarm,
        "sunder": self.db.sunder,
        "stagger": self.db.stagger,
        "cleave": self.db.cleave
        }

        # Generate an array of possible commands.
        ams_commands = [(command,)*value for command, value in amSkills.items() if value != 0]
        flat_ams_commands = [attack for groups in ams_commands for attack in groups]
        # Add free command to list
        flat_ams_commands.append("strike")
        # Choose random command
        chosen_command = random.choice(flat_ams_commands)
        # Catch exceptions to running active martial skills - weakness condition
        # Make sure npc is equipped:

        if not self.db.right_slot or self.db.left_slot:
            self.execute_cmd('equip iron large weapon')
            pass

        # Random command is strike. Run it, else check to make sure npc can run an active martial skill w/o exception.
        if chosen_command not in amSkills:
            if not target.db.bleed_points:
                action_string = 'disengage'
            else:
                action_string = chosen_command + ' ' + target.key
        else:
            # If target is in dying count, disengage, else run free combat command.
            if not target.db.bleed_points:
                action_string = 'disengage'
            else:
                chosen_command = 'strike' if self.db.weakness else chosen_command
                # Establish command string
                action_string = chosen_command + ' ' + target.key

        return action_string

class GreenSoldierBow(GreenMeleeSoldierOneHanded):
    """
    Generic solider NPC
    """
    def at_object_creation(self):
        "This is called when object is first created, only."
        # Entries for general stats
        self.db.master_of_arms = 1
        self.db.armor = 0
        self.db.armor_specialist = 1
        self.db.tough = 1
        self.db.body = 3
        self.db.av = 0
        self.db.resilience = 1
        self.db.indomitable = 0
        self.db.perception = 0
        self.db.tracking = 0

        # Entries for hit location system
        self.db.targetArray = ["torso", "torso", "right arm", "left arm", "right leg", "left leg"]
        self.db.right_arm = 1
        self.db.left_arm = 1
        self.db.right_leg = 1
        self.db.left_leg = 1
        self.db.torso = 1

        # Entries for status effects
        self.db.weakness = 0
        self.db.bleed_points = 3
        self.db.death_points = 3

        # Entries for combat
        self.db.resist = 0
        self.db.disarm = 0
        self.db.cleave = 0
        self.db.sunder = 0
        self.db.stun = 0
        self.db.stagger = 0
        self.db.weapon_level = 0
        self.db.shield_value = 0
        self.db.wyldinghand = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.arrow_slot = []
        self.db.is_aggressive = False
        self.db.skip_turn = False
        self.db.archer = 1
        self.db.armor_proficiency = 1

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

        # Clear inventory
        self.remove_equipment()

    def remove_equipment(self):
        inventory = self.contents
        [obj.delete() for obj in inventory]

    def make_equipment(self):
        prototype = prototypes.search_prototype("bow", require_single=True)
        armor_prototype = prototypes.search_prototype("iron_coat_of_plates", require_single=True)
        arrow_prototype = prototypes.search_prototype("arrows", require_single=True)
        # Get prototype data
        bow_data = prototype[0]
        armor_data = armor_prototype[0]
        arrow_data = arrow_prototype[0]
        # Spawn item using data
        weapon_item = spawn(bow_data)
        armor_item = spawn(armor_data)
        arrow_item = spawn(arrow_data)
        # Move item to caller's inventory
        weapon_item[0].move_to(self, quiet=True)
        armor_item[0].move_to(self, quiet=True)
        arrow_item[0].move_to(self, quiet=True)
        # Equip items
        self.execute_cmd('equip bow')
        self.execute_cmd('equip iron coat of plates')
        self.execute_cmd('equip arrows')


    def at_char_entered(self, character):
        # Do stuff to equip your character
        # Choose a random command and run it
        if self.db.is_aggressive and self.db.bleed_points:
            inventory = self.contents
            weapons = [item for item in inventory if item.db.damage or item.db.is_bow]

            if len(weapons) == 0:
                self.make_equipment()

            command = self.command_picker(character)
            self.execute_cmd(command)
        else:
            return


    def command_picker(self, target):
        """
        When it is this npcs turn to act they will pick from their available combat commands at random.
        1. Create dict of command key and self.db.<active_martial_skill_att> -> "stun": combat_stats.get(self.db.stun, 0).
        Need to import Helper to make this work.
        2. Every time the at_char_entered command fires, this is what happens:
        3. Generate array of possible commands as ["strike", other values are made by calling the combat_bank keys based on value != 0]
        4. Choose a random element of the array and execute_cmd
        """
        # Form execute_cmd template, choosing from random commands
        # helper = Helper(self)
        # combat_bank = helper.activeMartialCounter(self)
        amSkills = {
        "disarm": self.db.disarm,
        "stagger": self.db.stagger
        }

        # Generate an array of possible commands.
        ams_commands = [(command,)*value for command, value in amSkills.items() if value != 0]
        flat_ams_commands = [attack for groups in ams_commands for attack in groups]
        # Add free command to list
        flat_ams_commands.append("shoot")
        # Choose random command
        chosen_command = random.choice(flat_ams_commands)
        # Catch exceptions to running active martial skills - weakness condition
        # Make sure npc is equipped:

        if not self.db.right_slot or self.db.left_slot:
            self.execute_cmd('equip bow')
            pass

        # Random command is strike. Run it, else check to make sure npc can run an active martial skill w/o exception.
        if chosen_command not in amSkills:
            if not target.db.bleed_points:
                action_string = 'disengage'
            else:
                action_string = chosen_command + ' ' + target.key
        else:
            # If target is in dying count, disengage, else run free combat command.
            if not target.db.bleed_points:
                action_string = 'disengage'
            else:
                chosen_command = 'shoot' if self.db.weakness else chosen_command
                # Establish command string
                action_string = chosen_command + ' ' + target.key

        return action_string


class BlueMeleeSoldierOneHanded(Npc):
    """
    Generic solider NPC
    """
    def at_object_creation(self):
        "This is called when object is first created, only."
        # Entries for general stats
        self.db.master_of_arms = 2
        self.db.armor = 0
        self.db.armor_specialist = 1
        self.db.tough = 2
        self.db.body = 3
        self.db.av = 0
        self.db.resilience = 1
        self.db.indomitable = 0
        self.db.perception = 0
        self.db.tracking = 0

        # Entries for hit location system
        self.db.targetArray = ["torso", "torso", "right arm", "left arm", "right leg", "left leg"]
        self.db.right_arm = 1
        self.db.left_arm = 1
        self.db.right_leg = 1
        self.db.left_leg = 1
        self.db.torso = 1

        # Entries for status effects
        self.db.weakness = 0
        self.db.bleed_points = 3
        self.db.death_points = 3

        # Entries for combat
        self.db.resist = 0
        self.db.disarm = 2
        self.db.cleave = 0
        self.db.sunder = 0
        self.db.stun = 1
        self.db.stagger = 2
        self.db.weapon_level = 0
        self.db.shield_value = 0
        self.db.wyldinghand = 0
        self.db.shields = 1
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.is_aggressive = False
        self.db.skip_turn = False
        self.db.melee_weapons = 1
        self.db.armor_proficiency = 1

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

        # Clear inventory
        self.remove_equipment()

    def remove_equipment(self):
        inventory = self.contents
        [obj.delete() for obj in inventory]

    def make_equipment(self):
        prototype = prototypes.search_prototype("hardened_iron_medium_weapon", require_single=True)
        armor_prototype = prototypes.search_prototype("hardened_iron_coat_of_plates", require_single=True)
        shield_prototype = prototypes.search_prototype("hardened_iron_shield", require_single=True)
        # Get prototype data
        longsword_data = prototype[0]
        armor_data = armor_prototype[0]
        shield_data = shield_prototype[0]
        # Spawn item using data
        weapon_item = spawn(longsword_data)
        armor_item = spawn(armor_data)
        shield_item = spawn(shield_data)
        # Move item to caller's inventory
        weapon_item[0].move_to(self, quiet=True)
        armor_item[0].move_to(self, quiet=True)
        shield_item[0].move_to(self, quiet=True)
        # Equip items
        self.execute_cmd('equip hardened iron medium weapon')
        self.execute_cmd('equip hardened iron coat of plates')
        self.execute_cmd('equip hardened iron shield')


    def at_char_entered(self, character):
        # Do stuff to equip your character
        # Choose a random command and run it
        if self.db.is_aggressive and self.db.bleed_points:
            inventory = self.contents
            weapons = [item for item in inventory if item.db.damage]

            if len(weapons) == 0:
                self.make_equipment()

            command = self.command_picker(character)
            self.execute_cmd(command)
        else:
            return


    def command_picker(self, target):
        """
        When it is this npcs turn to act they will pick from their available combat commands at random.
        1. Create dict of command key and self.db.<active_martial_skill_att> -> "stun": combat_stats.get(self.db.stun, 0).
        Need to import Helper to make this work.
        2. Every time the at_char_entered command fires, this is what happens:
        3. Generate array of possible commands as ["strike", other values are made by calling the combat_bank keys based on value != 0]
        4. Choose a random element of the array and execute_cmd
        """
        # Form execute_cmd template, choosing from random commands
        # helper = Helper(self)
        # combat_bank = helper.activeMartialCounter(self)
        amSkills = {
        "stun": self.db.stun,
        "disarm": self.db.disarm,
        "sunder": self.db.sunder,
        "stagger": self.db.stagger,
        "cleave": self.db.cleave
        }

        # Generate an array of possible commands.
        ams_commands = [(command,)*value for command, value in amSkills.items() if value != 0]
        flat_ams_commands = [attack for groups in ams_commands for attack in groups]
        # Add free command to list
        flat_ams_commands.append("strike")
        # Choose random command
        chosen_command = random.choice(flat_ams_commands)
        self.caller.location.msg_contents(f"My chosen command is: {chosen_command}")
        # Catch exceptions to running active martial skills - weakness condition
        # Make sure npc is equipped:

        if not self.db.right_slot or self.db.left_slot:
            self.execute_cmd('equip hardened iron medium weapon')
            pass

        # Random command is strike. Run it, else check to make sure npc can run an active martial skill w/o exception.
        if chosen_command not in amSkills:
            if not target.db.bleed_points:
                action_string = 'disengage'
            else:
                action_string = chosen_command + ' ' + target.key
        else:
            # If target is in dying count, disengage, else run free combat command.
            if not target.db.bleed_points:
                action_string = 'disengage'
            else:
                chosen_command = 'strike' if self.db.weakness else chosen_command
                # Establish command string
                action_string = chosen_command + ' ' + target.key
                self.caller.location.msg_contents(f"My chosen action string is: {action_string}")

        return action_string


class BlueMeleeSoldierTwoHanded(Npc):
    """
    Generic solider NPC
    """
    def at_object_creation(self):
        "This is called when object is first created, only."
        # Entries for general stats
        self.db.master_of_arms = 2
        self.db.armor = 0
        self.db.armor_specialist = 1
        self.db.tough = 2
        self.db.body = 3
        self.db.av = 0
        self.db.resilience = 1
        self.db.indomitable = 0
        self.db.perception = 0
        self.db.tracking = 0

        # Entries for hit location system
        self.db.targetArray = ["torso", "torso", "right arm", "left arm", "right leg", "left leg"]
        self.db.right_arm = 1
        self.db.left_arm = 1
        self.db.right_leg = 1
        self.db.left_leg = 1
        self.db.torso = 1

        # Entries for status effects
        self.db.weakness = 0
        self.db.bleed_points = 3
        self.db.death_points = 3

        # Entries for combat
        self.db.resist = 0
        self.db.disarm = 0
        self.db.cleave = 2
        self.db.sunder = 2
        self.db.stun = 0
        self.db.stagger = 0
        self.db.weapon_level = 0
        self.db.shield_value = 0
        self.db.wyldinghand = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.is_aggressive = False
        self.db.skip_turn = False
        self.db.melee_weapons = 1
        self.db.armor_proficiency = 1

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

        # Clear inventory
        self.remove_equipment()

    def remove_equipment(self):
        inventory = self.contents
        [obj.delete() for obj in inventory]

    def make_equipment(self):
        prototype = prototypes.search_prototype("hardened_iron_large_weapon", require_single=True)
        armor_prototype = prototypes.search_prototype("hardened_iron_coat_of_plates", require_single=True)
        # Get prototype data
        large_data = prototype[0]
        armor_data = armor_prototype[0]
        # Spawn item using data
        weapon_item = spawn(large_data)
        armor_item = spawn(armor_data)
        # Move item to caller's inventory
        weapon_item[0].move_to(self, quiet=True)
        armor_item[0].move_to(self, quiet=True)
        # Equip items
        self.execute_cmd('equip hardened iron large weapon')
        self.execute_cmd('equip hardened iron coat of plates')


    def at_char_entered(self, character):
        # Do stuff to equip your character
        # Choose a random command and run it
        if self.db.is_aggressive and self.db.bleed_points:
            inventory = self.contents
            weapons = [item for item in inventory if item.db.damage]

            if len(weapons) == 0:
                self.make_equipment()

            command = self.command_picker(character)
            self.execute_cmd(command)
        else:
            return


    def command_picker(self, target):
        """
        When it is this npcs turn to act they will pick from their available combat commands at random.
        1. Create dict of command key and self.db.<active_martial_skill_att> -> "stun": combat_stats.get(self.db.stun, 0).
        Need to import Helper to make this work.
        2. Every time the at_char_entered command fires, this is what happens:
        3. Generate array of possible commands as ["strike", other values are made by calling the combat_bank keys based on value != 0]
        4. Choose a random element of the array and execute_cmd
        """
        # Form execute_cmd template, choosing from random commands
        # helper = Helper(self)
        # combat_bank = helper.activeMartialCounter(self)
        amSkills = {
        "stun": self.db.stun,
        "disarm": self.db.disarm,
        "sunder": self.db.sunder,
        "stagger": self.db.stagger,
        "cleave": self.db.cleave
        }

        # Generate an array of possible commands.
        ams_commands = [(command,)*value for command, value in amSkills.items() if value != 0]
        flat_ams_commands = [attack for groups in ams_commands for attack in groups]
        # Add free command to list
        flat_ams_commands.append("strike")
        # Choose random command
        chosen_command = random.choice(flat_ams_commands)
        # Catch exceptions to running active martial skills - weakness condition
        # Make sure npc is equipped:

        if not self.db.right_slot or self.db.left_slot:
            self.execute_cmd('equip hardened iron large weapon')
            pass

        # Random command is strike. Run it, else check to make sure npc can run an active martial skill w/o exception.
        if chosen_command not in amSkills:
            if not target.db.bleed_points:
                action_string = 'disengage'
            else:
                action_string = chosen_command + ' ' + target.key
        else:
            # If target is in dying count, disengage, else run free combat command.
            if not target.db.bleed_points:
                action_string = 'disengage'
            else:
                chosen_command = 'strike' if self.db.weakness else chosen_command
                # Establish command string
                action_string = chosen_command + ' ' + target.key

        return action_string

class BlueSoldierBow(Npc):
    """
    Generic solider NPC
    """
    def at_object_creation(self):
        "This is called when object is first created, only."
        # Entries for general stats
        self.db.master_of_arms = 2
        self.db.armor = 0
        self.db.armor_specialist = 1
        self.db.tough = 2
        self.db.body = 3
        self.db.av = 0
        self.db.resilience = 1
        self.db.indomitable = 0
        self.db.perception = 0
        self.db.tracking = 0

        # Entries for hit location system
        self.db.targetArray = ["torso", "torso", "right arm", "left arm", "right leg", "left leg"]
        self.db.right_arm = 1
        self.db.left_arm = 1
        self.db.right_leg = 1
        self.db.left_leg = 1
        self.db.torso = 1

        # Entries for status effects
        self.db.weakness = 0
        self.db.bleed_points = 3
        self.db.death_points = 3

        # Entries for combat
        self.db.resist = 0
        self.db.disarm = 1
        self.db.cleave = 0
        self.db.sunder = 0
        self.db.stun = 0
        self.db.stagger = 1
        self.db.weapon_level = 0
        self.db.shield_value = 0
        self.db.wyldinghand = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.arrow_slot = []
        self.db.is_aggressive = False
        self.db.skip_turn = False
        self.db.archer = 1
        self.db.armor_proficiency = 1
        self.db.sniper = 1

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

        # Clear inventory
        self.remove_equipment()

    def remove_equipment(self):
        inventory = self.contents
        [obj.delete() for obj in inventory]

    def make_equipment(self):
        prototype = prototypes.search_prototype("bow", require_single=True)
        armor_prototype = prototypes.search_prototype("hardened_iron_coat_of_plates", require_single=True)
        arrow_prototype = prototypes.search_prototype("arrows", require_single=True)
        # Get prototype data
        bow_data = prototype[0]
        armor_data = armor_prototype[0]
        arrow_data = arrow_prototype[0]
        # Spawn item using data
        weapon_item = spawn(bow_data)
        armor_item = spawn(armor_data)
        arrow_item = spawn(arrow_data)
        # Move item to caller's inventory
        weapon_item[0].move_to(self, quiet=True)
        armor_item[0].move_to(self, quiet=True)
        arrow_item[0].move_to(self, quiet=True)
        # Equip items
        self.execute_cmd('equip bow')
        self.execute_cmd('equip hardened iron coat of plates')
        self.execute_cmd('equip arrows')


    def at_char_entered(self, character):
        # Do stuff to equip your character
        # Choose a random command and run it
        if self.db.is_aggressive and self.db.bleed_points:
            inventory = self.contents
            weapons = [item for item in inventory if item.db.damage or item.db.is_bow]

            if len(weapons) == 0:
                self.make_equipment()

            command = self.command_picker(character)
            self.execute_cmd(command)
        else:
            return


    def command_picker(self, target):
        """
        When it is this npcs turn to act they will pick from their available combat commands at random.
        1. Create dict of command key and self.db.<active_martial_skill_att> -> "stun": combat_stats.get(self.db.stun, 0).
        Need to import Helper to make this work.
        2. Every time the at_char_entered command fires, this is what happens:
        3. Generate array of possible commands as ["strike", other values are made by calling the combat_bank keys based on value != 0]
        4. Choose a random element of the array and execute_cmd
        """
        # Form execute_cmd template, choosing from random commands
        # helper = Helper(self)
        # combat_bank = helper.activeMartialCounter(self)
        amSkills = {
        "disarm": self.db.disarm,
        "stagger": self.db.stagger
        }

        # Generate an array of possible commands.
        ams_commands = [(command,)*value for command, value in amSkills.items() if value != 0]
        flat_ams_commands = [attack for groups in ams_commands for attack in groups]
        # Add free command to list
        flat_ams_commands.append("shoot")
        # Choose random command
        chosen_command = random.choice(flat_ams_commands)
        # Catch exceptions to running active martial skills - weakness condition
        # Make sure npc is equipped:

        if not self.db.right_slot or self.db.left_slot:
            self.execute_cmd('equip bow')
            pass

        # Random command is strike. Run it, else check to make sure npc can run an active martial skill w/o exception.
        if chosen_command not in amSkills:
            if not target.db.bleed_points:
                action_string = 'disengage'
            else:
                action_string = chosen_command + ' ' + target.key
        else:
            # If target is in dying count, disengage, else run free combat command.
            if not target.db.bleed_points:
                action_string = 'disengage'
            else:
                chosen_command = 'shoot' if self.db.weakness else chosen_command
                # Establish command string
                action_string = chosen_command + ' ' + target.key

        return action_string



class GreenRevenant(Npc):
    """
    Level 1 Undead
    """

    def at_char_entered(self, character):
        # Choose a random command and run it
        command = self.command_picker(character)
        self.execute_cmd(command)


    def command_picker(self, target):
        """
        When it is this npcs turn to act they will pick from their available combat commands at random.
        1. Create dict of command key and self.db.<active_martial_skill_att> -> "stun": combat_stats.get(self.db.stun, 0).
        Need to import Helper to make this work.
        2. Every time the at_char_entered command fires, this is what happens:
        3. Generate array of possible commands as ["strike", other values are made by calling the combat_bank keys based on value != 0]
        4. Choose a random element of the array and execute_cmd
        """
        # Form execute_cmd template, choosing from random commands
        # helper = Helper(self)
        # combat_bank = helper.activeMartialCounter(self)
        amSkills = {
        "stun": self.db.stun,
        "disarm": self.db.disarm,
        "sunder": self.db.sunder,
        "stagger": self.db.stagger,
        "cleave": self.db.cleave
        }

        # Generate an array of possible commands.
        ams_commands = [(command,)*value for command, value in amSkills.items() if value != 0]
        flat_ams_commands = [attack for groups in ams_commands for attack in groups]
        # Add free command to list
        flat_ams_commands.append("strike")
        # Choose random command
        chosen_command = random.choice(flat_ams_commands)
        # Catch exceptions to running active martial skills - weakness condition
        # Make sure npc is equipped:
        if not self.db.right_slot or left_slot:
            self.execute_cmd('equip iron medium weapon')
            pass

        # Random command is strike. Run it, else check to make sure npc can run an active martial skill w/o exception.
        if chosen_command not in amSkills:
            if not target.db.bleed_points:
                action_string = 'disengage'
            else:
                action_string = chosen_command + ' ' + target.key
        else:
            # If target is in dying count, disengage, else run free combat command.
            if not target.db.bleed_points:
                action_string = 'disengage'
            else:
                chosen_command = 'strike' if self.db.weakness else chosen_command
                # Establish command string
                action_string = chosen_command + ' ' + target.key

        return action_string
