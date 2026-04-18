
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

    def at_object_creation(self):
        super().at_object_creation()
        self.db.is_npc = True

    def at_char_entered(self, character):
        """
         A simple is_aggressive check.
         Can be expanded upon later.
        """
        pass

    def at_object_receive(self, moved_obj, source_location, **kwargs):
        """When an item moves into this NPC, react if it's a player gift.

        For AI-driven NPCs (those with `ai_personality`), trigger an
        in-character LLM response so the NPC can acknowledge / thank /
        refuse / comment on what they were handed. The item itself
        stays in the NPC's inventory; the LLM only generates dialogue,
        not mechanical state changes.

        We DON'T fire on items moving via internal mechanisms (combat
        loot, populate scripts, admin @tel, etc.) — only when a
        Character with an account was the source.
        """
        try:
            super().at_object_receive(moved_obj, source_location, **kwargs)
        except Exception:
            pass

        if not self.attributes.get("ai_personality", default=None):
            return
        try:
            if (not source_location
                or not isinstance(source_location, Character)
                or not getattr(source_location, "db_account_id", None)):
                return
        except Exception:
            return
        if moved_obj == self:
            return

        item_name = getattr(moved_obj, "key", "an item")
        synthetic = (
            f"[GAME EVENT: {source_location.key} just handed you "
            f"{item_name}. Respond in-character — accept, refuse, "
            f"thank, comment, or barter.]"
        )
        try:
            from world import ai_npc

            def _on_reply(reply):
                if not reply:
                    return
                if self.location:
                    self.location.msg_contents(
                        f'|c{self.key}|n says, "{reply}"'
                    )
            ai_npc.chat(self, source_location, synthetic, _on_reply)
        except Exception:
            pass

    def take_combat_turn(self, target):
        """
        Called by the combat loop when it is this NPC's turn.
        Non-combatant NPCs disengage by default; combat subclasses override this.
        """
        self.execute_cmd("disengage")

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
        self.db.vigil = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.is_aggressive = True
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

    def take_combat_turn(self, target):
        """Called by the combat loop on this NPC's turn. Always executes regardless of is_aggressive."""
        inventory = self.contents
        weapons = [item for item in inventory if item.db.damage]
        if not weapons:
            self.make_equipment()
        command = self.command_picker(target)
        self.execute_cmd(command)

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
        if self.db.is_aggressive and self.db.bleed_points and self.db.combat_turn:
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

        if not self.db.right_slot:
            self.execute_cmd('equip iron medium weapon')

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
        self.db.vigil = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.is_aggressive = True
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
        if self.db.is_aggressive and self.db.bleed_points and self.db.combat_turn:
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

        if not self.db.right_slot:
            self.execute_cmd('equip iron large weapon')

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
        self.db.vigil = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.arrow_slot = []
        self.db.is_aggressive = True
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
        if self.db.is_aggressive and self.db.bleed_points and self.db.combat_turn:
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
        self.db.vigil = 0
        self.db.shields = 1
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.is_aggressive = True
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

    def take_combat_turn(self, target):
        """Called by the combat loop on this NPC's turn. Always executes regardless of is_aggressive."""
        inventory = self.contents
        weapons = [item for item in inventory if item.db.damage]
        if not weapons:
            self.make_equipment()
        command = self.command_picker(target)
        self.execute_cmd(command)

    def at_char_entered(self, character):
        # Do stuff to equip your character
        # Choose a random command and run it
        if self.db.is_aggressive and self.db.bleed_points and self.db.combat_turn:
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
        self.db.vigil = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.is_aggressive = True
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

    def take_combat_turn(self, target):
        """Called by the combat loop on this NPC's turn. Always executes regardless of is_aggressive."""
        inventory = self.contents
        weapons = [item for item in inventory if item.db.damage]
        if not weapons:
            self.make_equipment()
        command = self.command_picker(target)
        self.execute_cmd(command)

    def at_char_entered(self, character):
        # Do stuff to equip your character
        # Choose a random command and run it
        if self.db.is_aggressive and self.db.bleed_points and self.db.combat_turn:
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
        self.db.vigil = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.arrow_slot = []
        self.db.is_aggressive = True
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

    def take_combat_turn(self, target):
        """Called by the combat loop on this NPC's turn. Always executes regardless of is_aggressive."""
        inventory = self.contents
        weapons = [item for item in inventory if item.db.damage or item.db.is_bow]
        if not weapons:
            self.make_equipment()
        command = self.command_picker(target)
        self.execute_cmd(command)

    def at_char_entered(self, character):
        # Do stuff to equip your character
        # Choose a random command and run it
        if self.db.is_aggressive and self.db.bleed_points and self.db.combat_turn:
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


# ---------------------------------------------------------------------------
# New NPC types
# ---------------------------------------------------------------------------

class BanditMeleeOneHanded(Npc):
    """
    A human bandit fighter. Tougher than a basic zombie — medium weapon,
    more body, and sunder for disabling armour.
    """

    def at_object_creation(self):
        self.db.master_of_arms = 2
        self.db.armor = 1
        self.db.armor_specialist = 1
        self.db.tough = 1
        self.db.body = 5
        self.db.total_body = 5
        self.db.av = 1
        self.db.resilience = 1
        self.db.indomitable = 0
        self.db.perception = 1
        self.db.tracking = 0

        self.db.targetArray = ["torso", "torso", "right arm", "left arm", "right leg", "left leg"]
        self.db.right_arm = 1
        self.db.left_arm = 1
        self.db.right_leg = 1
        self.db.left_leg = 1
        self.db.torso = 1

        self.db.weakness = 0
        self.db.bleed_points = 3
        self.db.death_points = 3

        self.db.gunner = 0
        self.db.archer = 0
        self.db.shields = 1
        self.db.melee_weapons = 1
        self.db.armor_proficiency = 1

        self.db.resist = 1
        self.db.disarm = 1
        self.db.cleave = 0
        self.db.sunder = 1
        self.db.stun = 0
        self.db.stagger = 1
        self.db.weapon_level = 0
        self.db.shield_value = 0
        self.db.vigil = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.is_aggressive = True
        self.db.skip_turn = False
        self.db.is_staggered = False

    def make_equipment(self):
        from evennia import spawn
        weapon = spawn({"prototype_parent": "IRON_MEDIUM_WEAPON", "location": self})[0]
        self.db.right_slot = [weapon.key]
        # Iron medium weapon is level 1 → weaponValue(1) = 2
        self.db.weapon_level = 2

    def remove_equipment(self):
        for item in list(self.contents):
            if item.db.damage:
                item.delete()
        self.db.right_slot = []
        self.db.left_slot = []

    def command_picker(self, target):
        amSkills = {"sunder": self.db.sunder, "disarm": self.db.disarm, "stagger": self.db.stagger}
        flat = [c for c, v in amSkills.items() for _ in range(v)]
        flat.append("strike")
        chosen = random.choice(flat)
        if not self.db.right_slot:
            self.make_equipment()
        if not target.db.bleed_points:
            return "disengage"
        chosen = "strike" if self.db.weakness else chosen
        return f"{chosen} {target.key}"

    def take_combat_turn(self, target):
        if not self.db.right_slot:
            self.make_equipment()
        self.execute_cmd(self.command_picker(target))


class WildWolfNpc(Npc):
    """
    A wild wolf — fast, unarmoured, bite attack. Flees when bleeding.
    """

    def at_object_creation(self):
        self.db.master_of_arms = 1
        self.db.armor = 0
        self.db.armor_specialist = 0
        self.db.tough = 0
        self.db.body = 4
        self.db.total_body = 4
        self.db.av = 0
        self.db.resilience = 0
        self.db.indomitable = 0
        self.db.perception = 2
        self.db.tracking = 2

        self.db.targetArray = ["torso", "torso", "right arm", "left arm", "right leg", "left leg"]
        self.db.right_arm = 1
        self.db.left_arm = 1
        self.db.right_leg = 1
        self.db.left_leg = 1
        self.db.torso = 1

        self.db.weakness = 0
        self.db.bleed_points = 2
        self.db.death_points = 2

        self.db.gunner = 0
        self.db.archer = 0
        self.db.shields = 0
        self.db.melee_weapons = 1
        self.db.armor_proficiency = 0

        self.db.resist = 0
        self.db.disarm = 0
        self.db.cleave = 0
        self.db.sunder = 0
        self.db.stun = 0
        self.db.stagger = 1
        self.db.weapon_level = 0
        self.db.shield_value = 0
        self.db.vigil = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 0
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.is_aggressive = True
        self.db.skip_turn = False
        self.db.is_staggered = False

    def make_equipment(self):
        from evennia import spawn
        weapon = spawn({"prototype_parent": "IRON_SMALL_WEAPON",
                        "key": "wolf bite", "location": self})[0]
        self.db.right_slot = [weapon.key]
        # Small weapon is level 0 → weapon_level bonus 0
        self.db.weapon_level = 0

    def remove_equipment(self):
        for item in list(self.contents):
            if item.db.damage:
                item.delete()
        self.db.right_slot = []

    def command_picker(self, target):
        if not self.db.right_slot:
            self.make_equipment()
        if not self.db.bleed_points or not target.db.bleed_points:
            return "disengage"
        return f"{random.choice(['strike','strike','strike','stagger'])} {target.key}"

    def take_combat_turn(self, target):
        if not self.db.right_slot:
            self.make_equipment()
        self.execute_cmd(self.command_picker(target))


class SkeletonArcher(Npc):
    """
    An undead skeleton armed with a bow. Shoots until arrows run out,
    then falls back to melee.
    """

    def at_object_creation(self):
        self.db.master_of_arms = 1
        self.db.sniper = 1
        self.db.armor = 0
        self.db.armor_specialist = 0
        self.db.tough = 0
        self.db.body = 3
        self.db.total_body = 3
        self.db.av = 0
        self.db.resilience = 0
        self.db.indomitable = 0
        self.db.perception = 2
        self.db.tracking = 0

        self.db.targetArray = ["torso", "torso", "right arm", "left arm", "right leg", "left leg"]
        self.db.right_arm = 1
        self.db.left_arm = 1
        self.db.right_leg = 1
        self.db.left_leg = 1
        self.db.torso = 1

        self.db.weakness = 0
        self.db.bleed_points = 3
        self.db.death_points = 2

        self.db.gunner = 0
        self.db.archer = 1
        self.db.shields = 0
        self.db.melee_weapons = 1
        self.db.armor_proficiency = 0

        self.db.resist = 0
        self.db.disarm = 0
        self.db.cleave = 0
        self.db.sunder = 0
        self.db.stun = 0
        self.db.stagger = 0
        self.db.weapon_level = 0
        self.db.shield_value = 0
        self.db.vigil = 0
        self.db.shield = 0
        self.db.bow = 1
        self.db.activemartialskill = 0
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.arrow_slot = []
        self.db.body_slot = []
        self.db.is_aggressive = True
        self.db.skip_turn = False
        self.db.is_staggered = False

    def make_equipment(self):
        from evennia import spawn
        bow = spawn({"prototype_parent": "HUNTING_BOW", "location": self})[0]
        arrows = spawn({"prototype_parent": "ARROWS", "location": self})[0]
        self.db.right_slot = [bow.key]
        self.db.arrow_slot = [arrows.key]
        # Bow uses archer skill; weapon_level bonus from bow level
        bow_level = getattr(bow.db, 'level', 0) or 0
        from commands.combat import Helper
        self.db.weapon_level = Helper().weaponValue(bow_level)

    def remove_equipment(self):
        for item in list(self.contents):
            if item.db.damage or item.db.is_bow or item.db.arrow_slot:
                item.delete()
        self.db.right_slot = []
        self.db.arrow_slot = []

    def command_picker(self, target):
        if not self.db.right_slot:
            self.make_equipment()
        if not target.db.bleed_points:
            return "disengage"
        return f"{'shoot' if self.db.arrow_slot else 'strike'} {target.key}"

    def take_combat_turn(self, target):
        if not self.db.right_slot:
            self.make_equipment()
        self.execute_cmd(self.command_picker(target))


class CrowStriker(Npc):
    """
    Crow bandit striker — one-handed melee fighter. Mid-tier threat.
    Armed with an iron medium weapon; knows stun.
    """

    def at_object_creation(self):
        self.db.master_of_arms = 1
        self.db.armor = 0
        self.db.armor_specialist = 0
        self.db.tough = 1
        self.db.body = 3
        self.db.total_body = 3
        self.db.av = 0
        self.db.resilience = 0
        self.db.indomitable = 0
        self.db.perception = 0
        self.db.tracking = 0

        self.db.targetArray = ["torso", "torso", "right arm", "left arm", "right leg", "left leg"]
        self.db.right_arm = 1
        self.db.left_arm = 1
        self.db.right_leg = 1
        self.db.left_leg = 1
        self.db.torso = 1

        self.db.weakness = 0
        self.db.bleed_points = 3
        self.db.death_points = 3

        self.db.gunner = 0
        self.db.archer = 0
        self.db.shields = 0
        self.db.melee_weapons = 1
        self.db.armor_proficiency = 0

        self.db.resist = 0
        self.db.disarm = 0
        self.db.cleave = 0
        self.db.sunder = 0
        self.db.stun = 1
        self.db.stagger = 0
        self.db.weapon_level = 0
        self.db.shield_value = 0
        self.db.vigil = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.is_aggressive = True
        self.db.peaceful = False
        self.db.skip_turn = False
        self.db.is_staggered = False

        self.db.isLeading = False
        self.db.leader = []
        self.db.isFollowing = False
        self.db.followers = []

        self.db.iron_ingots = 0
        self.db.refined_wood = 0
        self.db.leather = 0
        self.db.cloth = 0
        self.db.gold = 0
        self.db.silver = 0
        self.db.copper = 0
        self.db.arrows = 0

    def make_equipment(self):
        from evennia import spawn
        weapon = spawn({"prototype_parent": "IRON_MEDIUM_WEAPON", "location": self})[0]
        self.db.right_slot = [weapon.key]
        self.db.weapon_level = 2

    def remove_equipment(self):
        for item in list(self.contents):
            if item.db.damage:
                item.delete()
        self.db.right_slot = []
        self.db.left_slot = []

    def command_picker(self, target):
        amSkills = {"stun": self.db.stun}
        flat = [c for c, v in amSkills.items() for _ in range(v)]
        flat.append("strike")
        chosen = random.choice(flat)
        if not self.db.right_slot:
            self.make_equipment()
        if not target.db.bleed_points:
            return "disengage"
        chosen = "strike" if self.db.weakness else chosen
        return f"{chosen} {target.key}"

    def take_combat_turn(self, target):
        if not self.db.right_slot:
            self.make_equipment()
        self.execute_cmd(self.command_picker(target))

    def at_char_entered(self, character):
        if self.db.is_aggressive and self.db.bleed_points and self.db.combat_turn:
            if not self.db.right_slot:
                self.make_equipment()
            command = self.command_picker(character)
            self.execute_cmd(command)


class CrowBruiser(Npc):
    """
    Crow bandit bruiser — heavy hitter with a two-handed weapon.
    Tougher than a Striker; knows sunder.
    """

    def at_object_creation(self):
        self.db.master_of_arms = 1
        self.db.armor = 0
        self.db.armor_specialist = 0
        self.db.tough = 2
        self.db.body = 3
        self.db.total_body = 3
        self.db.av = 2
        self.db.resilience = 0
        self.db.indomitable = 0
        self.db.perception = 0
        self.db.tracking = 0

        self.db.targetArray = ["torso", "torso", "right arm", "left arm", "right leg", "left leg"]
        self.db.right_arm = 1
        self.db.left_arm = 1
        self.db.right_leg = 1
        self.db.left_leg = 1
        self.db.torso = 1

        self.db.weakness = 0
        self.db.bleed_points = 3
        self.db.death_points = 3

        self.db.gunner = 0
        self.db.archer = 0
        self.db.shields = 0
        self.db.melee_weapons = 1
        self.db.armor_proficiency = 1

        self.db.resist = 0
        self.db.disarm = 0
        self.db.cleave = 0
        self.db.sunder = 1
        self.db.stun = 0
        self.db.stagger = 0
        self.db.weapon_level = 0
        self.db.shield_value = 0
        self.db.vigil = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.is_aggressive = True
        self.db.peaceful = False
        self.db.skip_turn = False
        self.db.is_staggered = False

        self.db.isLeading = False
        self.db.leader = []
        self.db.isFollowing = False
        self.db.followers = []

        self.db.iron_ingots = 0
        self.db.refined_wood = 0
        self.db.leather = 0
        self.db.cloth = 0
        self.db.gold = 0
        self.db.silver = 0
        self.db.copper = 0
        self.db.arrows = 0

    def make_equipment(self):
        from evennia import spawn
        weapon = spawn({"prototype_parent": "IRON_LARGE_WEAPON", "location": self})[0]
        self.db.right_slot = [weapon.key]
        self.db.weapon_level = 2

    def remove_equipment(self):
        for item in list(self.contents):
            if item.db.damage:
                item.delete()
        self.db.right_slot = []
        self.db.left_slot = []

    def command_picker(self, target):
        amSkills = {"sunder": self.db.sunder}
        flat = [c for c, v in amSkills.items() for _ in range(v)]
        flat.append("strike")
        chosen = random.choice(flat)
        if not self.db.right_slot:
            self.make_equipment()
        if not target.db.bleed_points:
            return "disengage"
        chosen = "strike" if self.db.weakness else chosen
        return f"{chosen} {target.key}"

    def take_combat_turn(self, target):
        if not self.db.right_slot:
            self.make_equipment()
        self.execute_cmd(self.command_picker(target))

    def at_char_entered(self, character):
        if self.db.is_aggressive and self.db.bleed_points and self.db.combat_turn:
            if not self.db.right_slot:
                self.make_equipment()
            command = self.command_picker(character)
            self.execute_cmd(command)


class CaleTheThorn(Npc):
    """
    Cale the Thorn — Crow lieutenant, boss of the Owl's Roost camp.
    Dangerous melee fighter with disarm, stagger, and cleave.
    Armed with a steel medium weapon.
    """

    def at_object_creation(self):
        self.db.master_of_arms = 2
        self.db.armor = 0
        self.db.armor_specialist = 1
        self.db.tough = 2
        self.db.body = 5
        self.db.total_body = 5
        self.db.av = 1
        self.db.resilience = 1
        self.db.indomitable = 0
        self.db.perception = 1
        self.db.tracking = 0

        self.db.targetArray = ["torso", "torso", "right arm", "left arm", "right leg", "left leg"]
        self.db.right_arm = 1
        self.db.left_arm = 1
        self.db.right_leg = 1
        self.db.left_leg = 1
        self.db.torso = 1

        self.db.weakness = 0
        self.db.bleed_points = 3
        self.db.death_points = 3

        self.db.gunner = 0
        self.db.archer = 0
        self.db.shields = 0
        self.db.melee_weapons = 2
        self.db.armor_proficiency = 1

        self.db.resist = 0
        self.db.disarm = 2
        self.db.cleave = 1
        self.db.sunder = 0
        self.db.stun = 0
        self.db.stagger = 2
        self.db.weapon_level = 0
        self.db.shield_value = 0
        self.db.vigil = 0
        self.db.shield = 0
        self.db.bow = 0
        self.db.activemartialskill = 1
        self.db.combat_turn = 1
        self.db.in_combat = 0
        self.db.left_slot = []
        self.db.right_slot = []
        self.db.body_slot = []
        self.db.is_aggressive = True
        self.db.peaceful = False
        self.db.skip_turn = False
        self.db.is_staggered = False

        self.db.isLeading = False
        self.db.leader = []
        self.db.isFollowing = False
        self.db.followers = []

        self.db.iron_ingots = 0
        self.db.refined_wood = 0
        self.db.leather = 0
        self.db.cloth = 0
        self.db.gold = 0
        self.db.silver = 0
        self.db.copper = 0
        self.db.arrows = 0

    def make_equipment(self):
        from evennia import spawn
        weapon = spawn({"prototype_parent": "STEEL_MEDIUM_WEAPON", "location": self})[0]
        self.db.right_slot = [weapon.key]
        self.db.weapon_level = 3

    def remove_equipment(self):
        for item in list(self.contents):
            if item.db.damage:
                item.delete()
        self.db.right_slot = []
        self.db.left_slot = []

    def command_picker(self, target):
        amSkills = {
            "disarm": self.db.disarm,
            "stagger": self.db.stagger,
            "cleave": self.db.cleave,
        }
        flat = [c for c, v in amSkills.items() for _ in range(v)]
        flat.append("strike")
        chosen = random.choice(flat)
        if not self.db.right_slot:
            self.make_equipment()
        if not target.db.bleed_points:
            return "disengage"
        chosen = "strike" if self.db.weakness else chosen
        return f"{chosen} {target.key}"

    def take_combat_turn(self, target):
        if not self.db.right_slot:
            self.make_equipment()
        self.execute_cmd(self.command_picker(target))

    def at_char_entered(self, character):
        if self.db.is_aggressive and self.db.bleed_points and self.db.combat_turn:
            if not self.db.right_slot:
                self.make_equipment()
            command = self.command_picker(character)
            self.execute_cmd(command)


class QuestGiverNpc(Npc):
    """
    A non-combatant NPC that offers quests.
    Has a description, will not attack players, and
    greets players who enter the room with available quest hints.
    """

    def at_char_entered(self, character):
        """Hint at available quests when a player enters."""
        if not getattr(character, "has_account", False) or not character.has_account:
            return
        try:
            from commands.quests import _available_quests, QUESTS
            available = [
                q for q in _available_quests(character)
                if q["giver"].lower() == self.key.lower()
            ]
            if available:
                titles = ", ".join(f"|w{q['title']}|n" for q in available)
                character.msg(
                    f"|540{self.key} has a task for you: {titles}. "
                    f"Type |wquest accept <title>|n to begin.|n"
                )
        except Exception:
            pass

    def take_combat_turn(self, target):
        self.execute_cmd("disengage")
