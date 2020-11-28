from evennia import utils
from typeclasses.characters import Character
from typeclasses.npc import Npc
import random

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

setmelee needs to be counted as an action in loop


"""

class CombatLoop:

	def __init__(self, caller, target = None):
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


	def isLast(self):
		# Check to see if caller is last in the combat_loop
		loopLength = self.getLoopLength()
		if self.combat_loop.index(self.caller) + 1 == loopLength:
			return True
		else:
			return False

	def goToNext(self):
		nextIndex = self.combat_loop.index(self.caller) + 1
		nextTurnCharacter = self.combat_loop[nextIndex]

		# Search for and return next element in combat loop
		# searchCharacter = self.caller.search(nextTurnCharacter)
		return nextTurnCharacter

	def goToFirst(self):
		firstCharacter = self.combat_loop[0]

		return firstCharacter

	def isDying(self, combatant):
		dying = True if combatant.db.bleed_points == 0 else False
		return dying

	def resolveCommand(self):
		loopLength = self.getLoopLength()

		# If character not in loop and loop is empty
		if self.inLoop() is False and loopLength == 0:

			# Add character to loop
			# Check to see if this is an npc. If so, do nothing. They will have attacked already.
			self.addToLoop(self.caller)
			self.caller.db.in_combat = 1
			callerTurn = self.getCombatTurn(self.caller)
			# Send message to attacker and resolve command
			self.caller.location.msg_contents(f"{self.caller.key} has been added to the combat loop for the {self.current_room}.\nThey are currently number {callerTurn} in the round order.")

			# Add target of attack to loop
			self.addToLoop(self.target)
			self.target.db.in_combat = 1
			# Send message to target and resolve command
			targetTurn = self.getCombatTurn(self.target)
			self.target.location.msg_contents(f"{self.target.key} has been added to the combat loop for the {self.current_room}.\nThey are currently number {targetTurn} in the round order.")
			# Disable their ability to use combat commands
			self.combatTurnOff(self.target)

		elif self.inLoop() is False and loopLength > 1:

			if self.target not in self.combat_loop:
				# Append caller and target to end of loop
				self.combat_loop.append(self.caller)
				self.caller.db.in_combat = 1
				self.combat_loop.append(self.target)
				self.target.db.in_combat = 1
				callerTurn = self.getCombatTurn(self.caller)
				targetTurn = self.getCombatTurn(self.target)
				# Change combat_turn to 0
				self.combatTurnOff(self.caller)
				self.combatTurnOff(self.target)
				self.caller.location.msg_contents(f"{self.caller.key} and {self.target.key} have been added to the combat loop for the {self.current_room}.\nThey are currently number ({callerTurn}) and ({targetTurn}) in the round order.")

			else:

				# caller not in loop, target in loop
				# Append to end of loop
				self.combat_loop.append(self.caller)
				self.caller.db.in_combat = 1
				callerTurn = self.getCombatTurn(self.caller)
				# Change combat_turn to 0
				self.combatTurnOff(self.caller)
				self.caller.location.msg_contents(f"{self.caller.key} has been added to the combat loop for the {self.current_room}.\nThey are currently number {callerTurn} in the round order.")

		elif self.inLoop() is True and self.target not in self.combat_loop and self.target is not None:

			# Handle when caller in loop and target is not
			# Need to add target to end of loop, set their combat_turn to 0.
			self.combat_loop.append(self.target)
			self.target.db.in_combat = 1
			self.combatTurnOff(self.target)
			self.target.location.msg_contents(f"{self.target.key} has been added to the combat loop for the {self.current_room}.\nThey are currently number {self.getCombatTurn(self.target)} in the round order.")

		# Solve for when no target as in resist command.
		elif self.inLoop() is True and self.target == None:
			pass

		else:
			# Solve for when no target as in resist command.
			pass

	def verboseEndTurn(self, combatant, statusMessage):
		combatant.location.msg_contents(statusMessage)
		self.combatTurnOff(combatant)
		self.cleanup()


	def cleanup(self):
		# Check for number of elements in the combat loop
		if self.getLoopLength() > 1:

			# If no character at next index (current character is last),
			# go back to beginning of combat_loop and prompt character for input.
			nextCharacter = self.goToFirst() if self.isLast() else self.goToNext()

			# Iterate through combat_loop until finding a character w/out the skip_turn flag set.
			while nextCharacter.db.skip_turn or not nextCharacter.db.bleed_points:
				# Turn off the skip_turn flag and then try to go to the next character in the loop
				nextCharacter.db.skip_turn = False
				nextCharacter.location.msg_contents(f"{nextCharacter.key} |430is unable to act this round.|n")
				try:
					# Try going to the next character based on the character that had skip_turn active
					nextTurn = self.combat_loop.index(nextCharacter) + 1
					nextCharacter = self.caller.search(self.combat_loop[nextTurn])

				except IndexError:
					nextCharacter = self.caller.search(self.combat_loop[0])

			self.combatTurnOn(nextCharacter)
			nextCharacter.location.msg_contents(f"ס₪₪₪₪§|(Ξ≥≤≥≤≥≤ΞΞΞΞΞΞΞΞΞΞ> |025It is now |n{nextCharacter.key}'s |025turn.|n")



			###### NPC Turn Resolver ######
			# Check to see if the character is an npc. If so run it's random command generator
			if utils.inherits_from(nextCharacter, Npc):

				# Get number of bots
				bots = [bot for bot in nextCharacter.location.db.combat_loop if utils.inherits_from(bot, Npc)]
				# Get number of dead/dying bots
				dying_bots = [bot for bot in bots if self.isDying(bot)]
				# Compare lengths to figure out whether or not to shut down combat.
				total_bots = len(bots)
				total_dying_bots = len(dying_bots)

				# If bots are all dying, reset combat stats and empty loop.
				if total_bots == total_dying_bots:
					for char in nextCharacter.location.db.combat_loop:
						self.combatTurnOn(char)
						char.db.in_combat = 0

					# Clear the loop for combat
					nextCharacter.location.db.combat_loop.clear()
					nextCharacter.location.msg_contents(f"|025All NPC combatants are now unable to act. Combat is now over for the {nextCharacter.location}.|n")

				else:
					# Hook into the npcs command generator.
					# Figure out which player targets NPCs can attack.
					targets = [target for target in nextCharacter.location.db.combat_loop if target.has_account and target.db.bleed_points]

					# If there are targets, make sure NPC has something to fight with and is not dying.
					if targets:
						if not self.isDying(nextCharacter):
							# Check to make sure carried item does damage
							right_item = self.caller.search(nextCharacter.db.right_slot[0]) if nextCharacter.db.right_slot else ''
							left_item = self.caller.search(nextCharacter.db.left_slot[0]) if nextCharacter.db.left_slot else ''
							rightDamage = True if right_item.db.damage else False
							leftDamage = True if left_item.db.damage else False

							if (rightDamage or leftDamage):
								random_target = random.choice(targets)
								# If character target, attack a random one.
								nextCharacter.at_char_entered(random_target)
							else:
								nextCharacter.location.msg_contents(f"{nextCharacter.key} |025has nothing to attack with.|n")
								nextCharacter.execute_cmd("disengage")
						else:
							nextCharacter.location.msg_contents(f"{nextCharacter.key} |300is too injured to act.|n")
							nextCharacter.execute_cmd("skip")
					else:
						nextCharacter.location.msg_contents(f"|430There are no possible targets.|n")
						nextCharacter.execute_cmd("disengage")

		else:
			try:
				remaining_character = self.combat_loop[0]
			except IndexError:
				self.caller.location.msg_contents(f"|430Combat is now over for {loop.current_room}.|n")
			else:
				self.caller.location.msg_contents(f"|430Combat is now over for the {remaining_character.location}.|n")
				self.removeFromLoop(remaining_character)
				self.caller.db.in_combat = 0
				# Change self.callers combat_turn to 1 so they can attack again.
				self.combatTurnOn(remaining_character)
