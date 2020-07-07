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

5. If the command does not belong to the combat loop, the character is prompted
to enter a command from the list and/or to disengage from the fight if they do not
wish to take part.

6. If the character is not listed in the room's combat loop, they are added to
the end of the round, or interpreted another way, to the end of the room's
combat loop.

7. If the character is currently engaged in combat, they will be prompted to
wait until it is their turn (combat_turn) before they are able to enter a command.

"""
