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
            self.msg_contents("Graaah, die %s!" % character)
        else:
            self.msg_contents("Greetings, %s!" % character)
