
"""
Combat Loop

The combat loop does the following in order to resolve combats as they occur in
the mush space.

1. Characters have the combat_turn flag as an attribute in the
database. A combat loop attribute has also been added to the Room class.

2. There can only be one combat_loop in a room at a time. A character may add and
remove themselves from the room's combat loop as they are able, using the
corresponding combat commands. The player may then only exit the combat loop when
brought to 0 body or by using the corresponding exit command (Disengage in this case.)

3. Combat loops are referenced each time one of the combat commands is called.

4. Logic checks if combat_loop is empty before adding a new character.

5. If loop is not empty, append to end of loop and set character's combat turn to 0.
Their combat command set should now be disabled. Another option: If character tries to
enter combat command, logic checks if it's their turn. The character will be prompted
that they've been added to the loop, then be prompted that they'll need to wait
until it is their turn.

6. Character's turn number is checked by logic. Their turn number in the round
will then be shown to them.

7. If loop is empty, append caller to loop.

8. Add target to combat loop and set target's combat_turn to 0.

9. At end of combat command resolution, switch combat_turn on caller to 0.
Ensure attacker can't do combat commands via handling.

9. Check for number of elements in combat loop. If greater than 1, go to next
element (character/npc).

9. Switch the next character/npc in the loop's combat_turn to 1. Prompt them
to enter command.

10. If number of elements left in loop <= 1, remove remaining elements in loop.
Change callers combat_turn to 1. Combat loop is empty and now ready for a new combat.

Notes:
Handle removal of character if body is 0 or less - check before setting combat_turn
to 1 if character is at 0 or less. If so, skip to next element in list. If > 0, proceed
as normal.
If bleeding, you can still use disengage, but only that command.
If dying, you can do nothing and be the target of a drag command
Build command - Drag. Your turn is skipped.
Need to fix it so you can see NPCs msgs

Hook ideas


"""

class CombatLoop:

    def __init__(self, caller, target):
        self.caller = caller
        self.target = target

        # TODO: Get access to rooms combat loop
        self.current_room = self.caller.location
        self.combat_loop = self.current_room.db.combat_loop


    def inLoop(self):
        # Check to see if caller is part of rooms combat loop
        if self.caller in self.combat_loop:
            return True
        else:
            return False


    def isTurn(self, combatant):
        if combatant.db.combat_turn:
            return True
        else:
            return False


    def combatTurnOn(self, combatant):
        combatant.db.combat_turn = 1


    def combatTurnOff(self, combatant):
        combatant.db.combat_turn = 0


    def addToLoop(self, combatant):
        # Add character to combat loop
        self.combat_loop.append(combatant)


    def removeFromLoop(self, combatant):
        # Remove character from combat loop
        self.combat_loop.remove(combatant)


    def getCombatTurn(self, combatant):
        # Set character turn to index of character in combat loop, plus one
        return self.combat_loop.index(combatant) + 1


    def getLoopLength(self):
        return len(self.combat_loop)


    def goToNext(self):
        nextIndex = self.combat_loop.index(self.caller.key) + 1
        nextTurnCharacter = self.combat_loop[nextIndex]

        # Search for and return next element in combat loop
        searchCharacter = self.caller.search(nextTurnCharacter)
        return searchCharacter

    def goToFirst(self):
        firstCharacter = self.combat_loop[0]

        # Search for and return first element in combat loop
        searchCharacter = self.caller.search(firstCharacter)
        return searchCharacter

    # Main logic
    def resolveCommand(self):
        loopLength = self.getLoopLength()

        # If character not in loop and loop is empty
        if not self.inLoop() and loopLength == 0:

            # Add character to loop
            self.addToLoop(self.caller.key)
            # Send message to attacker and resolve command
            self.caller.msg(f"You have been added to the combat loop for the {self.current_room}")

            # Add target of attack to loop
            self.addToLoop(self.target.key)
            # Send message to target and resolve command
            targetTurn = self.getCombatTurn(self.target.key)
            self.target.msg(f"You have been added to the combat loop for the {self.current_room}.\nYou are currently number {targetTurn} in the round order.")
            # Disable their ability to use combat commands
            self.combatTurnOff(self.target)

        elif not self.inLoop and loopLength > 0:

            # Append to end of loop
            self.combat_loop.append(self.caller.key)
            # Change combat_turn to 0
            self.combatTurnOff(self.caller)
            callerTurn = self.getCombatTurn(self.caller)
            self.caller.msg(f"You have been added to the combat loop for the {self.current_room}.\nYou are currently number {callerTurn} in the round order.")
