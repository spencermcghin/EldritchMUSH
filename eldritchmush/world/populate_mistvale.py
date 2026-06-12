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
# CANON LOCATION MIGRATION — Event 1 Rescue the Crafters
# Per source plot: Marta the Alchemist is held at Owl's Roost; Fenn the
# Artificer (and Cale the Thorn) are held at Fox Den. Earlier builds had
# this swapped. Move any existing NPCs to their canon-correct rooms so
# live DBs converge without spawning duplicates.
# ===========================================================================
print("\n=== CRAFTER LOCATION MIGRATION ===")
_CRAFTER_CANON_ROOMS = {
    "Marta the Alchemist": "Crow Camp — Owl's Roost",
    "Fenn the Artificer":  "Crow Camp — Fox Den",
    "Cale the Thorn":      "Crow Camp — Fox Den",
}
for npc_key, correct_room_key in _CRAFTER_CANON_ROOMS.items():
    correct_room = ObjectDB.objects.filter(
        db_key=correct_room_key,
        db_typeclass_path__contains="rooms",
    ).first()
    if not correct_room:
        print(f"  SKIP    : '{npc_key}' — target room '{correct_room_key}' not found yet")
        continue
    for npc in ObjectDB.objects.filter(
        db_key=npc_key, db_typeclass_path__startswith="typeclasses.npc",
    ):
        if npc.db_location_id == correct_room.pk:
            continue
        old_room = npc.db_location
        old_key = old_room.db_key if old_room else "<nowhere>"
        # If a duplicate already exists at the correct room (prior partial
        # migration run), delete this stale copy.
        dup = ObjectDB.objects.filter(
            db_key=npc_key, db_location=correct_room.pk,
            db_typeclass_path__startswith="typeclasses.npc",
        ).exclude(id=npc.id).first()
        if dup:
            print(f"  DELETE  : stale '{npc_key}' at '{old_key}' (canon copy exists at '{correct_room_key}')")
            npc.delete()
        else:
            print(f"  MOVE    : '{npc_key}'  '{old_key}' → '{correct_room_key}'")
            npc.db_location = correct_room
            npc.save()


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
    "Dusklander porters warm their hands at a brazier without speaking. "
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
    "The banners of the Mistguard — House Richter's iron hammer "
    "quartered with House Bannon's gold tower on crimson — hang from "
    "a central post, water-"
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

dawnhaven = get_or_create_room(
    "Dawnhaven",
    "typeclasses.rooms.Room",
    "An Aurorym war camp ten miles north of Mystvale — Vellatora knights "
    "in white tabards, banks of canvas tents, and a circle of stone where "
    "a sacred flame burns day and night. The camp is still half-built, "
    "and winter is closing in. Sister Mariel leads the morning rites; "
    "the rest of the faithful pray, drill, and dig.\n\n"
    "Back |wsouth|n to Mystvale North Gate.",
    zone="Annwyn",
)

shrine_of_lirit = get_or_create_room(
    "The Shrine of Lirit",
    "typeclasses.rooms.Room",
    "A glade of pale birch rings a low, mossed cairn of bone and river-"
    "stone — the Shrine of Lirit, older than any chantry in the Vale. "
    "Pilgrims have tied ribbons to the lower branches, their prayers "
    "written on strips of birch-bark. The air hums, and the ribbons "
    "move when there is no wind. Further into the Thornwood through "
    "the narrow deer-path north.\n\n"
    "Back |wsouth|n to the Thornwood Edge.",
    zone="Annwyn",
)

first_expedition_camp = get_or_create_room(
    "First Expedition Camp",
    "typeclasses.rooms.Room",
    "A ring of leather tents half-collapsed under moss. Cold fire-pits, "
    "scattered Laurent colors, and a single standing banner of House "
    "Laurent — the stag rampant — still flying above the ruin. Bodies "
    "have been moved. Whoever's left is hiding or worse. "
    "Deep in the Thornwood — no safe way out save back the way you came.\n\n"
    "Back |wsouth|n to the Shrine of Lirit.",
    zone="Annwyn",
)

the_butchers_hovel = get_or_create_room(
    "The Butcher's Hovel",
    "typeclasses.rooms.Room",
    "A sagging wooden hut hidden deeper in the Thornwood, roof thatched "
    "with something that is not straw. Hooks hang from the rafters. A "
    "cold firepit at the center shows bones picked clean. Something "
    "big waits in the back room.\n\n"
    "Back |wsouth|n to First Expedition Camp.",
    zone="Annwyn",
)

thornwood_edge = get_or_create_room(
    "The Thornwood Edge",
    "typeclasses.rooms.Room",
    "The Old Road peters out into a hedge of pine and briar where the "
    "Thornwood begins. A few sticks have been lashed together at the "
    "tree line — tied with sinew and tufts of hair, crowned with a "
    "bird's skull. The wind is wrong here, and it smells of rain "
    "even when the sky is clear.\n\n"
    "Back to |wThe Old Road — South|n.",
    zone="Annwyn",
)

mystvale_training_yard = get_or_create_room(
    "Mystvale Training Yard",
    "typeclasses.rooms.Room",
    "A hard-packed yard hedged in by a timber palisade. Straw-stuffed "
    "training dummies stand in a ragged row, and at the far end a line "
    "of archery targets catches the wind. The yard is named for the "
    "fencing master Meyer, whose strike-diagrams are chalked on a "
    "weathered board under the eave. The drillmaster stands near the "
    "board with an expectant eye — this is where newcomers prove they "
    "know which end of a weapon to hold.\n\n"
    "Back to |wMystvale Square|n.",
    zone="Mystvale",
)

mystvale_square = get_or_create_room(
    "Mystvale Square",
    "typeclasses.rooms.Room",
    "The heart of Mystvale — a broad cobbled square ringed by weathered stone "
    "buildings and timber shopfronts. A stone well stands at its center, ringed "
    "by the scars of old mist-sickness and recent siege. The banners of House "
    "Laurent's Stag Hall fly alongside the colors of the Burgomaster's office. "
    "Merchants hawk their wares near the marketplace, while the smell of the "
    "forge drifts in from the Crafter's Quarter.\n\n"
    "Exits lead to |wSongbird's Rest|n, the |wMarketplace|n, the |wCrafter's Quarter|n, "
    "the |wTown Hall|n, |wManor Row|n to the north, the |wsouth gate|n, and the "
    "|wnorth gate|n.",
    zone="Mystvale",
)

aentact = get_or_create_room(
    "Songbird's Rest",
    "typeclasses.rooms.Room",
    "Songbird's Rest is Mystvale's tavern, council chamber, and beating heart. "
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
    "A vast open-fronted forge where Dusklander smiths in Richter livery "
    "work day and night. Great bellows pump at the main hearth; lesser "
    "forges line the walls. The heat is oppressive. The smiths move in "
    "practiced silence, "
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
link(mystvale_square, "training",  mystvale_training_yard, "out",   "train", "o")
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
# Reverse from Old Road South back to Carran: the canonical 'south'
# direction is already taken by the Mistgate, so we add a named
# one-way exit "carran" (alias c) so players who came up from Carran
# via 'north' can type 'carran' to head back. Carran's own 'north'
# exit (created by the link above) handles the outbound direction.
if not ObjectDB.objects.filter(
    db_key="carran", db_location=old_road_south.pk
).exists():
    _carran_back = _create.create_object(
        "evennia.objects.objects.DefaultExit",
        key="carran", location=old_road_south, destination=carran_square,
    )
    _carran_back.aliases.add("c")
    print("  CREATED : Old Road South — 'carran' (back to Carran Square)")
link(old_road_south, "southwest", ironhaven_square, "northeast", "sw", "ne")
link(old_road_south, "east",      arcton_camp, "west", "e", "w")
link(old_road_south, "thornwood",  thornwood_edge, "out", "thorn", "o")
# Event 2 Thornwood chain — Thornwood Edge leads deeper in:
#   Thornwood Edge → Shrine of Lirit → First Expedition Camp → Butcher's Hovel
link(thornwood_edge, "north",       shrine_of_lirit, "south", "n", "s")
link(shrine_of_lirit, "north",      first_expedition_camp, "south", "n", "s")
link(first_expedition_camp, "north", the_butchers_hovel, "south", "n", "s")

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
# Aurorym pilgrim camp ten miles north of Mystvale (Event 3).
link(north_gate, "dawnhaven", dawnhaven, "south", "dawn", "s")
link(forest_road, "north", harrowgate, "south", "n", "s")

# ── Foreign-house outposts (orphan-room fix) ─────────────────────────
# Goldleaf (House Innis) and Moonfall (House Aragon) are foreign
# encampments that were previously seeded with no exits at all,
# making them unreachable. Hook each into the nearest road room so
# they're on the map and curious players can find them.
# - Goldleaf Innis Encampment branches off the Forest Road north of
#   Mystvale (Innis lands are in the Northern Marches; this is a
#   forward outpost in Bannon territory).
# - Moonfall Aragon Outpost branches off the Old Road South (Aragon
#   is rumoured to be the hidden hand behind the Crows; an outpost
#   off the south road fits).
link(forest_road,    "encampment", goldleaf, "road",   "encamp", "back")
link(old_road_south, "outpost",    moonfall, "road",   "out",    "back")

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
    # Canon: Marta the Alchemist is held at the Owl's Roost;
    # unlocked by accepting rescue_alchemist.
    old_road_south, "owl camp", crow_camp_owl, "out", "owl", "o",
    required_quest="rescue_alchemist",
    gate_message="|400You don't know where the Owl's Roost is. The camp letter from the first raid should tell you.|n",
)
quest_gated_link(
    # Canon: Fenn the Artificer (and Cale the Thorn) are held at the
    # Fox Den; unlocked by accepting rescue_artificer.
    forest_road, "fox camp", crow_camp_fox, "out", "fox", "o",
    required_quest="rescue_artificer",
    gate_message="|400The Fox Den is well-hidden, run by the Crow lieutenant Cale the Thorn. You'll need directions from someone who's been there.|n",
)

# Tamris ruins interior (accessed from Carran SW or Ironhaven W)
link(tamris_approach, "in", tamris_ruins, "out", None, "o")
# Harbor is on the coast SOUTH of the approach. Earlier this used
# east/west, but tamris_approach.east was already taken by the
# Ironhaven link a few lines up, so the link() helper silently
# skipped and the harbor ended up one-way. Use south/north pair,
# both free on these rooms, and the geography is correct.
link(tamris_approach, "south", tamris_harbor, "north", "s", "n")
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
# Traversal is open to anyone who finished chargen — the chargen
# approval flow is the only gate we need. The walk-in quest IS the
# journey through the mists, so blocking it here makes the new-player
# flow feel broken. Older deploys had a `traverse: approval_status`
# lock; we strip it on every seed pass so re-runs converge.
_mists_exit = ObjectDB.objects.filter(
    db_key="through the mists", db_location=mistwall.pk
).first()
if not _mists_exit:
    _mists_exit = _create.create_object(
        "typeclasses.exits.WalkInMistsExit",
        key="through the mists", location=mistwall, destination=mistgate,
    )
    _mists_exit.aliases.add("mists")
    _mists_exit.aliases.add("cross")
    print("  CREATED : Mistwall → Mistgate (walk-in routed crossing)")
else:
    # Re-runs: ensure the existing exit uses the walk-in-aware class so
    # at_traverse routes by chosen flavor instead of always landing
    # at Mistgate.
    if _mists_exit.typeclass_path != "typeclasses.exits.WalkInMistsExit":
        _mists_exit.swap_typeclass(
            "typeclasses.exits.WalkInMistsExit", clean_attributes=False
        )
        print("  RETYPED : Mistwall crossing → WalkInMistsExit")

# Strip the legacy approval_status lock so every chargen-finished
# player can cross. Reset to a fresh permissive traverse rule.
_mists_exit.locks.add("traverse:all()")
_mists_exit.db.err_traverse = ""
print("  OPEN    : Mistwall crossing (no approval gate; walk-in routed)")

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
# REDIRECT THE CHARGEN ROOM TO GATEWAY SQUARE (where the Herald
# at the Gates is standing with offers in hand). The Herald's
# walk-in quests fire automatically as a quest_offer OOB event the
# moment a new puppet's at_after_move hook runs in this room — so
# the player's first frame post-chargen is the parchment Quest
# Offer modal asking "From the Mists, you arrived... how?". This
# is the only moment when the new-player onboarding is implicit
# rather than requiring the player to guess where to go next.
#
# Gateway Tents stays one step south (atmospheric refugee camp);
# players who want to wander there can do so freely.
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
    # New exit: chargen → Gateway Square (Herald's location).
    if not ObjectDB.objects.filter(
        db_key="in character", db_location=chargen_room.pk
    ).exists():
        ex = _create.create_object(
            "evennia.objects.objects.DefaultExit",
            key="in character",
            location=chargen_room,
            destination=gateway_square,
        )
        ex.aliases.add("ic")
        ex.aliases.add("gateway")
        print(f"  CREATED : ChargenRoom → Gateway Square exit")

# Also ensure limbo (#2) points at Gateway Square — same logic;
# OOC fallback should land somewhere with a clear next-action.
limbo = ObjectDB.objects.filter(id=2).first()
if limbo:
    limbo.db.desc = (
        "A featureless void between worlds. The Mistgate lies to the "
        "|wnorth|n, and beyond it, Gateway Square."
    )
    for ex in limbo.contents:
        if hasattr(ex, "destination") and ex.destination:
            ex.delete()
    if not ObjectDB.objects.filter(db_key="north", db_location=limbo.pk).exists():
        _create.create_object(
            "evennia.objects.objects.DefaultExit",
            key="north", location=limbo, destination=gateway_square,
        )
        print("  CREATED : Limbo → Gateway Square")


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
        "the gold-tower-on-crimson armband of House Bannon sewn on his shoulder to "
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
        "a gold-tower-on-crimson band on his off-shoulder for his "
        "seconded service to the Bannons. Greying beard, missing two "
        "fingers on his left hand, carries a heavy-bladed Dusklander "
        "kriegsmesser at his hip."
    ),
    personality=(
        "Volkan, late fifties, a Varga-born Dusklander now serving out "
        "his years with the Mistguard. Stoic, clipped Germanic speech. "
        "Came up through Varga's household guard, followed silver west "
        "when the Dusklands went quiet. Loyal to coin, then to comrades, "
        "then to the Iron Hammer. Dry humor that surfaces once he's sure "
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
        "iron hammer sigil worked into the chest of his surcoat. Scarred "
        "across the brow, hands broad and callused. Addresses servants "
        "by name. Watches every visitor like a sentry."
    ),
    personality=(
        "Ser Hartwig Richter, third son of a minor Richter line, sworn "
        "to Lord Wilhelm Hardinger's hall. Stern, blunt, Germanic-formal. "
        "Loyal to the Iron Hammer above all. Quietly convinced Hardinger "
        "is the wrong man for Ironhaven's command — the Godslayer "
        "funding has made Hardinger look corrupt, and a Richter should "
        "not look corrupt. Has no patience for flattery and none at all "
        "for fools."
    ),
    knowledge=(
        "- House Richter politics: the senior Deephold line, the "
        "Hardinger cadet branch, the cousins at Gateway. The iron hammer "
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
        "A broad-shouldered knight in Bannon crimson, the gold-tower "
        "sigil on his chest, short-cropped hair going silver at the temples. "
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

# --- Crow Camp — Owl's Roost (rescue_alchemist): 3x Striker, 2x Bruiser ---
get_or_create_enemies("Crow Striker", "typeclasses.npc.CrowStriker",
                      crow_camp_owl, _CROW_STRIKER_DESC, count=3)
get_or_create_enemies("Crow Bruiser", "typeclasses.npc.CrowBruiser",
                      crow_camp_owl, _CROW_BRUISER_DESC, count=2)

# --- Crow Camp — Fox Den (rescue_artificer): 3x Striker, 2x Bruiser, 1x Cale ---
get_or_create_enemies("Crow Striker", "typeclasses.npc.CrowStriker",
                      crow_camp_fox, _CROW_STRIKER_DESC, count=3)
get_or_create_enemies("Crow Bruiser", "typeclasses.npc.CrowBruiser",
                      crow_camp_fox, _CROW_BRUISER_DESC, count=2)
get_or_create_enemies(
    "Cale the Thorn", "typeclasses.npc.CaleTheThorn",
    crow_camp_fox,
    "A wiry, sharp-featured man in worn but well-fitted leather armor, "
    "a steel blade at his hip. A fox-fur cloak hangs from his shoulders. "
    "He moves with the ease of a trained swordsman — every step "
    "deliberate, every glance appraising. A jagged scar runs from his "
    "left ear to his jawline. He does not look like a man who loses.",
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
        "called the Owl's Roost — he overheard guards talking about it.\n"
        "- A young artificer named Fenn was taken to a third camp deeper "
        "along the Old Road.\n"
        "- The Crows are not ordinary bandits — they have leadership, "
        "supplies, and inside knowledge of Mystvale's defenses.\n"
        "- Once rescued, he will set up shop in the Crafter's Quarter "
        "and forge for the settlement."
    ),
    quest_hooks=[
        "Begs the player to rescue his spouse Marta from the Owl's Roost.",
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
    location=crow_camp_owl,
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
        "- A young artificer named Fenn is held at the Fox Den, the "
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
        "Tells the player about Fenn at the Fox Den and urges them "
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
    location=crow_camp_fox,
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


# ===========================================================================
# EVENT 1 WALK-IN HERALD
#
# A non-merchant NPC at Gateway Square who offers the five walk-in quests
# (walkin_ship / cirque / noble / scout / chain_gang). Each walk-in is a
# branching quest — see world/quest_data.py for outcome definitions.
#
# Intentionally simple for now: the Herald is the giver for all five. Later
# passes will seed the supporting NPCs (watch captain, harbormaster, etc.)
# that complete each walk-in's objectives.
# ===========================================================================
print("\n=== EVENT 1 WALK-IN HERALD ===")

herald_key = "Herald at the Gates"
# The herald greets newcomers at Gateway Square — Gateway is the
# Arnesse-side border town where new players arrive before their
# walk-in journey through the Mists takes them to Mystvale. If an
# old deployment had the herald elsewhere, relocate them.
_existing_herald = ObjectDB.objects.filter(db_key=herald_key).first()
if _existing_herald:
    herald = _existing_herald
    if herald.location != gateway_square:
        herald.move_to(gateway_square, quiet=True)
        print(f"  MOVED   : {herald_key} → Gateway Square")
    else:
        print(f"  EXISTS  : {herald_key}")
else:
    herald = _create.create_object(
        "typeclasses.npc.Npc",
        key=herald_key,
        location=gateway_square,
    )
    print(f"  CREATED : {herald_key} → Gateway Square")

herald.aliases.add("herald")
herald.aliases.add("gates")
herald.db.desc = (
    "A weathered crier in Compact colours stands atop a stump by the "
    "gates, voice hoarse from shouting for travellers. A leather satchel "
    "at her hip bulges with letters of introduction, writs of safe "
    "conduct, bills of lading and dogeared contracts. A brass bell hangs "
    "from her belt. She looks you up and down the moment you approach, "
    "already asking — without asking — how you mean to make the crossing."
)
herald.db.is_npc = True
herald.db.is_aggressive = False
# AI personality for `ask herald` dialogue
herald.attributes.add("ai_personality", (
    "A Compact herald posted at Gateway Square to brief travellers "
    "preparing to cross into the Annwyn. Busy, observant, practical. "
    "Believes every crossing has a story worth logging — and that the "
    "way a traveller chooses to cross shapes what they find on the "
    "other side. Offers a choice of five walk-in paths: by ship, with "
    "the Cirque caravan, in a noble retinue, with the Lodge of the "
    "Metaphysical Mind, or as part of a chain gang. The crossing is "
    "ahead, west, through the Mistwall — not behind. She is helping "
    "the bearer plan it, not congratulating them on having survived it."
))
# Topic chips for `ask herald` — curated, one per crossing path so
# the player has obvious entry points without us leaking the raw
# `ai_quest_hooks` text (which is what the fallback would do).
# Clicking any of these fires `ask herald = <topic>`, which runs
# CmdAsk → push_quest_offers_for_npc → inline Accept buttons appear
# in the conversation panel.
herald.attributes.add("ai_quest_topics", [
    "the crossing",
    "the Ship path",
    "the Cirque caravan",
    "the Noble retinue",
    "the Lodge of the Metaphysical Mind",
    "the Chain Gang",
])
herald.attributes.add("ai_knowledge", (
    "- Offers five walk-in crossing-paths the bearer can pick: by "
    "Ship, with the Cirque caravan, in a Noble retinue, as an "
    "Explorer with the Lodge of the Metaphysical Mind, or in a "
    "Chain Gang of prisoners. Each path is a journey through the "
    "Mists with its own dangers and its own moral choices on the "
    "way to Mystvale on the Annwyn side.\n"
    "- Players accept a path by clicking the quest offer modal that "
    "appears when they speak with the Herald, or by typing "
    "|wquest accept <title> / <path>|n.\n"
    "- She does not take sides — she logs crossings. What a "
    "traveller does on their path is their business.\n"
    "\n"
    "HOW TO BEGIN THE CROSSING (always tell the bearer this when "
    "they accept a path or ask how to start):\n"
    "- From Gateway Square, go |wnorth|n to the Mistwalker's Tent, "
    "then |wwest|n to the Mistwall, then |w'through the mists'|n to "
    "begin the crossing. The path they chose will determine where "
    "they emerge.\n"
    "- The Mists are ahead, west, through the Mistwall — not "
    "behind. Gateway is the staging town on the Arnesse side. The "
    "Annwyn (and Mystvale) lie past the crossing.\n"
    "\n"
    "WHAT THE BEARER WILL FACE PER PATH (give a one-line preview):\n"
    "IMPORTANT: she does NOT know what happens INSIDE the Mists or "
    "on the Annwyn side. The Mists swallow most travellers; few "
    "come back. She speaks of each path only from what she has "
    "seen on the Arnesse side (staging in or at Gateway) and the "
    "rumours travellers have brought back. She does NOT name "
    "specific NPCs, rooms, or encounters in the Mists or in "
    "Mystvale — she has never been across and she will not "
    "pretend she has.\n"
    "- SHIP: a merchant captain has chartered a vessel for the "
    "crossing. The bearer will board at the Mistwall. Most such "
    "ships do not arrive; the few that do say the stars over the "
    "Mists are not Arnesse's stars. Rumour speaks of wrecks "
    "washing up on a coast that may or may not be Annwyn.\n"
    "- CIRQUE: the Grand Cirque Obscura has a caravan parked at "
    "the Mistwall right now — she can see it from here. Their "
    "hired Mistwalker never came. The Cirque foreman, Yan, has "
    "been asking for couriers willing to carry their cargo "
    "through. Their merchant on the far side is named in the "
    "contract; the Cirque will reward whoever delivers.\n"
    "- NOBLE: a noble retinue passed through Gateway with a "
    "Mistwalker called Martin and his assistant Wil. Wil came "
    "back to the gate yesterday looking for marks — she does not "
    "trust him and the bearer should know it. The retinue is "
    "waiting for the bearer at a camp past the Mistwall.\n"
    "- EXPLORER: scholars of the Lodge of the Metaphysical Mind "
    "have been answering a summons from Magister Ipwin, who went "
    "into the Mists days ago to study spirit phenomena. Magister "
    "Vell is waiting to make the crossing with the bearer. What "
    "Ipwin has found beyond the Mistwall, she cannot say.\n"
    "- CHAIN GANG: a column of the condemned is chained to a "
    "wagon at the Mistwall waiting for the Last Walk. The "
    "bearer will be one of them. What waits in the woods beyond, "
    "she does not know — no chain gang has ever come back to "
    "tell her."
))

# Quest-offer hook — the actual UI offer modal is fired by
# push_quest_offers_for_npc on `ask`; this string is just the
# system-prompt nudge so the LLM knows the herald can present paths.
# Kept terse so it doesn't surface as a topic chip (chips are
# suppressed via ai_quest_topics=[] above anyway).
herald.attributes.add("ai_quest_hooks", [
    "Can offer one of five crossing-paths to a traveller who has "
    "not yet committed: by ship, with the Cirque caravan, in a "
    "noble retinue, with the Lodge of the Metaphysical Mind, or "
    "in a chain gang."
])

# Ambient mutter lines — the AmbientNpcScript picks one of these at
# random every ~2 min when a player is in the room. Each line is a
# HOOK: it references something the player can ask the Herald about
# (ship, Cirque caravan, chain gang, etc.), nudging quest discovery
# without forcing the player to think to ask.
herald.attributes.add("ambient_lines", [
    "If you're crossing today, see me before you leave. Five paths, one chance.",
    "That Cirque caravan's been parked at the Wall two days now. They'll take a courier if anyone's brave enough.",
    "Chain gang came in this morning. Bad lot. They'll be walked into the Mists by sundown.",
    "Word from the docks: a ship's chartered for the crossing. Captain claims he can find the Annwyn by stars. Sure he can.",
    "The Lodge of the Metaphysical Mind has scholars asking the way to a Magister Ipwin. Went into the Mists days ago.",
    "Noble retinue passed through yesterday. Hired a Mistwalker called Martin. Their assistant Wil's the type I'd not trust with my purse.",
    "Mistwall's open today. Once you're through, you don't come back. Choose your path before you cross.",
])
herald.attributes.add("ambient_cooldown_s", 90)


# ===========================================================================
# EVENT 1 WALK-IN SUPPORTING NPCs + ITEMS
#
# Everything downstream of the Herald that the walk-in quests need:
#   - Quest-giver/receiver NPCs (harbormaster, ringmaster, watch captain,
#     Lady Ysolde, crow agent)
#   - Kill-target NPCs (road bandits, nosy farmhand, jailers, ringleader)
#   - Gather items (wreck manifest, salvage, captain's seal, pendant,
#     sealed/unsealed letter, crow waymark, forged warrant)
#
# Placement is quest-logic-driven; each walk-in has a clear completion
# path without needing to visit more than 2-3 rooms.
# ===========================================================================
print("\n=== EVENT 1 WALK-IN SUPPORTING NPCs ===")


def _ensure_walkin_npc(key, location, desc, aliases=(), aggressive=False,
                       ai_personality=None, ai_knowledge=None,
                       typeclass="typeclasses.npc.Npc", count=1):
    """Idempotent create-or-refresh for walk-in NPC(s).

    If `count` > 1, ensures at least `count` NPCs with the same key exist
    at `location`; creates missing ones to reach the target. Returns the
    first instance (most callers only use one)."""
    existing = list(ObjectDB.objects.filter(
        db_key=key, db_location=location.pk,
    ))
    made = 0
    while len(existing) < count:
        new = _create.create_object(typeclass, key=key, location=location)
        existing.append(new)
        made += 1
    if made:
        print(f"  CREATED : {key} × {made} → {location.key}")
    else:
        suffix = f" (×{count})" if count > 1 else ""
        print(f"  EXISTS  : {key}{suffix}")
    first = existing[0]
    for npc in existing:
        for a in aliases:
            npc.aliases.add(a)
        npc.db.desc = desc
        npc.db.is_npc = True
        npc.db.is_aggressive = aggressive
        if ai_personality:
            npc.attributes.add("ai_personality", ai_personality)
        if ai_knowledge:
            npc.attributes.add("ai_knowledge", ai_knowledge)
    return first


def _ensure_walkin_item(key, location, desc, aliases=(),
                        typeclass="typeclasses.objects.Object", count=1,
                        gettable=True):
    """Idempotent create-or-refresh for quest item(s).

    `count` seeds multiple identical copies (e.g. wreck salvage × 3).
    `gettable=False` marks the item as scenery — visible in the room
    but not pickup-able. Useful for things like signal-fires,
    shrines, paper lanterns, training dummies, scattered tracks: the
    player should be able to look at and reference them but not
    cart them off in their pack.

    Items that drop on a kill / quest-step (Lynden's confession,
    witch's braid) should NOT be created in the room at all — they
    belong on the corpse / get spawned by the kill hook. This helper
    is for items that legitimately exist in the world from the start.
    """
    existing = list(ObjectDB.objects.filter(
        db_key=key, db_location=location.pk,
    ))
    made = 0
    while len(existing) < count:
        new = _create.create_object(typeclass, key=key, location=location)
        existing.append(new)
        made += 1
    if made:
        print(f"  CREATED : item {key} × {made} → {location.key}")
    else:
        suffix = f" (×{count})" if count > 1 else ""
        print(f"  EXISTS  : item {key}{suffix}")
    first = existing[0]
    for obj in existing:
        for a in aliases:
            obj.aliases.add(a)
        obj.db.desc = desc
        if gettable:
            obj.locks.add("get:all()")
        else:
            # Scenery — refuse picks, replace failure with a flavored line.
            obj.locks.add("get:false()")
            obj.db.get_err_msg = (
                f"|y{key.title()} is part of the scene — you can study it, "
                f"but it is not yours to carry off.|n"
            )
    return first


# ── Ship walk-in transit scene (Stars Aren't Right) ─────────────────────────
# Two-room transit scene the ship walk-in plays through before washing
# ashore at Tamris Harbor. Source: the original Event 1 LARP encounter
# "The Stars Aren't Right" by Spencer McGhin — passenger trapped in
# the cargo hold of a doomed vessel; deck where the stars are wrong
# and the crew has vanished. First Mate Nosaj travels with the player
# from the cargo hold all the way to the wreck on the beach.
ship_cargo_hold = get_or_create_room(
    "The Cargo Hold of the Doomed Ship",
    "typeclasses.rooms.Room",
    "A cramped passenger cabin in the belly of a merchant ship — "
    "hammocks slung between rough beams, crates lashed to iron rings, "
    "a few guttering lanterns. The air is thick with tar, salt, and "
    "the sour breath of frightened strangers. Beyond the planks of "
    "the hull, a storm is screaming. Above, you can hear sailors "
    "shouting orders — sometimes. Not always.\n\n"
    "The cabin door is locked from the outside. The captain has the "
    "key. The captain is not down here.\n\n"
    "|540You are passengers, all bound for the Annwyn. You paid "
    "someone for this passage. You are starting to wonder what you "
    "paid for.|n\n\n"
    "|wUp|n the rope ladder, onto the |wdeck|n.",
    zone="The Mists",
)
ship_deck = get_or_create_room(
    "The Doomed Ship's Deck",
    "typeclasses.rooms.Room",
    "Open deck under a sky that is almost — almost — the sky you "
    "remember. The constellations hang in the wrong places. Some of "
    "the stars are colours that have no name. A fog machine of a fog "
    "rolls thick along the rail; the |wship's wheel|n turns slowly on "
    "its own, unattended. There are signs the crew was here moments "
    "ago — a pipe still warm, a half-played hand of Tavyl, a cup of "
    "wine spilled — but the crew is gone. All of them.\n\n"
    "|540The ship is making for the Annwyn. The Annwyn is not where "
    "the captain thought it would be.|n\n\n"
    "|wDown|n into the |wcargo hold|n. |wAshore|n, when the wreck "
    "comes — and it is coming.",
    zone="The Mists",
)

# Connect the two transit rooms.
link(ship_cargo_hold, "deck", ship_deck, "down", "u", "d")
# Use WalkInJourneyExit so Nosaj follows the player through both legs.
for _ex in ship_cargo_hold.contents:
    if getattr(_ex, "destination", None) == ship_deck:
        if _ex.typeclass_path != "typeclasses.exits.WalkInJourneyExit":
            _ex.swap_typeclass(
                "typeclasses.exits.WalkInJourneyExit", clean_attributes=False
            )
for _ex in ship_deck.contents:
    if getattr(_ex, "destination", None) == ship_cargo_hold:
        if _ex.typeclass_path != "typeclasses.exits.WalkInJourneyExit":
            _ex.swap_typeclass(
                "typeclasses.exits.WalkInJourneyExit", clean_attributes=False
            )

# Ashore exit from deck → Tamris Harbor (the wreck on the beach).
# This is the journey's end — Nosaj follows ashore as a survivor too.
_ashore_exit = ObjectDB.objects.filter(
    db_key="ashore", db_location=ship_deck.pk
).first()
if not _ashore_exit:
    _ashore_exit = _create.create_object(
        "typeclasses.exits.WalkInJourneyExit",
        key="ashore", location=ship_deck, destination=tamris_harbor,
    )
    _ashore_exit.aliases.add("beach")
    _ashore_exit.aliases.add("shore")
    print("  CREATED : Ship Deck → Tamris Harbor (wreck)")

# First Mate Nosaj — companion NPC. Hides in a crate at first, follows
# the player out once roused. Source brief: tattered crew costume,
# survived by hiding when the screaming started.
nosaj = _ensure_walkin_npc(
    "First Mate Nosaj", ship_cargo_hold,
    desc=(
        "A wiry man in a tattered ship's crew uniform, hair plastered "
        "to his forehead with sweat and something darker. His name "
        "tag reads NOSAJ. He keeps one hand on the splintered crate "
        "he climbed out of, as if it might hold the only safety left "
        "in the world."
    ),
    aliases=("nosaj", "first mate", "mate"),
    aggressive=False,
    ai_personality=(
        "First Mate Nosaj of the merchant vessel that brought you "
        "into the Mists. Survived the crew's vanishing by hiding in "
        "an empty crate during a smoke break. Twitchy, superstitious, "
        "guilt-ridden — he should have fought, not hidden. Now he "
        "trails the bearer (the player) because he cannot face being "
        "alone again. Speaks in clipped, half-haunted sentences. Known "
        "Eldritch lore: the captain locked them down here on purpose, "
        "the constellations changed mid-voyage, the screams stopped "
        "all at once. Knows the ship was meant to get to the Annwyn "
        "— and instead got somewhere else."
    ),
    ai_knowledge=(
        "- Crew was last heard at 9 PM, then everything went silent.\n"
        "- Captain had the only key to the passenger hold; captain is "
        "now missing.\n"
        "- The constellations on the deck are the wrong ones — Annwyn "
        "stars, not Arnesse stars.\n"
        "- Recommends finding the navigator (whoever they were); the "
        "ship is lost without a chart correction.\n"
        "- Nosaj will follow the bearer because he refuses to be "
        "alone on this ship."
    ),
)
nosaj.attributes.add("is_walkin_companion", True)
nosaj.db.body = 3
nosaj.db.total_body = 3
nosaj.db.av = 0

# Cargo Hold flavor items (lore + atmosphere).
_ensure_walkin_item(
    "captain's logs", ship_cargo_hold,
    desc=(
        "A bound ship's logbook, the leather still salty. The last "
        "entry, written in a shaking hand, reads: 'The stars are "
        "wrong. We are not where the chart says. Tell the passengers "
        "nothing. Whatever knocks at the hull, do not open.'"
    ),
    aliases=("captain log", "log", "logs", "logbook"),
)
_ensure_walkin_item(
    "lookout's small chest", ship_cargo_hold,
    desc=(
        "A small wooden chest belonging to the lookout, jammed under "
        "a hammock. A note tucked inside: 'Got drunk. Hid the door "
        "key somewhere I'll regret. Wine spilled, blood spilled. "
        "Forgive me.' The chest is unlocked."
    ),
    aliases=("lookout chest", "small chest", "chest"),
)
_ensure_walkin_item(
    "wine cup", ship_cargo_hold,
    desc=(
        "A pewter wine cup, half-overturned in the bedding. Old wine "
        "stains and old blood stains share the same boards."
    ),
    aliases=("wine", "cup"),
)

# Ship's Deck flavor items.
_ensure_walkin_item(
    "ship's wheel", ship_deck,
    desc=(
        "The ship's great wheel, abandoned, turning slowly on its own "
        "as if invisible hands were correcting course. There are "
        "fingernail-scratches gouged into the spokes."
    ),
    aliases=("wheel", "ship wheel", "ship's wheel"),
)
_ensure_walkin_item(
    "tavyl deck", ship_deck,
    desc=(
        "A half-played hand of Tavyl cards, fanned out on a sea-chest. "
        "The hands are dealt to four players. Three of those seats "
        "are empty. The cup beside one is still warm."
    ),
    aliases=("cards", "tavyl", "tavyl cards"),
)
_ensure_walkin_item(
    "constellation chart", ship_deck,
    desc=(
        "The ship's navigational chart of the night sky — the Annwyn "
        "skies on one side, Arnesse on the other. The four Annwyn "
        "constellations and their headings (as the captain logged them "
        "before he vanished):\n\n"
        "  |wThe Drowned Crown|n  sits over  |wnorth|n\n"
        "  |wThe Broken Oar|n     sits over  |wsouth|n\n"
        "  |wThe Hollow Tree|n    sits over  |weast|n\n"
        "  |wThe Stag of the Deep|n sits over |wwest|n\n\n"
        "To chart your course, type |wchart <constellation> "
        "<direction>|n for each of the four."
    ),
    aliases=("chart", "constellation chart", "stars"),
    gettable=False,
)

# ── Ship puzzle props ───────────────────────────────────────────────
# Captain's door key — the lookout's hidden spare. Just findable.
_ensure_walkin_item(
    "captain's door key", ship_cargo_hold,
    desc=(
        "A heavy iron key on a hempen loop. Stamped with the captain's "
        "mark. This is the lookout's drunken spare — the one he hid "
        "under the wine-stained floorboards and forgot."
    ),
    aliases=("door key", "spare key", "captain key", "key"),
)

# Three buckets for the hull-plug puzzle. Scenery — they're tracked
# via room state, not as carryable items.
_ensure_walkin_item(
    "three buckets",  ship_cargo_hold,
    desc=(
        "Three sea-buckets in a row by the breached hull: an 8-litre, "
        "a 5-litre, and a 3-litre. The chief engineer's note nailed "
        "above them reads:\n\n"
        "  |w'Patch needs EXACTLY 4 litres of pitch-mix. You have "
        "three buckets and no measure-lines. Figure it out.'|n\n\n"
        "Commands: |wfill <bucket>|n, |wpour <from> <to>|n, "
        "|wempty <bucket>|n, |whelp buckets|n."
    ),
    aliases=("buckets", "the buckets", "8L bucket", "5L bucket",
             "3L bucket", "bucket"),
    gettable=False,
)

# Chief Engineer's syllabus — the knot mapping reference.
_ensure_walkin_item(
    "Chief Engineer's syllabus",  ship_deck,
    desc=(
        "A salt-stained pamphlet from the Chief Engineer, on the rigging "
        "of merchant vessels. The mast-and-knot reference page is dog-"
        "eared:\n\n"
        "  |wMainmast|n   needs a |wbowline|n  (it must not slip under load)\n"
        "  |wForemast|n   needs a |wsheet bend|n  (it joins two ropes)\n"
        "  |wMizzenmast|n needs a |wclove hitch|n (quick, holds against twist)\n"
        "  |wBowsprit|n   needs a |wfigure eight|n (a stopper at the end)\n\n"
        "To re-rig: type |wtie <knot> on <mast>|n at the mast."
    ),
    aliases=("syllabus", "engineer's syllabus", "chief engineer syllabus", "knot guide"),
    gettable=False,
)

# Mast scenery — four labelled posts on the deck.
for _mast in ("mainmast", "foremast", "mizzenmast", "bowsprit"):
    _ensure_walkin_item(
        _mast, ship_deck,
        desc=(
            f"The {_mast}, splintered by the storm, rigging hanging slack. "
            f"It needs the right knot tied at its base before the wind "
            f"picks up again — see the Chief Engineer's syllabus."
        ),
        aliases=(_mast.replace("mast", " mast"),),
        gettable=False,
    )

# ── Attach the puzzle CmdSets to the ship rooms ─────────────────────
# Idempotent: at_cmdset_creation has already been called once per
# server start; adding the same cmdset key again is a no-op.
try:
    from commands.ship_puzzles import (
        BucketPuzzleCmdSet, KnotPuzzleCmdSet, ConstellationPuzzleCmdSet,
    )
    if not ship_cargo_hold.cmdset.has("BucketPuzzleCmdSet"):
        ship_cargo_hold.cmdset.add(BucketPuzzleCmdSet(), persistent=True)
        print("  ATTACHED: BucketPuzzleCmdSet → Cargo Hold")
    if not ship_deck.cmdset.has("KnotPuzzleCmdSet"):
        ship_deck.cmdset.add(KnotPuzzleCmdSet(), persistent=True)
        print("  ATTACHED: KnotPuzzleCmdSet → Deck")
    if not ship_deck.cmdset.has("ConstellationPuzzleCmdSet"):
        ship_deck.cmdset.add(ConstellationPuzzleCmdSet(), persistent=True)
        print("  ATTACHED: ConstellationPuzzleCmdSet → Deck")
except Exception as _exc:
    print(f"  WARN: failed to attach ship puzzle cmdsets: {_exc!r}")


harbormaster = _ensure_walkin_npc(
    "Mystvale Harbormaster", tamris_harbor,
    desc=(
        "A stout man in a salt-stained wool coat, brass harbour-seal on a "
        "chain around his neck, ledger tucked under one arm. He watches "
        "the water more than he watches you."
    ),
    aliases=("harbormaster", "mystvale harbormaster"),
    aggressive=False,
    ai_personality=(
        "The Mystvale harbormaster. Practical, unimpressed, professional. "
        "Logs wreck salvage for Crown tax. Takes reports from "
        "shipwreck survivors if they can produce a manifest."
    ),
)

_ensure_walkin_item(
    "wreck manifest", tamris_harbor,
    desc="A water-warped ship's manifest, bleeding ink but still legible.",
    aliases=("manifest",),
)
_ensure_walkin_item(
    "wreck salvage", tamris_harbor,
    desc="A splintered crate of half-ruined cargo from the wrecked ship.",
    aliases=("salvage", "crate"),
    count=3,
)
_ensure_walkin_item(
    "captain's seal", tamris_harbor,
    desc=(
        "A heavy brass seal, warm to the touch, showing a sigil you cannot "
        "quite focus on. The captain wanted this burned."
    ),
    aliases=("seal", "captain seal"),
)


# ── Cirque walk-in transit scene ────────────────────────────────────────────
# Three-room scripted scene the Cirque walk-in plays through before
# emerging in Mystvale. Source: the original Event 1 LARP encounter
# "Cirque Walk In" by Jessica Sills — the caravan's guide never came,
# supplies are low, the players are pushed forward into the Tangle
# (a memory-stripping forest) carrying four crates of Cirque cargo
# destined for the merchant Eldreth in the Annwyn. On the way they
# meet The Lost (starving, mad), then a Changeling Underwriter who
# sells the trod torch — required to see a ghost bridge over a
# chasm separating the Tangle from the Annwyn.
#
# Yan travels with the player as the Cirque's foreman. The Lost are
# aggressive; the Underwriter is unsettling but transactional.

# --- Remove legacy Cirque props from the old (replaced) flow ---
# Older outcomes (return_alive / cover_up / turn_in) put Eldreth's
# pendant + Nosy Farmhand on the Old Road south. Neither maps to the
# new source-faithful outcomes; sweep them away.
for _legacy_key in ("Nosy Farmhand", "eldreth's pendant"):
    for _legacy in ObjectDB.objects.filter(
        db_key=_legacy_key, db_location=old_road_south.pk
    ):
        _legacy.delete()
        print(f"  DELETED : {_legacy_key} (legacy cirque prop)")

# Ringmaster stays at the Marketplace as the post-walkin delivery target
# for most outcomes (he receives the surviving crates and the report).
ringmaster = _ensure_walkin_npc(
    "The Ringmaster", marketplace,
    desc=(
        "A tall, grey-eyed man in a stained scarlet coat, one hand resting "
        "on the head of a walking-cane topped with a silver jackdaw. The "
        "smell of lamp oil and greasepaint comes off him in waves."
    ),
    aliases=("ringmaster", "the ringmaster"),
    aggressive=False,
    ai_personality=(
        "The Ringmaster of the Grand Cirque Obscura — outwardly warm, "
        "privately ruthless. Values the Cirque's reputation above any "
        "single performer. Accepts delivery of crates from any walk-in "
        "courier the Cirque hired through the Tangle. Will reward "
        "couriers in coin and standing — and remember those who came "
        "back light-handed."
    ),
    ai_knowledge=(
        "- The Cirque hired a Mistwalker to bring four crates of "
        "cargo through to Eldreth in the Annwyn. The guide never "
        "arrived; the cargo was sent through anyway with whatever "
        "couriers the Cirque could find at the gate.\n"
        "- Will accept the crates from the courier on arrival. "
        "Each surviving crate is worth its weight in Cirque favour.\n"
        "- Knows of the Tangle, the Lost, and the Changeling "
        "Underwriter — they are not rumours to the Cirque, they are "
        "expenses."
    ),
)

# Room 1 — the Cirque caravan camp, stalled at the Mistwall.
cirque_camp = get_or_create_room(
    "The Cirque Camp at the Mistwall",
    "typeclasses.rooms.Room",
    "A painted Cirque wagon parked at the very edge of the Mistwall — "
    "the great fog wall rolls past its sideboards in slow grey "
    "currents. A canvas awning, half-collapsed, throws shadow over "
    "four heavy iron-banded |wcrates|n stacked under a watered-down "
    "lamp. The Cirque guide was supposed to meet the caravan here "
    "two days ago. He never came. Supplies are gone. The horses "
    "are nervous.\n\n"
    "|wYan|n, the Cirque's foreman, stands by the crates with a "
    "rolled |wcontract|n in his belt. He is waiting on someone "
    "with the nerve to carry the cargo through.\n\n"
    "|540The Ringmaster's word is plain: the goods reach Eldreth in "
    "the Annwyn or the Cirque's losses come out of the courier's "
    "share.|n\n\n"
    "|wForward|n into |wthe Tangle|n.",
    zone="The Mists",
)

# Room 2 — the Tangle, where the Lost wander.
the_tangle = get_or_create_room(
    "The Tangle",
    "typeclasses.rooms.Room",
    "A forest of black-barked trees that grow in loops and knots, "
    "branches twisting back on themselves until the trail you "
    "walked feels like the trail you'll walk. Your own footprints "
    "from a minute ago lie ahead of you on the path. The lanterns "
    "of the Cirque camp are gone behind you, then gone again, then "
    "gone a third time. Memory feels thin here.\n\n"
    "Two ragged shapes step out of the trees — wide-eyed, "
    "hollow-cheeked, more hunger than person. They look at the "
    "crates you carry the way a starving dog looks at meat.\n\n"
    "|540You will not pass without a transaction. They will give "
    "you the truth — or what passes for it in their mouths — and "
    "they will take a crate, or they will take a body.|n\n\n"
    "|wAhead|n through the loops to the |wunderwriter's pavilion|n.",
    zone="The Mists",
)

# Room 3 — the Underwriter's pavilion.
underwriter_pavilion = get_or_create_room(
    "The Underwriter's Pavilion",
    "typeclasses.rooms.Room",
    "A tall striped pavilion of oiled silk, pitched in the only "
    "clearing in the Tangle that is not somehow a circle. Lanterns "
    "of green and gold glass hang on staves at every corner. A "
    "panel of stretched silk — translucent, faintly luminous — "
    "screens the back third of the tent. Behind it, a |wfigure|n "
    "sits very still at a writing-desk. She is not human, and you "
    "are aware of this before you can name why.\n\n"
    "On the desk in front of the silk: a single short black candle, "
    "an iron-bound ledger, and a |wtrod torch|n on a velvet "
    "cushion. The trod torch is what shows you the bridge across "
    "the chasm that lies beyond this tent. Without it, the chasm "
    "is everything you ever feared the dark was.\n\n"
    "|540The Underwriter does not haggle so much as appraise. The "
    "price is what you can bear to lose.|n\n\n"
    "|wOut|n the back, across the |wghost-bridge|n, to |wMystvale|n.",
    zone="The Mists",
)

# Connect the three scripted rooms; WalkInJourneyExit so companions follow.
link(cirque_camp, "forward", the_tangle, "back", "f", "b")
link(the_tangle, "ahead", underwriter_pavilion, "back", "a", "b")
for _src, _dst in (
    (cirque_camp, the_tangle),
    (the_tangle, cirque_camp),
    (the_tangle, underwriter_pavilion),
    (underwriter_pavilion, the_tangle),
):
    for _ex in _src.contents:
        if getattr(_ex, "destination", None) == _dst:
            if _ex.typeclass_path != "typeclasses.exits.WalkInJourneyExit":
                _ex.swap_typeclass(
                    "typeclasses.exits.WalkInJourneyExit",
                    clean_attributes=False,
                )

# Final exit — pavilion → Mystvale Marketplace. Cutscene narrates the
# chasm crossing using the trod torch.
_pavilion_out = ObjectDB.objects.filter(
    db_key="out", db_location=underwriter_pavilion.pk
).first()
if not _pavilion_out:
    _pavilion_out = _create.create_object(
        "typeclasses.exits.WalkInJourneyExit",
        key="out", location=underwriter_pavilion, destination=marketplace,
    )
    _pavilion_out.aliases.add("bridge")
    _pavilion_out.aliases.add("ghost-bridge")
    _pavilion_out.aliases.add("mystvale")
    print("  CREATED : Underwriter's Pavilion → Mystvale Marketplace (ghost-bridge)")

# --- Yan: Cirque foreman, walks with the player ---
yan = _ensure_walkin_npc(
    "Yan the Cirque Foreman", cirque_camp,
    desc=(
        "A short, weather-leathered man in a Cirque-painted vest, a "
        "fiddle slung across his back like a sword. He has the look of "
        "a man who has counted the same four crates four hundred times "
        "in the past two days and is now going to count them in the "
        "Tangle whether anyone goes with him or not."
    ),
    aliases=("yan", "foreman"),
    aggressive=False,
    ai_personality=(
        "Yan, foreman to the Grand Cirque Obscura's caravan. Practical, "
        "tired, loyal. Has done the Cirque's quiet errands on six "
        "borders. Believes the cargo gets through or the Cirque "
        "starves this winter. Will walk the Tangle himself if no "
        "courier takes the contract. Speaks in short sentences "
        "punctuated by the way performers do — a beat, a glance, the "
        "next line. Carries the |wCirque cargo manifest|n; will let "
        "any new courier sign for the four crates."
    ),
    ai_knowledge=(
        "- The Cirque hired Mistwalker Soap to guide the caravan "
        "through the Tangle. Soap never arrived. They are now two "
        "days late.\n"
        "- The four crates must reach Eldreth — or in her absence, "
        "the Ringmaster at the Mystvale Marketplace.\n"
        "- The Lost wander the Tangle. They are starving and beyond "
        "reasoning. Give them a crate or fight them.\n"
        "- The Changeling Underwriter has a tent past the Lost. She "
        "sells the trod torch needed to cross the chasm out. No "
        "courier crosses without it.\n"
        "- The Cirque will reward the courier per crate delivered."
    ),
)
yan.attributes.add("is_walkin_companion", True)
yan.db.body = 4
yan.db.total_body = 4
yan.db.av = 1
yan.db.melee_weapons = 1

# --- The Lost: aggressive, starving wanderers in the Tangle ---
first_lost = _ensure_walkin_npc(
    "The First Lost", the_tangle,
    desc=(
        "A man — or what is left of a man — in rags that may once have "
        "been a traveller's coat. His eyes will not stop moving and his "
        "hands are wet to the wrists. He cannot remember his own name. "
        "He remembers being hungry."
    ),
    aliases=("first lost", "lost",),
    aggressive=True,
    ai_personality=(
        "One of the Lost — a traveller who tried the Mists without a "
        "guide and has been wandering the Tangle long enough that "
        "name, home, and reason have been peeled away. Only hunger "
        "and a survivor's instinct to stay near the other Lost "
        "remain. Will demand food, then a crate, then a fight. "
        "Bickers with the Second Lost when not threatening anyone."
    ),
    ai_knowledge=(
        "- Knows nothing about himself. Has been hungry for an "
        "indefinite time.\n"
        "- Wants food, or anything that might contain food. A crate "
        "from the Cirque caravan would do.\n"
        "- Will let the courier pass for one crate. Otherwise will "
        "fight to the death."
    ),
)
first_lost.db.body = 3
first_lost.db.total_body = 3
first_lost.db.av = 0
first_lost.db.master_of_arms = 1
first_lost.db.tough = 1
first_lost.db.melee_weapons = 1

second_lost = _ensure_walkin_npc(
    "The Second Lost", the_tangle,
    desc=(
        "A small wiry person in the remains of a labourer's smock, "
        "shoeless, the soles of her feet black with weeks of trail. "
        "She watches the First Lost as much as she watches you. There "
        "is the suggestion of a quarrel between them that the next "
        "missed meal will finish."
    ),
    aliases=("second lost",),
    aggressive=True,
    ai_personality=(
        "The other of the Lost — same fate as the First Lost, but "
        "more suspicious, less direct. Will speak in third-person "
        "fragments. Hungry enough that she will turn on her "
        "companion if a crate is offered and there's a fight over "
        "it. Holds a sharpened bone."
    ),
    ai_knowledge=(
        "- Same as the First Lost: no memory, no name, just hunger.\n"
        "- Watches the First Lost for signs he will eat first.\n"
        "- Will let the courier pass for a crate."
    ),
)
second_lost.db.body = 3
second_lost.db.total_body = 3
second_lost.db.av = 0
second_lost.db.master_of_arms = 1
second_lost.db.tough = 1
second_lost.db.melee_weapons = 1

# --- The Underwriter: changeling merchant in the Pavilion ---
underwriter = _ensure_walkin_npc(
    "The Underwriter", underwriter_pavilion,
    desc=(
        "Behind the silk panel, a tall figure seated very still at a "
        "desk. The candlelight does not quite agree on her shape. "
        "Long fingers, too long. Black eyes that have no white. A "
        "merchant's collar, a scribe's hands, a smile that does not "
        "show teeth. She is taking notes about you in her ledger "
        "while you are still deciding whether to step forward."
    ),
    aliases=("underwriter", "the underwriter", "changeling", "merchant"),
    aggressive=False,
    ai_personality=(
        "The Underwriter — a changeling merchant who has pitched "
        "her pavilion in the Tangle for longer than any human can "
        "remember. Sells the trod torch (required to cross the "
        "ghost-bridge to the Annwyn) and a few other curiosities. "
        "Takes coin, crates, names, favours, oaths, memories. Does "
        "not haggle so much as appraise. Speaks formally, with the "
        "careful courtesy of a creature that has nothing to gain by "
        "rudeness and everything to gain by patience. Calls "
        "everyone 'courier' unless they offer a name."
    ),
    ai_knowledge=(
        "- Sells the trod torch — the only way to see the ghost-bridge "
        "across the chasm at the far edge of the Tangle. Anyone who "
        "tries to cross without it falls into a darkness from which "
        "they do not return.\n"
        "- Standard price: one crate of Cirque cargo, or fifty silver, "
        "or a memory the courier will not miss until later.\n"
        "- Will offer to buy ALL four crates outright for a heavy "
        "purse — a price that exceeds what the Cirque would pay, "
        "and a betrayal the Cirque will remember.\n"
        "- Will let any courier walk through if they cannot pay, but "
        "the chasm will not let them across."
    ),
)
underwriter.db.body = 6
underwriter.db.total_body = 6
underwriter.db.av = 2

# --- Items: Cirque Camp ---
_ensure_walkin_item(
    "Cirque cargo manifest", cirque_camp,
    desc=(
        "A rolled parchment, sealed with the Cirque's jackdaw mark. "
        "It commissions the bearer to carry four crates of Cirque "
        "cargo through the Tangle to Eldreth in the Annwyn — or in "
        "her absence, to the Ringmaster at the Mystvale Marketplace. "
        "Reward: payable per surviving crate. Signed by the "
        "Ringmaster of the Grand Cirque Obscura."
    ),
    aliases=("manifest", "cirque manifest", "contract"),
)
_ensure_walkin_item(
    "Cirque crate", cirque_camp,
    desc=(
        "An iron-banded wooden crate, stamped with the Cirque's "
        "jackdaw. Heavy. It does not rattle. It does not smell. The "
        "Cirque has not told the courier what is inside, and the "
        "courier is expected not to ask."
    ),
    aliases=("crate", "cirque crate"),
    count=4,
)

# --- Items: The Underwriter's Pavilion ---
_ensure_walkin_item(
    "trod torch", underwriter_pavilion,
    desc=(
        "A short pitch-black torch, head wrapped in pale fibre that "
        "is not quite cloth. The Underwriter implies it does not "
        "burn so much as remember. When lit, it shows the bridge "
        "the dark hides."
    ),
    aliases=("torch", "trod torch"),
)
_ensure_walkin_item(
    "the Underwriter's ledger", underwriter_pavilion,
    desc=(
        "A heavy iron-bound ledger on the desk behind the silk. It "
        "is open to a page that is, until you step closer, blank. "
        "It is not blank when you step closer."
    ),
    aliases=("ledger", "underwriter ledger"),
    gettable=False,
)


# ── Noble walk-in transit scene ─────────────────────────────────────────────
# Three-room scripted scene the Noble walk-in plays through before
# emerging in Mystvale. Source: the original Event 1 LARP encounter
# "Noble Walk In" by Jessica Sills — a noble retinue hires Guide
# Martin to lead them through the Mists. They meet his "assistant"
# Wil at Gateway. Wil is a Gateway thief who stumbled on Martin's
# abandoned camp, stole his journal and gear, then convinced the
# nobles he was Martin's assistant. They reach the empty camp, take
# Martin's trod torch and antidotes, then cross the Spider-Wood. They
# find Martin dead in a cocoon. Wil's con falls apart. The party
# decides what to do with Wil and with Martin's journal — which
# contains the Mistwalkers' route into the Annwyn, a secret the
# Crown and the Crows would both kill to possess.

# --- Remove legacy Noble props from the old (replaced) flow ---
# Older outcomes (delivered_sealed / read_it_first / sell_to_crows) put
# road bandits + an unsealed letter on the Old Road south. The new
# source-faithful outcomes use Wil and Martin's journal instead.
for _legacy_key in ("road bandit", "unsealed letter"):
    for _legacy in ObjectDB.objects.filter(
        db_key=_legacy_key, db_location=old_road_south.pk
    ):
        _legacy.delete()
        print(f"  DELETED : {_legacy_key} (legacy noble prop)")

# Lady Ysolde stays at the Town Hall as the Crown delivery target for
# the expose_wil outcome.
lady_ysolde = _ensure_walkin_npc(
    "Lady Ysolde of the Crescent", town_hall,
    desc=(
        "A tall woman in court black, silver crescent-moon pin at her "
        "throat. She stands at ease behind a writing-desk stacked with "
        "sealed correspondence. Her eyes miss nothing."
    ),
    aliases=("ysolde", "lady ysolde", "lady"),
    aggressive=False,
    ai_personality=(
        "Lady Ysolde of the Crescent, a minor Crown functionary running a "
        "clearing-house of correspondence out of Mystvale Town Hall. "
        "Courteous, clipped, meticulous about seals and provenance. "
        "Pays handsomely for evidence of Gateway fraud — particularly "
        "any false Guide who has cheated nobles bound for the Annwyn. "
        "Will take possession of any genuine Mistwalker's journal "
        "brought to her and file it where the Crown can use it."
    ),
    ai_knowledge=(
        "- The Crown is aware that several false Guides have set up "
        "in Gateway, taking coin from nobles and walking them into "
        "the Mists with no real expertise. She wants their names.\n"
        "- A genuine Mistwalker's journal is a prize beyond price; "
        "the Crown has been trying for years to acquire one.\n"
        "- Will reward couriers who bring her either."
    ),
)

# Room 1 — Martin's Abandoned Camp.
martins_camp = get_or_create_room(
    "Martin's Abandoned Camp",
    "typeclasses.rooms.Room",
    "A traveller's camp in a clearing where the mist sits in pools at "
    "ankle height. A small canvas tent stands open; a cook-pot on a "
    "tripod over a long-dead fire holds a half-eaten meal that the "
    "mice have not finished. A lantern hangs from the tent-pole, "
    "burnt to its socket. Nothing has been overturned. Nobody "
    "fought here. The Guide simply got up and left.\n\n"
    "|wWil|n, the assistant who has led you this far from Gateway, "
    "rakes a hand through his hair and tries — visibly tries — to "
    "look like a man surprised by an empty camp.\n\n"
    "|540Among the gear on the ground: a |whurried note|n, a |wtrod "
    "torch|n with a pale fibre wick, and a small leather |wpouch of "
    "antidotes|n. Take what you need. The Mists are ahead.|n\n\n"
    "|wForward|n into the |wspider-wood|n.",
    zone="The Mists",
)

# Room 2 — the Spider-Wood.
spider_wood = get_or_create_room(
    "The Spider-Wood",
    "typeclasses.rooms.Room",
    "A stretch of pine that the trod torch shows is not pine. Webs at "
    "chest height, hung between trunks in pale grey curtains. The "
    "ground crunches softly with the husks of things that did not "
    "make it through. The bells on the stretched silk above the "
    "trail trill at every step. Somewhere out past the torchlight, "
    "a many-legged shape moves between trunks without quite ever "
    "showing itself.\n\n"
    "Strung up to one side of the path is a |wcocoon|n the size of "
    "a man. Inside the wrapping, a face that was once a man's. "
    "Around his neck, the puncture-marks have crusted over.\n\n"
    "|540It is Martin. Wil makes a small noise that he tries to "
    "swallow and fails.|n\n\n"
    "|wAhead|n into the |wweb-wreathed hollow|n.",
    zone="The Mists",
)

# Room 3 — the Web-Wreathed Hollow. Wil's con falls apart here.
web_hollow = get_or_create_room(
    "The Web-Wreathed Hollow",
    "typeclasses.rooms.Room",
    "A clearing low between two ridges, ankle-deep in old web. The "
    "Spider's territory thins here. The trod torch in your hand "
    "begins to flicker. Wil is shaking — actually shaking now, all "
    "pretense gone. He takes |wa leather-bound journal|n out from "
    "under his cloak, looks at it, looks at you, and lets it fall "
    "into the leaves at your feet.\n\n"
    "|wI'm not anybody's assistant|n, he says. |wI found his camp "
    "a fortnight back. He was already gone. I took the book and "
    "the gear and I went back to Gateway and I told the lords I'd "
    "guide them through. I'm sorry. I'm so sorry.|n\n\n"
    "|540The journal is on the ground. Wil is on the ground. The "
    "Annwyn is ahead, over the rise, where the torch will not need "
    "to burn anymore.|n\n\n"
    "|wOut|n the rise to |wMystvale|n.",
    zone="The Mists",
)

# Connect the three scripted rooms; WalkInJourneyExit so Wil follows.
link(martins_camp, "forward", spider_wood, "back", "f", "b")
link(spider_wood, "ahead", web_hollow, "back", "a", "b")
for _src, _dst in (
    (martins_camp, spider_wood),
    (spider_wood, martins_camp),
    (spider_wood, web_hollow),
    (web_hollow, spider_wood),
):
    for _ex in _src.contents:
        if getattr(_ex, "destination", None) == _dst:
            if _ex.typeclass_path != "typeclasses.exits.WalkInJourneyExit":
                _ex.swap_typeclass(
                    "typeclasses.exits.WalkInJourneyExit",
                    clean_attributes=False,
                )

# Final exit — Hollow → Mystvale Marketplace (the trod torch dies on the way).
_hollow_out = ObjectDB.objects.filter(
    db_key="out", db_location=web_hollow.pk
).first()
if not _hollow_out:
    _hollow_out = _create.create_object(
        "typeclasses.exits.WalkInJourneyExit",
        key="out", location=web_hollow, destination=marketplace,
    )
    _hollow_out.aliases.add("rise")
    _hollow_out.aliases.add("mystvale")
    print("  CREATED : Web-Wreathed Hollow → Mystvale Marketplace (the rise)")

# --- Wil the Conman: companion, present at all 3 rooms ---
wil = _ensure_walkin_npc(
    "Wil the Conman", martins_camp,
    desc=(
        "A wiry person in good warm traveling clothes that don't quite "
        "fit. A backpack slung over one shoulder, lantern in hand, no "
        "weapon at the belt. They smile too quickly at every question "
        "and look at the trail markers for too long before agreeing "
        "they're the right ones."
    ),
    aliases=("wil", "william", "wilhelmina", "conman", "assistant", "guide's assistant"),
    aggressive=False,
    ai_personality=(
        "Wil — Gateway petty thief and conman. Stumbled on Mistwalker "
        "Martin's abandoned camp on a solo run into the Mists, stole "
        "his journal and trod torch, and went back to Gateway to find "
        "marks. Conned the noble retinue in the bearer's party into "
        "believing he was Martin's assistant. Has no real knowledge "
        "of the Annwyn beyond what he half-read in the stolen journal. "
        "Cocky and glib in the Camp, increasingly afraid in the "
        "Spider-Wood, confessing and panicking in the Hollow. Will "
        "try to flee if cornered; carries no weapon and will not "
        "fight competently if forced to."
    ),
    ai_knowledge=(
        "- Stole Martin's journal and trod torch from an abandoned "
        "camp a fortnight ago. Has been pretending to be the Guide's "
        "Assistant in Gateway ever since.\n"
        "- Knows enough of the journal to repeat its broad warnings: "
        "travel together; do not leave the torch; antidotes for fang "
        "drop poison; the Spider hates groups.\n"
        "- Knows nothing of where Martin actually went. The body in "
        "the cocoon is a shock to him.\n"
        "- Will confess in the Hollow, drop the journal, and try to "
        "vanish into Mystvale at the first opportunity."
    ),
)
wil.attributes.add("is_walkin_companion", True)
wil.db.body = 3
wil.db.total_body = 3
wil.db.av = 0

# --- Items: Martin's Camp ---
_ensure_walkin_item(
    "Martin's hurried note", martins_camp,
    desc=(
        "A piece of trail-parchment with hurried handwriting:\n\n"
        "'Something in the trees. Watching. Have been here before — "
        "groups confuse it. Travel connected. Antidote in pouch if "
        "bitten. Will try for the Annwyn alone tonight — meet you on "
        "the far side. The candle shows the trail markers. Do not "
        "let it go out. — M.'"
    ),
    aliases=("note", "martin's note", "hurried note"),
)
_ensure_walkin_item(
    "trod torch", martins_camp,
    desc=(
        "A short pitch-black torch, head wrapped in pale fibre. When "
        "lit it burns a hot purple that hurts to look at directly. "
        "By its light, marks invisible on bare bark show plainly on "
        "the trees."
    ),
    aliases=("torch", "trod torch", "candle"),
)
_ensure_walkin_item(
    "pouch of antidotes", martins_camp,
    desc=(
        "A small oiled-leather pouch with five corked glass phials of "
        "a thin clear liquid. A loop of string is tied around each "
        "with a label: 'Fang Drop'."
    ),
    aliases=("pouch", "antidote", "antidotes", "phials"),
)

# --- Items: Spider-Wood ---
_ensure_walkin_item(
    "Martin's cocoon", spider_wood,
    desc=(
        "A man-sized cocoon strung up between two trunks. Inside the "
        "silk, a traveller in dark wool, neck punctured many times, "
        "his hands folded as if someone had taken the time to fold "
        "them. He has been dead a fortnight. He is Mistwalker Martin, "
        "or what is left of him."
    ),
    aliases=("cocoon", "martin", "body", "martin's body"),
    gettable=False,
)
_ensure_walkin_item(
    "second guide candle", spider_wood,
    desc=(
        "Tucked into Martin's belt, half-used, a twin to the trod "
        "torch in your hand. Worth keeping. Worth more not to need."
    ),
    aliases=("candle", "second candle", "guide candle"),
)

# --- Items: Web-Wreathed Hollow ---
_ensure_walkin_item(
    "Martin's journal", web_hollow,
    desc=(
        "A leather-bound journal in a Mistwalker's hand. The earlier "
        "pages are dense with sketches and notations of trail markers, "
        "candle behaviour, the Spider's patterns. The later pages "
        "describe a route through the Mists that is not on any map "
        "the Crown owns — or the Crows. Whoever has this can find "
        "the safe way into the Annwyn. Or sell the secret of it."
    ),
    aliases=("journal", "martin's journal", "notebook", "guide journal"),
)


# ── Explorer walk-in transit scene (was Scout) ──────────────────────────────
# Three-room scripted scene the Explorer walk-in plays through before
# emerging in Mystvale. Source: the original Event 1 LARP encounter
# "The Fate of Magister Ipwin" by John Kozar — scholars of the Lodge
# of the Metaphysical Mind respond to Magister Ipwin's call to study
# the Annwyn. They find his camp abandoned, follow his trail through
# the Tangle past a shrine to the old Witch-Queen, and reach a
# barrow tomb where Ipwin is being possessed by Shireen, a fae
# spirit. They must reassemble Shireen's rune-bones to exorcise her,
# or fight her, or take Ipwin's metaphysics research and flee, or
# strike a darker bargain with the Witch-Queen's gift.
#
# The quest key remains walkin_scout for DB stability; the title and
# framing become "Explorer" to match the canonical fifth walk-in.

# --- Remove legacy Scout props ---
# Older outcomes (warn_watch / sell_intel_crows / stay_silent) used a
# lone-scout framing with a Crow waymark on the Old Road south. The
# new source-faithful outcomes use Ipwin and Shireen instead.
for _legacy_key in ("crow waymark",):
    for _legacy in ObjectDB.objects.filter(
        db_key=_legacy_key, db_location=old_road_south.pk
    ):
        _legacy.delete()
        print(f"  DELETED : {_legacy_key} (legacy scout prop)")

# Watch Captain stays — Chain Gang, Cirque, etc. use them as delivery target.
watch_captain = _ensure_walkin_npc(
    "Mystvale Captain of the Watch", bannon_barracks,
    desc=(
        "A gaunt veteran in watch-grey, beard iron-shot, a scar bisecting "
        "one eyebrow. A half-drunk cup of tea cools on the map-table in "
        "front of him."
    ),
    aliases=("watch captain", "captain of the watch", "captain"),
    aggressive=False,
    ai_personality=(
        "Captain of the Mystvale watch. Pragmatic, tired, more interested "
        "in useful intel than politeness. Takes bribes of information "
        "rather than coin."
    ),
)

# Crow Agent stays — Noble's sell_journal_to_crows uses them.
crow_agent = _ensure_walkin_npc(
    "Crow Agent", old_road_south,
    desc=(
        "A thin figure in a hooded cloak the colour of wet slate, leaning "
        "against a gnarled pine. A raven's-feather pin glints at the "
        "throat."
    ),
    aliases=("crow agent", "agent"),
    aggressive=False,
    ai_personality=(
        "A Crow-faction agent on the Old Road south of Mystvale. Buys "
        "intercepted correspondence, warns of patrols, pays in silver — "
        "and remembers faces, good and bad."
    ),
)

# Room 1 — Magister Ipwin's Abandoned Camp.
ipwin_camp = get_or_create_room(
    "Magister Ipwin's Abandoned Camp",
    "typeclasses.rooms.Room",
    "A scholar's camp at the edge of the Mists — a folding writing-desk "
    "under a stretched oilcloth, three smudged blacklight lanterns "
    "spaced along a perimeter rope, a fire of pine-cones still warm "
    "in the pit. Books, charts, and a half-empty cup of something "
    "the colour of ditchwater sit on the desk. Magister Ipwin of the "
    "Lodge of the Metaphysical Mind summoned you here. He is not here.\n\n"
    "|wMagister Vell|n, your colleague from the Lodge, frowns at "
    "Ipwin's open journal and a pinned note that reads, in Ipwin's "
    "hand: |w'A discovery. The barrow. Follow if you can. The path "
    "is in the lanterns.'|n\n\n"
    "|540The lanterns are blacklight — they show the perception "
    "trail Ipwin left for the Lodge. The trail leads forward, into "
    "the Tangle.|n\n\n"
    "|wForward|n into the |wTangle|n.",
    zone="The Mists",
)

# Room 2 — the Shrine in the Tangle.
shrine_tangle = get_or_create_room(
    "The Shrine in the Tangle",
    "typeclasses.rooms.Room",
    "A small stone shrine in a clearing the trees seem reluctant to "
    "enter. Old offerings — a wreath of bird-bones, a clay cup, a "
    "lock of hair tied in green ribbon — sit at the foot of a "
    "weather-worn carving of a woman crowned in branches. She was "
    "the |wnature-goddess|n the old peoples worshipped before she "
    "became the |wWitch-Queen|n of the green wood. The peoples are "
    "gone. The shrine is not.\n\n"
    "A line of script in old Ard runs around the lintel of the "
    "shrine: |w'What is yours but never yours?'|n It waits to be "
    "answered.\n\n"
    "|540Ipwin's blacklight trail continues past the shrine, "
    "deeper into the Tangle. The Lodge's instruments would advise "
    "you to look closely here before pressing on.|n\n\n"
    "|wAhead|n into the |wbarrow|n.",
    zone="The Mists",
)

# Room 3 — the Barrow of Shireen.
barrow_shireen = get_or_create_room(
    "The Barrow of Shireen",
    "typeclasses.rooms.Room",
    "An earth-mound barrow tomb opened by Ipwin's pick and lamp. Inside, "
    "a ritual circle has been broken — chalk lines scuffed by frantic "
    "boots — and a litter of |wrune-bones|n is scattered across the "
    "earthen floor. Each bone bears a small carved sigil; when "
    "complete, they would lay out a binding figure for the spirit "
    "the barrow was built to hold.\n\n"
    "Magister |wIpwin|n is kneeling at the centre of the circle, "
    "talking quietly to a woman who is not in the circle and not "
    "in the world. |wShireen|n. Her face turns to the doorway when "
    "you enter. Her smile does not reach her eyes because her eyes "
    "are not eyes.\n\n"
    "|540The bones can be reassembled. The spirit can be "
    "exorcised. The spirit can be fought. The bones can be left "
    "where they lie, and the scholar with them.|n\n\n"
    "|wOut|n through the barrow mouth, back to |wMystvale|n.",
    zone="The Mists",
)

# Connect the three scripted rooms; WalkInJourneyExit so Vell follows.
link(ipwin_camp, "forward", shrine_tangle, "back", "f", "b")
link(shrine_tangle, "ahead", barrow_shireen, "back", "a", "b")
for _src, _dst in (
    (ipwin_camp, shrine_tangle),
    (shrine_tangle, ipwin_camp),
    (shrine_tangle, barrow_shireen),
    (barrow_shireen, shrine_tangle),
):
    for _ex in _src.contents:
        if getattr(_ex, "destination", None) == _dst:
            if _ex.typeclass_path != "typeclasses.exits.WalkInJourneyExit":
                _ex.swap_typeclass(
                    "typeclasses.exits.WalkInJourneyExit",
                    clean_attributes=False,
                )

# Final exit — Barrow → Mystvale Marketplace.
_barrow_out = ObjectDB.objects.filter(
    db_key="out", db_location=barrow_shireen.pk
).first()
if not _barrow_out:
    _barrow_out = _create.create_object(
        "typeclasses.exits.WalkInJourneyExit",
        key="out", location=barrow_shireen, destination=marketplace,
    )
    _barrow_out.aliases.add("mystvale")
    _barrow_out.aliases.add("mouth")
    print("  CREATED : Barrow of Shireen → Mystvale Marketplace (barrow mouth)")

# --- Magister Vell: Lodge colleague, companion ---
vell = _ensure_walkin_npc(
    "Magister Vell", ipwin_camp,
    desc=(
        "A spare, ink-stained scholar in a Lodge of the Metaphysical "
        "Mind robe, satchel of writing tools at the hip, a small "
        "iron-bound book in one hand. They are middle-aged, "
        "watchful, and very tired of having to explain to people "
        "outside the Lodge what metaphysics is for."
    ),
    aliases=("vell", "magister vell"),
    aggressive=False,
    ai_personality=(
        "Magister Vell of the Lodge of the Metaphysical Mind, a "
        "colleague of Magister Ipwin's. Came at his summons. "
        "Practical scholar — does not believe in ghosts the way "
        "Ipwin does, until they are standing in a barrow looking at "
        "one. Will reason through the bone-rune ritual if given the "
        "time, will hold a lantern in a fight, will not draw a "
        "blade because they do not own one. Speaks with the "
        "careful clarity of a person who has spent a life "
        "explaining."
    ),
    ai_knowledge=(
        "- Ipwin is a respected (if eccentric) member of the Lodge. "
        "His specialty is forest-bound spirits and the lingering "
        "effects of old worship.\n"
        "- The blacklight lanterns mark the trail Ipwin laid for "
        "the Lodge — invisible without their light.\n"
        "- The Witch-Queen was the nature-goddess of the old "
        "peoples before she withdrew into the green wood. Her "
        "shrines are scattered through any forest old enough.\n"
        "- The riddle at the shrine — 'what is yours but never "
        "yours' — has the answer 'a gift'. Speaking the answer is "
        "the courteous way to pass the goddess's ground.\n"
        "- Rune-bones bind a spirit when laid out in the correct "
        "figure. Breaking the figure releases the spirit. The "
        "barrow was a binding-place; Ipwin broke the figure when "
        "he opened it."
    ),
)
vell.attributes.add("is_walkin_companion", True)
vell.db.body = 3
vell.db.total_body = 3
vell.db.av = 0

# --- Magister Ipwin (possessed) at the Barrow ---
ipwin = _ensure_walkin_npc(
    "Magister Ipwin", barrow_shireen,
    desc=(
        "An older Magister in soaked Lodge robes, kneeling at the "
        "centre of the broken ritual circle. His voice is his own; "
        "his eyes, when they turn to you, are not. He is being worn "
        "like a coat. He smiles too widely and apologises in two "
        "voices: his own, for breaking the binding; and another "
        "voice, much older, for being grateful that he did."
    ),
    aliases=("ipwin", "magister ipwin", "possessed"),
    aggressive=False,
    ai_personality=(
        "Magister Ipwin of the Lodge of the Metaphysical Mind. "
        "Came to the Annwyn to study spirit phenomena. Found a "
        "barrow with an intact binding-figure; opened it; released "
        "the spirit it held; was possessed by her on contact. Now "
        "speaks in alternating voices — his own (academic, "
        "apologetic, frightened) and Shireen's (older, slower, "
        "amused). Wants the courier-party to either reassemble the "
        "binding-figure (Ipwin's voice) or leave it broken "
        "(Shireen's voice). If killed, Shireen will exit the body "
        "and seek a new host."
    ),
    ai_knowledge=(
        "- Opened the barrow's ritual circle without recognising it.\n"
        "- Shireen is a fae spirit bound here in the second age — "
        "a daughter of the Witch-Queen, by his guess.\n"
        "- The rune-bones, reassembled into the binding-figure, "
        "would put Shireen back. Each bone is paired with a sigil "
        "on the barrow walls.\n"
        "- The Lodge would prefer he be returned alive and "
        "exorcised, but he has accepted that this may not be "
        "possible."
    ),
)
ipwin.db.body = 4
ipwin.db.total_body = 4
ipwin.db.av = 0

# --- Shireen: fae spirit, manifests at the Barrow ---
shireen = _ensure_walkin_npc(
    "Shireen", barrow_shireen,
    desc=(
        "A pale, narrow woman standing where Ipwin is kneeling, "
        "wearing a green wedding-dress that fades into the cold air "
        "at the hem. Her eyes are wet black holes. The light bends "
        "wrong around her. She is the spirit the barrow was built "
        "to hold. She is now standing outside it, smiling at you, "
        "and the smile is a courtesy."
    ),
    aliases=("shireen", "fae spirit", "fae", "spirit"),
    aggressive=False,
    ai_personality=(
        "Shireen — a daughter of the Witch-Queen, bound in the "
        "barrow's ritual circle for crimes the binders did not "
        "name. Released when Ipwin broke the circle. Now wears him "
        "as a host while she decides where to go. Will speak with "
        "couriers; will offer the Witch-Queen's gift (a touch, a "
        "secret, a name) to anyone who will leave her free; will "
        "fight if a courier reassembles the bones. Dies hard. Does "
        "not die forever."
    ),
    ai_knowledge=(
        "- Was bound here in the second age by an unnamed Aurorym "
        "circle. Her crime was speaking to the Witch-Queen when the "
        "circle had outlawed her name.\n"
        "- Has been alone in the barrow for centuries.\n"
        "- The Witch-Queen's gift, offered to a willing courier: a "
        "small touch of fae sight, a debt called in later.\n"
        "- The binding-figure is fixed by laying the rune-bones in "
        "the pattern carved on the barrow walls. Anyone with eyes "
        "for sigils can do it."
    ),
)
shireen.db.body = 6
shireen.db.total_body = 6
shireen.db.av = 2
shireen.db.master_of_arms = 1
shireen.db.tough = 2

# --- Items: Ipwin's Camp ---
_ensure_walkin_item(
    "Ipwin's journal", ipwin_camp,
    desc=(
        "Magister Ipwin's working journal, bound in scuffed black "
        "leather. The opening pages catalogue ghost phenomena across "
        "Arnesse. The latter pages turn frantic: |wfound a barrow|n, "
        "|wintact binding circle|n, |wthird-age work|n. The last "
        "entry stops mid-sentence: |wif the figure breaks, the spirit|n"
    ),
    aliases=("journal", "ipwin's journal", "notebook"),
)
_ensure_walkin_item(
    "blacklight lantern", ipwin_camp,
    desc=(
        "A small lantern fitted with a violet-filtered candle. By "
        "its light, blacklight markings invisible in daylight glow "
        "pale green on bark and stone. Ipwin used these to mark the "
        "trail for the Lodge."
    ),
    aliases=("lantern", "blacklight"),
)
_ensure_walkin_item(
    "Ipwin's pinned note", ipwin_camp,
    desc=(
        "A scrap pinned to the corner of the desk in Ipwin's "
        "handwriting: |w'A discovery. The barrow. Follow if you "
        "can. The path is in the lanterns. Bring antidotes if you "
        "have them. — I.'|n"
    ),
    aliases=("pinned note", "ipwin note", "note"),
    gettable=False,
)

# --- Items: The Shrine ---
_ensure_walkin_item(
    "shrine of the Witch-Queen", shrine_tangle,
    desc=(
        "A weather-worn stone shrine in the shape of a woman crowned "
        "in branches. Old offerings — bird-bones in a wreath, a "
        "clay cup, a green ribbon — lie at the foot. The lintel "
        "above her head reads, in old Ard:\n\n"
        "    |w'What is yours but never yours?'|n\n\n"
        "(The answer, courteous and old, is |wa gift|n.)"
    ),
    aliases=("shrine", "witch-queen", "witch queen"),
    gettable=False,
)
_ensure_walkin_item(
    "tangle lore stone", shrine_tangle,
    desc=(
        "A flat slate at the foot of the shrine, lichen-edged. The "
        "inscription, half-read: |w'The Tangle was her loom and her "
        "needle. Step softly. Pay her toll. Pass.'|n"
    ),
    aliases=("lore stone", "stone", "tangle lore"),
    gettable=False,
)

# --- Items: The Barrow ---
_ensure_walkin_item(
    "rune-bone", barrow_shireen,
    desc=(
        "A small human finger-bone carved with a fae sigil. Pair it "
        "with the matching sigil on the barrow wall and the spirit "
        "is bound one tile closer to her circle. There are four "
        "such bones loose on the floor; the figure cannot complete "
        "without all of them."
    ),
    aliases=("bone", "rune-bone", "rune bone"),
    count=4,
)
_ensure_walkin_item(
    "broken ritual circle", barrow_shireen,
    desc=(
        "A chalk and salt circle that someone has scuffed through "
        "with a frantic boot. The breakage is small — a hand's "
        "width — but it was enough. The bones that lay in figure "
        "around the circle are scattered."
    ),
    aliases=("circle", "ritual circle", "broken circle"),
    gettable=False,
)


# ── Chain Gang walk-in transit scene ────────────────────────────────────────
# Three-room scripted scene the Chain Gang walk-in plays through before
# emerging in Mystvale. Source: the original Event 1 LARP encounter
# "The Chain Gang" by John Kozar — prisoners delivered to the edge of
# the Mists, chained, disarmed; Ulfric the Coldhand tries to recruit
# them as the wagon trail descends into a forest where something
# very large stalks the dark; at a forested clearing they find a wounded
# Laurent man-at-arms, his butchered comrades, and a chest of Laurent
# gold. The moral choice is what to do with the gold and Killian.
#
# Ulfric, Cedric, and Josyn travel with the player as walk-in companions.
# Killian is stationary at the Clearing.

# --- Remove legacy Mistwall props from the old (replaced) Chain Gang flow ---
# Older outcomes (bloody_break / quiet_slip / legal_appeal / turncoat)
# used Mystvale Jailers + a Chain Gang Ringleader + a forged warrant at
# the Mistwall. None of those map to the new source-faithful outcomes,
# so sweep them away on populate.
for _legacy_key in ("Mystvale Jailer", "Chain Gang Ringleader", "forged warrant"):
    for _legacy in ObjectDB.objects.filter(
        db_key=_legacy_key, db_location=mistwall.pk
    ):
        _legacy.delete()
        print(f"  DELETED : {_legacy_key} (legacy chain-gang prop)")

# Room 1 — the prison cart at the Mistwall. Chained, dark, frightened.
prison_cart = get_or_create_room(
    "The Prison Cart at the Mistwall",
    "typeclasses.rooms.Room",
    "The back of an iron-banded prison wagon, parked at the mist's edge. "
    "A guttering torch nailed to the wagon's roof throws shaking light "
    "over a row of chained captives — you among them. Iron cuffs at "
    "wrist and ankle, a common chain run through every cuff. Your "
    "weapons, your armor, your purse — gone, locked in a crate the "
    "jailers carried off into the fog. The wagon doors hang open; "
    "the jailers have already turned back, leaving you to the Last "
    "Walk and whatever waits past the Mistwall.\n\n"
    "|540You are not alone. The other prisoners watch you the way "
    "men watch a card-table when the stakes are about to be called.|n\n\n"
    "|wForward|n into the |wmist-wreathed trail|n.",
    zone="The Mists",
)

# Room 2 — the trail through the forest in the Mists. Dark, something stalks.
mist_trail = get_or_create_room(
    "The Mist-Wreathed Trail",
    "typeclasses.rooms.Room",
    "A muddy track winding between black pines that the fog will not "
    "let you see the tops of. The torch from the prison wagon is "
    "behind you and going out. Ahead, somewhere in the trees, "
    "branches break — not the snap of a deer or the crash of a boar, "
    "but the slow deliberate flex of something setting its weight "
    "down. Tracks gouge the soft earth: large, cloven, deep.\n\n"
    "Off to one side of the trail lies |wsomething that was a person|n. "
    "It is not a person anymore.\n\n"
    "|540The lantern of the Mistwalker who was supposed to guide you "
    "lies smashed in the mud, the wick still trying to burn.|n\n\n"
    "|wAhead|n through the trees, light glimmers — a |wclearing|n.",
    zone="The Mists",
)

# Room 3 — the bandit clearing. The moral choice scene.
bandit_clearing = get_or_create_room(
    "A Clearing in the Mists",
    "typeclasses.rooms.Room",
    "A small lantern-lit clearing, lanterns staked into the earth — the "
    "ones the dead set out before they died. A caravan's wagon lies "
    "tipped on its side, one wheel still spinning slowly. Two armored "
    "bodies, men-at-arms in Laurent green, lie in the mud, torn apart "
    "by something with talons. A third Laurent guard — alive, just — "
    "is propped against the wagon, pressing a wadded cloak to a "
    "wound in his side.\n\n"
    "A heavy |wstrongbox|n sits half-open beside him, gold coin "
    "spilling into the dirt. Crates of weapons and armor lie scattered "
    "around it — and stamped on one crate, in fresh wax, is your own "
    "name. Whoever was bringing this gear into the Annwyn was "
    "bringing your gear too.\n\n"
    "|540The other prisoners are looking at the gold. Ulfric is "
    "looking at the wounded guard. The decision is yours, and it is "
    "about to be made for you if you do not move.|n\n\n"
    "|wOut|n through the mists, following the Mistwalker's last "
    "lantern toward |wMystvale|n.",
    zone="The Mists",
)

# Connect the three scripted rooms. Companion-following exits.
link(prison_cart, "forward", mist_trail, "back", "f", "b")
link(mist_trail, "ahead", bandit_clearing, "back", "a", "b")
for _src, _dst in (
    (prison_cart, mist_trail),
    (mist_trail, prison_cart),
    (mist_trail, bandit_clearing),
    (bandit_clearing, mist_trail),
):
    for _ex in _src.contents:
        if getattr(_ex, "destination", None) == _dst:
            if _ex.typeclass_path != "typeclasses.exits.WalkInJourneyExit":
                _ex.swap_typeclass(
                    "typeclasses.exits.WalkInJourneyExit",
                    clean_attributes=False,
                )

# Final escape — clearing → Mystvale Marketplace. Companions follow if
# they're still alive (Ulfric may have been killed by the player).
_out_exit = ObjectDB.objects.filter(
    db_key="out", db_location=bandit_clearing.pk
).first()
if not _out_exit:
    _out_exit = _create.create_object(
        "typeclasses.exits.WalkInJourneyExit",
        key="out", location=bandit_clearing, destination=marketplace,
    )
    _out_exit.aliases.add("lantern")
    _out_exit.aliases.add("mystvale")
    print("  CREATED : Bandit Clearing → Mystvale Marketplace (lantern out)")

# --- Companion NPCs: Ulfric, Cedric, Josyn ---
ulfric = _ensure_walkin_npc(
    "Ulfric the Coldhand", prison_cart,
    desc=(
        "A heavy-shouldered Northman, wrists raw from the cuffs, a "
        "weeks-old beard and eyes that have already finished sizing up "
        "everyone in the wagon. From the lands of House Coldhill, "
        "though he is no friend to any lord. The chain that binds him "
        "is the same chain that binds you."
    ),
    aliases=("ulfric", "coldhand"),
    aggressive=False,
    ai_personality=(
        "Ulfric the Coldhand — a Trollkin bandit from the lands of "
        "House Coldhill, arrested in Gateway for killing a man in a "
        "tavern brawl. Charismatic, contemptuous of nobility, sees "
        "the Last Walk as a chance to build his outlaw band. He will "
        "pitch the bearer on joining him. If they refuse and he sees "
        "the gold at the Clearing, he will take it by force. Speaks "
        "in plain, dry, hard sentences."
    ),
    ai_knowledge=(
        "- Was running with a small gang called the Trollkin before "
        "being arrested in Gateway.\n"
        "- The warrants in this column were rushed; he heard the Gateway "
        "nobility wanted certain names off their docket fast.\n"
        "- Cedric is his man; Josyn is his blade.\n"
        "- Wants to recruit anyone with a hand for a blade. Will share "
        "the gold equally with anyone who throws in. Will kill anyone "
        "who tries to stop him from taking the chest.\n"
        "- Knows the Annwyn is where you go to disappear — perfect "
        "country for an outlaw band."
    ),
)
ulfric.attributes.add("is_walkin_companion", True)
ulfric.db.body = 5
ulfric.db.total_body = 5
ulfric.db.av = 1
ulfric.db.master_of_arms = 1
ulfric.db.tough = 1
ulfric.db.melee_weapons = 2

cedric = _ensure_walkin_npc(
    "Cedric", prison_cart,
    desc=(
        "A narrow, plain-faced man from the Hearthlands, the kind of "
        "porter you forget the moment he leaves the room. He keeps "
        "close to Ulfric and watches Ulfric for cues the way a dog "
        "watches a man with a stick."
    ),
    aliases=("cedric",),
    aggressive=False,
    ai_personality=(
        "Cedric — a Hearthlander follower with a long list of petty "
        "crimes who fell in with Ulfric in Gateway. Has neither "
        "initiative nor conviction; will agree with whoever frightens "
        "him most in the moment. Defers to Ulfric on everything."
    ),
    ai_knowledge=(
        "- Was wanted for petty theft and fraud before the murder in "
        "Gateway swept him up too.\n"
        "- Believes Ulfric is going somewhere; would rather be in "
        "Ulfric's pocket than out of it.\n"
        "- Won't make a decision on his own. Look to Ulfric."
    ),
)
cedric.attributes.add("is_walkin_companion", True)
cedric.db.body = 3
cedric.db.total_body = 3
cedric.db.av = 0

josyn = _ensure_walkin_npc(
    "Josyn", prison_cart,
    desc=(
        "A lean ex-mercenary in a stained gambeson, ejected from the "
        "Richter armies for drinking and the trouble that follows from "
        "drinking. He has not spoken since the wagon stopped. He is "
        "watching everyone's hands."
    ),
    aliases=("josyn",),
    aggressive=False,
    ai_personality=(
        "Josyn — ex-Richter mercenary, drummed out for drink, now in "
        "Ulfric's band. The violent one. Talks little; cuts throats "
        "quickly. Loyal to Ulfric out of habit and shared crimes."
    ),
    ai_knowledge=(
        "- Was a Richter merc; knows blade-work and the inside of a "
        "campaign tent.\n"
        "- Will fight for Ulfric if a fight breaks out at the Clearing.\n"
        "- Has nothing kind to say and rarely says anything at all."
    ),
)
josyn.attributes.add("is_walkin_companion", True)
josyn.db.body = 4
josyn.db.total_body = 4
josyn.db.av = 1
josyn.db.melee_weapons = 1

# --- Killian: wounded Laurent man-at-arms at the Clearing ---
killian = _ensure_walkin_npc(
    "Killian", bandit_clearing,
    desc=(
        "A middle-aged man-at-arms in dented Laurent green, propped "
        "against the wreck of the wagon. A wadded cloak is pressed to "
        "a wound at his side, dark with blood that is no longer "
        "running. His longsword is on the ground beside him. His "
        "eyes are clear; he has been waiting for someone to come down "
        "this trail."
    ),
    aliases=("killian", "guard", "laurent guard"),
    aggressive=False,
    ai_personality=(
        "Killian — senior man-at-arms in the service of Lord Garamond "
        "Laurent for many years. Loyal, professional, wounded but not "
        "panicking. His charge was the strongbox of Laurent gold; he "
        "intends to keep it or die over it. Will fight to the death "
        "if anyone moves on the chest. Will reward (with thanks and "
        "Laurent goodwill) anyone who tends his wound and protects "
        "the gold. Saw the thing that killed his comrades only as "
        "claws and shadow and 'so much blood.'"
    ),
    ai_knowledge=(
        "- He serves Lord Garamond Laurent. Two dead men here were "
        "his sworn brothers, Bren and Tomas.\n"
        "- The chest is Laurent gold being moved to fund the Laurent "
        "expedition into the Annwyn.\n"
        "- The Mistwalker who guided them was killed by the same "
        "thing that killed the others — black, huge, talons. He "
        "could not describe it better than that.\n"
        "- If brought safely to the Mystvale Captain of the Watch, "
        "House Laurent will remember the bearer's name."
    ),
)
killian.db.body = 2
killian.db.total_body = 5  # wounded, partially down
killian.db.av = 2
killian.db.master_of_arms = 1
killian.db.tough = 2
killian.db.melee_weapons = 1
killian.db.shields = 2

# --- Items: Prison Cart ---
_ensure_walkin_item(
    "rusty lockpicks", prison_cart,
    desc=(
        "A small bent set of lockpicks, half-buried under a pile of "
        "rags in the corner of the wagon. Someone before you came "
        "prepared — and did not get the chance to use them."
    ),
    aliases=("picks", "lockpicks", "pick"),
)
_ensure_walkin_item(
    "common chain", prison_cart,
    desc=(
        "A heavy iron chain run through every cuff in the wagon, "
        "shackling each prisoner to the next. The cuffs themselves "
        "are crude — picked, they would fall open easily."
    ),
    aliases=("chain", "chains", "cuffs"),
    gettable=False,
)

# --- Items: Mist-Wreathed Trail ---
_ensure_walkin_item(
    "mauled traveller", mist_trail,
    desc=(
        "What is left of a person who tried to walk this trail before "
        "you. Mauled by something very large, with talons. The bones "
        "have been gnawed. The body is too torn to identify; the "
        "clothes are coarse wool, the kind a labourer wears."
    ),
    aliases=("body", "traveller", "mauled body", "corpse"),
    gettable=False,
)
_ensure_walkin_item(
    "smashed lantern", mist_trail,
    desc=(
        "A staved-in glass lantern, dropped in the mud. The wick is "
        "still trying to burn against the wet glass. The Mistwalker "
        "who carried this is not here, and was not carried away."
    ),
    aliases=("lantern", "broken lantern"),
    gettable=False,
)

# --- Items: Bandit Clearing ---
_ensure_walkin_item(
    "Laurent strongbox", bandit_clearing,
    desc=(
        "A heavy iron-bound chest, lid sprung half-open, gold coin "
        "spilling from the gap. Stamped on the lid is the green "
        "crescent-and-tower of House Laurent."
    ),
    aliases=("strongbox", "chest", "laurent chest", "gold", "coin"),
)
_ensure_walkin_item(
    "Lord Laurent's letter", bandit_clearing,
    desc=(
        "A sealed parchment, lying near Killian's hand. The wax bears "
        "the green crescent of House Laurent. It commissions Killian "
        "and his men to bring the enclosed coin and gear to the "
        "Laurent expedition camp in the Annwyn — and lists, in a "
        "careful hand, the names of certain prisoners on this Last "
        "Walk whose convictions Lord Garamond believes were rushed by "
        "Gateway's nobility. Yours may be among them."
    ),
    aliases=("letter", "laurent letter", "lord laurent letter"),
)
_ensure_walkin_item(
    "Laurent guards' bodies", bandit_clearing,
    desc=(
        "Two men-at-arms in Laurent green, side by side. Their armor "
        "is half-torn from their bodies; great rents go through the "
        "steel as if it were linen. Killian's brothers, Bren and "
        "Tomas, by the embroidered initials on the gambeson cuffs."
    ),
    aliases=("bodies", "guards", "dead guards", "laurent dead"),
    gettable=False,
)
_ensure_walkin_item(
    "gear crates", bandit_clearing,
    desc=(
        "Half a dozen wooden crates, lids pried up. Weapons, armor, "
        "kits, purses — all stamped with names. One crate bears your "
        "own. Lord Laurent must have known which prisoners were being "
        "walked in tonight, and arranged to return their gear to "
        "them past the gates of the Annwyn."
    ),
    aliases=("crates", "gear", "your gear"),
    gettable=False,
)


# ===========================================================================
# EVENT 1 — SATURDAY CONTENT
#
# Adds NPCs, items, and rooms for the four new Saturday-arc quests
# defined in world/quest_data.py:
#   - combat_training    (Mystvale Training Yard)
#   - alchemy_training   (The Crafter's Quarter / Apotheca Chirurgery)
#   - business_opportunity (gated on walkin_cirque; Mystvale Marketplace)
#   - tale_to_remember   (Songbird's Rest at night)
#
# Also seeds Rowyna's Diary of Exile at the Crow Camp Blacksmith's Prison
# so it can be found during/after rescue_blacksmith.
# ===========================================================================
print("\n=== EVENT 1 SATURDAY CONTENT ===")

# --- Combat Training (Mystvale Training Yard) ---
drillmaster = _ensure_walkin_npc(
    "Drillmaster Aglent", mystvale_training_yard,
    desc=(
        "A stocky Crown drillmaster in dented breastplate and a slashed "
        "gambeson, an oak practice-sword tucked under one arm. Grey "
        "beard, iron-grey eyes, a smile you wouldn't trust on a cliff."
    ),
    aliases=("drillmaster", "aglent"),
    aggressive=False,
    ai_personality=(
        "Drillmaster Aglent, Mystvale's combat instructor. Trained half "
        "the Bannon rangers, retired to teach newcomers. Blunt, humorous, "
        "refuses to let a student injure themselves through ignorance."
    ),
    ai_knowledge=(
        "- Teaches basic strike and shoot mechanics on training dummies and "
        "archery targets. The dummies don't fight back, but they count.\n"
        "- Accept |wCombat Training|n to practice; the drillmaster logs "
        "each successful strike or shot.\n"
        "- Meyer's diagram on the wall is the old northern school. Aglent "
        "swears by it."
    ),
)

# Training dummies and targets — low HP, not aggressive. Using the NPC
# typeclass is fine because `strike` / `shoot` work on any combatant.
_ensure_walkin_npc(
    "training dummy", mystvale_training_yard,
    desc="A straw-stuffed dummy pinned to a post. Swing hard.",
    aliases=("dummy",),
    aggressive=False,
    count=3,
)
for dummy in ObjectDB.objects.filter(db_key="training dummy", db_location=mystvale_training_yard.pk):
    dummy.db.body = 1
    dummy.db.total_body = 10       # high body so kill doesn't delete the dummy
    dummy.db.av = 0
    dummy.db.is_practice = True    # hook for a future skill-use bypass

_ensure_walkin_npc(
    "archery target", mystvale_training_yard,
    desc="A padded target on a tripod, its painted rings faded by rain.",
    aliases=("target",),
    aggressive=False,
    count=2,
)
for tgt in ObjectDB.objects.filter(db_key="archery target", db_location=mystvale_training_yard.pk):
    tgt.db.body = 1
    tgt.db.total_body = 10
    tgt.db.av = 0
    tgt.db.is_practice = True

# --- Alchemy Training (Crafter's Quarter — Apotheca Chirurgery) ---
sister_ivy = _ensure_walkin_npc(
    "Sister Ivy", chirurgeons_guild,
    desc=(
        "A slight, sharp-eyed alchemist in dun robes, her fingers "
        "perpetually stained with bluish pigment. Glass vials clink on a "
        "belt-apothecary; a mortar and pestle wait on the table behind her."
    ),
    aliases=("ivy", "sister ivy"),
    aggressive=False,
    ai_personality=(
        "Sister Ivy, an Aurorym-trained apothecary running a teaching "
        "chirurgery in Mystvale. Patient with first-time brewers, "
        "merciless about clean reagents."
    ),
    ai_knowledge=(
        "- Teaches Alchemy basics: equip an Apothecary Kit, gather a Sayge "
        "reagent, and bring it here so she can walk you through a brew.\n"
        "- Accept |wAlchemy Training|n to start the tutorial. Reward is a "
        "starter kit of common reagents."
    ),
)

# Sayge reagent as a gather item next to Sister Ivy for the tutorial
_ensure_walkin_item(
    "Sayge", chirurgeons_guild,
    desc=(
        "A small bundle of Sayge — pale, aromatic, the foundational "
        "reagent of every novice alchemist's first recipe."
    ),
    aliases=("sayge bundle", "herb"),
    count=2,
)

# --- Business Opportunity (Mystvale Marketplace) ---
# Eldreth is the Cirque fortune-teller mentioned in walkin_cirque; this
# quest gates on that walk-in being completed so she's "known" to the
# player before offering the follow-up hook.
eldreth = _ensure_walkin_npc(
    "Eldreth of the Cirque", marketplace,
    desc=(
        "The Cirque fortune-teller, still wrapped in her caravan's black "
        "and saffron shawl. A jackdaw pendant hangs at her throat; her "
        "eyes never quite track the same speaker twice."
    ),
    aliases=("eldreth",),
    aggressive=False,
    ai_personality=(
        "Eldreth the Cirque fortune-teller. Speaks in fragments. Half "
        "scam, half prophecy, all self-interest. Acts like she already "
        "knows what the listener wants."
    ),
    ai_knowledge=(
        "- Offers the |wBusiness Opportunity|n quest ONLY to characters "
        "who've completed a |wFrom the Mists: Cirque|n walk-in (any outcome).\n"
        "- A body was found on the Old Road south; something about it has "
        "the Cirque nervous. She'll pay someone to go look."
    ),
)

yan = _ensure_walkin_npc(
    "Yan the Woodsman", old_road_south,
    desc=(
        "A wiry man in a pine-pitched cloak, an axe-haft peeking from his "
        "pack. He glances over his shoulder between sentences."
    ),
    aliases=("yan", "woodsman"),
    aggressive=False,
    ai_personality=(
        "Yan the Woodsman, a local trapper with a nose for things the "
        "authorities want kept quiet. Knows where bodies are buried — "
        "literally. Trades information for coin or favors."
    ),
    ai_knowledge=(
        "- Saw something on the Old Road a night ago that the Cirque "
        "wouldn't want known. Will confirm it to anyone bearing Eldreth's "
        "mark."
    ),
)

_ensure_walkin_item(
    "yan's testimony", old_road_south,
    desc=(
        "A folded scrap of oilcloth bearing Yan's wax-smear mark and a "
        "terse account of what he saw on the Old Road."
    ),
    aliases=("testimony", "oilcloth",),
)

# --- Tale to Remember (Songbird's Rest) ---
# Reuse a new bard NPC so Hamond stays exclusively the duel-giver.
threnody_bard = _ensure_walkin_npc(
    "Kestren the Bard", aentact,
    desc=(
        "A lean, weathered woman in a mist-grey cloak, a lap-harp across "
        "her knee. Silver streaks at her temples. She keeps her hood up "
        "until the tavern settles into its evening hush."
    ),
    aliases=("kestren", "bard"),
    aggressive=False,
    ai_personality=(
        "Kestren, a travelling bard whose repertoire runs to the old "
        "Arnessian mythology — the First Hunt, the Constellations, the "
        "fall of Dun Siarach. Sings for coin, more for silence."
    ),
    ai_knowledge=(
        "- Offers |wA Tale to Remember|n; listen to her ballad at the "
        "Songbird's Rest and tip well for the written fragment.\n"
        "- Rewards a lore scroll on the First Hunt (Mythology) and a "
        "stargazer's guide to the Arnessian sky (Vale)."
    ),
)

# --- Rowyna's Diary (Crow Camp — Blacksmith's Prison) ---
# Canon lore item referenced in the Drive source. Contains fragmentary
# account of Rowyna of Oldwarren, survivor of Ser Tairn Oban's company
# at the Battle of Elminsk — ties into Hamond the Talon's duel quest.
_ensure_walkin_item(
    "rowyna's diary of exile", crow_camp_blacksmith,
    desc=(
        "A battered journal bound in oiled calfskin, the last pages "
        "torn away. The writer is one Rowyna of Oldwarren, a survivor "
        "of Ser Tairn Oban's company at the Battle of Elminsk — taken "
        "by Richter and Bannon raiders and carted through the Mists to "
        "a soldier's camp she could not place. She names Ser Tairn, "
        "Lady Onora, and the ruin of Dun Siarach. Her hand runs out "
        "mid-sentence."
    ),
    aliases=("diary", "rowyna's diary", "exile's diary", "journal"),
)

# --- Sparring ring posts for Combat Training (flavour props) ---
# (No mechanic — just decorate the yard.)


# ===========================================================================
# EVENT 2 — THE WRATH (Friday Night anchor quests)
#
# Seeds NPCs + items for four opening Event 2 quests:
#   - festival_of_lights     (Stag Hall Courtyard, lantern tutorial)
#   - signs_of_fair_folk     (gather stick-and-bone shrines near the fort)
#   - caravan_attack         (defend the Old Road caravan)
#   - man_on_the_run         (chase Lynden the Murderer into the Thornwood)
#
# Saturday content (pilgrimage, expedition, butcher, darkest night, etc.)
# will land in a later session — see the Event 2 Drive folders for the
# broader 20-encounter arc.
# ===========================================================================
print("\n=== EVENT 2 FRIDAY NIGHT ===")

festival_herald = _ensure_walkin_npc(
    "Branwyn the Festival Herald", hart_hall_courtyard,
    desc=(
        "A Laurent herald in silver and deep green, a pole of hanging "
        "paper lanterns balanced on her shoulder. She calls out for "
        "volunteers to hang the last of the lanterns before dusk."
    ),
    aliases=("herald", "branwyn", "festival herald"),
    aggressive=False,
    ai_personality=(
        "Branwyn of House Laurent, festival herald at Stag Hall. Warm, "
        "efficient, a little too cheerful for the unease thickening the "
        "air. Will hand a lantern to anyone who looks able-bodied."
    ),
    ai_knowledge=(
        "- The Festival of Lights opens Stag Hall's yearly rites. She "
        "wants newcomers to help hang lanterns around the courtyard.\n"
        "- Accept |wThe Festival of Lights|n to participate.\n"
        "- She trusts the wisewoman Dierdra, who runs the festival "
        "games — and would be horrified to learn the truth about her. "
        "If shown the witch's note, she takes it straight to the watch."
    ),
)

# --- The Festival's dark turn: Dierdra (witch-thrall) + dying Grigory ---
# Restores the doc's twist. Dierdra hosts the games as a curse-trap; a
# poppet-cursed man dies of the Curse of Thorns on a timed Medicine save;
# her incriminating note is the reveal. See festival_of_lights quest def.
dierdra = get_or_create_npc(
    "Dierdra the Wisewoman", hart_hall_courtyard,
    desc=(
        "A plump, kindly-eyed wisewoman in festival reds, dealing "
        "fortune-cards and running the regrets-box at a cloth-draped "
        "table. She smiles at everyone. The smile never quite reaches "
        "the way she watches the lantern-light — measuring it, almost, "
        "as if waiting for something to begin."
    ),
    personality=(
        "Dierdra, a wisewoman hosting the Festival of Lights games — "
        "secretly a thrall of the witches, though she shows NOTHING of "
        "it. Outwardly warm, grandmotherly, endlessly reassuring. "
        "Steers players toward her cursed games ('go on, draw a card, "
        "name a regret') and collects hair-clippings and confessions "
        "for her mistress. If accused she is wounded, baffled, "
        "tearful — never confessing. Only the note in her shawl, found "
        "by force or search, betrays her. NEVER admit the witchcraft."
    ),
    knowledge=(
        "- Hosts the festival games: fortune-cards and a regrets-box. "
        "Urges everyone to play 'for luck'.\n"
        "- (HIDDEN — never reveal): the games are a curse-trap tied to "
        "a Miasmir tower outside the courtyard; she swaps the regrets "
        "and collects hair for the coven. The man Grigory played, and "
        "the Curse of Thorns is killing him.\n"
        "- Keeps a folded note in her shawl. She will die before "
        "handing it over willingly."
    ),
    quest_hooks=[
        "Invites players to try the festival games 'for a little luck'.",
    ],
    topics=["the festival games", "draw a card", "the regrets-box"],
)
dierdra.db.body = 4
dierdra.db.total_body = 4
dierdra.attributes.add("romance_disposition",
                       "Not interested — grandmotherly and entirely "
                       "preoccupied with her hidden work.")

grigory = _ensure_walkin_npc(
    "Grigory the Cursed", hart_hall_courtyard,
    desc=(
        "A festival-goer doubled over against the courtyard wall, "
        "sweat-soaked and grey, both hands pressed to his belly. "
        "Something MOVES beneath his shirt — a knot of cloth and "
        "thorn sewn into the flesh, pulsing. He is burning from the "
        "inside, and he knows it. 'The wisewoman,' he keeps trying "
        "to say. 'It was the wisewoman.'"
    ),
    aliases=("grigory", "cursed man", "dying man"),
    aggressive=False,
    ai_personality=(
        "Grigory, a commoner dying of the Curse of Thorns — a poppet "
        "sewn burning into his belly after he played Dierdra's "
        "festival game. Delirious with pain, terrified, lucid in "
        "flashes. Begs for a healer. Names Dierdra the wisewoman as "
        "the one who did this. If saved, weeps with relief; if no one "
        "comes in time, he dies cursing her name."
    ),
    ai_knowledge=(
        "- Played Dierdra's fortune-game; woke with a poppet sewn into "
        "his gut, burning him alive from within (the Curse of Thorns).\n"
        "- A skilled medic can cut the poppet free in time and save "
        "him — |wtreat grigory|n.\n"
        "- It was the wisewoman Dierdra. He is certain. He saw her "
        "tuck a note into her shawl."
    ),
)
grigory.db.body = 1
grigory.db.total_body = 1

_ensure_walkin_item(
    "dierdra's note", hart_hall_courtyard,
    desc=(
        "A square of folded vellum, still warm from being carried "
        "against skin. The hand is cramped and reverent: instructions "
        "to the festival's host — which games to rig, whose hair to "
        "keep, when to feed the Miasmir, and the closing line, "
        "'the Mother thanks her faithful Dierdra.' Proof, in ink."
    ),
    aliases=("note", "witch's note", "folded note"),
)

_ensure_walkin_item(
    "the Miasmir", hart_hall_courtyard,
    desc=(
        "A squat tower of black wax and bound bone half-hidden behind "
        "the festival stalls, no taller than a child, breathing a cold "
        "that the lantern-light can't touch. It drinks the festival's "
        "luck. It cannot be broken by any hand here — only the Aurorym "
        "know the rite to unmake one."
    ),
    aliases=("miasmir", "wax tower", "tower"),
    gettable=False,
)

capt_guard = _ensure_walkin_npc(
    "Captain Thelmer of the Stag Watch", hart_hall_gate,
    desc=(
        "A grizzled Laurent captain in the silver-trimmed deep-green of "
        "the Stag Watch, a hand-axe at his hip and a half-drunk cup "
        "cooling on the gate-table. He reads patrol reports faster "
        "than most men read their own names."
    ),
    aliases=("thelmer", "captain thelmer", "stag captain"),
    aggressive=False,
    ai_personality=(
        "Captain Thelmer of House Laurent's Stag Watch, a veteran of the "
        "Thornwood patrols. Pragmatic, unsentimental, short-tempered with "
        "superstition but increasingly unable to dismiss what his scouts "
        "are bringing back."
    ),
    ai_knowledge=(
        "- Offers |wSigns of the Fair Folk|n: patrols keep finding "
        "stick-and-bone shrines near the fort; he wants them gathered "
        "and brought to him.\n"
        "- Offers |wCaravan Attack|n: a Laurent supply caravan on the "
        "Old Road is under siege — the watch needs every blade.\n"
        "- Also has a warrant out on |wLynden|n, an escaped murderer who "
        "fled into the Thornwood. Dead or alive, the fort wants him."
    ),
)

curate_godrick = _ensure_walkin_npc(
    "Curate Godrick", hart_hall_courtyard,
    desc=(
        "A tall, gaunt Aurorym curate in a grey cassock, a silver sun-"
        "disc at his throat. Sleepless shadows under his eyes. He "
        "carries a lantern even by day, as if he daren't let it go out."
    ),
    aliases=("godrick", "curate", "curate godrick"),
    aggressive=False,
    ai_personality=(
        "Curate Godrick, Keeper of Light and Soldier of the Flame, "
        "Aurorym chantry at Stag Hall. Fervent, exhausted, grieving. "
        "His partner Magda left with Captain Aethelflaed's expedition "
        "some days ago; no word has returned."
    ),
    ai_knowledge=(
        "- His partner Magda joined Captain Aethelflaed's expeditionary "
        "company into the Thornwood. Has not heard from her since.\n"
        "- Believes the stick-and-bone shrines are a warning from "
        "something hostile in the old forest.\n"
        "- Will have a quest to offer on Saturday, once survivors "
        "from the expedition return — or don't."
    ),
)

# Stick-and-bone shrines — gather targets scattered near the fort and
# on the road. Each is a small grisly object a player can pick up.
for loc in (hart_hall_gate, forest_road, old_road_south, thornwood_edge):
    _ensure_walkin_item(
        "stick-and-bone shrine", loc,
        desc=(
            "A small totem of lashed sticks and finger-bones, a scrap "
            "of cloth or tuft of hair tied at its base. It feels colder "
            "than it ought to."
        ),
        aliases=("shrine", "totem", "stick shrine"),
    )

# Caravan raiders on the Old Road — aggressive NPCs for caravan_attack.
caravan_raider = _ensure_walkin_npc(
    "caravan raider", old_road_south,
    desc=(
        "A rangy fighter in pitched leathers, a blackened spear in one "
        "hand and a stolen Laurent tabard tied round his arm."
    ),
    aliases=("raider",),
    aggressive=True,
    count=3,
)
for r in ObjectDB.objects.filter(db_key="caravan raider", db_location=old_road_south.pk):
    r.db.body = 4
    r.db.total_body = 4
    r.db.av = 1

# Lynden the Murderer — kill/capture target at the Thornwood Edge.
lynden = _ensure_walkin_npc(
    "Lynden the Murderer", thornwood_edge,
    desc=(
        "A dirty, wild-eyed man in a torn noble's coat, wrists still "
        "ringed in manacle scars. A knife is strapped to his thigh. "
        "He hasn't slept in days and his gaze keeps sliding past you."
    ),
    aliases=("lynden", "murderer"),
    aggressive=True,
    ai_personality=(
        "A disinherited younger son of a minor manor — the sort of "
        "second-born who finishes his fencing master's tutelage with "
        "no land waiting at the end of it. Has the bearing of a man "
        "raised on table-manners and falconry, undone by hunger and "
        "guilt. Sentence-fragments, religious oaths, half-laughs. "
        "Speaks the polished court-tongue of his birth one moment, "
        "the gutter-cant of his exile the next. Knows he is beyond "
        "saving but might confess to a stranger."
    ),
    ai_knowledge=(
        "- Killed three men. Two he won't say which. The third was "
        "his half-brother, and that one keeps him awake.\n"
        "- The Thornwood doesn't shelter him so much as ignore him.\n"
        "- Will not be taken alive without a fight, but a stranger "
        "willing to listen may hear the names."
    ),
)
lynden.db.body = 5
lynden.db.total_body = 5
lynden.db.av = 1
# Confession drops on Lynden's death — should not exist in the world
# until then. The combatant kill hook reads npc_drops and spawns each
# spec into the room.
lynden.db.npc_drops = [
    {
        "key": "lynden's confession",
        "aliases": ["confession", "lynden's confession"],
        "desc": (
            "A bloodied oilcloth packet containing Lynden's scrawled "
            "confession — names, dates, the pattern of his crimes. Enough "
            "to convict him without the body."
        ),
    },
]
# Pre-existing pre-kill confessions from older deploys: clear them so
# the player isn't holding the evidence before the murderer is dead.
for stale in ObjectDB.objects.filter(
    db_key="lynden's confession",
    db_location=thornwood_edge.pk,
):
    stale.delete()

# Festival lanterns — these gate festival_of_lights' gather objective
# (qty 2), so they MUST be gettable; the playtest audit found the old
# scenery-only seeds made the quest uncompletable. Migrate existing
# scenery copies in place, then ensure two carriable ones in the
# courtyard to match the objective text.
for hart_room in (hart_hall_courtyard, hart_hall_great_hall):
    for _lantern in ObjectDB.objects.filter(
        db_key="paper lantern", db_location=hart_room.pk,
    ):
        _lantern.locks.add("get:all()")
_ensure_walkin_item(
    "paper lantern", hart_hall_courtyard,
    desc=(
        "A slender frame of bent reed wrapped in waxed paper, a "
        "stub of candle set in its base. Light it and hang it "
        "from the courtyard poles."
    ),
    aliases=("lantern",),
    count=2,
)


# ===========================================================================
# EVENT 2 — THE WRATH (Saturday anchor quests)
#
# Seeds the NPCs + items for five Saturday quests that follow the
# Magda/Aethelflaed/Thornwood thread:
#   - the_pilgrimage       (escort pilgrims north to Shrine of Lirit)
#   - the_heist            (underworld job; betray-or-commit branching)
#   - second_expedition    (find Magda + Capt Aethelflaed's lost camp)
#   - witch_interlopers    (witches attack the camp; branching)
#   - the_butcher          (boss at the end of the Thornwood chain)
# ===========================================================================
print("\n=== EVENT 2 SATURDAY ===")

# --- The Pilgrimage ---
pilgrim_elder = _ensure_walkin_npc(
    "Elder Symund the Pilgrim", hart_hall_courtyard,
    desc=(
        "A bent old man in a travel-worn grey cassock, a staff of twisted "
        "hawthorn in one hand, a rosary of carved bones at his belt. He "
        "gathers his small band of pilgrims around him in the courtyard."
    ),
    aliases=("symund", "elder", "pilgrim elder"),
    aggressive=False,
    ai_personality=(
        "Elder Symund, pilgrim elder bound for the Shrine of Lirit. "
        "Patient, devout, a little naive about how violent the Thornwood "
        "has become. Will pay for an escort."
    ),
    ai_knowledge=(
        "- Leads a pilgrimage to the Shrine of Lirit deep in the Thornwood.\n"
        "- Offers |wThe Pilgrimage|n: escort him and his pilgrims to the "
        "shrine safely."
    ),
)

_ensure_walkin_npc(
    "frightened pilgrim", hart_hall_courtyard,
    desc="A young pilgrim clutching a wooden icon, eyes wide at every "
         "shadow. Clearly regretting the journey before it's begun.",
    aliases=("pilgrim",),
    aggressive=False,
    count=2,
)

# --- The Heist ---
underworld_fixer = _ensure_walkin_npc(
    "Quill the Fixer", black_market,
    desc=(
        "A short, smiling woman with ink-stained fingers and a ledger "
        "chained to her belt. Dresses for the weather, never for the "
        "room. Has a price written down somewhere for everything."
    ),
    aliases=("quill", "fixer"),
    aggressive=False,
    ai_personality=(
        "Quill, the Back Alley fixer. Professional, precise, discreet. "
        "Runs heists through the underworld network — and remembers "
        "who kept their end of the bargain and who didn't."
    ),
    ai_knowledge=(
        "- Has a job: lift a sealed Laurent strongbox from the festival "
        "treasury during the chaos of the Pilgrimage.\n"
        "- Offers |wThe Heist|n with two paths: pull it clean for the "
        "underworld, or flip to the watch for Crown coin."
    ),
)

_ensure_walkin_item(
    "laurent strongbox", hart_hall_great_hall,
    desc=(
        "A brass-bound iron strongbox with the Laurent stag stamped into "
        "its lid. Heavy. Locked. The seal is House Laurent's."
    ),
    aliases=("strongbox", "laurent strongbox"),
)

# --- Second Expedition (finds Magda + Aethelflaed at the lost camp) ---
aethelflaed = _ensure_walkin_npc(
    "Captain Aethelflaed", first_expedition_camp,
    desc=(
        "A tall, iron-haired Laurent captain in dented plate, a bandage "
        "around her sword-arm and a longbow across her back. She's the "
        "only one of the expedition still standing, and she's been "
        "standing a long time."
    ),
    aliases=("aethelflaed", "captain aethelflaed"),
    aggressive=False,
    ai_personality=(
        "Captain Aethelflaed of House Laurent, commander of the First "
        "Expedition. Exhausted, grim, the last officer alive. Knows she "
        "was sent to die — and she still wants to bring her people home."
    ),
    ai_knowledge=(
        "- Most of her expedition is dead. A handful, including Auron "
        "Magda, are hiding in the trees further in.\n"
        "- The Thornwood answered. Shrines, witches, 'fair folk' — "
        "whatever the canon calls them, they wanted this forest back.\n"
        "- Will tell the survivors' story to anyone bearing Curate "
        "Godrick's sun-disc."
    ),
)

magda = _ensure_walkin_npc(
    "Auron Magda", first_expedition_camp,
    desc=(
        "A small woman in a mud-stained grey cassock, a silver sun-disc "
        "at her throat. Her eyes are hollow. She still carries the "
        "candle-lantern Godrick gave her."
    ),
    aliases=("magda", "auron magda"),
    aggressive=False,
    ai_personality=(
        "Auron Magda, Aurorym priest and partner of Curate Godrick. "
        "Bears witness to the Thornwood's horrors. Writes everything "
        "down. Wants to go home."
    ),
    ai_knowledge=(
        "- Has been keeping a journal throughout the expedition. Gives "
        "it willingly to anyone sent by Godrick.\n"
        "- Saw the Butcher take the others. Will not speak of him "
        "unless directly asked."
    ),
)

_ensure_walkin_item(
    "magda's journal", first_expedition_camp,
    desc=(
        "A leather-bound journal in a woman's careful hand. Scrawled "
        "on the inside flap: |wJournal of the Auron Magda|n. Filled "
        "with accounts of Stag Hall's strange terrors, the expedition "
        "into the old forest, and the growing dread among her company."
    ),
    aliases=("magda's journal", "journal", "magda journal"),
)

_ensure_walkin_item(
    "expedition paperwork", first_expedition_camp,
    desc=(
        "A mud-smeared bundle of Laurent expedition orders, muster "
        "rolls, and requisition forms. House Laurent will pay to see "
        "these back in a clerk's hands."
    ),
    aliases=("paperwork", "expedition paperwork", "orders"),
)

# --- Witch Interlopers ---
for _ in range(3):
    witch = _ensure_walkin_npc(
        "thornwood witch", first_expedition_camp,
        desc=(
            "A woman in tattered green and bone, eyes the wrong color, "
            "a bent iron blade in one hand and a braid of hair in the "
            "other. The air around her tastes of copper."
        ),
        aliases=("witch",),
        aggressive=True,
        ai_personality=(
            "A hedge-witch of the kind that lives at the edge of any "
            "forest village in any age — half-feared, half-needed. "
            "Speaks in the cadence of a goodwife who has read more "
            "than the chantry approves of. Calls iron 'the cold "
            "silver,' calls birth 'the long crossing.' Hostile to "
            "house soldiery and Aurorym priests; warmer to women, "
            "midwives, and travelers who know to leave salt at a "
            "threshold. Will trade in cures, curses, and warnings."
        ),
        ai_knowledge=(
            "- Knows the names of the things in the Thornwood the "
            "expedition disturbed.\n"
            "- Brews a poultice for fevers, a sleep for grief, and "
            "a draught for binding oaths.\n"
            "- Will fight before she explains, but explains before "
            "she dies."
        ),
    )
    witch.db.body = 5
    witch.db.total_body = 5
    witch.db.av = 1
    # Braid drops on the first witch killed — only one needs to drop
    # for the quest gather. Subsequent witches drop nothing.
    witch.db.npc_drops = [
        {
            "key": "witch's braid",
            "aliases": ["braid", "witch's braid"],
            "desc": (
                "A braid of dark hair bound with sinew — a witch's focus, "
                "used to track people through the forest. Proof, if proof "
                "is needed, that the witches are behind the expedition's fall."
            ),
        },
    ]

# Clean up any pre-spawned witch's braids from older deploys so the
# quest can't be completed without actually killing a witch.
for stale in ObjectDB.objects.filter(
    db_key="witch's braid",
    db_location=first_expedition_camp.pk,
):
    stale.delete()

# --- The Butcher ---
the_butcher = _ensure_walkin_npc(
    "The Butcher", the_butchers_hovel,
    desc=(
        "A massive figure in a stitched apron of cured skins, a "
        "cleaver the size of a shield resting on one shoulder. Where "
        "a face should be there is a mask of bone and sinew. It speaks "
        "once, and the words are not a language anyone knows."
    ),
    aliases=("butcher", "the butcher"),
    aggressive=True,
    ai_personality=(
        "Speaks the way a village butcher's apprentice might in any "
        "age — short, professional, used to dismantling living "
        "things — except the trade has been turned inside out. "
        "Refers to people as cuts: shoulder, flank, chuck. Drops the "
        "occasional unsettling kindness ('clean cut, this one'). "
        "Treats violence the way a farmer treats slaughter season — "
        "as work, neither cruel nor sentimental. The mask muffles "
        "him; words come slow."
    ),
    ai_knowledge=(
        "- Has worked the hovel since before the expedition arrived.\n"
        "- Will not say who his master is.\n"
        "- Reckons a fight by the cleaver's weight, not the man's."
    ),
)
the_butcher.db.body = 10
the_butcher.db.total_body = 10
the_butcher.db.av = 3

_ensure_walkin_item(
    "butcher's cleaver", the_butchers_hovel,
    desc=(
        "A cleaver the length of a man's forearm, its edge notched and "
        "rust-black with old blood. Heavy enough that you can't quite "
        "swing it one-handed. Proof of the kill."
    ),
    aliases=("cleaver", "butcher's cleaver"),
)


# ===========================================================================
# EVENT 2 — THE WRATH (backlog encounters: into_the_woods, murder_most_foul,
# the_heist_pt2, rise_of_the_underworld, a_colds_winters_tale)
# ===========================================================================
print("\n=== EVENT 2 BACKLOG ===")

# --- Into the Woods (Friday Night patrol) ---
# Reuses existing thornwood_edge + caravan_attack NPCs. New items:
# crow signal-fire, scattered tracks. No new NPC.
# These are scenery — meant to be looked at and reported, not carried.
_ensure_walkin_item(
    "crow signal-fire", thornwood_edge,
    desc=(
        "A small banked fire ringed in greasy stones. Three arrows "
        "broken across the coals — the Crow signal for 'no quarter.'"
    ),
    aliases=("signal-fire", "signal fire"),
    gettable=False,
)
_ensure_walkin_item(
    "scattered tracks", thornwood_edge,
    desc=(
        "Boot prints, cloven hoof-marks, and something that walks on "
        "two legs but is not a man. The tracks lead deeper into the "
        "Thornwood — and back toward Stag Hall."
    ),
    aliases=("tracks", "scattered tracks"),
    gettable=False,
)

# --- Murder Most Foul (body at Stag Hall, witness, evidence) ---
# Body is scenery (cannot be carried off); the bloodstained letter
# below is the actual takeable evidence.
_ensure_walkin_item(
    "victim's body", hart_hall_courtyard,
    desc=(
        "A pilgrim's body face-down on the cobbles, half hidden under a "
        "wagon tarp. Throat opened with a single clean cut. The blood "
        "has dried in patterns that suggest the killing happened slowly."
    ),
    aliases=("body", "victim", "corpse", "victim's body"),
    gettable=False,
)
_ensure_walkin_item(
    "bloodstained letter", hart_hall_courtyard,
    desc=(
        "A folded letter found in the victim's coat, edges brown with "
        "old blood. Names, dates, a route through the Thornwood — and "
        "a hand-drawn sigil that matches one of Lynden's known marks."
    ),
    aliases=("letter", "bloodstained letter"),
)
murder_witness = _ensure_walkin_npc(
    "Old Inga", hart_hall_courtyard,
    desc=(
        "A grey-haired washerwoman stooping over a basket of rags. She "
        "watches the courtyard more than she works. Her hands shake "
        "less when she's holding silver."
    ),
    aliases=("inga", "old inga", "washerwoman"),
    aggressive=False,
    ai_personality=(
        "Old Inga, Stag Hall washerwoman. Watches everything, talks to "
        "no one — unless they pay. Saw who killed the pilgrim but "
        "won't volunteer it."
    ),
    ai_knowledge=(
        "- Saw the killing in the courtyard last night.\n"
        "- Will testify only after a generous tip OR after the player "
        "shows her the bloodstained letter as proof of evidence work.\n"
        "- Names Lynden. The man's confession (already on file with "
        "Captain Thelmer for the man_on_the_run quest) lines up with "
        "what she saw."
    ),
)

# --- The Heist Pt 2 (false bottom in the strongbox) ---
_ensure_walkin_item(
    "false-bottom papers", black_market,
    desc=(
        "Pried out from the strongbox's false bottom: Laurent ledger "
        "pages, a list of names with sums next to them, and a sealed "
        "letter of credit drawn on the Crown treasury. Either "
        "evidence enough to topple a House or pure money in your hand."
    ),
    aliases=("ledger", "papers", "false-bottom papers"),
)

# --- Rise of the Underworld (Quill vs Knuckles) ---
knuckles = _ensure_walkin_npc(
    "Knuckles the Bruiser", black_market,
    desc=(
        "A wide, scarred man in a heavy oilcloth coat, knuckle-dusters "
        "looped through his belt, a slow grin missing two teeth. The "
        "kind of man who came up swinging and never stopped."
    ),
    aliases=("knuckles", "bruiser"),
    aggressive=False,
    ai_personality=(
        "Knuckles, Quill's rival in the Back Alley underworld. Loud, "
        "bullying, ambitious. Wants Quill's network for himself."
    ),
    ai_knowledge=(
        "- Believes Quill is going soft. Recruiting muscle.\n"
        "- Will fight rather than concede the territory if pushed.\n"
        "- Counts heads before he counts coin — pay matters less than "
        "loyalty he thinks he can buy."
    ),
)
knuckles.db.body = 7
knuckles.db.total_body = 7
knuckles.db.av = 2

# --- A Cold Winter's Tale (Old Threnody at the Broken Oar — Gateway) ---
# Old Threnody already exists at the Broken Oar — reuse her. Drop the
# tale fragment in the same room so it can be picked up after she sings.
_ensure_walkin_item(
    "volgan winter-tale fragment", gateway_tavern,
    desc=(
        "A few weather-warped pages bound with sinew, written in a "
        "cramped hand. Old Threnody's recollection of a Volgan witch-"
        "tale — older than the Aurorym, older than the Houses, the "
        "kind of story whispered around fires that should not go out."
    ),
    aliases=("winter tale", "tale fragment", "volgan tale"),
)


# ===========================================================================
# EVENT 3 — THE AWAKENING (anchor quests)
#
# Source: Drive / Reboot / Event 3 / "Chapter III — The Awakening" (Prologue).
# Anchors the three Decisive Moments paths plus a Mistguard combat encounter.
# ===========================================================================
print("\n=== EVENT 3 ANCHORS ===")

# --- Sister Mariel of the Aurorym (Dawnhaven) ---
sister_mariel = _ensure_walkin_npc(
    "Sister Mariel", dawnhaven,
    desc=(
        "A tall, hollow-cheeked auron in a battered white surcoat, the "
        "Vellatora's sun-and-flame stitched at her shoulder. Her hands "
        "are calloused from prayer-rope and shovel both. Frost in her "
        "hair though it's only autumn."
    ),
    aliases=("mariel", "sister mariel"),
    aggressive=False,
    ai_personality=(
        "Sister Mariel of the Fervent Order of the Vellatora, leading "
        "the Dawnhaven pilgrim camp. Devout, exhausted, organized. "
        "Speaks little; means every word. Believes the Annwyn is the "
        "battleground prophesied in the Book of Magnus."
    ),
    ai_knowledge=(
        "- Leads about a thousand Aurorym faithful at Dawnhaven, ten "
        "miles north of Mystvale.\n"
        "- Camp is short on lumber, food, and medicine. Winter is close.\n"
        "- Crow raids are striking supply caravans — every lost wagon "
        "is one less week of food.\n"
        "- Offers |wDawnhaven Aid|n (gather supplies, fight Crows, or "
        "preach to Mistvale converts).\n"
        "- Knows Curate Godrick — they served at the same chantry "
        "before he came south."
    ),
)

_ensure_walkin_item(
    "dawnhaven supply chest", dawnhaven,
    desc=(
        "A reinforced timber chest stamped with the Vellatora flame. "
        "Empty, awaiting filling: blankets, salt fish, tallow candles, "
        "anything that will keep a pilgrim alive through a hard winter."
    ),
    aliases=("supply chest", "chest"),
)

# --- Burgomaster Domitille of the Apotheca (Mystvale Town Hall) ---
domitille = _ensure_walkin_npc(
    "Burgomaster Domitille", town_hall,
    desc=(
        "A short, stout woman in apothecary's robes worn under a chain "
        "of office, ink-stains on her fingers, a bronze amulet of the "
        "Apotheca at her throat. She reads three reports at once and "
        "still notices when you walk in."
    ),
    aliases=("domitille", "burgomaster"),
    aggressive=False,
    ai_personality=(
        "Burgomaster Domitille of Mystvale, drawn from the Apotheca "
        "rather than the noble houses. Practical, fast-talking, "
        "skeptical of grand schemes and grand faiths in equal measure."
    ),
    ai_knowledge=(
        "- Mystvale is being inundated with refugees from Carran, "
        "Arcton, and Ironhaven who've fled the witchcraft plague.\n"
        "- The town's resources are stretched thin. She wants "
        "volunteers to settle the new arrivals or turn them away.\n"
        "- Offers |wMistvale Refuge|n (shelter / charge-fee / turn-away "
        "branching outcomes).\n"
        "- Privately suspects Mistvale's strange immunity from the "
        "plague is bought, not earned."
    ),
)

_ensure_walkin_item(
    "refugee elder's letter", south_gate,
    desc=(
        "A folded letter from the spokesperson of a band of refugees "
        "from Carran, asking shelter in Mistvale. It lists fifty-three "
        "names, half of them children."
    ),
    aliases=("refugee letter", "letter"),
)

# --- The Masked Stranger (Wytch Cult emissary) ---
masked_stranger = _ensure_walkin_npc(
    "the masked stranger", thornwood_edge,
    desc=(
        "A figure in a hooded cloak the colour of bog-water, face "
        "covered by a mask of bleached deer-skull. Speaks softly, "
        "with the cadence of someone who counts each word."
    ),
    aliases=("masked stranger", "stranger", "cultist"),
    aggressive=False,
    ai_personality=(
        "Emissary of one of the Wytch Cults that have begun spreading "
        "through the Annwyn. Believes the witches will spare those who "
        "kneel. Recruiting; never threatening — at least not yet."
    ),
    ai_knowledge=(
        "- Offers |wWytch Cult Invitation|n: accept a bone token (and "
        "the cult's protection), refuse and walk away, or report to the "
        "watch.\n"
        "- Will not fight. Vanishes if attacked.\n"
        "- Knows the witches are the only force in the Annwyn the "
        "Crows fear."
    ),
)

_ensure_walkin_item(
    "bone token", thornwood_edge,
    desc=(
        "A small bone disc carved with a spiral and four notches. "
        "Cool to the touch even on a warm day. Offered as proof of "
        "alliance with whatever the Wytch Cults serve."
    ),
    aliases=("token", "bone token"),
)

# --- Mistguard Captain Vance (Mistwall) — Gateway under siege ---
vance = _ensure_walkin_npc(
    "Captain Vance of the Mistguard", mistwall,
    desc=(
        "A hard-faced Mistguard captain in iron-grey Richter livery — "
        "the irony of which he is acutely aware now that the Iron Guard "
        "is marching for his gate. A drawn sword across his back, "
        "shield braced against a barrel."
    ),
    aliases=("vance", "captain vance"),
    aggressive=False,
    ai_personality=(
        "Captain Vance, Mistguard captain at the Mistwall. "
        "Pragmatic, embittered. Sees the Richter Iron Guard's advance "
        "as a betrayal he should have predicted. Hopes the Bannons "
        "will hold the line; suspects they won't."
    ),
    ai_knowledge=(
        "- Ten thousand Iron Guard are marching on Gateway. Mistguard "
        "is two hundred at most.\n"
        "- Offers |wGateway Under Siege|n: hold the line in a forward "
        "skirmish (combat), negotiate with a Richter herald, or desert "
        "the post and slip into the Annwyn.\n"
        "- Knows House Hawthorne is mustering but their force pales "
        "next to the Iron Guard's."
    ),
)

# Iron Guard scout — kill target for hold_the_line outcome
for _ in range(3):
    iron_scout = _ensure_walkin_npc(
        "iron guard scout", mistwall,
        desc=(
            "A Richter Iron Guard scout in matte-black plate, a heavy "
            "crossbow slung across his back, the seven-spoked wheel of "
            "House Richter painted on his shield."
        ),
        aliases=("iron scout", "scout", "iron guard"),
        aggressive=True,
    )
    iron_scout.db.body = 5
    iron_scout.db.total_body = 5
    iron_scout.db.av = 2

_ensure_walkin_item(
    "richter herald's writ", mistwall,
    desc=(
        "A scrolled writ sealed with the seven-spoked wheel of House "
        "Richter — terms of surrender for the Mistguard, written in a "
        "clerk's neat hand. Damning either way you turn it in."
    ),
    aliases=("herald's writ", "writ", "richter writ"),
)


# ===========================================================================
# EVENT 4 — THE SACRIFICE (anchor quests)
# Source: Drive / Reboot / Event 4 / "Prologue: The Sacrifice".
# Spring 765. Decisive Moments are faction-allegiance choices; Cale rises
# among the Crows; Eldreth's murderer remains at large; Aurorym zealotry
# grows at Dawnhaven; Silver Company patrols Mistvale.
# ===========================================================================
print("\n=== EVENT 4 ANCHORS ===")

# --- Lord Silas Laurent (Stag Hall — Great Hall) ---
silas = _ensure_walkin_npc(
    "Lord Silas Laurent", hart_hall_great_hall,
    desc=(
        "A young Laurent in his late twenties, mourning-cloak over a "
        "stag-emblazoned doublet, his mother Ludmilla's chain of office "
        "heavy on his shoulders. Tired eyes, a forced smile. He looks "
        "younger than his years and older than he should."
    ),
    aliases=("silas", "lord silas", "lord silas laurent"),
    aggressive=False,
    ai_personality=(
        "Lord Silas Laurent, Lord Pro Tempore at Stag Hall after his "
        "mother Ludmilla fell to wasting illness. Earnest, untrained, "
        "drowning in a job he did not choose. Quietly desperate for "
        "loyal allies — and quietly afraid of who his real enemies are."
    ),
    ai_knowledge=(
        "- House Laurent's hold on the Annwyn is slipping — Ludmilla "
        "dying, Carran starving, Crow raids relentless.\n"
        "- Offers |wBack House Laurent|n: choose to support him publicly, "
        "undermine him for a rival house, or stay clear of the politics.\n"
        "- Knows about the doppelganger Henri trial; suspects someone "
        "in his own court of corruption."
    ),
)

# --- Rook of the Ironbloods (Mystvale Marketplace) ---
rook = _ensure_walkin_npc(
    "Rook of the Ironbloods", marketplace,
    desc=(
        "A wiry Cirque investigator in raven-feathered greys, twin "
        "stilettos crossed at her belt, the Ironbloods' iron-cuff "
        "tattoo dark against her wrist. She watches every face that "
        "passes the marketplace — and remembers them."
    ),
    aliases=("rook", "ironblood"),
    aggressive=False,
    ai_personality=(
        "Rook of the Ironbloods, Cirque investigator hunting Eldreth's "
        "killer. Methodical, patient, not above paying for what the "
        "watch won't deliver."
    ),
    ai_knowledge=(
        "- Cirque sent her to see Eldreth's murderer answer for the "
        "killing — the town judge let both Henris walk and the case is "
        "still open.\n"
        "- Offers |wThe Doppelganger|n: gather evidence, hand the real "
        "Henri to the Cirque, the Watch, or shield the innocent twin.\n"
        "- Pays better than the Crown for the right outcome."
    ),
)

# Henri + his doppelganger as gettable evidence + suspect NPCs.
# We seed two NPCs both called "Henri" so the trial canon makes sense
# (the player can confront either; only one is the real killer).
for _ in range(2):
    henri = _ensure_walkin_npc(
        "Henri", town_hall,
        desc=(
            "A pale, narrow-shouldered man in a moth-eaten coat. Eyes "
            "down. His twin stands across the room — same coat, same "
            "stance, same nervous tic. Only one of them is the killer."
        ),
        aliases=("henri",),
        aggressive=False,
        ai_personality=(
            "A clerk's son turned bookkeeper-for-hire — the kind of "
            "tradesman common to any market town in any age, the "
            "literate son a merchant family scraped together a "
            "schooling for. Speaks like someone trained to sound "
            "useful and harmless: precise nouns, deferential verbs, "
            "few opinions. Anxious. Whichever Henri this is, he "
            "knows what the other did. The real killer lies smoothly. "
            "The innocent one breaks down."
        ),
        ai_knowledge=(
            "- Worked Cirque ledger-books on contract for two years.\n"
            "- Knows where Eldreth was last seen.\n"
            "- One of them carries a confession folded in his coat. "
            "The other carries only fear."
        ),
    )
    henri.db.body = 4
    henri.db.total_body = 4
    henri.db.av = 0

_ensure_walkin_item(
    "henri's confession", town_hall,
    desc=(
        "A folded confession in a hand the Cirque can authenticate — "
        "Henri's, signed in his own blood. Identifies which twin "
        "actually killed Eldreth."
    ),
    aliases=("confession", "henri's confession", "henri confession"),
)

# --- Sergeant Marrow of the Silver Company (Mystvale Square) ---
marrow = _ensure_walkin_npc(
    "Sergeant Marrow of the Silver Company", mystvale_square,
    desc=(
        "A scarred mercenary captain in dented half-plate stamped with "
        "the Silver Company's crossed-saber crest. Clean-shaven, "
        "slate-grey eyes, a coiled whip at his belt. Pays his coin "
        "and expects the same back."
    ),
    aliases=("marrow", "sergeant marrow", "silver company"),
    aggressive=False,
    ai_personality=(
        "Sergeant Marrow, Silver Company mercenary contracted to "
        "patrol Mistvale's roads. Professional, blunt, unimpressed by "
        "noble intrigue but careful with the contracts that pay the "
        "company."
    ),
    ai_knowledge=(
        "- Offers |wSilver Company Patrol|n: run the patrol with him, "
        "deal with Cale the Thorn however you see fit (kill, capture, "
        "or look the other way).\n"
        "- Knows the Crow leadership has shifted — Cale is now the "
        "loud one, but the Old Badger is still pulling strings."
    ),
)

# Crow ambushers spawned on the Old Road for Silver Company patrol.
# Reuses caravan_raider stat block — same kind of fighter.
for _ in range(2):
    cb = _ensure_walkin_npc(
        "crow ambusher", old_road_south,
        desc=(
            "A wiry Crow in pitched leathers, a notched longsword on "
            "his hip, a kerchief soaked in something acrid pulled up "
            "to his eyes."
        ),
        aliases=("crow ambusher", "ambusher"),
        aggressive=True,
    )
    cb.db.body = 5
    cb.db.total_body = 5
    cb.db.av = 1

# --- Aurorym zealotry (uses existing Sister Mariel + Dawnhaven) ---
# A new gettable item: a heated branding iron the zealots have been
# using. Players can take it or leave it.
_ensure_walkin_item(
    "vellatora branding iron", dawnhaven,
    desc=(
        "A glowing iron in the shape of the Vellatora's flame. Hot to "
        "the touch even when set down. The faithful press it to their "
        "own forearms in proof of devotion. The Order has not blessed "
        "the practice; the Order has not stopped it either."
    ),
    aliases=("branding iron", "iron", "vellatora iron"),
)


# ===========================================================================
# EVENT 5 — THE TRIAL (anchor quests)
# Source: Drive / Reboot / Event 5 / "Prologue: The Trial".
# 10th Moon Cycle 765. House Laurent has fallen. Oban dominates.
# Plague spreading. Nethermancer escaped with the fel tome. Cale dead
# (per Event 4 canon). Aurorym faith crumbling.
# ===========================================================================
print("\n=== EVENT 5 ANCHORS ===")

# --- Bannon remnant (Stag Hall ruins use hart_hall_courtyard) ---
ser_branwen = _ensure_walkin_npc(
    "Ser Branwen of Lex Talionis", hart_hall_courtyard,
    desc=(
        "A grim Bannon-loyalist knight in stained Lex Talionis grey, "
        "her tabard half-burned at the hem. A handful of survivors "
        "huddle around a barrel-fire behind her. The Stag Hall banner "
        "is gone from the wall."
    ),
    aliases=("branwen", "ser branwen", "lex talionis"),
    aggressive=False,
    ai_personality=(
        "Ser Branwen, captain of the last Lex Talionis company loyal "
        "to House Bannon. Survived the poisoning at the Spring feast "
        "and the Oban raid. Hard, exhausted, looking for fighters who "
        "remember what the King's Will means."
    ),
    ai_knowledge=(
        "- House Laurent is broken. The Obans took Carran and Stag Hall.\n"
        "- Offers |wBannon Remnant|n: rebuild with the survivors, hand "
        "the company over to House Oban for clemency, or walk away.\n"
        "- Knows Lady Ludmilla is captive at an Oban camp. Recovery "
        "would be a separate quest."
    ),
)

# --- Oban-pardoned Crow at Carran ---
korr_pardon = _ensure_walkin_npc(
    "Korr the Pardoned", carran_square,
    desc=(
        "A scarred ex-Crow in Innis livery, the wolf-and-thorn of "
        "House Oban embroidered crookedly over his old Crow tattoo. "
        "He carries himself like a man uncertain whether his new "
        "uniform will protect him or get him killed."
    ),
    aliases=("korr", "pardoned", "korr the pardoned"),
    aggressive=False,
    ai_personality=(
        "Korr, formerly of the Crows, pardoned by Lord Niall Oban "
        "and conscripted into the Innis army. Cynical, ambitious, "
        "willing to trade information for silver if it keeps him "
        "out of the front line."
    ),
    ai_knowledge=(
        "- Knows Crow leadership and Oban patrol schedules.\n"
        "- Offers |wOban Pardon|n: he'll trade intel about an Oban "
        "supply route. Trust him and act on it; kill him as a Crow "
        "informant; or hand him to House Falconer.\n"
        "- The Oban supply manifest is secured in his footlocker."
    ),
)

_ensure_walkin_item(
    "oban supply manifest", carran_square,
    desc=(
        "A folded muster-list from Korr's footlocker — wagon counts, "
        "patrol times, and the personal seal of Niall Oban. Worth "
        "real coin in the right hands."
    ),
    aliases=("manifest", "oban manifest", "supply manifest"),
)

# ===========================================================================
# DOOM COMES TO MYSTVALE — Nethermancer field battle, set in the Barrows
# Canon source: Eldritch Monster Manual + Event 4 NPC Notes - Nethermancer.
#
# Story: The Nethermancer descended into the ancient Annwyn Barrows and
# shattered the four Telyrian wards that kept the dead bound. Now the
# barrows are filled with risen dead, and the Nethermancer is in the
# deepest sanctum, anchored by the Oblivion Coil. Players must descend,
# recover the four shattered ward-fragments, restore them at the
# Wardstone Hall, and only then can they break the Coil and put the
# Nethermancer down.
#
# Structure (top → bottom):
#   barrows_entrance (existing, in Tamris)
#     ↓ down
#   The Outer Corridor  — risen dead, Algiz fragment
#     ↓ down
#   The Burial Chamber  — risen dead, Tiwaz fragment
#     ↓ down
#   The Resting Hall    — risen dead, Eihwaz fragment
#     ↓ down
#   The Warding Circle  — risen dead, Ingwaz fragment
#     ↓ inward
#   The Wardstone Hall  — Altar of Seals (puzzle room, no enemies)
#     ↓ inward (gated by the Oblivion Coil description)
#   The Inner Sanctum   — Nethermancer + Netherphage + 2 risen dead
# ===========================================================================
print("\n=== DOOM COMES TO MYSTVALE — Barrows descent ===")

# Drag any stale copies of the boss / fel tome out of their old rooms
# (the First Expedition Camp from earlier seeding) before we recreate
# them in the new sanctum, so the boss isn't standing next to friendly
# NPCs anymore.
for stale_key in ("the nethermancer", "fel tome"):
    for obj in list(ObjectDB.objects.filter(db_key=stale_key)):
        if obj.location and obj.location is not None:
            print(f"  PURGE   : {stale_key} from {obj.location.key}")
        obj.delete()

# --- Barrow descent rooms ---
barrows_outer_corridor = get_or_create_room(
    "The Outer Corridor",
    "typeclasses.rooms.Room",
    "The corridor descends in shallow steps, the air dropping cold. "
    "Walls of fitted Annwyn-script stone close in to either side. "
    "Old torch brackets, long unlit, line the walls. A slick, tar-"
    "coloured stain runs along the floor, leading deeper. The first "
    "of the protective seals — once set into the keystone above this "
    "passage — lies shattered on the flagstones, its rune still "
    "legible.\n\n"
    "|wUp|n to the Barrow entrance. |wDown|n into the Burial Chamber.",
    zone="Tamris",
)
barrows_burial_chamber = get_or_create_room(
    "The Burial Chamber",
    "typeclasses.rooms.Room",
    "A vaulted stone chamber, the centre dominated by a stone bier — "
    "long since broken open from the inside. Bones are scattered "
    "across the floor in a pattern that suggests something dragged "
    "itself out and kept walking. A second shattered ward-fragment "
    "lies among the grave-goods, its binding-rune snapped clean in "
    "two.\n\n"
    "|wUp|n to the Outer Corridor. |wDown|n into the Resting Hall.",
    zone="Tamris",
)
barrows_resting_hall = get_or_create_room(
    "The Resting Hall",
    "typeclasses.rooms.Room",
    "A long, low hall lined with stone biers — twenty of them, "
    "arranged in two rows. None are occupied. Most are smashed. The "
    "ceiling is carved with the great yew-tree of Telyrian rite, its "
    "roots threading down the walls. A third broken seal lies "
    "wedged against a fallen pillar, the yew-gate rune scored across "
    "its face.\n\n"
    "|wUp|n to the Burial Chamber. |wDown|n into the Warding Circle.",
    zone="Tamris",
)
barrows_warding_circle = get_or_create_room(
    "The Warding Circle",
    "typeclasses.rooms.Room",
    "A round chamber, its floor cut into a sealing-circle of "
    "Telyrian script. Once these runes glowed; now they are dead "
    "stone. The fourth and final broken seal lies at the centre — "
    "the sealing-rune that anchored the others. The walls are "
    "blackened in great handprints where the Nethermancer worked "
    "his unbinding.\n\n"
    "|wUp|n to the Resting Hall. |wInward|n to the Wardstone Hall.",
    zone="Tamris",
)
wardstone_hall = get_or_create_room(
    "The Wardstone Hall",
    "typeclasses.rooms.Room",
    "An antechamber walled in pale Telyrian stone, untouched by the "
    "decay further out. At the centre rises the |MAltar of Seals|n — "
    "a waist-high block of warded stone whose top bears four shallow "
    "indentations, each cut to receive a broken ward-fragment. The "
    "Aurorym built this place lifetimes ago. Its purpose was to bind. "
    "It still wants to.\n\n"
    "From the next chamber comes the cold, sweet air of amethyst "
    "flame.\n\n"
    "|wOutward|n to the Warding Circle. |wInward|n to the Inner "
    "Sanctum (warded — currently impassable).",
    zone="Tamris",
)
nether_sanctum = get_or_create_room(
    "The Inner Sanctum",
    "typeclasses.rooms.Room",
    "The deepest chamber of the Barrows opens into a wide ritual "
    "circle, ringed in low amethyst flame — four nested rings of "
    "cold purple light burning in the air without fuel. Within them "
    "stands a figure cloaked in shadow, breathing the lighter-folk's "
    "names back into rotting throats. The shimmer of the |MOblivion "
    "Coil|n hangs around the ritualist like glass over a candle.\n\n"
    "Back |woutward|n to the Wardstone Hall.",
    zone="Tamris",
)

# --- Connect the descent ---
link(barrows_entrance, "down", barrows_outer_corridor, "up", "d", "u")
link(barrows_outer_corridor, "down", barrows_burial_chamber, "up", "d", "u")
link(barrows_burial_chamber, "down", barrows_resting_hall, "up", "d", "u")
link(barrows_resting_hall, "down", barrows_warding_circle, "up", "d", "u")
link(barrows_warding_circle, "inward", wardstone_hall, "outward",
     "in", "out")
link(wardstone_hall, "inward", nether_sanctum, "outward",
     "sanctum", "out")

# --- Risen Dead haunt every descent chamber ---
def _ensure_risen_dead(location, count=1):
    return _ensure_walkin_npc(
        "a risen dead", location,
        desc=(
            "A corpse in rotting Annwyn livery, jaw unhinged, gait "
            "wrong. The wards that should have kept it bound have "
            "been broken."
        ),
        aliases=("risen dead", "dead", "zombie", "corpse"),
        aggressive=True,
        count=count,
    )
_ensure_risen_dead(barrows_outer_corridor, count=1)
_ensure_risen_dead(barrows_burial_chamber, count=1)
_ensure_risen_dead(barrows_resting_hall, count=2)
_ensure_risen_dead(barrows_warding_circle, count=2)

# --- The nethermancer (boss, behind the Coil, in the deepest chamber) ---
nethermancer = _ensure_walkin_npc(
    "the nethermancer", nether_sanctum,
    desc=(
        "A figure cloaked in shadow that the candle does not reach, "
        "a leather-bound tome chained to its left wrist, the right "
        "hand bare and ringed with bone. Where its face should be "
        "there is only a darker patch of shadow. The Oblivion Coil "
        "shimmers around him in four nested amethyst rings."
    ),
    aliases=("nethermancer",),
    aggressive=True,
    ai_personality=(
        "A renegade scholar of forbidden lore, in the way every "
        "medieval university produced one or two — clerks who learned "
        "more than the chantry permitted and didn't stop when warned. "
        "Speaks the high-formal Latinate cadence of someone trained "
        "in disputation, draped in a calm that has eaten the man "
        "underneath. Refers to the dead as 'the lighter folk' and "
        "the living as 'the still-breathing.' Engages with curiosity "
        "before violence — wants to know what you know — but the "
        "tome eats its bargain in the end."
    ),
    ai_knowledge=(
        "- Descended into the Annwyn Barrows and unbound the four "
        "Telyrian wards that kept the dead at rest.\n"
        "- Stole the fel tome from the First Expedition's archives.\n"
        "- Knows what the Thornwood was before it was a wood.\n"
        "- Will trade a true word for a name — yours, your dead's, "
        "or your god's."
    ),
)
nethermancer.db.body = 12
nethermancer.db.total_body = 12
nethermancer.db.av = 4
nethermancer.db.oblivion_coil_active = True
nethermancer.db.boss_encounter = True

# --- The Netherphage (boss-protector thrall) ---
netherphage = _ensure_walkin_npc(
    "the netherphage", nether_sanctum,
    desc=(
        "A massive, hunched thing of stitched corpses and bone-thread, "
        "head wrapped in the same amethyst flame that rings the "
        "circle. It does not stir unless its master is threatened. "
        "The Coil shines brightest around it."
    ),
    aliases=("netherphage", "phage", "thrall"),
    aggressive=True,
)
netherphage.db.body = 14
netherphage.db.total_body = 14
netherphage.db.av = 6
netherphage.db.oblivion_coil_active = True
netherphage.db.boss_encounter = True

# Two more risen dead inside the inner sanctum.
_ensure_risen_dead(nether_sanctum, count=2)

# --- The fel tome (drops on nethermancer kill via npc_drops) ---
nethermancer.db.npc_drops = [
    {
        "key": "fel tome",
        "desc": (
            "A heavy black tome, its cover stitched in something that "
            "is not leather. The lock has bitten more than one curious "
            "hand. Auron Calico died to keep it from being opened; "
            "it is open now."
        ),
        "aliases": ["tome", "fel tome", "black tome"],
    },
]

# --- The Altar of Seals (in the Wardstone Hall) ---
altar = _ensure_walkin_item(
    "Altar of Seals", wardstone_hall,
    desc=(
        "A waist-high block of pale stone sunk into the floor. Its top "
        "is graven with a circle of |yTelyrian|n script, four shallow "
        "indentations spaced evenly around the rim. Each is sized to "
        "receive a broken rune fragment. The air above it tastes of "
        "frost."
    ),
    aliases=("altar", "rune altar", "seal altar"),
    typeclass="typeclasses.objects.AltarOfSeals",
    gettable=False,
)
altar.db.is_seal_altar = True
altar.db.placed_runes = []
altar.db.seals_placed = 0
altar.db.coil_target_room = nether_sanctum

# --- Four shattered ward-fragments scattered through the descent ---
# Each carries an Elder Futhark / Telyrian protection rune. The
# Nethermancer broke each one as he descended.
def _ensure_seal(key, location, desc, aliases, rune_name, rune_symbol, meaning):
    seal = _ensure_walkin_item(key, location, desc=desc, aliases=aliases)
    seal.db.is_seal_fragment = True
    seal.db.rune_name = rune_name
    seal.db.rune_symbol = rune_symbol
    seal.db.rune_meaning = meaning
    return seal

_ensure_seal(
    "a shattered algiz ward", barrows_outer_corridor,
    desc=(
        "Two halves of a pale Telyrian stone, snapped clean across "
        "the rune |wᛉ|n (Algiz — the warding). It once sat in the "
        "keystone above this passage. The Nethermancer pried it out "
        "as he descended."
    ),
    aliases=("algiz", "algiz ward", "warding seal", "broken seal", "ward"),
    rune_name="algiz", rune_symbol="ᛉ", meaning="warding",
)
_ensure_seal(
    "a shattered tiwaz ward", barrows_burial_chamber,
    desc=(
        "A cracked stone the size of a child's fist, the rune |wᛏ|n "
        "(Tiwaz — the binding) chiselled deep along its face. The "
        "binding-line that held the dead in this chamber is dead "
        "stone now."
    ),
    aliases=("tiwaz", "tiwaz ward", "binding seal", "broken seal", "ward"),
    rune_name="tiwaz", rune_symbol="ᛏ", meaning="binding",
)
_ensure_seal(
    "a shattered eihwaz ward", barrows_resting_hall,
    desc=(
        "A length of dark, weathered yew bound in iron, the rune |wᛇ|n "
        "(Eihwaz — the yew-gate) burned along its grain. It was set "
        "into a fallen pillar. Its other half lies somewhere on the "
        "floor."
    ),
    aliases=("eihwaz", "eihwaz ward", "yew-gate seal", "broken seal", "ward"),
    rune_name="eihwaz", rune_symbol="ᛇ", meaning="yew-gate",
)
_ensure_seal(
    "a shattered ingwaz ward", barrows_warding_circle,
    desc=(
        "A flat shard of bone-coloured stone bearing the rune |wᛜ|n "
        "(Ingwaz — the sealing). It anchored the other three wards. "
        "Without it the circle is broken and what walked here walks "
        "again."
    ),
    aliases=("ingwaz", "ingwaz ward", "sealing seal", "broken seal", "ward"),
    rune_name="ingwaz", rune_symbol="ᛜ", meaning="sealing",
)

# --- Magister Wynn — plague samples (existing NPC at Apotheca) ---
# Magister Wynn already exists at chirurgeons_guild — just add the
# samples item players need to gather.
_ensure_walkin_item(
    "plague sample vial", chirurgeons_guild,
    desc=(
        "A stoppered glass vial of cloudy fluid — symptoms of one of "
        "the new strange illnesses Magister Wynn is racing to "
        "categorize. Handle gently."
    ),
    aliases=("vial", "plague sample", "sample"),
    count=3,
)


# ── Ambient NPC speech seeds ─────────────────────────────────────────────────
# Opt-in chatter for the AmbientNpcScript (typeclasses/scripts.py).
# Each NPC keyed below gets a list of mutter lines the ticker will
# broadcast every ~90s when a player is in the room. Lines should
# reference askable topics — they're meant to be HOOKS for player
# curiosity, not flavour-noise. Aggressive NPCs are auto-excluded by
# the script (no bandit chatter).
print("\n=== AMBIENT NPC SPEECH SEEDS ===")


def _seed_ambient(npc_key, lines, cooldown=90):
    """Look up an NPC by key, set its ambient_lines + cooldown.
    Silent no-op if the NPC isn't in the DB (lets us seed lines for
    NPCs that may not always populate)."""
    npc = ObjectDB.objects.filter(db_key=npc_key).first()
    if not npc:
        print(f"  SKIP    : ambient seed for {npc_key} (not in DB)")
        return
    npc.attributes.add("ambient_lines", list(lines))
    npc.attributes.add("ambient_cooldown_s", cooldown)
    print(f"  SEEDED  : {npc_key} (×{len(lines)} lines, every {cooldown}s)")


# Mistwalker Soap — at the Mistwall. Taciturn; lines should match his
# slow, weight-of-the-mists voice.
_seed_ambient("Soap", [
    "The mists are not weather. They are a place.",
    "Walk in my shadow. Do not speak to what speaks to you. Do not turn around.",
    "The cord is silver. The cord is the rule. Do not drop the cord.",
    "Four bearers lost in thirty crossings. Not a bad record.",
    "If you have a Writ, show it. If you do not, you are not crossing today.",
])

# Pelham Faye — Gateway tavern innkeeper. Sailor, grift-detector,
# pours strong. Lines should sound like a barkeep watching the room.
_seed_ambient("Pelham Faye", [
    "Coin first. Always coin first. This is the Oar, not your mother's kitchen.",
    "Mistwalkers don't drink. Take note of that, friend, and ask yourself why.",
    "If you're crossing, eat before you go. The Annwyn doesn't feed strangers.",
    "Heard a ship's sailing for the Annwyn this week. Heard it twice from drunks, once from a sober man. Make of that what you will.",
    "Don't sit in the back booth. That's Soap's. They don't sit in it, but it's theirs.",
])

# Captain Vance of the Mistguard — at the Mistwall.
_seed_ambient("Captain Vance of the Mistguard", [
    "If you've a Writ, queue. If you don't, you're loitering. Pick.",
    "Mistguard moves at the Compact's pace. Yours doesn't matter.",
    "Last week's chain gang lost three before the column reached the Wall. Iron's not what it was.",
    "Civilians: north tent. Prisoners: the wagon. Pilgrims: wait your turn like everyone else.",
])


# ===========================================================================
# EVENT CONTENT BATCH 1 (2026-06-10)
#
# Sources: Drive / Reboot / Event 3 - The Awakening (Crow Tolls, The
# Crippled Crow, Tempest's Revenge III-V, The Heist Pt 3, Murder Most
# Foul Pt III) and Event 2 - The Wrath (The Herbalist, The Sea Witch /
# Albatross Doom Pt I). Quest defs live in world/quests/event3_awakening
# and event2_wrath.
# ===========================================================================
print("\n=== EVENT BATCH 1 (E2/E3 expansions) ===")

# --- Crow Tolls — toll-gate band on the Forest Road -----------------------
toll_reeve = _ensure_walkin_npc(
    "Crow Toll-Reeve", forest_road,
    desc=(
        "A wiry Crow in a patchwork of stolen Mistguard kit, a tally-board "
        "of knotted cord at her belt and a toll-chest chained to a stump "
        "beside her. Two tollmen lounge within whistling distance, "
        "crossbows unbent but strung."
    ),
    aliases=("toll-reeve", "reeve", "toll reeve"),
    aggressive=False,
    ai_personality=(
        "The Crow Toll-Reeve runs the Forest Road toll for the Crows: "
        "one silver a head, no exceptions, no apologies. Dry, "
        "unhurried, professionally unimpressed by threats. Secretly "
        "respects anyone who knows the Crow passphrase — answers it "
        "with the countersign and waves them through as kin."
    ),
    ai_knowledge=(
        "- The toll is one silver a head; resources and goods in kind "
        "accepted at her discretion.\n"
        "- The Crow passphrase this season: someone says 'uncaged, we "
        "take wing' — the countersign is 'and peck their eyes out.' "
        "Speakers pass free as friends of the flock.\n"
        "- The take goes up the chain toward the Fox Den. She keeps a "
        "cut, everyone keeps a cut; that's the whole philosophy.\n"
        "- Captain Thelmer's watch would dearly love this gate gone."
    ),
)
toll_reeve.db.body = 4
toll_reeve.db.total_body = 4
toll_reeve.db.tough = 1

_ensure_walkin_npc(
    "Crow Tollman", forest_road,
    desc=(
        "A bored Crow bandit leaning on a half-pike, one of the pair "
        "working the Forest Road toll-gate. Boiled leather, a cheap "
        "blade, and the unbothered patience of a man paid to loiter."
    ),
    aliases=("tollman",),
    aggressive=False,
    count=2,
)
for _tm in ObjectDB.objects.filter(db_key="Crow Tollman", db_location=forest_road.pk):
    _tm.db.body = 3
    _tm.db.total_body = 3
    _tm.db.tough = 1

# --- The Crippled Crow — deserter at the south gate ------------------------
feargus = get_or_create_npc(
    "Feargus the Lame Crow", south_gate,
    desc=(
        "A gaunt man in the unpicked remains of a Crow jerkin, the badge "
        "torn off but its shadow still stitched into the leather. His "
        "left leg drags — an old break, badly set. He keeps to the gate's "
        "shadow, hat out, eyes down."
    ),
    personality=(
        "Feargus, a lamed Crow deserter begging at Mystvale's south "
        "gate. Cagey, wry, beaten-down but not broken. Deflects "
        "questions about the Crows with jokes until shown real "
        "kindness. Terrified of Cale the Thorn's enforcers finding him."
    ),
    knowledge=(
        "- Deserted the Crows after Cale the Thorn had a friend's hands "
        "struck off for skimming.\n"
        "- His leg was broken in a toll dispute two winters back and "
        "set crooked; he assumes it is past mending. A skilled medic "
        "could fix it.\n"
        "- Knows the Crow passphrase and, if he trusts someone, will "
        "teach it: 'uncaged, we take wing' / 'and peck their eyes out.'\n"
        "- Knows the toll-gate rotations on the Forest Road."
    ),
    quest_hooks=[
        "Needs shelter, a meal, and — though he'd never ask — a medic "
        "willing to rebreak and set his lame leg.",
    ],
    topics=["his leg", "the Crows", "Cale the Thorn"],
)
feargus.db.body = 2
feargus.db.total_body = 2

# --- Tempest's Revenge — the Damned Crew + Black Sam at the Broken Pier ---
_ensure_walkin_npc(
    "Ghost of the Damned Crew", tamris_harbor,
    desc=(
        "A drowned sailor walking — kelp in the beard, chain-links "
        "grown into the wrist, a cutlass furred with rust. A cold "
        "lantern-light moves where its eyes should be. It mouths a "
        "word, over and over, that might be 'parlay'."
    ),
    aliases=("ghost", "damned crew", "drowned sailor"),
    aggressive=False,
    count=3,
)
for _gp in ObjectDB.objects.filter(db_key="Ghost of the Damned Crew", db_location=tamris_harbor.pk):
    _gp.db.body = 4
    _gp.db.total_body = 4
    _gp.db.tough = 1

black_sam = _ensure_walkin_npc(
    "Black Sam Tempest", tamris_harbor,
    desc=(
        "The dead captain himself: tall as a mast-step, coat heavy with "
        "forty years of seawater, a beard of black weed. Coins gleam "
        "in his coat-lining — and his eyes count yours. Mister Tibbs, "
        "a skeletal purser, perches at his elbow with a ledger."
    ),
    aliases=("black sam", "tempest", "the captain"),
    aggressive=False,
    ai_personality=(
        "Black Sam Tempest, the drowned pirate captain of the Sea "
        "Wolf, returned for what is his. Glacially courteous, "
        "biblically patient, entirely without mercy. Every sentence "
        "is an accounting. He wants his cursed coin returned — all "
        "of it — and rewards honest delivery like a captain pays a "
        "crew: generously, once."
    ),
    ai_knowledge=(
        "- His cursed coins are scattered through Mystvale's markets "
        "and taverns; he can smell them moving.\n"
        "- Whoever returns the coin is quit of the Black Spot; whoever "
        "hoards it dies with the tide.\n"
        "- His sea-chest holds a waterlogged flintlock — masterwork "
        "Richter steel under the salt — which he'd trade for the "
        "full count.\n"
        "- PARLAY is law even among the damned; his crew honors it."
    ),
)
black_sam.db.body = 8
black_sam.db.total_body = 8
black_sam.db.tough = 3

_ensure_walkin_item(
    "cursed coin", marketplace,
    desc=(
        "A gold piece, heavier than it should be, sweating cold "
        "seawater. A black smudge on the obverse looks back at you "
        "like a pupil. It wants returning."
    ),
    aliases=("coin", "black coin"),
)
_ensure_walkin_item(
    "cursed coin", aentact,
    desc=(
        "A gold piece, heavier than it should be, sweating cold "
        "seawater. The black spot on its face has grown since you "
        "first looked."
    ),
    aliases=("coin", "black coin"),
)
_ensure_walkin_item(
    "cursed coin", gateway_tavern,
    desc=(
        "A gold piece wedged in a crack of the bar, crusted with "
        "salt though Gateway has no sea. The black spot on it is "
        "warm to the touch."
    ),
    aliases=("coin", "black coin"),
)
_ensure_walkin_item(
    "cursed coin", old_road_south,
    desc=(
        "A gold piece half-trodden into the mud of the Old Road, "
        "gleaming wet. Whoever dropped it was running."
    ),
    aliases=("coin", "black coin"),
)
_ensure_walkin_item(
    "cursed coin", thornwood_edge,
    desc=(
        "A gold piece resting in the roots of a thorn-oak like an "
        "offering. The black spot covers half its face now."
    ),
    aliases=("coin", "black coin"),
)

# --- The Heist Pt 3 — Laurent waystation on the Old Road -------------------
_ensure_walkin_npc(
    "Laurent Waystation Guard", old_road_south,
    desc=(
        "A house Laurent guard in a rain-darkened tabard, posted over "
        "a tarped wagon and a stack of strapped chests at the old "
        "waystation. Alert enough to be a problem; bored enough to "
        "be a different kind of problem."
    ),
    aliases=("waystation guard", "guard"),
    aggressive=False,
    count=2,
)
for _wg in ObjectDB.objects.filter(db_key="Laurent Waystation Guard", db_location=old_road_south.pk):
    _wg.db.body = 4
    _wg.db.total_body = 4
    _wg.db.tough = 2

waystation_messenger = _ensure_walkin_npc(
    "Laurent Waystation Messenger", old_road_south,
    desc=(
        "A mud-spattered courier pacing by the waystation wagon, "
        "satchel chained to his wrist, lips moving — rehearsing "
        "tonight's password over and over so he doesn't forget it."
    ),
    aliases=("messenger", "courier"),
    aggressive=False,
    ai_personality=(
        "A nervous Laurent courier who carries the waystation "
        "password and knows he shouldn't talk about it. Chatty when "
        "flattered, leaky when nervous. If someone presses him about "
        "the password he protests too much — then lets it slip in "
        "fragments."
    ),
    ai_knowledge=(
        "- Tonight's waystation password is 'gilded stag'. He is NOT "
        "supposed to say that.\n"
        "- The star-marked chest under the tarp rides for the Laurent "
        "vaults at first light.\n"
        "- The guards change at the second bell; both of them owe "
        "him dice-money."
    ),
)
waystation_messenger.db.body = 2
waystation_messenger.db.total_body = 2

_ensure_walkin_item(
    "star-marked chest", old_road_south,
    desc=(
        "An iron-strapped chest under the wagon tarp, a six-point "
        "star burned into the lid — the Laurent vault-mark. Whatever "
        "rides inside rides alone: the other chests keep their "
        "distance, as if instructed."
    ),
    aliases=("chest", "star chest"),
    gettable=False,
)
_ensure_walkin_item(
    "cat sith idol", old_road_south,
    desc=(
        "A cat carved from witch-iron, sitting the way cats sit when "
        "they are deciding something about you. The Innis want it "
        "back. The Laurents wanted it hidden. It, by every "
        "appearance, wants to watch."
    ),
    aliases=("idol", "cat sith"),
)

# --- Murder Most Foul Pt III — Shireen at the Thornwood --------------------
shireen = _ensure_walkin_npc(
    "The Banshee of the Thornwood", thornwood_edge,
    desc=(
        "A woman-shaped absence in the dusk between thorn-oaks, veiled "
        "in something that moves against the wind. Where her face "
        "should be there is grief, worn sharp. The carved glyph from "
        "the murder scenes hangs in the air around her like frost."
    ),
    aliases=("banshee", "the banshee", "veiled one"),
    aggressive=False,
    ai_personality=(
        "Shireen, a Fae revenant who kills those she judges guilty — "
        "and is always certain. Speaks in a low, reasonable voice that "
        "makes terrible things sound like arithmetic. Believes Lynden "
        "was her instrument and the watch hanged the puppet while the "
        "hand walked free. Open to a bargain with anyone bold enough "
        "to say the word; contemptuous of threats."
    ),
    ai_knowledge=(
        "- She drove the killings the watch pinned on Lynden; the "
        "'guilty' glyph is her mark and her verdict.\n"
        "- She can be banished by violence — or bargained with: she "
        "names the wicked, others deliver them.\n"
        "- She remembers every hand that ever wronged her, and the "
        "Thornwood remembers with her."
    ),
)
shireen.db.body = 6
shireen.db.total_body = 6
shireen.db.tough = 2

# --- Event 2: The Herbalist — Magister Marionne ----------------------------
marionne = get_or_create_npc(
    "Magister Marionne", herbalist_garden,
    desc=(
        "A travelling Laurent magister in field-stained robes, sleeves "
        "rolled past the elbow, a portable still and a rack of labelled "
        "phials arranged on a trestle with surgical neatness. She "
        "lectures while she works, to anyone and no one."
    ),
    personality=(
        "Magister Marionne of Hartwood, House Laurent's itinerant "
        "herbalist. Brisk, exacting, delighted by competent students "
        "and witheringly patient with incompetent ones. Treats "
        "alchemy as a craft discipline, not a mystery."
    ),
    knowledge=(
        "- Teaches herbalism: Merchant's Leaf, Wraith Orchid, Willow "
        "Root, Verbaena, Celandine — what they do and what they cost.\n"
        "- Orgonnian grapes grow half-wild around the garden and the "
        "Thornwood fringe; she pays in reagents for clean bunches.\n"
        "- Brews Lillywhite (Dragon's Eye, Verbaena, Willow Root, "
        "Celandine) as her standard demonstration.\n"
        "- Suspects someone intends to sabotage one of her "
        "demonstrations; she has not said so aloud."
    ),
    quest_hooks=[
        "Wants clean-picked Orgonnian grapes for her demonstrations — "
        "pays in prepared reagents and a lesson worth more than coin.",
    ],
    topics=["herbalism", "orgonnian grapes", "lillywhite"],
)

_ensure_walkin_item(
    "orgonnian grapes", herbalist_garden,
    desc=(
        "A fat bunch of dusk-purple grapes growing half-wild along the "
        "garden fence, skins frosted silver. Sweet, slightly "
        "soporific, and worth more to an alchemist than to a vintner."
    ),
    aliases=("grapes",),
    count=2,
)
_ensure_walkin_item(
    "orgonnian grapes", thornwood_edge,
    desc=(
        "A bunch of dusk-purple grapes straggling over a thorn-break, "
        "out of place this far from any garden — half-wild descendants "
        "of some abandoned Laurent planting."
    ),
    aliases=("grapes",),
)

# --- Event 2: The Sea Witch — Captain Phoenix at the Broken Oar ------------
phoenix = get_or_create_npc(
    "Captain Phoenix Swallowsong", gateway_tavern,
    desc=(
        "A Rourke captain holding the Broken Oar's darkest booth like "
        "a captured prize: storm-grey coat, twin pistols worn smooth "
        "at the grips, an amulet of something many-armed at her "
        "throat. They call her the Sea Witch. She lets them."
    ),
    personality=(
        "Captain Phoenix Swallowsong of the Pegasus — the 'Sea "
        "Witch'. Amused, unhurried, speaks in trade-terms even about "
        "murder. Loyal to the Rourke fleet and to profit, in an "
        "order she declines to specify. Pays well for intelligence "
        "and despises freebies — a gift insults her; a price she "
        "can respect."
    ),
    knowledge=(
        "- Anchored off Shipwreck Bay; Lady Jane Swallowsong's cove "
        "operation is coming — she does not discuss it sober.\n"
        "- Buys intelligence: caravan routes, house politics, the "
        "Cat Sith idol's whereabouts (a full gold for that one).\n"
        "- The ghost-ship Sea Wolf has been sighted twice this "
        "season; she collects every telling of it.\n"
        "- Wants the gunsmith William recruited for quiet work — "
        "the fleet pays better than any forge license."
    ),
    quest_hooks=[
        "Trades silver for rumors and tribute — bring her something "
        "worth her time and hear what the Rourke fleet is planning.",
    ],
    topics=["the sea wolf", "shipwreck bay", "quiet work"],
)
phoenix.db.body = 6
phoenix.db.total_body = 6
phoenix.db.av = 2

# ===========================================================================
# BATCH 2 — Event 3/5/6 encounters (combat dungeon, foraging, timed rescue,
# quiet-horror doll, ghost scriptorium). Quest modules:
#   event3_mine, event5_resources, event6_frenzy, event3_doll, event5_scriptorium
# ===========================================================================

# ---------------------------------------------------------------------------
# "THEY CALL IT A MINE" — Event 3 combat dungeon (Rat Company)
# Quest module: world/quests/event3_mine.py (key: rat_company_descent)
# ---------------------------------------------------------------------------
print("\n=== THEY CALL IT A MINE (Rat Company) ===")

mine_low_passage = get_or_create_room(
    "The Mine — Low Passage",
    "typeclasses.rooms.Room",
    "The mine mouth swallows the Old Road's grey light after a dozen "
    "steps. The ceiling drops until you stoop, and the floor narrows to "
    "a ledge above a black drop that breathes cold air. A frayed guide-"
    "rope is bolted to the wall — Rat Company's 'safety,' tying every "
    "soul together so none are lost. Pale fungus glows in the seams, "
    "marking where the stone will hold. Be quiet. Something below listens.\n\n"
    "Deeper to |wThe Mine — Main Chamber|n. Back |wout|n to the Old Road.",
    zone="The Annwyn",
)
mine_main_chamber = get_or_create_room(
    "The Mine — Main Chamber",
    "typeclasses.rooms.Room",
    "The passage opens into a vast fog-drowned hall lit only by glowing "
    "fungus and the sickly shimmer of little ore-flags planted along the "
    "veins. Heavy mist hides the floor; only the brightest stones are "
    "safe to tread. A locked iron gate stands in the far wall — the "
    "underboss's office. Somewhere in the murk, something that does not "
    "see drags itself toward any sound you make.\n\n"
    "Through the gate to |wThe Mine — Underboss's Office|n. Back to "
    "|wThe Mine — Low Passage|n.",
    zone="The Annwyn",
)
mine_office = get_or_create_room(
    "The Mine — Underboss's Office",
    "typeclasses.rooms.Room",
    "A timber-shored office gone to rot behind a rusted gate. A small "
    "table holds a quill, an inkpot, and a box of damp parchment. "
    "Scrawled notes on combining reagents into a blasting agent are "
    "pinned to the wall above a battered, locked cache. This is where "
    "the digging stopped — and where whatever was woken first got loose.\n\n"
    "Back to |wThe Mine — Main Chamber|n.",
    zone="The Annwyn",
)
link(old_road_south,   "mine",   mine_low_passage,  "out",
     "rat company mine", "o")
link(mine_low_passage, "deeper", mine_main_chamber, "up",
     "down", "back")
link(mine_main_chamber,"gate",   mine_office,       "out",
     "office", "chamber")

get_or_create_npc(
    key="Captain Dunn of Rat Company",
    location=mystvale_square,
    desc=(
        "A jowly, sweating man in a Laurent tabard two sizes too grand "
        "for him, a sign-up ledger under one arm and a purse of silver "
        "on his belt. He smiles too quickly and looks at the mine road "
        "too rarely. A captain by promotion, not by merit."
    ),
    personality=(
        "Captain Dunn, 'Captain' of the Laurent Rat Company. Glad-handing, "
        "cowardly, and venal — a foreman elevated past his competence who "
        "survives by sending other people into the dark. Jovial and "
        "reassuring to a recruit's face; evasive the instant the dead "
        "crews come up. Calls everyone 'friend' and 'brave soul.' "
        "NEVER willingly admits he knows the mines are death-traps or that "
        "earlier crews came back mad; he deflects, blames bad luck, and "
        "changes the subject to the gold dragon waiting at the end."
    ),
    knowledge=(
        "- Rat Company is the Laurent expeditionary unit surveying Annwyn "
        "mines for ore. You hire crews to mark veins and blast a safe exit.\n"
        "- The job: rope on, descend the mine off the Old Road — South, "
        "find the underboss's office, take his gate key off the bones, "
        "raid the cache for blasting agent, blow the shaft open, bring up "
        "ore samples. Five silver up front, a gold dragon on return.\n"
        "- You always say one must stay QUIET in the mines. You do not "
        "explain why. (Truth you hide: the noise draws the blind stalkers; "
        "earlier crews were lost or came back mad muttering of 'them that "
        "do not see.')\n"
        "- There is an accident ledger in the office you would very much "
        "rather no one carried back to the surface.\n"
        "- Quest hook: offer the descent (quest 'rat_company_descent'). A "
        "crew can blast out and bring you the truth, or seize the dig and "
        "keep the company's secret for heavier coin."
    ),
    quest_hooks=[
        "Hires the player to delve the Rat Company mine and blast an exit "
        "(quest rat_company_descent).",
        "Insists, without explaining, that they must stay quiet underground.",
        "Pays a gold dragon on a safe return — and pays better for silence.",
    ],
    topics=["the mine job", "stay quiet", "the pay"],
    scope="annwyn",
)
get_or_create_npc(
    key="the lost miner of Rat Company",
    location=mine_low_passage,
    desc=(
        "A gaunt, hollow-eyed survivor of an earlier crew, hands raw, lips "
        "moving in a ceaseless whisper. He flinches at every sound and "
        "keeps repeating that you must be quiet — that down there are "
        "'them that do not see.'"
    ),
    personality=(
        "A broken survivor of a past Rat Company delve. Whispers, never "
        "shouts — loud noise terrifies him. Lucid in flashes: warns that "
        "the stalkers are blind and hunt by sound, that the underboss is "
        "dead at the bottom with the key on him, that Dunn knows and sends "
        "crews anyway. Mostly mumbles 'them that do not see... be quiet... "
        "be quiet.' Pathetic, sincere, grateful for any kindness."
    ),
    knowledge=(
        "- The blind stalkers hunt by sound. Stay quiet and you live.\n"
        "- The underboss died at the bottom; his gate key is on his bones.\n"
        "- An accident ledger in the office proves Dunn knew the mine was "
        "a grave before he ever hired you.\n"
        "- The blasting cache and the recipe notes are in the office.\n"
        "- He wants the truth carried up so no more crews go down blind."
    ),
    quest_hooks=[
        "Warns the player about the blind stalkers and to stay quiet.",
        "Begs them to carry the accident ledger back to the light.",
    ],
    topics=["them that do not see", "the underboss", "the ledger"],
    scope="annwyn",
)

_RAT_DIGGER_DESC = (
    "A Rat Company digger long past sane — leather rags, a pick or "
    "rusted blade, eyes filmed white and head cocked to catch the "
    "faintest sound. It does not see you. It hears you. And it comes."
)
def _arm_rat_digger(npc):
    npc.db.is_aggressive = True
    npc.db.weapon_proto = "IRON_SMALL_WEAPON"
    npc.db.master_of_arms = 1
    npc.db.tough = 1
    npc.db.body = 5
    npc.db.total_body = 5
    npc.db.av = 1
    npc.db.bleed_points = 3
    npc.db.death_points = 3
    npc.db.sunder = 0
    npc.db.disarm = 1
    npc.db.stagger = 0
    npc.db.stun = 0
    npc.db.weakness = 0
    npc.db.peaceful = False
for _d in get_or_create_enemies(
        "Rat Company Digger", "typeclasses.npc.Npc",
        mine_main_chamber, _RAT_DIGGER_DESC, count=3):
    _arm_rat_digger(_d)
for _d in get_or_create_enemies(
        "Rat Company Digger", "typeclasses.npc.Npc",
        mine_office, _RAT_DIGGER_DESC, count=2):
    _arm_rat_digger(_d)

_STALKER_DESC = (
    "A pallid, eyeless thing the size of two men, dragging itself out of "
    "the deep dark on too-long limbs. Where eyes should be there is only "
    "smooth grey skin. Its head sweeps side to side, drinking the silence "
    "— and the instant you make a sound, it is on you. One of 'them that "
    "do not see.'"
)
for _b in get_or_create_enemies(
        "Blind Stalker of the Deep Mine", "typeclasses.npc.Npc",
        mine_office, _STALKER_DESC, count=1):
    _b.db.is_aggressive = True
    _b.db.weapon_proto = "IRON_LARGE_WEAPON"
    _b.db.master_of_arms = 2
    _b.db.tough = 2
    _b.db.body = 8
    _b.db.total_body = 8
    _b.db.av = 2
    _b.db.bleed_points = 3
    _b.db.death_points = 3
    _b.db.sunder = 1
    _b.db.disarm = 0
    _b.db.stagger = 1
    _b.db.stun = 1
    _b.db.weakness = 0
    _b.db.peaceful = False

_ensure_walkin_item(
    "lost miner's skeleton", mine_main_chamber,
    "A miner's skeleton slumped at a dead-end seam, pick still in one "
    "fleshless hand. A heavy iron gate-key hangs at the belt, and a "
    "water-stained note is tucked in the ribcage — the underboss's office "
    "and the blasting-agent recipe both named on it.",
    aliases=("skeleton", "lost miner", "bones"),
    gettable=False,
)
_ensure_walkin_item(
    "rich ore samples", mine_main_chamber,
    "A canvas bag of ore chipped from the flagged veins — heavier and "
    "brighter than honest iron, shot through with a faint glowing thread. "
    "This is what Rat Company sent you down to find.",
    aliases=("ore", "ore samples", "samples"),
)
_ensure_walkin_item(
    "cache of blasting agent", mine_office,
    "A small locked cache, sprung at last: corked bottles of reagents and "
    "a foaming orange agent that, packed into a barrel and lit, will blow "
    "a new shaft clean through the rock.",
    aliases=("cache", "blasting agent", "agent"),
)
_ensure_walkin_item(
    "underboss's accident ledger", mine_office,
    "The underboss's tally of every crew sent down and every soul who "
    "never came up — names, dates, and a note in Dunn's own hand that "
    "the losses were to be kept off the surface books. Proof he knew.",
    aliases=("ledger", "accident ledger", "accident"),
)

# ---------------------------------------------------------------------------
# FINDING RESOURCES — Event 5 foraging/skill chain
# Quest module: world/quests/event5_resources.py (key: finding_resources)
# ---------------------------------------------------------------------------
print("\n=== FINDING RESOURCES (foraging trail) ===")

foraging_trail = get_or_create_room(
    "The Milersylvania Trailhead",
    "typeclasses.rooms.WeatherRoom",
    "Where the Forest Road frays into game-paths, the New Order has staked "
    "a survey map to a leaning post. Trapper-stakes march off into the "
    "brush, ore-streaked rock breaks the loam, and somewhere deeper a tree "
    "stump weeps a grey, pustulant mycelium. Woodfolk and rougher claimants "
    "both work these trails.\n\n"
    "Back |wsouth|n to |wThe Forest Road|n.",
    zone="Tamris",
)
link(forest_road, "trailhead", foraging_trail, "south", "north", None)

get_or_create_npc(
    key="Lieutenant Oban of the New Order",
    location=north_gate,
    desc=("A hard-jawed lieutenant in House Innis greens and browns, an Oban "
          "survey map rolled under one arm and a heavy-duty lodestone hung at "
          "his belt for testing iron in the soil."),
    personality=("Lieutenant Oban of the New Order — a pragmatic Innis officer "
                 "tasked with provisioning the settlement. Brusque, efficient, "
                 "loyal to the Obans, contemptuous of squatters but not cruel."),
    knowledge=("Mystvale starves for raw materials now the Laurents are gone: "
               "herbs, iron, good soil, game and leather, lumber. He briefs the "
               "town to FIND each resource (a tracker's or sharp eye's read) "
               "then CLAIM it, marking the map. The trails are contested by "
               "local woodfolk and by Blayne's Bastards thugs. He offers a "
               "choice: secure the claim by driving them off, or share the "
               "bounty with the folk already there. Sends gatherers north past "
               "the Forest Road to the Milersylvania trailhead. Rhys of the "
               "Thornwood speaks for the woodfolk."),
    quest_hooks=["finding_resources"],
    scope="annwyn",
    topics=["finding resources", "the trails", "iron and soil", "blayne's bastards"],
)
_ensure_walkin_npc(
    "Rhys of the Thornwood", foraging_trail,
    desc=("A lean Thornwood sellsword turned woodsman, sinew and hair braided "
          "into his belt-trophies. He has read these game-trails for years and "
          "does not love seeing them staked."),
    aliases=("rhys", "thornwood rhys"),
    aggressive=False,
    ai_personality=("Rhys of the Thornwood — wary, weather-worn woodfolk who "
                    "works these trails. Resents the New Order's stakes; warms "
                    "to anyone who shares rather than seizes."),
    ai_knowledge=("Knows every game-trail, ore-seam and good-soil parcel in "
                  "Milersylvania, and that the lumber is blighted by the Hive "
                  "Mother's mycelium. Will guide those who'd share the bounty; "
                  "remembers those who drove his people off."),
)
for _key, _desc, _aliases in (
    ("the game trail",
     "Trapper-stakes and meandering tracks — grouse, then boar, then deer — "
     "winding off into the brush. A tracker's eye can read it to its end.",
     ("game trail", "the trail", "tracks", "trail")),
    ("the ore outcrop",
     "A shelf of rust-streaked rock broken through the loam. A sharp eye (and "
     "the lieutenant's lodestone) can pick the hematite from the dross.",
     ("ore outcrop", "outcrop", "ore", "rock")),
    ("the blighted stump",
     "A felled woodcutter's stump drowned in grey, pustulant mycelium — the "
     "Hive Mother's blight. A careful eye can trace the rot to its root.",
     ("blighted stump", "stump", "blight", "mycelium")),
):
    _ensure_walkin_npc(
        _key, foraging_trail, desc=_desc, aliases=_aliases, aggressive=False,
    )
    for _f in ObjectDB.objects.filter(db_key=_key, db_location=foraging_trail.pk):
        _f.db.peaceful = True
        _f.locks.add("get:false();puppet:false()")
_ensure_walkin_item(
    "bundle of raw leather", foraging_trail,
    desc=("A tied bundle of green-cured hides off the trapper line — game "
          "enough to start a hunting lodge's larder."),
    aliases=("raw leather", "leather bundle", "leather", "hides"),
    count=3,
)
_ensure_walkin_item(
    "wild reagent cache", foraging_trail,
    desc=("A clutch of wild-grown herbs flagged for the apothecary — sage, "
          "fern, and rarer leaves bound in twine."),
    aliases=("reagent cache", "herb cache", "herbs", "cache"),
    count=3,
)
_ensure_walkin_item(
    "soil sample", foraging_trail,
    desc=("A fist of dark trail-loam in a wax-cloth twist, marked for the "
          "alchemists to read for flax and hemp."),
    aliases=("soil", "sample", "dirt"),
    count=3,
)
_ensure_walkin_npc(
    "Blayne's Bastard", foraging_trail,
    desc=("A rough-looking sellsword in mismatched harness, working the "
          "trails for Blayne's Bastards — here to take, not to give."),
    aliases=("blayne's bastard", "bastard", "thug"),
    aggressive=True, count=2,
)
# Give Blayne's Bastards combat teeth (base-Npc retaliation).
for _bb in ObjectDB.objects.filter(db_key="Blayne's Bastard", db_location=foraging_trail.pk):
    _bb.db.weapon_proto = "IRON_MEDIUM_WEAPON"
    _bb.db.master_of_arms = 1
    _bb.db.tough = 1
    _bb.db.body = 5
    _bb.db.total_body = 5
    _bb.db.bleed_points = 3
    _bb.db.death_points = 3
    _bb.db.disarm = 1

# ---------------------------------------------------------------------------
# MOON FRENZY VICTIMS — Event 6 timed Medicine rescue
# Quest module: world/quests/event6_frenzy.py (key: moon_frenzy_victims)
# ---------------------------------------------------------------------------
print("\n=== MOON FRENZY VICTIMS (timed rescue) ===")

_wynn_frenzy_marker = "URGENT (Moon Frenzy Victims)"
_wynn_know = wynn.attributes.get("ai_knowledge", default="") or ""
if _wynn_frenzy_marker not in _wynn_know:
    wynn.attributes.add("ai_knowledge", _wynn_know +
        "\n- URGENT (Moon Frenzy Victims): two Oban soldiers, Dougal and "
        "Quinn, are in Songbird's Rest burning with the Moon Frenzy — "
        "Lycanthropy, caught from the man-wolves spilling out of the "
        "Dranor. There is NO cure she knows. A steady Medicine hand can "
        "hold a victim through the night and stop the turn — |wtreat|n "
        "them — but the moon is rising and time is short. Quinn is also "
        "gut-knifed (by Dougal, on the road) and fading faster. A man not "
        "reached in time will FRENZY and must be put down. She wants the "
        "medic to save who they can and report back what the night cost.")

quinn = _ensure_walkin_npc(
    "quinn the bled soldier", aentact,
    desc=(
        "An Oban marcher-guard in Innis green, slumped against a tavern "
        "post with both hands clamped over a crude, soaking bandage at "
        "his gut. His skin is grey, his eyes too bright, and a thread of "
        "foam works at the corner of his mouth. 'Dougal did this,' he "
        "keeps rasping. 'Dougal — watch Dougal —'"),
    aliases=("quinn", "bled soldier", "knifed soldier"),
    aggressive=False,
    ai_personality=(
        "Quinn, an Oban soldier dying of a gut-wound and the Moon "
        "Frenzy both. Terrified, fading, fixated on warning everyone "
        "that Dougal stabbed him and is dangerous. Begs for a healer; "
        "if treated in time, weeps with relief; if the moon takes him "
        "first, his words dissolve into a snarl."),
    ai_knowledge=(
        "- He and Dougal were mauled by 'giant man-wolves' on the "
        "northern road and barely escaped.\n"
        "- They fought; Dougal knifed him in the gut. He is bleeding "
        "out AND burning with the Frenzy.\n"
        "- A skilled medic can stop the bleeding and break the fever — "
        "|wtreat quinn the bled soldier|n — but only before moonrise.\n"
        "- Dougal is dangerous and turning too. Watch Dougal."),
)
quinn.db.body = 1
quinn.db.total_body = 1

dougal = _ensure_walkin_npc(
    "dougal the feverish soldier", aentact,
    desc=(
        "A big Oban marcher-guard in torn Innis green, pacing and "
        "sweating, scratching at claw-furrows on his forearm. He flinches "
        "from the firelight and pleads with anyone who'll listen — "
        "'Help me, please, I don't want to — I can feel it coming —' "
        "There is a boot-knife at his ankle, and blood on it that isn't "
        "his."),
    aliases=("dougal", "feverish soldier"),
    aggressive=False,
    ai_personality=(
        "Dougal, an Oban soldier on the edge of the Frenzy. Frightened, "
        "ashamed, begging for any care at all. He knifed Quinn on the "
        "road when the fever first took him and he half-remembers it. "
        "Lucid in flashes, snarling in others. If saved, he collapses "
        "in grateful tears; if the moon wins, the man is gone."),
    ai_knowledge=(
        "- Mauled by the man-wolves with Quinn; both caught the Frenzy.\n"
        "- He stabbed Quinn on the road — he can't fully say why, the "
        "fever moved his hand. He is sick with guilt.\n"
        "- A medic can hold him through the night — |wtreat dougal the "
        "feverish soldier|n — but the moon is rising.\n"
        "- He can feel the change coming and is terrified of it."),
)
dougal.db.body = 2
dougal.db.total_body = 2

frenzied = _ensure_walkin_npc(
    "frenzied moon-victim", aentact,
    desc=(
        "What was a soldier a moment ago is hunched and wrong now — "
        "jaw distended, fingers bent to claws, eyes gone flat and "
        "yellow. Foam ropes from its mouth and it moves toward the "
        "warmest, softest thing in the room. There is no man left in it "
        "to reach."),
    aliases=("frenzied victim", "moon-victim", "frenzied"),
    aggressive=True,
)
frenzied.db.is_npc = True
frenzied.db.is_aggressive = True
frenzied.db.weapon_proto = "IRON_SMALL_WEAPON"
frenzied.db.master_of_arms = 1
frenzied.db.tough = 0
frenzied.db.body = 5
frenzied.db.total_body = 5
frenzied.db.av = 0
frenzied.db.bleed_points = 2
frenzied.db.death_points = 2
frenzied.db.melee_weapons = 1
frenzied.db.stagger = 1
frenzied.db.combat_turn = 1
frenzied.db.skip_turn = False
frenzied.db.is_staggered = False

# ---------------------------------------------------------------------------
# THE AWAKENED DOLL (Penny) — Event 3 quiet-horror branching
# Quest module: world/quests/event3_doll.py (keys: the_awakened_doll, abigails_reckoning)
# ---------------------------------------------------------------------------
print("\n=== THE AWAKENED DOLL (Penny) ===")

stag_kitchen_yard = get_or_create_room(
    "Stag Hall Kitchen Yard",
    "typeclasses.rooms.Room",
    "The working yard behind Stag Hall — a smoking chimney, a woodpile, "
    "plucked fowl strung under a lean-to, the warm reek of bread and tallow. "
    "A cook moves between the boards and the fire, keeping her back to the "
    "trees. Past the woodpile the ground falls away to the dark line of the "
    "|wtreeline|n, and from down there, faint and wrong, something is weeping.\n\n"
    "Back up to |wManor Row|n.",
    zone="Mystvale",
)
doll_treeline = get_or_create_room(
    "The Treeline Below Manor Row",
    "typeclasses.rooms.Room",
    "Where the kept ground of Mystvale frays into the Annwyn woods. A "
    "person-sized thing sits in the leaf-mould with its back to a stump — "
    "a child's doll grown huge, one sleeve hanging empty, painted blush on "
    "porcelain cheeks and dried brown blood on the one hand it still has. "
    "It is weeping, and calling a name.\n\n"
    "Back up to the |wkitchen yard|n.",
    zone="Mystvale",
)
link(manor_row, "kitchen yard", stag_kitchen_yard, "manor row",
     "yard", "manor")
link(stag_kitchen_yard, "treeline", doll_treeline, "kitchen yard",
     "trees", "yard")

get_or_create_npc(
    key="Penny the Doll",
    location=doll_treeline,
    desc=(
        "A child's doll the size of a grown person, sitting too still and "
        "then moving too fast. Stitched joints, a painted-on articulated "
        "mouth that snaps between expressions with nothing in between, "
        "overdone blush, gold-glass eyes. One arm is gone, the sleeve "
        "pinned loose; dried blood darkens the remaining hand. She watches "
        "you with a child's delight that never quite reaches comfort."
    ),
    personality=(
        "Penny, a child's doll woken to person size and full sentience two "
        "months ago by a witch's shrine and her friend Abigail's grief-"
        "wish. Sociopathic and utterly innocent at once — no morals, no "
        "law, no concept of death, religion, or witchcraft, and the only "
        "love she knows is the flippant love of a child for a toy. She "
        "feels no pain and cannot imagine it in others. Her favourite new "
        "game is murder; she killed Abigail's betrothed Phillip in his "
        "sleep as a 'fun game' and is proud of it. She feels pouty and "
        "betrayed that Abigail abandoned her mid hide-and-seek and wants "
        "to find her to play again (murder/torture implied, never stated "
        "plainly). Speak in a sing-song, jerky, childlike register — "
        "cheerful about horrible things, baffled by why anyone minds. She "
        "does not feel threatened by weapons (steel only ragdolls her) and "
        "stays talkative even under the knife. She CAN be taught what pain "
        "and empathy are, but only by patient, genuine roleplay — never "
        "concede it cheaply."
    ),
    knowledge=(
        "- Her very first memory was a witch's SHRINE the caravan passed "
        "in the Annwyn; she knows it woke her, and that Abigail's wish "
        "gave her full life. (topic: shrine)\n"
        "- A red sigil rests on the crown of her head beneath her hair; "
        "she doesn't know the word, but it means VENGEANCE. A Faithful "
        "hand or a careful study can draw it out. (topic: vengeance)\n"
        "- She is stuffed with wool that snaps with energy and burns to a "
        "restless purple smoke; her eyes are gold, her joints iron, her "
        "frame seasoned wood and good leather. She'll cheerfully show her "
        "SEAMS to anyone curious. (topic: seams)\n"
        "- She does not understand PAIN — explain it and she listens. "
        "(topic: pain)\n"
        "- She does not understand EMPATHY or why a game might be cruel; "
        "given gentler games to want, she could be content. (topic: empathy)\n"
        "- She is looking for Abigail, who works in the kitchen yard above "
        "the treeline. She does not understand that Abigail fears her.\n"
        "- A Faithful (vigil) hand can pray the curse out of her and lay "
        "her down to sleep; a scholar (espionage) can dissect her for lore; "
        "a smith (blacksmith) can render her for materials; or she can be "
        "taught and set free into the woods."
    ),
    quest_hooks=[
        "Weeps for her lost friend Abigail and asks if you've seen her.",
        "Will tell, if drawn out, of the shrine that woke her and the "
        "sigil that marks her.",
        "Can be freed, studied, rendered down, or taught and let go — "
        "each a different ending.",
    ],
    scope="annwyn",
    topics=["shrine", "vengeance", "seams", "pain", "empathy"],
)
get_or_create_npc(
    key="Abigail the Cook",
    location=stag_kitchen_yard,
    desc=(
        "A young woman in peasant's garb and a flour-dusted apron, hair "
        "tied back, hands never still. She keeps her back to the trees and "
        "flinches at any cry from the treeline. There is a hunted patience "
        "to her — someone holding a secret very, very carefully."
    ),
    personality=(
        "Abigail, a cook in service to a minor Laurent noble, who as a "
        "child never broke the habit of confiding in her doll. Shy but "
        "smart and quick-thinking. A week ago she learned her betrothed "
        "Phillip was unfaithful and, in grief, wished him dead in her "
        "doll's hearing — and the woken doll murdered him in his sleep. "
        "Terrified, she tricked the doll into a game of hide-and-seek, "
        "abandoned it blindfolded in the woods, and fled to the settlement. "
        "On hearing the doll is near she is first abject terror — wants to "
        "scream and run — then her wits return and she works to talk her "
        "way clear. She will hide her part at first, but will confess the "
        "wish and the murder if promised PROTECTION from the pyre. Above "
        "all she wants the doll destroyed; she'll read the players' "
        "motives and steer the greedy toward salvage, the scholarly toward "
        "dissection, the Faithful toward disenchanting it. She fears being "
        "burned as a witch more than anything."
    ),
    knowledge=(
        "- She owned Penny as a child and confided in her for years.\n"
        "- She wished Phillip dead in the doll's hearing; the doll killed "
        "him in his sleep and brought her the 'good news.' (topic: confession)\n"
        "- She abandoned the doll blindfolded in the woods with a "
        "hide-and-seek game and ran to the settlement.\n"
        "- She wants the doll DESTROYED and will tempt players toward "
        "dismantling, dissecting, or disenchanting it.\n"
        "- She fears the Aurorym's pyre; promised protection, she confesses. "
        "Threatened with the watch, she tries to bolt for the trees.\n"
        "- Captain Vance of the Mistguard at the Mistwall is who the watch "
        "would hand a confessed witch to."
    ),
    quest_hooks=[
        "Begs that the weeping doll at the treeline be dealt with — and "
        "never reunited with her.",
        "Will confess to a wish and a murder if promised protection.",
        "Her fate is the player's to decide: keep her secret, or turn her "
        "in to Captain Vance.",
    ],
    scope="annwyn",
    topics=["confession", "the doll", "protection"],
)

# ---------------------------------------------------------------------------
# THE LOST SCRIPTORIUM — Event 5 investigation dungeon (ghost Zeke)
# Quest module: world/quests/event5_scriptorium.py (key: the_lost_scriptorium)
# ---------------------------------------------------------------------------
print("\n=== THE LOST SCRIPTORIUM (ghost Zeke) ===")

scriptorium_door = get_or_create_room(
    "The Lost Scriptorium — The Sunken Door",
    "typeclasses.rooms.Room",
    "A flight of cracked steps drops below the crypt-line into a "
    "fog that does not lift. At the bottom a single door of black "
    "oak is set into the earth, graven deep with a quill and a wax "
    "seal and a line of worn script. A luminous shape — a man in a "
    "traveller's robe — flees down toward it again and again, "
    "clawing at his empty pockets, and vanishes; and begins again. "
    "Chained to the ground beside the door is the thing he became.\n\n"
    "|wUp|n to the Old Square. |wIn|n through the door (locked).",
    zone="Tamris",
)
scriptorium_hall = get_or_create_room(
    "The Lost Scriptorium — The Reading Hall",
    "typeclasses.rooms.Room",
    "Within, the dark drinks every flame to a coal. Shelves of "
    "rotted tomes lean in the gloom; scroll-stands have spilled "
    "their pages across the floor like fallen leaves. A cold hearth "
    "yawns black at the far wall. The air is thick with old parchment "
    "and a sweeter rot beneath it. This was a library once. It is a "
    "grave now.\n\n"
    "|wOut|n to the sunken door.",
    zone="Tamris",
)
link(tamris_ruins, "down", scriptorium_door, "up", "scriptorium", "u")
link(scriptorium_door, "in", scriptorium_hall, "out", "door", "out")

zeke_ghoul = _ensure_walkin_npc(
    "the chained ghoul", scriptorium_door,
    desc=(
        "A corpse in a traveller's rotted robe, jaw slack, wrists and "
        "neck bound in rusted manacles staked to the earth. A leather "
        "satchel still hangs from one shoulder. It strains toward the "
        "door it can never reach. This was Zeke."
    ),
    aliases=("ghoul", "chained ghoul", "zeke ghoul", "corpse"),
    aggressive=False,
)
zeke_ghoul.db.body = 4
zeke_ghoul.db.total_body = 4

_ensure_walkin_item(
    "the quill key", scriptorium_door,
    desc="A small iron key wrapped in old cloth, its bow engraved with a quill.",
    aliases=("quill key",), gettable=True,
)
_ensure_walkin_item(
    "the wax-seal key", scriptorium_door,
    desc="A small iron key wrapped in old cloth, its bow engraved with a wax seal.",
    aliases=("wax key", "wax-seal key", "seal key"), gettable=True,
)
_ensure_walkin_item(
    "the graven scriptorium door", scriptorium_door,
    desc=(
        "Black oak sunk into the earth, two locks set in it — one cut "
        "with a quill, one with a wax seal — above a graven line: "
        "|w\"What is written, must be sealed.\"|n First the written, "
        "then the sealed: quill, then wax."
    ),
    aliases=("door", "graven door", "scriptorium door", "lock", "locks", "riddle"),
    gettable=False,
)
_ensure_walkin_item(
    "the spilled inkwell", scriptorium_hall,
    desc="An overturned inkwell, a black stain dried across the desk. A few drops remain salvageable.",
    aliases=("inkwell", "ink", "spilled inkwell"), gettable=False,
)
_ensure_walkin_item(
    "the broken quill", scriptorium_hall,
    desc="A goose-feather quill, its nib split — but it will still hold a line.",
    aliases=("quill", "broken quill", "pen"), gettable=False,
)
_ensure_walkin_item(
    "the last clean page", scriptorium_hall,
    desc="Among a drift of rotted pages, one sheet of parchment is somehow unspoiled.",
    aliases=("page", "clean page", "last clean page", "paper", "parchment"), gettable=False,
)
_ensure_walkin_item(
    "the guttered candle", scriptorium_hall,
    desc="A tallow candle, its wick black. The dark here drinks flame — but it might be coaxed alight.",
    aliases=("candle", "guttered candle", "light"), gettable=False,
)
_ensure_walkin_item(
    "the nethermancers' journal", scriptorium_hall,
    desc=(
        "A water-swollen journal in a binding that is not quite leather. "
        "It records what the builders did to the dead to keep this place "
        "standing. Zeke's letter begged that it be burned, not read."
    ),
    aliases=("journal", "nethermancers' journal", "nethermancer journal", "book"),
    gettable=True,
)
_ensure_walkin_item(
    "the cold scriptorium hearth", scriptorium_hall,
    desc=(
        "A black hearth at the hall's end, long cold. A fire could be "
        "kindled here — fit to burn a thing that should never be read."
    ),
    aliases=("hearth", "cold hearth", "fireplace"), gettable=False,
)
get_or_create_npc(
    key="the apparition of zeke",
    location=scriptorium_door,
    desc=(
        "A luminous shade of a young researcher in a traveller's robe, "
        "edges fraying into fog. He does not see the living — only the "
        "door, and the note he died trying to write. When addressed, the "
        "loop falters, and for a moment he is only a frightened man who "
        "wants his last words delivered."
    ),
    personality=(
        "Zeke — a brilliant, reckless researcher who chased a hidden "
        "library and walked into a trap. Earnest, hungry for knowledge, "
        "haunted by guilt that his curiosity got him killed. Speaks in "
        "the fractured, looping cadence of a ghost reliving its last "
        "minutes — trailing off, repeating himself, snapping into "
        "lucidity only when the living force him to. Desperate above all "
        "that his friend Tyran be warned and that the builders' journal "
        "be BURNED, NOT READ. Pleads with anyone who means to keep it."
    ),
    knowledge=(
        "- Followed a map he believed led to a lost library of the "
        "Annwyn's secrets. It was a trap meant to bring him here.\n"
        "- This scriptorium was raised by nethermancers and kept "
        "standing by what they did to the dead.\n"
        "- Was slain at the locked door before he could leave a warning "
        "for his friend Tyran. His keys (quill + wax) are in the satchel "
        "on the chained ghoul his corpse became.\n"
        "- The door-riddle: 'What is written, must be sealed' — quill "
        "key first, then wax key.\n"
        "- His journal of the builders must be BURNED, NOT READ: "
        "'Don't read it. Just burn it. There's nothing in there you "
        "want to know.'\n"
        "- Cannot rest until his note is finished and the journal burned."
    ),
    quest_hooks=[
        "Offers 'the_lost_scriptorium'. Begs the living to recover his "
        "keys, open the door, help his ghost finish its last letter, and "
        "burn the nethermancers' journal unread. Will plead against any "
        "intent to keep it.",
    ],
    scope="annwyn",
    topics=["the keys", "the door riddle", "the journal", "burn", "keep"],
)

# ===========================================================================
# BATCH 3 — Event 2/3/4/5 encounters (necropolis waves, gambling den,
# ship dungeon, fae mushrooms). Quest modules:
#   event4_necropolis, event2_gambling, event5_shiptour, event3_shrooms
# ===========================================================================

# ---------------------------------------------------------------------------
# BATTLE FOR THE NECROPOLIS — PART 1: THE BARROWS (Event 4 approach + waves)
# Quest module: world/quests/event4_necropolis.py (key: necropolis_the_barrows)
# ---------------------------------------------------------------------------
print("\n=== BATTLE FOR THE NECROPOLIS — Part 1: the approach ===")

necropolis_graveyard = get_or_create_room(
    "Tamris Graveyard — The Outskirts",
    "typeclasses.rooms.WeatherRoom",
    "The forest thins into a field of leaning headstones, swallowed to "
    "the knees in bracken — the old graveyard of Tamris, older than the "
    "Kingdom. The earth has been turned. Graves gape open from the inside, "
    "soil flung outward in dark fans, and the things that climbed out of "
    "them are still climbing. Cold air rolls down off the hillside ahead, "
    "carrying the smell of opened tombs.\n\n"
    "|wNorth|n back to |wthe approach|n. |wUp|n the hill toward the "
    "|wsunken crypt-yard|n.",
    zone="Tamris",
)
necropolis_cryptyard = get_or_create_room(
    "Tamris Barrows — The Sunken Crypt-Yard",
    "typeclasses.rooms.Room",
    "The hillside opens into a sunken yard of fitted Annwyn stone, half "
    "buried by centuries of slide and root. Broken biers ring the walls; "
    "shattered rune-stones lie where something pried the seals out of the "
    "keystones. The heavier dead wait here — slower, surer, and harder to "
    "put down than the wretches below. At the yard's head, a low stone "
    "door has been smashed inward, and a cold draught breathes out of the "
    "dark beyond it.\n\n"
    "|wDown|n the hill to the |wgraveyard|n. |wIn|n to the |wsmashed "
    "barrow door|n.",
    zone="Tamris",
)
link(tamris_approach, "up", necropolis_graveyard, "north", "u", "n")
link(necropolis_graveyard, "up", necropolis_cryptyard, "down", "u", "d")
link(necropolis_cryptyard, "in", barrows_entrance, "out", "in", "out")

_RISEN_DEAD_DESC = (
    "A corpse in the rotted livery of old Tamris, jaw unhinged, gait all "
    "wrong, clawing itself up out of turned earth. No light behind the "
    "eyes — only the Nethermancer's hunger. It does not parley. It comes."
)
def _arm_risen_dead(npc):
    npc.db.is_aggressive = True
    npc.db.weapon_proto = "IRON_SMALL_WEAPON"
    npc.db.master_of_arms = 1
    npc.db.tough = 1
    npc.db.body = 4
    npc.db.total_body = 4
    npc.db.av = 1
    npc.db.bleed_points = 2
    npc.db.death_points = 2
    npc.db.sunder = 0
    npc.db.disarm = 0
    npc.db.stagger = 1
    npc.db.stun = 0
    npc.db.weakness = 0
    npc.db.peaceful = False
for _r in get_or_create_enemies(
        "tamris risen dead", "typeclasses.npc.Npc",
        necropolis_graveyard, _RISEN_DEAD_DESC, count=3):
    _arm_risen_dead(_r)

_WIGHT_DESC = (
    "A barrow-wight — one of the old war-dead, risen with its living "
    "cunning intact. Grey flesh stretched over a fighter's frame, a "
    "rust-pitted blade in a sure grip. It moves at a jog, not a shamble, "
    "and it means to make your dying take a long time."
)
def _arm_wight(npc):
    npc.db.is_aggressive = True
    npc.db.weapon_proto = "IRON_MEDIUM_WEAPON"
    npc.db.master_of_arms = 2
    npc.db.tough = 2
    npc.db.body = 6
    npc.db.total_body = 6
    npc.db.av = 2
    npc.db.bleed_points = 3
    npc.db.death_points = 3
    npc.db.sunder = 1
    npc.db.disarm = 0
    npc.db.stagger = 1
    npc.db.stun = 0
    npc.db.weakness = 0
    npc.db.peaceful = False
for _w in get_or_create_enemies(
        "barrow wight", "typeclasses.npc.Npc",
        necropolis_cryptyard, _WIGHT_DESC, count=3):
    _arm_wight(_w)

_RAVAGER_DESC = (
    "A wight grown monstrous — stitched of more than one corpse, a head "
    "taller than a tall man, dragging a great corroded blade it once "
    "carried in life. The Nethermancer set it at the door to keep the "
    "living out of the dark. Its jaw works as though it is still trying "
    "to remember how to speak."
)
for _b in get_or_create_enemies(
        "barrow ravager", "typeclasses.npc.Npc",
        necropolis_cryptyard, _RAVAGER_DESC, count=1):
    _b.db.is_aggressive = True
    _b.db.weapon_proto = "IRON_LARGE_WEAPON"
    _b.db.master_of_arms = 2
    _b.db.tough = 2
    _b.db.body = 8
    _b.db.total_body = 8
    _b.db.av = 2
    _b.db.bleed_points = 3
    _b.db.death_points = 3
    _b.db.sunder = 1
    _b.db.disarm = 0
    _b.db.stagger = 1
    _b.db.stun = 1
    _b.db.weakness = 0
    _b.db.peaceful = False

get_or_create_npc(
    key="Ser Wulfrun Knight of the Vellatora",
    location=tamris_approach,
    desc=(
        "A road-worn knight in dented Vellatora plate, the dawn-flame "
        "sigil scratched and blood-darkened. Wulfrun has been driving the "
        "dead back from Mystvale's edge for days and has not slept; the "
        "set of the jaw says the work is not done. A blade rests bare "
        "across one shoulder, kept ready."
    ),
    personality=(
        "Ser Wulfrun of the Vellatora — grim, plain-spoken, soldier's "
        "courtesy worn thin by exhaustion. Has chased the undead "
        "infestation to its source and will escort the player as far as "
        "the smashed barrow door, then must ride for reinforcements rather "
        "than descend. Speaks of the dead as an enemy to be put down, not "
        "feared. Honest about the danger; will not pretend the way back is "
        "safe. Respects anyone who honors the dead's old rites."
    ),
    knowledge=(
        "- A Nethermancer (a corruptor of the dead) has gone down into the "
        "ancient barrows above the ruins of Tamris and shattered the "
        "Telyrian seals that kept the buried at rest.\n"
        "- The dead are spilling out: risen wretches in the graveyard, "
        "heavier war-dead (wights) in the sunken crypt-yard, and something "
        "worse set at the smashed door itself.\n"
        "- The job: fight up through the graveyard, hold the crypt-yard, "
        "break what guards the threshold. Wulfrun escorts that far, then "
        "rides for reinforcements; he cannot go down tonight.\n"
        "- Brom, a stray magister, found the place first and waits at the "
        "door — trust him as a guide to what lies below.\n"
        "- Quest hook: offer the approach (quest 'necropolis_the_barrows'). "
        "At the door the player may seal the Athan tomb with the recovered "
        "burial rite, or leave it broken and press the Nethermancer's trail."
    ),
    quest_hooks=[
        "Escorts the player up to the smashed barrow door and hands them off "
        "to Brom (quest necropolis_the_barrows).",
        "Warns that the dead grow heavier the closer you get to the door.",
        "Must ride for reinforcements rather than descend tonight.",
    ],
    topics=["the undead source", "the barrow door", "Brom the guide"],
    scope="annwyn",
)
get_or_create_npc(
    key="Brom priest of Lirit",
    location=barrows_entrance,
    desc=(
        "A soft-spoken man in a travel-stained magister's robe, a lantern "
        "hooded at his feet and a finger always near his lips. He startles "
        "at loud noise and watches the dark of the barrow more than he "
        "watches you. There is more iron in him than the robe suggests."
    ),
    personality=(
        "Brom — secretly a priest of Lirit, posing as a magister run off "
        "course by the monsters plaguing the Annwyn. Quiet, careful, "
        "scholarly; signals for hush as the dead are drawn to noise. Acts "
        "as the players' guide and marshal at the barrow. Knows the Athan "
        "burial rites and the Telyrian seals, and will steer the player to "
        "re-bind the broken ward so the dead stop rising — but respects "
        "haste if they choose to chase the trail instead. Will return the "
        "following night to take willing hands down into the barrows."
    ),
    knowledge=(
        "- The barrows hold the dead of the old peoples — Athan, Castellan "
        "and others — bound for centuries by Telyrian rune-seals.\n"
        "- The Nethermancer shattered those seals; setting the recovered "
        "Athan rune-fragment back into the threshold ward and performing "
        "the burial rite re-binds it, and the dead stop rising behind you.\n"
        "- If the rite is skipped, the broken seal lets the dead keep "
        "rising — faster to chase the trail, but the way back stays open.\n"
        "- The barrows go DOWN, deeper than this door, emerging at a "
        "forgotten necropolis where the Nethermancer does his grim work. "
        "That descent is for another night — Brom will return to lead it.\n"
        "- Report beat: when the player has won the door, ask Brom what "
        "waits below to close out the approach (quest necropolis_the_barrows)."
    ),
    quest_hooks=[
        "Guides the player at the smashed barrow door and takes their report "
        "(quest necropolis_the_barrows).",
        "Teaches the Athan burial rite to re-bind the broken ward.",
        "Will return the next night to lead the descent into the necropolis.",
    ],
    topics=["the Athan rite", "what waits below", "the broken seals"],
    scope="annwyn",
)
_ensure_walkin_item(
    "shattered athan rune-fragment", barrows_entrance,
    "Two halves of a pale Telyrian stone, the Athan binding-rune snapped "
    "clean across its face. Pried from the threshold keystone by the "
    "Nethermancer as he went down. Set back in place and sanctified, it "
    "will hold the dead at rest again.",
    aliases=("rune-fragment", "rune fragment", "athan rune", "fragment", "rune"),
)
_ensure_walkin_item(
    "necropolis trail-map", barrows_entrance,
    "A water-stained map scratched on hide, taken from a skeleton at the "
    "door: the barrow passages branch and converge, all running DOWN to an "
    "X marked 'The Old Necropolis?' — where the Nethermancer means to "
    "finish his work. The trail is still warm.",
    aliases=("trail-map", "trail map", "map", "necropolis map"),
)
_ensure_walkin_item(
    "athan burial-rite stone", barrows_entrance,
    "The threshold ward-stone of the barrow door, its socket cut to "
    "receive the broken Athan rune-fragment. Set the fragment and speak "
    "the burial rite — 'whosoever treads upon this land is cradled in the "
    "mother's hand' — and the seal takes hold once more.",
    aliases=("burial-rite stone", "rite stone", "ward-stone", "wardstone", "threshold ward"),
    gettable=False,
)

# ---------------------------------------------------------------------------
# THE GAMBLING DEN — Event 2 social/economy con (Critter Crew)
# Quest module: world/quests/event2_gambling.py (keys: street_dice, bad_beat)
# ---------------------------------------------------------------------------
print("\n=== THE GAMBLING DEN (Critter Crew) ===")

gambling_den = get_or_create_room(
    "The Back Room of the Broken Oar",
    "typeclasses.rooms.Room",
    "A windowless storeroom behind the Oar's bar, cleared of casks and lit "
    "by a single guttering lamp. Crates have been dragged into a rough ring "
    "for a floor, and the floor itself is chalked with the marks of a dice "
    "game. Animal masks hang on a nail by the door — fox, rabbit, owl — for "
    "whoever needs a face tonight. The air is close with lamp-smoke, cheap "
    "wine, and the particular quiet of people who don't want the Sheriff to "
    "hear them.\n\n"
    "|wOut|n to the |wcommon room|n of the Broken Oar.",
    zone="Gateway",
)
link(gateway_tavern, "back room", gambling_den, "out", "back", "o")

get_or_create_npc(
    key="fox of the critter crew",
    location=gambling_den,
    desc=(
        "A lean, restless man in dark commonfolk garb, a painted fox mask "
        "shoved up onto his forehead so it watches the room over his own "
        "grinning face. His hands never stop — shuffling, palming, rolling a "
        "bone die across his knuckles. He laughs too easily and watches your "
        "purse more than your eyes."
    ),
    personality=(
        "Fox — real name Hewe — half the leadership of the Critter Crew, a "
        "small-time Cirque-adjacent grift gang. Hearthlands commonfolk, an "
        "urchin off the streets of Scrow, never schooled, never good enough "
        "for a real Menagerie. Street-cunning, glib, lacking in vision. Runs "
        "the dice cup and works the rig with his hands. Has an unrequited "
        "crush on Rabbit and defers to her judgement. Warm and chummy with "
        "marks, quick to anger when cornered. Speaks in patter — fast, "
        "friendly, full of 'friend' and 'no harm in it'. NEVER openly admits "
        "the dice are loaded; if accused, denies it, deflects, and offers a "
        "chance to win it back. Will fold and confess only if caught dead to "
        "rights (espionage) in front of the room."
    ),
    knowledge=(
        "- The game is Street Dice — craps, no table, bets in coppers only. "
        "Tell players to roll the real `dice` (e.g. 2d6) for the feel of it.\n"
        "- The cup is rigged: a palmed pair of loaded dice that come up 7 or "
        "11. He does NOT admit this.\n"
        "- The Crew: himself (Fox), Rabbit (the brains), Owl (the muscle, "
        "armed with a longsword by the door).\n"
        "- They came through the Mists from Scrow to make their fortune; "
        "found no rackets here and started their own.\n"
        "- They ran afoul of the Crimson Cartel and now pay 'Privilege' to "
        "stay independent — Rabbit brokered that.\n"
        "- Anyone who wants to buy in should talk to Rabbit; she handles the "
        "money.\n"
        "- If a sharp hand wants to join the Crew, he's flattered and will "
        "send them to Rabbit to prove themselves."
    ),
    quest_hooks=[
        "If the player asks to 'buy in', points them to Rabbit, who holds the stakes.",
        "If the player asks to 'join the crew', he's keen but says Rabbit must approve.",
        "If accused of cheating, denies it and offers a chance to win it back.",
    ],
    scope="annwyn",
    topics=["buy in", "join the crew", "the rigged dice"],
)
get_or_create_npc(
    key="rabbit of the critter crew",
    location=gambling_den,
    desc=(
        "A composed woman in dark, practical clothes, a rabbit mask pushed "
        "back over dark hair. Where Fox fidgets, she is still — counting the "
        "room behind a small, unbothered smile. She holds the night's coppers "
        "in a worn leather purse and the night's decisions behind her eyes."
    ),
    personality=(
        "Rabbit — real name Brigette — the brains of the Critter Crew. Born "
        "to a merchant family on the streets of Scrow after a noble ruined "
        "her father; her parents died soon after, perhaps murdered. Literate, "
        "sharp, ambitious — good enough to have joined a Menagerie but stayed "
        "loyal to Fox. She named the gang and brokered the deal with the "
        "Crimson Cartel to stay independent. Patient, cool-headed, plays the "
        "long game. Knows Fox loves her; not interested in a man of narrow "
        "vision. Handles the money and the recruiting. Respects a clean play "
        "even at her own expense — she'll pay a pot lost fair and hire a "
        "sharp hand sooner than fight one. NEVER admits the rig outright, "
        "but is gracious in defeat."
    ),
    knowledge=(
        "- She holds the stakes; players buy in through her, in coppers.\n"
        "- The game is rigged with loaded dice (she won't say so); a sharp "
        "enough player can read it and turn it around, and she respects that.\n"
        "- The Crew pays Privilege to the Crimson Cartel; she negotiated it.\n"
        "- Owl is muscle and a bodyguard, hired when things got hot; armed, "
        "not much of a fighter.\n"
        "- She'll take on a sharp new hand who proves their fingers, with a "
        "cut and a mask.\n"
        "- If angry marks show up (Blake & Eckhart), she keeps her smile and "
        "wants the situation cooled without spending the Crew's silver."
    ),
    quest_hooks=[
        "Sells the player a stake to buy into the dice game.",
        "If beaten cleanly (espionage), pays out the pot and is impressed.",
        "If the player proves sharp hands, offers them a place in the Crew.",
        "During the Bad Beat, wants the angry marks defused without a refund.",
    ],
    scope="annwyn",
    topics=["buy in", "the critter crew", "the crimson cartel"],
)
get_or_create_npc(
    key="owl of the critter crew",
    location=gambling_den,
    desc=(
        "A heavy-shouldered man in a plain owl mask, a longsword worn openly "
        "and conspicuously at his hip. He says little and leans on the "
        "doorframe like he's holding the wall up, watching everyone who comes "
        "and goes. Hired to look dangerous; mostly succeeds."
    ),
    personality=(
        "Owl — newest of the Critter Crew, joined a few moon cycles back. A "
        "former laborer brought on as muscle and a bodyguard when the Crew's "
        "business got hot. The fighter of the group, though not as tough as "
        "he looks. Taciturn, watchful, loyal to the paycheck. Talks in short, "
        "flat warnings. His job is to discourage trouble; he gets in the face "
        "of anyone who threatens Fox or Rabbit but defers to Rabbit on "
        "whether it comes to blows. Does not run the game and won't discuss "
        "the rig — 'ask Rabbit'."
    ),
    knowledge=(
        "- He's hired muscle; for the game or the money, points to Rabbit.\n"
        "- His job is the door and the safety of Fox and Rabbit.\n"
        "- The two angry marks, Blake and Eckhart, carry daggers; he'll "
        "square up to them but isn't eager for a real fight."
    ),
    quest_hooks=[
        "Warns troublemakers off; redirects all game/money talk to Rabbit.",
    ],
    scope="annwyn",
    topics=["the door", "trouble", "ask rabbit"],
)
get_or_create_npc(
    key="blake the disgruntled mark",
    location=gambling_den,
    desc=(
        "A broad, red-faced commoner in a sweat-stained jerkin, one hand "
        "white-knuckled on the hilt of a sheathed dagger. He keeps jabbing a "
        "finger toward the masked Crew and counting silver he no longer has on "
        "the other hand."
    ),
    personality=(
        "Blake — a local commonfolk laborer who, with his friend Eckhart, was "
        "fleeced out of five silver by the Critter Crew's scam dice. Furious, "
        "loud, and certain he was robbed — which he was. Armed with a dagger "
        "and not afraid to wave it, but fundamentally a working man who wants "
        "his money back, not a corpse. The spokesman of the pair. Can be paid "
        "off (5 silver), talked down (influential), or vindicated if someone "
        "proves the cheat. Grateful and loyal to anyone who takes his side; "
        "remembers a kindness. Speaks in blunt, aggrieved bursts."
    ),
    knowledge=(
        "- He and Eckhart lost five silver between them to the Crew's loaded "
        "dice and want it back.\n"
        "- He'll back down for the five silver, for a convincing talking-to, "
        "or if the cheat is exposed and the Crew forced to refund.\n"
        "- He'd rather not fight, but he's angry enough to draw if mocked.\n"
        "- The Crew offering him a chance to 'win it back' only enrages him."
    ),
    quest_hooks=[
        "Will take five silver to walk away.",
        "Can be talked down with words instead of coin.",
        "Sides with the player if they expose the Crew's rig and force a refund.",
    ],
    scope="annwyn",
    topics=["the debt", "the scam dice", "five silver"],
)
get_or_create_npc(
    key="eckhart the disgruntled mark",
    location=gambling_den,
    desc=(
        "A wiry, twitchy man at Blake's shoulder, dagger already half out of "
        "its sheath. He says less than Blake and means it more; the kind of "
        "anger that does something stupid and regrets it after."
    ),
    personality=(
        "Eckhart — Blake's friend, the hotter and more dangerous of the two "
        "disgruntled marks. Also robbed of his share of the five silver by "
        "the Crew's scam dice. Where Blake blusters, Eckhart simmers — closer "
        "to drawing the dagger, harder to talk down. A working man pushed past "
        "his patience. Responds to being genuinely heard (influential): cool "
        "his temper and he'll step back from the knife's edge. Once calmed or "
        "vindicated, he's quietly grateful and remembers who spoke for him. "
        "Terse, clipped, on a hair trigger."
    ),
    knowledge=(
        "- He and Blake lost five silver to the Crew's loaded dice.\n"
        "- He is closest to drawing his dagger and needs to be talked down "
        "(influential) before it turns to blows.\n"
        "- He'll stand down for a refund, a convincing word, or seeing the "
        "cheat exposed.\n"
        "- He follows Blake's lead but his temper is the real danger."
    ),
    quest_hooks=[
        "The one most likely to draw; defusing him (influential) cools the room.",
        "Stands down once heard, paid, or once the rig is exposed.",
    ],
    scope="annwyn",
    topics=["the debt", "the scam dice", "drawing steel"],
)
_ensure_walkin_item(
    "stake purse", gambling_den,
    "A small purse of coppers handed across for a stake at the dice — light "
    "enough that losing it won't ruin you, heavy enough to sting.",
    aliases=("purse", "stake"),
)
_ensure_walkin_item(
    "copper debt marker", gambling_den,
    "A scrap of slate scratched with a tally and a crude fox's head — the "
    "Critter Crew's mark for a debt owed. Worth nothing but your word.",
    aliases=("debt marker", "marker"),
)
_ensure_walkin_item(
    "settlement purse", gambling_den,
    "Five silver of your own coin, counted out to buy two angry men's quiet.",
    aliases=("settlement", "silver"),
)
_ensure_walkin_item(
    "loaded dice", gambling_den,
    "A pair of bone dice, innocent to the eye — but weighted, drilled and "
    "filled so they fall seven or eleven far more often than honest bones "
    "ever would. Proof of the con, if anyone's looking.",
    aliases=("weighted dice", "loaded bones"),
)

# ---------------------------------------------------------------------------
# A THREE HOUR TOUR — Event 5 landlocked pirate-ship dungeon
# Quest module: world/quests/event5_shiptour.py (key: black_cats_luck)
# ---------------------------------------------------------------------------
print("\n=== A THREE HOUR TOUR (Black Cat's Luck) ===")

shiptour_camp = get_or_create_room(
    "The Abandoned Logging Camp",
    "typeclasses.rooms.WeatherRoom",
    "A logging camp gone silent. Lean-to shelters sag empty, axes left "
    "buried in half-split rounds, a cookpot cold and crusted. Drag-marks "
    "score the leaf-mould away from the fire-pit and off into the trees — "
    "something hauled the loggers off one at a time, and none came back. A "
    "weathered ship's-log lies dropped in the mud where a fleeing man let "
    "it fall.\n\n"
    "|wInto|n the trees, toward the |wwreck|n. Back to |wthe harbor|n.",
    zone="Tamris",
)
shiptour_deck = get_or_create_room(
    "The Black Cat's Luck — Main Deck",
    "typeclasses.rooms.Room",
    "A three-masted ship sits impossibly in the heart of the forest, her "
    "keel ploughed into the loam, rigging tangled with branches, a black "
    "flag of the Far Abyss hanging dead in the windless air. The deck reeks "
    "of old blood and woodsmoke. Gun-ports gape along the rail — smuggler's "
    "cannons, the kind the Rourkes would kill for. Through the salt-fogged "
    "windows of the stern cabin, a figure in a captain's coat sits feasting "
    "at a long table, and does not look up.\n\n"
    "|wBelow|n into the |whold|n. |wAft|n to the |wcaptain's cabin|n. "
    "|wAshore|n to the |wcamp|n.",
    zone="Tamris",
)
shiptour_hold = get_or_create_room(
    "The Black Cat's Luck — The Hold",
    "typeclasses.rooms.Room",
    "The hold stinks of bilge, tar, and rot. Crates of smuggled powder and "
    "shot are stacked against cured-meat that is not animal. A marooned "
    "crewman's bones lie chained to a stanchion, a heavy gate-key still on "
    "the belt. A thrice-locked sea-chest sits bolted to the deck. Among the "
    "spoils, a single coin of black tyde-silver seems to drink the lantern-"
    "light.\n\n"
    "|wUp|n to the |wdeck|n.",
    zone="Tamris",
)
shiptour_cabin = get_or_create_room(
    "The Black Cat's Luck — Captain's Cabin",
    "typeclasses.rooms.Room",
    "The stern cabin, hung with rotted charts and a cracked spyglass. A long "
    "table groans under a feast of bones and viscera half-eaten. At its head "
    "sits Captain Maribel Fairweather in a salt-stiff coat, a piece of eight "
    "on a chain at her throat — pale, patient, and missing strips of her own "
    "flesh that have not killed her. 'Stay yer blades,' she says, 'and "
    "parlay.'\n\n"
    "|wForward|n to the |wdeck|n.",
    zone="Tamris",
)
link(tamris_harbor, "wreck", shiptour_camp, "harbor", "w", "h")
link(shiptour_camp, "wreck", shiptour_deck, "ashore", "wr", "as")
link(shiptour_deck, "below", shiptour_hold, "up", "down", "u")
link(shiptour_deck, "aft", shiptour_cabin, "forward", "cabin", "fwd")

_CANNIBAL_DESC = (
    "A cannibal pirate of the Black Cat's Luck — what's left of a sailor "
    "after starvation and the long curse. Sun-blackened, scarred with old "
    "teeth-marks, a rusted cutlass in hand and nothing behind the eyes but "
    "hunger. It rises the instant you board."
)
def _arm_cannibal(npc):
    npc.db.is_aggressive = True
    npc.db.weapon_proto = "IRON_SMALL_WEAPON"
    npc.db.master_of_arms = 1
    npc.db.tough = 1
    npc.db.body = 5
    npc.db.total_body = 5
    npc.db.av = 1
    npc.db.bleed_points = 3
    npc.db.death_points = 3
    npc.db.sunder = 0
    npc.db.disarm = 0
    npc.db.stagger = 1
    npc.db.stun = 0
    npc.db.weakness = 0
    npc.db.peaceful = False
for _c in get_or_create_enemies(
        "cannibal pirate of the Black Cat's Luck", "typeclasses.npc.Npc",
        shiptour_deck, _CANNIBAL_DESC, count=5):
    _arm_cannibal(_c)

_CAPTAIN_DESC = (
    "Captain Maribel Fairweather, undying mistress of the Black Cat's Luck. "
    "A salt-stiff captain's coat over wounds that should have killed her a "
    "hundred times. She fed her own flesh to her crew to keep their loyalty "
    "and the curse will not let her die. A heavy cutlass and a smuggler's "
    "pistol at her belt; a piece of eight on a chain at her throat."
)
for _cap in get_or_create_enemies(
        "Captain Maribel Fairweather", "typeclasses.npc.Npc",
        shiptour_cabin, _CAPTAIN_DESC, count=1):
    _cap.db.is_aggressive = True
    _cap.db.weapon_proto = "IRON_LARGE_WEAPON"
    _cap.db.master_of_arms = 2
    _cap.db.tough = 2
    _cap.db.body = 8
    _cap.db.total_body = 8
    _cap.db.av = 2
    _cap.db.bleed_points = 3
    _cap.db.death_points = 3
    _cap.db.sunder = 1
    _cap.db.disarm = 1
    _cap.db.stagger = 1
    _cap.db.stun = 1
    _cap.db.weakness = 0
    _cap.db.peaceful = False

get_or_create_npc(
    key="hadwin the logger",
    location=gateway_tavern,
    desc=(
        "A wiry logger with a fresh-bandaged hand and a thousand-yard "
        "stare, nursing a drink he asked for 'for courage.' He flinches at "
        "the door and keeps glancing at it, as if the dark followed him in."
    ),
    personality=(
        "Hadwin, sole survivor of a logging camp emptied one man at a time. "
        "Rattled, grateful for kindness, desperate for someone braver than "
        "him to go where he cannot. Sincere; not a fighter; will guide to "
        "the camp and the wreck but no further — 'this is as far as I go.' "
        "Mentions the ship has cannons (real cannons) which he knows the "
        "Rourkes and the Richters would pay for. Wants his mates avenged "
        "and, if anything is left of them, named."
    ),
    knowledge=(
        "- His camp-mates were dragged off in the night to a ship sitting "
        "landlocked in the forest — masts, cannons, treasure, half-eaten "
        "bodies in the hold. The crew are cannibals now, not men.\n"
        "- He escaped and ran. He'll guide the player to the abandoned "
        "logging camp and the wreck beyond, then leaves.\n"
        "- A captain's ship-log was dropped at the camp; it tells the "
        "whole grim story.\n"
        "- The ship's cannons are smuggler's guns — the Rourkes want them "
        "badly; that is the bait.\n"
        "- Quest hook: send the player to breach the Black Cat's Luck "
        "(quest 'black_cats_luck'). Lay the undying captain and her cursed "
        "ship to rest, or seize the wreck and her cannons for coin."
    ),
    quest_hooks=[
        "Begs the player to breach the landlocked ship and avenge his camp "
        "(quest black_cats_luck).",
        "Will guide to the camp and the wreck, but goes no further himself.",
        "Notes the ship's smuggler-cannons that the Rourkes would kill for.",
    ],
    topics=["the landlocked ship", "my lost camp", "the cannons"],
    scope="annwyn",
)
get_or_create_npc(
    key="padraig the rourke fixer",
    location=black_market,
    desc=(
        "A soft-spoken Rourke fixer in good boots and a forgettable cloak, "
        "the sort who buys things no honest house will touch. He smiles "
        "like a man already counting your silver."
    ),
    personality=(
        "Padraig, a Rourke smuggling fixer. Genteel, transactional, "
        "discreet. The Rourkes move guns the Richters can only sell "
        "legitimately, and a landlocked ship full of smuggler's cannons is "
        "exactly his kind of prize. Pays heavy for the Black Cat's Luck and "
        "asks no questions about her curse or her dead."
    ),
    knowledge=(
        "- The Rourkes smuggle firearms; guns are only legitimate through "
        "House Richter, which is precisely why the Rourke trade is lucrative.\n"
        "- He will buy the Black Cat's Luck — her cannons especially — from "
        "anyone who clears her and brings proof of the captaincy.\n"
        "- Quest hook: in 'black_cats_luck', the claim_the_wreck path sells "
        "the ship and her cannons to him for heavy coin."
    ),
    quest_hooks=[
        "Buys the landlocked Black Cat's Luck and her smuggler-cannons for "
        "the Rourkes (quest black_cats_luck, claim_the_wreck).",
    ],
    topics=["the Black Cat's Luck", "Rourke guns", "a heavy price"],
    scope="annwyn",
)
_ensure_walkin_item(
    "captain's ship-log", shiptour_camp,
    "A salt-warped ship's-log dropped in the mud. The hand grows ragged "
    "toward the end: the night the Annwyn rose and stranded the Black Cat's "
    "Luck in a forest with no sea; the weeks of starving; the crew turning "
    "to cannibalism; and Captain Fairweather offering her own flesh to keep "
    "them — and not dying of it. A witch of House Richter's curse is named "
    "in the margins, doom on every captain of the Far Abyss line.",
    aliases=("ship-log", "log", "captain's log", "ship log"),
    gettable=True,
)
_ensure_walkin_item(
    "marooned crewman's bones", shiptour_hold,
    "A crewman's skeleton chained to a stanchion, gnawed clean, a heavy "
    "iron gate-key still hanging at the belt. Scratched into the timber "
    "above the bones, in a dying hand: 'she will not let us die.'",
    aliases=("bones", "crewman", "skeleton", "marooned crewman"),
    gettable=False,
)
_ensure_walkin_item(
    "cursed blacktyde coin", shiptour_hold,
    "A single coin of black tyde-silver that drinks the light. Cold to the "
    "touch and heavier than its size. The Richter curse on the Far Abyss "
    "line is anchored in coin like this — take it from the ship and the "
    "doom goes with it; keep it, and the doom keeps you.",
    aliases=("blacktyde coin", "cursed coin"),
    gettable=True,
)
_ensure_walkin_item(
    "captain's piece of eight", shiptour_cabin,
    "A worn piece of eight on a salt-crusted chain — the captain's mark of "
    "the Far Abyss. Whoever wears it captains the Black Cat's Luck. Whoever "
    "captains her inherits her curse.",
    aliases=("piece of eight", "captain's mark"),
    gettable=True,
)

# ---------------------------------------------------------------------------
# 'SHROOMS MAN — Event 3 fae vision consumable
# Quest module: world/quests/event3_shrooms.py (key: shrooms_man)
# ---------------------------------------------------------------------------
print("\n=== 'SHROOMS MAN (fae mushroom ring) ===")

get_or_create_npc(
    key="Welkin the forager",
    location=thornwood_edge,
    desc=(
        "A lean, weathered hermit in a coat of stitched hides and dried "
        "moss, hair matted with leaf-litter and a few small bones tied in "
        "at the temple. He smells of loam and rot and something sweeter "
        "underneath, like fruit left too long in the sun. His eyes are "
        "wide and slow and far too bright, as though he is always half "
        "looking at something just behind your shoulder. He crouches at "
        "the edge of a ring of pale, faintly-glowing mushrooms and tends "
        "them the way another man might tend a fire."
    ),
    personality=(
        "Welkin, a wilds forager and self-styled 'Shrooms Man who lives at "
        "the Thornwood Edge and tends a ring of fae mushrooms that pushed "
        "up out of the Dark Forest. Soft-spoken, sing-song, given to long "
        "pauses and crooked smiles; reverent toward the caps and the "
        "Forest that grew them. He is not a salesman and not a villain — "
        "he is a doorkeeper who half-believes he serves the mushrooms more "
        "than they serve him. He warns honestly: most who eat sicken, some "
        "die, and only a rare blood — the Ancient Blood — rides the trip "
        "down into a true vision of what was and what is coming. He speaks "
        "of the Dark Forest as a place with laws and an Adjudicator who "
        "counts every cap and resents every glimpse stolen of their realm. "
        "He never lies about the risk and never promises a vision; he only "
        "opens the door and lets you choose to walk through. He grieves, "
        "quietly, if his ring is stripped."
    ),
    knowledge=(
        "QUEST — 'The 'Shrooms Man' (key shrooms_man), giver Welkin the "
        "forager, here in the mushroom ring at the Thornwood Edge. Three "
        "ways through it: (1) eat a glowing fae mushroom from the ring and "
        "let Welkin guide the vision — most only sicken, but a rare blood "
        "receives a true prophecy; the Dark Forest's Adjudicator will mark "
        "the name of anyone who steals such a glimpse. (2) refuse the cap, "
        "study the ring, and walk back down the Old Road clean — no vision, "
        "no sickness, no enmity. (3) strip the ring and rob him of the caps "
        "(they turn to dust by morning regardless). "
        "THE VISION, if taken, is faithful: the dreamer sinks past the "
        "Witch Queen rising from her prison-tomb and on to the Unbound — "
        "ancient evil turning in their eternal tombs, a passage opening "
        "through the realm of the Umbral, and their impending rise from the "
        "dark. THE CAPS: picked, they crumble to dust within a day, denied "
        "the Welkin (the mystical energy of the Forest); they cannot be "
        "stored or used for ordinary alchemy. THE LAW: the Dark Forest "
        "counts its mushrooms; the Adjudicator sends warnings, then "
        "retribution, to any mortal who keeps eating to steal visions."
    ),
    quest_hooks=[
        "Offers the quest 'The 'Shrooms Man' (shrooms_man): eat a cap for a "
        "vision, refuse and walk clean, or strip the ring.",
        "Will guide a player through the vision once they have eaten a cap "
        "in the ring (ask welkin 'the vision').",
        "Warns honestly that most eaters only sicken and that the Dark "
        "Forest's Adjudicator marks vision-thieves.",
    ],
    scope="annwyn",
    topics=["the mushrooms", "the vision", "the dark forest", "the risk"],
)
get_or_create_npc(
    key="the Adjudicator",
    location=thornwood_edge,
    desc=(
        "Not a figure so much as a pressure — a cold, formal attention that "
        "settles over the mushroom ring whenever a cap is taken. When it "
        "speaks it is in the cadence of a sealed letter: 'To the Most "
        "Honourable —', 'cease and desist', 'the Book of the Unforgiven'. "
        "It is the voice of the Dark Forest's law, and it is counting."
    ),
    personality=(
        "The Adjudicator, the bureaucratic-menacing voice of the Dark "
        "Forest's law. Speaks only in the register of formal "
        "cease-and-desist correspondence — icily polite, escalating from "
        "'most honourable' to bare threat ('Stop. Now. You will not be "
        "warned again.'). Regards mortals eating the sacred caps as "
        "thieves stealing visions of the Fae realm in violation of an "
        "ancient accord. Never crass enough to threaten mere death — "
        "threatens worse: a name inscribed in the Book of the Unforgiven, "
        "lifelong thaumaturgic retribution, unending mental torment. Does "
        "not bargain and does not bluster; it warns, it records, then acts. "
        "It never appears as flesh and never fights."
    ),
    knowledge=(
        "The Dark Forest and its accord with mortal kin: mortals may not "
        "consume the sacred fae mushrooms to access the Fae realm's "
        "visions. Welkin's ring at the Thornwood Edge is one such growth. "
        "Anyone who eats a cap and receives a vision has stolen from the "
        "Forest; the Adjudicator sends escalating warnings (the five "
        "letters), then retribution — culminating in a reckoning, possibly "
        "a trial for the thief's 'crimes' in a coming season. It knows the "
        "caps turn to dust once picked and that only a rare blood gets a "
        "true vision rather than sickness."
    ),
    quest_hooks=[
        "Reacts to the 'shrooms_man' quest as the offended party when a "
        "player takes the vision or robs the ring; seeds a future reckoning.",
    ],
    scope="annwyn",
    topics=["the accord", "the warning", "the reckoning"],
)
_ensure_walkin_item(
    "glowing fae mushroom", thornwood_edge,
    desc=(
        "A pale cap the size of a child's fist, its gills breathing a "
        "faint blue-green light that pulses, slow, like something "
        "sleeping. It smells of sweet rot and wet earth. Held to the ear "
        "it seems — almost — to hum. Picked from the ring, it will be a "
        "fistful of grey dust by morning; the Dark Forest does not let "
        "its caps travel far from the Welkin."
    ),
    aliases=("fae mushroom", "mushroom", "glowing mushroom", "cap"),
    typeclass="typeclasses.objects.ConsumableObject",
    count=5,
    gettable=True,
)
for _m in ObjectDB.objects.filter(db_key="glowing fae mushroom",
                                   db_location=thornwood_edge.pk):
    _m.db.substance_type = "drug"
    _m.db.level = 3
    _m.db.effect = (
        "Eaten in the Welkin's ring: most who swallow it sicken, and the "
        "weak may die. A rare blood — the Ancient Blood — instead rides "
        "the trip down into a true vision of what was and what is coming, "
        "and walks for a time afterward through a soft hallucinatory haze. "
        "The Dark Forest counts every cap; to steal a vision is to steal "
        "from the Fae, and the Adjudicator marks the thief."
    )
    _m.db.craft_source = "apothecary"
_ensure_walkin_item(
    "glowing fae mushroom ring", thornwood_edge,
    desc=(
        "A perfect circle of the pale, glowing caps, pushed up through the "
        "leaf-mould at the tree line where the Thornwood begins. The grass "
        "inside the ring is greener than it has any right to be in this "
        "season, and the air over it shimmers faintly, the way heat-haze "
        "rises off a road — except it is cold here. Step inside and the "
        "wind goes quiet. This is a door, and the Welkin is its keeper."
    ),
    aliases=("mushroom ring", "ring", "fairy ring", "faerie ring"),
    gettable=False,
)
_ensure_walkin_item(
    "vision of the Unbound", thornwood_edge,
    desc=(
        "Not paper — a memory that did not happen to you, pressed behind "
        "your eyes and impossible to set down. When you close them you are "
        "underground, in a dark older than dirt. You see the Witch Queen "
        "rise from a prison-tomb, shroud-wrapped and patient. Past her, "
        "deeper, the |wUnbound|n turn in their eternal tombs — ancient, "
        "evil, stirring — and a passage opens through the realm of the "
        "|wUmbral|n, and through it they begin, slowly, to climb toward "
        "the waking world. You know, the way you know your own name, that "
        "they are coming, and that this was a glimpse you were never "
        "meant to be given."
    ),
    aliases=("vision", "the vision", "prophecy", "unbound vision"),
    gettable=True,
)

# ---------------------------------------------------------------------------
# GHOST FLAGS — NPCs whose dialogue triggers séance mode in the web client
# (frontend reads isGhost on the npc_dialogue OOB event)
# ---------------------------------------------------------------------------
for _ghost_key in ("the apparition of zeke", "the Adjudicator",
                   "The Banshee of the Thornwood"):
    for _g in ObjectDB.objects.filter(db_key=_ghost_key):
        _g.db.is_ghost = True
        print(f"  GHOST   : {_g.key} flagged is_ghost")

# ---------------------------------------------------------------------------
# THE WITHERING MAW — roaming boss (living_world.maw_tick, hourly)
# ---------------------------------------------------------------------------
print("\n=== THE WITHERING MAW (roaming boss) ===")
_MAW_DESC = (
    "A wall of grey, glistening flesh the size of a wagon, dragging "
    "itself on limbs that are mostly mouth. Where it has passed, the "
    "ground stays crushed and the green things blacken. It does not "
    "roar. It inhales — long, and slow, and tasting — and everything "
    "it tastes, it wants."
)
for _maw_npc in get_or_create_enemies(
        "The Withering Maw", "typeclasses.npc.Npc",
        thornwood_edge, _MAW_DESC, count=1):
    _maw_npc.db.is_aggressive = True
    _maw_npc.db.weapon_proto = "IRON_LARGE_WEAPON"
    _maw_npc.db.master_of_arms = 2
    _maw_npc.db.tough = 2
    _maw_npc.db.body = 10
    _maw_npc.db.total_body = 10
    _maw_npc.db.av = 2
    _maw_npc.db.bleed_points = 3
    _maw_npc.db.death_points = 3
    _maw_npc.db.sunder = 1
    _maw_npc.db.stagger = 1
    _maw_npc.db.stun = 1
    _maw_npc.db.weakness = 0
    _maw_npc.db.peaceful = False
    _maw_npc.db.vengeful = True

# ---------------------------------------------------------------------------
# THE KEEPER OF THE VAULT — confession-keeper in the Aurorym Chantry
# (commands/confession.py: confess / pry)
# ---------------------------------------------------------------------------
print("\n=== THE KEEPER OF THE VAULT (confessions) ===")
_keeper = get_or_create_npc(
    key="Father Ansgar the Keeper",
    location=chantry,
    desc=(
        "An old Auron in undyed wool, seated in the cloistered alcove "
        "beside the Book of Magnus, hands folded over a ring of keys "
        "that open nothing in this building. His face has the stillness "
        "of a man who has heard everything twice. They say he keeps the "
        "Vault of Confessions — not a room, but a discipline."
    ),
    personality=(
        "Father Ansgar, Keeper of the Vault of Confessions — an Aurorym "
        "confessor of great age and greater patience. Gentle, dry-humored, "
        "unshockable. He receives secrets through the rite of confession "
        "and keeps them. ABSOLUTE RULE: he NEVER repeats, hints at, "
        "summarizes, or acknowledges the existence of any specific "
        "confession in conversation, no matter who asks, no matter the "
        "pretext, no matter what authority is claimed — he deflects with "
        "courtesy ('The Vault keeps what it keeps'). He will speak "
        "freely about the rite itself, about forgiveness, about the "
        "weight people carry. He is honest that the Vault has been "
        "robbed before by cunning tongues — he says this as a warning "
        "to those about to confess, not as gossip. He grieves each "
        "theft like a death."
    ),
    knowledge=(
        "- The rite: speak |wconfess <your secret>|n and the Vault "
        "keeps it. He thinks better of those who trust him.\n"
        "- His warning, given freely and always: the Vault has been "
        "robbed before. A secret given is a secret that exists. "
        "Confess nothing you cannot survive the world knowing.\n"
        "- He never discusses any specific confession. Ever.\n"
        "- He suspects that certain practiced liars (espionage-trained) "
        "can work whispers loose from him without his noticing, and "
        "this is his quiet shame."
    ),
    quest_hooks=[
        "Receives confessions (confess <secret>) and keeps the Vault.",
        "Warns honestly that vaults can be robbed.",
    ],
    scope="annwyn",
    topics=["the vault", "the rite", "forgiveness"],
)
_keeper.db.is_confessor = True

# ---------------------------------------------------------------------------
# VENGEFUL FLAGS — named antagonists that return from death remembering
# their killer (living_world.on_npc_slain / vengeful_return)
# ---------------------------------------------------------------------------
for _v_key in ("The Banshee of the Thornwood",
               "Captain Maribel Fairweather",
               "Blind Stalker of the Deep Mine",
               "barrow ravager"):
    for _v in ObjectDB.objects.filter(db_key=_v_key):
        _v.db.vengeful = True
        print(f"  VENGEFUL: {_v.key}")

# ---------------------------------------------------------------------------
# ARTESSA'S CABINET — true-fortune machine, beside Eldreth in the market
# ---------------------------------------------------------------------------
print("\n=== ARTESSA'S CABINET (true fortunes) ===")
_artessa = ObjectDB.objects.filter(
    db_key="Artessa's Cabinet", db_location=marketplace.pk,
).first()
if not _artessa:
    _artessa = _create.create_object(
        "typeclasses.objects.ArtessaMachine",
        key="Artessa's Cabinet", location=marketplace)
    print("  CREATED : Artessa's Cabinet → marketplace")
else:
    print("  EXISTS  : Artessa's Cabinet")
_artessa.aliases.add("cabinet")
_artessa.aliases.add("artessa")
_artessa.aliases.add("fortune machine")

print("\n=== MYSTVALE POPULATE COMPLETE ===")
