"""
Effect-text lookup for items in the shop UI.

Everything else about each item (name, price, materials, level,
craft_source, damage, slot, etc.) already lives in world/prototypes.py.
This module only fills the one gap: the descriptive "Item Effect"
text from the Schematics and Items Cost Master spreadsheet, which the
prototypes don't carry.

Used by server/conf/inputfuncs.py's __shop_ui__ handler to enrich
the shop payload with `effect` text so the ShopModal can render it
alongside prototype data.

Data source: world/schematics_master.csv (copy of the Drive master).
"""
import csv
import os
import re

_CSV_PATH = os.path.join(os.path.dirname(__file__), "schematics_master.csv")


def _normalize(name):
    """Lowercase, drop parentheticals, collapse whitespace, strip non-alphanum."""
    if not name:
        return ""
    s = re.sub(r"\([^)]*\)", "", name).strip().lower()
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _load_effects():
    effects = {}
    if not os.path.exists(_CSV_PATH):
        return effects
    with open(_CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("") or row.get(None) or "").strip()
            effect = (row.get("Item Effect") or "").strip()
            if not name or not effect:
                continue
            key = _normalize(name)
            if key:
                effects[key] = effect
    return effects


# Module-level cache — loaded once at import.
_EFFECT_BY_NAME = _load_effects()


# Common aliases where prototype keys differ slightly from CSV titles.
_ALIASES = {
    "iron small weapon": "iron small and throwing weapons",
    "iron medium weapon": "iron medium weapons",
    "iron large weapon": "iron large weapons",
    "iron coat of plates": "iron scalemail coat of plates",
    "chirurgeon kit": "chirurgeon's kit",
    "duelist gloves": "duelist's gloves",
    "highwayman cloak": "highwayman's cloak",
}


def _translate_effect(text):
    """Rewrite tabletop-LARP timing language for the always-on MUSH.

    The CSV is a tabletop reference where benefits proc 'at check-in'
    (start of an event session) and refresh per event. In our MUSH
    those map to a real-time daily refresh.
    """
    if not text:
        return text
    replacements = [
        ("at check-in", "once per day"),
        ("Check-in", "Daily refresh"),
        ("check-in", "daily refresh"),
        ("per event", "per day"),
        ("once per refresh", "once per day"),
        ("per skill refresh", "per day"),
        ("per refresh", "per day"),
    ]
    out = text
    for old, new in replacements:
        out = out.replace(old, new)
    return out


def get_effect(name):
    """Return the CSV Item Effect text for a given item name, or "".

    Tolerates variant prototype spellings — "Iron Small Weapon" matches
    "Iron Small and Throwing Weapons", etc. Tabletop "check-in" /
    "per event" / "per refresh" timing is rewritten to "per day" for
    the always-on MUSH.
    """
    norm = _normalize(name)
    raw = _EFFECT_BY_NAME.get(norm)
    if not raw:
        target = _ALIASES.get(norm)
        if target:
            raw = _EFFECT_BY_NAME.get(target, "")
    return _translate_effect(raw or "")
