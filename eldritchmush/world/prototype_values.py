"""
Read fields off an Evennia prototype, normalized or raw.

Evennia homogenizes module prototypes at registration: every key that is not
reserved (key / aliases / typeclass / prototype_*) is moved into an `attrs`
list of (name, value, category, lockstring) tuples. So a prototype that reads
like this in world/prototypes.py:

    IRON_COAT_OF_PLATES = {
        "key": "Iron Coat of Plates",
        "craft_source": "blacksmith",
        "level": 0,
        "iron_ingots": 2,
        "material_value": 3,
    }

comes back from `prototypes.search_prototype()` with NONE of those readable at
the top level:

    proto.get("iron_ingots")   -> None
    proto["attrs"]             -> [("craft_source", "blacksmith", None, ""),
                                   ("iron_ingots", 2, None, ""), ...]

Code that reads the searched prototype with a plain `.get()` therefore sees 0
or "" for every game value. That silently broke three separate systems: shop
buy prices (everything cost 1 silver), forge material costs (everything was
free) and repair (`material_value` None, so nothing could be repaired).

Use `proto_value()` for anything read off a prototype that may have come from
`search_prototype()`. Raw dicts imported straight from world/prototypes.py
still work — the top-level lookup is tried first.
"""


def proto_value(proto, name, default=0):
    """Return `proto[name]`, looking inside a normalized `attrs` list too."""
    if not proto:
        return default

    try:
        if name in proto:
            return proto[name]
    except TypeError:
        return default

    for entry in proto.get("attrs") or []:
        try:
            if entry[0] == name:
                return entry[1]
        except (IndexError, TypeError, KeyError):
            continue

    return default


def proto_int(proto, name, default=0):
    """proto_value() coerced to int, tolerating None/'' /bad values."""
    value = proto_value(proto, name, default)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def proto_str(proto, name, default=""):
    """proto_value() coerced to a stripped string."""
    value = proto_value(proto, name, default)
    if value is None:
        return default
    return str(value).strip()


def prototype_key_candidates(obj):
    """Candidate prototype keys for a spawned object, best guess first.

    Several commands re-derive an item's prototype from its display key with
    `key.lower().replace(" ", "_")`. That breaks on any key containing
    punctuation: "Chirurgeon's Kit" becomes "chirurgeon's_kit", which matches
    no prototype, and callers that swallow the resulting KeyError then do
    nothing at all — silently. That single mismatch disabled every healing
    command, because they all gate on an equipped chirurgeon's kit.
    """
    candidates = []

    # Evennia records the prototype an object was spawned from; trust it first.
    for attr in ("prototype_key", "prototype"):
        try:
            value = obj.attributes.get(attr, default=None)
        except Exception:
            value = None
        if value and isinstance(value, str):
            candidates.append(value)

    key = getattr(obj, "key", "") or ""
    lowered = key.lower()
    base = lowered.replace(" ", "_")
    candidates.append(base)

    # Drop apostrophes entirely: "chirurgeon's_kit" -> "chirurgeons_kit".
    stripped = base.replace("'", "").replace("’", "")
    candidates.append(stripped)

    # Drop the possessive 's': "chirurgeon's_kit" -> "chirurgeon_kit".
    depossessed = base.replace("'s", "").replace("’s", "")
    candidates.append(depossessed)

    # Keep only word characters, collapsing anything else to an underscore.
    cleaned = "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in base)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    candidates.append(cleaned.strip("_"))

    seen = set()
    ordered = []
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            ordered.append(candidate)
    return ordered


def find_prototype(obj, search_prototype):
    """Resolve the prototype dict for a spawned object, or None.

    `search_prototype` is passed in so this module stays import-light.
    Tries each candidate key, preferring an exact prototype_key match.
    """
    for candidate in prototype_key_candidates(obj):
        try:
            results = search_prototype(candidate)
        except Exception:
            results = None
        if not results:
            continue
        wanted = candidate.upper()
        for proto in results:
            if str(proto.get("prototype_key", "")).upper() == wanted:
                return proto
        return results[0]
    return None
