
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


class GreenMeleeSoldierOneHanded(Character):
    """
    Generic solider NPC
    """

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
        self.execute_cmd('equip hardened iron coat of plates')
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
