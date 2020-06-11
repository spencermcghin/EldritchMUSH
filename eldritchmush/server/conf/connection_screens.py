# -*- coding: utf-8 -*-
"""
Connection screen

This is the text to show the user when they first connect to the game (before
they log in).

To change the login screen in this module, do one of the following:

- Define a function `connection_screen()`, taking no arguments. This will be
  called first and must return the full string to act as the connection screen.
  This can be used to produce more dynamic screens.
- Alternatively, define a string variable in the outermost scope of this module
  with the connection string that should be displayed. If more than one such
  variable is given, Evennia will pick one of them at random.

The commands available to the user when the connection screen is shown
are defined in evennia.default_cmds.UnloggedinCmdSet. The parsing and display
of the screen is done by the unlogged-in "look" command.

"""

from django.conf import settings
from evennia import utils

CONNECTION_SCREEN = """
|b==============================================================|n
                                    o
                               _---|         _ _ _ _ _
                            o   ---|     o   ]-I-I-I-[
         _ _ _ _ _  _---|      | _---|    \ ` ' /
        ]-I-I-I-I-[  ---|      |  ---|    |.   |
         \ `   '_/      |     / \    |    | /^\|
             [*]  __|       ^    / ^ \   ^    | |*||
             |__   ,|      / \  /    `\ / \   | ===|
         ___| ___ ,|__   /    /=_=_=_=\   \  |,  _|
        I_I__I_I__I_I  (====(_________)___|_|____|____
         \-\--|-|--/-/  |     I  [ ]__I I_I__|____I_I_|
        |[]      '|   | []  |`__  . [  \-\--|-|--/-/
        |.   | |' |___|_____I___|___I___|---------|
        / \| []   .|_|-|_|-|-|_|-|_|-|_|-| []   [] |
        <===>  |   .|-=-=-=-=-=-=-=-=-=-=-|   |    / \\
        ] []|`   [] ||.|.|.|.|.|.|.|.|.|.||-      <===>
        ] []| ` |   |/////////\\\\\\\\\\\\\\\\\\\\.||__.  | |[] [
        <===>     ' ||||| |   |   | ||||.||  []   <===>
        \T/  | |-- ||||| | O | O | ||||.|| . |'   \T/
        |      . _||||| |   |   | ||||.|| |     | |
        ../|' v . | .|||||/____|____\|||| /|. . | . ./
        .|//\............/...........\........../../\\\\\\
     _____ _     _      _ _       _      ___  ____   _ _____ _   _
    |  ___| |   | |    (_) |     | |     |  \/  | | | /  ___| | | |
    | |__ | | __| |_ __ _| |_ ___| |__   | .  . | | | \ `--.| |_| |
    |  __|| |/ _` | '__| | __/ __| '_ \  | |\/| | | | |`--. \  _  |
    | |___| | (_| | |  | | || (__| | | | | |  | | |_| /\__/ / | | |
    \____/|_|\__,_|_|  |_|\__\___|_| |_| \_|  |_/\___/\____/\_| |_/


 If you have an existing account, connect to it by typing:
      |wconnect <username> <password>|n
 If you need to create an account, type (without the <>'s):
      |wcreate <username> <password>|n

 If you have spaces in your username, enclose it in quotes.
 Enter |whelp|n for more info. |wlook|n will re-show this screen.
|b==============================================================|n""".format(
    settings.SERVERNAME, utils.get_evennia_version("short")
)
