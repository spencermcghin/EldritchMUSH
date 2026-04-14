"""
world/populate_mystvale.py — Mystvale (reboot campaign) world builder.

Creates the new campaign world centered on Mystvale. Idempotent — safe
to re-run; skips rooms/exits/objects that already exist by key.

Run once from inside eldritchmush/:
    evennia shell -c "exec(open('world/populate_mystvale.py').read())"

Or via start.sh migration for automatic deploy-time setup.

Zones assigned to each room via room.db.zone for the frontend map
filtering system (see server/conf/inputfuncs.py __map_ui__ handler).
"""
import evennia
# Ensure Evennia is fully initialized (populates _create.create_object,
# evennia.search_object, etc.) Required when this script is run from a
# plain python shell with only django.setup() — without this,
# _create.create_object is None and we get TypeError: NoneType not callable.
try:
    evennia._init()
except Exception:
    pass
from evennia.objects.models import ObjectDB
from evennia.utils import create as _create


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_or_create_room(key, typeclass_path, desc, zone=None):
    existing = ObjectDB.objects.filter(
        db_key=key, db_typeclass_path=typeclass_path
    ).first()
    if existing:
        print(f"  EXISTS  : {key}")
        if zone:
            existing.attributes.add("zone", zone)
        return existing
    room = _create.create_object(typeclass_path, key=key)
    room.db.desc = desc
    if zone:
        room.attributes.add("zone", zone)
    room.save()
    print(f"  CREATED : {key} [{zone or 'no-zone'}]")
    return room


def link(room_a, exit_a, room_b, exit_b, alias_a=None, alias_b=None):
    """Create two exits between rooms, skipping if already present."""
    def _make(name, loc, dest, alias):
        if not ObjectDB.objects.filter(db_key=name, db_location=loc.pk).exists():
            ex = _create.create_object(
                "evennia.objects.objects.DefaultExit",
                key=name, location=loc, destination=dest
            )
            if alias:
                ex.aliases.add(alias)
    _make(exit_a, room_a, room_b, alias_a)
    _make(exit_b, room_b, room_a, alias_b)


def create_obj(key, typeclass_path, location, desc):
    existing = ObjectDB.objects.filter(
        db_key=key, db_location=location.pk
    ).first()
    if existing:
        print(f"  EXISTS  : {key} (in {location.key})")
        return existing
    obj = _create.create_object(typeclass_path, key=key, location=location)
    obj.db.desc = desc
    obj.save()
    print(f"  OBJECT  : {key} → {location.key}")
    return obj


def move_to(obj, new_location):
    """Move an existing object (like a crafting station) to a new room."""
    if obj and obj.location != new_location:
        obj.move_to(new_location, quiet=True)
        print(f"  MOVED   : {obj.key} → {new_location.key}")


# ===========================================================================
# RENAME MIGRATION — "Mistvale" → "Mystvale"
# Earlier runs of this script used the spelling "Mistvale"; the canonical
# spelling is "Mystvale" with a Y. Rename any stale rooms + zone attrs.
# Also update zone attributes on all rooms that have "Mistvale" as their
# zone, so the frontend map zone filter works correctly.
# ===========================================================================
print("\n=== RENAME MIGRATION: Mistvale → Mystvale ===")
for stale in ObjectDB.objects.filter(db_key__icontains="Mistvale"):
    new_name = stale.db_key.replace("Mistvale", "Mystvale").replace("mistvale", "mystvale")
    if new_name != stale.db_key:
        print(f"  RENAMED : '{stale.db_key}' → '{new_name}'")
        stale.db_key = new_name
        stale.save()
# Update zone attrs on all rooms (we can't filter by attribute value easily)
for room in ObjectDB.objects.filter(db_typeclass_path__contains="typeclasses.rooms"):
    z = room.attributes.get("zone", default=None)
    if z and ("Mistvale" in z or "mistvale" in z):
        new_z = z.replace("Mistvale", "Mystvale").replace("mistvale", "mystvale")
        room.attributes.add("zone", new_z)
        print(f"  ZONE    : {room.db_key} zone '{z}' → '{new_z}'")


# ===========================================================================
# MYSTVALE ZONE — the central hub town
# ===========================================================================
print("\n=== MYSTVALE ROOMS ===")

mystvale_square = get_or_create_room(
    "Mystvale Square",
    "typeclasses.rooms.Room",
    "The heart of Mystvale — a broad cobbled square ringed by weathered stone "
    "buildings and timber shopfronts. A stone well stands at its center, ringed "
    "by the scars of old mist-sickness and recent siege. The banners of House "
    "Laurent's Stag Hall fly alongside the colors of the Burgomaster's office. "
    "Merchants hawk their wares near the marketplace, while the smell of the "
    "forge drifts in from the Crafter's Quarter.\n\n"
    "Exits lead to |wThe Aentact|n, the |wMarketplace|n, the |wCrafter's Quarter|n, "
    "the |wTown Hall|n, |wManor Row|n to the north, the |wsouth gate|n, and the "
    "|wnorth gate|n.",
    zone="Mystvale",
)

aentact = get_or_create_room(
    "The Aentact",
    "typeclasses.rooms.Room",
    "The Aentact is Mystvale's tavern, council chamber, and beating heart. "
    "A long hearth roars against the north wall, its smoke curling up past "
    "beams hung with antlers, tattered banners, and the Crow Favor tokens of "
    "guests past. Rough tables crowd the flagstone floor. A rumor board near "
    "the entrance is plastered with parchment scraps — news from Gateway, "
    "whispers from beyond the Mists. In one corner stands an iron-banded box "
    "marked for Decisive Moments — the mechanism by which the town decides "
    "its fate.\n\n"
    "Back to |wMystvale Square|n.",
    zone="Mystvale",
)

marketplace = get_or_create_room(
    "The Mystvale Marketplace",
    "typeclasses.rooms.MarketRoom",
    "A sprawling marketplace under oiled-canvas awnings, where the Cirque "
    "caravan has set its colorful wagons. Painted cloth snaps in the wind "
    "above stalls of iron tools, dried herbs, bolts of cloth, strange curios "
    "brought through the Mists. A Cirque trader minds the central pavilion "
    "while hawkers shout their prices. Resource crates stamped with the "
    "Cirque's sigil stack against the walls.\n\n"
    "Back to |wMystvale Square|n.",
    zone="Mystvale",
)

crafter_quarter = get_or_create_room(
    "The Crafter's Quarter",
    "typeclasses.rooms.Room",
    "A grid of workshops crammed against Mystvale's eastern wall. Smoke rises "
    "from the forge's chimney; steam hisses from the alchemist's still; the "
    "rhythmic thock of the artificer's mallet keeps time. The air tastes of "
    "hot iron, herbs, and sawdust. Workbenches stand in the open so apprentices "
    "can learn the trade from the street. This is where the goods that keep "
    "the Annwyn alive are made.\n\n"
    "Back to |wMystvale Square|n.",
    zone="Mystvale",
)

town_hall = get_or_create_room(
    "The Town Hall",
    "typeclasses.rooms.Room",
    "The Burgomaster's office — modest, cluttered, and smelling faintly of "
    "apothecary herbs. Ledgers, maps, and official seals cover a heavy oak "
    "desk. A rack of signed writs and proclamations hangs on the wall. The "
    "Burgomaster's chair is worn smooth from long hours of adjudicating "
    "disputes between crafters, merchants, and noblefolk. A tax coffer is "
    "bolted to the floor behind the desk. A small side table holds a ledger "
    "of current town coffers and a posting for the Sheriff's rounds.\n\n"
    "Back to |wMystvale Square|n.",
    zone="Mystvale",
)

herbalist_garden = get_or_create_room(
    "The Herbalist's Garden",
    "typeclasses.rooms.WeatherRoom",
    "A walled garden tucked between the Town Hall and the Chantry. Raised "
    "beds of sage, comfrey, willow-bark, and rarer herbs grow in careful "
    "rows. A small greenhouse shelters the delicate vale-plants brought "
    "back by the first expeditions. The air smells of mint and turned earth. "
    "A weathered sign reads: |wHerbalists and gatherers welcome — take what "
    "you need, leave what you owe.|n\n\n"
    "Back to |wMystvale Square|n.",
    zone="Mystvale",
)

chantry = get_or_create_room(
    "The Aurorym Chantry",
    "typeclasses.rooms.Room",
    "A modest stone chapel dedicated to the Aurorym faith, lit by tall "
    "candles and the pale glow of stained glass depicting the Passage of "
    "Magnus. An altar of polished white stone stands at the chancel, and "
    "brass censers hang from the beams, swaying gently. Aurons and pilgrims "
    "kneel in silent prayer. A cloistered alcove holds the Book of Magnus, "
    "its pages marked by ribbons of blue and gold.\n\n"
    "Back to |wMystvale Square|n.",
    zone="Mystvale",
)

black_market = get_or_create_room(
    "The Back Alley",
    "typeclasses.rooms.Room",
    "A narrow alley behind the Marketplace, shadowed by overhanging eaves "
    "and forgotten signs. A single lantern flickers above an iron-bound "
    "door. Those who know the right knock find the Menagerie's black market "
    "within — stolen heirlooms, banned lore, poisons, and other vices for "
    "those with coin and discretion. Strangers are watched. The unwary are "
    "robbed.\n\n"
    "Back to |wthe Marketplace|n.",
    zone="Mystvale",
)

south_gate = get_or_create_room(
    "Mystvale South Gate",
    "typeclasses.rooms.Room",
    "A reinforced timber gate set into the southern wall of Mystvale. The "
    "Silver Company's guards stand watch in grey-trimmed surcoats, checking "
    "all who enter. The road beyond winds south through the mist-haunted "
    "forest and eventually leads to the Mistgate — the way back to Gateway "
    "and the wider kingdom. Travelers pause here to steel themselves before "
    "either journey.\n\n"
    "|wNorth|n into |wMystvale Square|n. |wSouth|n to the |wOld Road|n.",
    zone="Mystvale",
)

north_gate = get_or_create_room(
    "Mystvale North Gate",
    "typeclasses.rooms.Room",
    "The northern gate of Mystvale, smaller than the south but heavily "
    "guarded. Beyond lie the wild country, the road to the ruins of Tamris, "
    "and eventually the lands of the Coldhills at Harrowgate. Wolves have "
    "been heard at night, and stranger things. The sentries keep their "
    "fires high and their crossbows strung.\n\n"
    "|wSouth|n into |wMystvale Square|n. |wNorth|n toward the |wForest Road|n.",
    zone="Mystvale",
)

manor_row = get_or_create_room(
    "Manor Row",
    "typeclasses.rooms.Room",
    "A short cobbled avenue running north from the square. Stag Hall, the "
    "seat of House Laurent in the Annwyn, stands at its head — Mystvale's "
    "only noble manor. The other houses hold their own settlements further "
    "afield: Ironhaven to the east (Richter), Arcton to the west (Corveaux), "
    "Carran to the south (Bannon), and rumor of others further out. Silver "
    "Company sentries patrol the street.\n\n"
    "Gate leads to |wStag Hall|n. Back to |wMystvale Square|n.",
    zone="Mystvale",
)

# ===========================================================================
# HART HALL ZONE — Laurent seat of power
# ===========================================================================
print("\n=== HART HALL ROOMS ===")

hart_hall_gate = get_or_create_room(
    "Stag Hall — The Gate",
    "typeclasses.rooms.Room",
    "The gatehouse of Stag Hall, seat of House Laurent in the Annwyn. A "
    "pair of stag skulls crown the archway, their antlers polished to a "
    "dull shine. Laurent banners — antlered hart on deep green — hang from "
    "the walls. Guards in House Laurent's livery stand watch. The great "
    "hall lies within, through the courtyard.\n\n"
    "|wInside|n to the |wCourtyard|n. Back to |wManor Row|n.",
    zone="Mystvale",
)

hart_hall_courtyard = get_or_create_room(
    "Stag Hall Courtyard",
    "typeclasses.rooms.WeatherRoom",
    "A flagstone courtyard open to the grey Annwyn sky. A stag-fountain "
    "stands at its center, water trickling from antlered spouts into a "
    "moss-ringed basin. Training dummies line the north wall where the "
    "Laurent household guard drill daily. The Great Hall's double doors "
    "stand at the eastern side.\n\n"
    "|wEast|n into the |wGreat Hall|n. |wOut|n to the |wgate|n.",
    zone="Mystvale",
)

hart_hall_great_hall = get_or_create_room(
    "Stag Hall — The Great Hall",
    "typeclasses.rooms.Room",
    "A long hall with a vaulted beam ceiling and banners hung from the "
    "rafters. A raised dais at the far end holds the carved hart-throne "
    "where House Laurent holds court in the Annwyn. Trestle tables "
    "stretch down the hall for feast days. Tapestries depict the Laurent "
    "line from Maidencourt to the present day — and the gap left by those "
    "who have not returned. The air smells of candle wax and old wine.\n\n"
    "|wUp|n to the |wsolar|n. |wOut|n to the |wcourtyard|n.",
    zone="Mystvale",
)

hart_hall_solar = get_or_create_room(
    "Stag Hall — The Solar",
    "typeclasses.rooms.Room",
    "The private solar of Stag Hall's highest noble. A writing desk holds "
    "correspondence sealed with the Laurent hart. A narrow window looks "
    "out over Mystvale and the road to the Mists. A locked iron chest "
    "sits beside the chair. The air holds the scent of old ink and the "
    "faintest hint of lavender from some long-ago attendant.\n\n"
    "|wDown|n to the |wGreat Hall|n.",
    zone="Mystvale",
)

# ===========================================================================
# TAMRIS RUINS ZONE — ancient port, early-game exploration
# ===========================================================================
print("\n=== TAMRIS RUINS ROOMS ===")

forest_road = get_or_create_room(
    "The Forest Road",
    "typeclasses.rooms.WeatherRoom",
    "A narrow track winds north from Mystvale through the ancient forest. "
    "The trees grow close and tall, their trunks wrapped in grey moss. "
    "Somewhere a crow calls, and the answer sounds wrong — slower, deeper. "
    "The road climbs gently, and in the distance the broken towers of "
    "Tamris can be glimpsed through the canopy.\n\n"
    "|wSouth|n to |wMystvale|n. |wNorth|n to |wthe Ruins of Tamris|n.",
    zone="Tamris",
)

tamris_approach = get_or_create_room(
    "The Ruins of Tamris — Approach",
    "typeclasses.rooms.WeatherRoom",
    "Tamris was once a prosperous port, centuries before the Mists. Now "
    "only foundations remain — stone walls reclaimed by moss, streets "
    "lost beneath the forest floor. A broken arch marks what was once the "
    "town gate. Fragments of old tile catch the weak sun. The silence is "
    "louder here than the forest; even the crows do not come.\n\n"
    "|wSouth|n to the |wForest Road|n. |wInto|n the ruins. |wEast|n to "
    "the |wTamris Harbor|n. |wDown|n to the |wBarrows|n.",
    zone="Tamris",
)

tamris_ruins = get_or_create_room(
    "The Ruins of Tamris — The Old Square",
    "typeclasses.rooms.WeatherRoom",
    "The old market square of Tamris, now a field of broken stone. A "
    "weather-worn statue — once a noble, her face now eroded smooth — "
    "stands at the center, wreathed in ivy. Half-buried paving stones "
    "bear faded runes. Something has been digging among the ruins "
    "recently; fresh earth surrounds several broken crypts.\n\n"
    "Back to |wthe approach|n.",
    zone="Tamris",
)

tamris_harbor = get_or_create_room(
    "Tamris Harbor — The Broken Pier",
    "typeclasses.rooms.WeatherRoom",
    "What was once the harbor of Tamris is now a wreck of rotted pilings "
    "and black water. The tide never seems to come in. A wrecked ship lies "
    "tilted against the pier's remains, its hull pierced by coral that "
    "has no business growing this far north. Bones litter the shore — "
    "some human, some not.\n\n"
    "Back to |wthe approach|n.",
    zone="Tamris",
)

barrows_entrance = get_or_create_room(
    "The Barrows — Entrance",
    "typeclasses.rooms.Room",
    "A stone doorway set into the hillside, partly collapsed and partly "
    "dug out by someone — or something. Cold air flows from within, "
    "smelling of old dust and older decay. The carvings around the arch "
    "are Annwyn-script, older than the Kingdom itself. A broken torch "
    "lies on the ground, still faintly warm.\n\n"
    "|wUp|n to |wTamris ruins|n. Deeper passages await those who dare.",
    zone="Tamris",
)

# ===========================================================================
# THE WILDERNESS ZONE — roads and paths between settlements
# ===========================================================================
print("\n=== WILDERNESS ROOMS ===")

old_road_south = get_or_create_room(
    "The Old Road — South",
    "typeclasses.rooms.WeatherRoom",
    "The old road winds south from Mystvale through the mist-shrouded "
    "countryside. The ground is rutted with centuries of wheel-tracks. "
    "The trees lean close on either side, and patches of thin fog drift "
    "across the road even in clear weather. Every so often a wooden "
    "marker — carved with the sigil of the Mistguard — marks a league.\n\n"
    "|wNorth|n to |wMystvale|n. |wSouth|n to the |wMistgate|n. "
    "|wEast|n toward |wCarran|n. |wWest|n toward |wArcton|n.",
    zone="The Annwyn",
)

mistgate = get_or_create_room(
    "The Mistgate",
    "typeclasses.rooms.WeatherRoom",
    "The boundary of the Annwyn — a wall of rolling, impenetrable fog. "
    "The Mistguard's camp huddles against the veil, banners of the "
    "Mistwalkers snapping in a wind that blows only where the mist touches. "
    "Those who pass through go to Gateway and the wider kingdom. Those "
    "who come through arrive cold, dazed, and usually poorer than when "
    "they left. The air here tastes of metal.\n\n"
    "|wNorth|n back to the |wOld Road|n.",
    zone="The Annwyn",
)

# ===========================================================================
# IRONHAVEN ZONE — Richter holding east of Mystvale
# ===========================================================================
print("\n=== IRONHAVEN ROOMS ===")

ironhaven_square = get_or_create_room(
    "Ironhaven Square",
    "typeclasses.rooms.Room",
    "The heart of Ironhaven — House Richter's coastal bulwark, perched "
    "where the Richter claimed land far to the southwest of Mystvale, "
    "down near the sea. A cramped square dominated by the black iron bulk "
    "of the great anvil that serves as both monument and tool. Salt air "
    "mingles with forge smoke. The banners of House Richter — the iron "
    "tower on a field of grey — hang from every pole. The Hardinger Hall "
    "broods over the square from the eastern side.\n\n"
    "|wNortheast|n toward |wMystvale|n. |wEast|n to |wHardinger's Hall|n. "
    "|wSouth|n to the |wIronhaven Forge|n.",
    zone="Ironhaven",
)

ironhaven_forge = get_or_create_room(
    "Ironhaven Forge",
    "typeclasses.rooms.Room",
    "A vast open-fronted forge where the Richter smiths work day and night. "
    "Great bellows pump at the main hearth; lesser forges line the walls. "
    "The heat is oppressive. Richter smiths move in practiced silence, "
    "their leather aprons scarred by years of spark. Weapon racks and armor "
    "stands display their wares. This is the secondary crafting hub of the "
    "Annwyn, should Mystvale fall.\n\n"
    "|wNorth|n to |wIronhaven Square|n.",
    zone="Ironhaven",
)

hardinger_hall = get_or_create_room(
    "Hardinger's Hall",
    "typeclasses.rooms.Room",
    "The great hall of the Hardinger lords, senior Richter nobles in the "
    "Annwyn. A long table of black oak dominates the room, ringed by "
    "high-backed chairs. Trophies of the hunt — boar tusks, wolf skulls — "
    "line the walls. A war-harness stands on a rack beside the throne. "
    "The fire burns dim even at midday; the Richter prefer it that way.\n\n"
    "|wWest|n back to |wIronhaven Square|n.",
    zone="Ironhaven",
)

# ===========================================================================
# ARCTON ZONE — Corveaux outpost west of Mystvale
# ===========================================================================
print("\n=== ARCTON ROOMS ===")

arcton_camp = get_or_create_room(
    "Arcton — The Falconer Keep",
    "typeclasses.rooms.WeatherRoom",
    "Far to the east of Mystvale, near the inland sea, stands Arcton — a "
    "fortified Corveaux keep growing into a proper walled settlement. "
    "Stonework rises above palisades as masons work. The banners of House "
    "Corveaux — the grey falcon on sky blue — fly from the keep's towers. "
    "Lady Ella Falconer holds court within, guarded by knights of the "
    "Falconer order.\n\n"
    "|wWest|n toward |wMystvale|n. |wInside|n to |wLady Ella's Solar|n.",
    zone="Arcton",
)

arcton_pavilion = get_or_create_room(
    "Lady Ella's Solar",
    "typeclasses.rooms.Room",
    "A stone-walled solar atop the Falconer keep, hung with tapestries and "
    "lit by narrow arrow-slit windows overlooking the eastern sea. Maps of "
    "the Annwyn are spread across a central table, marked with Corveaux "
    "strategy. Lady Ella Falconer — austere, sharp-eyed — holds council "
    "here with her captains. A perch near the door holds her hunting falcon.\n\n"
    "|wOut|n to |wArcton|n.",
    zone="Arcton",
)

# ===========================================================================
# CARRAN — Bannon village (Event 1 state: still functioning)
# ===========================================================================
print("\n=== CARRAN ROOMS ===")

carran_square = get_or_create_room(
    "Carran — The Village Square",
    "typeclasses.rooms.WeatherRoom",
    "Carran is House Laurent's primary town in the Annwyn, founded shortly "
    "after the First Expedition. Timber houses with thatched roofs ring a "
    "packed-dirt square. The banners of House Laurent — the antlered hart "
    "on deep green — fly alongside the colors of the Bannon garrison "
    "that keeps watch here for the Crown. A training yard echoes with the "
    "clatter of wood against wood, where Arch Magistrat Symon Bannon drills "
    "his knights.\n\n"
    "|wNortheast|n toward |wMystvale|n. |wEast|n to the |wBannon Barracks|n.",
    zone="Carran",
)

bannon_barracks = get_or_create_room(
    "The Bannon Barracks",
    "typeclasses.rooms.Room",
    "A long low building of timber and stone, home to the Bannon garrison "
    "led by Arch Magistrat Symon Bannon. Though Carran is Laurent territory, "
    "King Giles II sent the Bannons along to ensure the Laurents serve the "
    "interests of the throne — and they have made themselves at home here. "
    "The walls are lined with racks of weapons and training dummies. "
    "Magistrat Bannon holds war councils at the far end.\n\n"
    "|wWest|n back to |wCarran Square|n.",
    zone="Carran",
)

# ===========================================================================
# HARROWGATE — Hale/Coldhill settlement, further north
# ===========================================================================
print("\n=== HARROWGATE ROOMS ===")

harrowgate = get_or_create_room(
    "Harrowgate — The Hall of Bears",
    "typeclasses.rooms.WeatherRoom",
    "Several days' journey north of the former Laurent lands stands "
    "Harrowgate, the Hale settlement of Lady Thora Coldhill. A longhouse "
    "of dark pine and iron bands dominates the clearing, hung with the "
    "hides of Great Bears. The Get of Ursin — berserkers sworn to the "
    "Coldhills — keep a fire burning day and night at the Hall's entrance. "
    "The air is colder here than elsewhere, and the birds fall silent when "
    "the Get pass.\n\n"
    "|wSouth|n toward the |wForest Road|n (many days' journey).",
    zone="Harrowgate",
)

# ===========================================================================
# GOLDLEAF — Innis settlement (hidden / unverified location)
# ===========================================================================
print("\n=== GOLDLEAF ROOMS ===")

goldleaf = get_or_create_room(
    "Goldleaf — Innis Encampment",
    "typeclasses.rooms.WeatherRoom",
    "A tidy encampment hidden deep in the forested hills. Gold-edged "
    "banners of House Innis hang from the trees. The Innis keep to "
    "themselves, their intentions obscure even to the other houses. "
    "Scouts in leaf-green cloaks patrol the perimeter. Rumor places "
    "Goldleaf here, but few outside the Innis retinue can find it "
    "without being led.",
    zone="Goldleaf",
)

# ===========================================================================
# MOONFALL — Aragon settlement (hidden / unverified location)
# ===========================================================================
print("\n=== MOONFALL ROOMS ===")

moonfall = get_or_create_room(
    "Moonfall — Aragon Outpost",
    "typeclasses.rooms.WeatherRoom",
    "An austere stone outpost on a cliff edge, surrounded by old standing "
    "stones worn smooth by wind and time. Aragon banners — the crescent "
    "moon on deep blue — snap in the constant gale. The Aragonese here "
    "are quiet, watchful, and give no indication of their purpose. Many "
    "whisper that they are the hidden hand behind the Crows and the Oban "
    "incursions. Moonfall's location is one of the Annwyn's better-kept "
    "secrets.",
    zone="Moonfall",
)

# ===========================================================================
# EXITS — connect all the new zones
# ===========================================================================
print("\n=== EXITS ===")

# Mystvale Square hub
link(mystvale_square, "tavern",    aentact,           "out",        "t",  "o")
link(mystvale_square, "market",    marketplace,        "out",        "m",  None)
link(mystvale_square, "crafters",  crafter_quarter,    "out",        None, None)
link(mystvale_square, "town hall", town_hall,          "out",        "hall", None)
link(mystvale_square, "garden",    herbalist_garden,   "out",        None, None)
link(mystvale_square, "chantry",   chantry,            "out",        None, None)
link(mystvale_square, "north",     manor_row,          "south",      "n",  "s")
link(mystvale_square, "south",     south_gate,         "north",      "s",  "n")
link(mystvale_square, "northgate", north_gate,         "south",      None, None)

# Marketplace → Black Market
link(marketplace, "alley",  black_market, "back", None, None)

# Manor row → Stag Hall
link(manor_row, "hart hall", hart_hall_gate, "out", "hart", "o")
link(hart_hall_gate, "in",   hart_hall_courtyard, "out", None, None)
link(hart_hall_courtyard, "east",  hart_hall_great_hall, "west", "e", "w")
link(hart_hall_great_hall, "up",   hart_hall_solar, "down", "u", "d")

# South gate → Old Road → Mistgate (the road back to Gateway, off-map south)
link(south_gate, "south",  old_road_south, "north", "s", "n")
link(old_road_south, "south", mistgate, "north", "s", "n")

# The Old Road is a crossroads with paths branching to other settlements
# per the canonical map:
#   - South → Carran (Laurent town)
#   - Southwest → Ironhaven (Richter, coastal)
#   - East → Arcton (Corveaux, eastern sea)
#   - Far southwest → Tamris ruins (ancient port)
link(old_road_south, "south",     carran_square, "north", None, None)
link(old_road_south, "southwest", ironhaven_square, "northeast", "sw", "ne")
link(old_road_south, "east",      arcton_camp, "west", "e", "w")

# Carran south continues to Tamris ruins (far southwestern coast)
link(carran_square, "southwest", tamris_approach, "northeast", "sw", "ne")

# Ironhaven internal
link(ironhaven_square, "east",  hardinger_hall, "west", "e", "w")
link(ironhaven_square, "south", ironhaven_forge, "north", "s", "n")
# Ironhaven west continues to Tamris coast
link(ironhaven_square, "west", tamris_approach, "east", "w", "e")

# Arcton internal
link(arcton_camp, "in", arcton_pavilion, "out", None, "o")

# Carran internal
link(carran_square, "east", bannon_barracks, "west", "e", "w")

# North gate → Forest Road → Harrowgate (far north per canonical map)
link(north_gate, "north", forest_road, "south", "n", "s")
link(forest_road, "north", harrowgate, "south", "n", "s")

# Tamris ruins interior (accessed from Carran SW or Ironhaven W)
link(tamris_approach, "in", tamris_ruins, "out", None, "o")
link(tamris_approach, "east", tamris_harbor, "west", "e", "w")
link(tamris_approach, "down", barrows_entrance, "up", "d", "u")

# ===========================================================================
# LEGACY CLEANUP — delete old placeholder rooms that don't match canon
# ===========================================================================
print("\n=== LEGACY CLEANUP ===")

# Noble-named "cabin" rooms from the old world — these were placeholders.
# The canonical settlements are Ironhaven, Arcton, Harrowgate, Carran, etc.
# Any room matching these patterns is a stale placeholder to be removed.
_LEGACY_CABIN_PATTERNS = [
    "Eastern Cabin", "Western Cabin",
    "Hale Cabin", "Hale's Cabin",
    "Zorya Cabin", "Zorya's Cabin",
    "Laurent Cabin", "Richter Cabin", "Corveaux Cabin",
    "Bannon Cabin", "Blayne Cabin", "Innis Cabin",
    "Aragon Cabin", "Rourke Cabin", "Draghean Cabin",
    # Fields were also placeholders for the new zones
    "North Field", "South Field", "East Field", "West Field",
    # "Inside Ruined Hovel" and similar
    "Inside Ruined Hovel", "Forest Clearing",
]

for room_key in _LEGACY_CABIN_PATTERNS:
    stale = ObjectDB.objects.filter(db_key=room_key).first()
    if stale:
        # Move any objects/characters inside to Mystvale Square before deletion
        for obj in list(stale.contents):
            if hasattr(obj, "destination") and obj.destination:
                # It's an exit — just delete it
                obj.delete()
            elif hasattr(obj, "has_account") and obj.has_account:
                # Character — move to safety
                obj.move_to(mystvale_square, quiet=True)
            else:
                # Generic object — move to Mystvale Marketplace
                try:
                    obj.move_to(marketplace, quiet=True)
                except Exception:
                    pass
        print(f"  DELETED : legacy room '{room_key}'")
        stale.delete()

# ===========================================================================
# MOVE CRAFTING STATIONS INTO CRAFTER'S QUARTER
# ===========================================================================
print("\n=== RELOCATING CRAFTING STATIONS ===")

# Find the existing crafting stations from Maker's Hollow
old_forge = ObjectDB.objects.filter(
    db_key="forge", db_typeclass_path="typeclasses.objects.Forge"
).first()
if old_forge:
    move_to(old_forge, crafter_quarter)
else:
    # If the old forge doesn't exist, create a new one in Mystvale
    create_obj("forge", "typeclasses.objects.Forge", crafter_quarter,
               "A squat stone forge, iron-mouthed and hungry. Coals glow deep "
               "inside. Strike the anvil to shape metal into weapons and armour.")

old_bench = ObjectDB.objects.filter(
    db_key="workbench", db_typeclass_path="typeclasses.objects.ArtificerWorkbench"
).first()
if old_bench:
    move_to(old_bench, crafter_quarter)
else:
    create_obj("workbench", "typeclasses.objects.ArtificerWorkbench", crafter_quarter,
               "A heavy oak workbench scarred by blades. Drawers hold small "
               "tools. A craftworker's table for bows, gunsmith work, and fine artifice.")

old_apoth = ObjectDB.objects.filter(
    db_key="apothecary workbench", db_typeclass_path="typeclasses.objects.ApothecaryWorkbench"
).first()
if old_apoth:
    move_to(old_apoth, crafter_quarter)
else:
    create_obj("apothecary workbench", "typeclasses.objects.ApothecaryWorkbench", crafter_quarter,
               "A stone-topped table stained every colour by spilled reagents. "
               "Glass tubes, a mortar and pestle, drying racks. Brew here.")

# ===========================================================================
# MOVE THE GENERAL MERCHANT TO THE NEW MARKETPLACE
# ===========================================================================
print("\n=== RELOCATING MERCHANTS ===")

old_merchant = ObjectDB.objects.filter(
    db_key="General Merchant", db_typeclass_path="typeclasses.objects.Merchant"
).first()
if old_merchant:
    move_to(old_merchant, marketplace)

# ===========================================================================
# REDIRECT THE CHARGEN ROOM TO MYSTVALE SOUTH GATE
# ===========================================================================
print("\n=== CHARGEN ROOM EXIT ===")

chargen_room = ObjectDB.objects.filter(
    db_typeclass_path="typeclasses.rooms.ChargenRoom"
).first()
if chargen_room:
    # Remove any existing exits from the chargen room
    for ex in chargen_room.contents:
        if hasattr(ex, "destination") and ex.destination:
            print(f"  REMOVE  : old exit '{ex.key}' from ChargenRoom")
            ex.delete()
    # New exit: chargen → Mystvale South Gate
    if not ObjectDB.objects.filter(
        db_key="in character", db_location=chargen_room.pk
    ).exists():
        ex = _create.create_object(
            "evennia.objects.objects.DefaultExit",
            key="in character",
            location=chargen_room,
            destination=south_gate,
        )
        ex.aliases.add("ic")
        ex.aliases.add("mystvale")
        print(f"  CREATED : ChargenRoom → Mystvale South Gate exit")

# Also ensure limbo (#2) points at Mystvale South Gate
limbo = ObjectDB.objects.filter(id=2).first()
if limbo:
    limbo.db.desc = (
        "A featureless void between worlds. The Mistgate lies to the |wsouth|n, "
        "and beyond it, the road to Mystvale."
    )
    for ex in limbo.contents:
        if hasattr(ex, "destination") and ex.destination:
            ex.delete()
    if not ObjectDB.objects.filter(db_key="south", db_location=limbo.pk).exists():
        _create.create_object(
            "evennia.objects.objects.DefaultExit",
            key="south", location=limbo, destination=south_gate,
        )
        print("  CREATED : Limbo → Mystvale South Gate")

print("\n=== MYSTVALE POPULATE COMPLETE ===")
