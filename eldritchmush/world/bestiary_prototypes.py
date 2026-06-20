"""
world/bestiary_prototypes.py — Encounter-ready monster prototypes.

The 9 "ready-to-build" Eldritch Monster Manual entries: those that have BOTH
a full manual statline AND dedicated matched art. Each is a spawnable
``typeclasses.npc.Npc`` prototype.

Stat mapping (from docs/bestiary.md "How the manual maps onto an NPC"):
    Manual "Tough - N" worn armor   ->  db.tough  (natural armor)
    Manual worn/Medium/Heavy armor  ->  db.av     (from equipped armor)
    NPC AV = tough + av
    Stagger/Cleave/Sunder/Stun/     ->  db.<skill>  (integer rank)
      Disarm/Resist ranks
    Weapon (Small/Medium/Large/2H)  ->  db.weapon_proto + db.weapon_level
    Challenge Rating                ->  db.tier (0-4) + threat role
    "always attacks"                ->  db.is_aggressive = True

NEW data-only fields carried for the web client / future systems:
    db.art_key  — portrait slug; frontend resolves slug -> framed PNG
                  (see frontend/src/data/antagonists.js)
    db.tier     — our 0-4 tier (manual CR mapped per docs/bestiary.md)
    db.special  — list of the manual's special-ability NAMES as flags.
                  These are LARP rules (regen / disease / ranged-immunity /
                  Fear / Paralyze / Nether Ward, etc.) with NO MUD mechanic
                  yet — they are carried as data only. Wiring them is a
                  separate combat-code task; see docs/bestiary-build.md.

The manual gives no `body` value — every entry uses AV (Tough + armor) as
its durability. We leave body/bleed/death at NPC defaults (3/3/3) and treat
`tough` as the meaningful durability stat (see docs/bestiary-build.md
"HP/body mapping decision").

Spawn in-game with:  @spawn WIGHT
Prototype keys are globally unique ALL_CAPS.
"""

# ─────────────────────────────────────────────────────────────────────────
# Lycanthropes
# ─────────────────────────────────────────────────────────────────────────

WURDULAC = {
    "key": "wurdulac",
    "typeclass": "typeclasses.npc.Npc",
    "desc": (
        "A diseased werewolf spawn, all rage and hunger — a pack ambusher "
        "whose claws never seem to tire."
    ),
    # AV 4 (Tough 4)
    "tough": 4, "av": 0,
    "body": 3, "bleed_points": 3, "death_points": 3,
    # Cleave 1
    "cleave": 1,
    "stagger": 0, "sunder": 0, "stun": 0, "disarm": 0, "resist": 0,
    # boffer claws / 1H -> medium weapon
    "weapon_proto": "IRON_MEDIUM_WEAPON", "weapon_level": 1,
    "is_aggressive": True,
    "art_key": "werewolf", "tier": 2,
    "special": ["immune_ranged", "lesser_regeneration", "lycanthropic_infection"],
}

WEREWOLF = {
    "key": "werewolf",
    "typeclass": "typeclasses.npc.Npc",
    "desc": (
        "An apex lycan of Dranor's line — it howls, rampages with brief "
        "invulnerability, and knits its wounds shut faster than you can open "
        "them."
    ),
    # AV 10 (Tough 10)
    "tough": 10, "av": 0,
    "body": 3, "bleed_points": 3, "death_points": 3,
    # Cleave is its normal attack; Disarm at will
    "cleave": 1, "disarm": 1,
    "stagger": 0, "sunder": 0, "stun": 0, "resist": 0,
    # 2x boffer claws -> large weapon
    "weapon_proto": "IRON_LARGE_WEAPON", "weapon_level": 2,
    "is_aggressive": True, "boss_encounter": True,
    "art_key": "werewolf_alpha", "tier": 4,
    "special": [
        "immune_ranged", "immune_sunder", "immune_disarm", "immune_stun",
        "music_of_the_dark_forest", "lycan_regeneration",
    ],
}

# ─────────────────────────────────────────────────────────────────────────
# Risen Dead (Unhallowed)
# ─────────────────────────────────────────────────────────────────────────

THE_RISEN_DEAD = {
    "key": "the risen dead",
    "typeclass": "typeclasses.npc.Npc",
    "desc": (
        "A rotting brute raised by a nethermancer — a grunt of the undead "
        "world, slow but relentless."
    ),
    # AV 4 (Tough 4)
    "tough": 4, "av": 0,
    "body": 3, "bleed_points": 3, "death_points": 3,
    # 1H -> Stagger 1 (2H option would give Cleave/Sunder 1)
    "stagger": 1,
    "cleave": 0, "sunder": 0, "stun": 0, "disarm": 0, "resist": 0,
    "weapon_proto": "IRON_MEDIUM_WEAPON", "weapon_level": 1,
    "is_aggressive": True,
    "art_key": "risen_dead", "tier": 1,
    "special": ["immune_stun", "immune_stagger", "no_vitals",
                "decomposition_x2", "no_dexterity"],
}

WIGHT = {
    "key": "dread wight",
    "typeclass": "typeclasses.npc.Npc",
    "desc": (
        "A corrupted warrior-corpse, swift and cruel, raised by a "
        "nethermancer. Once a notable warrior; now only marginally sentient "
        "and far more vicious."
    ),
    # AV 8 (Tough 8)
    "tough": 8, "av": 0,
    "body": 3, "bleed_points": 3, "death_points": 3,
    # Stagger 2; 2H -> Cleave/Sunder 2
    "stagger": 2, "cleave": 2, "sunder": 2,
    "stun": 0, "disarm": 0, "resist": 0,
    "weapon_proto": "IRON_LARGE_WEAPON", "weapon_level": 2,
    "is_aggressive": True,
    "art_key": "wight", "tier": 2,
    "special": ["immune_stun", "immune_stagger", "no_vitals",
                "decomposition_x2", "dextrous"],
}

REVENANT = {
    "key": "revenant",
    "typeclass": "typeclasses.npc.Npc",
    "desc": (
        "The most dangerous of the risen dead — fast, capable, and "
        "relentless. It can run you down."
    ),
    # AV 12 (Tough 12)
    "tough": 12, "av": 0,
    "body": 3, "bleed_points": 3, "death_points": 3,
    # Stagger 3; 2H -> Cleave/Sunder 3
    "stagger": 3, "cleave": 3, "sunder": 3,
    "stun": 0, "disarm": 0, "resist": 0,
    "weapon_proto": "IRON_LARGE_WEAPON", "weapon_level": 2,
    "is_aggressive": True, "boss_encounter": True,
    "art_key": "revenant", "tier": 3,
    "special": ["immune_stun", "immune_stagger", "no_vitals",
                "decomposition_x2", "dextrous"],
}

UNHALLOWED_SPAWN = {
    "key": "spawn of the unhallowed",
    "typeclass": "typeclasses.npc.Npc",
    "desc": (
        "A lesser raised servant of a nethermancer — it can only be truly "
        "slain by Hallowed (blue-coded) weapons."
    ),
    # AV 8 (Tough 6 + armor 2)
    "tough": 6, "av": 2,
    "body": 3, "bleed_points": 3, "death_points": 3,
    # Stagger 2, Disarm 2 (+ Target Fear 2, carried as special)
    "stagger": 2, "disarm": 2,
    "cleave": 0, "sunder": 0, "stun": 0, "resist": 0,
    "weapon_proto": "IRON_MEDIUM_WEAPON", "weapon_level": 1,
    "is_aggressive": True,
    "art_key": "unhallowed_spawn", "tier": 2,
    "special": ["immune_stun", "immune_disarm", "undead_resilience",
                "target_fear_2", "killable_only_by_hallowed"],
}

# ─────────────────────────────────────────────────────────────────────────
# Nethermancers (boss-encounter framework)
# ─────────────────────────────────────────────────────────────────────────

NETHERMANCER_INITIATE = {
    "key": "nethermancer initiate",
    "typeclass": "typeclasses.npc.Npc",
    "desc": (
        "A lesser dark caster who raises the dead, wards itself behind a "
        "purple barrier, and sows fear among the living."
    ),
    # AV 6 (Tough 6)
    "tough": 6, "av": 0,
    "body": 3, "bleed_points": 3, "death_points": 3,
    # Stun 3, Stagger 3; 2H -> Cleave 3 + Sunder 3
    "stun": 3, "stagger": 3, "cleave": 3, "sunder": 3,
    "disarm": 0, "resist": 0,
    "weapon_proto": "IRON_LARGE_WEAPON", "weapon_level": 2,
    "is_aggressive": True, "boss_encounter": True,
    "art_key": "nethermancer", "tier": 2,
    "special": ["undead_resilience", "staring_into_the_void",
                "nether_ward", "raise_dead"],
}

NETHERMANCER_ACOLYTE = {
    "key": "nethermancer acolyte",
    "typeclass": "typeclasses.npc.Npc",
    "desc": (
        "A stronger dark caster — it paralyzes, drives whole rooms to terror, "
        "and summons a Netherphage to guard it."
    ),
    # AV 8 (Tough 8)
    "tough": 8, "av": 0,
    "body": 3, "bleed_points": 3, "death_points": 3,
    # Stun 4, Stagger 4; 2H -> Cleave 4 + Sunder 4
    "stun": 4, "stagger": 4, "cleave": 4, "sunder": 4,
    "disarm": 0, "resist": 0,
    "weapon_proto": "IRON_LARGE_WEAPON", "weapon_level": 2,
    "is_aggressive": True, "boss_encounter": True,
    "art_key": "necromancer", "tier": 3,
    "special": ["undead_resilience", "sphere_of_terror", "nether_ward",
                "summon_necrophage", "chill_of_the_grave", "no_vitals",
                "mass_fear_1", "target_fear_3", "paralyze_1"],
}

NETHERPHAGE = {
    "key": "netherphage",
    "typeclass": "typeclasses.npc.Npc",
    "desc": (
        "A terrifying summoned bodyguard — it stirs only when its "
        "nethermancer master is threatened, then it does not stop."
    ),
    # AV 12 (Tough 12) — Immune: All (all damage incl. martial skills hits AV)
    "tough": 12, "av": 0,
    "body": 3, "bleed_points": 3, "death_points": 3,
    "stagger": 0, "cleave": 0, "sunder": 0, "stun": 0, "disarm": 0, "resist": 0,
    # 1-2 2H weapons
    "weapon_proto": "IRON_LARGE_WEAPON", "weapon_level": 2,
    "is_aggressive": True, "boss_encounter": True,
    "art_key": "netherphage", "tier": 4,
    "special": ["immune_all", "undead_resilience", "thrall",
                "unhallowed_resurrection", "fresh_meat"],
}


# Registry of every prototype key in this module, for tooling / docs.
BESTIARY_KEYS = [
    "WURDULAC", "WEREWOLF",
    "THE_RISEN_DEAD", "WIGHT", "REVENANT", "UNHALLOWED_SPAWN",
    "NETHERMANCER_INITIATE", "NETHERMANCER_ACOLYTE", "NETHERPHAGE",
]
