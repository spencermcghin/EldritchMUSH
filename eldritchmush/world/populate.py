"""
world/populate.py — World builder for EldritchMUSH.

Run once from inside eldritchmush/:
    evennia shell -c "exec(open('world/populate.py').read())"

Safe to re-run: skips objects that already exist by key+typeclass.
"""
import evennia
from evennia.objects.models import ObjectDB
from evennia.accounts.models import AccountDB


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_or_create_room(key, typeclass_path, desc):
    existing = ObjectDB.objects.filter(
        db_key=key, db_typeclass_path=typeclass_path
    ).first()
    if existing:
        print(f"  EXISTS  : {key}")
        return existing
    room = evennia.create_object(typeclass_path, key=key)
    room.db.desc = desc
    room.save()
    print(f"  CREATED : {key}")
    return room


def link(room_a, exit_a, room_b, exit_b, alias_a=None, alias_b=None):
    """Create two exits between rooms, skipping if already present."""
    def _make(name, loc, dest, alias):
        if not ObjectDB.objects.filter(db_key=name, db_location=loc.pk).exists():
            ex = evennia.create_object(
                "evennia.objects.objects.DefaultExit",
                key=name, location=loc, destination=dest
            )
            if alias:
                ex.aliases.add(alias)
    _make(exit_a, room_a, room_b, alias_a)
    _make(exit_b, room_b, room_a, alias_b)


def create_npc(key, typeclass_path, location, desc, aggressive=True):
    npc = evennia.create_object(typeclass_path, key=key, location=location)
    npc.db.desc = desc
    npc.db.is_aggressive = aggressive
    npc.save()
    print(f"  NPC     : {key} → {location.key}")
    return npc


def create_obj(key, typeclass_path, location, desc):
    obj = evennia.create_object(typeclass_path, key=key, location=location)
    obj.db.desc = desc
    obj.save()
    print(f"  OBJECT  : {key} → {location.key}")
    return obj


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------
print("\n=== ROOMS ===")

tavern = get_or_create_room(
    "Songbird's Rest",
    "typeclasses.rooms.Room",
    "Songbird's Rest is a low-ceilinged hall smelling of tallow smoke, stale ale, "
    "and old blood. Rough-hewn tables bear the scars of a hundred brawls. A great "
    "hearth crackles in the west wall, casting iron-red shadows across faces better "
    "left unlit. The barkeep watches everything and says nothing.\n\n"
    "To the |wnorth|n lies the old road. The |wkitchen|n is east. The |woffice|n is up the back stairs."
)

kitchen = get_or_create_room(
    "Tavern Kitchen",
    "typeclasses.rooms.Room",
    "A hot, cramped kitchen thick with the smell of boiling bone-broth and burnt fat. "
    "Copper pots hang from low beams. A rat vanishes behind the flour barrel. "
    "This is not a place for guests."
)

office = get_or_create_room(
    "Tavern Office",
    "typeclasses.rooms.Room",
    "A cluttered back office. Ledgers stacked to the ceiling, a locked iron strongbox "
    "bolted to the floor. Someone has scratched a warning into the desk in a language "
    "you don't recognise."
)

crossroads = get_or_create_room(
    "Old Road — Crossroads",
    "typeclasses.rooms.WeatherRoom",
    "A muddy crossroads where four paths meet beneath a leaning signpost. The signs have "
    "been defaced. Crows watch from the deadwood.\n\n"
    "|wNorth|n: the marketplace. |wSouth|n: back to the tavern. "
    "|wEast|n: toward the docks. |wWest|n: the maker's hollow. "
    "|wNortheast|n: the north fields."
)

docks = get_or_create_room(
    "The Docks",
    "typeclasses.rooms.Room",
    "Rotting piers extend over black water that reflects nothing. Mooring ropes hang "
    "slack — whatever boats were here are gone. The smell is fish, brine, and something "
    "worse underneath. Fog rolls in from the river."
)

makers_hollow = get_or_create_room(
    "Maker's Hollow",
    "typeclasses.rooms.MarketRoom",
    "A vaulted stone workshop hollowed from the hill. Forge light paints the walls amber. "
    "The smell of hot iron and pine resin fills the air. A |wforge|n, |wworkbench|n, and "
    "|wapothecary workbench|n crowd the space. Craftworkers come here when they need privacy."
)

marketplace = get_or_create_room(
    "The Marketplace",
    "typeclasses.rooms.MarketRoom",
    "A cobbled square ringed by low stalls. Merchants hawk under oiled-canvas awnings. "
    "The goods are practical and the prices are not: tools, provisions, weapons — things "
    "that keep you alive one more day. A |wGeneral Merchant|n holds court near the dry fountain."
)

north_field = get_or_create_room(
    "North Field",
    "typeclasses.rooms.WeatherRoom",
    "A wide field of withered crops. Whatever was planted here rotted in the ground. "
    "The earth is soft and dark, and at night shapes move that are not animals. Stay alert."
)

south_field = get_or_create_room(
    "South Field",
    "typeclasses.rooms.WeatherRoom",
    "Knee-high dead grass stretches to a tree line of bare oaks. Old farmsteads visible "
    "in the distance, all dark. The road back to the tavern lies |wnorth|n."
)

east_cabin = get_or_create_room(
    "Eastern Cabin",
    "typeclasses.rooms.Room",
    "A low hunting cabin, roof half-caved. A rusted iron stove sits cold in the corner. "
    "Dried herbs still hang from the rafters — whoever lived here left in a hurry. "
    "The door hangs open."
)

west_cabin = get_or_create_room(
    "Western Cabin",
    "typeclasses.rooms.Room",
    "A sturdier cabin than most, with iron-banded shutters and a heavy lock — kicked in. "
    "Inside: an overturned cot, scattered coin, dried blood on the floorboards. "
    "Someone lost a fight here."
)

graveyard = get_or_create_room(
    "Raven's Rest Graveyard",
    "typeclasses.rooms.WeatherRoom",
    "Crooked headstones lean at wrong angles in the black earth. Names worn away by rain. "
    "Fresh mounds interrupt the older graves — some of the mounds are moving. "
    "The graveyard is never fully quiet."
)

chargen_room = get_or_create_room(
    "The Threshold",
    "typeclasses.rooms.ChargenRoom",
    "A dim stone antechamber with a single mirrored pool. Your reflection stares back, "
    "waiting. This is where you decide who you are.\n\n"
    "|yUse the |wset|y commands to choose your skills.|n Type |wdone|n when you are ready."
)

# ---------------------------------------------------------------------------
# Exits
# ---------------------------------------------------------------------------
print("\n=== EXITS ===")

# Tavern hub
link(tavern,    "north",   crossroads,    "south",   "n", "s")
link(tavern,    "east",    kitchen,       "west",    "e", "w")
link(tavern,    "up",      office,        "down",    "u", "d")
link(tavern,    "south",   south_field,   "north",   "s", "n")

# Crossroads spokes
link(crossroads, "east",      docks,        "west",    "e", "w")
link(crossroads, "west",      makers_hollow,"east",    "w", "e")
link(crossroads, "north",     marketplace,  "south",   "n", "s")
link(crossroads, "northeast", north_field,  "southwest","ne","sw")

# Fields & cabins
link(north_field, "east",  east_cabin,  "west",  "e", "w")
link(north_field, "west",  west_cabin,  "east",  "w", "e")
link(north_field, "north", graveyard,   "south", "n", "s")

# Limbo → Tavern (so new characters arrive in-world)
limbo = ObjectDB.objects.filter(id=2).first()
if limbo:
    limbo.db.desc = (
        "A featureless void between worlds. Songbird's Rest lies |wsouth|n."
    )
    if not ObjectDB.objects.filter(db_key="south", db_location=limbo.pk).exists():
        evennia.create_object(
            "evennia.objects.objects.DefaultExit",
            key="south", location=limbo, destination=tavern
        )
        print("  CREATED : Limbo → Tavern exit")

# ---------------------------------------------------------------------------
# Move existing characters to the Tavern
# ---------------------------------------------------------------------------
print("\n=== RELOCATING CHARACTERS ===")
for acct in AccountDB.objects.all():
    try:
        char = acct.db._last_puppet
        if char and hasattr(char, 'location'):
            char.db.prelogout_location = tavern
            char.location = tavern
            char.save()
            print(f"  MOVED   : {char.key} → Tavern")
    except Exception as e:
        print(f"  SKIP    : {acct.username} ({e})")

# ---------------------------------------------------------------------------
# Crafting stations in Maker's Hollow
# ---------------------------------------------------------------------------
print("\n=== CRAFTING STATIONS ===")

if not ObjectDB.objects.filter(db_key="forge", db_location=makers_hollow.pk).exists():
    forge = create_obj(
        "forge", "typeclasses.objects.Forge", makers_hollow,
        "A squat stone forge, iron-mouthed and hungry. Coals glow deep inside. "
        "Strike the anvil to shape metal into weapons and armour."
    )

if not ObjectDB.objects.filter(db_key="workbench", db_location=makers_hollow.pk).exists():
    bench = create_obj(
        "workbench", "typeclasses.objects.ArtificerWorkbench", makers_hollow,
        "A heavy oak workbench scarred by blades. Drawers hold small tools. "
        "A craftworker's table for bows, gunsmith work, and fine artifice."
    )

if not ObjectDB.objects.filter(db_key="apothecary workbench", db_location=makers_hollow.pk).exists():
    apoth = create_obj(
        "apothecary workbench", "typeclasses.objects.ApothecaryWorkbench", makers_hollow,
        "A stone-topped table stained every colour by spilled reagents. "
        "Glass tubes, a mortar and pestle, drying racks. Brew here."
    )

# ---------------------------------------------------------------------------
# Merchant in Marketplace
# ---------------------------------------------------------------------------
print("\n=== MERCHANTS ===")

if not ObjectDB.objects.filter(db_key="General Merchant", db_location=marketplace.pk).exists():
    merchant = evennia.create_object(
        "typeclasses.objects.Merchant",
        key="General Merchant", location=marketplace
    )
    merchant.db.desc = (
        "A heavyset merchant in a waxed canvas coat. Their eyes track every "
        "coin in the square. They sell practical goods at impractical prices."
    )
    merchant.db.shop_inventory = [
        "IRON_SMALL_WEAPON",
        "IRON_MEDIUM_WEAPON",
        "LEATHER_LIGHT_ARMOR",
        "IRON_LIGHT_ARMOR",
        "IRON_MEDIUM_ARMOR",
        "HUNTING_BOW",
        "ARROWS",
        "IRON_SMALL_SHIELD",
        "IRON_MEDIUM_SHIELD",
        "MEDICINE_KIT",
        "CHIRURGEONS_KIT",
    ]
    merchant.save()
    print(f"  CREATED : General Merchant → Marketplace")

# ---------------------------------------------------------------------------
# NPCs
# ---------------------------------------------------------------------------
print("\n=== NPCS ===")

# Graveyard zombies (3)
existing_graveyard_npcs = ObjectDB.objects.filter(
    db_key="zombie", db_location=graveyard.pk
).count()
for i in range(3 - existing_graveyard_npcs):
    create_npc(
        "zombie",
        "typeclasses.npc.GreenMeleeSoldierOneHanded",
        graveyard,
        "A shambling corpse in rotting burial clothes. Its jaw hangs loose. "
        "Dead eyes track movement with unsettling focus.",
        aggressive=True
    )

# North Field zombies (2)
existing_field_npcs = ObjectDB.objects.filter(
    db_key="field zombie", db_location=north_field.pk
).count()
for i in range(2 - existing_field_npcs):
    create_npc(
        "field zombie",
        "typeclasses.npc.GreenMeleeSoldierOneHanded",
        north_field,
        "A grave-risen thing half-sunk in the mud. It smells of turned earth "
        "and old meat. Slow, but it doesn't stop.",
        aggressive=True
    )

# Revenant in the graveyard (1, tougher)
if not ObjectDB.objects.filter(db_key="revenant", db_location=graveyard.pk).exists():
    create_npc(
        "revenant",
        "typeclasses.npc.GreenRevenant",
        graveyard,
        "A tall figure in the rags of fine burial clothes. Unlike the shambling "
        "dead, this one moves with purpose. Its eyes burn with pale cold fire.",
        aggressive=True
    )

# Bandit in the Western Cabin (1)
if not ObjectDB.objects.filter(db_key="bandit", db_location=west_cabin.pk).exists():
    create_npc(
        "bandit",
        "typeclasses.npc.BanditMeleeOneHanded",
        west_cabin,
        "A scarred figure in patchwork leathers. They eye you from the corner "
        "with the practiced calm of someone who has done this before.",
        aggressive=True
    )

# ---------------------------------------------------------------------------
# Quest giver NPCs — non-combatant
# ---------------------------------------------------------------------------

def create_quest_giver(key, location, desc):
    tp = "typeclasses.npc.QuestGiverNpc"
    if not ObjectDB.objects.filter(db_key=key, db_typeclass_path=tp).exists():
        npc = create_object(tp, key=key, location=location)
        npc.db.desc = desc
        npc.db.is_aggressive = False
        npc.db.is_npc = True
        print(f"  + quest giver: {key}")
    else:
        print(f"  (quest giver {key!r} already exists)")


# Elara — innkeeper in the Tavern Main Hall
create_quest_giver(
    "elara",
    tavern,
    "The innkeeper of Songbird's Rest. Dark circles under her eyes and hands "
    "that won't stay still. Something is wrong and she clearly needs help.",
)

# Grimwald — blacksmith in Maker's Hollow
try:
    makers_hollow = ObjectDB.objects.filter(db_key="maker's hollow").first() or tavern
except Exception:
    makers_hollow = tavern
create_quest_giver(
    "grimwald",
    makers_hollow,
    "A broad, soot-stained blacksmith with a wrestler's build. He speaks in short "
    "sentences and watches the door when he talks, as if expecting trouble.",
)

# Mira — apothecary in the Marketplace
try:
    marketplace_room = ObjectDB.objects.filter(db_key="the marketplace").first() or tavern
except Exception:
    marketplace_room = tavern
create_quest_giver(
    "mira",
    marketplace_room,
    "A wiry woman surrounded by jars and bundled herbs. She moves with quick "
    "efficiency and smells faintly of lavender and something sharper.",
)

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
print("\n=== POPULATE COMPLETE ===")
print(f"Rooms    : {ObjectDB.objects.filter(db_typeclass_path__contains='rooms').count()}")
print(f"NPCs     : {ObjectDB.objects.filter(db_typeclass_path__contains='npc').count()}")
print(f"Objects  : {ObjectDB.objects.filter(db_typeclass_path__contains='objects').count()}")
