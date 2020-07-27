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
Begin weapon prototypes.

Should have name, required resources, value_silver, value_gold, value_copper, material value

"""
BLACKSMITH = {
"key": "blacksmith",
"level": 0,
"required_resources": 0,
"material_value": 0,
"value_copper": 0,
"value_silver": 0,
"value_gold": 0
}

IRON_SMALL_WEAPON = {
"prototype_parent": "BLACKSMITH",
"key": "Iron Small Weapon",
"aliases": ["small dagger", "dagger", "shortsword", "small club", "small hammer"],
"required_resources": ["1 Iron Ingot", "1 Refined Wood"],
"damage": 1,
"value_copper": 70,
"value_silver": 7,
"value_gold": .7
}

IRON_MEDIUM_WEAPON = {
"prototype_parent": "BLACKSMITH",
"key": "Iron Medium Weapon",
"aliases": ["longsword", "medium sword", "mace", "axe", "hammer"],
"required_resources": ["2 Iron Ingots", "1 Refined Wood", "1 Leather"],
"damage": 1,
"value_copper": 90,
"value_silver": 9,
"value_gold": .9
}

IRON_LARGE_WEAPON = {
"prototype_parent": "BLACKSMITH",
"key": "Iron Large Weapon",
"aliases": ["staff", "polearm", "spear", "great axe", "great hammer", "two handed sword", "bastard sword"],
"required_resources": ["2 Iron Ingots", "1 Refined Wood", "1 Leather"],
"damage": 2,
"value_copper": 90,
"value_silver": 9,
"value_gold": .9
}

IRON_SHIELD = {
"prototype_parent": "BLACKSMITH",
"key": "Iron Shield",
"aliases": ["iron shield, basic shield"],
"required_resources": ["1 Iron Ingot", "1 Refined Wood", "1 Leather"],
"value_copper": 80,
"value_silver": 8,
"value_gold": .8
}
