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
"value_gold": .7
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
"value_gold": .9
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
"value_gold": .9
}

IRON_SHIELD = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Iron Shield",
"aliases": ["iron shield"],
"required_resources": 3,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"value_copper": 80,
"value_silver": 8,
"value_gold": .8
}

LEATHER_ARMOR = {
"typeclass": "typeclasses.objects.WeaponObject",
"required_resources": 2,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
 "value_copper": 70,
 "value_silver": 7,
 "value_gold": .7
}

IRON_CHAIN_SHIRT = {
"typeclass": "typeclasses.objects.WeaponObject",
"required_resources": 2,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 0,
"cloth": 0,
 "value_copper": 70,
 "value_silver": 7,
 "value_gold": .7
}

IRON_COAT_OF_PLATES = {
"typeclass": "typeclasses.objects.WeaponObject",
"required_resources": 5,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 2,
"cloth": 0,
 "value_copper": 100,
 "value_silver": 10,
 "value_gold": 1
}

IRON_PLATEMAIL = {
"typeclass": "typeclasses.objects.WeaponObject",
"required_resources": 7,
"iron_ingots": 4,
"refined_wood": 1,
"leather": 2,
"cloth": 0,
 "value_copper": 120,
 "value_silver": 12,
 "value_gold": 1.2
}

"""
Level 1 Blacksmith Items
"""

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
"value_gold": 1.3
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
"value_gold": 1.7
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
"value_gold": .9
}

HARDENED_IRON_SHIELD = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"key": "Iron Shield",
"aliases": ["iron shield, basic shield"],
"required_resources": 3,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"value_copper": 80,
"value_silver": 8,
"value_gold": .8
}

HARDENED_LEATHER_ARMOR = {
"typeclass": "typeclasses.objects.BlacksmithObject",
"required_resources": 2,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
 "value_copper": 70,
 "value_silver": 7,
 "value_gold": .7
}

HARDENED_IRON_CHAIN_SHIRT = {
"typeclass": "typeclasses.objects.WeaponObject",
"required_resources": 2,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 0,
"cloth": 0,
 "value_copper": 70,
 "value_silver": 7,
 "value_gold": .7
}

HARDENED_IRON_COAT_OF_PLATES = {
"typeclass": "typeclasses.objects.WeaponObject",
"required_resources": 5,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 2,
"cloth": 0,
 "value_copper": 100,
 "value_silver": 10,
 "value_gold": 1
}

HARDENED_IRON_PLATEMAIL = {
"typeclass": "typeclasses.objects.WeaponObject",
"required_resources": 7,
"iron_ingots": 4,
"refined_wood": 1,
"leather": 2,
"cloth": 0,
 "value_copper": 120,
 "value_silver": 12,
 "value_gold": 1.2
}

"""
Level 2 Blacksmith Items
"""

STEEL_SMALL_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Small Weapon",
"aliases": ["iron small weapon", "small dagger", "dagger", "shortsword", "small club", "small hammer"],
"required_resources": 2,
"iron_ingots": 1,
"refined_wood": 1,
"damage": 1,
"value_copper": 70,
"value_silver": 7,
"value_gold": .7
}

STEEL_MEDIUM_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Medium Weapon",
"aliases": ["iron medium weapon", "longsword", "medium sword", "mace", "axe", "hammer"],
"required_resources": 4,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"damage": 1,
"value_copper": 90,
"value_silver": 9,
"value_gold": .9
}

STEEL_LARGE_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Large Weapon",
"aliases": ["iron large weapon", "staff", "polearm", "spear", "great axe", "great hammer", "two handed sword", "bastard sword"],
"required_resources": 4,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"damage": 2,
"twohanded": True,
"value_copper": 90,
"value_silver": 9,
"value_gold": .9
}

STEEL_SHIELD = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Shield",
"aliases": ["iron shield, basic shield"],
"required_resources": 3,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"value_copper": 80,
"value_silver": 8,
"value_gold": .8
}

STEEL_CHAIN_SHIRT = {
"typeclass": "typeclasses.objects.WeaponObject",
"required_resources": 2,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
 "value_copper": 70,
 "value_silver": 7,
 "value_gold": .7
}


STEEL_COAT_OF_PLATES = {
"typeclass": "typeclasses.objects.WeaponObject",
"required_resources": 5,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 2,
"cloth": 0,
 "value_copper": 100,
 "value_silver": 10,
 "value_gold": 1
}

STEEL_PLATEMAIL = {
"typeclass": "typeclasses.objects.WeaponObject",
"required_resources": 7,
"iron_ingots": 4,
"refined_wood": 1,
"leather": 2,
"cloth": 0,
 "value_copper": 120,
 "value_silver": 12,
 "value_gold": 1.2
}

"""
Level 3 Blacksmith Items
"""

MASTERWORK_STEEL_SMALL_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Small Weapon",
"aliases": ["iron small weapon", "small dagger", "dagger", "shortsword", "small club", "small hammer"],
"required_resources": 2,
"iron_ingots": 1,
"refined_wood": 1,
"damage": 1,
"value_copper": 70,
"value_silver": 7,
"value_gold": .7
}

MASTERWORK_STEEL_MEDIUM_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Medium Weapon",
"aliases": ["iron medium weapon", "longsword", "medium sword", "mace", "axe", "hammer"],
"required_resources": 4,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"damage": 1,
"value_copper": 90,
"value_silver": 9,
"value_gold": .9
}

MASTERWORK_STEEL_LARGE_WEAPON = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Large Weapon",
"aliases": ["iron large weapon", "staff", "polearm", "spear", "great axe", "great hammer", "two handed sword", "bastard sword"],
"required_resources": 4,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"damage": 2,
"twohanded": True,
"value_copper": 90,
"value_silver": 9,
"value_gold": .9
}

MASTERWORK_STEEL_SHIELD = {
"typeclass": "typeclasses.objects.WeaponObject",
"key": "Iron Shield",
"aliases": ["iron shield, basic shield"],
"required_resources": 3,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
"value_copper": 80,
"value_silver": 8,
"value_gold": .8
}

MASTERWORK_STEEL_CHAIN_SHIRT = {
"typeclass": "typeclasses.objects.WeaponObject",
"required_resources": 2,
"iron_ingots": 1,
"refined_wood": 1,
"leather": 1,
"cloth": 0,
 "value_copper": 70,
 "value_silver": 7,
 "value_gold": .7
}


MASTERWORK_STEEL_COAT_OF_PLATES = {
"typeclass": "typeclasses.objects.WeaponObject",
"required_resources": 5,
"iron_ingots": 2,
"refined_wood": 1,
"leather": 2,
"cloth": 0,
 "value_copper": 100,
 "value_silver": 10,
 "value_gold": 1
}

MASTERWORK_STEEL_PLATEMAIL = {
"typeclass": "typeclasses.objects.WeaponObject",
"required_resources": 7,
"iron_ingots": 4,
"refined_wood": 1,
"leather": 2,
"cloth": 0,
 "value_copper": 120,
 "value_silver": 12,
 "value_gold": 1.2
}
