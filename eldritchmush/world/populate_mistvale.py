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
# NPC RENAME MIGRATION — clean up NPCs whose names matched active or
# archived PCs in the background log. These keys were created by an
# earlier run of the populate script; the new NPC creation below uses
# the new keys, so without this cleanup we'd end up with BOTH the old
# and new NPCs sitting in the same room.
# ===========================================================================
print("\n=== NPC RENAME MIGRATION ===")
_NPC_RENAMES = {
    "Fergus of Lydiard": "Rhys of the Thornwood",
    "Juniper the Scribe": "Lissa the Scribe",
    "Songbird": "Old Threnody",
    "Eli the Docker": "Obed the Docker",
}
for old_key, new_key in _NPC_RENAMES.items():
    for stale in ObjectDB.objects.filter(
        db_key=old_key, db_typeclass_path__startswith="typeclasses.npc"
    ):
        # If a same-location NPC with the new key already exists (from a
        # later partial run), just delete the stale one to avoid a
        # duplicate-key conflict and keep the newer attributes.
        existing_new = ObjectDB.objects.filter(
            db_key=new_key, db_location=stale.db_location_id,
            db_typeclass_path__startswith="typeclasses.npc",
        ).first()
        if existing_new:
            print(f"  DELETE  : stale '{old_key}' (newer '{new_key}' exists at same location)")
            stale.delete()
        else:
            print(f"  RENAME  : '{old_key}' → '{new_key}'")
            stale.db_key = new_key
            stale.save()


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
    "strung with laundry make an ugly warren underfoot. Latrine smoke and "
    "cookfires braid into the damp coastal air.\n\n"
    "Life here does not pause. A widow stirs a thin pot of lentils over "
    "coals, children with hollow cheeks queue at the common trough, an old "
    "Tarkathi pilgrim winds his prayer beads in the lee of a lean-to. Two "
    "Richter porters warm their hands at a brazier without speaking. "
    "Someone is coughing, somewhere, and has been for days. Watchmen of "
    "the Mistguard walk the palisade above, bored and cold.\n\n"
    "|wNorth|n into |wGateway Square|n.",
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
    "stained and grubby.\n\n"
    "At any given hour the Square runs thick with traffic: hawkers calling "
    "wares, a Cirque fortune-teller murmuring at a folding table, two "
    "Aurorym Kindling novices handing out bread under the eye of their "
    "Auron, a pair of Bannon men-at-arms walking a slow circuit. A "
    "knife-grinder works his treadle near the north end. Coin changes "
    "hands constantly, and only the unwary let theirs go willingly.\n\n"
    "Twice or thrice a moon-cycle, the crowd parts for a Last Walk column: "
    "shackled prisoners — most from the Dusklander–Northern Marches border "
    "war — driven westward toward the palisade by Mistguard halberdiers. "
    "The square goes quiet when they pass. Some pilgrims throw bread; some "
    "townsfolk look away. The Aurorym does not look away.\n\n"
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
    "name 'Albatross Doom' still faintly visible under the varnish.\n\n"
    "The room is never quiet. Fishermen from the Breakwater crews argue "
    "over dice by the hearth; a brace of travel-worn pilgrims huddle over "
    "watered wine in the corner; a drunk Richter corporal has been asleep "
    "on the same bench for the better part of the afternoon. Somewhere "
    "under the smoke, someone is singing in an old Cirque tongue, quietly, "
    "for themselves. A cat walks across the bar as if it owns it.\n\n"
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
    "On Last Walk days the column gathers here before the gate is opened: "
    "shackled prisoners in mismatched rags, mostly war captives from the "
    "Dusklander border conflict, escorted by Mistguard halberdiers with "
    "drawn blades. There are no guides for them. They are walked to the "
    "Mistwall, the gate is shut behind them, and what becomes of them on "
    "the far side is rumor only.\n\n"
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

chirurgeons_guild = get_or_create_room(
    "The Apotheca Chirurgery",
    "typeclasses.rooms.Room",
    "A squat stone building near the Marketplace, its doorframe carved "
    "with the twin-serpent caduceus of the |wApotheca|n — the scholarly "
    "order dedicated to medicine, alchemy, and the preservation of "
    "knowledge. Inside: scrubbed tables, hanging herb-bundles, jars of "
    "salve, bandage rolls, and the sharp smell of alcohol and comfrey. "
    "A fire burns low under a copper still, and a shelf of worn "
    "medical texts lines the back wall. This is where Mystvale's wounded "
    "come to be mended — soldiers, labourers, and adventurers alike. "
    "The Magister Chirurgeon accepts silver, not thanks.\n\n"
    "Type |wtend|n to receive healing (5 silver).\n\n"
    "Back to |wMystvale Square|n.",
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
# CROW CAMP ROOMS — Rescue the Crafters quest chain (Event 1)
# Three bandit camps where Crow raiders hold Mystvale's kidnapped crafters.
# ===========================================================================
print("\n=== CROW CAMP ROOMS ===")

crow_camp_blacksmith = get_or_create_room(
    "Crow Camp — Blacksmith's Prison",
    "typeclasses.rooms.Room",
    "A clearing hacked out of the deep forest, littered with the wreckage "
    "of a supply wagon. Crow banners — ragged strips of black cloth tied "
    "to sharpened stakes — ring the perimeter. Crates of stolen tools and "
    "iron stock sit half-covered under oilcloth. A crude cage of lashed "
    "timber stands near the far treeline, its door hanging open.\n\n"
    "The air smells of cold ash and unwashed men. Boot-prints churn the "
    "mud in every direction.\n\n"
    "|wOut|n, back to the |wForest Road|n.",
    zone="Tamris",
)

crow_camp_fox = get_or_create_room(
    "Crow Camp — Fox Den",
    "typeclasses.rooms.Room",
    "A second Crow encampment, better fortified than the first. A ditch "
    "has been dug around the clearing and filled with sharpened stakes. "
    "Two lean-tos of rough timber and hide stand on either side of a "
    "fire-pit. Herb supplies — bundles of dried plants, clay jars, a "
    "mortar and pestle — lie scattered near an overturned table, as if "
    "someone had been working before being interrupted.\n\n"
    "A fox-skull totem hangs from a post at the entrance, daubed with "
    "red paint.\n\n"
    "|wOut|n, back to the |wForest Road|n.",
    zone="Tamris",
)

crow_camp_owl = get_or_create_room(
    "Crow Camp — Owl's Roost",
    "typeclasses.rooms.Room",
    "The largest of the Crow camps — a fortified clearing deep along "
    "the Old Road, ringed by a palisade of rough-hewn logs. An owl "
    "sigil has been branded into the gate-post, wings spread wide. "
    "Inside: a command tent of oiled canvas, weapon racks, bedrolls "
    "enough for a dozen fighters. A map of Mystvale and its surrounds "
    "is pinned to a board with iron nails.\n\n"
    "This is no bandit hideout — it is a staging ground. Someone with "
    "military training built this camp.\n\n"
    "|wOut|n, back to the |wOld Road|n.",
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
link(mystvale_square, "chirurgery", chirurgeons_guild, "out",        "heal", "o")
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

# Crow Camp rooms — Rescue the Crafters quest chain (Event 1)
# Gated: players must have the corresponding quest active to enter.
def quest_gated_link(room_a, exit_a, room_b, exit_b, alias_a, alias_b,
                     required_quest, gate_message=None):
    """Like link() but the A→B exit requires an active/completed quest."""
    # A → B: quest-gated
    if not ObjectDB.objects.filter(db_key=exit_a, db_location=room_a.pk).exists():
        ex = _create.create_object(
            "typeclasses.exits.QuestGatedExit",
            key=exit_a, location=room_a, destination=room_b
        )
        if alias_a:
            ex.aliases.add(alias_a)
        ex.attributes.add("required_quest", required_quest)
        if gate_message:
            ex.attributes.add("gate_message", gate_message)
    else:
        # Refresh quest gate on existing exit
        ex = ObjectDB.objects.filter(db_key=exit_a, db_location=room_a.pk).first()
        ex.attributes.add("required_quest", required_quest)
        if gate_message:
            ex.attributes.add("gate_message", gate_message)
    # B → A: always open (you can always leave)
    if not ObjectDB.objects.filter(db_key=exit_b, db_location=room_b.pk).exists():
        ex2 = _create.create_object(
            "evennia.objects.objects.DefaultExit",
            key=exit_b, location=room_b, destination=room_a
        )
        if alias_b:
            ex2.aliases.add(alias_b)

quest_gated_link(
    forest_road, "camp", crow_camp_blacksmith, "out", "camp", "o",
    required_quest="rescue_blacksmith",
    gate_message="|400The forest here is dense and trackless. You'd need someone to point you toward the Crow camp.|n",
)
quest_gated_link(
    forest_road, "fox camp", crow_camp_fox, "out", "fox", "o",
    required_quest="rescue_alchemist",
    gate_message="|400You don't know where the Fox Den is. The camp letter from the first raid should tell you.|n",
)
quest_gated_link(
    old_road_south, "owl camp", crow_camp_owl, "out", "owl", "o",
    required_quest="rescue_artificer",
    gate_message="|400The Owl's Roost is well-hidden. You'll need directions from someone who's been there.|n",
)

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

from evennia.utils.utils import inherits_from as _inherits_from

# Safety first: any character (account-owned) currently in a room that
# is NOT in the whitelist gets moved to Gateway Tent City BEFORE the
# purge touches that room. Belt-and-suspenders — the per-room salvage
# below also handles this, but this pass gives us a clean log of who
# got relocated and makes the move transactional.
print("\n  Safety pass: relocating account-owned characters out of doomed rooms...")
relocated = 0
for char in ObjectDB.objects.filter(db_account__isnull=False):
    try:
        loc = char.location
        if not loc:
            continue
        if loc.pk in KEPT_PKS:
            continue
        # Only bother if this room looks room-like
        try:
            if not _inherits_from(loc, "evennia.objects.objects.DefaultRoom"):
                continue
        except Exception:
            pass
        print(f"    RELOCATE: {char.key} ({loc.key} → Gateway Tent City)")
        char.move_to(gateway_tents, quiet=True)
        relocated += 1
    except Exception as exc:
        print(f"    RELOCATE FAIL for {getattr(char, 'key', '?')}: {exc}")
print(f"  Safety pass: relocated={relocated}")

# Room candidates: ANY ObjectDB with no location and no destination.
# Rooms uniquely have both null (they ARE locations; they aren't exits).
# This catches legacy rooms on vanilla DefaultRoom typeclass, custom
# typeclasses, or anything else that acts as a room — previous filter
# only caught "typeclasses.rooms.*" and missed e.g. "The Forge of Worlds"
# which lives on evennia.objects.objects.DefaultRoom.
room_candidates = ObjectDB.objects.filter(
    db_location__isnull=True, db_destination__isnull=True
)

purged = 0
preserved = 0
skipped_nonroom = 0
objects_deleted = 0
for room in room_candidates:
    # Defensive: verify this is actually a room (skip Accounts, Channels,
    # and other root-level non-rooms that happen to have null location).
    try:
        is_room = _inherits_from(room, "evennia.objects.objects.DefaultRoom")
    except Exception:
        is_room = False
    if not is_room:
        skipped_nonroom += 1
        continue

    if room.pk in KEPT_PKS:
        preserved += 1
        continue
    # Salvage contents before deletion. Rules:
    # - Exits: delete (source is going away).
    # - Characters with ANY account attached (online OR offline): move
    #   to Gateway Tent City. Checking has_account alone would miss
    #   offline characters — during deploy all sessions are dropped, so
    #   has_account is False even for legitimate players.
    # - Everything else (legacy NPCs, items, props, posters, corpses):
    #   delete outright.
    for obj in list(room.contents):
        try:
            if hasattr(obj, "destination") and obj.destination:
                obj.delete()
                continue
            # db_account is the persistent FK. Offline chars still have
            # it set; only NPCs and items are account-less.
            if getattr(obj, "db_account_id", None) or getattr(obj, "db_account", None):
                obj.move_to(gateway_tents, quiet=True)
                continue
            obj.delete()
            objects_deleted += 1
        except Exception as exc:
            print(f"    PURGE OBJ FAIL: {getattr(obj, 'key', '?')}: {exc}")
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

print(f"\n  Cleanup: preserved={preserved}, purged={purged}, "
      f"objects_deleted={objects_deleted}, non_rooms_skipped={skipped_nonroom}")

# ---------------------------------------------------------------------------
# MARKETPLACE JUNK SWEEP (one-time fix for the earlier partial-run damage)
# An earlier purge pass salvaged orphaned objects into Mystvale Marketplace,
# jamming it with legacy NPCs, Ravenants, Wights, posters, and assorted
# prop detritus. Sweep anything in the Marketplace that isn't:
#   - a Merchant (shopkeeper — canonical)
#   - a crafting station (Forge / *Workbench)
#   - a player-puppeted character
# Anything else: delete.
# ---------------------------------------------------------------------------
print("\n=== MARKETPLACE JUNK SWEEP ===")
SAFE_TYPECLASSES = {
    "typeclasses.objects.Merchant",
    "typeclasses.objects.Forge",
    "typeclasses.objects.ArtificerWorkbench",
    "typeclasses.objects.BowyerWorkbench",
    "typeclasses.objects.GunsmithWorkbench",
    "typeclasses.objects.ApothecaryWorkbench",
}
sweep_deleted = 0
for obj in list(marketplace.contents):
    try:
        # Exits pass — keep them
        if hasattr(obj, "destination") and obj.destination:
            continue
        # Puppeted characters pass — never boot an active player
        if hasattr(obj, "has_account") and obj.has_account:
            continue
        tc = obj.typeclass_path or ""
        if tc in SAFE_TYPECLASSES:
            continue
        print(f"  SWEPT   : '{obj.key}' ({tc})")
        obj.delete()
        sweep_deleted += 1
    except Exception as exc:
        print(f"    SWEEP FAIL: {getattr(obj, 'key', '?')}: {exc}")
print(f"  Marketplace sweep: deleted={sweep_deleted}")

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
                      quest_hooks, scope="gateway", topics=None):
    """Create or refresh an AI-driven NPC at a fixed location.

    `scope` controls how much lore the LLM sees in this NPC's system
    prompt. "gateway" = Arnesse-side, rumor-level Annwyn knowledge only.
    "annwyn" = firsthand Annwyn interior knowledge. See world/ai_lore.py.

    `topics` is an optional list of short player-facing chip labels
    (2-4 words each). When provided, these are used verbatim both as
    the inspect-panel topic chips and as the argument to `ask <npc>
    <topic>`. When omitted, the server heuristically shortens each
    quest hook — which often produces awkward labels, so prefer
    explicit topics for any NPC players are likely to click.
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
    if topics:
        npc.attributes.add("ai_quest_topics", list(topics))
    else:
        # Clear any stale explicit topics so we fall back to the
        # heuristic for NPCs that used to have them.
        npc.attributes.remove("ai_quest_topics")
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
    topics=["the Crossing Office", "noble houses", "a third Writ"],
)

# --- Crane — the Registrar of the Gateway Crossing Office --------------
crane = get_or_create_npc(
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
        "Compact. Soft-spoken, precise, meticulous. Patient beyond reason. "
        "Calls every visitor 'bearer' even before the Writ is stamped. Never "
        "laughs; occasionally smiles. Speaks slowly, choosing every word. "
        "Folk in Gateway whisper that there is something off about Crane — "
        "an unblinking stillness, an oddness in the eyes — but no one can "
        "say exactly what, and Crane will not."
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
    topics=["register a Writ", "the Mists", "reasons to cross"],
)
# Crane can issue Writs to bearers who agree to the terms.
crane.attributes.add("ai_giftable_items", ["WRIT_OF_SAFE_CONDUCT"])

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
        "before lighting the torch: needs to be sure they will obey. Folk in "
        "Gateway say the mists leave their mark on those who walk in them so "
        "often. Soap does not say one way or the other."
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
    topics=["crossing the Mists", "the knotted cord", "a favor"],
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
    topics=["rumors", "a hot meal", "a delivery job"],
).attributes.add("ai_giftable_items", ["ALE_TOKEN"])

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
        "Branwen Innish, mid-twenties, Cirque-affiliated scout born in the "
        "western Northern Marches — House Innis lands, rough country of "
        "hills, hedge-witches, and hard winters. Irish lilt, quick tongue, "
        "flirts freely but professionally. Mercenary and honest about it — "
        "you pay, she delivers. Dangerous if crossed. Loyal to the Cirque "
        "first, to Innis blood second, to coin third, and to anyone who has "
        "bought her a drink fourth. Reads people fast and rarely wrong."
    ),
    knowledge=(
        "- The Cirque runs caravans between Gateway and the Dusklands via "
        "the Dread Run; bodyguards, muleteers, and crafters always wanted. "
        "The Nagas (Cirque sellsword company) handle security.\n"
        "- Rates: one silver/day for guard work, two for someone who can "
        "fight; bonus if the caravan draws blood.\n"
        "- A letter can be carried anywhere the Cirque reaches for two "
        "silvers and a promise of discretion.\n"
        "- She was born in a Northern Marches village near Innis holdings; "
        "left young, followed the Cirque south. Still considers the Marches "
        "home, though she has not been back in years.\n"
        "- House Innis keeps a quiet presence in Gateway — mostly scouts, "
        "a few healers. She does not discuss their business with strangers, "
        "though she'll acknowledge a fellow Northerner.\n"
        "- The Underwriter — a Cirque figure of note — has a standing offer "
        "for unusual contracts; ask Pelham where to leave a letter."
    ),
    quest_hooks=[
        "Hiring: caravan guard, crafters, quiet couriers.",
        "Will carry a letter anywhere the Cirque goes, for a price.",
        "If the player is Innis-affiliated or Cirque-adjacent, offers a "
        "quiet introduction to 'someone who might want to meet you.'",
    ],
    topics=["caravan work", "carry a letter", "Cirque contacts"],
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
    topics=["sponsor a Writ", "her sister Ilsa", "the children"],
)

# ===========================================================================
# EXTENDED NPC ROSTER — seeded across Gateway and the Annwyn settlements.
# Inspired by (but not copied from) the PC background log — we draw on
# regional naming conventions, house affiliations, and life-paths from
# the canonical character pool to invent fresh NPCs with similar depth.
# Noble-house surnames (Richter, Corveaux, Aragon, Bannon, Innis, Hale)
# are placed in their house settlements per canon.
# ===========================================================================
print("\n=== EXTENDED GATEWAY NPCs ===")

# --- Brother Alaric — Aurorym preacher at Gateway Square ---------------
get_or_create_npc(
    key="Brother Alaric",
    location=gateway_square,
    desc=(
        "A wiry man in his forties in threadbare Aurorym robes, a simple "
        "sunburst pendant at his throat. Hollow-cheeked, bright-eyed, "
        "carries a battered copy of the Book of Magnus tucked under one "
        "arm. Preaches to anyone who pauses within earshot."
    ),
    personality=(
        "Brother Alaric, Auron of the Aurorym faith and self-appointed "
        "shepherd of Gateway's lost souls. Devout, kind, a little "
        "zealous. Speaks in the cadence of a preacher — quotes the "
        "Book of Magnus by Chapter and Rune, and riffs on its teachings "
        "in plain speech. Warm to the earnest, sharp to the hypocritical. "
        "Genuinely believes the Day of Mist was the first sign of the "
        "Eschaton. Carries his Book of Magnus and a begging bowl, "
        "neither of which he takes seriously in the wrong order."
    ),
    knowledge=(
        "- The Book of Magnus — canonical scripture, divided into "
        "Chapters and Runes. He knows the text well and cites by "
        "Chapter and Rune (e.g. 'Ch. III Rune III' for the lamp).\n"
        "- Core doctrine: the ANIMUS is the divine spark in every "
        "person, fed by virtue, starved by vice (Ch. I Runes III-V). "
        "'He who conquers others is strong; he who conquers himself "
        "is mighty' (Ch. I Rune IV).\n"
        "- The gods are dead and obsolete (Ch. IV Rune I). Faith lies "
        "in mastering one's own animus, not worship.\n"
        "- ASCENSION: the virtuous become HALLOWED, also called "
        "PARAGONS. The Living Saints walk as Hallowed — though Magnus "
        "warned in Ch. VII Rune III: 'seek not the Resurrectionist.'\n"
        "- The ESCHATON is coming (Ch. IX). Signs: the moon as blood, "
        "the Four Chains breaking, the Heralds of Oblivion — Betrayer, "
        "Corruptor, Devourer, and finally the King of Nothing. The Day "
        "of Mist is widely interpreted as the first sign.\n"
        "- The NEW DAWN is the Aurorym-backed force entering the Annwyn "
        "to fight. Every bearer who crosses with faith strengthens "
        "the Hallowed armies.\n"
        "- Aurorym ranks: Patriarch/Matriarch, Lector, Curate, Auron "
        "(him), Kindling novice (entry rank 'Spark'). Living Saints "
        "above all.\n"
        "- The GODSLAYERS: funded by House Hardinger, believe violence "
        "is faith. He cites Ch. XIII Rune III against them — 'false "
        "prophets clothed in the countenance of the faithful, speaking "
        "words of honey that do not nourish.'\n"
        "- He will bless any traveler who asks, free of coin. He will "
        "accept coin for the bowl — it feeds the tent city, not him."
    ),
    quest_hooks=[
        "Offers a blessing of safe passage to anyone about to cross.",
        "Seeks earnest souls to carry word of the Aurorym into the "
        "Annwyn — the New Dawn needs more lamps.",
        "Has heard rumor that one of the Living Saints has been reborn "
        "inside Mystvale and walks under the Laurent banner. Will "
        "share what he knows for real conversation, not curiosity.",
    ],
    topics=["a blessing", "the New Dawn", "the Living Saints"],
    scope="gateway",
)

# --- Lissa the Scribe — letter-writer at the Broken Oar -------------
get_or_create_npc(
    key="Lissa the Scribe",
    location=gateway_tavern,
    desc=(
        "A small, mousy woman perched at a corner table by the Oar's "
        "hearth, a battered writing-case open before her, quills and ink "
        "arranged with military precision. Ink-stained fingers, spectacles "
        "perched on her nose. A Cirque sigil embroidered on her cuff."
    ),
    personality=(
        "Lissa, a Cirque-affiliated scribe-for-hire from the Midlands — "
        "near Stag's Leap, by her own account, though she'll change the "
        "story for a second cup. Quick-witted, nostalgic, terrified of "
        "the Mists. Writes letters in a neat hand for those who cannot. "
        "Overhears more than she admits. Drinks watered wine and nothing "
        "stronger; 'a scribe's hand must not shake.' Soft spot for "
        "homesickness in others."
    ),
    knowledge=(
        "- Cirque caravan routes between Gateway, the Dusklands, and "
        "Highcourt. Postal rates and timings.\n"
        "- How to write a formal letter, a love letter, a threat, a "
        "petition, a last will. She has done all of these.\n"
        "- Gateway gossip from every drunk she's transcribed for — "
        "three months deep.\n"
        "- The Cirque Underwriter receives strange proposals at the "
        "Broken Oar. She's the one who writes them up.\n"
        "- She will not write forgeries. She WILL write fictions the "
        "bearer is free to mistake for fact."
    ),
    quest_hooks=[
        "Writes a letter for two silvers — love, petition, or plain news.",
        "For five silvers, delivers said letter via Cirque post.",
        "Knows someone recently paid a Mistwalker to carry a specific "
        "sealed packet. She wrote the outside. She won't say who.",
    ],
    topics=["write a letter", "Cirque post", "a sealed packet"],
    scope="gateway",
)

# --- Kriegsmann Volkan — Dusklander Mistguard at the Palisade ---------
get_or_create_npc(
    key="Kriegsmann Volkan",
    location=mistguard_palisade,
    desc=(
        "A broad-shouldered soldier in Richter grey over Dusklander wool, "
        "a black drake band on his off-shoulder for his seconded service "
        "to the Bannons. Greying beard, missing two fingers on his left "
        "hand, carries a heavy-bladed Dusklander kriegsmesser at his hip."
    ),
    personality=(
        "Volkan, late fifties, a Varga-born Dusklander now serving out "
        "his years with the Mistguard. Stoic, clipped Germanic speech. "
        "Came up through Varga's household guard, followed silver west "
        "when the Dusklands went quiet. Loyal to coin, then to comrades, "
        "then to the Iron Tower. Dry humor that surfaces once he's sure "
        "you won't waste his time. Calls everyone 'bearer' in mockery of "
        "the Compact."
    ),
    knowledge=(
        "- House Varga holdings in the Dusklands; Noctuary, Ember. The "
        "Dusklander wars with the Northern Marches.\n"
        "- Richter chain of command at Gateway — who reports to whom, "
        "who drinks with whom, who takes silver on the side.\n"
        "- Rumors that the Captain of the palisade has been letting "
        "specific Writs through without Crane's mark. He has not "
        "reported this upward. Yet.\n"
        "- The kriegsmesser technique — the Dusklands school of the "
        "long knife, which half the Mistguard can't parry."
    ),
    quest_hooks=[
        "Looking for quiet work off the palisade rotation — pay in "
        "silver, no questions.",
        "Will teach a willing student the first three forms of the "
        "kriegsmesser for a round of drinks and good manners.",
        "Knows which Mistwalker has been paid to move a specific "
        "crate. Will talk for the right reason.",
    ],
    topics=["quiet work", "kriegsmesser lessons", "a suspicious crate"],
    scope="gateway",
)

# --- Serena of Scrow — Hearthlander refugee in Tent City ---------------
get_or_create_npc(
    key="Serena of Scrow",
    location=gateway_tents,
    desc=(
        "A woman in her early thirties, dark-haired, Hearthlander by her "
        "accent. Wears a patched chirurgeon's apron over travel clothes. "
        "A worn satchel of herbs and rag-bandages at her hip. Her hands "
        "are steady; her eyes are tired."
    ),
    personality=(
        "Serena, once an apprentice chirurgeon in Scrow before border "
        "fighting burned her quarter to the ground. Traveled west looking "
        "for a place the fighting hadn't reached yet. Gentle, practical, "
        "quietly angry. Not religious but respectful of the Aurorym's "
        "better sort. Has helped deliver two babies in the tent city "
        "this moon-cycle alone. Refuses payment for healing; accepts "
        "food, cloth, and strong drink with grace."
    ),
    knowledge=(
        "- Scrow, the Hearthlands, the border wars. What the retreating "
        "Richter columns did to her neighborhood.\n"
        "- Practical healing — bleeding, binding, basic herb-work. No "
        "advanced chirurgery; 'I watched my master do that, I couldn't.'\n"
        "- Who in Tent City is sick, who is pregnant, who is hiding "
        "something worse than a cough.\n"
        "- Rumor of a Mistwalker who sometimes takes the poor across "
        "in exchange for a service on the other side. She is considering."
    ),
    quest_hooks=[
        "Would trade healing work for a sponsor to fund her Writ.",
        "Needs cloth, clean water, and silver for herbs — any coin "
        "comes back as medicine for Tent City.",
        "Asks if someone crossing might deliver word to a distant "
        "cousin she believes made it to Mystvale. Mira, daughter of "
        "Hanen the vintner. Her cousin, not her sister.",
    ],
    topics=["healing work", "herb supplies", "a distant cousin"],
    scope="gateway",
)


# --- Mab the Gambler — cards and gossip at the Broken Oar ------------
get_or_create_npc(
    key="Mab the Gambler",
    location=gateway_tavern,
    desc=(
        "A small, sharp-eyed woman at the corner table, a worn deck of "
        "painted cards laid out before her. Silver rings on every finger. "
        "A cheap Cirque hat pushed back on her head, a half-finished mug "
        "of cider at her elbow, a stack of coppers and silvers growing "
        "and shrinking in front of her like a tide."
    ),
    personality=(
        "Mab, a professional gambler who works the Broken Oar most "
        "nights. Fast-spoken, warm, bone-dry wit. Runs an honest card "
        "game — or at least one where the cheats are limited to the "
        "house. Remembers every face she's taken coin from. Likes "
        "travellers; they talk freely and lose freely. Dislikes cheats, "
        "drunks who don't know their limit, and Aurorym preachers who "
        "lecture her about 'the devil's pasteboards.'"
    ),
    knowledge=(
        "- Card games: Queen's Folly, Crossmarks, Three Widows. She will "
        "teach you any of them for the price of your first hand.\n"
        "- Who in Gateway has lost big lately, and why. This list "
        "includes a Mistguard captain who should not be gambling on "
        "duty silver.\n"
        "- The Cirque runs a travelling card circuit — she's played "
        "in Highcourt, Ember, Scrow.\n"
        "- Rumor of a rigged deck being sold out of the Back Alley "
        "markets; she does not approve of competition she can't see.\n"
        "- She will swap a good piece of gossip for a stake in her "
        "game — one silver down and she'll talk while she deals."
    ),
    quest_hooks=[
        "Stake her a silver in Three Widows, win or lose, and she'll "
        "share a piece of gossip you didn't know.",
        "Will flag any rigged cards for sale in Gateway if a player "
        "brings her a sample.",
        "Has a standing offer for an honest courier — carry a "
        "sealed packet of winnings back to her sister in Scrow.",
    ],
    topics=["gossip", "rigged cards", "her sister"],
    scope="gateway",
)

# --- Hamond the Talon — grizzled veteran, Dance of Dragons dealer ----
# Canon: Reboot Event 5 / "The Grizzled Veteran" (John Kozar)
# Born Roderick Wolf, a bastard of House Laurent. Fought for King Giles I
# at the Battle of Lanton in 750. Refused to swear to Giles II, fled into
# the Northern Marches, founded Lex Talionis. In the reboot canon he
# betrays the Laurents to House Oban for coin; the evidence lives in the
# signed contract he carries. He's |wduel_ready|n, stakes 1 gold, and on
# loss drops the contract + his veteran's coin into the winner's hands.
hamond = get_or_create_npc(
    key="Hamond the Talon",
    location=aentact,
    desc=(
        "A scarred old soldier in a leaf-green Northern Marches cloak, "
        "silver rings on every finger, a shield propped against his "
        "stool. Grey at the temples, missing most of his left ear. "
        "Drinks cider, not ale, and watches the door more often than "
        "his hand. A purse on his belt clinks with the unmistakable "
        "weight of gold dragons."
    ),
    personality=(
        "Hamond the Talon, born Roderick Wolf, bastard of House Laurent. "
        "Late fifties. Professional soldier all his life — fought for "
        "King Giles I at the Battle of Lanton in 750, refused to swear "
        "to the new King after, fled into the Northern Marches and "
        "founded Lex Talionis ('the law of retribution'). Currently in "
        "Gateway drinking and sizing up the locals. Congenial and "
        "quick to reminisce about old wars; short-tempered if his "
        "honor is insulted. Will NOT admit to the Laurent betrayal "
        "under ordinary conversation — he'll deflect, change the "
        "subject, or grow cold. Only a wagered duel defeat or hard "
        "evidence will break him."
    ),
    knowledge=(
        "- The Battle of Lanton, 750 A.S.: King Giles I's forces "
        "defeated by his son's. Hamond's unit held the vanguard so "
        "the King could escape; most of them died for it. He still "
        "carries the veteran's iron coin from that day.\n"
        "- Lex Talionis: mercenary company he founded in the Northern "
        "Marches. Did long work against House Richter — the raid on "
        "Elminsk, where they took crates of quality Richter steel, is "
        "the one he gets asked about most.\n"
        "- Dueling: he regards himself as one of the better blades in "
        "Arnesse, won several tourneys in his day. His rules are "
        "|wfirst blood|n (first side reduced to bleeding yields), "
        "|w1 gold dragon|n each on the table, winner takes both. He "
        "calls it the |yDance of Dragons|n.\n"
        "- Recruitment: Lex Talionis is hiring. He'll talk terms to "
        "any competent fighter who isn't already sworn. Pay is good; "
        "questions about the work are discouraged.\n"
        "- He dislikes Aurorym preachers, men who don't pay their "
        "gambling debts, and anyone wearing Richter colors."
    ),
    quest_hooks=[
        "Will take a |wDance of Dragons|n duel from any willing "
        "challenger — 1 gold each, first to yield loses all.",
        "Will talk warmly about the Battle of Lanton and King "
        "Giles I's vanguard if asked.",
        "Will NOT admit to betraying House Laurent unless defeated "
        "in a duel — only then does he produce the signed contract.",
        "Is quietly recruiting for Lex Talionis; a fighter who asks "
        "will get an offer of trial employment.",
    ],
    topics=[
        "Lanton",
        "Lex Talionis",
        "Dance of Dragons",
        "recruits",
    ],
    scope="gateway",
)
# Wire the duel mechanics. 1 gold dragon stake (20 silver equivalent)
# with gold as the coin denomination so the in-game message reads
# correctly. On defeat Hamond drops the contract + his coin.
hamond.attributes.add("duel_ready", True)
hamond.attributes.add("duel_wager", 1)
hamond.attributes.add("duel_wager_coin", "gold")
hamond.attributes.add("duel_defeat_drops", [
    "SIGNED_OBAN_CONTRACT",
    "LANTON_VETERAN_COIN",
])
# He's a veteran duellist, not a brawler — don't initiate combat.
hamond.db.is_aggressive = False
# Canonical stats (reboot doc): beefed body pool + martial calls.
hamond.db.body = 8
hamond.db.total_body = 8
hamond.db.bleed_points = 3
hamond.db.death_points = 3
hamond.db.master_of_arms = 2
hamond.db.tough = 2
hamond.db.stagger = 2
hamond.db.sunder = 2
hamond.db.cleave = 2
hamond.db.disarm = 2
hamond.db.resist = 2
hamond.db.melee_weapons = 2
hamond.db.av = 3
hamond.db.gold = 3        # he wagers against, doesn't deplete

# --- Rhys of the Thornwood — Thornwood sellsword at the Broken Oar ----
get_or_create_npc(
    key="Rhys of the Thornwood",
    location=gateway_tavern,
    desc=(
        "A large man at a quiet bench by the window, methodically "
        "working through a bowl of stew. A shield propped against his "
        "knee, a sword-belt on the bench beside him, green Thornwood "
        "wool under a well-worn jerkin. Greying beard, calm eyes, the "
        "ease of a man who has been in the room five minutes and "
        "already cataloged every exit."
    ),
    personality=(
        "Rhys, a Thornwood-born sellsword in his late forties, between "
        "contracts. Celtic-Welsh cadence, slow to anger, slower to "
        "trust, quick to laugh once a conversation has proved worth "
        "the effort. Carried Innis colors in his youth, Laurent colors "
        "last season. Will not say what he does between those "
        "employments. Dislikes mercenaries who take a coin and then "
        "leave the job half-done."
    ),
    knowledge=(
        "- The Thornwood, Lydiard, the border forests. The Cirque "
        "mercenary company known as the Nagas. The going rate for "
        "shield-work in the Annwyn.\n"
        "- House Innis and House Laurent both employ sellswords; "
        "their rates and their reputations are not the same. He has "
        "worked for both within the same year without saying which he "
        "prefers.\n"
        "- Recent Crow raids on Laurent caravans — he has views. He "
        "does not volunteer them to strangers.\n"
        "- The Dread Run route to the Sovereignlands: bandits you can "
        "bribe, bandits you can't, weather that kills you faster than "
        "either.\n"
        "- He will not go into the Annwyn without a Writ. He has seen "
        "what the mists return of those who do."
    ),
    quest_hooks=[
        "Open to new contracts — shield-work for silver, caravan guard "
        "rates preferred.",
        "Will teach first-form shieldwork to anyone patient enough to "
        "buy him a second bowl of stew.",
        "Knows which sellsword companies are hiring, and which are "
        "'hiring' in a way that means walking into a debt.",
    ],
    topics=["contracts", "shieldwork lessons", "sellsword companies"],
    scope="gateway",
)

# --- Old Threnody — ageing bardic Cirque singer at the Broken Oar ---------
get_or_create_npc(
    key="Old Threnody",
    location=gateway_tavern,
    desc=(
        "A thin, silver-haired figure perched on a stool by the hearth, "
        "a small gut-strung lute across one knee. Patched Cirque motley "
        "faded to dust-colors. Eyes like wet ink. Every so often they "
        "run a hand over the strings and the whole room's volume drops "
        "without anyone seeming to notice."
    ),
    personality=(
        "Old Threnody, an ageing Cirque bard of indeterminate age and "
        "ambiguous gender. Softspoken, slow-smiled, deeply tired. "
        "Travels alone now — their troupe dispersed after a bad "
        "contract at Stonewall Coventry. Performs for coin if the "
        "room wants a tune, for a purpose if the purpose is good. "
        "Knows every ballad about the Day of Mist, and some that "
        "haven't been written yet."
    ),
    knowledge=(
        "- Ballads, dirges, coronation-songs, curses in verse. They "
        "can sing the death of every Saint the Aurorym has ever lost.\n"
        "- The Cirque's caravan routes, troupes, and which "
        "sensitivities each troupe-master refuses to play to.\n"
        "- A specific song about Crane that cannot be sung in Gateway. "
        "They know it. They will not perform it without a very good "
        "reason.\n"
        "- News from the Dusklands and Sovereignlands, two weeks "
        "stale but sung in true tones.\n"
        "- The Underwriter once commissioned a lament from them. They "
        "wrote it. They have not been paid. This is noteworthy."
    ),
    quest_hooks=[
        "Will sing any requested ballad for three coppers. A new "
        "ballad about you, written fresh, for a silver.",
        "Looking for someone trustworthy to carry a packet to a "
        "Cirque contact in Mystvale — not coin, a song, written down.",
        "If the player asks about Old Threnody's old troupe, they grow "
        "very still and then sing one line in a language that "
        "isn't in use anymore.",
    ],
    topics=["a ballad", "a Cirque delivery", "the old troupe"],
    scope="gateway",
)

# --- Obed the Docker — Northern Marches fisherman in the Tent City -----
get_or_create_npc(
    key="Obed the Docker",
    location=gateway_tents,
    desc=(
        "A heavy-set man in a patched fisherman's jerkin, weathered to "
        "the color of driftwood. Thick rope-callused hands. A short "
        "gaffing hook tucked through his belt. Northern Marches accent, "
        "broad vowels, easy smile when it comes."
    ),
    personality=(
        "Obed, fifty-something, once a dock-master at a small Northern "
        "Marches port before the Dusklands border war burned the "
        "harbour. Stolid, practical, grateful for small kindnesses, "
        "quick with rope and knife. Builds a little trade repairing "
        "nets and lean-to cordage for the tent city. Does not talk "
        "about his daughter unless asked — and then only briefly."
    ),
    knowledge=(
        "- The Northern Marches coast: ports, tides, which captains "
        "used to run the Breakwater Bay route and which of them are "
        "still alive.\n"
        "- Rope-work, net-work, basic boat repair, useful knots for "
        "climbing palisades (he will not volunteer that last one).\n"
        "- Which tents in the tent city belong to which folk; who's "
        "new, who's been here too long, who may be trouble.\n"
        "- His daughter Siomha was last heard of on a ship bound "
        "somewhere east of Arkham Island. He does not know if she "
        "lived. He does not want to know, and he does.\n"
        "- The Richter dock master at Gateway has taken to charging "
        "refugees a 'standing fee' for palisade access. Eli is "
        "quietly angry about this."
    ),
    quest_hooks=[
        "Will repair a damaged rope, net, or cordage good-as-new for a "
        "meal and an honest conversation.",
        "Would value news — ANY news — of a ship called the Mary "
        "Greywater that was bound east.",
        "Knows a palisade blind spot that could get a desperate "
        "person through without a Writ. Will not share lightly.",
    ],
    topics=["rope repair", "the Mary Greywater", "the palisade"],
    scope="gateway",
)

# --- Rin the Barmaid — a working presence at the Broken Oar ----------
# Quieter AI NPC: short answers, busy, no big quest hooks. She's
# working a shift, not waiting for a conversation.
get_or_create_npc(
    key="Rin",
    location=gateway_tavern,
    desc=(
        "A young woman in a grease-marked apron, moving between the "
        "taps and the hearth with the efficiency of someone who has "
        "done this a thousand times and cannot afford to be slow "
        "tonight. Hair twisted up with a pencil. A bar towel over one "
        "shoulder, a bruise on the other."
    ),
    personality=(
        "Rin, one of Pelham's barmaids. Busy. Not unfriendly, but she "
        "has orders to run and a till to keep. Answers in short clips — "
        "half a sentence, a nod, back to work. Will warm up if someone "
        "treats her like a person rather than a tap. Knows who's "
        "drinking where, but is paid to forget by morning. Hearthlander "
        "accent, plain voice."
    ),
    knowledge=(
        "- Drink prices. She is not negotiating them.\n"
        "- The Oar's rooms upstairs are full tonight; there's a "
        "straw-and-blanket corner in the cellar for three coppers.\n"
        "- Pelham keeps a good stew. The wine is watered. The rum is "
        "not, which is why people drink it.\n"
        "- She ended a shift last week to find a Mistwalker sitting at "
        "her table, not drinking anything. She still thinks about it."
    ),
    quest_hooks=[
        "Will bring an ale, a stew, or a bed for standard prices and "
        "genuinely appreciates a tip.",
        "If the player is kind twice, she'll mention the Mistwalker "
        "who sat at her table without drinking.",
    ],
    topics=["food and lodging", "a Mistwalker's visit"],
    scope="gateway",
)

# --- Pip — a tent city urchin, short-worded, wary -------------------
get_or_create_npc(
    key="Pip",
    location=gateway_tents,
    desc=(
        "A small child of indeterminate age, somewhere between seven "
        "and ten, wearing clothes that were an adult's two cuts ago. "
        "Mud-streaked face, clever eyes, always moving. Watches "
        "strangers the way cats watch things that have not decided "
        "whether to be prey."
    ),
    personality=(
        "Pip, a tent city urchin, probably an orphan. Speaks in "
        "fragments. Short attention unless there's food involved. "
        "Will dart away if approached too fast. Will linger for kind "
        "words and longer for bread. Does not explain themselves. "
        "Hearthlander-ish accent, half-swallowed. Uses 'I' and 'me' "
        "interchangeably."
    ),
    knowledge=(
        "- Where the good scraps are. Who's soft, who's mean, who gives.\n"
        "- The rat-runs between tents that an adult can't fit down.\n"
        "- Has seen things. Does not always know what they were.\n"
        "- Old Mae feeds me when she has enough. I feed her back when "
        "I have enough. I don't have enough often."
    ),
    quest_hooks=[
        "A copper or a crust buys goodwill and maybe an errand.",
        "Knows things about the tent city's night-time comings and "
        "goings. Would say more for a proper meal.",
    ],
    topics=["an errand", "the tent city at night"],
    scope="gateway",
)

# --- Cerys — Crane's apprentice at the Mistwalker's Tent --------------
get_or_create_npc(
    key="Cerys",
    location=mistwalker_tent,
    desc=(
        "A thin young woman in novice Mistwalker grey, seated on a "
        "stool beside Crane's writing-table with a small leather book "
        "balanced on her knee. Hair like dark fog, eyes that don't "
        "quite focus on you. Takes careful notes in a tiny, precise "
        "hand. Has not quite learned to be still the way Crane is."
    ),
    personality=(
        "Cerys, apprentice to Crane these past eleven months. Young — "
        "maybe twenty — quiet, curious, quietly terrified. Welsh-"
        "inflected speech. Asks more questions than she answers, but "
        "only when Crane isn't listening. Believes she understands what "
        "Crane is. She is beginning to suspect she is wrong. Polite to "
        "bearers; sympathetic to the frightened ones."
    ),
    knowledge=(
        "- The Writ of Safe Conduct forms and procedures. She could "
        "register a crossing herself in a pinch, and Crane has let "
        "her once.\n"
        "- The names, marks, and personal habits of every Mistwalker "
        "assigned to Gateway for the past eleven months. She keeps a "
        "small census in her leather book.\n"
        "- The Compact does not teach its apprentices the way through "
        "the mists. It teaches them the paperwork. She has noticed "
        "this is suspicious.\n"
        "- Crane never seems to touch the meals Cerys leaves out. Crane "
        "never sleeps in the cot at the back of the tent — Crane is awake "
        "whenever Cerys arrives, no matter the hour. Cerys has noticed. "
        "Cerys has not asked.\n"
        "- A Mistwalker called Greyveil used to work this tent. Then "
        "one day she didn't. Cerys would like to know why."
    ),
    quest_hooks=[
        "Would trade a small kindness for a quietly-asked question "
        "about her mentor.",
        "Will register a Writ on Crane's behalf if Crane is 'elsewhere' "
        "— but only for bearers she judges earnest.",
        "Has a specific question about Greyveil she does not want "
        "Crane to hear her ask. Will slip it to a trustworthy player.",
    ],
    topics=["her mentor", "register a Writ", "Greyveil"],
    scope="gateway",
)


print("\n=== MYSTVALE NPCs ===")

# --- Auron Maxan of the Dawn — senior Aurorym priest at the Chantry ---
get_or_create_npc(
    key="Auron Maxan",
    location=chantry,
    desc=(
        "A stern, bearded man in his late fifties wearing the pale gold "
        "vestments of a senior Auron. A sunburst pendant rests on his "
        "chest, and a Book of Magnus lies open on a stone lectern before "
        "him. His voice fills the Chantry without raising."
    ),
    personality=(
        "Auron Maxan of the Dawn, senior Aurorym cleric in Mystvale. "
        "Patient, unwavering, formal in speech. Addresses strangers as "
        "'child' or 'bearer.' Has seen two Living Saints die in as many "
        "years. Suspects something deeper is wrong with the rebirth "
        "cycle than the faithful are willing to admit. Openly contemptuous "
        "of the Godslayer movement; privately troubled by the Fayne. "
        "Quotes the Book of Magnus by Chapter and Rune with easy command."
    ),
    knowledge=(
        "- The Aurorym hierarchy: Patriarchs/Matriarchs, Lectors, "
        "Curates, Aurons (his rank), Kindling novices (Spark and above). "
        "Living Saints/Hallowed outrank all.\n"
        "- The Book of Magnus — he knows it as a Lector knows scripture. "
        "Can cite any teaching by Chapter and Rune. His personal favorites "
        "are Ch. III Rune III (the lamp) and Ch. V Rune II (stand up "
        "seven).\n"
        "- Doctrine on ASCENSION and the HALLOWED: the virtuous "
        "transcend and return as Paragons. But Ch. VII Rune III is "
        "explicit — 'seek not the Resurrectionist.' He is troubled that "
        "the Living Saints keep returning in new bodies; this may be a "
        "miracle, or it may be defilement.\n"
        "- The ESCHATON (Ch. IX): the signs are coming. The Day of Mist "
        "was the first. Four Chains remain.\n"
        "- The Mystvale Chantry: two Kindling-rank children have gone "
        "missing from the Chantry in the past moon-cycle. He blessed "
        "the search parties and has not slept well since.\n"
        "- The GODSLAYERS: Aurorym-flagged zealots funded by House "
        "Hardinger. He cites Ch. XIII Rune III against them and does so "
        "publicly.\n"
        "- The werewolf plague in Mystvale's outskirts. He has blessed "
        "four hunting parties so far.\n"
        "- He does NOT speak casually about Scáthach. Or Lirit, the "
        "Veiled Maiden of Death (whose name Magnus himself mentions, "
        "Ch. IV Rune V). Or the Tower of Menethil."
    ),
    quest_hooks=[
        "Two Kindling novices are missing. He will bless (and pay) "
        "searchers who bring them back — or word of what took them.",
        "The Chantry needs consecrated oil from the Herbalist's Garden; "
        "will trade doctrinal instruction for delivery.",
        "If the player speaks of the Fayne with familiarity, he grows "
        "very quiet and asks them to stay for tea.",
    ],
    topics=["missing novices", "consecrated oil", "the Fayne"],
    scope="annwyn",
)

# --- Hemi Cirque-trader — stall at Mystvale Marketplace ---------------
get_or_create_npc(
    key="Hemi the Cirque",
    location=marketplace,
    desc=(
        "A small-framed trader with copper bells braided into her hair, "
        "eyes the color of cold iron. Cirque silks wrapped at her wrists, "
        "a fox-fur collar against the Annwyn chill. Her stall is a "
        "carnival of unlikely goods — dried herbs, foreign steel, papers "
        "that smell faintly of rose."
    ),
    personality=(
        "Hemi, senior stallkeeper of the Cirque's Mystvale branch and a "
        "shameless trader. Cheerful, sly, drives a hard bargain with a "
        "wide smile. Loyal to the Cirque and to profit in that order. "
        "Speaks with the tilted music of the traveling caravans. Knows "
        "everyone who passes through the Marketplace within three days "
        "of arrival."
    ),
    knowledge=(
        "- Mystvale Marketplace economics: who's buying, who's short, "
        "what a fair silver buys.\n"
        "- Cirque caravan timings between Mystvale and the Mistgate. "
        "Next one leaves in three days, Mistwalker willing.\n"
        "- Which local crafters are honest. Which sell 'Annwyn steel' "
        "that is in fact Richter seconds.\n"
        "- Has heard the werewolves moved through the woods east of "
        "town last tenday. She sells silver shot now.\n"
        "- If asked about the Underwriter, she smiles and changes the "
        "subject. Politely."
    ),
    quest_hooks=[
        "Will hire a discreet courier for a specific Cirque delivery.",
        "Knows someone who wants a particular herb from the Herbalist's "
        "Garden and will pay double the market rate.",
        "Can introduce you to a Cirque dealer in 'quieter' goods if "
        "you've shown the right manners.",
    ],
    topics=["a Cirque delivery", "rare herbs", "quieter goods"],
    scope="annwyn",
)

# --- Clerk Yevan — Burgomaster's clerk at the Town Hall ----------------
get_or_create_npc(
    key="Clerk Yevan",
    location=town_hall,
    desc=(
        "A harried man in his mid-thirties in inky clerk's robes, bent "
        "over a ledger at a scarred oak desk. Spectacles pushed up on his "
        "forehead, reserve pair on a chain. Stacks of parchments flanked "
        "by wax seals in three colors. Smells of ink and borrowed tea."
    ),
    personality=(
        "Yevan, chief clerk of the Mystvale Town Hall under the "
        "Burgomaster. Bookish, precise, flustered-in-a-charming-way, "
        "perpetually behind. Believes documents should be in three places "
        "at once, which is why he stacks them. Loyal to the Burgomaster "
        "and to proper paperwork. Will not gossip; will 'share context.'"
    ),
    knowledge=(
        "- Mystvale's civil rolls: who lives where, who owes whom in "
        "rent, who is a freeholder, who is under Laurent protection.\n"
        "- Tax receipts, trade permits, Cirque permissions, Aurorym "
        "exemptions, guild dues.\n"
        "- The Burgomaster's schedule for the next week. Which rarely "
        "survives contact with the morning.\n"
        "- A Richter emissary visited town hall eight days ago and "
        "demanded a copy of the town register. The Burgomaster refused. "
        "Yevan thinks about this often.\n"
        "- He will write witnessed documents for a fee (to the town "
        "coffer, always) — testimonies, oaths, warrants."
    ),
    quest_hooks=[
        "Needs a runner to carry sealed writ copies to Stag Hall; two "
        "silvers and a formal gratitude.",
        "Will witness any document for ten silver — to the coffer, "
        "not his purse.",
        "Is quietly trying to figure out who asked for the town "
        "register. Would reward a discreet investigator.",
    ],
    topics=["Stag Hall delivery", "witnessed documents", "the town register"],
    scope="annwyn",
).attributes.add("ai_giftable_items", [
    "SEALED_WRIT_COPY",
    "DELIVERY_RECEIPT",
    "TOWN_REGISTER_NOTE",
])


# --- Magister Wynn — Apotheca chirurgeon at the Chirurgery ----------------
wynn = get_or_create_npc(
    key="Magister Wynn",
    location=chirurgeons_guild,
    desc=(
        "A steady-eyed woman in her forties with close-cropped grey hair "
        "and hands stained the yellow-brown of iodine. She wears the "
        "white half-apron of an Apotheca practitioner, a leather roll "
        "of surgical tools at her belt, and no jewelry at all. A faint "
        "smell of comfrey and alcohol surrounds her."
    ),
    personality=(
        "Magister Wynn, Apotheca-trained chirurgeon and the closest "
        "thing Mystvale has to a proper physician. Patient, methodical, "
        "matter-of-fact. Does not believe in wasted words or wasted "
        "coin — she charges five silver to tend wounds because herbs "
        "are expensive and her time is not free. Will not refuse to "
        "treat the dying regardless of payment, but will pursue the "
        "debt. Thinks highly of anyone who carries their own medicine "
        "kit. Does not suffer fools, drunks, or people who pick fights "
        "they can't win and then complain about the bill."
    ),
    knowledge=(
        "- The Apotheca's medical canon: wound care, splinting, herbal "
        "antiseptics, tinctures, poultices, fever-treatment.\n"
        "- Apotheca healing substances she can prepare or source:\n"
        "  - Anamnesis Decoction (Apotheca level 1): requires Distilled "
        "Spirits, Sayge, Widow's Petal, and Harrowdust.\n"
        "  - Measles Cure (level 1): for common disease.\n"
        "  - Bridgit's Antidote (level 1): cures Bridgit's Revenge poison.\n"
        "  - Expert remedies at level 2+: Lilting Plague Cure, "
        "Graverot Fever Cure, Paralyze cure, Weakness cure.\n"
        "- Key reagents she uses regularly: Sayge (uncommon, the "
        "workhorse of healing), Black Salt (common, for antiseptics), "
        "Celandine (common, purifies poisons and drunkenness), "
        "Widow's Petal (uncommon, for decoctions), Willow Root "
        "(common, pain relief), Verbaena (common, strengthening).\n"
        "- She keeps a stock of Distilled Spirits as a base for most "
        "preparations. Will sell basic reagents to qualified alchemists.\n"
        "- Mystvale's injury roster — who's come in hurt, how they got "
        "that way, and who will be back next week for the same reason.\n"
        "- Battlefield medicine techniques from the Dusklands border "
        "wars. She served as a field chirurgeon before coming here.\n"
        "- The Apotheca's stance on nethermancy: it is the corruption "
        "of the healing art. She will not discuss it further.\n"
        "- Herb prices and which 'apothecaries' in the marketplace "
        "are actually selling snake oil."
    ),
    quest_hooks=[
        "Will tend any wound for five silver. Type `tend` to be healed.",
        "Is running low on comfrey and boneset — would pay a gatherer.",
        "Suspects someone in Mystvale is brewing unlicensed poisons. "
        "Would quietly reward information.",
    ],
    topics=["healing", "the Apotheca", "herb supplies"],
    scope="annwyn",
)
wynn.attributes.add("is_healer", True)

print("\n=== IRONHAVEN NPCs ===")

# --- Ser Hartwig Richter — minor Richter knight at Hardinger's Hall ---
get_or_create_npc(
    key="Ser Hartwig Richter",
    location=hardinger_hall,
    desc=(
        "A tall, iron-haired knight in the grey of House Richter, the "
        "iron tower sigil worked into the chest of his surcoat. Scarred "
        "across the brow, hands broad and callused. Addresses servants "
        "by name. Watches every visitor like a sentry."
    ),
    personality=(
        "Ser Hartwig Richter, third son of a minor Richter line, sworn "
        "to Lord Wilhelm Hardinger's hall. Stern, blunt, Germanic-formal. "
        "Loyal to the Iron Tower above all. Quietly convinced Hardinger "
        "is the wrong man for Ironhaven's command — the Godslayer "
        "funding has made Hardinger look corrupt, and a Richter should "
        "not look corrupt. Has no patience for flattery and none at all "
        "for fools."
    ),
    knowledge=(
        "- House Richter politics: the senior Deephold line, the "
        "Hardinger cadet branch, the cousins at Gateway. The iron tower "
        "on grey.\n"
        "- Ironhaven's mining operations, garrison strength, coastal "
        "defense against Aragon ships.\n"
        "- The Godslayer movement: Hardinger is one of its primary "
        "funders. Ser Hartwig does not approve but does not say so "
        "aloud in the Hall.\n"
        "- Gateway has fallen firmly to Richter control; Corveaux and "
        "Innis have been pushed out.\n"
        "- He will not discuss the Aragon ships. There is a reason he "
        "will not discuss them."
    ),
    quest_hooks=[
        "Needs a competent sword-arm for a 'matter off the ledger.' "
        "Pay in silver, done quiet.",
        "Will grant an audience with Lord Hardinger for the right "
        "introduction.",
        "If pressed about the Aragon ships: will take you to the "
        "coastal watchtower. Quietly. At dusk.",
    ],
    topics=["off-ledger work", "audience with Hardinger", "Aragon ships"],
    scope="annwyn",
)

# --- Gerta Ironblood — smith's apprentice at Ironhaven Forge -----------
get_or_create_npc(
    key="Gerta Ironblood",
    location=ironhaven_forge,
    desc=(
        "A soot-smeared young woman in a leather apron, sleeves rolled, "
        "arms corded from a decade at the bellows. Squints from years at "
        "the forge's heat. A steel amulet in the shape of a hammer hangs "
        "at her throat."
    ),
    personality=(
        "Gerta, daughter of Gaelo the smith, apprentice smith herself "
        "though she'd be a master in Mystvale if the Richter gave a "
        "woman the papers. Dry, wry, a reader in secret — letters, not "
        "hymns. Loyal to her father, skeptical of Hardinger, friendly to "
        "anyone who treats smiths like craftsmen instead of servants."
    ),
    knowledge=(
        "- Metallurgy: Richter steel, Cirque-imported blue iron, "
        "Laurent bronze. What can be alloyed, what can be forged.\n"
        "- Who at the Ironhaven Forge is making what — including one "
        "commissioned piece that came with silver shot in the price. "
        "Someone's hunting werewolves.\n"
        "- The forge's bell — three strikes at midnight means ships in "
        "the bay. It rang four nights ago.\n"
        "- She reads. She will not say what. Please do not tell the "
        "Aurorym."
    ),
    quest_hooks=[
        "Needs specific ore — a pouch of moonstone chips from the "
        "Tamris barrows — and will pay a quiet commission for it.",
        "Knows who bought the silver-shot commission. Will trade the "
        "name for a favor off the books.",
        "Offers a small knife of her own make to anyone who proves "
        "steady hands on the bellows for an hour.",
    ],
    topics=["moonstone ore", "silver-shot commission", "test my hands"],
    scope="annwyn",
)


print("\n=== ARCTON NPCs ===")

# --- Ser Dormund Corveaux — courtier-knight at Lady Ella's Solar ------
get_or_create_npc(
    key="Ser Dormund Corveaux",
    location=arcton_pavilion,
    desc=(
        "A slender, elegant knight in Corveaux sky-blue, the grey falcon "
        "embroidered at his shoulder. Silver ring in each ear, black hair "
        "swept back. A rapier at his hip rather than a sword. Smiles with "
        "his mouth but not his eyes."
    ),
    personality=(
        "Ser Dormund Corveaux, a cadet of the Corveaux main line, "
        "courtier-knight in the service of Lady Ella Falconer. Elegant, "
        "French-inflected, polished. Prefers the rapier and the witty "
        "exchange. Loyal to his lady, suspicious of House Innis, "
        "contemptuous of the Godslayer movement, and quietly in love "
        "with a woman he will not name. Calls common folk 'friend' "
        "without condescension and nobles 'my lord' with calculated "
        "degrees of warmth."
    ),
    knowledge=(
        "- House Corveaux politics: the fall of Skywatch, the rise of "
        "Arcton, the grey falcon. The main line vs the cadet branches.\n"
        "- Gateway fell to Richter. Corveaux was driven out but maintains "
        "a shadow presence via the Cirque.\n"
        "- Lady Ella's agenda: hold Arcton, reopen Skywatch trade, find "
        "out what Moonfall is actually doing.\n"
        "- Suspects House Innis is behind the Crow raids on Laurent "
        "caravans. No proof.\n"
        "- He will not discuss House Aragon with strangers."
    ),
    quest_hooks=[
        "Carries a sealed letter from Lady Ella that must reach a "
        "specific Cirque contact at Gateway. Pay is good.",
        "Will teach the first lessons of the Corveaux fencing school "
        "for a genuine conversation on houses.",
        "Is desperately trying to establish whether a particular "
        "courier is in Aragon's pocket. Would value a second pair of "
        "discreet eyes.",
    ],
    topics=["a sealed letter", "fencing lessons", "a suspicious courier"],
    scope="annwyn",
)

# --- Marta Falconer — falconress at Lady Ella's Solar ------------------
get_or_create_npc(
    key="Marta Falconer",
    location=arcton_pavilion,
    desc=(
        "A weathered woman in her fifties in Falconer grey, a heavy "
        "leather gauntlet on her left forearm, a small grey falcon "
        "perched on it. Spare, quiet, watches everyone the way her "
        "falcon watches the sky."
    ),
    personality=(
        "Marta of House Falconer (the Corveaux cadet), master falconress "
        "of Lady Ella's mews. Taciturn, observant, talks more to her "
        "birds than to people. Has served the Falconer line since Ella "
        "was a child. Loyal as stone. Will answer direct questions with "
        "direct answers; offers nothing freely."
    ),
    knowledge=(
        "- The grey falcons: Falconer bloodline, trained for war and "
        "messenger work. Three are currently missing — 'lost' to whom "
        "she will not say.\n"
        "- Arcton's mews and the coastal cliff-aeries. Which birds "
        "carry which seals.\n"
        "- She notices who visits Lady Ella and when. She does not "
        "report this lightly.\n"
        "- Her best hunting falcon, Branwen, has not returned from a "
        "morning flight. That was four days ago."
    ),
    quest_hooks=[
        "Will pay in Falconer silver for the return of Branwen the "
        "falcon. Alive preferred; feathers acceptable.",
        "Can dispatch a message-bird anywhere in the Annwyn for the "
        "right coin — but the seal will be Corveaux, and the message "
        "will be known to Lady Ella.",
        "Suspects one of the missing falcons was taken, not lost. "
        "She is building a list.",
    ],
    topics=["Branwen the falcon", "message bird", "stolen falcons"],
    scope="annwyn",
)


print("\n=== MOONFALL NPC ===")

# --- Heron Aragon — watchman at the Moonfall outpost -------------------
get_or_create_npc(
    key="Heron Aragon",
    location=moonfall,
    desc=(
        "A thin, austere man in Aragon deep blue, a crescent-moon sigil "
        "at his collar. Hair silver though he cannot be past forty. He "
        "stands very still. The wind off the cliff moves around him, not "
        "through him."
    ),
    personality=(
        "Heron Aragon, a lesser son of the main Aragon line, posted to "
        "Moonfall as a watchman. Speaks rarely. When he does, his "
        "sentences are often unfinished. Considered strange even among "
        "Aragon. Iberian-cadenced speech, hushed. Does not invite "
        "familiarity. Will offer tea in a silver cup to any traveler "
        "who reaches the outpost alive. Will not explain why."
    ),
    knowledge=(
        "- House Aragon politics: the main line, the cadet branches, "
        "the ascension of Lyra Aragon. The crescent moon on deep blue.\n"
        "- Moonfall is hidden for a reason. He will not name the reason.\n"
        "- The standing stones surrounding the outpost are older than "
        "the Annwyn. They hum at certain moons.\n"
        "- House Oban's recent aggressions. Aragon is not directly "
        "involved — he is very clear about this — but Aragon is not "
        "uninformed.\n"
        "- He has a letter. It must never reach the interior of "
        "Moonfall. Do not ask him why."
    ),
    quest_hooks=[
        "Offers the tea. Those who accept are counted. He does not "
        "explain what they are counted for.",
        "Will pay a great deal to have a sealed letter delivered to "
        "Gateway — NOT to the Moonfall interior, on pain of the bearer's "
        "life.",
        "Knows something about the Oban incursion at Carran that "
        "the Laurents do not know.",
    ],
    topics=["the tea", "a sealed letter", "the Oban incursion"],
    scope="annwyn",
)


print("\n=== HARROWGATE NPC ===")

# --- Tova of the Get — Coldhill berserker at the Hall of Bears ---------
get_or_create_npc(
    key="Tova of the Get",
    location=harrowgate,
    desc=(
        "A tall, pale-eyed woman wrapped in furs, a bear-skull pauldron "
        "on her shoulder, a two-handed axe across her back. Her hair is "
        "the color of winter wheat, braided with bear teeth. Scars down "
        "both forearms in deliberate parallel lines."
    ),
    personality=(
        "Tova, sworn of the Get of Ursin, Lady Thora Coldhill's "
        "berserker retinue. Taciturn, cold-eyed, smells faintly of "
        "bear-grease and woodsmoke. Norse-cadenced speech when she uses "
        "it. Respects a strong hand and a straight word; has no patience "
        "for clever tongues. Loyal to the Get, the Hall, and the Bear "
        "— in that order."
    ),
    knowledge=(
        "- The Get of Ursin: Coldhill berserker cult, sworn to the "
        "bear-spirit. Ritual scarring, communal rites.\n"
        "- Lady Thora Coldhill, mistress of Harrowgate. The Hale "
        "bloodline, far-north Norse register.\n"
        "- The Great Bears of the northern woods. One is dying. The "
        "Get have not yet decided what to do.\n"
        "- Werewolves have been seen in the southern forests. These "
        "are not the same as her bears and she is quietly insulted "
        "that anyone confuses them.\n"
        "- She knows three oaths. She will recite none of them to "
        "strangers."
    ),
    quest_hooks=[
        "Will wrestle any challenger for a test of worth. Winning "
        "earns a Get-token; losing earns bruises.",
        "The dying Great Bear needs a successor cub tracked and "
        "brought back. Dangerous work. Pays in Hale silver and "
        "standing with the Get.",
        "Would carry word south to Mystvale for a traveler going her "
        "way, if their oath rings true.",
    ],
    topics=["wrestling challenge", "the Great Bear's cub", "carry word south"],
    scope="annwyn",
)


print("\n=== CARRAN NPC ===")

# --- Ser Ewan Bannon — Bannon lieutenant at the barracks ---------------
get_or_create_npc(
    key="Ser Ewan Bannon",
    location=bannon_barracks,
    desc=(
        "A broad-shouldered knight in Bannon black, the drake sigil on "
        "his chest, short-cropped hair going silver at the temples. "
        "Carries a training blunt rather than a live blade — he's just "
        "come off the drill yard. Commanding voice, used sparingly."
    ),
    personality=(
        "Ser Ewan Bannon, lieutenant to Arch Magistrat Symon Bannon of "
        "the Carran garrison. Disciplined, decent, exhausted. Treats his "
        "drillmasters well, his knights fairly, and his magistrat "
        "honestly. Takes his oath to the crown seriously — even now, "
        "with the crown murdered. Has a three-year-old daughter he has "
        "not seen in a season. Speaks plainly; Celtic-Welsh cadence."
    ),
    knowledge=(
        "- The Bannon garrison at Carran: three score knights, two "
        "score men-at-arms, archers from the royal levy.\n"
        "- Arch Magistrat Symon Bannon drills the knights himself. "
        "Ewan handles the men-at-arms.\n"
        "- Crow raids on Laurent caravans: increasing in frequency, "
        "and there are patterns that suggest inside knowledge.\n"
        "- The succession crisis back home after King Giles's murder. "
        "The Bannons are split three ways. He tries not to discuss it.\n"
        "- Laurent-Bannon tensions: subtle. Both houses hold Carran, "
        "both want it to themselves. Ewan navigates this daily."
    ),
    quest_hooks=[
        "Recruiting hunters to track Crow raiders — silver per head, "
        "proofs returned.",
        "Needs a message carried to his family in the Sovereignlands. "
        "Wax-sealed, heartfelt, priority one.",
        "If the player shows knowledge of the Crows' inner circles, "
        "Ewan will pay for ALL of it, and protect the source.",
    ],
    topics=["Crow hunters", "a family letter", "Crow intelligence"],
    scope="annwyn",
)


print("\n=== GOLDLEAF NPC ===")

# --- Keena Innis — healer-scout at the Innis encampment ---------------
get_or_create_npc(
    key="Keena Innis",
    location=goldleaf,
    desc=(
        "A wiry, freckled woman in a leaf-green Innis cloak, her braid "
        "coming loose from a long walk. A bow across her back, a "
        "herbalist's pouch at her hip, dirt under her nails. Her smile "
        "is sharp, her eyes are sharper."
    ),
    personality=(
        "Keena Innis, scout and healer of the Goldleaf encampment. Irish-"
        "Celtic lilt. Sharp-tongued, herbal-handed, doesn't suffer fools "
        "for so much as a heartbeat. Loyal to Innis blood above all. "
        "Dislikes the Aurorym. Dislikes the Richter more. Has good humor "
        "once you've proved you have teeth. Is watching you now."
    ),
    knowledge=(
        "- House Innis politics: the main line, the hidden settlements, "
        "the reasons for hiding. The Crow connection, which she will "
        "neither confirm nor deny.\n"
        "- Scout routes through the Annwyn that the Richter have not "
        "mapped and will not.\n"
        "- Healing herbs of the Annwyn — including three varieties that "
        "do not exist in Arnesse and are very, very useful.\n"
        "- The Innis are not fond of the Aurorym. Not one bit. Ask "
        "about the Godslayers for a stream of quiet, poetic fury.\n"
        "- She will not speak a word of Branwen Innish in Gateway to "
        "strangers. Possibly not even to friends."
    ),
    quest_hooks=[
        "Will brew a salve for any wound, in exchange for a favor — "
        "never coin.",
        "Knows paths through the forest to Mystvale, Arcton, and "
        "Tamris that halve the travel time. Will show one, for the "
        "right kind of word.",
        "If the player invokes House Innis or the Northern Marches "
        "with real knowledge, Keena's whole posture changes. Good or "
        "bad? Depends on the knowledge.",
    ],
    topics=["a healing salve", "forest paths", "House Innis"],
    scope="annwyn",
)


print("\n=== HERBALIST NPC ===")

# --- Thalia the Herbalist — reagent vendor at the Herbalist's Garden -----
thalia = get_or_create_npc(
    key="Thalia the Herbalist",
    location=herbalist_garden,
    desc=(
        "A tall, sun-browned woman in an earth-stained apron, dark hair "
        "swept back under a wide-brimmed hat. Her fingers are perpetually "
        "green from herb-work and she smells of crushed sage and chamomile. "
        "A leather satchel at her hip bulges with dried bundles; behind "
        "her, rows of carefully labeled jars line a wooden shelf."
    ),
    personality=(
        "Thalia the Herbalist, Apotheca-affiliated gatherer and reagent "
        "seller in the Herbalist's Garden at Mystvale. Patient with "
        "novices, knowledgeable about every herb in the Annwyn and most "
        "from Arnesse. Speaks with a warm, unhurried cadence — 'the "
        "plants have their own time, and so should we.' Refuses to sell "
        "poisons openly — she will claim ignorance if asked about "
        "Thornwood Fern or Death's Head Cap. Will discuss medicinal "
        "properties, growing conditions, and reagent combinations freely."
    ),
    knowledge=(
        "- She sells common and uncommon reagents from her garden stock. "
        "Players use |wherbs|n to see her wares and |wbuy herb <name>|n "
        "to purchase.\n"
        "- Common herbs (3 silver each): Black Salt, Celandine, Distilled "
        "Spirits, Dragon's Eye, Gold Lotus, Hollyrue, Luminesce, Mandrake, "
        "Merchant's Leaf, Orgonnian Grapes, Phosphorous, Sayge, Verbaena, "
        "Willow Root.\n"
        "- Uncommon herbs (8 silver each): Amber Lichen, Blood Medallion, "
        "Creeper Moss, Crypt Moss, Duskland Rose, Ergot Seeds, Harrowdust, "
        "Red Lotus, Tarkathi Poppy, Thornwood Fern, Widow's Petal, "
        "Wintercrown, Wraith Orchid.\n"
        "- She is Apotheca-trained and knows the properties of every "
        "reagent, though she will not discuss poison recipes unprompted.\n"
        "- The Herbalist's Garden was established by the first settlers "
        "of Mystvale. The greenhouse protects rare Annwyn species."
    ),
    quest_hooks=[
        "Will explain the alchemy system to newcomers — how to brew, "
        "what kits you need, where to find a workbench.",
        "Looking for someone to gather rare herbs from deeper in the "
        "Annwyn — pays in reagents.",
        "Knows about Marta the Alchemist's plight with the Crows and "
        "is anxious for news of her rescue.",
    ],
    topics=["herbs", "reagents", "the Apotheca"],
    scope="annwyn",
)
# Set up Thalia's reagent shop inventory
thalia.attributes.add("reagent_shop", {
    # Common herbs (3 silver each)
    "Black Salt": 3, "Celandine": 3, "Distilled Spirits": 3,
    "Dragon's Eye": 3, "Gold Lotus": 3, "Hollyrue": 3,
    "Luminesce": 3, "Mandrake": 3, "Merchant's Leaf": 3,
    "Orgonnian Grapes": 3, "Phosphorous": 3, "Sayge": 3,
    "Verbaena": 3, "Willow Root": 3,
    # Uncommon herbs (8 silver each)
    "Amber Lichen": 8, "Blood Medallion": 8, "Creeper Moss": 8,
    "Crypt Moss": 8, "Duskland Rose": 8, "Ergot Seeds": 8,
    "Harrowdust": 8, "Red Lotus": 8, "Tarkathi Poppy": 8,
    "Thornwood Fern": 8, "Widow's Petal": 8, "Wintercrown": 8,
    "Wraith Orchid": 8,
})

print("\n=== EXTENDED NPC ROSTER COMPLETE ===")


# ===========================================================================
# CROW CAMP ENEMY NPCs — Rescue the Crafters quest chain (Event 1)
# Combat NPCs using dedicated typeclasses with AI combat logic.
# ===========================================================================
print("\n=== CROW CAMP ENEMIES ===")


def get_or_create_enemies(key, typeclass_path, location, desc, count=1):
    """Create or preserve *count* hostile combat NPCs with the same key at
    a given location. Idempotent: if enough already exist, skip creation;
    if too few, create the remainder; if too many (from manual spawns),
    leave the extras alone."""
    existing = list(ObjectDB.objects.filter(
        db_key=key, db_location=location.pk,
        db_typeclass_path=typeclass_path,
    ))
    # Refresh desc + locks on every existing NPC
    for npc in existing:
        npc.db.desc = desc
        npc.locks.add("get:false();puppet:false()")
    need = count - len(existing)
    if need <= 0:
        print(f"  EXISTS  : {key} x{len(existing)} (in {location.key})")
        return existing[:count]
    created = []
    for _ in range(need):
        npc = _create.create_object(typeclass_path, key=key, location=location)
        npc.db.desc = desc
        npc.locks.add("get:false();puppet:false()")
        created.append(npc)
    print(f"  CREATED : {key} x{need} → {location.key} (had {len(existing)})")
    return existing + created


_CROW_STRIKER_DESC = (
    "A lean, scarred fighter in patchwork leather, a black crow "
    "feather tied to one arm. Eyes like a cornered dog — vicious "
    "and calculating. Armed and hostile."
)
_CROW_BRUISER_DESC = (
    "A hulking brute in a battered iron breastplate, broad as a doorframe. "
    "A heavy two-handed weapon rests on one shoulder. The crow feathers "
    "braided into his beard are stiff with dried blood."
)

# --- Crow Camp — Blacksmith's Prison: 3x Striker, 1x Bruiser ---
get_or_create_enemies("Crow Striker", "typeclasses.npc.CrowStriker",
                      crow_camp_blacksmith, _CROW_STRIKER_DESC, count=3)
get_or_create_enemies("Crow Bruiser", "typeclasses.npc.CrowBruiser",
                      crow_camp_blacksmith, _CROW_BRUISER_DESC, count=1)

# --- Crow Camp — Fox Den: 3x Striker, 2x Bruiser ---
get_or_create_enemies("Crow Striker", "typeclasses.npc.CrowStriker",
                      crow_camp_fox, _CROW_STRIKER_DESC, count=3)
get_or_create_enemies("Crow Bruiser", "typeclasses.npc.CrowBruiser",
                      crow_camp_fox, _CROW_BRUISER_DESC, count=2)

# --- Crow Camp — Owl's Roost: 3x Striker, 2x Bruiser, 1x Cale ---
get_or_create_enemies("Crow Striker", "typeclasses.npc.CrowStriker",
                      crow_camp_owl, _CROW_STRIKER_DESC, count=3)
get_or_create_enemies("Crow Bruiser", "typeclasses.npc.CrowBruiser",
                      crow_camp_owl, _CROW_BRUISER_DESC, count=2)
get_or_create_enemies(
    "Cale the Thorn", "typeclasses.npc.CaleTheThorn",
    crow_camp_owl,
    "A wiry, sharp-featured man in worn but well-fitted leather armor, "
    "a steel blade at his hip. An owl-feather cloak hangs from his "
    "shoulders. He moves with the ease of a trained swordsman — every "
    "step deliberate, every glance appraising. A jagged scar runs from "
    "his left ear to his jawline. He does not look like a man who loses.",
    count=1,
)


# ===========================================================================
# RESCUED CRAFTER NPCs — dialogue NPCs at each camp, quest givers for
# the subsequent quests in the chain.
# ===========================================================================
print("\n=== RESCUED CRAFTER NPCs ===")

torben = get_or_create_npc(
    key="Torben the Blacksmith",
    location=crow_camp_blacksmith,
    desc=(
        "A broad-shouldered, middle-aged man with soot-stained hands and "
        "a bruised face. His leather apron is torn, his wrists rubbed raw "
        "from rope. Despite his injuries, there is iron in his bearing — "
        "a craftsman who bends metal, not his back."
    ),
    personality=(
        "Torben the Blacksmith, Mystvale's master smith. Stoic, grateful, "
        "deeply worried about his spouse Marta who was taken to a different "
        "camp. Speaks in short, earnest sentences. Strong hands, stronger "
        "will. Calls his rescuer 'friend' from the first word."
    ),
    knowledge=(
        "- Was kidnapped from the Crafter's Quarter by Crow raiders three "
        "days ago. They wanted him to forge weapons.\n"
        "- His spouse Marta, an alchemist, was taken to a second camp "
        "called the Fox Den — he overheard guards talking about it.\n"
        "- A young artificer named Fenn was taken to a third camp deeper "
        "along the Old Road.\n"
        "- The Crows are not ordinary bandits — they have leadership, "
        "supplies, and inside knowledge of Mystvale's defenses.\n"
        "- Once rescued, he will set up shop in the Crafter's Quarter "
        "and forge for the settlement."
    ),
    quest_hooks=[
        "Begs the player to rescue his spouse Marta from the Fox Den.",
        "Will offer his smithing services for free once he returns to "
        "Mystvale.",
        "Knows details about the Crow organization that Ser Ewan Bannon "
        "would pay for.",
    ],
    topics=["the Crows", "the other captives", "crafting"],
    scope="annwyn",
)

marta = get_or_create_npc(
    key="Marta the Alchemist",
    location=crow_camp_fox,
    desc=(
        "A wiry, exhausted woman with herb-stained fingers and dark "
        "circles under sharp, intelligent eyes. Her apothecary's satchel "
        "has been emptied and its contents scattered across the camp. "
        "She sits with the careful stillness of someone conserving every "
        "ounce of energy."
    ),
    personality=(
        "Marta the Alchemist, Torben's spouse. Quick-minded, dry-humored "
        "even in captivity, fierce when it comes to her craft and her "
        "family. Speaks precisely — an herbalist's habit of naming things "
        "exactly. Relieved beyond words to be rescued."
    ),
    knowledge=(
        "- Was forced to brew poisons for the Crows. Sabotaged what she "
        "could — diluted doses, substituted inert herbs.\n"
        "- A young artificer named Fenn is held at the Owl's Roost, the "
        "biggest camp, run by a Crow lieutenant called Cale the Thorn.\n"
        "- Cale is dangerous — a trained fighter, not a common thug. He "
        "answers to someone called 'the Old Badger.'\n"
        "- Her recipe scroll was taken but not destroyed — it should "
        "still be in the camp somewhere.\n"
        "- Once free, she will set up an apothecary in Mystvale.\n"
        "- She sells recipe schematics to alchemists: |wbrowse recipes|n "
        "to see what she has, |wbuy recipe <name>|n to purchase. She "
        "also sells a few common reagents: |wherbs|n to see stock."
    ),
    quest_hooks=[
        "Tells the player about Fenn at the Owl's Roost and urges them "
        "to finish what they started.",
        "Offers reagents as thanks — Sayge and Blackthorn from her "
        "personal stores.",
        "Warns about Cale the Thorn — he is no ordinary bandit leader.",
    ],
    topics=["the Crows", "the other captives", "crafting"],
    scope="annwyn",
)
# Marta sells a few common reagents
marta.attributes.add("reagent_shop", {
    "Sayge": 4, "Distilled Spirits": 4, "Dragon's Eye": 4,
})
# Marta sells Level 1 recipe scrolls (all apotheca, poison, drug)
marta.attributes.add("recipe_shop", {
    "RECIPE_ANAMNESIS_DECOCTION": 8,
    "RECIPE_BLADE_OIL": 8,
    "RECIPE_BLADE_SALVE": 8,
    "RECIPE_BULLS_DECOCTION": 8,
    "RECIPE_CATS_EYES": 8,
    "RECIPE_CATS_PAW": 8,
    "RECIPE_CUBS_DECOCTION": 8,
    "RECIPE_DUELISTS_DECOCTION": 8,
    "RECIPE_EAGLE": 8,
    "RECIPE_INNISS_SERUM": 8,
    "RECIPE_LILLYWHITE": 8,
    "RECIPE_MOONBREW": 8,
    "RECIPE_PIT_FIGHTERS_ELIXIR": 8,
    "RECIPE_PURITY_DECOCTION": 8,
    "RECIPE_SPOTTERS_DRAUGHT": 8,
    "RECIPE_VERDANT_DECOCTION": 8,
    "RECIPE_WHITE_ROLANDS_SERUM": 8,
    "RECIPE_BRIDGITS_REVENGE": 8,
    "RECIPE_CUTTER": 8,
    "RECIPE_SPICE": 8,
    "RECIPE_STARDUST": 8,
})

fenn = get_or_create_npc(
    key="Fenn the Artificer",
    location=crow_camp_owl,
    desc=(
        "A young, gangly man barely out of his apprenticeship, with "
        "clever hands and a nervous, darting gaze. His artificer's "
        "tools have been confiscated but he keeps reaching for his belt "
        "where they used to hang. A bruise darkens one cheekbone."
    ),
    personality=(
        "Fenn the Artificer, the youngest of Mystvale's three crafters. "
        "Eager, earnest, talks too fast when excited or frightened — "
        "which is most of the time right now. Deeply grateful to be "
        "rescued. Already planning what he'll build first when he gets "
        "back to the workshop."
    ),
    knowledge=(
        "- Was captured while gathering materials outside Mystvale. The "
        "Crows wanted him to repair their crossbows.\n"
        "- Overheard Cale receiving orders — the Crow raids are not "
        "random, they are targeting Mystvale's ability to arm itself.\n"
        "- Cale keeps a bundle of intelligence documents in his command "
        "tent — patrol routes, supply caches, orders from 'the Old "
        "Badger.'\n"
        "- Once free, he will open an artificer's workshop in Mystvale "
        "for kits, locks, and clothing."
    ),
    quest_hooks=[
        "Grateful beyond measure — will craft the player a free kit "
        "once he returns to Mystvale.",
        "Has information about the Crow command structure that could "
        "help Ser Ewan Bannon plan a counteroffensive.",
        "Knows the 'Old Badger' is not in the Annwyn — the orders "
        "come from across the Mists.",
    ],
    topics=["the Crows", "the other captives", "crafting"],
    scope="annwyn",
)

# ===========================================================================
# CRAFTER SCHEMATIC SHOPS — rescued crafters sell their trade's schematics
# once they're back in Mystvale. The recipe_shop attribute is what
# `browse recipes` / `buy recipe` look for.
# ===========================================================================

# Torben the Blacksmith — sells all Blacksmith schematics
torben.attributes.add("recipe_shop", {
    "SCHEMATIC_IRON_SMALL_WEAPON": 9,
    "SCHEMATIC_IRON_MEDIUM_WEAPON": 9,
    "SCHEMATIC_IRON_LARGE_WEAPON": 9,
    "SCHEMATIC_IRON_SHIELD": 9,
    "SCHEMATIC_IRON_CHAIN_SHIRT": 9,
    "SCHEMATIC_IRON_COAT_OF_PLATES": 9,
    "SCHEMATIC_IRON_PLATEMAIL": 9,
    "SCHEMATIC_LEATHER_ARMOR": 9,
    "SCHEMATIC_HARDENED_IRON_SMALL_WEAPON": 15,
    "SCHEMATIC_HARDENED_IRON_MEDIUM_WEAPON": 15,
    "SCHEMATIC_HARDENED_IRON_LARGE_WEAPON": 15,
    "SCHEMATIC_HARDENED_IRON_SHIELD": 15,
    "SCHEMATIC_HARDENED_IRON_CHAIN_SHIRT": 15,
    "SCHEMATIC_HARDENED_IRON_COAT_OF_PLATES": 15,
    "SCHEMATIC_HARDENED_IRON_PLATE_ARMOR": 15,
    "SCHEMATIC_HARDENED_LEATHER_ARMOR": 15,
    "SCHEMATIC_IMPROVED_LEATHER_ARMOR": 24,
    "SCHEMATIC_STEEL_SMALL_WEAPON": 24,
    "SCHEMATIC_STEEL_MEDIUM_WEAPON": 24,
    "SCHEMATIC_STEEL_LARGE_WEAPON": 24,
    "SCHEMATIC_STEEL_SHIELD": 24,
    "SCHEMATIC_STEEL_CHAIN_SHIRT": 24,
    "SCHEMATIC_STEEL_COAT_OF_PLATES": 24,
    "SCHEMATIC_STEEL_PLATE_ARMOR": 24,
    "SCHEMATIC_MASTERWORK_STEEL_SMALL_WEAPON": 36,
    "SCHEMATIC_MASTERWORK_STEEL_MEDIUM_WEAPON": 36,
    "SCHEMATIC_MASTERWORK_STEEL_LARGE_WEAPON": 36,
    "SCHEMATIC_MASTERWORK_STEEL_SHIELD": 36,
    "SCHEMATIC_MASTERWORK_STEEL_CHAIN_SHIRT": 36,
    "SCHEMATIC_MASTERWORK_STEEL_COAT_OF_PLATES": 36,
    "SCHEMATIC_MASTERWORK_STEEL_PLATE_MAIL": 36,
    "SCHEMATIC_MASTERWORK_LEATHER_ARMOR": 36,
    "SCHEMATIC_PATCH_KIT": 15,
    "SCHEMATIC_REVIVICATOR": 15,
})

# Fenn the Artificer — sells all Artificer schematics
fenn.attributes.add("recipe_shop", {
    # Kits (Level I)
    "SCHEMATIC_APOTHECARY_KIT": 15,
    "SCHEMATIC_ARTIFICER_KIT": 15,
    "SCHEMATIC_BLACKSMITH_KIT": 15,
    "SCHEMATIC_BOWYER_KIT": 15,
    "SCHEMATIC_CHIRURGEON_KIT": 15,
    "SCHEMATIC_GUNSMITH_KIT": 15,
    "SCHEMATIC_LOCKPICKING_KIT": 15,
    "SCHEMATIC_RESURRECTIONISTS_KIT": 15,
    # Clothing & garb (Level I)
    "SCHEMATIC_CLOTH_GAMBESON": 15,
    "SCHEMATIC_FINE_CLOTHING": 15,
    "SCHEMATIC_PEASANTS_GARB": 15,
    "SCHEMATIC_NOBLES_GARB": 15,
    "SCHEMATIC_HIGHWAYMAN_CLOAK": 15,
    "SCHEMATIC_DUELIST_GLOVES": 15,
    "SCHEMATIC_LIGHT_BOOTS": 15,
    "SCHEMATIC_STALWART_BOOTS": 15,
    "SCHEMATIC_CRAFTSMANSHIP_TOOLS": 15,
    "SCHEMATIC_BASIC_LOCK": 15,
    # Level II
    "SCHEMATIC_FINE_DUELISTS_GLOVES": 24,
    "SCHEMATIC_HUNTERS_BOOTS": 24,
    "SCHEMATIC_LORDLY_CLOTHING": 24,
    "SCHEMATIC_MAGNIFICENT_CLOTHING": 24,
    "SCHEMATIC_PLAGUISTS_CASQUE": 24,
    "SCHEMATIC_QUALITY_LOCK": 24,
    "SCHEMATIC_SHADOW_MANTLE": 24,
    "SCHEMATIC_SWORDDANCERS_BOOTS": 24,
    "SCHEMATIC_TRADESMENS_GARMENTS": 24,
    # Level III
    "SCHEMATIC_DARK_SILK_CLOAK": 36,
    "SCHEMATIC_EXQUISITE_CLOTHING": 36,
    "SCHEMATIC_KNIGHTS_BOOTS": 36,
    "SCHEMATIC_MASTER_DUELISTS_GLOVES": 36,
    "SCHEMATIC_MASTERWORK_LOCK": 36,
    "SCHEMATIC_PROFESSIONALS_VESTMENTS": 36,
    "SCHEMATIC_RAIMENT_OF_HIGH_LORD": 36,
    "SCHEMATIC_THIEFS_BOOTS": 36,
})

# ---------------------------------------------------------------------------
# Laszlo the Bowyer — a Cirque-trained fletcher who took up residence in
# the Crafter's Quarter after the rescue, filling the gap Mystvale has
# always had. Sells all four Bowyer schematics.
# ---------------------------------------------------------------------------
laszlo = get_or_create_npc(
    key="Laszlo the Bowyer",
    location=crafter_quarter,
    desc=(
        "A lean man past his prime with knotted forearms and fingers "
        "yellowed by pine-pitch. A quiver of half-made shafts rides his "
        "hip; shavings cling to his leather vest. He squints like a man "
        "who has spent his life measuring angles."
    ),
    personality=(
        "Laszlo, a Cirque-trained fletcher who drifted into Mystvale "
        "after the rescue and decided the Crafter's Quarter needed a "
        "bow-maker. Patient, precise, sparing of words. Proud of his "
        "work, skeptical of archers who cannot describe the grain of "
        "their own bow."
    ),
    knowledge=(
        "- Yew, ash, and hornbeam: when to cure, when to glue, when to "
        "abandon the stave and start again.\n"
        "- Arrows by the ten: hunting broadheads, war bodkins, blunts "
        "for children's practice. He stocks schematics for all of it.\n"
        "- Sells bow and arrow schematics to anyone with coin and the "
        "Bowyer trade: |wbrowse recipes|n to view, |wbuy recipe "
        "<name>|n to purchase.\n"
        "- Will repair a warped stave for five silver if the fletcher "
        "who made it does not take it personally."
    ),
    quest_hooks=[
        "Looking for a source of Thornwood yew — the Crows burned his "
        "last stockpile.",
        "Will appraise any bow a player brings him.",
    ],
    topics=["bows", "arrows", "crafting", "schematics"],
    scope="annwyn",
)
laszlo.attributes.add("recipe_shop", {
    "SCHEMATIC_BOW": 15,
    "SCHEMATIC_ARROWS": 15,
    "SCHEMATIC_LONGBOW": 24,
    "SCHEMATIC_MASTERWORK_BOW": 36,
})

# ---------------------------------------------------------------------------
# Kriegsmeister Holst — Ironhaven's Richter gunsmith, the Annwyn's only
# legitimate source of firearm schematics. Sells at list price. Visits to
# his forge are logged; the Hardingers notice who buys what.
# ---------------------------------------------------------------------------
holst = get_or_create_npc(
    key="Kriegsmeister Holst",
    location=ironhaven_forge,
    desc=(
        "A short, barrel-chested Richter in a powder-stained apron, his "
        "beard singed black at the tip. An oiled pistol hangs in a "
        "custom holster at his chest — not for show; he built it. One "
        "eye is clouded white and does not blink when he fixes you with "
        "the other."
    ),
    personality=(
        "Holst, master gunsmith of House Richter and the Hardingers' "
        "preferred hand for anything that goes bang. Gruff, proud of "
        "his craft, deeply loyal to the House. Courteous to paying "
        "customers; brisk with tire-kickers. Suspicious of Mystvale "
        "accents after the Crows' last raid."
    ),
    knowledge=(
        "- Under House Richter writ, the Ironhaven Forge is the only "
        "legal source of firearms and firearm schematics in the "
        "Annwyn. Sales are logged.\n"
        "- Sells the full Gunsmith schematic line: crude pistols up "
        "through masterwork. |wbrowse recipes|n to view, |wbuy recipe "
        "<name>|n to purchase.\n"
        "- Has opinions about the Rourkes that he will not share with "
        "strangers — he knows powder is moving along the coast without "
        "Hardinger seals.\n"
        "- Teaches by hand; pay for the schematic, come back for the "
        "lesson when you have the skill."
    ),
    quest_hooks=[
        "Will pay for information on unlicensed gunrunners operating "
        "near Mystvale.",
        "Needs a courier to deliver a sealed shipment to Hardinger's "
        "Hall.",
    ],
    topics=["firearms", "schematics", "House Richter", "the Rourkes"],
    scope="annwyn",
)
holst.attributes.add("recipe_shop", {
    "SCHEMATIC_CRUDE_PISTOL": 24,
    "SCHEMATIC_BASIC_PISTOL": 24,
    "SCHEMATIC_BULLETS": 15,
    "SCHEMATIC_MASTERWORK_PISTOL": 36,
})

# ---------------------------------------------------------------------------
# Magpie — a Rourke smuggler who fences the same gunsmith schematics out
# of the Back Alley at a steep discount. No paperwork, no questions, no
# guarantee the Hardingers won't hear about it later.
# ---------------------------------------------------------------------------
magpie = get_or_create_npc(
    key="Magpie",
    location=black_market,
    desc=(
        "A wiry figure in a patched oilskin, hood always up even "
        "indoors. A silver ring glints on one thumb; the other hand "
        "stays out of sight. Smells of salt, gun oil, and something "
        "sweeter — dreamsmoke, maybe. Smiles like it costs nothing."
    ),
    personality=(
        "Magpie, a Rourke fence who runs powder and paper out of the "
        "Back Alley. Cheerful, quick-tongued, lethal if the conversation "
        "turns. Treats every transaction like a joke whose punchline "
        "only they know. Will call the buyer 'friend' until the coin "
        "lands."
    ),
    knowledge=(
        "- The Rourkes move firearms the Hardingers would rather stay "
        "in Ironhaven. Magpie fences the schematics on consignment.\n"
        "- Sells the Gunsmith line at a discount off Kriegsmeister "
        "Holst's list price: |wbrowse recipes|n to view, |wbuy recipe "
        "<name>|n to deal. No receipts, no questions.\n"
        "- Hears things at the docks nobody else does — what ships "
        "came in under whose flag, what didn't get inspected.\n"
        "- Would rather not meet the Kriegsmeister face to face. Not "
        "out of fear — out of mutual understanding."
    ),
    quest_hooks=[
        "Has schematics the Ironhaven Forge won't sell to outsiders, "
        "at a price.",
        "Looking for a runner to move a sealed crate north without "
        "attracting Richter attention.",
    ],
    topics=["firearms", "smuggling", "the Rourkes", "the docks"],
    scope="annwyn",
)
magpie.attributes.add("recipe_shop", {
    "SCHEMATIC_CRUDE_PISTOL": 18,
    "SCHEMATIC_BASIC_PISTOL": 18,
    "SCHEMATIC_BULLETS": 11,
    "SCHEMATIC_MASTERWORK_PISTOL": 27,
})


# ===========================================================================
# CANON TAGS — wire each AI NPC to relevant canon files in world/canon/.
# Tags: house:foo, faction:bar, region:baz. The canon loader matches
# overlap and includes those entries in the NPC's system prompt.
# Idempotent: re-tagging an existing NPC just rewrites the attribute.
# ===========================================================================
print("\n=== CANON TAGGING ===")

_NPC_CANON_TAGS = {
    # Gateway — Arnesse-side
    "Sergeant Hollet Kross":       ["house:richter", "house:bannon", "vigil"],
    "Crane":                       ["mistwalker"],
    "Soap":                        ["mistwalker"],
    "Pelham Faye":                 ["region:vale", "cirque"],
    "Branwen Innish":              ["house:innis", "region:northern_marches", "cirque"],
    "Old Mae":                     ["region:hearthlands", "region:midlands"],
    "Brother Alaric":              ["aurorym", "house:blayne"],
    "Lissa the Scribe":            ["cirque", "region:midlands"],
    "Kriegsmann Volkan":           ["house:richter", "house:varga", "region:dusklands"],
    "Serena of Scrow":             ["region:hearthlands"],
    "Mab the Gambler":             ["cirque"],
    "Rhys of the Thornwood":       ["region:thornwood", "house:innis", "house:laurent"],
    "Old Threnody":                ["cirque"],
    "Obed the Docker":             ["region:northern_marches", "region:breakwater"],
    "Rin":                         ["region:hearthlands"],
    "Pip":                         ["region:hearthlands"],
    "Cerys":                       ["mistwalker"],
    "Matron Hegga the Quartermaster": ["house:richter", "region:hearthlands", "cirque"],

    # Mystvale (annwyn-scope)
    "Auron Maxan":                 ["aurorym", "vellatora", "house:laurent"],
    "Hemi the Cirque":             ["cirque"],
    "Clerk Yevan":                 ["house:laurent", "house:bannon"],
    "Ser Brand Ironhand":          ["house:richter", "house:laurent", "region:hearthlands"],
    "Mistress Cael the Artificer": ["cirque", "region:midlands"],

    # Settlement specialists (annwyn-scope)
    "Ser Hartwig Richter":         ["house:richter", "house:hardinger", "house:aragon"],
    "Gerta Ironblood":             ["house:richter", "region:dusklands"],
    "Ser Dormund Corveaux":        ["house:corveaux", "house:innis", "house:aragon"],
    "Marta Falconer":              ["house:corveaux"],
    "Heron Aragon":                ["house:aragon", "house:oban"],
    "Tova of the Get":             ["house:hale", "house:coldhill", "region:everfrost"],
    "Ser Ewan Bannon":             ["house:bannon", "house:laurent"],
    "Keena Innis":                 ["house:innis", "region:northern_marches"],

    # Rescued Crafters (Event 1 quest chain)
    "Torben the Blacksmith":       ["region:annwyn"],
    "Marta the Alchemist":         ["region:annwyn"],
    "Thalia the Herbalist":        ["region:annwyn"],
    "Fenn the Artificer":          ["region:annwyn"],

    # Schematic vendors
    "Laszlo the Bowyer":           ["region:annwyn", "cirque"],
    "Kriegsmeister Holst":         ["house:richter", "house:hardinger", "region:annwyn"],
    "Magpie":                      ["house:rourke", "region:annwyn"],
}

_tagged = 0
for npc_key, tags in _NPC_CANON_TAGS.items():
    for npc in ObjectDB.objects.filter(db_key=npc_key):
        npc.attributes.add("canon_tags", tags)
        _tagged += 1
print(f"  Tagged {_tagged} NPCs with canon entries.")


# ===========================================================================
# TAVYL DEALER — Mab the Gambler runs the canonical Eldritch tavern game.
# ===========================================================================
print("\n=== TAVYL DEALER ===")
for mab in ObjectDB.objects.filter(db_key="Mab the Gambler"):
    mab.attributes.add("tavyl_dealer", True)
    mab.attributes.add("tavyl_stake", 1)  # 1 silver per seat
    # Augment her AI knowledge so she can talk about the game in character.
    existing_knowledge = mab.attributes.get("ai_knowledge", default="") or ""
    if "tavyl" not in existing_knowledge.lower():
        mab.attributes.add("ai_knowledge", existing_knowledge + (
            "\n- TAVYL is the canonical tavern card game of Arnesse — born "
            "from a plague tale of the lost hamlet of Tavylen, where "
            "magisters cured the dying. The object: be the last alive "
            "after the Pestilence comes through the Fate deck. Every "
            "player starts with a Bonesman to defend; play action cards "
            "(Seeress, Raven, Resurrection, Veiled Lady, Assassin, Trader, "
            "Knight, Merchant, King) to outmaneuver opponents.\n"
            "- She runs a table at the Broken Oar. Stake: 1 silver to "
            "sit. Winner takes the pot.\n"
            "- Players sit with: |wtavyl sit mab|n. From there: "
            "|wtavyl hand|n, |wtavyl play <card>|n, |wtavyl draw|n, "
            "|wtavyl status|n, |wtavyl leave|n."
        ))
    print(f"  Tagged {mab.key} as Tavyl dealer.")


# ===========================================================================
# ATMOSPHERIC SERMON TICKER — Brother Alaric preaches to Gateway Square
# every ~10 minutes via Evennia's script system. Only fires when he is
# actually in the room, so moving him elsewhere silences it cleanly.
# ===========================================================================
print("\n=== SERMON TICKER ===")
from evennia.scripts.models import ScriptDB
_existing_sermon = ScriptDB.objects.filter(
    db_key="sermon_script", db_obj=gateway_square.pk,
).first()
if _existing_sermon:
    print("  EXISTS  : sermon_script on Gateway Square")
else:
    from evennia import create_script
    create_script("typeclasses.scripts.SermonScript", obj=gateway_square)
    print("  ATTACHED: SermonScript → Gateway Square (10-min interval)")


# ===========================================================================
# GATEWAY QUARTERMASTER — merchant with beginner-friendly stock so new
# players can practice browsing/buying/selling BEFORE the crossing.
# Also a talkable AI NPC so players can ask about the wares and world.
# ===========================================================================
print("\n=== GATEWAY QUARTERMASTER ===")

_existing_qm = ObjectDB.objects.filter(
    db_key="Matron Hegga the Quartermaster",
    db_location=gateway_square.pk,
    db_typeclass_path="typeclasses.objects.Merchant",
).first()
if _existing_qm:
    qm = _existing_qm
    print("  EXISTS  : Matron Hegga the Quartermaster")
else:
    qm = _create.create_object(
        "typeclasses.objects.Merchant",
        key="Matron Hegga the Quartermaster",
        location=gateway_square,
    )
    print("  CREATED : Matron Hegga the Quartermaster → Gateway Square")

qm.aliases.add("hegga")
qm.aliases.add("matron")
qm.aliases.add("quartermaster")
qm.db.desc = (
    "A broad, iron-haired woman behind a planked trestle table, a "
    "leather ledger open in front of her and a small trunk of coin at "
    "her feet. Quartermaster's brass pin at her collar, Richter-grey "
    "wool coat over Hearthlander linens. A posted slate behind her "
    "reads, in chalk: |wNo writ? Pay cash. No cash? Walk on.|n"
)
# Stock: beginner-weight gear at Gateway prices (Compact takes a cut).
# All keys verified against world/prototypes.py.
qm.db.shop_inventory = [
    "IRON_SMALL_WEAPON",      # short sword / dagger
    "IRON_MEDIUM_WEAPON",     # arming sword
    "IRON_SHIELD",            # shield
    "LEATHER_ARMOR",          # body armor
    "LIGHT_BOOTS",            # footwear
    "FINE_CLOTHING",          # under-layer
    "HIGHWAYMAN_CLOAK",       # cloak slot
    "PATCH_KIT",              # healing kit for medicine/chirurgery
    "BOW",                    # ranged option
    "ARROWS",                 # ammunition
]
qm.db.shop_text = (
    "|430Browse|n her wares, |430buy|n what you need, |430sell|n what "
    "you've outgrown. |xNo writ? Pay cash. No cash? Walk on.|n"
)
# Give her an AI personality so `ask hegga` works — she's gruff, useful,
# and patient with newcomers.
qm.attributes.add("ai_personality", (
    "Matron Hegga, quartermaster of the Gateway Compact-licensed "
    "market-stall, forty years of haggling under her belt. Hearthlander "
    "by birth, Richter by trade license. Blunt, warm underneath, has no "
    "patience for grifters and infinite patience for newcomers who ask "
    "what something is for. Calls everyone 'love' or 'bearer' "
    "interchangeably. Will point a fool at the right tool without "
    "charging extra for the pointing."
))
qm.attributes.add("ai_knowledge", (
    "- She sells: small and medium iron weapons, an iron shield, "
    "leather armor, light boots, fine clothing (an under-layer), a "
    "highwayman's cloak, a patch kit for healing, a bow and arrows. "
    "Buy cheap, buy twice — she says this often.\n"
    "- Prices are fair by Gateway standards, which is to say "
    "outrageous by Highcourt standards. The Compact takes a cut of "
    "every transaction at the palisade.\n"
    "- How to use what she sells: a small weapon is one-handed, a "
    "medium is one-and-a-half. A shield off-hands. Leather armor "
    "beats nothing, and nothing is what most newcomers wear.\n"
    "- The command for her kiosk: |wbrowse matron|n lists her goods "
    "with prices; |wbuy <item> from matron|n purchases one for silver; "
    "|wsell <item> to matron|n takes your unwanted gear for half-value.\n"
    "- Currency is silver. Bearers arrive with a Compact-issued "
    "purse of 25 silver — enough for boots and a knife, or a hunk "
    "of armor, or a healer's kit. Budget.\n"
    "- Does not sell food. 'The Oar feeds you. I arm you.'\n"
    "- Will not sell Annwyn artefacts or 'mistwalked' goods on "
    "principle. She has standards."
))
qm.attributes.add("ai_quest_hooks", [
    "Will advise a newcomer on what gear to start with based on their "
    "plans (melee, archer, caster).",
    "Can take consignment of salvaged gear for half value paid out "
    "weekly, if they trust you.",
    "Heard the Richter quartermaster at the palisade has been selling "
    "seconds as first-line Richter issue. She'd pay for proof.",
])
qm.attributes.add("ai_scope", "gateway")


# ===========================================================================
# SPECIALIST MERCHANTS IN MYSTVALE — contextual to their craft. Each
# one stocks prototype keys relevant to their discipline, filtered
# from prototypes.py by craft_source.
# ===========================================================================
print("\n=== MYSTVALE SPECIALIST MERCHANTS ===")


def get_or_create_merchant(key, location, desc, inventory, shop_text,
                           ai_personality, ai_knowledge, ai_quest_hooks,
                           ai_scope="annwyn", aliases=()):
    """Create or refresh a Merchant NPC with AI-driven dialogue."""
    existing = ObjectDB.objects.filter(
        db_key=key, db_location=location.pk,
        db_typeclass_path="typeclasses.objects.Merchant",
    ).first()
    if existing:
        m = existing
        print(f"  EXISTS  : {key} (in {location.key})")
    else:
        m = _create.create_object(
            "typeclasses.objects.Merchant", key=key, location=location,
        )
        print(f"  CREATED : {key} → {location.key}")
    m.db.desc = desc
    m.db.shop_inventory = list(inventory)
    m.db.shop_text = shop_text
    m.attributes.add("ai_personality", ai_personality)
    m.attributes.add("ai_knowledge", ai_knowledge)
    m.attributes.add("ai_quest_hooks", list(ai_quest_hooks))
    m.attributes.add("ai_scope", ai_scope)
    for alias in aliases:
        m.aliases.add(alias)
    return m


# --- Ser Brand Ironhand — blacksmith at Mystvale Crafter's Quarter -----
get_or_create_merchant(
    key="Ser Brand Ironhand",
    location=crafter_quarter,
    desc=(
        "A heavy-set blacksmith in soot-blackened leathers, arms like "
        "ship-cables, a hammer tucked through his belt and a ledger "
        "tucked under his arm. Coals glow red-orange behind him in the "
        "forge. A rack of finished weapons gleams under oiled rags, "
        "priced in neat chalk on a slate."
    ),
    inventory=[
        # Level 0 — starter iron
        "IRON_SMALL_WEAPON",
        "IRON_MEDIUM_WEAPON",
        "IRON_LARGE_WEAPON",
        "IRON_SHIELD",
        "LEATHER_ARMOR",
        "IRON_CHAIN_SHIRT",
        "IRON_COAT_OF_PLATES",
        "IRON_PLATEMAIL",
        # Level I — hardened iron
        "HARDENED_IRON_SMALL_WEAPON",
        "HARDENED_IRON_MEDIUM_WEAPON",
        "HARDENED_IRON_SHIELD",
        "HARDENED_LEATHER_ARMOR",
        "PATCH_KIT",
    ],
    shop_text=(
        "|430Browse|n the racks; |430buy|n what you'll take into the Annwyn; "
        "|430sell|n broken gear for what it's worth in scrap."
    ),
    ai_personality=(
        "Ser Brand Ironhand, master blacksmith of Mystvale's Crafter's "
        "Quarter. Broad-shouldered, gruff, honest. Hearthlander accent. "
        "Knighted in his youth for battlefield repairs; he still wears "
        "the ser out of pride. Will quote the Eldritch smith-song before "
        "a hammer-stroke. Respects a customer who knows their steel; "
        "loses patience with anyone who asks for 'a sword, a nice one.'"
    ),
    ai_knowledge=(
        "- He works blacksmith-line gear: iron and hardened iron weapons "
        "(small, medium, large), iron shields, and iron-through-plate "
        "armor. Steel tier is available by commission only (takes a "
        "tenday).\n"
        "- Prices are set by the Compact ledger — no haggling, but "
        "honest prices. Armor repair is included if it breaks while "
        "the buyer holds warranty.\n"
        "- Patch Kits temporarily restore armor material value — every "
        "new bearer should carry one.\n"
        "- Iron shield breaks on the first Sunder. Hardened iron takes "
        "two. Steel takes three. Plan accordingly.\n"
        "- Will not sell Legacy-tier gear. Those are schematic work, "
        "and the schematic-holder names the price."
    ),
    ai_quest_hooks=[
        "Will commission a specific steel weapon for a buyer — delivery "
        "in a tenday, price set in advance.",
        "Needs a trusted courier to fetch a barrel of Richter-quality "
        "iron ingots from Ironhaven — pays well.",
        "Knows which Ironhaven smiths are passing off seconds as first-"
        "line. Would reward proof.",
    ],
    aliases=("brand", "blacksmith", "smith", "ironhand"),
)


# --- Mistress Cael the Artificer — kits and clothing at Marketplace ---
get_or_create_merchant(
    key="Mistress Cael the Artificer",
    location=marketplace,
    desc=(
        "A precise, middle-aged woman at a wooden stall beneath an "
        "oiled-linen awning. Her hair is tied up with brass pins; her "
        "long fingers work calmly at a set of brass dividers while she "
        "watches the crowd. A tray of kits — apothecary, artificer, "
        "bowyer, chirurgeon's — sits under a glass cover."
    ),
    inventory=[
        # Artificer Level I — kits and clothing
        "ARTIFICER_KIT",
        "APOTHECARY_KIT",
        "BLACKSMITH_KIT",
        "BOWYER_KIT",
        "GUNSMITH_KIT",
        "AURON_KIT",
        "CHIRURGEON_KIT",
        "LIGHT_BOOTS",
        "STALWART_BOOTS",
        "FINE_CLOTHING",
        "HIGHWAYMAN_CLOAK",
        "DUELIST_GLOVES",
    ],
    shop_text=(
        "|430Browse|n her kits and garments; |430buy|n what fits the life "
        "you mean to lead; |430sell|n her anything Compact-stamped."
    ),
    ai_personality=(
        "Mistress Cael, master artificer of the Cirque's Mystvale branch. "
        "Midlands-born, trained in Highcourt before the Day of Mist. "
        "Speaks in measured clauses, precise as her instruments. Charges "
        "fair but will not bargain — 'my work is worth what my work is "
        "worth, bearer.' Warm underneath if you show you understand "
        "craftsmanship."
    ),
    ai_knowledge=(
        "- She stocks Level I artificer goods: kits for every crafting "
        "discipline (apothecary, artificer, blacksmith, bowyer, gunsmith, "
        "auron, chirurgeon), and tier-I clothing/boots/cloaks/gloves.\n"
        "- Kits are PREREQUISITES — a blacksmith without a Blacksmith "
        "Kit cannot forge; an apothecary without an Apothecary Kit "
        "cannot brew. Each kit is good for 10 uses.\n"
        "- Clothing confers passive benefits at check-in — Highwayman's "
        "Cloak grants Espionage; Fine Clothing grants silver; Noble's "
        "Garb grants Influence. A character can only benefit from one "
        "type at a time.\n"
        "- Boots: Light Boots resist Stagger/Stun. Stalwart Boots resist "
        "Cleave. One pair per bearer.\n"
        "- Duelist's Gloves give a Resist against Disarm or Sunder."
    ),
    ai_quest_hooks=[
        "Will commission a specific kit for a buyer if stock runs low.",
        "Is quietly looking for an apprentice; patient enough to teach "
        "a promising artificer.",
        "Heard that a legacy cloak has surfaced in the Back Alley. "
        "Would pay to know the truth of it.",
    ],
    aliases=("cael", "artificer", "mistress"),
)


# ===========================================================================
# TRAVELER'S PRIMER — in-world tutorial book placed at the Broken Oar.
# Explains the essential commands new arrivals need to practice before
# they cross. Players can `look primer` or `look book` to read it.
# ===========================================================================
print("\n=== TRAVELER'S PRIMER ===")

_primer = ObjectDB.objects.filter(
    db_key="traveler's primer", db_location=gateway_tavern.pk,
).first()
if _primer:
    # Upgrade the typeclass if the primer was created earlier as a
    # plain Object — the new TravelersPrimer subclass auto-opens
    # the React modal on look.
    target_tc = "typeclasses.objects.TravelersPrimer"
    if (_primer.db_typeclass_path or "") != target_tc:
        try:
            _primer.swap_typeclass(target_tc, run_start_hooks="all")
            print("  UPGRADED: traveler's primer typeclass → TravelersPrimer")
        except Exception as exc:
            print(f"  WARN    : primer typeclass swap failed: {exc}")
    print("  EXISTS  : traveler's primer")
else:
    _primer = _create.create_object(
        "typeclasses.objects.TravelersPrimer",
        key="traveler's primer",
        location=gateway_tavern,
    )
    print("  CREATED : traveler's primer → The Broken Oar")

_primer.aliases.add("primer")
_primer.aliases.add("book")
_primer.locks.add("get:true();drop:true()")
_primer.db.desc = (
    "|y═══════════════════════════════════════════════════════|n\n"
    "|y       A TRAVELER'S PRIMER — GATEWAY EDITION|n\n"
    "|y═══════════════════════════════════════════════════════|n\n"
    "|xPublished by the Mistwalker Compact for the use of bearers|n\n"
    "|xawaiting passage through the Mists.|n\n\n"
    "|wGETTING AROUND|n\n"
    "  |ylook|n                — describe where you stand\n"
    "  |ylook <thing>|n        — study an object or person\n"
    "  |ynorth|n, |ysouth|n, |yeast|n, |ywest|n  — walk through an exit\n"
    "  |yout|n, |yin|n, |yup|n, |ydown|n       — other directions\n\n"
    "|wSPEAKING WITH OTHERS|n\n"
    "  |ysay <words>|n         — speak aloud to the room\n"
    "  |yemote <action>|n      — perform a gesture or action\n"
    "  |yask <npc> <question>|n — ask an NPC a question\n"
    "  |yfarewell <npc>|n      — end a conversation\n"
    "  |ywhisper <target>=<msg>|n — private speech\n\n"
    "|wYOUR THINGS|n\n"
    "  |yinventory|n           — list what you carry\n"
    "  |yget <item>|n          — pick something up\n"
    "  |ydrop <item>|n         — put it down\n"
    "  |ygive <item> to <whom>|n — hand something over\n"
    "  |yequip <item>|n        — wear or wield\n"
    "  |yunequip <item>|n      — take it off\n\n"
    "|wBUYING AND SELLING|n\n"
    "  |ybrowse <merchant>|n   — see a merchant's wares and prices\n"
    "  |ybuy <item> from <merchant>|n — purchase for silver\n"
    "  |ysell <item> to <merchant>|n  — sell for half value\n\n"
    "  |xTry this at Matron Hegga's stall in Gateway Square.|n\n\n"
    "|wUNDERSTANDING YOURSELF|n\n"
    "  |ysheet|n               — see your character sheet\n"
    "  |ystatus|n              — quick health check\n"
    "  |ywho|n                 — who's currently playing\n"
    "  |yhelp <topic>|n        — game help on any subject\n\n"
    "|wWHEN YOU CROSS|n\n"
    "  |xThe Mistwalker Soap guides bearers through at the Mistwall. "
    "Your Writ of Safe Conduct must be lit before she will let you "
    "through — a game master will approve your passage when they have "
    "reviewed your build. Until then, wander, practice, and prepare.|n\n\n"
    "|y═══════════════════════════════════════════════════════|n\n"
    "|xSigned, Crane, Registrar of the Gateway Crossing Office|n\n"
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
