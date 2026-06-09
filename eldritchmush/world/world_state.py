"""
World-level state — shared flags and faction-standing helpers.

Everything in the quest system so far is per-character. These helpers
give event content two MUSH-native levers:

1. World flags — server-wide booleans/values stored in Evennia's
   ServerConfig (survive reloads, shared by every player). Use them for
   shared consequences: the first party that resolves an encounter one
   way changes what everyone else finds.

       from world.world_state import get_flag, set_flag
       if not get_flag("butcher_hovel_burned"):
           set_flag("butcher_hovel_burned", True)
           # ...swap room desc, despawn the Butcher, etc.

2. Faction standing tiers — a canonical mapping from raw faction_rep
   integers to named tiers, so content (pricing, dialogue tone, quest
   gates) keys off shared thresholds instead of ad-hoc numbers.
   Quest-side gating uses the faction prereq form directly:

       "prereqs": [{"faction": "crown", "min": 5}]      # friendly+
       "prereqs": [{"faction": "crows", "max": -3}]     # crows hate you
"""

_FLAG_PREFIX = "world_flag_"

# (threshold, tier) — first tier whose threshold <= rep wins, scanning
# from the top. Keep in sync with any frontend display of standing.
FACTION_TIERS = [
    (10, "honored"),
    (3, "friendly"),
    (-2, "neutral"),
    (-9, "unfriendly"),
    (-10**9, "hostile"),
]


def get_flag(name, default=None):
    """Read a world flag. Returns `default` when unset."""
    try:
        from evennia.server.models import ServerConfig
        value = ServerConfig.objects.conf(_FLAG_PREFIX + name)
        return default if value is None else value
    except Exception:
        return default


def set_flag(name, value):
    """Set a world flag (any pickleable value; None deletes)."""
    from evennia.server.models import ServerConfig
    if value is None:
        ServerConfig.objects.conf(_FLAG_PREFIX + name, delete=True)
    else:
        ServerConfig.objects.conf(_FLAG_PREFIX + name, value)


def all_flags():
    """Return {name: value} for every set world flag (admin tooling)."""
    out = {}
    try:
        from evennia.server.models import ServerConfig
        for conf in ServerConfig.objects.all():
            key = conf.db_key or ""
            if key.startswith(_FLAG_PREFIX):
                out[key[len(_FLAG_PREFIX):]] = ServerConfig.objects.conf(key)
    except Exception:
        pass
    return out


def faction_rep(char, faction):
    """Raw faction rep int for a character (0 when unset)."""
    try:
        return int((char.db.faction_rep or {}).get(faction, 0))
    except Exception:
        return 0


def faction_tier(char, faction):
    """Return (rep_int, tier_name) for a character's faction standing."""
    rep = faction_rep(char, faction)
    for threshold, tier in FACTION_TIERS:
        if rep >= threshold:
            return rep, tier
    return rep, "hostile"
