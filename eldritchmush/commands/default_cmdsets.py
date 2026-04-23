"""
Command sets

All commands in the game must be grouped in a cmdset.  A given command
can be part of any number of cmdsets and cmdsets can be added/removed
and merged onto entities at runtime.

To create new commands to populate the cmdset, see
`commands/command.py`.

This module wraps the default command sets of Evennia; overloads them
to add/remove commands from the default lineup. You can create your
own cmdsets by inheriting from them or directly from `evennia.CmdSet`.

"""

from evennia import default_cmds
from evennia.commands.default import general, building
from evennia import CmdSet
from commands import combat, blacksmith, crafting, command, npc, dice, alchemy, shop, quests, account, ai_dialogue, tavyl as tavyl_cmd, duel as duel_cmd, heal as heal_cmd, learn, reputation
from commands.combat_commands import strike, disengage, shoot, cleave, sunder, disarm, stagger, stun, medicine, skip, chirurgery


class RoomCmdSet(CmdSet):

    """General room command set. Be sure to build other location based command
    sets with this as the parent class."""

    def at_cmdset_creation(self):
        super().at_cmdset_creation()

        self.add(command.CmdPerception())
        self.add(command.CmdTracking())


"""
Crafting Command Sets
"""
class BlacksmithCmdSet(CmdSet):
    """
    Commands for making and repairing blacksmith items
    """

    def at_cmdset_creation(self):
        super().at_cmdset_creation()

        self.add(blacksmith.CmdForge())
        self.add(crafting.CmdRepair())
        self.add(crafting.CmdCraft())

class CrafterCmdSet(CmdSet):
    """
    Commands for making and repairing bowyer and artificer items
    """

    def at_cmdset_creation(self):
        super().at_cmdset_creation()

        self.add(crafting.CmdCraft())
        self.add(crafting.CmdRepair())

class ApothecaryWorkbenchCmdSet(CmdSet):
    """
    Commands available at an Apothecary workbench.
    Merged into the character's cmdset when in the same room as the bench.
    """

    def at_cmdset_creation(self):
        super().at_cmdset_creation()

        self.add(alchemy.CmdBrew())


class ShopCmdSet(CmdSet):
    """
    Commands available when a Merchant object is in the room.
    browse/buy/sell become available to all players in the room.
    """

    def at_cmdset_creation(self):
        super().at_cmdset_creation()

        self.add(shop.CmdBrowse())
        self.add(shop.CmdBuy())
        self.add(shop.CmdSell())

"""
Strange Circus Command Sets - Virtual Event 1
"""


class BoxCmdSet(CmdSet):
    """
    Command set for box object in carnival
    """

    def at_cmdset_creation(self):
        super().at_cmdset_creation()

        self.add(command.CmdPushButton())


class AltarCmdSet(RoomCmdSet):
    """
    Command set for box object in carnival
    """

    def at_cmdset_creation(self):
        super().at_cmdset_creation()

        self.add(command.CmdTouchAltar())

"""
End circus command sets
"""


class CharacterCmdSet(default_cmds.CharacterCmdSet):
    """
    The `CharacterCmdSet` contains general in-game commands like `look`,
    `get`, etc available on in-game Character objects. It is merged with
    the `AccountCmdSet` when an Account puppets a Character.
    """

    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
        self.add(strike.CmdStrike())
        self.add(skip.CmdSkip())
        self.add(shoot.CmdShoot())
        self.add(cleave.CmdCleave())
        self.add(disarm.CmdDisarm())
        self.add(stun.CmdStun())
        self.add(disengage.CmdDisengage())
        self.add(stagger.CmdStagger())
        self.add(command.CmdGive())
        self.add(command.CmdGet())
        self.add(command.CmdOpen())
        self.add(command.CmdSmile())
        self.add(command.SetTough())
        self.add(command.SetWeakness())
        self.add(combat.CmdBattlefieldCommander())
        self.add(command.SetIndomitable())
        self.add(combat.CmdRally())
        self.add(command.CharSheet())
        self.add(command.CharStatus())
        self.add(chirurgery.CmdChirurgery())
        self.add(command.CmdDiagnose())
        self.add(command.CmdEquip())
        self.add(command.CmdUnequip())
        self.add(sunder.CmdSunder())
        self.add(dice.CmdDice())
        self.add(command.CmdFollow())
        self.add(command.CmdUnfollow())
        self.add(command.CmdUnfollowForce())
        self.add(command.CmdFollowStatus())
        self.add(command.CmdPatch())
        self.add(medicine.CmdMedicine())
        self.add(combat.CmdTargets())
        self.add(alchemy.CmdReagents())
        self.add(shop.CmdBrowse())
        self.add(shop.CmdBuy())
        self.add(shop.CmdSell())
        self.add(quests.CmdQuest())
        self.add(reputation.CmdReputation())
        self.add(ai_dialogue.CmdAsk())
        self.add(ai_dialogue.CmdFarewell())
        # Overrides default whisper: private messaging still works
        # player-to-player, but whispering at an AI NPC routes through
        # the LLM and gets a private in-character reply.
        self.add(ai_dialogue.CmdWhisper())
        # Overrides default say: still broadcasts to the room as
        # normal, but if an AI NPC's name is mentioned in the message,
        # that NPC will respond in-character.
        self.add(ai_dialogue.CmdSay())
        # Tavyl card game (dealer NPCs run the table).
        self.add(tavyl_cmd.CmdTavyl())
        # Wagered duels — NPCs can advertise themselves as duel_ready.
        self.add(duel_cmd.CmdDuel())
        # Healer NPC interaction — pay silver to restore health.
        self.add(heal_cmd.CmdHeal())
        # Alchemy recipe + herbalist system
        self.add(learn.CmdLearn())
        self.add(learn.CmdRecipes())
        self.add(learn.CmdHerbs())
        self.add(learn.CmdBuyHerb())
        self.add(learn.CmdBuyRecipe())
        self.add(learn.CmdBrowseRecipes())

#### Special command sets

class ArtessaCmdSet(RoomCmdSet):

    """Command set for fortune machine"""
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(command.CmdPull())


class NotchCmdSet(RoomCmdSet):

    """Command set for knife throwing"""
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(command.CmdThrow())

class HammerCmdSet(RoomCmdSet):

    """Command set for hammer swing"""
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(command.CmdSwing())

class MirrorsCmdSet(RoomCmdSet):

    """Command set for hall of mirrors"""
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(command.CmdStart())

class AccountCmdSet(default_cmds.AccountCmdSet):
    """
    This is the cmdset available to the Account at all times. It is
    combined with the `CharacterCmdSet` when the Account puppets a
    Character. It holds game-account-specific commands, channel
    commands, etc.
    """

    key = "DefaultAccount"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
        self.add(npc.CmdCreateNPC())
        self.add(npc.CmdEditNPC())
        self.add(npc.CmdNPC())
        self.add(alchemy.CmdAddReagent())
        # Override default charcreate so new characters spawn in the
        # ChargenRoom (so the React ChargenWizard fires automatically).
        self.add(account.CmdCharCreate())

class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    """
    Command set available to the Session before being logged in.  This
    holds commands like creating a new account, logging in, etc.
    """

    key = "DefaultUnloggedin"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #


class SessionCmdSet(default_cmds.SessionCmdSet):
    """
    This cmdset is made available on Session level once logged in. It
    is empty by default.
    """

    key = "DefaultSession"

    def at_cmdset_creation(self):
        """
        This is the only method defined in a cmdset, called during
        its creation. It should populate the set with command instances.

        As and example we just add the empty base `Command` object.
        It prints some info.
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #

class ChargenCmdset(CmdSet):
    """
    This cmdset it used in character generation areas.
    """
    key = "Chargen"
    def at_cmdset_creation(self):
        "This is called at initialization"
        super().at_cmdset_creation()

        self.add(command.SetTracking())
        self.add(command.SetPerception())
        self.add(command.SetBlacksmith())
        self.add(command.SetArtificer())
        self.add(command.SetGunsmith())
        self.add(command.SetBowyer())
        self.add(command.SetAlchemist())
        self.add(command.SetMasterOfArms())
        self.add(command.SetArmorSpecialist())
        self.add(command.SetGunner())
        self.add(command.SetArcher())
        self.add(command.SetShields())
        self.add(command.SetMeleeWeapons())
        self.add(command.SetArmorProficiency())
        self.add(command.SetResist())
        self.add(command.SetDisarm())
        self.add(command.SetCleave())
        self.add(command.SetStun())
        self.add(command.SetSunder())
        self.add(command.SetStagger())
        self.add(command.SetVigil())
        self.add(command.SetStabilize())
        self.add(command.SetMedicine())
        self.add(command.SetBattleFieldMedicine())
        self.add(command.SetBattleFieldCommander())
        self.add(command.SetRally())
        self.add(command.SetChirurgeon())
        self.add(command.SetResilience())
