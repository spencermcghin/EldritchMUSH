"""
Prototypes

A prototype is a simple way to create individualized instances of a
given `Typeclass`. For example, you might have a Sword typeclass that
implements everything a Sword would need to do. The only difference
between different individual Swords would be their key, description
and some Attributes. The Prototype system allows to create a range of
such Swords with only minor variations. Prototypes can also inherit
and combine together to form entire hierarchies (such as giving all
Sabres and all Broadswords some common properties). Note that bigger
variations, such as custom commands or functionality belong in a
hierarchy of typeclasses instead.

Example prototypes are read by the `@spawn` command but is also easily
available to use from code via `evennia.spawn` or `evennia.utils.spawner`.
Each prototype should be a dictionary. Use the same name as the
variable to refer to other prototypes.

Possible keywords are:
    prototype_parent - string pointing to parent prototype of this structure.
    key - string, the main object identifier.
    typeclass - string, if not set, will use `settings.BASE_OBJECT_TYPECLASS`.
    location - this should be a valid object or #dbref.
    home - valid object or #dbref.
    destination - only valid for exits (object or dbref).

    permissions - string or list of permission strings.
    locks - a lock-string.
    aliases - string or list of strings.

    ndb_<name> - value of a nattribute (the "ndb_" part is ignored).
    any other keywords are interpreted as Attributes and their values.

See the `@spawn` command and `evennia.utils.spawner` for more info.

"""

# from random import randint
#
# GOBLIN = {
# "key": "goblin grunt",
# "health": lambda: randint(20,30),
# "resists": ["cold", "poison"],
# "attacks": ["fists"],
# "weaknesses": ["fire", "light"]
# }
#
# GOBLIN_WIZARD = {
# "prototype_parent": "GOBLIN",
# "key": "goblin wizard",
# "spells": ["fire ball", "lighting bolt"]
# }
#
# GOBLIN_ARCHER = {
# "prototype_parent": "GOBLIN",
# "key": "goblin archer",
# "attacks": ["short bow"]
# }
#
# This is an example of a prototype without a prototype
# (nor key) of its own, so it should normally only be
# used as a mix-in, as in the example of the goblin
# archwizard below.
# ARCHWIZARD_MIXIN = {
# "attacks": ["archwizard staff"],
# "spells": ["greater fire ball", "greater lighting"]
# }
#
# GOBLIN_ARCHWIZARD = {
# "key": "goblin archwizard",
# "prototype_parent" : ("GOBLIN_WIZARD", "ARCHWIZARD_MIXIN")
# }

"""
Begin blacksmith and weapon protoypes
Ensure material_value of weapon or armor is always 9th element in attrs.
"""

"""
Level 0 Blacksmith Items
"""

IRON_SMALL_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Small Weapon",
"aliases": ["iron small weapon"],
"craft_source": "blacksmith",
"required_resources": 2,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 0,
"cloth": 0,
"value_copper": 70,
"value_silver": 7,
"value_gold": .7,
"material_value": 1,
"required_skill": "melee_weapons",
"level": 0,
"damage": 1
}

IRON_MEDIUM_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Medium Weapon",
"aliases": ["iron medium weapon"],
"craft_source": "blacksmith",
"required_resources": 4,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"value_copper": 90,
"value_silver": 9,
"value_gold": .9,
"material_value": 1,
"required_skill": "melee_weapons",
"level": 0,
"damage": 1
}

IRON_LARGE_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Large Weapon",
"aliases": ["iron large weapon"],
"craft_source": "blacksmith",
"required_resources": 4,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"value_copper": 90,
"value_silver": 9,
"value_gold": .9,
"material_value": 1,
"required_skill": "melee_weapons",
"level": 0,
"twohanded": True,
"damage": 2
}

IRON_SHIELD = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Iron Shield",
"aliases": ["iron shield"],
"craft_source": "blacksmith",
"required_resources": 3,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"value_copper": 80,
"value_silver": 8,
"value_gold": .8,
"material_value": 1,
"required_skill": "shields",
"level": 0,
"is_shield": True
}

LEATHER_ARMOR = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Leather Armor",
"aliases": ["leather armor"],
"craft_source": "blacksmith",
"required_resources": 2,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"value_copper": 70,
"value_silver": 7,
"value_gold": .7,
"material_value": 1,
"required_skill": "armor_proficiency",
"level": 0,
"is_armor": True
}

IRON_CHAIN_SHIRT = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Chain Shirt",
"aliases": ["iron chain shirt"],
"craft_source": "blacksmith",
"required_resources": 2,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 0,
"cloth": 0,
"value_copper": 70,
"value_silver": 7,
"value_gold": .7,
"material_value": 1,
"required_skill": "armor_proficiency",
"level": 0,
"is_armor": True
}

IRON_COAT_OF_PLATES = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Coat of Plates",
"aliases": ["iron coat of plates"],
"craft_source": "blacksmith",
"required_resources": 5,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 2,
"cloth": 0,
"value_copper": 100,
"value_silver": 10,
"value_gold": 1,
"material_value": 3,
"required_skill": "armor_proficiency",
"level": 0,
"is_armor": True
}

IRON_PLATEMAIL = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Platemail",
"aliases": ["iron platemail"],
"craft_source": "blacksmith",
"required_resources": 7,
"iron_ingots": 4,
"refined_wood": 1,
"leather": 2,
"cloth": 0,
"value_copper": 120,
"value_silver": 12,
"value_gold": 1.2,
"material_value": 5,
"required_skill": "armor_proficiency",
"level": 0,
"is_armor": True
}

"""
Level 1 Blacksmith Items
"""

# Used with the patch command
PATCH_KIT = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Patch Kit",
"aliases": ["patch kit"],
"craft_source": "blacksmith",
"required_resources": 2,
"iron_ingots": 1,
"refined_wood": 0,
"leather": 0,
"cloth": 1,
"value_copper": 70,
"value_silver": 7,
"value_gold": .7,
"level": 1
}

HARDENED_IRON_SMALL_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Hardened Iron Small Weapon",
"aliases": ["hardened iron small weapon"],
"craft_source": "blacksmith",
"required_resources": 5,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 2,
"cloth": 0,
"value_copper": 130,
"value_silver": 13,
"value_gold": 1.3,
"material_value": 2,
"required_skill": "melee_weapons",
"level": 1,
"damage": 1
}

HARDENED_IRON_MEDIUM_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Hardened Iron Medium Weapon",
"aliases": ["hardened iron medium weapon"],
"craft_source": "blacksmith",
"required_resources": 9,
"iron_ingots": 5,
"refined_wood": 2,
"leather": 2,
"cloth": 0,
"value_copper": 170,
"value_silver": 17,
"value_gold": 1.7,
"material_value": 2,
"required_skill": "melee_weapons",
"level": 1,
"damage": 1
}

HARDENED_IRON_LARGE_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Hardened Iron Large Weapon",
"aliases": ["hardened iron large weapon"],
"craft_source": "blacksmith",
"required_resources": 4,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"value_copper": 90,
"value_silver": 9,
"value_gold": .9,
"material_value": 2,
"required_skill": "melee_weapons",
"level": 1,
"damage": 2,
"twohanded": True
}

HARDENED_IRON_SHIELD = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Hardened Iron Shield",
"aliases": ["hardened iron shield"],
"craft_source": "blacksmith",
"required_resources": 6,
"iron_ingots": 2,
"refined_wood": 2,
"leather": 2,
"cloth": 0,
"value_copper": 140,
"value_silver": 14,
"value_gold": 1.4,
"material_value": 2,
"required_skill": "shields",
"level": 1,
"is_shield": True
}

HARDENED_LEATHER_ARMOR = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Hardened Leather Armor",
"aliases": ["hardened leather armor"],
"craft_source": "blacksmith",
"required_resources": 6,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 4,
"cloth": 2,
"value_copper": 140,
"value_silver": 14,
"value_gold": 1.4,
"material_value": 2,
"required_skill": "armor_proficiency",
"level": 1,
"is_armor": True
}

HARDENED_IRON_CHAIN_SHIRT = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Hardened Iron Shield",
"aliases": ["hardened iron shield"],
"craft_source": "blacksmith",
"required_resources": 7,
"iron_ingots": 3,
"refined_wood": 2,
"leather": 2,
"cloth": 0,
"value_copper": 150,
"value_silver": 15,
"value_gold": 1.5,
"material_value": 2,
"required_skill": "armor_proficiency",
"level": 1,
"is_armor": True
}

HARDENED_IRON_COAT_OF_PLATES = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Hardened Iron Coat of Plates",
"aliases": ["hardened iron coat of plates"],
"craft_source": "blacksmith",
"required_resources": 12,
"iron_ingots": 6,
"refined_wood": 2,
"leather": 2,
"cloth": 2,
"value_copper": 200,
"value_silver": 20,
"value_gold": 2,
"material_value": 4,
"required_skill": "armor_proficiency",
"level": 1,
"is_armor": True
}

HARDENED_IRON_PLATEMAIL = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Hardened Iron Plate",
"aliases": ["hardened iron plate"],
"craft_source": "blacksmith",
"required_resources": 14,
"iron_ingots": 8,
"refined_wood": 2,
"leather": 2,
"cloth": 2,
"value_copper": 220,
"value_silver": 22,
"value_gold": 2.2,
"material_value": 6,
"required_skill": "armor_proficiency",
"level": 1,
"is_armor": True
}

"""
Level 2 Blacksmith Items
"""

STEEL_SMALL_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Steel Small Weapon",
"aliases": ["steel small weapon"],
"craft_source": "blacksmith",
"required_resources": 6,
"iron_ingots": 4,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"value_copper": 180,
"value_silver": 18,
"value_gold": 1.8,
"material_value": 3,
"required_skill": "melee_weapons",
"level": 2,
"damage": 1,
# Per Schematics CSV: "Gain +1 Stun per day."
"equip_bonus": {"stun": 1},
}

STEEL_MEDIUM_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Steel Medium Weapon",
"aliases": ["steel medium weapon"],
"craft_source": "blacksmith",
"required_resources": 11,
"iron_ingots": 6,
"refined_wood": 2,
"leather": 3,
"cloth": 0,
"value_copper": 230,
"value_silver": 23,
"value_gold": 2.3,
"material_value": 3,
"required_skill": "melee_weapons",
"level": 2,
"damage": 1,
# Per Schematics CSV: "Gain +1 Disarm per day."
"equip_bonus": {"disarm": 1},
}

STEEL_LARGE_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Steel Large Weapon",
"aliases": ["steel large weapon"],
"craft_source": "blacksmith",
"required_resources": 13,
"iron_ingots": 8,
"refined_wood": 2,
"leather": 3,
"cloth": 0,
"value_copper": 250,
"value_silver": 25,
"value_gold": 2.5,
"material_value": 3,
"required_skill": "melee_weapons",
"level": 2,
"damage": 2,
"twohanded": True,
# Per Schematics CSV: "Gain +1 Sunder per day."
"equip_bonus": {"sunder": 1},
}

STEEL_SHIELD = {
"typeclass": "typeclasses.objects.WeaponObject",
"is_shield": True,
"key": "Steel Shield",
"aliases": ["steel shield"],
"craft_source": "blacksmith",
"required_resources": 11,
"iron_ingots": 5,
"refined_wood": 3,
"leather": 3,
"cloth": 0,
"value_copper": 230,
"value_silver": 23,
"value_gold": 2.3,
"material_value": 3,
"required_skill": "shields",
"level": 2,
# Per Schematics CSV: "Grants +1 Stagger with a shield per day."
"equip_bonus": {"stagger": 1},
}

STEEL_CHAIN_SHIRT = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Steel Chain Shirt",
"aliases": ["steel chain shirt"],
"craft_source": "blacksmith",
"required_resources": 8,
"iron_ingots": 4,
"refined_wood": 2,
"leather": 2,
"cloth": 0,
"value_copper": 200,
"value_silver": 20,
"value_gold": 2,
"material_value": 4,
"required_skill": "armor_proficiency",
"level": 2,
"is_armor": True
}


STEEL_COAT_OF_PLATES = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Steel Coat of Plates",
"aliases": ["steel coat of plates"],
"craft_source": "blacksmith",
"required_resources": 14,
"iron_ingots": 8,
"refined_wood": 2,
"leather": 2,
"cloth": 2,
"value_copper": 260,
"value_silver": 26,
"value_gold": 2.6,
"material_value": 6,
"required_skill": "armor_proficiency",
"is_armor": True
}

STEEL_PLATEMAIL = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Steel Platemail",
"aliases": ["steel platemail"],
"craft_source": "blacksmith",
"required_resources": 17,
"iron_ingots": 8,
"refined_wood": 3,
"leather": 3,
"cloth": 3,
"value_copper": 290,
"value_silver": 29,
"value_gold": 2.9,
"material_value": 8,
"required_skill": "armor_proficiency",
"level": 2,
"is_armor": True
}

"""
Level 3 Blacksmith Items
"""

MASTERWORK_STEEL_SMALL_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Masterwork Steel Small Weapon",
"aliases": ["masterwork steel small weapon"],
"craft_source": "blacksmith",
"required_resources": 14,
"iron_ingots": 8,
"refined_wood": 2,
"leather": 4,
"cloth": 0,
"value_copper": 320,
"value_silver": 32,
"value_gold": 3.2,
"material_value": 4,
"required_skill": "melee_weapons",
"level": 3,
"damage": 2
}

MASTERWORK_STEEL_MEDIUM_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Masterwork Steel Medium Weapon",
"aliases": ["masterwork steel medium weapon"],
"craft_source": "blacksmith",
"required_resources": 21,
"iron_ingots": 11,
"refined_wood": 5,
"leather": 5,
"cloth": 0,
"value_copper": 390,
"value_silver": 39,
"value_gold": 3.9,
"material_value": 4,
"required_skill": "melee_weapons",
"level": 3,
"damage": 2
}

MASTERWORK_STEEL_LARGE_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Masterwork Steel Large Weapon",
"aliases": ["masterwork steel large weapon"],
"craft_source": "blacksmith",
"required_resources": 24,
"iron_ingots": 12,
"refined_wood": 6,
"leather": 6,
"cloth": 0,
"twohanded": True,
"value_copper": 420,
"value_silver": 42,
"value_gold": 4.2,
"level": 3,
"material_value": 4,
"required_skill": "melee_weapons",
"damage": 3,
"twohanded": True
}

MASTERWORK_STEEL_SHIELD = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Masterwork Steel Shield",
"aliases": ["masterwork steel shield"],
"craft_source": "blacksmith",
"required_resources": 17,
"iron_ingots": 9,
"refined_wood": 4,
"leather": 4,
"cloth": 0,
"value_copper": 350,
"value_silver": 35,
"value_gold": 3.8,
"material_value": 5,
"required_skill": "shields",
"level": 3,
"is_shield": True
}

MASTERWORK_STEEL_CHAIN_SHIRT = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Masterwork Steel Chain Shirt",
"aliases": ["masterwork steel chain shirt"],
"craft_source": "blacksmith",
"required_resources": 17,
"iron_ingots": 10,
"refined_wood": 0,
"leather": 4,
"cloth": 3,
"value_copper": 350,
"value_silver": 35,
"value_gold": 3.5,
"material_value": 8,
"required_skill": "armor_proficiency",
"level": 3,
"is_armor": True
}


MASTERWORK_STEEL_COAT_OF_PLATES = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Masterwork Steel Coat of Plates",
"aliases": ["masterwork steel coat of plates"],
"craft_source": "blacksmith",
"required_resources": 24,
"iron_ingots": 10,
"refined_wood": 2,
"leather": 8,
"cloth": 4,
"value_copper": 420,
"value_silver": 42,
"value_gold": 4.2,
"material_value": 10,
"required_skill": "armor_proficiency",
"level": 3,
"is_armor": True
}

MASTERWORK_STEEL_PLATEMAIL = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Masterwork Steel Platemail",
"aliases": ["masterwork steel platemail"],
"craft_source": "blacksmith",
"required_resources": 28,
"iron_ingots": 16,
"refined_wood": 2,
"leather": 6,
"cloth": 4,
"value_copper": 460,
"value_silver": 46,
"value_gold": 4.6,
"material_value": 12,
"required_skill": "armor_proficiency",
"level": 3,
"is_armor": True
}


"""
Begin artificer protoypes
"""

"""
Level 0 Artificer Items
"""

APOTHECARY_KIT = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Apothecary Kit",
"aliases": ["apothecary kit"],
"craft_source": "artificer",
"required_resources": 12,
"iron_ingots": 4,
"refined_wood": 4,
"leather": 0,
"cloth": 4,
"value_copper": 170,
"value_silver": 17,
"value_gold": 1.7,
"level": 0,
"type": "apothecary",
"kit_slot": True,
"uses": 10
}

ARTIFICER_KIT = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Artificer Kit",
"aliases": ["artificer kit"],
"craft_source": "artificer",
"required_resources": 12,
"iron_ingots": 4,
"refined_wood": 4,
"leather": 0,
"cloth": 4,
"value_copper": 170,
"value_silver": 17,
"value_gold": 1.7,
"level": 0,
"type": "artificer",
"kit_slot": True,
"uses": 10
}

BLACKSMITH_KIT = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Blacksmith Kit",
"aliases": ["blacksmith kit"],
"craft_source": "artificer",
"required_resources": 12,
"iron_ingots": 4,
"refined_wood": 4,
"leather": 4,
"cloth": 0,
"value_copper": 170,
"value_silver": 17,
"value_gold": 1.7,
"level": 0,
"type": "blacksmith",
"kit_slot": True,
"uses": 10
}

AURON_KIT = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Auron Kit",
"aliases": ["auron kit"],
"craft_source": "artificer",
"required_resources": 12,
"iron_ingots": 4,
"refined_wood": 2,
"leather": 2,
"cloth": 4,
"value_copper": 170,
"value_silver": 17,
"value_gold": 1.7,
"level": 0,
"type": "auron",
"kit_slot": True,
"uses": 10
}

BOWYER_KIT = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Bowyer Kit",
"aliases": ["bowyer kit"],
"craft_source": "artificer",
"required_resources": 12,
"iron_ingots": 0,
"refined_wood": 4,
"leather": 4,
"cloth": 4,
"value_copper": 170,
"value_silver": 17,
"value_gold": 1.7,
"level": 0,
"type": "bowyer",
"kit_slot": True,
"uses": 10
}

GUNSMITH_KIT = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Gunsmith Kit",
"aliases": ["gunsmith kit"],
"craft_source": "artificer",
"required_resources": 12,
"iron_ingots": 4,
"refined_wood": 4,
"leather": 4,
"cloth": 0,
"value_copper": 170,
"value_silver": 17,
"value_gold": 1.7,
"level": 0,
"type": "gunsmith",
"kit_slot": True,
"uses": 10
}

CHIRURGEON_KIT = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Chirurgeon Kit",
"aliases": ["chirurgeon kit"],
"craft_source": "artificer",
"required_resources": 12,
"iron_ingots": 4,
"refined_wood": 4,
"leather": 0,
"cloth": 4,
"value_copper": 170,
"value_silver": 17,
"value_gold": 1.7,
"level": 0,
"type": "chirurgeon",
"kit_slot": True,
"uses": 10
}

"""
Level 1 Artificer Items
"""

DUELIST_GLOVES = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Duelist Gloves",
"aliases": ["duelist gloves"],
"craft_source": "artificer",
"required_resources": 12,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 6,
"cloth": 6,
"value_copper": 200,
"value_silver": 20,
"value_gold": 2,
"level": 1,
"resist": 1,
"hand_slot": True
}

STALWART_BOOTS = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Stalwart Boots",
"aliases": ["stalwart boots"],
"craft_source": "artificer",
"required_resources": 12,
"iron_ingots": 3,
"refined_wood": 0,
"leather": 6,
"cloth": 3,
"value_copper": 200,
"value_silver": 20,
"value_gold": 2,
"level": 1,
"resist": 1,
"foot_slot": True
}

LIGHT_BOOTS = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Light Boots",
"aliases": ["light boots"],
"craft_source": "artificer",
"required_resources": 12,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 6,
"cloth": 6,
"value_copper": 200,
"value_silver": 20,
"value_gold": 2,
"level": 1,
"resist": 1,
"foot_slot": True
}

FINE_CLOTHING = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Fine Clothing",
"aliases": ["fine clothing"],
"craft_source": "artificer",
"required_resources": 10,
"iron_ingots": 3,
"refined_wood": 0,
"leather": 0,
"cloth": 7,
"value_copper": 180,
"value_silver": 18,
"value_gold": 1.8,
"level": 1,
"influential": 1,
"clothing_slot": True
}

HIGHWAYMAN_CLOAK = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Highwayman Cloak",
"aliases": ["highwayman cloak"],
"craft_source": "artificer",
"required_resources": 10,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 3,
"cloth": 7,
"value_copper": 180,
"value_silver": 18,
"value_gold": 1.8,
"level": 1,
"espionage": 1,
"cloak_slot": True
}

"""
Level 2 Artificer Items
"""

SHADOW_MANTLE = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Shadow Mantle",
"aliases": ["shadow mantle"],
"craft_source": "artificer",
"required_resources": 13,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 3,
"cloth": 10,
"value_copper": 250,
"value_silver": 25,
"value_gold": 2.5,
"level": 2,
"espionage": 4,
"cloak_slot": True
}

COURTIER_CLOTHING = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Courtier Clothing",
"aliases": ["courtier clothing"],
"craft_source": "artificer",
"required_resources": 13,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 3,
"cloth": 10,
"value_copper": 250,
"value_silver": 25,
"value_gold": 2.5,
"level": 2,
"influential": 2,
"clothing_slot": True
}

FINE_DUELIST_GLOVES = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Fine Duelist Gloves",
"aliases": ["fine duelist gloves"],
"craft_source": "artificer",
"required_resources": 16,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 8,
"cloth": 8,
"value_copper": 280,
"value_silver": 28,
"value_gold": 2.8,
"level": 2,
"resist": 2,
"hand_slot": True
}

SWORDDANCER_BOOTS = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Sworddancer Boots",
"aliases": ["sworddancer boots"],
"craft_source": "artificer",
"required_resources": 16,
"iron_ingots": 4,
"refined_wood": 0,
"leather": 8,
"cloth": 4,
"value_copper": 280,
"value_silver": 28,
"value_gold": 2.8,
"level": 2,
"resist": 2,
"foot_slot": True
}

HUNTER_BOOTS = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Hunter Boots",
"aliases": ["hunter boots"],
"craft_source": "artificer",
"required_resources": 16,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 8,
"cloth": 8,
"value_copper": 280,
"value_silver": 28,
"value_gold": 2.8,
"level": 2,
"resist": 2,
"foot_slot": True
}

"""
Level 3 Artificer Items
"""

MASTERWORK_APOTHECARY_KIT = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Masterwork Apothecary Kit",
"aliases": ["masterwork apothecary kit"],
"craft_source": "artificer",
"required_resources": 15,
"iron_ingots": 0,
"refined_wood": 5,
"leather": 5,
"cloth": 5,
"value_copper": 320,
"value_silver": 32,
"value_gold": 3.2,
"level": 3,
"type": "apothecary",
"kit_slot": True,
"uses": 10
}

MASTERWORK_ARTIFICER_KIT = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Masterwork Arifticer Kit",
"aliases": ["masterwork artificer kit"],
"craft_source": "artificer",
"required_resources": 15,
"iron_ingots": 0,
"refined_wood": 5,
"leather": 5,
"cloth": 5,
"value_copper": 320,
"value_silver": 32,
"value_gold": 3.2,
"level": 3,
"type": "artificer",
"kit_slot": True,
"uses": 10
}

MASTERWORK_BLACKSMITH_KIT = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Masterwork Blacksmith Kit",
"aliases": ["masterwork blacksmith kit"],
"craft_source": "artificer",
"required_resources": 12,
"iron_ingots": 4,
"refined_wood": 4,
"leather": 4,
"cloth": 0,
"value_copper": 290,
"value_silver": 29,
"value_gold": 2.9,
"level": 3,
"type": "blacksmith",
"kit_slot": True,
"uses": 10
}

MASTERWORK_BOWYER_KIT = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Masterwork Bowyer Kit",
"aliases": ["masterwork bowyer kit"],
"craft_source": "artificer",
"required_resources": 15,
"iron_ingots": 5,
"refined_wood": 5,
"leather": 5,
"cloth": 0,
"value_copper": 320,
"value_silver": 32,
"value_gold": 3.2,
"level": 3,
"type": "bowyer",
"kit_slot": True,
"uses": 10
}

MASTERWORK_GUNSMITH_KIT = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Masterwork Gunsmith Kit",
"aliases": ["masterwork gunsmith kit"],
"craft_source": "artificer",
"required_resources": 23,
"iron_ingots": 8,
"refined_wood": 5,
"leather": 5,
"cloth": 5,
"value_copper": 400,
"value_silver": 40,
"value_gold": 4,
"level": 3,
"type": "gunsmith",
"kit_slot": True,
"uses": 10
}

DARK_SILK_CLOAK = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Dark Silk Cloak",
"aliases": ["Dark Silk Cloak"],
"craft_source": "artificer",
"required_resources": 18,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 9,
"cloth": 9,
"value_copper": 350,
"value_silver": 35,
"value_gold": 3.5,
"level": 3,
"espionage": 6,
"cloak_slot": True
}

NOBLE_FINERY = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Noble Finery",
"aliases": ["noble finery"],
"craft_source": "artificer",
"required_resources": 18,
"iron_ingots": 2,
"refined_wood": 0,
"leather": 7,
"cloth": 9,
"value_copper": 350,
"value_silver": 35,
"value_gold": 3.5,
"level": 3,
"influential": 3,
"clothing_slot": True
}

MASTER_DUELIST_GLOVES = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Master Duelist Gloves",
"aliases": ["master duelist gloves"],
"craft_source": "artificer",
"required_resources": 23,
"iron_ingots": 3,
"refined_wood": 0,
"leather": 10,
"cloth": 10,
"value_copper": 400,
"value_silver": 40,
"value_gold": 4,
"level": 3,
"resist": 3,
"hand_slot": True
}

KNIGHT_BOOTS = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Knight Boots",
"aliases": ["knight boots"],
"craft_source": "artificer",
"required_resources": 23,
"iron_ingots": 3,
"refined_wood": 0,
"leather": 10,
"cloth": 10,
"value_copper": 400,
"value_silver": 40,
"value_gold": 4,
"level": 3,
"resist": 3,
"foot_slot": True
}

THIEF_BOOTS = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Thief Boots",
"aliases": ["thie boots"],
"craft_source": "artificer",
"required_resources": 23,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 10,
"cloth": 13,
"value_copper": 400,
"value_silver": 40,
"value_gold": 4,
"level": 3,
"resist": 3,
"foot_slot": True
}

"""
Bowyer Items
"""

ARROWS = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Arrows",
"aliases": ["arrows"],
"craft_source": "bowyer",
"required_resources": 3,
"iron_ingots": 1,
"refined_wood": 2,
"leather": 0,
"cloth": 0,
"value_copper": 80,
"value_silver": 8,
"value_gold": .8,
"level": 0,
"arrow_slot": True,
"quantity": 10
}


BOW = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Bow",
"aliases": ["bow"],
"craft_source": "bowyer",
"required_resources": 9,
"iron_ingots": 2,
"refined_wood": 6,
"leather": 1,
"cloth": 0,
"value_copper": 170,
"value_silver": 17,
"value_gold": 1.7,
"material_value": 2,
"required_skill": "archer",
"level": 1,
"is_bow": True,
"twohanded": True
}

MASTERWORK_BOW = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Masterwork Bow",
"aliases": ["masterwork bow"],
"craft_source": "bowyer",
"required_resources": 18,
"iron_ingots": 2,
"refined_wood": 12,
"leather": 4,
"cloth": 0,
"value_copper": 350,
"value_silver": 35,
"value_gold": 3.5,
"material_value": 3,
"required_skill": "archer",
"level": 3,
"is_bow": True,
"twohanded": True,
# Per Schematics CSV: "Gain +2 Tough per day. Gain +1 Resist per day."
"equip_bonus": {"tough": 2, "resist": 1},
}

"""
Gunsmith Items
"""

BULLETS = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Bullets",
"aliases": ["bullets"],
"craft_source": "gunsmith",
"required_resources": 9,
"iron_ingots": 6,
"refined_wood": 3,
"leather": 0,
"cloth": 0,
"value_copper": 170,
"value_silver": 17,
"value_gold": 1.7,
"level": 1,
"bullet_slot": True,
"quantity": 3
}


PISTOL = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Pistol",
"aliases": ["pistol"],
"craft_source": "gunsmith",
"required_resources": 18,
"iron_ingots": 10,
"refined_wood": 8,
"leather": 0,
"cloth": 0,
"value_copper": 300,
"value_silver": 30,
"value_gold": 3,
"material_value": 2,
"required_skill": "gunner",
"level": 2,
"is_pistol": True
}

MASTERWORK_PISTOL = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Masterwork Pistol",
"aliases": ["masterwork pistol"],
"craft_source": "gunsmith",
"required_resources": 23,
"iron_ingots": 10,
"refined_wood": 10,
"leather": 3,
"cloth": 0,
"value_copper": 400,
"value_silver": 40,
"value_gold": 4,
"material_value": 3,
"required_skill": "gunner",
"level": 3,
"is_pistol": True
}


"""
=====================================================================
  REAL ITEM PROTOTYPES — sourced from EldritchMUSH crafting spreadsheet
  Sections:
    1. Blacksmith (additional tiers: Steel, Masterwork Steel)
    2. Bowyer (Longbow)
    3. Gunsmith (Crude Pistol, Basic Pistol — corrected stats)
    4. Artificer (kits, clothing, boots, gloves, locks)
=====================================================================
"""

# =====================================================================
# BLACKSMITH — Tier 0 additions / corrections
# =====================================================================

LEATHER_ARMOR = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Leather Armor",
"aliases": ["leather armor"],
"craft_source": "blacksmith",
"required_resources": 2,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 1,
"cloth": 1,
"value_copper": 50,
"value_silver": 5,
"value_gold": 0.5,
"material_value": 1,
"required_skill": "armor_proficiency",
"level": 0,
"is_armor": True,
"armor_value": 1,
}

IRON_PLATEMAIL = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Iron Platemail",
"aliases": ["iron platemail", "iron plate mail"],
"craft_source": "blacksmith",
"required_resources": 9,
"iron_ingots": 6,
"refined_wood": 1,
"leather": 2,
"cloth": 0,
"value_copper": 120,
"value_silver": 12,
"value_gold": 1.2,
"material_value": 4,
"required_skill": "armor_proficiency",
"level": 0,
"is_armor": True,
"armor_value": 4,
}

# =====================================================================
# BLACKSMITH — Tier 1 additions
# =====================================================================

HARDENED_LEATHER_ARMOR = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Hardened Leather Armor",
"aliases": ["hardened leather armor"],
"craft_source": "blacksmith",
"required_resources": 6,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 4,
"cloth": 2,
"value_copper": 110,
"value_silver": 11,
"value_gold": 1.1,
"material_value": 2,
"required_skill": "armor_proficiency",
"level": 1,
"is_armor": True,
"armor_value": 2,
}

HARDENED_IRON_PLATE_ARMOR = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Hardened Iron Plate Armor",
"aliases": ["hardened iron plate armor", "hardened iron plate"],
"craft_source": "blacksmith",
"required_resources": 14,
"iron_ingots": 8,
"refined_wood": 2,
"leather": 2,
"cloth": 2,
"value_copper": 190,
"value_silver": 19,
"value_gold": 1.9,
"material_value": 6,
"required_skill": "armor_proficiency",
"level": 1,
"is_armor": True,
"armor_value": 6,
}

REVIVICATOR = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Revivicator",
"aliases": ["revivicator"],
"craft_source": "blacksmith",
"required_resources": 7,
"iron_ingots": 3,
"refined_wood": 2,
"leather": 1,
"cloth": 1,
"value_copper": 120,
"value_silver": 12,
"value_gold": 1.2,
"material_value": 1,
"required_skill": "blacksmith",
"level": 1,
"uses": 1,
}

# =====================================================================
# BLACKSMITH — Tier 2 (Steel)
# =====================================================================

STEEL_SHIELD = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Steel Shield",
"aliases": ["steel shield"],
"craft_source": "blacksmith",
"required_resources": 11,
"iron_ingots": 5,
"refined_wood": 3,
"leather": 3,
"cloth": 0,
"value_copper": 190,
"value_silver": 19,
"value_gold": 1.9,
"material_value": 3,
"required_skill": "shields",
"level": 2,
"is_shield": True,
}

IMPROVED_LEATHER_ARMOR = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Improved Leather Armor",
"aliases": ["improved leather armor"],
"craft_source": "blacksmith",
"required_resources": 8,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 5,
"cloth": 3,
"value_copper": 160,
"value_silver": 16,
"value_gold": 1.6,
"material_value": 4,
"required_skill": "armor_proficiency",
"level": 2,
"is_armor": True,
"armor_value": 4,
}

STEEL_CHAIN_SHIRT = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Steel Chain Shirt",
"aliases": ["steel chain shirt"],
"craft_source": "blacksmith",
"required_resources": 8,
"iron_ingots": 4,
"refined_wood": 2,
"leather": 2,
"cloth": 0,
"value_copper": 160,
"value_silver": 16,
"value_gold": 1.6,
"material_value": 4,
"required_skill": "armor_proficiency",
"level": 2,
"is_armor": True,
"armor_value": 4,
}

STEEL_COAT_OF_PLATES = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Steel Coat of Plates",
"aliases": ["steel coat of plates", "steel scalemail"],
"craft_source": "blacksmith",
"required_resources": 14,
"iron_ingots": 8,
"refined_wood": 2,
"leather": 2,
"cloth": 2,
"value_copper": 220,
"value_silver": 22,
"value_gold": 2.2,
"material_value": 6,
"required_skill": "armor_proficiency",
"level": 2,
"is_armor": True,
"armor_value": 6,
}

STEEL_PLATE_ARMOR = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Steel Plate Armor",
"aliases": ["steel plate armor", "steel platemail"],
"craft_source": "blacksmith",
"required_resources": 17,
"iron_ingots": 8,
"refined_wood": 3,
"leather": 3,
"cloth": 3,
"value_copper": 250,
"value_silver": 25,
"value_gold": 2.5,
"material_value": 8,
"required_skill": "armor_proficiency",
"level": 2,
"is_armor": True,
"armor_value": 8,
}

STEEL_SMALL_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Steel Small Weapon",
"aliases": ["steel small weapon"],
"craft_source": "blacksmith",
"required_resources": 6,
"iron_ingots": 4,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"value_copper": 140,
"value_silver": 14,
"value_gold": 1.4,
"material_value": 3,
"required_skill": "melee_weapons",
"level": 2,
"damage": 1,
}

STEEL_MEDIUM_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Steel Medium Weapon",
"aliases": ["steel medium weapon"],
"craft_source": "blacksmith",
"required_resources": 11,
"iron_ingots": 6,
"refined_wood": 2,
"leather": 3,
"cloth": 0,
"value_copper": 190,
"value_silver": 19,
"value_gold": 1.9,
"material_value": 3,
"required_skill": "melee_weapons",
"level": 2,
"damage": 1,
}

STEEL_LARGE_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Steel Large Weapon",
"aliases": ["steel large weapon"],
"craft_source": "blacksmith",
"required_resources": 13,
"iron_ingots": 8,
"refined_wood": 2,
"leather": 3,
"cloth": 0,
"value_copper": 210,
"value_silver": 21,
"value_gold": 2.1,
"material_value": 3,
"required_skill": "melee_weapons",
"level": 2,
"damage": 2,
"twohanded": True,
}

# =====================================================================
# BLACKSMITH — Tier 3 (Masterwork Steel)
# =====================================================================

MASTERWORK_STEEL_SHIELD = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Masterwork Steel Shield",
"aliases": ["masterwork steel shield"],
"craft_source": "blacksmith",
"required_resources": 14,
"iron_ingots": 7,
"refined_wood": 4,
"leather": 3,
"cloth": 0,
"value_copper": 260,
"value_silver": 26,
"value_gold": 2.6,
"material_value": 4,
"required_skill": "shields",
"level": 3,
"is_shield": True,
}

MASTERWORK_LEATHER_ARMOR = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Masterwork Leather Armor",
"aliases": ["masterwork leather armor"],
"craft_source": "blacksmith",
"required_resources": 11,
"iron_ingots": 1,
"refined_wood": 0,
"leather": 7,
"cloth": 3,
"value_copper": 230,
"value_silver": 23,
"value_gold": 2.3,
"material_value": 8,
"required_skill": "armor_proficiency",
"level": 3,
"is_armor": True,
"armor_value": 8,
}

MASTERWORK_STEEL_CHAIN_SHIRT = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Masterwork Steel Chain Shirt",
"aliases": ["masterwork steel chain shirt"],
"craft_source": "blacksmith",
"required_resources": 11,
"iron_ingots": 5,
"refined_wood": 0,
"leather": 3,
"cloth": 3,
"value_copper": 230,
"value_silver": 23,
"value_gold": 2.3,
"material_value": 8,
"required_skill": "armor_proficiency",
"level": 3,
"is_armor": True,
"armor_value": 8,
}

MASTERWORK_STEEL_COAT_OF_PLATES = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Masterwork Steel Coat of Plates",
"aliases": ["masterwork steel coat of plates", "masterwork steel scalemail"],
"craft_source": "blacksmith",
"required_resources": 17,
"iron_ingots": 5,
"refined_wood": 4,
"leather": 3,
"cloth": 5,
"value_copper": 290,
"value_silver": 29,
"value_gold": 2.9,
"material_value": 10,
"required_skill": "armor_proficiency",
"level": 3,
"is_armor": True,
"armor_value": 10,
}

MASTERWORK_STEEL_PLATE_MAIL = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Masterwork Steel Plate Mail",
"aliases": ["masterwork steel plate mail", "masterwork steel plate"],
"craft_source": "blacksmith",
"required_resources": 20,
"iron_ingots": 10,
"refined_wood": 3,
"leather": 4,
"cloth": 3,
"value_copper": 320,
"value_silver": 32,
"value_gold": 3.2,
"material_value": 12,
"required_skill": "armor_proficiency",
"level": 3,
"is_armor": True,
"armor_value": 12,
}

MASTERWORK_STEEL_SMALL_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Masterwork Steel Small Weapon",
"aliases": ["masterwork steel small weapon"],
"craft_source": "blacksmith",
"required_resources": 8,
"iron_ingots": 3,
"refined_wood": 2,
"leather": 3,
"cloth": 0,
"value_copper": 200,
"value_silver": 20,
"value_gold": 2.0,
"material_value": 4,
"required_skill": "melee_weapons",
"level": 3,
"damage": 1,
}

MASTERWORK_STEEL_MEDIUM_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Masterwork Steel Medium Weapon",
"aliases": ["masterwork steel medium weapon"],
"craft_source": "blacksmith",
"required_resources": 15,
"iron_ingots": 7,
"refined_wood": 4,
"leather": 4,
"cloth": 0,
"value_copper": 270,
"value_silver": 27,
"value_gold": 2.7,
"material_value": 4,
"required_skill": "melee_weapons",
"level": 3,
"damage": 1,
}

MASTERWORK_STEEL_LARGE_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Masterwork Steel Large Weapon",
"aliases": ["masterwork steel large weapon"],
"craft_source": "blacksmith",
"required_resources": 17,
"iron_ingots": 8,
"refined_wood": 5,
"leather": 4,
"cloth": 0,
"value_copper": 290,
"value_silver": 29,
"value_gold": 2.9,
"material_value": 4,
"required_skill": "melee_weapons",
"level": 3,
"damage": 2,
"twohanded": True,
}

# =====================================================================
# BOWYER — additional tiers
# =====================================================================

LONGBOW = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Longbow",
"aliases": ["longbow"],
"craft_source": "bowyer",
"required_resources": 9,
"iron_ingots": 0,
"refined_wood": 7,
"leather": 2,
"cloth": 0,
"value_copper": 170,
"value_silver": 17,
"value_gold": 1.7,
"material_value": 2,
"required_skill": "archer",
"level": 2,
"is_bow": True,
# Per Schematics CSV: "Gain +1 Tough per day."
"equip_bonus": {"tough": 1},
}

# =====================================================================
# GUNSMITH — corrected tier names
# =====================================================================

CRUDE_PISTOL = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Crude Pistol",
"aliases": ["crude pistol"],
"craft_source": "gunsmith",
"required_resources": 16,
"iron_ingots": 9,
"refined_wood": 7,
"leather": 0,
"cloth": 0,
"value_copper": 240,
"value_silver": 24,
"value_gold": 2.4,
"material_value": 1,
"required_skill": "gunner",
"level": 1,
"is_pistol": True,
}

BASIC_PISTOL = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Basic Pistol",
"aliases": ["basic pistol"],
"craft_source": "gunsmith",
"required_resources": 22,
"iron_ingots": 12,
"refined_wood": 10,
"leather": 0,
"cloth": 0,
"value_copper": 300,
"value_silver": 30,
"value_gold": 3.0,
"material_value": 2,
"required_skill": "gunner",
"level": 2,
"is_pistol": True,
}

# =====================================================================
# ARTIFICER — Kits (Tier I)
# =====================================================================

LOCKPICKING_KIT = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Lockpicking Kit",
"aliases": ["lockpicking kit"],
"craft_source": "artificer",
"required_resources": 5,
"iron_ingots": 3,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"value_copper": 100,
"value_silver": 10,
"value_gold": 1.0,
"material_value": 1,
"required_skill": "artificer",
"level": 1,
"uses": 10,
}

RESURRECTIONISTS_KIT = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Resurrectionist's Kit",
"aliases": ["resurrectionist's kit", "resurrectionist kit", "resurrectionists kit"],
"craft_source": "artificer",
"required_resources": 5,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 1,
"cloth": 2,
"value_copper": 100,
"value_silver": 10,
"value_gold": 1.0,
"material_value": 1,
"required_skill": "artificer",
"level": 1,
"uses": 10,
}

CRAFTSMANSHIP_TOOLS = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Craftsmanship Tools",
"aliases": ["craftsmanship tools"],
"craft_source": "artificer",
"required_resources": 10,
"iron_ingots": 4,
"refined_wood": 4,
"leather": 1,
"cloth": 1,
"value_copper": 150,
"value_silver": 15,
"value_gold": 1.5,
"material_value": 1,
"required_skill": "artificer",
"level": 1,
}

CLOTH_GAMBESON = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Cloth Gambeson",
"aliases": ["cloth gambeson", "gambeson"],
"craft_source": "artificer",
"required_resources": 3,
"iron_ingots": 0,
"refined_wood": 1,
"leather": 1,
"cloth": 2,
"value_copper": 80,
"value_silver": 8,
"value_gold": 0.8,
"material_value": 1,
"required_skill": "armor_proficiency",
"level": 1,
"is_armor": True,
"armor_value": 1,
}

# =====================================================================
# ARTIFICER — Clothing Tier I
# =====================================================================

PEASANTS_GARB = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Peasant's Garb",
"aliases": ["peasant's garb", "peasants garb", "peasant garb"],
"craft_source": "artificer",
"required_resources": 9,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 3,
"cloth": 6,
"value_copper": 140,
"value_silver": 14,
"value_gold": 1.4,
"material_value": 1,
"required_skill": "artificer",
"level": 1,
"clothing_type": "peasant",
}

NOBLES_GARB = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Noble's Garb",
"aliases": ["noble's garb", "nobles garb", "noble garb"],
"craft_source": "artificer",
"required_resources": 9,
"iron_ingots": 2,
"refined_wood": 0,
"leather": 2,
"cloth": 5,
"value_copper": 140,
"value_silver": 14,
"value_gold": 1.4,
"material_value": 1,
"required_skill": "artificer",
"level": 1,
"clothing_type": "noble",
}

# =====================================================================
# ARTIFICER — Locks
# =====================================================================

BASIC_LOCK = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Basic Lock",
"aliases": ["basic lock"],
"craft_source": "artificer",
"required_resources": 5,
"iron_ingots": 5,
"refined_wood": 0,
"leather": 0,
"cloth": 0,
"value_copper": 100,
"value_silver": 10,
"value_gold": 1.0,
"material_value": 1,
"required_skill": "artificer",
"level": 1,
"lock_level": 1,
}

QUALITY_LOCK = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Quality Lock",
"aliases": ["quality lock"],
"craft_source": "artificer",
"required_resources": 7,
"iron_ingots": 7,
"refined_wood": 0,
"leather": 0,
"cloth": 0,
"value_copper": 150,
"value_silver": 15,
"value_gold": 1.5,
"material_value": 2,
"required_skill": "artificer",
"level": 2,
"lock_level": 2,
}

MASTERWORK_LOCK = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Masterwork Lock",
"aliases": ["masterwork lock"],
"craft_source": "artificer",
"required_resources": 9,
"iron_ingots": 9,
"refined_wood": 0,
"leather": 0,
"cloth": 0,
"value_copper": 210,
"value_silver": 21,
"value_gold": 2.1,
"material_value": 3,
"required_skill": "artificer",
"level": 3,
"lock_level": 3,
}

# =====================================================================
# ARTIFICER — Clothing Tier II
# =====================================================================

PLAGUISTS_CASQUE = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Plaguist's Casque",
"aliases": ["plaguist's casque", "plaguists casque", "plague mask"],
"craft_source": "artificer",
"required_resources": 13,
"iron_ingots": 2,
"refined_wood": 0,
"leather": 5,
"cloth": 6,
"value_copper": 210,
"value_silver": 21,
"value_gold": 2.1,
"material_value": 2,
"required_skill": "artificer",
"level": 2,
}

MAGNIFICENT_CLOTHING = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Magnificent Clothing",
"aliases": ["magnificent clothing"],
"craft_source": "artificer",
"required_resources": 13,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 3,
"cloth": 10,
"value_copper": 210,
"value_silver": 21,
"value_gold": 2.1,
"material_value": 2,
"required_skill": "artificer",
"level": 2,
"clothing_type": "fine",
}

TRADESMENS_GARMENTS = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Tradesmen's Garments",
"aliases": ["tradesmen's garments", "tradesmens garments", "tradesman garments"],
"craft_source": "artificer",
"required_resources": 13,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 3,
"cloth": 10,
"value_copper": 210,
"value_silver": 21,
"value_gold": 2.1,
"material_value": 2,
"required_skill": "artificer",
"level": 2,
"clothing_type": "peasant",
}

LORDLY_CLOTHING = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Lordly Clothing",
"aliases": ["lordly clothing"],
"craft_source": "artificer",
"required_resources": 13,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 3,
"cloth": 10,
"value_copper": 210,
"value_silver": 21,
"value_gold": 2.1,
"material_value": 2,
"required_skill": "artificer",
"level": 2,
"clothing_type": "noble",
}

FINE_DUELISTS_GLOVES = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Fine Duelist's Gloves",
"aliases": ["fine duelist's gloves", "fine duelists gloves"],
"craft_source": "artificer",
"required_resources": 13,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 7,
"cloth": 6,
"value_copper": 210,
"value_silver": 21,
"value_gold": 2.1,
"material_value": 2,
"required_skill": "artificer",
"level": 2,
"resist": 2,
}

HUNTERS_BOOTS = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Hunter's Boots",
"aliases": ["hunter's boots", "hunters boots"],
"craft_source": "artificer",
"required_resources": 13,
"iron_ingots": 3,
"refined_wood": 0,
"leather": 7,
"cloth": 3,
"value_copper": 210,
"value_silver": 21,
"value_gold": 2.1,
"material_value": 2,
"required_skill": "artificer",
"level": 2,
"resist": 2,
}

SWORDDANCERS_BOOTS = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Sworddancer's Boots",
"aliases": ["sworddancer's boots", "sworddancers boots"],
"craft_source": "artificer",
"required_resources": 13,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 7,
"cloth": 6,
"value_copper": 210,
"value_silver": 21,
"value_gold": 2.1,
"material_value": 2,
"required_skill": "artificer",
"level": 2,
"resist": 2,
}

# =====================================================================
# ARTIFICER — Clothing Tier III
# =====================================================================

EXQUISITE_CLOTHING = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Exquisite Clothing",
"aliases": ["exquisite clothing"],
"craft_source": "artificer",
"required_resources": 17,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 8,
"cloth": 9,
"value_copper": 290,
"value_silver": 29,
"value_gold": 2.9,
"material_value": 3,
"required_skill": "artificer",
"level": 3,
"clothing_type": "fine",
}

PROFESSIONALS_VESTMENTS = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Professional's Vestments",
"aliases": ["professional's vestments", "professionals vestments"],
"craft_source": "artificer",
"required_resources": 17,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 8,
"cloth": 9,
"value_copper": 290,
"value_silver": 29,
"value_gold": 2.9,
"material_value": 3,
"required_skill": "artificer",
"level": 3,
"clothing_type": "peasant",
}

RAIMENT_OF_HIGH_LORD = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Raiment of the High Lord",
"aliases": ["raiment of the high lord", "raiment high lord", "high lord raiment"],
"craft_source": "artificer",
"required_resources": 17,
"iron_ingots": 2,
"refined_wood": 0,
"leather": 6,
"cloth": 9,
"value_copper": 290,
"value_silver": 29,
"value_gold": 2.9,
"material_value": 3,
"required_skill": "artificer",
"level": 3,
"clothing_type": "noble",
}

MASTER_DUELISTS_GLOVES = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Master Duelist's Gloves",
"aliases": ["master duelist's gloves", "master duelists gloves"],
"craft_source": "artificer",
"required_resources": 17,
"iron_ingots": 3,
"refined_wood": 0,
"leather": 8,
"cloth": 6,
"value_copper": 290,
"value_silver": 29,
"value_gold": 2.9,
"material_value": 3,
"required_skill": "artificer",
"level": 3,
"resist": 3,
}

KNIGHTS_BOOTS = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Knight's Boots",
"aliases": ["knight's boots", "knights boots"],
"craft_source": "artificer",
"required_resources": 17,
"iron_ingots": 3,
"refined_wood": 0,
"leather": 10,
"cloth": 4,
"value_copper": 290,
"value_silver": 29,
"value_gold": 2.9,
"material_value": 3,
"required_skill": "artificer",
"level": 3,
"resist": 3,
}

THIEFS_BOOTS = {
"typeclass": "typeclasses.objects.ArtificerObject",
"key": "Thief's Boots",
"aliases": ["thief's boots", "thiefs boots", "thief boots"],
"craft_source": "artificer",
"required_resources": 17,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 9,
"cloth": 8,
"value_copper": 290,
"value_silver": 29,
"value_gold": 2.9,
"material_value": 3,
"required_skill": "artificer",
"level": 3,
"resist": 3,
}


# =============================================================================
# QUEST ITEMS — lore props, evidence, letters. No crafting, no trade value.
# =============================================================================

SIGNED_OBAN_CONTRACT = {
    "typeclass": "typeclasses.objects.Object",
    "key": "signed Oban contract",
    "aliases": ["signed contract", "contract", "oban contract", "signed oban contract"],
    "desc": (
        "A folded sheet of cheap Oban parchment, creased from being "
        "carried close. On opening, the inner face bears a short "
        "contract of service in a hurried hand, signed at the foot "
        "with a bold '|wRoderick Wolf, commander of Lex Talionis|n' "
        "and the matching blot-seal of the mercenary company. "
        "A second, smaller seal beside it carries the black-and-gold "
        "chevron of |WHouse Oban|n. The numbers listed — gold dragons, "
        "three figures of them — are more than any honest season's "
        "work. Below the signatures, in a different hand: |540'on the "
        "night the north gate is opened, payment in full.'|n"
    ),
    "is_quest_item": True,
}

MORPHOS_LORE_SCROLL = {
    "typeclass": "typeclasses.objects.Object",
    "key": "lore of the Harbingers",
    "aliases": ["lore scroll", "harbingers", "morphos lore", "harbinger scroll"],
    "desc": (
        "A battered scroll tied with a length of black butterfly-silk. "
        "Within: a disjointed account of a figure called |yMorphos|n, "
        "said to move through the world 'swathed in darkness and a "
        "cloud of dark butterflies.' The writer — a frightened old "
        "soldier, by the cadence — names Morphos as a cultist of "
        "the |wHarbingers of Change|n, and admits under his own hand "
        "that such a creature paid him to open a gate that should "
        "never have been opened. He does not say where or for whom, "
        "only that he felt 'almost powerless to resist.'"
    ),
    "is_quest_item": True,
}

# Veteran's coin: drops alongside the contract on duel defeat — a small
# flavor prop Hamond wore on a thong around his neck. The Battle of
# Lanton is the canon event where he lost his unit holding the line for
# King Giles I. Players can `look` at it for backstory.
LANTON_VETERAN_COIN = {
    "typeclass": "typeclasses.objects.Object",
    "key": "veteran's coin of Lanton",
    "aliases": ["veteran's coin", "lanton coin", "veterans coin"],
    "desc": (
        "A plain iron coin, one face struck with the sun-and-stag of "
        "|WHouse Bannon|n, the other with the year |w747 A.S.|n and "
        "the word |430LANTON|n. Struck and handed out to the survivors "
        "of King Giles I's vanguard after the battle. The edge is "
        "worn smooth from being rubbed between a thumb and a "
        "forefinger for a long, long time."
    ),
    "is_quest_item": True,
}

# NPC giftable items — things AI NPCs can hand to players mid-dialogue.
# These are matched by the [GIVE: KEY] parser in world/npc_gifts.py.

WRIT_OF_SAFE_CONDUCT = {
    "typeclass": "typeclasses.objects.WritOfSafeConduct",
    "key": "Writ of Safe Conduct",
    "aliases": ["writ", "writ of safe conduct"],
    "is_quest_item": True,
}

SEALED_WRIT_COPY = {
    "typeclass": "typeclasses.objects.Object",
    "key": "sealed writ copy",
    "aliases": ["writ copy", "sealed writ", "writ"],
    "desc": (
        "A folded parchment bearing the official seal of the Mystvale "
        "Town Hall — three stamps of wax in red, blue, and yellow. "
        "The text inside is a certified copy of some civil record, "
        "intended for delivery to Stag Hall."
    ),
    "is_quest_item": True,
}

DELIVERY_RECEIPT = {
    "typeclass": "typeclasses.objects.Object",
    "key": "delivery receipt",
    "aliases": ["receipt"],
    "desc": (
        "A narrow strip of parchment with a line for a signet "
        "impression and a brief description of the document it "
        "accompanied. Return this to the clerk who issued it once "
        "the delivery has been acknowledged."
    ),
    "is_quest_item": True,
}

ALE_TOKEN = {
    "typeclass": "typeclasses.objects.Object",
    "key": "ale token",
    "aliases": ["token", "drink token"],
    "desc": (
        "A small wooden disc stamped with the Broken Oar's mark — "
        "a snapped oar over a mug. Good for one ale, no questions "
        "asked. Pelham Faye hands these out to folk he likes."
    ),
    "is_quest_item": False,
}

TOWN_REGISTER_NOTE = {
    "typeclass": "typeclasses.objects.Object",
    "key": "note on the town register",
    "aliases": ["register note", "town register note"],
    "desc": (
        "A hastily scrawled note in Clerk Yevan's cramped hand: "
        "'The Richter emissary asked for the full town register. "
        "Why? Lord Hardinger denied it — but someone was seen "
        "copying pages from the archive after hours. I cannot "
        "prove it yet. Discretion is required.'"
    ),
    "is_quest_item": True,
}

# --- Rescue the Crafters quest chain items ---

CROW_CAMP_LETTER = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Crow camp letter",
    "aliases": ["crow letter", "letter", "camp letter"],
    "desc": (
        "A crumpled letter in Aldrith script, found at the Crow camp. "
        "It mentions two other camps — Fox Den and Owl's Roost — where "
        "more captives are being held. The handwriting is hurried and angry."
    ),
    "is_quest_item": True,
}

CROW_INTELLIGENCE_REPORT = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Crow intelligence report",
    "aliases": ["crow report", "intelligence report", "crow intel"],
    "desc": (
        "A bundle of notes found on Cale the Thorn — patrol routes, "
        "supply cache locations, and a terse set of orders from someone "
        "signing as 'the Old Badger.' The Crows are more organized than "
        "anyone in Mystvale suspected."
    ),
    "is_quest_item": True,
}

ALCHEMY_RECIPE_SCROLL = {
    "typeclass": "typeclasses.objects.Object",
    "key": "alchemy recipe scroll",
    "aliases": ["recipe scroll", "alchemy scroll"],
    "desc": (
        "A stained scroll of herbal recipes recovered from the Crow camp. "
        "Marta the Alchemist had been working on these before her capture "
        "— they describe preparations for healing salves and blade oils."
    ),
    "is_quest_item": True,
}
