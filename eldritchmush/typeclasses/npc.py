from typeclasses.characters import Character
from commands.combat_commands import combat

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
        helper = Helper()
        combat_bank = helper.activeMartialCounter(self)

        # Generate an array of possible commands. There will be
        ams_commands = [(command,)*value for command, value in combat_bank.items() if value != 0]
        flat_ams_commands = [attack for groups in ams_commands for attack in groups]
        all_commands = ["strike"].extend(flat_ams_commands)

        # Choose random command
        chosen_command = random.choice(all_commands)
        # Establish command string
        action_string = f"{chosen_command} {target}"

        return action_string
