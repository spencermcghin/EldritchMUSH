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



      ..      .           ..    ..                       .         s
   x88f` `..x88. .> x .d88"   dF                        @88>      :8                .uef^"
 :8888   xf`*8888%   5888R   '88bu.         .u    .     %8P      .88              :d88E
:8888f .888  `"`     '888R   '*88888bu    .d88B :@8c     .      :888ooo       .   `888E
88888' X8888. >"8x    888R     ^"*8888N  ="8888f8888r  .@88u  -*8888888  .udR88N   888E .z8k
88888  ?88888< 888>   888R    beWE "888L   4888>'88"  ''888E`   8888    <888'888k  888E~?888L
88888   "88888 "8%    888R    888E  888E   4888> '      888E    8888    9888 'Y"   888E  888E
88888 '  `8888>       888R    888E  888E   4888>        888E    8888    9888       888E  888E
`8888> %  X88!        888R    888E  888F  .d888L .+     888E   .8888Lu= 9888       888E  888E
 `888X  `~""`   :    .888B . .888N..888   ^"8888*"      888&   ^%888*   ?8888u../  888E  888E
   "88k.      .~     ^*888%   `"888*""       "Y"        R888"    'Y"     "8888P'  m888N= 888>
     `""*==~~`         "%        ""                      ""                "P'     `Y"   888
                                                                                        J88"


    .....                                         ..
 .H8888888h.  ~-.    .uef^"                    :**888H: `: .xH""                                x=~                ..
 888888888888x  `> :d88E                      X   `8888k XX888       u.    u.      u.    u.    88x.   .e.   .e.   @L             u.    u.
X~     `?888888hx~ `888E            .u       '8hx  48888 ?8888     x@88k u@88c.  x@88k u@88c. '8888X.x888:.x888  9888i   .dL   x@88k u@88c.
'      x8.^"*88*"   888E .z8k    ud8888.     '8888 '8888 `8888    ^"8888""8888" ^"8888""8888"  `8888  888X '888k `Y888k:*888. ^"8888""8888"
 `-:- X8888x        888E~?888L :888'8888.     %888>'8888  8888      8888  888R    8888  888R    X888  888X  888X   888E  888I   8888  888R
      488888>       888E  888E d888 '88%"       "8 '888"  8888      8888  888R    8888  888R    X888  888X  888X   888E  888I   8888  888R
    .. `"88*        888E  888E 8888.+"         .-` X*"    8888      8888  888R    8888  888R    X888  888X  888X   888E  888I   8888  888R
  x88888nX"      .  888E  888E 8888L             .xhx.    8888      8888  888R    8888  888R   .X888  888X. 888~   888E  888I   8888  888R
 !"*8888888n..  :   888E  888E '8888c. .+      .H88888h.~`8888.>   "*88*" 8888"  "*88*" 8888"  `%88%``"*888Y"     x888N><888'  "*88*" 8888"
'    "*88888888*   m888N= 888>  "88888%       .~  `%88!` '888*~      ""   'Y"      ""   'Y"      `~     `"         "88"  888     ""   'Y"
        ^"***"`     `Y"   888     "YP'              `"     ""                                                            88F
                         J88"                                                                                           98"
                         @%                                                                                           ./"
                       :"                                                                                            ~`

 If you have an existing account, connect to it by typing:
      |wconnect <username> <password>|n
 If you need to create an account, type (without the <>'s):
      |wcreate <username> <password>|n

 If you have spaces in your username, enclose it in quotes.
 Enter |whelp|n for more info. |wlook|n will re-show this screen.
|b==============================================================|n""".format(
    settings.SERVERNAME, utils.get_evennia_version("short")
)
