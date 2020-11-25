# Imports
import random

# Local imports
from evennia import Command, CmdSet, default_cmds, utils, create_script
from evennia.utils import evtable
from typeclasses.npc import Npc
from commands import command
from world.combat_loop import CombatLoop
from typeclasses.characters import Character


class Helper():
    """
    Class for general combat helper commands.
    """

    def __init__(self, caller):
        self.caller = caller


    def targetHandler(self, target):
        # Check for designated target

        try:
            target = self.caller.search(target)

        except:
            self.caller.msg(f"|300No such target, {target}, or target not legal.|n")
            return

        else:
            return target


    def canFight(self, caller):
        can_fight = True if caller.db.bleed_points else False

        return can_fight


    def isAlive(self, target):
        is_alive = True if target.db.death_points else False

        return is_alive


    def weaponValue(self, level):
        """
        Returns bonus for weapon level based on value set
        """
        if level == 1:
            bonus = 2
        elif level == 2:
            bonus = 4
        elif level == 3:
            bonus = 6
        elif level == 4:
            bonus = 8
        else:
            bonus = 0

        return bonus


    def masterOfArms(self, level):
        """
        Returns die result based on master of arms level
        """
        if level == 0:
            die_result = random.randint(1,6)
        elif level == 1:
            die_result = random.randint(1,10)
        elif level == 2:
            die_result = random.randint(1,6) + random.randint(1,6)
        elif level == 3:
            die_result = random.randint(1,8) + random.randint(1,8)

        return die_result


    def wyldingHand(self, level):
        """
        Returns die result based on wylding hand level
        """
        if level == 0:
            die_result = random.randint(1,6)
        elif level == 1:
            die_result = random.randint(1,10)
        elif level == 2:
            die_result = random.randint(1,6) + random.randint(1,6)
        elif level == 3:
            die_result = random.randint(1,8) + random.randint(1,8)

        return die_result

    def shotFinder(self, targetArray):
        """
        Rolls a number between 1 and 5 and then maps it to an area of the body for the hit
        """
        # Roll a d5 and then map the result to the targetArray.
        # Return the value from the target array and remove it from the current character's targetArray value in the db

        # Roll random number
        result = random.randint(0,5)

        # Get part of body based on targetArray input
        target = targetArray[result]

        return target


    def bodyChecker(self, bodyScore):
        """
        Just checks amount of body and applies penalty based on number character is down.
        """
        if bodyScore >= 3:
            damage_penalty = 0
        elif bodyScore == 2:
            damage_penalty = 1
        elif bodyScore == 1:
            damage_penalty = 2
        elif bodyScore == 0:
            damage_penalty = 3
        elif bodyScore == -1:
            damage_penalty = 4
        elif bodyScore == -2:
            damage_penalty = 5
        else:
            damage_penalty = 6

        return damage_penalty

    def weaknessChecker(self, hasWeakness):
        """
        Checks to see if caller has weakness and then applies corresponding penalty.
        """
        attack_penalty = 2 if hasWeakness else 0

        return attack_penalty

    def deathSubtractor(self, damage, target, caller):
        """
        Handles damage at or below 3 body.
        """
        target_body = target.db.body
        target_bleed_points = target.db.bleed_points
        target_death_points = target.db.death_points

        if target_body and damage:
            body_damage = target_body - damage
            if body_damage < 0:
                damage = abs(body_damage)
                target.db.body = 0
            else:
                target.db.body = body_damage
                damage = 0

        if target_bleed_points and damage:
            bleed_damage = target_bleed_points - damage
            if bleed_damage < 0:
                damage = abs(bleed_damage)
                target.db.bleed_points = 0
                target.db.weakness = 1
            else:
                target.db.bleed_points = bleed_damage
                damage = 0
                target.db.weakness = 1

            target.msg("|430You are bleeding profusely from many wounds and can no longer use any active martial skills.\n|n")
            target.location.msg_contents(f"|025{target.key} is bleeding profusely from many wounds and will soon lose consciousness.|n")


        if target_death_points and damage:
            death_damage = target_death_points - damage
            if death_damage < 0:
                damage = abs(death_damage)
                target.db.death_points = 0
            else:
                target.db.death_points = death_damage
                damage = 0

            target.msg("|300You are unconscious and can no longer move of your own volition.|n")
            target.location.msg_contents(f"|025{target.key} does not seem to be moving.|n")

        else:
            pass


    def damageSubtractor(self, damage, target, caller):
        """
        Takes attack type of caller and assigns damage based on target stats.
        """
        # Build the target av objects
        target_shield_value = target.db.shield_value  # Applied conditionally
        target_armor = target.db.armor
        target_tough = target.db.tough
        target_armor_specialist = target.db.armor_specialist

        # Apply damage in order
        if target_shield_value:
            # Get value of shield damage to check if it's under 0. Need to pass
            # this on to armor
            shield_damage = target_shield_value - damage
            if shield_damage < 0:
                # Check if damage would make shield go below 0
                damage = abs(shield_damage)
                # Set shield_value to 0
                target.db.shield_value = 0
                # Recalc and set av with new shield value
            else:
                target.db.shield_value = shield_damage
                damage = 0

        if target_armor_specialist and damage:
            # Get value of damage
            armor_specialist_damage = target_armor_specialist - damage
            if armor_specialist_damage < 0:
                damage = abs(armor_specialist_damage)
                target.db.armor_specialist = 0
            else:
                target.db.armor_specialist = armor_specialist_damage
                damage = 0

        if target_armor and damage:
            # Get value of damage
            armor_damage = target_armor - damage
            if armor_damage < 0:
                damage = abs(armor_damage)
                target.db.armor = 0
            else:
                target.db.armor = armor_damage
                damage = 0

        if target_tough and damage:
            tough_damage = target_tough - damage
            if tough_damage < 0:
                damage = abs(tough_damage)
                target.db.tough = 0
            else:
                target.db.tough = tough_damage
                damage = 0
        else:
            self.deathSubtractor(damage, target, caller)

        new_av = self.updateArmorValue(target.db.shield_value, target.db.armor, target.db.tough, target.db.armor_specialist)

        return new_av


    def updateArmorValue(self, shieldValue, armor, tough, armorSpecialist):
        armor_value = shieldValue + armor + tough + armorSpecialist

        return armor_value

    def dmgPenalty(self):
        return self.bodyChecker(self.caller.db.body)

    def weaknessPenalty(self):
        return self.weaknessChecker(self.caller.db.weakness)

    def getKitTypeAndUsesItem(self):
        kit = self.caller.db.kit_slot[0] if self.caller.db.kit_slot else []

        if kit:
            return kit.db.type, kit.db.uses
        else:
            return "",None

    def useKit(self):
        kit = self.caller.db.kit_slot[0] if self.caller.db.kit_slot else []

        if kit:
            kit.db.uses -= 1

    def getMeleeCombatStats(self, combatant):
        # Get hasMelee for character to check that they've armed themselves.
        melee = combatant.db.melee

        # Vars for melee attack_result logic
        master_of_arms = combatant.db.master_of_arms
        weapon_level = self.weaponValue(combatant.db.weapon_level)
        wylding_hand = combatant.db.wylding_hand

        # Penalties
        weakness = self.weaknessChecker(combatant.db.weakness)
        dmg_penalty = self.bodyChecker(combatant.db.body)

        # Slot checks for sunder command
        left_slot = combatant.db.left_slot[0] if combatant.db.left_slot else []
        right_slot = combatant.db.right_slot[0] if combatant.db.right_slot else []

        is_bow = True if right_slot and right_slot.db.is_bow else False

        two_handed = True if left_slot == right_slot and not None else False
        bow = True if left_slot == right_slot and is_bow else False
        arrows = combatant.db.arrows

        melee_stats = {"melee": melee,
                       "bow": bow,
                       "arrows": arrows,
                       "bow_penalty": 2,
                       "master_of_arms": master_of_arms,
                       "weapon_level": weapon_level,
                       "wylding_hand": wylding_hand,
                       "weakness": weakness,
                       "dmg_penalty": dmg_penalty,
                       "two_handed": two_handed,
                       "left_slot": left_slot,
                       "right_slot": right_slot,
                       "disarm_penalty": 2,
                       "stagger_penalty": 2,
                       "stagger_damage": 2,
                       "bow_damage": 1,
                       "stun_penalty": 1}

        return melee_stats


    def fayneChecker(self, master_of_arms, wylding_hand):
        # Return die roll based on level in master of arms or wylding hand.
        if wylding_hand:
            die_result = self.wyldingHand(wylding_hand)
        else:
            die_result = self.masterOfArms(master_of_arms)

        return die_result

"""
General Combat Commands
"""
class CmdTargets(Command):
    """
    Lists current possible targets and their general status per the look command.

    Usage:
      targets

    Logic:
    1. Check to see if in combat loop for location.
    2. Else broadcast not in combat message.
    3. If in combat, get turn order, enemy names, and their general status.


    """
    key = "targets"
    aliases = ["combat targets", "enemies"]
    help_category = "combat"

    def parse(self):
        self.combat_loop = self.caller.location.db.combat_loop

    def isBleeding(self, character):
        isBleeding = True if not character.db.body and character.db.bleed_points else False
        return f"{character.name} |025is bleeding profusely from mutliple, serious wounds.|n" if isBleeding else ""

    def isDying(self, character):
        isDying = True if not character.db.bleed_points and not character.db.body else False
        return f"{character.name} |025has succumbed to their injuries and is now unconscious.|n" if isDying else ""

    def func(self):
        # Check to see if caller is in combat loop:
        if self.caller in self.combat_loop:
            enemies = [char for char in self.combat_loop if utils.inherits_from(char, Npc)]

            table = self.styled_table(border="header")
            for enemy in enemies:
                table.add_row("|C%s|n" % enemy.name, enemy.db.desc or "", self.isBleeding(enemy), self.isDying(enemy))
            string = "|430Current Targets:|n\n%s" % table
            self.caller.msg(string)

        else:
            self.msg(f"|400You are not part of any combat for {self.caller.location}.|n")


"""
Knight commands
"""

class CmdBattlefieldCommander(Command):
    """
    Usage: bolster <speech>

    Use the bolster command followed by a speech to give all in the room 1 tough.
    """
    key = "bolster"
    aliases = ["battlefieldcommander"]
    help_category = "combat"

    def parse(self):
        "Very trivial parser"
        self.speech = self.args.strip()

    def func(self):
        if not self.args:
            self.caller.msg("|430Usage: bolster <target>|n")
            return

        bolsterRemaining = self.caller.db.battlefieldcommander

        # if bolsterRemaining > 0:

        self.caller.location.msg_contents(f"|025Amidst the chaos of the fighting, |n{self.caller.key} |025shouts so all can hear,|n {self.speech}|025.|n")
            # self.caller.db.battlefieldcommander -= 1
        room_contents = self.caller.location.contents
        characters = [char for char in room_contents if char.has_account]
        tough_vals = [map(update_tough, char) for char in characters]
        self.msg(tough_vals)

        # else:
        #     self.caller.msg("|300You have no uses of your battlefield commander ability remaining or do not have the skill.|n")

    def update_tough(self, character):
        current_tough_value = character.db.tough
        new_tough_value = current_tough_value + 1
        character.db.tough = new_tough_value

class CmdRally(Command):
    """
    Usage: rally <speech>

    Use the rally command followed by a speech to remove a fear effect from those in the room.
    """
    key = "rally"
    help_category = "combat"

    def parse(self):
        "Very trivial parser"
        self.speech = self.args.strip()

    def func(self):
        if not self.args:
            self.caller.msg("|430Usage: rally <speech>|n")
            return

        rallyRemaining = self.caller.db.rally

        if rallyRemaining > 0:
            self.caller.location.msg_contents(f"|025{self.caller.key} shouts so all can hear,|n |300{self.speech}|n.\n|430Everyone in the room now feels unafraid. Cancel the fear effect.|n")
            self.caller.db.rally -= 1
        else:
            self.caller.msg("|300You have no uses of your rally ability remaining or do not have the skill.|n")
