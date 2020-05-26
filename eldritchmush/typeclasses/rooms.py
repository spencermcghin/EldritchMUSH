"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia import DefaultRoom, TICKER_HANDLER
from evennia import CmdSet, default_cmds
from commands.default_cmdsets import ChargenCmdset, RoomCmdSet
from commands import command

import random


class Room(DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """

    def at_object_creation(self):
        """
        Called when room is first created
        """

        self.cmdset.add_default(RoomCmdSet)

    def return_perception(self, perceptionkey, perceptionlevel):
        """
        This looks for an Attribute "obj_perception" and possibly
        returns the value of it.
        Args:
            perceptionkey (str): The perception detail being looked at. This is
                case-insensitive.
        """

        look_results = []

        try:
            perception_details = self.db.perception_details

        except:
            look_results.append("There is nothing matching that description.")

        else:

            if perception_details.get(perceptionkey.lower(), None) is not None:
                for details in perception_details[perceptionkey.lower()]:
                    if details[0] <= perceptionlevel:
                        look_results.append(details[1])

        return look_results

    def return_tracking(self, trackingkey, trackinglevel):
        """
        This looks for an Attribute "obj_tracking" and possibly
        returns the value of it.
        Args:
            trackingkey (str): The perception detail being looked at. This is
                case-insensitive.
        """
        tracking_details = self.db.tracking_details

        look_results = []

        if tracking_details.get(trackingkey.lower(), None) is not None:
            for details in tracking_details[trackingkey.lower()]:
                if details[0] <= trackinglevel:
                    look_results.append(details[1])
        else:
            look_results.append("There is nothing matching that description.")

        return look_results

    def set_perception(self, perceptionkey, level, description):
        """
        This sets a perception on the room.
        Args:
            perceptionkey (str): The detail identifier to add (for
                aliases you need to add multiple keys to the
                same description). Case-insensitive.
            level (int): Level of the perception needed to access the information.
            description (str): The text to return when looking
                at the given perceptionkey.
        """
        if self.db.perception_details:
            self.db.perception_details[perceptionkey.lower()].append((level, description))
        else:
            self.db.perception_details = {perceptionkey.lower(): [(level, description)]}

    def set_tracking(self, trackingkey, level, description):
        """
        This sets a perception on the room.
        Args:
            trackingkey (str): The detail identifier to add (for
                aliases you need to add multiple keys to the
                same description). Case-insensitive.
            level (int): Level of the perception needed to access the information.
            description (str): The text to return when looking
                at the given perceptionkey.
        """
        if self.db.tracking_details:
            self.db.tracking_details[trackingkey.lower()].append((level, description))
        else:
            self.db.tracking_details = {trackingkey.lower(): [(level, description)]}

class ChargenRoom(Room):
    """
    This room class is used by character-generation rooms. It makes
    the ChargenCmdset available.
    """
    def at_object_creation(self):
        "this is called only at first creation"
        self.cmdset.add(ChargenCmdset, permanent=True)

# Weather room

# These are rainy weather strings
WEATHER_STRINGS = (
    "Clouds cover the sky, obscuring might otherwise have been a pleasant day.",
    "It begins to sprinkle in a soft all-encompassing mist. You would harldy call it rain, though it is certainly wet.",
    "The rainfall eases a bit and the sky momentarily brightens.",
    "For a moment it looks like the rain is slowing, then it begins anew with renewed force.",
    "The rain pummels you with large, heavy drops. You hear the rumble of thunder in the distance.",
    "The wind is picking up, howling around you, throwing water droplets in your face. It's cold.",
    "Bright fingers of lightning flash over the sky, moments later followed by a deafening rumble.",
    "It rains so hard you can hardly see your hand in front of you. You'll soon be drenched to the bone.",
    "Lightning strikes in several thundering bolts, striking the trees in the forest to your west.",
    "You hear the distant howl of what sounds like some sort of dog or wolf.",
    "Large clouds rush across the sky, throwing their load of rain over the world.",
)

class WeatherRoom(Room):
    """
    This should probably better be called a rainy room...
    This sets up an outdoor room typeclass. At irregular intervals,
    the effects of weather will show in the room. Outdoor rooms should
    inherit from this.
    """

    def at_object_creation(self):
        """
        Called when object is first created.
        We set up a ticker to update this room regularly.
        Note that we could in principle also use a Script to manage
        the ticking of the room; the TickerHandler works fine for
        simple things like this though.
        """
        super().at_object_creation()
        # subscribe ourselves to a ticker to repeatedly call the hook
        # "update_weather" on this object. The interval is randomized
        # so as to not have all weather rooms update at the same time.
        self.db.interval = random.randint(50, 70)
        TICKER_HANDLER.add(
            interval=self.db.interval, callback=self.update_weather, idstring="tutorial"
        )

    def update_weather(self, *args, **kwargs):
        """
        Called by the tickerhandler at regular intervals. Even so, we
        only update 20% of the time, picking a random weather message
        when we do. The tickerhandler requires that this hook accepts
        any arguments and keyword arguments (hence the *args, **kwargs
        even though we don't actually use them in this example)
        """
        if random.random() < 0.2:
            # only update 20 % of the time
            self.msg_contents("|w%s|n" % random.choice(WEATHER_STRINGS))
