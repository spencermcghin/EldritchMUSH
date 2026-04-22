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

# ===========================================================================
# RECIPE SCROLL PROTOTYPES -- generated from alchemy_prototypes.py
# Players learn these via: learn <scroll>
# Sold by Marta the Alchemist and other recipe vendors.
# ===========================================================================

RECIPE_ANAMNESIS_DECOCTION = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Anamnesis Decoction",
    "aliases": ['anamnesis decoction recipe', 'anamnesis decoction schematic'],
    "desc": "A detailed schematic describing how to brew Anamnesis Decoction (Level 1 Apotheca). Requires: Distilled Spirits x2, Harrowdust x1, Sayge x1, Widow's Petal x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "ANAMNESIS_DECOCTION",
    "value_silver": 8,
}

RECIPE_BLADE_OIL = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Blade Oil",
    "aliases": ['blade oil recipe', 'blade oil schematic'],
    "desc": "A detailed schematic describing how to brew Blade Oil (Level 1 Apotheca). Requires: Distilled Spirits x1, Dragon's Eye x4. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "BLADE_OIL",
    "value_silver": 8,
}

RECIPE_BLADE_SALVE = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Blade Salve",
    "aliases": ['blade salve recipe', 'blade salve schematic'],
    "desc": "A detailed schematic describing how to brew Blade Salve (Level 1 Apotheca). Requires: Distilled Spirits x2, Sayge x1, Verbaena x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "BLADE_SALVE",
    "value_silver": 8,
}

RECIPE_BULLS_DECOCTION = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Bull's Decoction",
    "aliases": ["bull's decoction recipe", "bull's decoction schematic"],
    "desc": "A detailed schematic describing how to brew Bull's Decoction (Level 1 Apotheca). Requires: Distilled Spirits x1, Dragon's Eye x2, Gold Lotus x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "BULLS_DECOCTION",
    "value_silver": 8,
}

RECIPE_CATS_EYES = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Cat's Eyes",
    "aliases": ["cat's eyes recipe", "cat's eyes schematic"],
    "desc": "A detailed schematic describing how to brew Cat's Eyes (Level 1 Apotheca). Requires: Distilled Spirits x1, Gold Lotus x3, Orgonnian Grapes x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "CATS_EYES",
    "value_silver": 8,
}

RECIPE_CATS_PAW = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Cat's Paw",
    "aliases": ["cat's paw recipe", "cat's paw schematic"],
    "desc": "A detailed schematic describing how to brew Cat's Paw (Level 1 Apotheca). Requires: Distilled Spirits x2, Phosphorous x2, Verbaena x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "CATS_PAW",
    "value_silver": 8,
}

RECIPE_CUBS_DECOCTION = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Cub's Decoction",
    "aliases": ["cub's decoction recipe", "cub's decoction schematic"],
    "desc": "A detailed schematic describing how to brew Cub's Decoction (Level 1 Apotheca). Requires: Distilled Spirits x2, Phosphorous x1, Sayge x1, Willow Root x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "CUBS_DECOCTION",
    "value_silver": 8,
}

RECIPE_DUELISTS_DECOCTION = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Duelist's Decoction",
    "aliases": ["duelist's decoction recipe", "duelist's decoction schematic"],
    "desc": "A detailed schematic describing how to brew Duelist's Decoction (Level 1 Apotheca). Requires: Distilled Spirits x1, Dragon's Eye x2, Sayge x1, Verbaena x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "DUELISTS_DECOCTION",
    "value_silver": 8,
}

RECIPE_EAGLE = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Eagle",
    "aliases": ['eagle recipe', 'eagle schematic'],
    "desc": "A detailed schematic describing how to brew Eagle (Level 1 Apotheca). Requires: Distilled Spirits x1, Gold Lotus x2, Orgonnian Grapes x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "EAGLE",
    "value_silver": 8,
}

RECIPE_INNISS_SERUM = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Innis's Serum",
    "aliases": ["innis's serum recipe", "innis's serum schematic"],
    "desc": "A detailed schematic describing how to brew Innis's Serum (Level 1 Apotheca). Requires: Celandine x1, Distilled Spirits x2, Dragon's Eye x1, Orgonnian Grapes x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "INNISS_SERUM",
    "value_silver": 8,
}

RECIPE_LILLYWHITE = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Lillywhite",
    "aliases": ['lillywhite recipe', 'lillywhite schematic'],
    "desc": "A detailed schematic describing how to brew Lillywhite (Level 1 Apotheca). Requires: Distilled Spirits x1, Dragon's Eye x1, Verbaena x1, Willow Root x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "LILLYWHITE",
    "value_silver": 8,
}

RECIPE_MOONBREW = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Moonbrew",
    "aliases": ['moonbrew recipe', 'moonbrew schematic'],
    "desc": "A detailed schematic describing how to brew Moonbrew (Level 1 Apotheca). Requires: Distilled Spirits x1, Gold Lotus x1, Mandrake x1, Phosphorous x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "MOONBREW",
    "value_silver": 8,
}

RECIPE_PIT_FIGHTERS_ELIXIR = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Pit Fighter's Elixir",
    "aliases": ["pit fighter's elixir recipe", "pit fighter's elixir schematic"],
    "desc": "A detailed schematic describing how to brew Pit Fighter's Elixir (Level 1 Apotheca). Requires: Distilled Spirits x1, Dragon's Eye x1, Phosphorous x1, Verbaena x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "PIT_FIGHTERS_ELIXIR",
    "value_silver": 8,
}

RECIPE_PURITY_DECOCTION = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Purity Decoction",
    "aliases": ['purity decoction recipe', 'purity decoction schematic'],
    "desc": "A detailed schematic describing how to brew Purity Decoction (Level 1 Apotheca). Requires: Celandine x1, Distilled Spirits x2, Luminesce x1, Phosphorous x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "PURITY_DECOCTION",
    "value_silver": 8,
}

RECIPE_SPOTTERS_DRAUGHT = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Spotter's Draught",
    "aliases": ["spotter's draught recipe", "spotter's draught schematic"],
    "desc": "A detailed schematic describing how to brew Spotter's Draught (Level 1 Apotheca). Requires: Distilled Spirits x1, Orgonnian Grapes x2, Verbaena x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "SPOTTERS_DRAUGHT",
    "value_silver": 8,
}

RECIPE_VERDANT_DECOCTION = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Verdant Decoction",
    "aliases": ['verdant decoction recipe', 'verdant decoction schematic'],
    "desc": "A detailed schematic describing how to brew Verdant Decoction (Level 1 Apotheca). Requires: Celandine x1, Distilled Spirits x2, Hollyrue x1, Sayge x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "VERDANT_DECOCTION",
    "value_silver": 8,
}

RECIPE_WHITE_ROLANDS_SERUM = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: White Roland's Serum",
    "aliases": ["white roland's serum recipe", "white roland's serum schematic"],
    "desc": "A detailed schematic describing how to brew White Roland's Serum (Level 1 Apotheca). Requires: Distilled Spirits x1, Merchant's Leaf x1, Phosphorous x3. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "WHITE_ROLANDS_SERUM",
    "value_silver": 8,
}

RECIPE_BRIDGITS_REVENGE = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Bridgit's Revenge",
    "aliases": ["bridgit's revenge recipe", "bridgit's revenge schematic"],
    "desc": "A detailed schematic describing how to brew Bridgit's Revenge (Level 1 Poison). Requires: Distilled Spirits x1, Thornwood Fern x4. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "BRIDGITS_REVENGE",
    "value_silver": 8,
}

RECIPE_CUTTER = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Cutter",
    "aliases": ['cutter recipe', 'cutter schematic'],
    "desc": "A detailed schematic describing how to brew Cutter (Level 1 Drug). Requires: Distilled Spirits x1, Merchant's Leaf x3, Verbaena x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "CUTTER",
    "value_silver": 8,
}

RECIPE_SPICE = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Spice",
    "aliases": ['spice recipe', 'spice schematic'],
    "desc": "A detailed schematic describing how to brew Spice (Level 1 Drug). Requires: Distilled Spirits x1, Gold Lotus x1, Mandrake x1, Sayge x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "SPICE",
    "value_silver": 8,
}

RECIPE_STARDUST = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Stardust",
    "aliases": ['stardust recipe', 'stardust schematic'],
    "desc": "A detailed schematic describing how to brew Stardust (Level 1 Drug). Requires: Distilled Spirits x1, Mandrake x3, Willow Root x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "STARDUST",
    "value_silver": 8,
}

RECIPE_BEARS_DECOCTION = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Bear's Decoction",
    "aliases": ["bear's decoction recipe", "bear's decoction schematic"],
    "desc": "A detailed schematic describing how to brew Bear's Decoction (Level 2 Apotheca). Requires: Distilled Spirits x3, Phosphorous x2, Verbaena x3, Wintercrown x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "BEARS_DECOCTION",
    "value_silver": 15,
}

RECIPE_EXPERT_BLADE_OIL = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Expert Blade Oil",
    "aliases": ['expert blade oil recipe', 'expert blade oil schematic'],
    "desc": "A detailed schematic describing how to brew Expert Blade Oil (Level 2 Apotheca). Requires: Crypt Moss x1, Distilled Spirits x1, Dragon's Eye x1, Willow Root x3. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "EXPERT_BLADE_OIL",
    "value_silver": 15,
}

RECIPE_EXPERT_BLADE_SALVE = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Expert Blade Salve",
    "aliases": ['expert blade salve recipe', 'expert blade salve schematic'],
    "desc": "A detailed schematic describing how to brew Expert Blade Salve (Level 2 Apotheca). Requires: Distilled Spirits x2, Sayge x2, Verbaena x1, Willow Root x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "EXPERT_BLADE_SALVE",
    "value_silver": 15,
}

RECIPE_EXPERT_DUELISTS_DECOCTION = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Expert Duelist's Decoction",
    "aliases": ["expert duelist's decoction recipe", "expert duelist's decoction schematic"],
    "desc": "A detailed schematic describing how to brew Expert Duelist's Decoction (Level 2 Apotheca). Requires: Distilled Spirits x2, Dragon's Eye x1, Ergot Seeds x2, Sayge x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "EXPERT_DUELISTS_DECOCTION",
    "value_silver": 15,
}

RECIPE_FALCON = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Falcon",
    "aliases": ['falcon recipe', 'falcon schematic'],
    "desc": "A detailed schematic describing how to brew Falcon (Level 2 Apotheca). Requires: Creeper Moss x1, Distilled Spirits x2, Harrowdust x1, Orgonnian Grapes x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "FALCON",
    "value_silver": 15,
}

RECIPE_GORGONS_BREW = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Gorgon's Brew",
    "aliases": ["gorgon's brew recipe", "gorgon's brew schematic"],
    "desc": "A detailed schematic describing how to brew Gorgon's Brew (Level 2 Apotheca). Requires: Crypt Moss x1, Distilled Spirits x1, Ergot Seeds x2, Gold Lotus x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "GORGONS_BREW",
    "value_silver": 15,
}

RECIPE_LASTING_BREATH = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Lasting Breath",
    "aliases": ['lasting breath recipe', 'lasting breath schematic'],
    "desc": "A detailed schematic describing how to brew Lasting Breath (Level 2 Apotheca). Requires: Distilled Spirits x2, Phosphorous x1, Thornwood Fern x3, Willow Root x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "LASTING_BREATH",
    "value_silver": 15,
}

RECIPE_LOOKOUT = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Lookout",
    "aliases": ['lookout recipe', 'lookout schematic'],
    "desc": "A detailed schematic describing how to brew Lookout (Level 2 Apotheca). Requires: Distilled Spirits x1, Harrowdust x4, Orgonnian Grapes x1, Tarkathi Poppy x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "LOOKOUT",
    "value_silver": 15,
}

RECIPE_MENDER = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Mender",
    "aliases": ['mender recipe', 'mender schematic'],
    "desc": "A detailed schematic describing how to brew Mender (Level 2 Apotheca). Requires: Black Salt x2, Distilled Spirits x2, Wraith Orchid x3. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "MENDER",
    "value_silver": 15,
}

RECIPE_NYRAS_BALM = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Nyra's Balm",
    "aliases": ["nyra's balm recipe", "nyra's balm schematic"],
    "desc": "A detailed schematic describing how to brew Nyra's Balm (Level 2 Apotheca). Requires: Blood Medallion x2, Distilled Spirits x1, Tarkathi Poppy x2, Wintercrown x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "NYRAS_BALM",
    "value_silver": 15,
}

RECIPE_PUISSANCE_DRAUGHT = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Puissance Draught",
    "aliases": ['puissance draught recipe', 'puissance draught schematic'],
    "desc": "A detailed schematic describing how to brew Puissance Draught (Level 2 Apotheca). Requires: Distilled Spirits x2, Duskland Rose x2, Hollyrue x1, Luminesce x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "PUISSANCE_DRAUGHT",
    "value_silver": 15,
}

RECIPE_ELIXIR_OF_THE_WANING_MOON = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Elixir of the Waning Moon",
    "aliases": ['elixir of the waning moon recipe', 'elixir of the waning moon schematic'],
    "desc": "A detailed schematic describing how to brew Elixir of the Waning Moon (Level 2 Apotheca). Requires: Amber Lichen x1, Distilled Spirits x2, Werewolf Tallow x3, Willow Root x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "ELIXIR_OF_THE_WANING_MOON",
    "value_silver": 15,
}

RECIPE_RESURGENCE = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Resurgence",
    "aliases": ['resurgence recipe', 'resurgence schematic'],
    "desc": "A detailed schematic describing how to brew Resurgence (Level 2 Apotheca). Requires: Distilled Spirits x1, Dragon's Eye x1, Grave Blood x1, Thornwood Fern x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "RESURGENCE",
    "value_silver": 15,
}

RECIPE_SLAYER = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Slayer",
    "aliases": ['slayer recipe', 'slayer schematic'],
    "desc": "A detailed schematic describing how to brew Slayer (Level 2 Apotheca). Requires: Crypt Moss x2, Distilled Spirits x1, Dragon's Eye x2, Phosphorous x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "SLAYER",
    "value_silver": 15,
}

RECIPE_STUNNER = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Stunner",
    "aliases": ['stunner recipe', 'stunner schematic'],
    "desc": "A detailed schematic describing how to brew Stunner (Level 2 Apotheca). Requires: Distilled Spirits x2, Luminesce x2, Sayge x1, Wintercrown x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "STUNNER",
    "value_silver": 15,
}

RECIPE_SUNRISE_DECOCTION = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Sunrise Decoction",
    "aliases": ['sunrise decoction recipe', 'sunrise decoction schematic'],
    "desc": "A detailed schematic describing how to brew Sunrise Decoction (Level 2 Apotheca). Requires: Black Salt x2, Distilled Spirits x1, Ergot Seeds x2, Wraith Orchid x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "SUNRISE_DECOCTION",
    "value_silver": 15,
}

RECIPE_SWINDLERS_BREW = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Swindler's Brew",
    "aliases": ["swindler's brew recipe", "swindler's brew schematic"],
    "desc": "A detailed schematic describing how to brew Swindler's Brew (Level 2 Apotheca). Requires: Amber Lichen x2, Distilled Spirits x2, Duskland Rose x1, Hollyrue x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "SWINDLERS_BREW",
    "value_silver": 15,
}

RECIPE_URSINS_STRENGTH = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Ursin's Strength",
    "aliases": ["ursin's strength recipe", "ursin's strength schematic"],
    "desc": "A detailed schematic describing how to brew Ursin's Strength (Level 2 Apotheca). Requires: Distilled Spirits x4, Red Lotus x1, Wintercrown x2, Wraith Orchid x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "URSINS_STRENGTH",
    "value_silver": 15,
}

RECIPE_BROTH_OF_THE_VOLKUN = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Broth of the Volkun",
    "aliases": ['broth of the volkun recipe', 'broth of the volkun schematic'],
    "desc": "A detailed schematic describing how to brew Broth of the Volkun (Level 2 Poison). Requires: Creeper Moss x3, Distilled Spirits x5, Mandrake x1, Red Lotus x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "BROTH_OF_THE_VOLKUN",
    "value_silver": 15,
}

RECIPE_GRAVEDIGGER = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Gravedigger",
    "aliases": ['gravedigger recipe', 'gravedigger schematic'],
    "desc": "A detailed schematic describing how to brew Gravedigger (Level 2 Poison). Requires: Death's Head Cap x3, Distilled Spirits x1, Mandrake x1, Wraith Orchid x3. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "GRAVEDIGGER",
    "value_silver": 15,
}

RECIPE_QUAGMIRE = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Quagmire",
    "aliases": ['quagmire recipe', 'quagmire schematic'],
    "desc": "A detailed schematic describing how to brew Quagmire (Level 2 Poison). Requires: Distilled Spirits x3, Mandrake x1, Widow's Petal x4. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "QUAGMIRE",
    "value_silver": 15,
}

RECIPE_THE_GLOAMING = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: The Gloaming",
    "aliases": ['the gloaming recipe', 'the gloaming schematic'],
    "desc": "A detailed schematic describing how to brew The Gloaming (Level 2 Drug). Requires: Distilled Spirits x1, Essence of the Unhallowed x3, Tarkathi Poppy x2, Widow's Petal x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "THE_GLOAMING",
    "value_silver": 15,
}

RECIPE_MASTER_MOONLIGHT = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Master Moonlight",
    "aliases": ['master moonlight recipe', 'master moonlight schematic'],
    "desc": "A detailed schematic describing how to brew Master Moonlight (Level 2 Drug). Requires: Blood Medallion x1, Distilled Spirits x3, Harrowdust x1, Mandrake x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "MASTER_MOONLIGHT",
    "value_silver": 15,
}

RECIPE_MIRAGE = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Mirage",
    "aliases": ['mirage recipe', 'mirage schematic'],
    "desc": "A detailed schematic describing how to brew Mirage (Level 2 Drug). Requires: Distilled Spirits x2, Harrowdust x2, Widow's Petal x1, Wraith Orchid x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "MIRAGE",
    "value_silver": 15,
}

RECIPE_WINGS_OF_CORVUS = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Wings of Corvus",
    "aliases": ['wings of corvus recipe', 'wings of corvus schematic'],
    "desc": "A detailed schematic describing how to brew Wings of Corvus (Level 2 Drug). Requires: Blood Medallion x1, Distilled Spirits x3, Red Lotus x1, Tarkathi Poppy x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "WINGS_OF_CORVUS",
    "value_silver": 15,
}

RECIPE_GRIZZLYS_DECOCTION = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Grizzly's Decoction",
    "aliases": ["grizzly's decoction recipe", "grizzly's decoction schematic"],
    "desc": "A detailed schematic describing how to brew Grizzly's Decoction (Level 3 Apotheca). Requires: Distilled Spirits x2, Ergot Seeds x1, Spirit Essence x1, Verbaena x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "GRIZZLYS_DECOCTION",
    "value_silver": 25,
}

RECIPE_SERUM_OF_THE_LAST_TOWER = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Serum of the Last Tower",
    "aliases": ['serum of the last tower recipe', 'serum of the last tower schematic'],
    "desc": "A detailed schematic describing how to brew Serum of the Last Tower (Level 3 Apotheca). Requires: Black Salt x2, Distilled Spirits x3, Duskland Rose x3, Waste Lilly x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "SERUM_OF_THE_LAST_TOWER",
    "value_silver": 25,
}

RECIPE_BRINK = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Brink",
    "aliases": ['brink recipe', 'brink schematic'],
    "desc": "A detailed schematic describing how to brew Brink (Level 3 Apotheca). Requires: Distilled Spirits x3, Ergot Seeds x4, Merchant's Leaf x2, Thornwood Fern x3. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "BRINK",
    "value_silver": 25,
}

RECIPE_REAPERS_ELIXIR = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Reaper's Elixir",
    "aliases": ["reaper's elixir recipe", "reaper's elixir schematic"],
    "desc": "A detailed schematic describing how to brew Reaper's Elixir (Level 3 Apotheca). Requires: Distilled Spirits x2, Grave Blood x1, Hollyrue x1, Wraith Orchid x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "REAPERS_ELIXIR",
    "value_silver": 25,
}

RECIPE_AWAKENERS_DRAUGHT = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Awakener's Draught",
    "aliases": ["awakener's draught recipe", "awakener's draught schematic"],
    "desc": "A detailed schematic describing how to brew Awakener's Draught (Level 3 Apotheca). Requires: Celandine x3, Distilled Spirits x2, Embercap x4, Merchant's Leaf x3. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "AWAKENERS_DRAUGHT",
    "value_silver": 25,
}

RECIPE_STYPTIC_TONIC = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Styptic Tonic",
    "aliases": ['styptic tonic recipe', 'styptic tonic schematic'],
    "desc": "A detailed schematic describing how to brew Styptic Tonic (Level 3 Apotheca). Requires: Black Salt x2, Blood Medallion x4, Distilled Spirits x3, Lachrymite Resin x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "STYPTIC_TONIC",
    "value_silver": 25,
}

RECIPE_TINCTURE_OF_THE_WHITE_VEIN = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Tincture of the White Vein",
    "aliases": ['tincture of the white vein recipe', 'tincture of the white vein schematic'],
    "desc": "A detailed schematic describing how to brew Tincture of the White Vein (Level 3 Apotheca). Requires: Distilled Spirits x1, Grave Blood x3, Hag's Wort x3, Willow Root x3. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "TINCTURE_OF_THE_WHITE_VEIN",
    "value_silver": 25,
}

RECIPE_GERMAINES_CURE = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Germaine's Cure",
    "aliases": ["germaine's cure recipe", "germaine's cure schematic"],
    "desc": "A detailed schematic describing how to brew Germaine's Cure (Level 3 Apotheca). Requires: Amber Lichen x2, Distilled Spirits x2, Lachrymite Resin x3, Luminesce x3. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "GERMAINES_CURE",
    "value_silver": 25,
}

RECIPE_WEAPONMASTERS_DECOCTION = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Weaponmaster's Decoction",
    "aliases": ["weaponmaster's decoction recipe", "weaponmaster's decoction schematic"],
    "desc": "A detailed schematic describing how to brew Weaponmaster's Decoction (Level 3 Apotheca). Requires: Distilled Spirits x3, Duskland Rose x2, Entheric Oil x4, Sayge x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "WEAPONMASTERS_DECOCTION",
    "value_silver": 25,
}

RECIPE_BREATH_OF_MEDEINA = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Breath of Medeina",
    "aliases": ['breath of medeina recipe', 'breath of medeina schematic'],
    "desc": "A detailed schematic describing how to brew Breath of Medeina (Level 3 Apotheca). Requires: Crypt Moss x3, Distilled Spirits x2, Entheric Oil x4, Grave Blood x3. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "BREATH_OF_MEDEINA",
    "value_silver": 25,
}

RECIPE_SILENCE_OF_THE_SERPENT = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Silence of the Serpent",
    "aliases": ['silence of the serpent recipe', 'silence of the serpent schematic'],
    "desc": "A detailed schematic describing how to brew Silence of the Serpent (Level 3 Apotheca). Requires: Distilled Spirits x3, Embercap x2, Hag's Wort x3, Red Lotus x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "SILENCE_OF_THE_SERPENT",
    "value_silver": 25,
}

RECIPE_THE_SLEEPER = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: The Sleeper",
    "aliases": ['the sleeper recipe', 'the sleeper schematic'],
    "desc": "A detailed schematic describing how to brew The Sleeper (Level 3 Poison). Requires: Death's Head Cap x3, Distilled Spirits x4, Luminesce x1, Tarkathi Poppy x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "THE_SLEEPER",
    "value_silver": 25,
}

RECIPE_LEECH = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Leech",
    "aliases": ['leech recipe', 'leech schematic'],
    "desc": "A detailed schematic describing how to brew Leech (Level 3 Poison). Requires: Death's Head Cap x1, Distilled Spirits x3, Fulger Powder x2, Ghoul Venom x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "LEECH",
    "value_silver": 25,
}

RECIPE_REST_DENIED = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Rest Denied",
    "aliases": ['rest denied recipe', 'rest denied schematic'],
    "desc": "A detailed schematic describing how to brew Rest Denied (Level 3 Poison). Requires: Distilled Spirits x1, Essence of the Unhallowed x1, Fulger Powder x1, Ghoul Venom x1. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "REST_DENIED",
    "value_silver": 25,
}

RECIPE_LIRITS_KISS = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Lirit's Kiss",
    "aliases": ["lirit's kiss recipe", "lirit's kiss schematic"],
    "desc": "A detailed schematic describing how to brew Lirit's Kiss (Level 3 Poison). Requires: Basilisk Venom x2, Crypt Moss x4, Distilled Spirits x3, Fulger Powder x3. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "LIRITS_KISS",
    "value_silver": 25,
}

RECIPE_SONG_OF_THE_ASP = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Song of the Asp",
    "aliases": ['song of the asp recipe', 'song of the asp schematic'],
    "desc": "A detailed schematic describing how to brew Song of the Asp (Level 3 Poison). Requires: Asp Venom x2, Distilled Spirits x3, Red Lotus x3, Wraith Orchid x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "SONG_OF_THE_ASP",
    "value_silver": 25,
}

RECIPE_RESET = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Reset",
    "aliases": ['reset recipe', 'reset schematic'],
    "desc": "A detailed schematic describing how to brew Reset (Level 3 Drug). Requires: Black Lotus x3, Blood Medallion x1, Distilled Spirits x3, Red Lotus x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "RESET",
    "value_silver": 25,
}

RECIPE_STONEFACE = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Stoneface",
    "aliases": ['stoneface recipe', 'stoneface schematic'],
    "desc": "A detailed schematic describing how to brew Stoneface (Level 3 Drug). Requires: Amber Lichen x1, Creeper Moss x3, Distilled Spirits x3, Waste Lilly x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "STONEFACE",
    "value_silver": 25,
}

RECIPE_ELIXIR_OF_REVELATION = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Recipe: Elixir of Revelation",
    "aliases": ['elixir of revelation recipe', 'elixir of revelation schematic'],
    "desc": "A detailed schematic describing how to brew Elixir of Revelation (Level 3 Drug). Requires: Black Lotus x1, Distilled Spirits x3, Hag's Wort x2, Harrowdust x2. Use 'learn <scroll>' to memorize it.",
    "recipe_key": "ELIXIR_OF_REVELATION",
    "value_silver": 25,
}


# ===========================================================================
# CRAFTING SCHEMATIC SCROLLS (auto-generated from world/schematics_master.csv)
# Players learn these via:  learn <scroll>
# Sold by appropriate guild/vendor NPCs.
# ===========================================================================

SCHEMATIC_LOCKPICKING_KIT = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Lockpicking Kit',
    "aliases": ['lockpicking kit schematic', 'lockpicking kit recipe'],
    "desc": "A detailed artificer schematic describing how to craft Lockpicking Kit (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'LOCKPICKING_KIT',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_APOTHECARY_KIT = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Apothecary Kit',
    "aliases": ['apothecary kit schematic', 'apothecary kit recipe'],
    "desc": "A detailed artificer schematic describing how to craft Apothecary Kit (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'APOTHECARY_KIT',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_ARTIFICER_KIT = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Artificer Kit',
    "aliases": ['artificer kit schematic', 'artificer kit recipe'],
    "desc": "A detailed artificer schematic describing how to craft Artificer Kit (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'ARTIFICER_KIT',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_BLACKSMITH_KIT = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Blacksmith Kit',
    "aliases": ['blacksmith kit schematic', 'blacksmith kit recipe'],
    "desc": "A detailed artificer schematic describing how to craft Blacksmith Kit (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'BLACKSMITH_KIT',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_CLOTH_GAMBESON = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Cloth Gambeson',
    "aliases": ['cloth gambeson schematic', 'cloth gambeson recipe'],
    "desc": "A detailed artificer schematic describing how to craft Cloth Gambeson (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'CLOTH_GAMBESON',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_BOWYER_KIT = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Bowyer Kit',
    "aliases": ['bowyer kit schematic', 'bowyer kit recipe'],
    "desc": "A detailed artificer schematic describing how to craft Bowyer Kit (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'BOWYER_KIT',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_GUNSMITH_KIT = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Gunsmith Kit',
    "aliases": ['gunsmith kit schematic', 'gunsmith kit recipe'],
    "desc": "A detailed artificer schematic describing how to craft Gunsmith Kit (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'GUNSMITH_KIT',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_RESURRECTIONISTS_KIT = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Schematic: Resurrectionist's Kit",
    "aliases": ["resurrectionist's kit schematic", "resurrectionist's kit recipe"],
    "desc": "A detailed artificer schematic describing how to craft Resurrectionist's Kit (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'RESURRECTIONISTS_KIT',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_CHIRURGEON_KIT = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Schematic: Chirurgeon's Kit",
    "aliases": ["chirurgeon's kit schematic", "chirurgeon's kit recipe"],
    "desc": "A detailed artificer schematic describing how to craft Chirurgeon's Kit (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'CHIRURGEON_KIT',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_CRAFTSMANSHIP_TOOLS = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Craftsmanship Tools',
    "aliases": ['craftsmanship tools schematic', 'craftsmanship tools recipe'],
    "desc": "A detailed artificer schematic describing how to craft Craftsmanship Tools (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'CRAFTSMANSHIP_TOOLS',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_HIGHWAYMAN_CLOAK = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Schematic: Highwayman's Cloak",
    "aliases": ["highwayman's cloak schematic", "highwayman's cloak recipe"],
    "desc": "A detailed artificer schematic describing how to craft Highwayman's Cloak (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'HIGHWAYMAN_CLOAK',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_FINE_CLOTHING = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Fine Clothing',
    "aliases": ['fine clothing schematic', 'fine clothing recipe'],
    "desc": "A detailed artificer schematic describing how to craft Fine Clothing (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'FINE_CLOTHING',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_PEASANTS_GARB = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Schematic: Peasant's Garb",
    "aliases": ["peasant's garb schematic", "peasant's garb recipe"],
    "desc": "A detailed artificer schematic describing how to craft Peasant's Garb (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'PEASANTS_GARB',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_NOBLES_GARB = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Schematic: Noble's Garb",
    "aliases": ["noble's garb schematic", "noble's garb recipe"],
    "desc": "A detailed artificer schematic describing how to craft Noble's Garb (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'NOBLES_GARB',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_DUELIST_GLOVES = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Schematic: Duelist's Gloves",
    "aliases": ["duelist's gloves schematic", "duelist's gloves recipe"],
    "desc": "A detailed artificer schematic describing how to craft Duelist's Gloves (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'DUELIST_GLOVES',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_BASIC_LOCK = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Basic Lock',
    "aliases": ['basic lock schematic', 'basic lock recipe'],
    "desc": "A detailed artificer schematic describing how to craft Basic Lock (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'BASIC_LOCK',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_STALWART_BOOTS = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Stalwart Boots',
    "aliases": ['stalwart boots schematic', 'stalwart boots recipe'],
    "desc": "A detailed artificer schematic describing how to craft Stalwart Boots (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'STALWART_BOOTS',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_LIGHT_BOOTS = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Light Boots',
    "aliases": ['light boots schematic', 'light boots recipe'],
    "desc": "A detailed artificer schematic describing how to craft Light Boots (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'LIGHT_BOOTS',
    "value_silver": 15,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_PLAGUISTS_CASQUE = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Schematic: Plaguist's Casque",
    "aliases": ["plaguist's casque schematic", "plaguist's casque recipe"],
    "desc": "A detailed artificer schematic describing how to craft Plaguist's Casque (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'PLAGUISTS_CASQUE',
    "value_silver": 24,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_SHADOW_MANTLE = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Shadow Mantle',
    "aliases": ['shadow mantle schematic', 'shadow mantle recipe'],
    "desc": "A detailed artificer schematic describing how to craft Shadow Mantle (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'SHADOW_MANTLE',
    "value_silver": 24,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_MAGNIFICENT_CLOTHING = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Magnificent Clothing',
    "aliases": ['magnificent clothing schematic', 'magnificent clothing recipe'],
    "desc": "A detailed artificer schematic describing how to craft Magnificent Clothing (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'MAGNIFICENT_CLOTHING',
    "value_silver": 24,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_TRADESMENS_GARMENTS = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Schematic: Tradesmen's Garments",
    "aliases": ["tradesmen's garments schematic", "tradesmen's garments recipe"],
    "desc": "A detailed artificer schematic describing how to craft Tradesmen's Garments (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'TRADESMENS_GARMENTS',
    "value_silver": 24,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_LORDLY_CLOTHING = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Lordly Clothing',
    "aliases": ['lordly clothing schematic', 'lordly clothing recipe'],
    "desc": "A detailed artificer schematic describing how to craft Lordly Clothing (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'LORDLY_CLOTHING',
    "value_silver": 24,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_FINE_DUELISTS_GLOVES = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Schematic: Fine Duelist's Gloves",
    "aliases": ["fine duelist's gloves schematic", "fine duelist's gloves recipe"],
    "desc": "A detailed artificer schematic describing how to craft Fine Duelist's Gloves (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'FINE_DUELISTS_GLOVES',
    "value_silver": 24,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_QUALITY_LOCK = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Quality Lock',
    "aliases": ['quality lock schematic', 'quality lock recipe'],
    "desc": "A detailed artificer schematic describing how to craft Quality Lock (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'QUALITY_LOCK',
    "value_silver": 24,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_HUNTERS_BOOTS = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Schematic: Hunter's Boots",
    "aliases": ["hunter's boots schematic", "hunter's boots recipe"],
    "desc": "A detailed artificer schematic describing how to craft Hunter's Boots (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'HUNTERS_BOOTS',
    "value_silver": 24,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_SWORDDANCERS_BOOTS = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Schematic: Sworddancer's Boots",
    "aliases": ["sworddancer's boots schematic", "sworddancer's boots recipe"],
    "desc": "A detailed artificer schematic describing how to craft Sworddancer's Boots (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'SWORDDANCERS_BOOTS',
    "value_silver": 24,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_DARK_SILK_CLOAK = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Dark Silk Cloak',
    "aliases": ['dark silk cloak schematic', 'dark silk cloak recipe'],
    "desc": "A detailed artificer schematic describing how to craft Dark Silk Cloak (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'DARK_SILK_CLOAK',
    "value_silver": 36,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_EXQUISITE_CLOTHING = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Exquisite Clothing',
    "aliases": ['exquisite clothing schematic', 'exquisite clothing recipe'],
    "desc": "A detailed artificer schematic describing how to craft Exquisite Clothing (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'EXQUISITE_CLOTHING',
    "value_silver": 36,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_PROFESSIONALS_VESTMENTS = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Schematic: Professional's Vestments",
    "aliases": ["professional's vestments schematic", "professional's vestments recipe"],
    "desc": "A detailed artificer schematic describing how to craft Professional's Vestments (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'PROFESSIONALS_VESTMENTS',
    "value_silver": 36,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_RAIMENT_OF_HIGH_LORD = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Raiment of the High Lord',
    "aliases": ['raiment of the high lord schematic', 'raiment of the high lord recipe'],
    "desc": "A detailed artificer schematic describing how to craft Raiment of the High Lord (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'RAIMENT_OF_HIGH_LORD',
    "value_silver": 36,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_MASTER_DUELISTS_GLOVES = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Schematic: Master Duelist's Gloves",
    "aliases": ["master duelist's gloves schematic", "master duelist's gloves recipe"],
    "desc": "A detailed artificer schematic describing how to craft Master Duelist's Gloves (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'MASTER_DUELISTS_GLOVES',
    "value_silver": 36,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_MASTERWORK_LOCK = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Masterwork Lock',
    "aliases": ['masterwork lock schematic', 'masterwork lock recipe'],
    "desc": "A detailed artificer schematic describing how to craft Masterwork Lock (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'MASTERWORK_LOCK',
    "value_silver": 36,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_KNIGHTS_BOOTS = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Schematic: Knight's Boots",
    "aliases": ["knight's boots schematic", "knight's boots recipe"],
    "desc": "A detailed artificer schematic describing how to craft Knight's Boots (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'KNIGHTS_BOOTS',
    "value_silver": 36,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_THIEFS_BOOTS = {
    "typeclass": "typeclasses.objects.Object",
    "key": "Schematic: Thief's Boots",
    "aliases": ["thief's boots schematic", "thief's boots recipe"],
    "desc": "A detailed artificer schematic describing how to craft Thief's Boots (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'THIEFS_BOOTS',
    "value_silver": 36,
    "schematic_craft_type": 'Artificer',
}

SCHEMATIC_IRON_SHIELD = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Iron Shield',
    "aliases": ['iron shield schematic', 'iron shield recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Iron Shield (Level 0). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'IRON_SHIELD',
    "value_silver": 9,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_LEATHER_ARMOR = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Leather Armor',
    "aliases": ['leather armor schematic', 'leather armor recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Leather Armor (Level 0). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'LEATHER_ARMOR',
    "value_silver": 9,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_IRON_CHAIN_SHIRT = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Iron Chain Shirt',
    "aliases": ['iron chain shirt schematic', 'iron chain shirt recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Iron Chain Shirt (Level 0). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'IRON_CHAIN_SHIRT',
    "value_silver": 9,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_IRON_COAT_OF_PLATES = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Iron Scalemail/Coat of Plates',
    "aliases": ['iron scalemail/coat of plates schematic', 'iron scalemail/coat of plates recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Iron Scalemail/Coat of Plates (Level 0). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'IRON_COAT_OF_PLATES',
    "value_silver": 9,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_IRON_PLATEMAIL = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Iron Platemail',
    "aliases": ['iron platemail schematic', 'iron platemail recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Iron Platemail (Level 0). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'IRON_PLATEMAIL',
    "value_silver": 9,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_IRON_SMALL_WEAPON = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Iron Small and Throwing Weapons',
    "aliases": ['iron small and throwing weapons schematic', 'iron small and throwing weapons recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Iron Small and Throwing Weapons (Level 0). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'IRON_SMALL_WEAPON',
    "value_silver": 9,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_IRON_MEDIUM_WEAPON = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Iron Medium Weapons',
    "aliases": ['iron medium weapons schematic', 'iron medium weapons recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Iron Medium Weapons (Level 0). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'IRON_MEDIUM_WEAPON',
    "value_silver": 9,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_IRON_LARGE_WEAPON = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Iron Large Weapons',
    "aliases": ['iron large weapons schematic', 'iron large weapons recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Iron Large Weapons (Level 0). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'IRON_LARGE_WEAPON',
    "value_silver": 9,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_PATCH_KIT = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Patch Kit',
    "aliases": ['patch kit schematic', 'patch kit recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Patch Kit (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'PATCH_KIT',
    "value_silver": 15,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_HARDENED_IRON_SHIELD = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Hardened Iron Shield',
    "aliases": ['hardened iron shield schematic', 'hardened iron shield recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Hardened Iron Shield (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'HARDENED_IRON_SHIELD',
    "value_silver": 15,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_HARDENED_LEATHER_ARMOR = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Hardened Leather Armor',
    "aliases": ['hardened leather armor schematic', 'hardened leather armor recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Hardened Leather Armor (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'HARDENED_LEATHER_ARMOR',
    "value_silver": 15,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_HARDENED_IRON_CHAIN_SHIRT = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Hardened Iron Chain Shirt',
    "aliases": ['hardened iron chain shirt schematic', 'hardened iron chain shirt recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Hardened Iron Chain Shirt (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'HARDENED_IRON_CHAIN_SHIRT',
    "value_silver": 15,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_HARDENED_IRON_COAT_OF_PLATES = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Hardened Iron Scalemail/Coat of Plates',
    "aliases": ['hardened iron scalemail/coat of plates schematic', 'hardened iron scalemail/coat of plates recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Hardened Iron Scalemail/Coat of Plates (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'HARDENED_IRON_COAT_OF_PLATES',
    "value_silver": 15,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_HARDENED_IRON_PLATE_ARMOR = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Hardened Iron Plate Armor',
    "aliases": ['hardened iron plate armor schematic', 'hardened iron plate armor recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Hardened Iron Plate Armor (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'HARDENED_IRON_PLATE_ARMOR',
    "value_silver": 15,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_HARDENED_IRON_SMALL_WEAPON = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Hardened Iron Small and Throwing Weapons',
    "aliases": ['hardened iron small and throwing weapons schematic', 'hardened iron small and throwing weapons recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Hardened Iron Small and Throwing Weapons (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'HARDENED_IRON_SMALL_WEAPON',
    "value_silver": 15,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_HARDENED_IRON_MEDIUM_WEAPON = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Hardened Iron Medium Weapons',
    "aliases": ['hardened iron medium weapons schematic', 'hardened iron medium weapons recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Hardened Iron Medium Weapons (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'HARDENED_IRON_MEDIUM_WEAPON',
    "value_silver": 15,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_HARDENED_IRON_LARGE_WEAPON = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Hardened Iron Large Weapons',
    "aliases": ['hardened iron large weapons schematic', 'hardened iron large weapons recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Hardened Iron Large Weapons (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'HARDENED_IRON_LARGE_WEAPON',
    "value_silver": 15,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_REVIVICATOR = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Revivicator',
    "aliases": ['revivicator schematic', 'revivicator recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Revivicator (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'REVIVICATOR',
    "value_silver": 15,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_STEEL_SHIELD = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Steel Shield',
    "aliases": ['steel shield schematic', 'steel shield recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Steel Shield (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'STEEL_SHIELD',
    "value_silver": 24,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_IMPROVED_LEATHER_ARMOR = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Improved Leather Armor',
    "aliases": ['improved leather armor schematic', 'improved leather armor recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Improved Leather Armor (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'IMPROVED_LEATHER_ARMOR',
    "value_silver": 24,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_STEEL_CHAIN_SHIRT = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Steel Chain Shirt',
    "aliases": ['steel chain shirt schematic', 'steel chain shirt recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Steel Chain Shirt (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'STEEL_CHAIN_SHIRT',
    "value_silver": 24,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_STEEL_COAT_OF_PLATES = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Steel Coat of Plates',
    "aliases": ['steel coat of plates schematic', 'steel coat of plates recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Steel Coat of Plates (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'STEEL_COAT_OF_PLATES',
    "value_silver": 24,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_STEEL_PLATE_ARMOR = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Steel Plate Armor',
    "aliases": ['steel plate armor schematic', 'steel plate armor recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Steel Plate Armor (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'STEEL_PLATE_ARMOR',
    "value_silver": 24,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_STEEL_SMALL_WEAPON = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Steel Small Weapon',
    "aliases": ['steel small weapon schematic', 'steel small weapon recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Steel Small Weapon (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'STEEL_SMALL_WEAPON',
    "value_silver": 24,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_STEEL_MEDIUM_WEAPON = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Steel Medium Weapons',
    "aliases": ['steel medium weapons schematic', 'steel medium weapons recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Steel Medium Weapons (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'STEEL_MEDIUM_WEAPON',
    "value_silver": 24,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_STEEL_LARGE_WEAPON = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Steel Large Weapons',
    "aliases": ['steel large weapons schematic', 'steel large weapons recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Steel Large Weapons (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'STEEL_LARGE_WEAPON',
    "value_silver": 24,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_MASTERWORK_STEEL_SHIELD = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Masterwork Steel Shield',
    "aliases": ['masterwork steel shield schematic', 'masterwork steel shield recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Masterwork Steel Shield (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'MASTERWORK_STEEL_SHIELD',
    "value_silver": 36,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_MASTERWORK_LEATHER_ARMOR = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Masterwork Leather Armor',
    "aliases": ['masterwork leather armor schematic', 'masterwork leather armor recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Masterwork Leather Armor (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'MASTERWORK_LEATHER_ARMOR',
    "value_silver": 36,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_MASTERWORK_STEEL_CHAIN_SHIRT = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Masterwork Steel Chain Shirt',
    "aliases": ['masterwork steel chain shirt schematic', 'masterwork steel chain shirt recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Masterwork Steel Chain Shirt (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'MASTERWORK_STEEL_CHAIN_SHIRT',
    "value_silver": 36,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_MASTERWORK_STEEL_COAT_OF_PLATES = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Masterwork Steel Coat of Plates',
    "aliases": ['masterwork steel coat of plates schematic', 'masterwork steel coat of plates recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Masterwork Steel Coat of Plates (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'MASTERWORK_STEEL_COAT_OF_PLATES',
    "value_silver": 36,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_MASTERWORK_STEEL_PLATE_MAIL = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Masterwork Steel Plate Mail',
    "aliases": ['masterwork steel plate mail schematic', 'masterwork steel plate mail recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Masterwork Steel Plate Mail (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'MASTERWORK_STEEL_PLATE_MAIL',
    "value_silver": 36,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_MASTERWORK_STEEL_SMALL_WEAPON = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Masterwork Steel Small or Thrown Weapons',
    "aliases": ['masterwork steel small or thrown weapons schematic', 'masterwork steel small or thrown weapons recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Masterwork Steel Small or Thrown Weapons (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'MASTERWORK_STEEL_SMALL_WEAPON',
    "value_silver": 36,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_MASTERWORK_STEEL_MEDIUM_WEAPON = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Masterwork Steel Medium Weapons',
    "aliases": ['masterwork steel medium weapons schematic', 'masterwork steel medium weapons recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Masterwork Steel Medium Weapons (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'MASTERWORK_STEEL_MEDIUM_WEAPON',
    "value_silver": 36,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_MASTERWORK_STEEL_LARGE_WEAPON = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Masterwork Steel Large Weapons',
    "aliases": ['masterwork steel large weapons schematic', 'masterwork steel large weapons recipe'],
    "desc": "A detailed blacksmith schematic describing how to craft Masterwork Steel Large Weapons (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'MASTERWORK_STEEL_LARGE_WEAPON',
    "value_silver": 36,
    "schematic_craft_type": 'Blacksmith',
}

SCHEMATIC_ARROWS = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Arrows (10)',
    "aliases": ['arrows (10) schematic', 'arrows (10) recipe'],
    "desc": "A detailed bowyer schematic describing how to craft Arrows (10) (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'ARROWS',
    "value_silver": 15,
    "schematic_craft_type": 'Bowyer',
}

SCHEMATIC_BOW = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Bow',
    "aliases": ['bow schematic', 'bow recipe'],
    "desc": "A detailed bowyer schematic describing how to craft Bow (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'BOW',
    "value_silver": 15,
    "schematic_craft_type": 'Bowyer',
}

SCHEMATIC_LONGBOW = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Longbow',
    "aliases": ['longbow schematic', 'longbow recipe'],
    "desc": "A detailed bowyer schematic describing how to craft Longbow (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'LONGBOW',
    "value_silver": 24,
    "schematic_craft_type": 'Bowyer',
}

SCHEMATIC_MASTERWORK_BOW = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Masterwork Bow',
    "aliases": ['masterwork bow schematic', 'masterwork bow recipe'],
    "desc": "A detailed bowyer schematic describing how to craft Masterwork Bow (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'MASTERWORK_BOW',
    "value_silver": 36,
    "schematic_craft_type": 'Bowyer',
}

SCHEMATIC_BULLETS = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Bullets (3)',
    "aliases": ['bullets (3) schematic', 'bullets (3) recipe'],
    "desc": "A detailed gunsmith schematic describing how to craft Bullets (3) (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'BULLETS',
    "value_silver": 15,
    "schematic_craft_type": 'Gunsmith',
}

SCHEMATIC_CRUDE_PISTOL = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Crude Pistol',
    "aliases": ['crude pistol schematic', 'crude pistol recipe'],
    "desc": "A detailed gunsmith schematic describing how to craft Crude Pistol (Level I). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'CRUDE_PISTOL',
    "value_silver": 24,
    "schematic_craft_type": 'Gunsmith',
}

SCHEMATIC_BASIC_PISTOL = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Basic Pistol',
    "aliases": ['basic pistol schematic', 'basic pistol recipe'],
    "desc": "A detailed gunsmith schematic describing how to craft Basic Pistol (Level II). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'BASIC_PISTOL',
    "value_silver": 24,
    "schematic_craft_type": 'Gunsmith',
}

SCHEMATIC_MASTERWORK_PISTOL = {
    "typeclass": "typeclasses.objects.Object",
    "key": 'Schematic: Masterwork Pistol',
    "aliases": ['masterwork pistol schematic', 'masterwork pistol recipe'],
    "desc": "A detailed gunsmith schematic describing how to craft Masterwork Pistol (Level III). Use 'learn <scroll>' to memorize.",
    "recipe_key": 'MASTERWORK_PISTOL',
    "value_silver": 36,
    "schematic_craft_type": 'Gunsmith',
}
