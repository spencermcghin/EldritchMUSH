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
    def at_object_creation(self):
        """
        Called when soldier first created.
        """
        # Set defensive stats
        self.db.master_of_arms = 1
        self.db.armor = 2
        self.db.armor_specialist = 1
        self.db.tough = 1
        self.db.resilience = 1

        # Set offensive stats
        self.db.melee = 1
        self.db.stagger = 2
        self.db.weapon_level = 1
        self.db.shield = 1
        self.db.disarm = 1


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
