"""
Combat Loop

The combat loop does the following in order to resolve combats as they occur in
the mush space.

1. Characters have the combat_turn flag as an attribute in the
database. A combat loop attribute has also been added to the Room class.

2. There can only be one combat_loop in a room at a time. A character may add and
remove themselves from the rooms combat loop as they are able, using the
corresponding combat commands.

3. Once a character uses one of the commands as contained in the COMBAT_COMMANDS
list, the rules system checks to make sure the command is acceptable.

4. If the command belongs to the list of combat commands, the code checks to
see if the character is currently in the room's combat loop.

5. If the character does not belong to the combat loop, the character is prompted
to enter a command from the list and/or to disengage from the fight if they do not
wish to take part.

6. If the character is not listed in the room's combat loop, they are added to
the end of the round, or interpreted another way, to the end of the room's
combat loop.

7. If the character is currently engaged in combat, they will be prompted to
wait until it is their turn (combat_turn) before they are able to enter a command.

"""
class CombatLoop:

    # Acceptable COMBAT_COMMANDS
    COMBAT_COMMANDS = ["strike",
                       "hit",
                       "slash",
                       "bash",
                       "punch",
                       "shoot",
                       "cleave",
                       "disarm",
                       "stun",
                       "stagger",
                       "sunder"]


    def checkCommand(self, command: str) -> bool:
        if command in COMBAT_COMMANDS:
            return True
        else:
            return False


    def isTurn(self, character):
        if character.db.combat_turn:
            return True
        else:
            return False


    def checkLoop(self, character):
        # Get room where character is calling the combat command.
        current_room = character.location.dbref
        combat_loop = current_room.db.combat_loop

        # Check to see if caller is part of rooms combat loop
        if character in combat_loop:
            return True
        else:
            return False


    def addCharacter(self, character):
        # TODO: get character return type
        # Get room where character is calling the combat command.
        current_room = character.location.dbref
        combat_loop = current_room.db.combat_loop

        # Add character to combat loop
        combat_loop.append(character)
