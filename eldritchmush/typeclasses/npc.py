from typeclasses.characters import Character

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
        """
        # Form execute_cmd template, choosing from random commands.

        action_string = f"strike {target}"

        return action_string
