"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia import TICKER_HANDLER
from evennia import CmdSet, default_cmds, DefaultRoom
from commands.default_cmdsets import ChargenCmdset, RoomCmdSet, ArtessaCmdSet, NotchCmdSet, BridgeCmdSet
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

    def return_appearance(self, looker):
        string = super().return_appearance(looker)

        # Set value of perception/tracking key for returning values.
        room_perception_search_key = looker.location
        looker_perception = looker.db.perception
        looker_tracking = looker.db.tracking

        # Message headers for look_results
        perception_message = f"|015Perception - After careful inspection of {room_perception_search_key}, you discover the following:|n"
        tracking_message = f"|015Tracking - After combing the {room_perception_search_key} for tracks and other signs, you discover the following:|n"

        # Returns list of messages if anything
        room_perception_results = self.return_perception(room_perception_search_key, looker_perception)
        room_tracking_results = self.return_tracking(room_perception_search_key, looker_tracking)

        # Format room perception results for printing
        if room_perception_results:
            format_room_perception_results = [f"|y{result}|n" for result in room_perception_results]
            perception_results = [perception_message].extend(format_room_perception_results)

        if room_tracking_results:
            format_room_tracking_results = [f"|y{result}|n" for result in room_tracking_results]
            # tracking_results = [tracking_message].append(format_room_tracking_results)

        # # If just room perception results, return the desc and header
        # if room_perception_results and not room_tracking_results:
        #     results = [perception_message].append(format_room_perception_results)
        # elif room_tracking_results and not room_perception_results:
        #     results = [tracking_message].append(format_room_tracking_results)
        # elif room_perception_results and room_tracking_results:
        #     perception_results = [perception_message].append(format_room_perception_results)
        #     tracking_results = [tracking_message].append(format_room_tracking_results)
        #     results = [string, perception_results, tracking_results]
        # else:
        #     results = [string]
        #
        # return results

        for result in perception_results:
            looker.msg(f"{result}\n")

    def return_perception(self, perceptionkey, perceptionlevel):
        """
        This looks for an Attribute "obj_perception" and possibly
        returns the value of it.
        Args:
            perceptionkey (str): The perception detail being looked at. This is
                case-insensitive.
        """

        look_results = []

        if self.db.perception_details:
            perception_details = self.db.perception_details.get(perceptionkey.name.lower(), None)
            for details in perception_details:
                if details[0] <= perceptionlevel:
                    look_results.append(details[1])
            return look_results
        else:
            return


    def return_tracking(self, trackingkey, trackinglevel):
        """
        This looks for an Attribute "obj_tracking" and possibly
        returns the value of it.
        Args:
            trackingkey (str): The perception detail being looked at. This is
                case-insensitive.
        """
        look_results = []

        if self.db.tracking_details:
            tracking_details = self.db.tracking_details.get(trackingkey.name.lower(), None)
            for details in tracking_details:
                if details[0] <= trackinglevel:
                    look_results.append(details[1])
            return look_results
        else:
            return

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
            if perceptionkey.lower() in self.db.perception_details:
                self.db.perception_details[perceptionkey.lower()].append((level, description))
            else:
                self.db.perception_details.update({perceptionkey.lower(): [(level, description)]})
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
            if trackingkey.lower() in self.db.tracking_details:
                self.db.tracking_details[trackingkey.lower()].append((level, description))
            else:
                self.db.tracking_details.update({trackingkey.lower(): [(level, description)]})
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

class ArtessaRoom(Room):
    """
    This room used for the Artessa command.
    """
    def at_object_creation(self):
        "this is called only at first creation"
        self.cmdset.add(ArtessaCmdSet, permanent=True)

class NotchRoom(Room):
    """
    This room used for the Notch command.
    """
    def at_object_creation(self):
        "this is called only at first creation"
        self.cmdset.add(NotchCmdSet, permanent=True)

# Weather room

# These are rainy weather strings
RAINY_STRINGS = ["Clouds move in to completely cover the sky, obscuring what might otherwise have been a pleasant day.",
                      "It begins to sprinkle in a soft all-encompassing mist. You would hardly call it rain, though it is certainly wet.",
                      "The rainfall eases a bit and the sky momentarily brightens.",
                      "For a moment it looks like the rain is slowing, then it begins anew with renewed force.",
                      "The rain pummels you with large, heavy drops. You hear the rumble of thunder in the distance.",
                      "The wind is picking up, howling around you, throwing water droplets in your face. It's cold.",
                      "Bright fingers of lightning flash over the sky, moments later followed by a deafening rumble.",
                      "It rains so hard you can hardly see your hand in front of you. You'll soon be drenched to the bone.",
                      "Large clouds rush across the sky, throwing their load of rain over the world.",
                      "The rain ceases, giving you a welcome reprieve, though the clouds seem to be sticking around.",
                      "Cloud cover persists. The air feels heavy and humid."]
# These are sunny weather strings
SUNNY_STRINGS = ["The skies begin to clear and you can see patches of blue among the grey.",
                      "The clouds float away and above you is a gorgeous, clear sky. Birds flit over your head.",
                      "The wind picks up, catching your clothes. Soft, white clouds scuttle quickly across the sky.",
                      "The air stills and the sun warms you.",
                      "You hear the breeze before it reaches you; the trees whisper as it passes through their leaves.",
                      "Rays of sunshine beam through the clouds in the sky.",
                      "The area darkens slightly as a cloud passes over the sun. The drop in temperature is noticeable, but not extreme.",
                      "Recent rains make the air smell fresh, but damp. Water droplets on the grass sparkle in the sun.",
                      "A bird of prey soars overhead on a warm draft. White clouds hang in the air high above.",
                      "The sun peaks out from behind intermittent clouds, suggesting the threat of spring rain."]

class WeatherRoom(DefaultRoom):
    """
    This sets up an outdoor room typeclass. At irregular intervals,
    the effects of weather will show in the room. Outdoor rooms should
    inherit from this.
    """
    current_weather = ""
    current_weather_type = []
    weather_counter = 0

    def at_object_creation(self):
        """
        Called when object is first created.
        We set up a ticker to update this room regularly.
        """
        super(WeatherRoom, self).at_object_creation()

        weather_choice = random.randint(0, 1)
        if weather_choice == 0:
            self.current_weather_type = RAINY_STRINGS
        else:
            self.current_weather_type = SUNNY_STRINGS

        TICKER_HANDLER.add(30*60, self.update_weather, idstring="weather_ticker", persistent=False)

    def update_weather(self, *args, **kwargs):
        """
        Called by the tickerhandler at regular intervals.
        """
        previous_weather = self.current_weather

        # When the weather has broadcasted 2 times (every 30 minutes)...
        if self.weather_counter >= 1:
            previous_weather_type = self.current_weather_type

            # On the last weather broadcast, randomly decide whether the next hour will be sunny or rainy.
            # There is a 75% chance the weather will be the same, and a 25% chance the weather will be different.
            new_weather_choice = random.randint(0, 100)
            if new_weather_choice > 75:
                if previous_weather_type == RAINY_STRINGS:
                    self.current_weather_type = SUNNY_STRINGS
                else:
                    self.current_weather_type = RAINY_STRINGS

            # Set the weather broadcast to the first value in the weather type array, to indicate that the
            # weather is changing. If the weather is not changing, pick a random value from the array.
            if self.current_weather_type == previous_weather_type:
                while self.current_weather == previous_weather or self.current_weather == self.current_weather_type[0]:
                    self.current_weather = random.choice(self.current_weather_type)
            else:
                self.current_weather = self.current_weather_type[0]

            # Reset the weather counter to 0.
            self.weather_counter = 0
        else:
            while self.current_weather == previous_weather or self.current_weather == self.current_weather_type[0]:
                self.current_weather = random.choice(self.current_weather_type)
            self.weather_counter += 1

        self.msg_contents("|w%s|n" % self.current_weather)

MARKET_STRINGS = [
    "\"Get your smoked meats here! Two for a coppa'...\"",
    "\"Fresh cuts today! Chops, liver, ribs, get it before the flies do, friends!\"",
    "\"Come and see the man of many cheeses! Finest cheeses in all of Arnesse...!\"",
    "\"Tomatoes, olives, grapes... fresh bread, he'ah! Get it at Gilfrain's...!\"",
    "\"Fine wrought iron! Intricate metalwork... artisan quality...\"",
    "\"Good wool and linen for dresses. Leather hides for your saddles and armor. Nearly out... good prices!\"",
    "\"Boots, shoes, ladies' slippers... children's shoes, booties. Produced in Highcourt! Come and size a pair for yourself...\"",
    "\"Cutlery from the Dusklands... sharp as the day it left the smithy! Guarenteed!\"",
    "\"Brought in some horses to thin me herd, stout geldings and mares... This one would made a good palfrey, he would!\"",
    "\"Mule for sale! Won't find a more reliable animal!\"",
    "\"Sturdy farm tools at Red's Smithy... These'll last ye a life time!\"",
    "\"Freshly cut flowers! Fit even for Queen Aline herself, your loved ones will be delighted!\"",
    "\"Git yer fine leather goods here... Pouches designed to deter thieves! Don't believe me? Come see fer yerself!\"",
    "\"Refreshing beer, cooled in the nearby stream! Got a couple barrels of Beggar's Amber!\"",
    "\"Fine wines! Imports from Orgonne and Corsicana, come by for a tasting...\"",
    "\"Pelts and furs from the Barrier Mountains... Never too early to prepare for winter!\"",
    "\"Tarkathi crafts! Fine Tarkathi crafts, direct from Tyranthis!\"",
    "A nearby merchant tells a customer, \"Khalico has wares if you have coin...\"",
    "A merchant is overheard saying, \"Come back when you're ready to spend more coin... goodness knows I could use it...\"",
    "\"Got some good pieces out here if yer looking to buy. More inside the tent!\""
]

class MarketRoom(WeatherRoom):

    # A list to keep track of the phrases that have already been broadcast.
    used_phrases = []

    def at_object_creation(self):
        """
        Called when object is first created.
        We set up a ticker to update this room regularly.
        """
        super(MarketRoom, self).at_object_creation()

        TICKER_HANDLER.add(10*60, self.update_market, idstring="market_ticker", persistent=False)

    def update_market(self, *args, **kwargs):
        """
        Called by the tickerhandler at regular intervals.
        """

        # If we have gone through all of the Market broadcasts, then clear the used_phrases list.
        if len(self.used_phrases) == len(MARKET_STRINGS):
            self.used_phrases.clear()

        next_phrase = random.choice(MARKET_STRINGS)

        # Retrieve a new market broadcast that has not been played yet.
        while next_phrase in self.used_phrases:
            next_phrase = random.choice(MARKET_STRINGS)

        # Add the new phrase to the used_phrases list.
        self.used_phrases.append(next_phrase)

        self.msg_contents("|w%s|n" % next_phrase)

# These are rookery strings
ROOKERY_STRINGS = ["Ravens peer down from several perches with their beady black eyes. It feels like they're studying you.",
                      "*splat* ... White poo lands on the stone floor, dangerously close.",
                      "A group of ravens croak loudly as their neighbor lands on their perch and ruffles its feathers, getting comfortable.",
                      "The soft sh-sh-sh sounds of feather moving against feather is constant.",
                      "A raven takes flight from the floor, disturbing dust and feathers which float up in the rays of light coming from the windows.",
                      "Several ravens exchange a series of gurgling croaks before settling down into soft beak snaps.",
                      "A few ravens look up as one of their brethren soars in from a high window.",
                      "Nearby, a jet black bird intently preens itself.",
                      "One rather large raven hops from one roost to the next, stopping now and then to wipe its beak across the wooden perches.",
                      "A fight breaks out between two ravens. They exchange snaps and shrill caws before one flies away from the other."]

class RookeryRoom(DefaultRoom):

    # A list to keep track of the phrases that have already been broadcast.
    used_phrases = []

    def at_object_creation(self):
        """
        Called when object is first created.
        We set up a ticker to update this room regularly.
        """
        super(RookeryRoom, self).at_object_creation()

        TICKER_HANDLER.add(10*60, self.update_rookery, idstring="rookery_ticker", persistent=False)

    def update_rookery(self, *args, **kwargs):
        """
        Called by the tickerhandler at regular intervals.
        """

        # If we have gone through all of the Market broadcasts, then clear the used_phrases list.
        if len(self.used_phrases) == len(ROOKERY_STRINGS):
            self.used_phrases.clear()

        next_phrase = random.choice(ROOKERY_STRINGS)

        # Retrieve a new market broadcast that has not been played yet.
        while next_phrase in self.used_phrases:
            next_phrase = random.choice(ROOKERY_STRINGS)

        # Add the new phrase to the used_phrases list.
        self.used_phrases.append(next_phrase)

        self.msg_contents("|w%s|n" % next_phrase)


"""
Bridge Room
"""

BRIDGE_WEATHER = (
    "The rain intensifies, making the planks of the bridge even more slippery.",
    "A gust of wind throws the rain right in your face.",
    "The rainfall eases a bit and the sky momentarily brightens.",
    "The bridge shakes under the thunder of a closeby thunder strike.",
    "The rain pummels you with large, heavy drops. You hear the distinct howl of a large hound in the distance.",
    "The wind is picking up, howling around you and causing the bridge to sway from side to side.",
    "Some sort of large bird sweeps by overhead, giving off an eery screech. Soon it has disappeared in the gloom.",
    "The bridge sways from side to side in the wind.",
    "Below you a particularly large wave crashes into the rocks.",
    "From the ruin you hear a distant, otherwordly howl. Or maybe it was just the wind.",
)

class BridgeRoom(DefaultRoom):
    """
    The bridge room implements an unsafe bridge. It also enters the player into
    a state where they get new commands so as to try to cross the bridge.
     We want this to result in the account getting a special set of
     commands related to crossing the bridge. The result is that it
     will take several steps to cross it, despite it being represented
     by only a single room.
     We divide the bridge into steps:
        self.db.west_exit     -   -  |  -   -     self.db.east_exit
                              0   1  2  3   4
     The position is handled by a variable stored on the character
     when entering and giving special move commands will
     increase/decrease the counter until the bridge is crossed.
     We also has self.db.fall_exit, which points to a gathering
     location to end up if we happen to fall off the bridge (used by
     the CmdLookBridge command).
    """

    def at_object_creation(self):
        """Setups the room"""
        # this will start the weather room's ticker and tell
        # it to call update_weather regularly.
        super().at_object_creation()
        # this identifies the exits from the room (should be the command
        # needed to leave through that exit). These are defaults, but you
        # could of course also change them after the room has been created.
        self.db.west_exit = "cliff"
        self.db.east_exit = "gate"
        self.db.fall_exit = "cliffledge"
        # add the cmdset on the room.
        self.cmdset.add_default(BridgeCmdSet)
        # since the default Character's at_look() will access the room's
        # return_description (this skips the cmdset) when
        # first entering it, we need to explicitly turn off the room
        # as a normal view target - once inside, our own look will
        # handle all return messages.
        self.locks.add("view:false()")

    def update_weather(self, *args, **kwargs):
        """
        This is called at irregular intervals and makes the passage
        over the bridge a little more interesting.
        """
        if random.random() < 80:
            # send a message most of the time
            self.msg_contents("|w%s|n" % random.choice(BRIDGE_WEATHER))

    def at_object_receive(self, character, source_location):
        """
        This hook is called by the engine whenever the player is moved
        into this room.
        """
        if character.has_account:
            # we only run this if the entered object is indeed a player object.
            # check so our east/west exits are correctly defined.
            wexit = search_object(self.db.west_exit)
            eexit = search_object(self.db.east_exit)
            fexit = search_object(self.db.fall_exit)
            if not (wexit and eexit and fexit):
                character.msg(
                    "The bridge's exits are not properly configured. "
                    "Contact an admin. Forcing west-end placement."
                )
                character.db.tutorial_bridge_position = 0
                return
            if source_location == eexit[0]:
                # we assume we enter from the same room we will exit to
                character.db.tutorial_bridge_position = 4
            else:
                # if not from the east, then from the west!
                character.db.tutorial_bridge_position = 0
            character.execute_cmd("look")

    def at_object_leave(self, character, target_location):
        """
        This is triggered when the player leaves the bridge room.
        """
        if character.has_account:
            # clean up the position attribute
            del character.db.tutorial_bridge_position
