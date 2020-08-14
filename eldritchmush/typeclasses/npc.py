
# Local imports
from typeclasses.characters import Character
from
from evennia import create_object
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
        if self.db.is_aggressive:
            self.execute_cmd("say Graaah, die %s!" % character)
        else:
            self.execute_cmd("say Greetings, %s!" % character)


class MeleeSoldier(Npc):
    """
    Generic solider NPC
    """

    def at_object_creation(self):
        # Arm with item:
        longsword = create_object(typeclasses.IRON_MEDIUM_WEAPON,
                                  key="Longsword",
                                  location=self)

        self.execute_cmd("equip longsword")

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

        if not self.db.right_slot or self.db.left_slot:
            self.execute_cmd('equip longsword')
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


class Revenant(Npc):
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
        if not self.db.melee:
            self.execute_cmd('equip ')
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
