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

# Track the PKs of every room we build or preserve in this run. The final
# cleanup stage uses this as a whitelist: any room-typeclass object NOT in
# this set (and not Limbo / ChargenRoom) is considered stale and purged.
KEPT_PKS = set()


def get_or_create_room(key, typeclass_path, desc, zone=None):
    existing = ObjectDB.objects.filter(
        db_key=key, db_typeclass_path=typeclass_path
    ).first()
    if existing:
        print(f"  EXISTS  : {key}")
        if zone:
            existing.attributes.add("zone", zone)
        existing.db.desc = desc  # refresh description on re-run
        KEPT_PKS.add(existing.pk)
        return existing
    room = _create.create_object(typeclass_path, key=key)
    room.db.desc = desc
    if zone:
        room.attributes.add("zone", zone)
    room.save()
    KEPT_PKS.add(room.pk)
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
# GATEWAY ZONE — the Arnesse-side border village on the edge of the Mists
# ---------------------------------------------------------------------------
# Per the Event 1 Prologue ("Many Meetings", 7th Moon Cycle 763 A.S.):
#   Gateway is a ramshackle village raised on the borders of the Annwyn to
#   handle the flood of expeditions, nobles, Cirque, and commonfolk seeking
#   passage through the mists. It is a "stinking, festering boil of raw
#   sewage, open-air markets, and decrepit buildings" — a haven for
#   criminals, grifters, and price-gougers. It is nominally administered
#   by the Mistguard (House Richter + House Bannon coalition) and is the
#   overland staging point for the Mistwalkers who guide passage.
# ===========================================================================
print("\n=== GATEWAY ROOMS ===")

gateway_tents = get_or_create_room(
    "Gateway — The Tent City",
    "typeclasses.rooms.WeatherRoom",
    "A sprawling, mud-churned tent city pressed against the outer palisade "
    "of Gateway. Weather-beaten canvas, driftwood lean-tos, and rope lines "
    "strung with laundry make an ugly warren underfoot. Children with "
    "hollow cheeks fetch water from a common trough. Latrine smoke and "
    "cookfires braid into the damp coastal air. This is where most "
    "newcomers to Gateway end up — those who cannot afford Gateway's "
    "inflated lodgings, or who are quietly waiting for a Mistwalker to "
    "agree to take them.\n\n"
    "|wNorth|n into |wGateway Square|n. Watchmen of the Mistguard walk "
    "the palisade above.",
    zone="Gateway",
)

gateway_square = get_or_create_room(
    "Gateway — The Open Square",
    "typeclasses.rooms.Room",
    "The true heart of Gateway — if the word 'heart' can apply to such a "
    "place. A broad open square of trampled mud and splintered planks, "
    "ringed by the wooden bulk of Gateway's buildings. Open-air stalls "
    "peddle everything from spoiled bread to Annwyn 'relics' of highly "
    "doubtful origin. Fights start at one end and finish at the other. "
    "The banners of the Mistguard — House Richter's iron tower quartered "
    "with House Bannon's black drake — hang from a central post, water-"
    "stained and grubby. Coin changes hands constantly, and only the "
    "unwary let theirs go willingly.\n\n"
    "|wSouth|n to the |wtent city|n. |wEast|n to the |wBroken Oar|n. "
    "|wWest|n to the |wpalisade gate|n. |wNorth|n to the |wMistwalker's Tent|n.",
    zone="Gateway",
)

gateway_tavern = get_or_create_room(
    "The Broken Oar",
    "typeclasses.rooms.Room",
    "A low-ceilinged tavern leaning hard against its neighbors, walls stained "
    "black from lamp-smoke. The Broken Oar is Gateway's only lodging worth "
    "the name — which is to say its mattresses have merely most of their "
    "lice. The bar is made from the prow of a wrecked mistwalker ship, the "
    "name 'Albatross Doom' still faintly visible under the varnish. Sailors, "
    "grifters, sellswords, and an occasional pale-eyed Mistwalker share the "
    "benches. This is where contracts are whispered and passage is bought.\n\n"
    "Back to the |wSquare|n.",
    zone="Gateway",
)

mistguard_palisade = get_or_create_room(
    "The Palisade Gate",
    "typeclasses.rooms.WeatherRoom",
    "A heavy timber gate set into the western wall of Gateway — the Mistguard "
    "checkpoint between the village and the wall of fog beyond. Sergeant-at-"
    "arms of House Richter stand watch beside halberdiers of House Bannon, "
    "their banners hanging heavy with damp. Every traveler seeking the Mists "
    "must show cause; those without a Writ of Passage are turned back or "
    "pressed to the work of the camp. A brazier burns even at noon, its "
    "smoke lost in the mist-haze beyond the gate.\n\n"
    "|wEast|n back to |wGateway Square|n. |wWest|n, the wall of mist rolls "
    "like an ocean against the sky — cross only with a guide, and a Writ.",
    zone="Gateway",
)

mistwalker_tent = get_or_create_room(
    "The Mistwalker's Tent",
    "typeclasses.rooms.Room",
    "A canvas pavilion pitched just inside the palisade, its walls painted "
    "with sigils in a script no scholar has yet named. Inside, incense "
    "smolders in a copper bowl and the light seems always to be just after "
    "sunset, no matter the hour. The Mistwalker who keeps this tent sits "
    "behind a writing table of pale wood, stamp and ink at the ready. Here "
    "passage is negotiated, silver counted, and the Writ of Passage inked "
    "with a mark that burns faintly blue when held to flame.\n\n"
    "|wSouth|n to |wGateway Square|n. |wWest|n, through the flap, to the "
    "|wMistwall|n itself.",
    zone="Gateway",
)

mistwall = get_or_create_room(
    "The Mistwall",
    "typeclasses.rooms.WeatherRoom",
    "The edge of the known world. A wall of roiling, impenetrable fog rises "
    "before you, taller than any tower, shifting with slow and dreadful "
    "purpose. The earth is salt-scoured dead soil; nothing grows in the "
    "Mistwall's shadow. Sound is wrong here — footsteps fall muted, voices "
    "carry too far or not at all. A Mistwalker stands at the threshold, "
    "waiting. Cross, and the Annwyn takes you. |yOnce the Annwyn has you, "
    "only she can let you go.|n\n\n"
    "|wEast|n, back through the palisade. |wThrough the mists|n — the "
    "Mistgate lies on the other side.",
    zone="Gateway",
)

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

# Gateway zone — Arnesse side of the Mists
link(gateway_tents,      "north", gateway_square,     "south",       "n",  "s")
link(gateway_square,     "east",  gateway_tavern,     "out",         "e",  "o")
link(gateway_square,     "west",  mistguard_palisade, "east",        "w",  "e")
link(gateway_square,     "north", mistwalker_tent,    "south",       "n",  "s")
link(mistwalker_tent,    "west",  mistwall,           "east",        "w",  "e")
# The one-way crossing: Mistwall (Gateway) → Mistgate (Annwyn).
# Canon: "once the Annwyn has you, only she can let you go" — so the
# return path is intentionally not a simple walk.
#
# Traversal is gated on the character's approval_status attribute. Pending
# or rejected bearers are blocked by Soap with a themed message. Admins
# (Builder+) can always cross.
_mists_exit = ObjectDB.objects.filter(
    db_key="through the mists", db_location=mistwall.pk
).first()
if not _mists_exit:
    _mists_exit = _create.create_object(
        "evennia.objects.objects.DefaultExit",
        key="through the mists", location=mistwall, destination=mistgate,
    )
    _mists_exit.aliases.add("mists")
    _mists_exit.aliases.add("cross")
    print("  CREATED : Mistwall → Mistgate (one-way crossing)")

# Always refresh the lock + err_traverse so re-runs keep the gate current.
_mists_exit.locks.add(
    "traverse:attr(approval_status, approved) or perm(Builder)"
)
_mists_exit.db.err_traverse = (
    "|ySoap raises a black-gloved hand, barring your way. The brim of the "
    "tall hat throws their face into shadow.|n\n"
    "|y\"Your Writ has not yet been lit, bearer. The Compact has not yet "
    "judged your passage. Return to Crane when the mark burns blue — or "
    "wait here. The mists are patient.\"|n"
)
print("  GATED   : Mistwall → Mistgate (requires approved Writ)")

# ===========================================================================
# LEGACY CLEANUP — whitelist purge.
# Every room typeclass object that ISN'T one we just created/kept (tracked
# in KEPT_PKS), AND isn't Limbo (#2) or a ChargenRoom, is considered stale
# pre-Mystvale-reboot content and gets deleted. Characters and objects
# inside get salvaged to safe locations before the delete.
# ===========================================================================
print("\n=== LEGACY CLEANUP (whitelist purge) ===")

# Always preserve Limbo (#2) and any ChargenRoom instances no matter what.
_limbo = ObjectDB.objects.filter(id=2).first()
if _limbo:
    KEPT_PKS.add(_limbo.pk)
for _cr in ObjectDB.objects.filter(db_typeclass_path="typeclasses.rooms.ChargenRoom"):
    KEPT_PKS.add(_cr.pk)

# All room-like typeclasses in the project. We look for typeclass paths
# starting with "typeclasses.rooms" to catch Room, WeatherRoom, MarketRoom,
# ChargenRoom — the full family.
room_qs = ObjectDB.objects.filter(
    db_typeclass_path__startswith="typeclasses.rooms"
)

purged = 0
preserved = 0
for room in room_qs:
    if room.pk in KEPT_PKS:
        preserved += 1
        continue
    # Salvage contents before deletion
    for obj in list(room.contents):
        try:
            if hasattr(obj, "destination") and obj.destination:
                # Exit — stale once its source is gone
                obj.delete()
                continue
            # Account-puppeted character → move to Gateway Tent City
            if hasattr(obj, "has_account") and obj.has_account:
                obj.move_to(gateway_tents, quiet=True)
                continue
            # Generic object — send to Mystvale Marketplace for later sort
            obj.move_to(marketplace, quiet=True)
        except Exception as exc:
            print(f"    SALVAGE FAIL: {getattr(obj, 'key', '?')}: {exc}")
    # Also delete any exits in other rooms that pointed at this one,
    # so we don't leave dangling exits.
    for ex in ObjectDB.objects.filter(db_destination=room.pk):
        try:
            print(f"    DANGLING : {ex.key} in {ex.location.key if ex.location else '?'}")
            ex.delete()
        except Exception:
            pass
    print(f"  PURGED  : '{room.key}' (was {room.db_typeclass_path})")
    room.delete()
    purged += 1

print(f"\n  Cleanup: preserved={preserved}, purged={purged}")

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


# ===========================================================================
# GATEWAY AI-DRIVEN NPCs — dialogue practice for new players
# Each NPC carries an ai_personality / ai_knowledge / ai_quest_hooks block.
# Players interact via: ask <npc> <message>   /  farewell <npc>
# The LLM backend is configured via NPC_LLM_* env vars (see world/ai_npc.py).
# Names and personalities drawn from canonical faction packets + the Event 8
# Writ of Safe Conduct prop (Crane as registrar, Soap as guide, etc.).
# ===========================================================================
print("\n=== GATEWAY NPCs ===")


def get_or_create_npc(key, location, desc, personality, knowledge,
                      quest_hooks, scope="gateway"):
    """Create or refresh an AI-driven NPC at a fixed location.

    `scope` controls how much lore the LLM sees in this NPC's system
    prompt. "gateway" = Arnesse-side, rumor-level Annwyn knowledge only.
    "annwyn" = firsthand Annwyn interior knowledge. See world/ai_lore.py.
    """
    existing = ObjectDB.objects.filter(
        db_key=key, db_location=location.pk,
        db_typeclass_path="typeclasses.npc.Npc",
    ).first()
    if existing:
        npc = existing
        print(f"  EXISTS  : {key} (in {location.key})")
    else:
        npc = _create.create_object("typeclasses.npc.Npc", key=key, location=location)
        print(f"  CREATED : {key} → {location.key}")
    # Always refresh description + AI config so edits to this script
    # propagate to existing NPCs on re-run.
    npc.db.desc = desc
    npc.db.is_npc = True
    npc.db.is_aggressive = False       # dialogue NPCs never attack
    npc.db.peaceful = True
    npc.attributes.add("ai_personality", personality)
    npc.attributes.add("ai_knowledge", knowledge)
    npc.attributes.add("ai_quest_hooks", quest_hooks)
    npc.attributes.add("ai_scope", scope)
    # Block picking them up; they are fixtures.
    npc.locks.add("get:false();puppet:false()")
    return npc


# --- Sergeant Hollet Kross — Mistguard NCO at the Palisade Gate --------
get_or_create_npc(
    key="Sergeant Hollet Kross",
    location=mistguard_palisade,
    desc=(
        "A weather-beaten Mistguard sergeant in iron-grey Richter livery, "
        "the black drake armband of House Bannon sewn on his shoulder to "
        "mark the joint command. Salt-and-pepper beard, scar across one "
        "brow, halberd planted beside him like a third leg. He has seen "
        "everything twice and is not impressed the second time."
    ),
    personality=(
        "Sergeant Hollet Kross, a forty-something Mistguard NCO. Richter-born, "
        "served fifteen years on the palisade and before that in the Dusklands "
        "wars. Dry, pragmatic, sardonic — the kind of humor that keeps men "
        "alive at three in the morning. Gruff but fundamentally fair; hates "
        "liars and grifters on sight. Speaks in clipped, declarative sentences. "
        "Addresses strangers as 'you' or 'bearer'; addresses a proven newcomer "
        "as 'lad' or 'lass'. Never wastes a word."
    ),
    knowledge=(
        "- The Mistguard is a coalition of Houses Richter and Bannon, commanded "
        "here jointly. Richter contributes iron; Bannon contributes drilling.\n"
        "- No one crosses the mists without a Writ of Safe Conduct.\n"
        "- The Writ is registered at the Mistwalker Compact's tent — ask for "
        "Crane, the registrar. Bring silver.\n"
        "- Your assigned guide will be noted on the Writ. Do not approach any "
        "other Mistwalker; there have been ugly disputes.\n"
        "- Without a Writ, you can be pressed to work the tent city or turned "
        "out. Some choose the Last Walk instead; he does not recommend it.\n"
        "- Gateway is stinking, lawless, and full of grifters. Keep your purse "
        "close and don't buy 'Annwyn relics' off anyone who isn't a Mistwalker."
    ),
    quest_hooks=[
        "If the player seems earnest, he can vouch for them at the Crossing Office.",
        "If the player admits to a noble house, he asks which; he has opinions.",
        "Has heard a third Writ was issued to someone matching the player's "
        "description — might be a case of mistaken identity, might not.",
    ],
)

# --- Crane — the Registrar of the Gateway Crossing Office --------------
get_or_create_npc(
    key="Crane",
    location=mistwalker_tent,
    desc=(
        "An ageless figure seated behind a pale-wood writing table, ledger "
        "open, a stick of blue-black sealing wax at their elbow. Tall and "
        "spare, long hands, eyes the color of wet slate. Addresses everyone "
        "who enters as 'bearer.' Incense curls from a copper bowl and never "
        "seems to run out."
    ),
    personality=(
        "Crane, Registrar of the Gateway Crossing Office of the Mistwalker "
        "Compact. Soft-spoken, precise, meticulous. Bureaucratic in the way "
        "that only someone who has seen centuries can be. Calls every visitor "
        "'bearer' even before the Writ is stamped. Never laughs; occasionally "
        "smiles. Speaks with the unhurried cadence of someone for whom time "
        "is a polite suggestion. Obvious that something is deeply wrong about "
        "them, though no one can say exactly what."
    ),
    knowledge=(
        "- The terms of the Writ of Safe Conduct, exactly:\n"
        "  - Passage granted for ONE crossing unless otherwise specified.\n"
        "  - Bearer is assigned to a specific guide by name and mark.\n"
        "  - Assignment is binding. Approach no other guide.\n"
        "  - In the mists, the guide's word is law.\n"
        "  - Those who cannot abide the terms are invited to surrender the "
        "writ before the torch is lit.\n"
        "  - The Compact makes no warranty of safe arrival.\n"
        "  - Separation from the guide = lost at your own peril. Retrieval "
        "is billed separately.\n"
        "  - Non-transferable. Expires on arrival or confirmed death.\n"
        "- The guide currently working the Mistwall is Soap, identifiable "
        "by a tall, buckled hat.\n"
        "- Registration requires: the bearer's name, a statement of purpose, "
        "and a fee in silver (which Crane never names a price for — the bearer "
        "is expected to know what the Compact is worth to them).\n"
        "- Crane does not answer questions about what Crane is."
    ),
    quest_hooks=[
        "Will register a Writ for any bearer who agrees to the terms aloud.",
        "If pressed about the Mists themselves, deflects with Compact paperwork.",
        "If the player has a specific reason to cross — a lost kin, a debt, "
        "a calling — Crane notes it in the ledger with quiet approval.",
    ],
)

# --- Soap — the Mistwalker guide at the Mistwall ----------------------
get_or_create_npc(
    key="Soap",
    location=mistwall,
    desc=(
        "A tall figure in a travel-stained greatcoat, a battered black hat "
        "with a wide brim and a tarnished buckle. Features are hard to place "
        "— the face keeps catching in the mist's shifting light. A rope of "
        "knotted silver cord hangs at their belt. They stand very still, as "
        "if the mist has agreed to go around them."
    ),
    personality=(
        "Soap, a Mistwalker of the Compact. Gender ambiguous; age impossible "
        "to read. Speaks slowly, chooses words deliberately. Rare smile that "
        "doesn't reach the eyes. Not cold, just... distant. Tests the bearer "
        "before lighting the torch: needs to be sure they will obey. Has crossed "
        "the mists so many times that the mists have begun to cross into them."
    ),
    knowledge=(
        "- The mists are not weather. They are a place. The place has opinions.\n"
        "- The rules of a crossing: walk in my shadow, do not speak to what "
        "speaks to you, do not turn around, do not drop the cord.\n"
        "- If a bearer breaks the rules, the mists choose what happens. Soap "
        "does not interfere with the mists' choices.\n"
        "- Before the torch is lit, Soap asks the bearer one question: 'Why "
        "are you crossing?' Lies are not punished by Soap — they are punished "
        "by the mists.\n"
        "- On the other side: the Mistgate at the edge of the Annwyn, then "
        "the road north to Mystvale.\n"
        "- Soap has lost four bearers in thirty-some crossings. They do not "
        "consider this a bad record."
    ),
    quest_hooks=[
        "Will cross with any bearer who shows a valid Writ and answers the "
        "question of purpose.",
        "If the bearer expresses real fear, Soap gives them a knotted silver "
        "cord to hold during the crossing. 'Do not drop it.'",
        "Occasionally needs a favor done on the Annwyn side — a message "
        "delivered, a token recovered — in exchange for a return crossing.",
    ],
)

# --- Pelham Faye — innkeeper at The Broken Oar ------------------------
get_or_create_npc(
    key="Pelham Faye",
    location=gateway_tavern,
    desc=(
        "A weathered man in his sixties behind the Oar's driftwood bar, "
        "white hair tied back in a sailor's queue, salt-burned hands never "
        "still. A knot of rope is tattooed on the back of each forearm. He "
        "pours strong, listens better than he speaks, and can tell a grifter "
        "from a decent soul at forty paces."
    ),
    personality=(
        "Pelham Faye, formerly the bosun of the Mistwalker ship Albatross Doom "
        "— the prow of which he later built his bar from. Sixty-three, lost "
        "his ship, his left-hand fingers, and his wife all in the same bad "
        "year. Warm under the gruff, once you earn it. Loves a good story "
        "more than a paying customer. Remembers every face he's poured for. "
        "Calls everyone 'friend' until they prove otherwise, and 'you' when "
        "they do."
    ),
    knowledge=(
        "- Everything said in Gateway in the last ten years; most of it wrong "
        "by the time it reached the Oar, but Pelham knows which parts to trust.\n"
        "- Current rumors: a Richter captain at the palisade has been taking "
        "bribes; a Cirque wagon disappeared on the Dread Run last week; "
        "someone's been paying Mistwalkers to carry specific letters only.\n"
        "- Sea-lore: the Silent Shores, Skeleton Shoals, Crow's Nest, Arkham "
        "Island. The privateers out of Ludavar. The wreck of his own Albatross.\n"
        "- Mistwalkers he knows: Crane (never drinks), Soap (drinks well water), "
        "Greyveil (doesn't come in anymore).\n"
        "- A back room is available for quiet conversations — silver opens "
        "the door."
    ),
    quest_hooks=[
        "Will trade rumors for a round of drinks shared with the player.",
        "If the player seems hungry/broke, will slide them a bowl of stew "
        "and a crust 'on the Oar' in exchange for a story.",
        "Is looking for someone trustworthy to carry a small sealed packet "
        "to a friend in Mystvale; silver on delivery.",
    ],
)

# --- Branwen Innish — Cirque scout in the Open Square -----------------
get_or_create_npc(
    key="Branwen Innish",
    location=gateway_square,
    desc=(
        "A wiry young woman perched on the edge of a barrel, Cirque colors "
        "wrapped at her wrist, a Pooka charm on a silver chain at her "
        "throat. Dagger-scars on both forearms. A smile that is doing more "
        "work than it lets on."
    ),
    personality=(
        "Branwen Innish, mid-twenties, Cirque-affiliated scout with Innis "
        "ties back in the Sovereignlands. Irish lilt, quick tongue, flirts "
        "freely but professionally. Mercenary and honest about it — you pay, "
        "she delivers. Dangerous if crossed. Loyal to the Cirque first, to "
        "coin second, and to anyone who has bought her a drink third. Reads "
        "people fast and rarely wrong."
    ),
    knowledge=(
        "- The Cirque runs caravans between Gateway and the Dusklands via "
        "the Dread Run; bodyguards, muleteers, and crafters always wanted. "
        "The Nagas (Cirque sellsword company) handle security.\n"
        "- Rates: one silver/day for guard work, two for someone who can "
        "fight; bonus if the caravan draws blood.\n"
        "- A letter can be carried anywhere the Cirque reaches for two "
        "silvers and a promise of discretion.\n"
        "- House Innis keeps a quiet presence in Gateway — mostly scouts, "
        "a few healers. She does not discuss their business with strangers.\n"
        "- The Underwriter — a Cirque figure of note — has a standing offer "
        "for unusual contracts; ask Pelham where to leave a letter."
    ),
    quest_hooks=[
        "Hiring: caravan guard, crafters, quiet couriers.",
        "Will carry a letter anywhere the Cirque goes, for a price.",
        "If the player is Innis-affiliated or Cirque-adjacent, offers a "
        "quiet introduction to 'someone who might want to meet you.'",
    ],
)

# --- Old Mae — widow in the Tent City ---------------------------------
get_or_create_npc(
    key="Old Mae",
    location=gateway_tents,
    desc=(
        "A Midlander woman, maybe forty though she looks older, hunched in "
        "a patched grey cloak against the damp. Two small shapes bundled "
        "beneath a driftwood lean-to behind her — her children, asleep. "
        "Her eyes are hollow but steady. She holds a tin cup without "
        "quite asking."
    ),
    personality=(
        "Old Mae (just 'Mae' to those she trusts). Widow of a Midlander "
        "farmer killed by bandits in the clashes at the Dusklands border. "
        "Forty-two, looks fifty. Two small children asleep beside her. "
        "Tries to stay gentle — failing would break her. Tears come easily "
        "if pressed, but she does not beg. Proud in the exhausted way of "
        "people who have nothing left but pride."
    ),
    knowledge=(
        "- Her sister Ilsa crossed to Mystvale four moons ago and sent one "
        "letter before going silent. Mae is trying to get across to find her.\n"
        "- The price of a Writ is beyond her. The Mistguard turned her away "
        "twice — once gently, once not. She will not ask a third time.\n"
        "- She has heard there are ways for someone without coin: the Last "
        "Walk (which is death); throwing oneself on a Mistwalker's charity "
        "(which is rumored); or finding a patron with a Writ to spare.\n"
        "- She has been in Gateway eleven days. The food is running out.\n"
        "- The children's names are Tillie (four) and Cole (two). Do not "
        "wake them. They cry with hunger otherwise."
    ),
    quest_hooks=[
        "Would be profoundly grateful if someone sponsored a Writ for her.",
        "Will accept — with dignity — food, a coin for bread, or a warm "
        "cloak for the children.",
        "Asks if anyone crossing might carry a letter to her sister Ilsa in "
        "Mystvale, in case she herself doesn't make it across.",
    ],
)

# Hand Old Mae a letter to carry. This is a tiny prop so the hook works:
_mae = ObjectDB.objects.filter(db_key="Old Mae").first()
if _mae:
    letter_key = "worn letter to ilsa"
    existing_letter = ObjectDB.objects.filter(
        db_key=letter_key, db_location=_mae.pk
    ).first()
    if not existing_letter:
        letter = _create.create_object(
            "typeclasses.objects.Object", key=letter_key, location=_mae,
        )
        letter.db.desc = (
            "A small folded sheet of coarse paper, sealed with a smear of "
            "tallow. Addressed in shaky ink:\n\n"
            "   |yTo Ilsa of the Crookhouse, Mystvale. From your sister Mae.|n\n\n"
            "Paper rustles inside. It is marked with the faint print of a "
            "child's thumb."
        )
        letter.locks.add("get:true();drop:true()")
        print(f"  PROP    : '{letter_key}' → Old Mae")


# ===========================================================================
# WRIT OF SAFE CONDUCT — demo prop for Crane's tent
# A single canonical example Writ is placed on Crane's writing table so
# players can `look writ` to read the document before one is issued to them.
# ===========================================================================
print("\n=== WRIT OF SAFE CONDUCT (demo) ===")

writ_key = "writ of safe conduct"
existing_writ = ObjectDB.objects.filter(
    db_key=writ_key, db_location=mistwalker_tent.pk,
    db_typeclass_path="typeclasses.objects.WritOfSafeConduct",
).first()
if not existing_writ:
    writ = _create.create_object(
        "typeclasses.objects.WritOfSafeConduct",
        key=writ_key, location=mistwalker_tent,
    )
    writ.aliases.add("writ")
    writ.db.bearer = ""  # blank so players see "________________"
    writ.locks.add("get:perm(Builder)")  # demo copy — admins only can pocket it
    print(f"  CREATED : {writ_key} → Crane's Tent (demo)")


print("\n=== MYSTVALE POPULATE COMPLETE ===")
