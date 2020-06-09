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
from commands import command
from commands import combat
from commands import npc
from commands import dice


class RoomCmdSet(CmdSet):

    """General room command set"""

    def at_cmdset_creation(self):
        super().at_cmdset_creation()

        self.add(command.CmdPerception())
        self.add(command.CmdTracking())

class BoxCmdSet(CmdSet):
    """
    Command set for box object in carnival
    """

    def at_cmdset_creation(self):
        super().at_cmdset_creation()

        self.add(command.CmdPushButton())


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
        self.add(combat.CmdStrike())
        self.add(combat.CmdShoot())
        self.add(combat.CmdCleave())
        self.add(combat.CmdResist())
        self.add(combat.CmdDisarm())
        self.add(combat.CmdStun())
        self.add(combat.CmdDisengage())
        self.add(combat.CmdStagger())
        self.add(command.SetShield())
        self.add(command.SetTwoHanded())
        self.add(command.SetBow())
        self.add(command.SetMelee())
        self.add(command.SetWeaponValue())
        self.add(command.CmdSmile())
        self.add(command.SetArmorValue())
        self.add(command.SetTough())
        self.add(command.SetBody())
        self.add(command.CmdStabilize())
        self.add(command.CmdMedicine())
        self.add(command.SetWeakness())
        self.add(combat.CmdBattlefieldCommander())
        self.add(command.CmdBattlefieldMedicine())
        self.add(combat.CmdRally())
        self.add(command.SetShieldValue())
        self.add(command.CharSheet())
        self.add(command.CharStatus())
        self.add(command.CmdChirurgery())

#### Special command sets
class DiceCmdSet(CmdSet):
    """
    a small cmdset for testing purposes.
    Add with @py self.cmdset.add("contrib.dice.DiceCmdSet")
    """

    def at_cmdset_creation(self):
        """Called when set is created"""
        self.add(dice.CmdDice())

class ArtessaCmdSet(RoomCmdSet):

    """Command set for fortune machine"""
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(command.CmdPull())


class NotchCmdSet(RoomCmdSet):

    """Command set for fortune machine"""
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(command.CmdThrow())

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
        self.add(command.SetMasterOfArms())
        self.add(command.SetArmorSpecialist())
        self.add(command.SetResist())
        self.add(command.SetDisarm())
        self.add(command.SetCleave())
        self.add(command.SetStun())
        self.add(command.SetStagger())
        self.add(command.SetWyldingHand())
        self.add(command.SetStabilize())
        self.add(command.SetMedicine())
        self.add(command.SetBattleFieldMedicine())
        self.add(command.SetBattleFieldCommander())
        self.add(command.SetRally())
        self.add(command.SetChirurgeon())
