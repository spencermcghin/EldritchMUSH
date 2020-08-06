"""
Room

Rooms are simple containers that has no location of their own.

"""
# Local imports
from evennia import TICKER_HANDLER
from evennia import CmdSet, default_cmds, DefaultRoom
from evennia import utils
from commands.default_cmdsets import ChargenCmdset, RoomCmdSet, ArtessaCmdSet, NotchCmdSet, AltarCmdSet, HammerCmdSet
from commands import command
from typeclasses.characters import Character
from typeclasses.npc import Npc

# Imports
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

    def at_object_receive(self, obj, source_location):
        if utils.inherits_from(obj, 'Npc'): # An NPC has entered
            obj.msg("if statement")
            pass
        else:
            if utils.inherits_from(obj, 'Character'):
                obj.msg("character")
                # A PC has entered, NPC is caught above.
                # Cause the character to look around
                obj.execute_cmd('look')
                for item in self.contents:
                    if utils.inherits_from(item, 'Npc'):
                        # An NPC is in the room
                        item.at_char_entered(obj)


    def at_object_creation(self):
        """
        Called when room is first created
        """

        self.cmdset.add_default(RoomCmdSet)
        # Holds character in for combat loop. Stores character,
        # and command entered.
        self.db.combat_loop = []


    def return_appearance(self, looker):
        string = super().return_appearance(looker)

        # Set value of perception/tracking key for returning values.
        room_perception_search_key = looker.location
        looker_perception = looker.db.perception
        looker_tracking = looker.db.tracking

        # Message headers for look_results
        perception_message = f"|530Perception|n - After careful inspection of the {room_perception_search_key}, you discover the following:\n"
        tracking_message = f"|210Tracking|n - After combing the {room_perception_search_key} for tracks and other signs, you discover the following:\n"

        # Returns list of messages if anything
        room_perception_results = self.return_perception(room_perception_search_key, looker_perception)
        room_tracking_results = self.return_tracking(room_perception_search_key, looker_tracking)

        # List for final print
        final_payload = [string]

        # Format room perception results for printing
        if room_perception_results:
            format_room_perception_results = [f"|=t{result}|n\n" for result in room_perception_results]
            perception_results = [perception_message] + format_room_perception_results
            final_payload.extend(perception_results)

        if room_tracking_results:
            format_room_tracking_results = [f"|=t{result}|n\n" for result in room_tracking_results]
            tracking_results = [tracking_message] + format_room_tracking_results
            final_payload.extend(tracking_results)

        for line in final_payload:
            looker.msg(f"{line}\n")

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

class HammerRoom(Room):
    """
    This room used for the Notch command.
    """
    def at_object_creation(self):
        "this is called only at first creation"
        self.cmdset.add(HammerCmdSet, permanent=True)

class AltarRoom(Room):
    """
    This room used for the Notch command.
    """
    def at_object_creation(self):
        "this is called only at first creation"
        self.cmdset.add(AltarCmdSet, permanent=True)

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

class WeatherRoom(Room):
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

        TICKER_HANDLER.add(30*60, self.update_weather, idstring="weather_ticker", persistent=True)

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

        TICKER_HANDLER.add(5*60, self.update_market, idstring="market_ticker", persistent=True)

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

# Need to finish adding carnival shouts.
CARNIVAL_STRINGS = [
    "\"Test yer strength he'ah! Think yer strong enough? Prove it at The Hammer!\"",
    "\"Fuck the king...\"",
    "\"See the lady serpents, the mistress ophidia...shows every hour on the hour...\"",
    "\"Follow the cat, follow the mouse, find your way through the looking glass house...\"",
    "\"Find yer way to the golden fist...test your mettle...break a nose or get one broke! You'll never receive a finer kiss than at the golde fist!\"",
    "\"Piss off ya ruddy cunt...\"",
    "\"Exotic inhalants at the gardens...indulge your every whim...kneel at the feet of the goddess herself, ophidia!\"",
    "\"Think yer good with a dagger? Prove it at the notch...\"",
    "\"Spin the wheel of pain. Win a prize, or go insane...\"",
    "\"See the show no one's talking about...the brood of queen aline, at linster's foolery. See it before its imminent demise...\"",
    "\"Roast fowl, 1 for a copper...\"",
    "\"Daphne ain’t no cirkee. She’s a right pomp.\"",
    "\"Daphne makes her dresses out of sack cloth\"",
    "\"Daphne’s stitches are crooked\"",
    "\"Reynaldo couldn’t strike a spark!\"",
    "\"Reynaldo’s cloaks are made of farmer’s burlap\"",
    "\"What does Artessa have in store for you? Find out at Artessa's Auguary!\"",
    "\"Shazar Trap-springer, hahhhh\"",
    "\"So greedy, so dumb, for the right price, Shazar’ll poison yer mum\"",
    "\"Khepri hates the queen!\"",
    "\"Khepri sold my da’\"",
    "\"He’ll spear all your cats, he’ll piss on your dog, Khepri’s a bastard and smells like a hog!\"",
    "A nearby Cirque member tells a customer, I'll not take a copper less than tha'...\"\""
]

class CarnivalRoom(WeatherRoom):

    # A list to keep track of the phrases that have already been broadcast.
    used_phrases = []

    def at_object_creation(self):
        """
        Called when object is first created.
        We set up a ticker to update this room regularly.
        """
        super(CarnivalRoom, self).at_object_creation()

        TICKER_HANDLER.add(5*60, self.update_carnival, idstring="carnival_ticker", persistent=True)

    def update_carnival(self, *args, **kwargs):
        """
        Called by the tickerhandler at regular intervals.
        """

        # If we have gone through all of the Carnival broadcasts, then clear the used_phrases list.
        if len(self.used_phrases) == len(CARNIVAL_STRINGS):
            self.used_phrases = []

        next_phrase = random.choice(CARNIVAL_STRINGS)

        # Retrieve a new market broadcast that has not been played yet.
        while next_phrase in self.used_phrases:
            next_phrase = random.choice(CARNIVAL_STRINGS)

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

class RookeryRoom(Room):

    # A list to keep track of the phrases that have already been broadcast.
    used_phrases = []

    def at_object_creation(self):
        """
        Called when object is first created.
        We set up a ticker to update this room regularly.
        """
        super(RookeryRoom, self).at_object_creation()

        TICKER_HANDLER.add(8*60, self.update_rookery, idstring="rookery_ticker", persistent=True)

    def update_rookery(self, *args, **kwargs):
        """
        Called by the tickerhandler at regular intervals.
        """

        # If we have gone through all of the Rookery broadcasts, then clear the used_phrases list.
        if len(self.used_phrases) == len(ROOKERY_STRINGS):
            self.used_phrases.clear()

        next_phrase = random.choice(ROOKERY_STRINGS)

        # Retrieve a new market broadcast that has not been played yet.
        while next_phrase in self.used_phrases:
            next_phrase = random.choice(ROOKERY_STRINGS)

        # Add the new phrase to the used_phrases list.
        self.used_phrases.append(next_phrase)

        self.msg_contents("|w%s|n" % next_phrase)

# These are evil fun house strings
FUNHOUSE_STRINGS = ["1",
                      "2",
                      "3",
                      "4",
                      "5",
                      "6",
                      "7",
                      "8",
                      "9",
                      "10"]

class FunHouseRoom(Room):

    # A list to keep track of the phrases that have already been broadcast.
    used_phrases = []

    def at_object_creation(self):
        """
        Called when object is first created.
        We set up a ticker to update this room regularly.
        """
        super(FunHouseRoom, self).at_object_creation()

        TICKER_HANDLER.add(10*60, self.update_funhouse, idstring="funhouse_ticker", persistent=True)

    def update_funhouse(self, *args, **kwargs):
        """
        Called by the tickerhandler at regular intervals.
        """

        # If we have gone through all of the FunHouse broadcasts, then clear the used_phrases list.
        if len(self.used_phrases) == len(FUNHOUSE_STRINGS):
            self.used_phrases.clear()

        next_phrase = random.choice(FUNHOUSE_STRINGS)

        # Retrieve a new market broadcast that has not been played yet.
        while next_phrase in self.used_phrases:
            next_phrase = random.choice(FUNHOUSE_STRINGS)

        # Add the new phrase to the used_phrases list.
        self.used_phrases.append(next_phrase)

        self.msg_contents("|w%s|n" % next_phrase)

OPHIDIA_STRINGS = [
    "\"Come one, come all and feast your eyes on the amber jewel of Tarkath, for your viewing pleasure...\"\n",
    "|230The lights dim, as candles at the wooden tables are snuffed out by the servants...\nMusic begins to play, though you don't see any musicians present.|n\n",
    "|230The curtain draws back, revealing a well dressed, portly man with slicked back, black hair that shines with a fresh applicaiton of grease.\n",
    "\"Come, sit, be not afraid, for the Mistress Ophidia is here to soothe your fears and caress your desires.\"\n",
    "\"Kneel and worship at her altar, bow your head, pay homage...dine upon her divinity...\"",
    "|230The well dressed, portly man finishes his display of broad, sweeping gestures, and disappears behind the heavy dark curtain.|n\n"
    "|230What little light there is now completely fades away, until the room goes black and the music dies.|n\n",
    "|230And then from nowhere, a thousand points of light, like the stars in the night sky illuminate the stage, rotating in celestial accord.|n\n",
    "|230The music starts again, slow at first. A lone stringed instruments starts to play a seductive melody in a minor key. The dreamers on the floor rouse at the sound.|n\n",
    "|230As the melody reaches its crescendo, the curtains begin to part, slowly curling in on themselves, until reaching the edge of the stage|n\n",
    "|230At a break in the melody, a woman then emerges from the nighted abyss beyond the curtain. She is goregous;voluptuous and as soft as new silk, covered minimally in the same. Wrapped around her neck and covering her breasts is a large python, its shining scales a brackish green in the low light of the twinkling stars..|n\n",
    "|230She begins to dance, slowly at first, the python moving in time with her lithe gestations. In one practiced motion, she twirls, her hair, dark and shining, comes undone from its long braid. From the crowd comes an audible gasp.|n\n",
    "|230She moves quicker now, and from the audience comes one of the crowd, lurching at the dancing beauty.|n\n",
    "|230A large woman erupts from a darkened corner to tackle the would be intruder, though no one seems to notice. Especially Ophidia...|n\n",
    "|230The woman dancing on the stage moves quicker now...quicker...to a dizzying melody that is sad and gorgeous in the way twilight is these things.|n\n",
    "|230The star lights suddenly shut off, casting the room into a pitch dark.|n\n",
    "|230One by one, the tiny points of light illuminate once again, as though on the first days of everything...|n\n",
    "|230Alone on the stage is the python whose shining scales are a brackish green. Nowhere to be seen is the one called Mistress Ophidia."
]

class OphidiaRoom(Room):

    # A list to keep track of the phrases that have already been broadcast.
    show_counter = 0

    def at_object_creation(self):
        """
        Called when object is first created.
        We set up a ticker to update this room regularly.
        """
        super(OphidiaRoom, self).at_object_creation()

        TICKER_HANDLER.add(60*60, self.start_show, idstring="ophidia_show_ticker", persistent=True)

    def start_show(self, *args, **kwargs):
        # create ticker - go through all phrases - delete ticker
        TICKER_HANDLER.add(20, self.update_show, idstring="ophidia_start_show_ticker", persistent=False)

    def update_show(self, *args, **kwargs):
        """
        Called by the tickerhandler at regular intervals.
        """

        if self.show_counter >= len(OPHIDIA_STRINGS):
            self.show_counter = 0
            TICKER_HANDLER.remove(20, self.update_show, idstring="ophidia_start_show_ticker")
        else:
            phrase = OPHIDIA_STRINGS[self.show_counter]
            self.msg_contents("%s" % phrase)
            self.show_counter += 1

PUPPET_STRINGS = [
    "|230The lights dim and a small spot light covers the large, sad booth in a coarse and ruddy glow.|n\n",
    "|230Two puppets emerge from below the small stage, one in a threadbare green and gold noble lady's dress, the other in an outfit that might befit a king of Arnesse.|n\n",
    "|230The lights dim and a small spot light covers the booth in a coarse and ruddy glow.|n\n",
    "|230The lights dim and a small spot light covers the booth in a coarse and ruddy glow.|n\n",

    "\"On this day \"",
    "\"Come, sit, be not afraid, for the Mistress Ophidia is here to soothe your fears and caress your desires.\"",
    "\"Kneel and worship at her altar, bow your head, pay homage...dine upon her divinity...\"",

]

class PuppetRoom(Room):

    # A list to keep track of the phrases that have already been broadcast.
    show_counter = 0

    def at_object_creation(self):
        """
        Called when object is first created.
        We set up a ticker to update this room regularly.
        """
        super(PuppetRoom, self).at_object_creation()

        TICKER_HANDLER.add(60*60, self.start_show, idstring="puppet_show_ticker", persistent=True)

    def start_show(self, *args, **kwargs):
        # create ticker - go through all phrases - delete ticker
        TICKER_HANDLER.add(20, self.update_show, idstring="puppet_start_show_ticker", persistent=False)

    def update_show(self, *args, **kwargs):
        """
        Called by the tickerhandler at regular intervals.
        """

        if self.show_counter >= len(PUPPET_STRINGS):
            self.show_counter = 0
            TICKER_HANDLER.remove(2, self.update_show, idstring="puppet_start_show_ticker")
        else:
            phrase = PUPPET_STRINGS[self.show_counter]
            self.msg_contents("%s" % phrase)
            self.show_counter += 1
