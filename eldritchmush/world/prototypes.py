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
"required_resources": 2,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 0,
"cloth": 0,
"damage": 1,
"value_copper": 70,
"value_silver": 7,
"value_gold": .7,
"material_value": 1,
"level": 0
}

IRON_MEDIUM_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Medium Weapon",
"aliases": ["iron medium weapon"],
"required_resources": 4,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"damage": 1,
"value_copper": 90,
"value_silver": 9,
"value_gold": .9,
"material_value": 1,
"level": 0
}

IRON_LARGE_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Large Weapon",
"aliases": ["iron large weapon"],
"required_resources": 4,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"damage": 2,
"twohanded": True,
"value_copper": 90,
"value_silver": 9,
"value_gold": .9,
"material_value": 1,
"level": 0
}

IRON_SHIELD = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"is_shield": True,
"key": "Iron Shield",
"aliases": ["iron shield"],
"required_resources": 3,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"value_copper": 80,
"value_silver": 8,
"value_gold": .8,
"material_value": 1,
"level": 0
}

LEATHER_ARMOR = {
"typeclass": "typeclasses.objects.WeaponObject",
"is_armor": True,
"key": "Leather Armor",
"required_resources": 2,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
 "value_copper": 70,
 "value_silver": 7,
 "value_gold": .7,
 "material_value": 1,
 "level": 0
}

IRON_CHAIN_SHIRT = {
"typeclass": "typeclasses.objects.WeaponObject",
"is_armor": True,
"key": "Iron Chain Shirt",
"aliases": ["iron chain shirt"],
"required_resources": 2,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 0,
"cloth": 0,
 "value_copper": 70,
 "value_silver": 7,
 "value_gold": .7,
 "material_value": 1,
 "level": 0
}

IRON_COAT_OF_PLATES = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Coat of Plates",
"aliases": ["iron coat of plates"],
"is_armor": True,
"required_resources": 5,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 2,
"cloth": 0,
 "value_copper": 100,
 "value_silver": 10,
 "value_gold": 1,
 "material_value": 3,
 "level": 0
}

IRON_PLATEMAIL = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Platemail",
"aliases": ["iron platemail"],
"is_armor": True,
"required_resources": 7,
"iron_ingots": 4,
"refined_wood": 1,
"leather": 2,
"cloth": 0,
 "value_copper": 120,
 "value_silver": 12,
 "value_gold": 1.2,
 "material_value": 5,
 "level": 0
}

"""
Level 1 Blacksmith Items
"""

# Used with the patch command
PATCH_KIT = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Patch Kit",
"aliases": ["patch kit"],
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
"required_resources": 5,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 2,
"cloth": 0,
"damage": 1,
"value_copper": 130,
"value_silver": 13,
"value_gold": 1.3,
"material_value": 1,
"level": 1
}

HARDENED_IRON_MEDIUM_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Hardened Iron Medium Weapon",
"aliases": ["hardened iron medium weapon"],
"required_resources": 9,
"iron_ingots": 5,
"refined_wood": 2,
"leather": 2,
"cloth": 0,
"damage": 1,
"value_copper": 170,
"value_silver": 17,
"value_gold": 1.7,
"material_value": 1,
"level": 1
}

HARDENED_IRON_LARGE_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Hardened Iron Large Weapon",
"aliases": ["hardened iron large weapon", "staff", "polearm", "spear", "great axe", "great hammer", "two handed sword", "bastard sword"],
"required_resources": 4,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"damage": 2,
"twohanded": True,
"value_copper": 90,
"value_silver": 9,
"value_gold": .9,
"material_value": 1,
"level": 1
}

HARDENED_IRON_SHIELD = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"is_shield": True,
"key": "Hardened Iron Shield",
"aliases": ["hardened iron shield"],
"required_resources": 6,
"iron_ingots": 2,
"refined_wood": 2,
"leather": 2,
"cloth": 0,
"value_copper": 140,
"value_silver": 14,
"value_gold": 1.4,
"material_value": 1,
"level": 1
}

HARDENED_LEATHER_ARMOR = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"is_armor": True,
"key": "Hardened Leather Armor",
"aliases": ["hardened leather armor"],
"required_resources": 6,
"iron_ingots": 0,
"refined_wood": 0,
"leather": 4,
"cloth": 2,
"value_copper": 140,
"value_silver": 14,
"value_gold": 1.4,
"material_value": 2,
"level": 1
}

HARDENED_IRON_CHAIN_SHIRT = {
"typeclass": "typeclasses.objects.WeaponObject",
"is_armor": True,
"key": "Hardened Iron Shield",
"aliases": ["hardened iron shield"],
"required_resources": 7,
"iron_ingots": 3,
"refined_wood": 2,
"leather": 2,
"cloth": 0,
"value_copper": 150,
"value_silver": 15,
"value_gold": 1.5,
"material_value": 2,
"level": 1
}

HARDENED_IRON_COAT_OF_PLATES = {
"typeclass": "typeclasses.objects.WeaponObject",
"is_armor": True,
"key": "Hardened Iron Coat of Plates",
"aliases": ["hardened iron coat of plates"],
"required_resources": 12,
"iron_ingots": 6,
"refined_wood": 2,
"leather": 2,
"cloth": 2,
"value_copper": 200,
"value_silver": 20,
"value_gold": 2,
"material_value": 4,
"level": 1
}

HARDENED_IRON_PLATEMAIL = {
"typeclass": "typeclasses.objects.WeaponObject",
"is_armor": True,
"key": "Hardened Iron Plate",
"aliases": ["hardened iron plate"],
"required_resources": 14,
"iron_ingots": 8,
"refined_wood": 2,
"leather": 2,
"cloth": 2,
"value_copper": 220,
"value_silver": 22,
"value_gold": 2.2,
"material_value": 6,
"level": 1
}

"""
Level 2 Blacksmith Items
"""

STEEL_SMALL_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Steel Small Weapon",
"aliases": ["steel small weapon"],
"required_resources": 6,
"iron_ingots": 4,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"damage": 1,
"value_copper": 180,
"value_silver": 18,
"value_gold": 1.8,
"material_value": 2,
"level": 2
}

STEEL_MEDIUM_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Steel Medium Weapon",
"aliases": ["steel medium weapon"],
"required_resources": 11,
"iron_ingots": 6,
"refined_wood": 2,
"leather": 3,
"cloth": 0,
"damage": 1,
"value_copper": 230,
"value_silver": 23,
"value_gold": 2.3,
"material_value": 2,
"level": 2
}

STEEL_LARGE_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Steel Large Weapon",
"aliases": ["steel large weapon"],
"required_resources": 13,
"iron_ingots": 8,
"refined_wood": 2,
"leather": 3,
"cloth": 0,
"damage": 2,
"twohanded": True,
"value_copper": 250,
"value_silver": 25,
"value_gold": 2.5,
"material_value": 2,
"level": 2
}

STEEL_SHIELD = {
"typeclass": "typeclasses.objects.WeaponObject",
"is_shield": True,
"key": "Steel Shield",
"aliases": ["steel shield"],
"required_resources": 11,
"iron_ingots": 5,
"refined_wood": 3,
"leather": 3,
"cloth": 0,
"value_copper": 230,
"value_silver": 23,
"value_gold": 2.3,
"material_value": 2,
"level": 2
}

STEEL_CHAIN_SHIRT = {
"typeclass": "typeclasses.objects.WeaponObject",
"is_armor": True,
"key": "Steel Chain Shirt",
"aliases": ["steel chain shirt"],
"required_resources": 8,
"iron_ingots": 4,
"refined_wood": 2,
"leather": 2,
"cloth": 0,
"value_copper": 200,
"value_silver": 20,
"value_gold": 2,
"material_value": 4,
"level": 2
}


STEEL_COAT_OF_PLATES = {
"typeclass": "typeclasses.objects.WeaponObject",
"is_armor": True,
"key": "Steel Coat of Plates",
"aliases": ["steel coat of plates"],
"required_resources": 14,
"iron_ingots": 8,
"refined_wood": 2,
"leather": 2,
"cloth": 2,
"value_copper": 260,
"value_silver": 26,
"value_gold": 2.6,
"material_value": 6
}

STEEL_PLATEMAIL = {
"typeclass": "typeclasses.objects.WeaponObject",
"is_armor": True,
"key": "Steel Platemail",
"aliases": ["steel platemail"],
"required_resources": 17,
"iron_ingots": 8,
"refined_wood": 3,
"leather": 3,
"cloth": 3,
"value_copper": 290,
"value_silver": 29,
"value_gold": 2.9,
"material_value": 8,
"level": 2
}

"""
Level 3 Blacksmith Items
"""

MASTERWORK_STEEL_SMALL_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Masterwork Steel Small Weapon",
"aliases": ["masterwork steel small weapon"],
"required_resources": 14,
"iron_ingots": 8,
"refined_wood": 2,
"leather": 4,
"cloth": 0,
"damage": 1,
"value_copper": 320,
"value_silver": 32,
"value_gold": 3.2,
"material_value": 3,
"level": 3
}

MASTERWORK_STEEL_MEDIUM_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Masterwork Steel Medium Weapon",
"aliases": ["masterwork steel medium weapon"],
"required_resources": 21,
"iron_ingots": 11,
"refined_wood": 5,
"leather": 5,
"cloth": 0,
"damage": 1,
"value_copper": 390,
"value_silver": 39,
"value_gold": 3.9,
"material_value": 3,
"level": 3
}

MASTERWORK_STEEL_LARGE_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Masterwork Steel Large Weapon",
"aliases": ["masterwork steel large weapon"],
"required_resources": 24,
"iron_ingots": 12,
"refined_wood": 6,
"leather": 6,
"cloth": 0,
"damage": 2,
"twohanded": True,
"value_copper": 420,
"value_silver": 42,
"value_gold": 4.2,
"material_value": 3,
"level": 3
}

MASTERWORK_STEEL_SHIELD = {
"typeclass": "typeclasses.objects.WeaponObject",
"is_shield": True,
"key": "Masterwork Steel Shield",
"aliases": ["masterwork steel shield"],
"required_resources": 17,
"iron_ingots": 9,
"refined_wood": 4,
"leather": 4,
"cloth": 0,
"value_copper": 350,
"value_silver": 35,
"value_gold": 3.8,
"material_value": 4,
"level": 3
}

MASTERWORK_STEEL_CHAIN_SHIRT = {
"typeclass": "typeclasses.objects.WeaponObject",
"is_armor": True,
"key": "Masterwork Steel Chain Shirt",
"aliases": ["masterwork steel chain shirt"],
"required_resources": 17,
"iron_ingots": 10,
"refined_wood": 0,
"leather": 4,
"cloth": 3,
"value_copper": 350,
"value_silver": 35,
"value_gold": 3.5,
"material_value": 8,
"level": 3
}


MASTERWORK_STEEL_COAT_OF_PLATES = {
"typeclass": "typeclasses.objects.WeaponObject",
"is_armor": True,
"key": "Masterwork Steel Coat of Plates",
"aliases": ["masterwork steel coat of plates"],
"required_resources": 24,
"iron_ingots": 10,
"refined_wood": 2,
"leather": 8,
"cloth": 4,
"value_copper": 420,
"value_silver": 42,
"value_gold": 4.2,
"material_value": 10,
"level": 3
}

MASTERWORK_STEEL_PLATEMAIL = {
"typeclass": "typeclasses.objects.WeaponObject",
"is_armor": True,
"key": "Masterwork Steel Platemail",
"aliases": ["masterwork steel platemail"],
"required_resources": 28,
"iron_ingots": 16,
"refined_wood": 2,
"leather": 6,
"cloth": 4,
"value_copper": 460,
"value_silver": 46,
"value_gold": 4.6,
"material_value": 12,
"level": 3
}

"""
Begin artificer protoypes
"""

"""
Bowyer Items
"""

ARROWS = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Arrows",
"aliases": ["arrows"],
"quantity": 10,
"required_resources": 3,
"iron_ingots": 1,
"refined_wood": 2,
"leather": 0,
"cloth": 0,
"value_copper": 80,
"value_silver": 8,
"value_gold": .8,
"level": 0
}


BOW = {
"typeclass": "typeclasses.objects.WeaponObject",
"is_bow": True,
"twohanded": True,
"key": "Bow",
"aliases": ["bow"],
"required_resources": 9,
"iron_ingots": 2,
"refined_wood": 6,
"leather": 1,
"cloth": 0,
"value_copper": 170,
"value_silver": 17,
"value_gold": 1.7,
"material_value": 2,
"level": 1
}

MASTERWORK_BOW = {
"typeclass": "typeclasses.objects.WeaponObject",
"is_bow": True,
"twohanded": True,
"key": "Masterwork Bow",
"aliases": ["masterwork bow"],
"required_resources": 18,
"iron_ingots": 2,
"refined_wood": 12,
"leather": 4,
"cloth": 0,
"value_copper": 350,
"value_silver": 35,
"value_gold": 3.5,
"material_value": 3,
"level": 3
}
