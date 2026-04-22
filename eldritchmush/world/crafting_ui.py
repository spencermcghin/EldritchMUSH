"""
world/crafting_ui.py — Shared logic for the unified crafting modal.

Enumerates prototypes from world.prototypes + world.alchemy_prototypes,
buckets them by craft_source, and exposes two entry points used by the
OOB handlers in server/conf/inputfuncs.py:

    build_payload(puppet)           → dict for the `crafting_data` event
    craft_item(puppet, recipe_key)  → (ok, main_msg, broadcast_msg)

One tab per craft_source the character has the skill for (superuser sees
all). Each tab reports station + kit readiness separately so the modal
can render disabled-state reasons. Recipe gating:

    - Known recipes only (puppet.db.known_recipes); superuser bypass.
    - Skill level ≥ recipe.level.
    - Matching station in room.
    - Matching kit equipped with uses > 0.
    - Required materials / reagents present.
"""

import inspect as _inspect
import time as _time

from evennia import spawn as ev_spawn
from world import prototypes as _protos
from world import alchemy_prototypes as _apmod


# The three generic crafter workbench typeclasses are treated as
# interchangeable for bowyer / artificer / gunsmith — a single workbench
# in a room is enough for any of those three skills.
_WORKBENCH_STATIONS = ("BowyerWorkbench", "ArtificerWorkbench", "GunsmithWorkbench")

# craft_source → (skill_attr, kit_type, station_class_names, tab_label)
# station_class_names is a tuple — any matching typeclass in the room
# counts as a valid station.
CRAFT_SOURCES = {
    "blacksmith": ("blacksmith", "blacksmith", ("Forge",),                "Blacksmith"),
    "bowyer":     ("bowyer",     "bowyer",     _WORKBENCH_STATIONS,       "Bowyer"),
    "artificer":  ("artificer",  "artificer",  _WORKBENCH_STATIONS,       "Artificer"),
    "gunsmith":   ("gunsmith",   "gunsmith",   _WORKBENCH_STATIONS,       "Gunsmith"),
    "apothecary": ("alchemist",  "apothecary", ("ApothecaryWorkbench",),  "Alchemy"),
}

MATERIAL_FIELDS = ("iron_ingots", "refined_wood", "leather", "cloth")


def _collect_prototypes():
    """Return {craft_source: {PROTO_KEY: proto_dict}} for all modules."""
    out = {cs: {} for cs in CRAFT_SOURCES}
    for name, obj in _inspect.getmembers(_protos):
        if not isinstance(obj, dict):
            continue
        cs = obj.get("craft_source")
        if cs in out:
            out[cs][name.upper()] = obj
    for name, obj in _inspect.getmembers(_apmod):
        if isinstance(obj, dict) and obj.get("craft_source") == "apothecary":
            out["apothecary"][name.upper()] = obj
    return out


def _room_has_station(puppet, station_class_names):
    """station_class_names may be a string or an iterable of strings."""
    if isinstance(station_class_names, str):
        station_class_names = (station_class_names,)
    loc = getattr(puppet, "location", None)
    if not loc:
        return False
    wanted = {"." + n for n in station_class_names}
    for obj in loc.contents:
        tcp = getattr(obj, "typeclass_path", "") or ""
        if any(tcp.endswith(w) for w in wanted):
            return True
    return False


def _equipped_kit(puppet, kit_type):
    kit_slot = getattr(puppet.db, "kit_slot", []) or []
    kit = kit_slot[0] if kit_slot else None
    if not kit:
        return None, False
    if getattr(kit.db, "type", None) != kit_type:
        return kit, False
    ready = (getattr(kit.db, "uses", 0) or 0) > 0
    return kit, ready


def _known_keys(puppet):
    raw = puppet.db.known_recipes
    # Evennia wraps collections in SaverSet/SaverList — accept anything
    # iterable, not just a bare `set`.
    if raw is None:
        return set(), set()
    try:
        iter(raw)
    except TypeError:
        return set(), set()
    upper = {str(k).upper() for k in raw}
    lower_names = {str(k).lower() for k in raw}
    return upper, lower_names


def _is_superuser(puppet):
    acc = getattr(puppet, "account", None)
    return bool(acc and getattr(acc, "is_superuser", False))


def _recipe_entry(cs, proto_key, proto, puppet, skill_level, station_and_kit_ok):
    level = proto.get("level", 0) or 0
    name = proto.get("key", proto_key)

    materials = []
    if cs == "apothecary":
        reagents_inv = puppet.db.reagents or {}
        for i in range(1, 6):
            rn = proto.get(f"reagent_{i}")
            rq = proto.get(f"reagent_{i}_qty", 0) or 0
            if rn and rq > 0:
                materials.append({
                    "name": rn,
                    "qty": rq,
                    "have": reagents_inv.get(rn, 0),
                })
    else:
        for mf in MATERIAL_FIELDS:
            qty = proto.get(mf, 0) or 0
            if qty > 0:
                materials.append({
                    "name": mf,
                    "qty": qty,
                    "have": getattr(puppet.db, mf, 0) or 0,
                })

    can = (
        skill_level >= level
        and station_and_kit_ok
        and all(m["have"] >= m["qty"] for m in materials)
    )

    entry = {
        "key": proto_key,
        "name": name,
        "level": level,
        "materials": materials,
        "canCraft": can,
        "qtyProduced": proto.get("qty_produced", 1) or 1,
    }
    if cs == "apothecary":
        entry["substanceType"] = (proto.get("substance_type") or "").capitalize()
        entry["effect"] = proto.get("effect", "")
    return entry


def build_payload(puppet):
    """Build the crafting_data OOB kwargs for this puppet."""
    all_protos = _collect_prototypes()
    known_upper, known_lower = _known_keys(puppet)
    is_su = _is_superuser(puppet)

    tabs = []
    for cs, (skill_attr, kit_type, station_cls, label) in CRAFT_SOURCES.items():
        skill_level = getattr(puppet.db, skill_attr, 0) or 0
        if skill_level <= 0 and not is_su:
            continue

        station_present = _room_has_station(puppet, station_cls)
        _kit, kit_ready = _equipped_kit(puppet, kit_type)

        protos = all_protos.get(cs, {})
        if is_su:
            recipe_keys = set(protos.keys())
        else:
            recipe_keys = {k for k in protos if k in known_upper}
            # Fallback: match by display name (legacy alchemy entries).
            for rk, rp in protos.items():
                if rk in recipe_keys:
                    continue
                if (rp.get("key") or "").lower() in known_lower:
                    recipe_keys.add(rk)

        ok_env = station_present and kit_ready
        recipes = [
            _recipe_entry(cs, rk, protos[rk], puppet, skill_level, ok_env)
            for rk in sorted(recipe_keys)
        ]

        tabs.append({
            "id": cs,
            "label": label,
            "skillLevel": skill_level,
            "kitType": kit_type,
            "hasKit": kit_ready,
            "stationPresent": station_present,
            "recipes": recipes,
        })

    materials_inv = {mf: (getattr(puppet.db, mf, 0) or 0) for mf in MATERIAL_FIELDS}
    reagents_inv = {k: v for k, v in (puppet.db.reagents or {}).items() if v > 0}

    return {
        "type": "crafting_data",
        "_ts": _time.time(),
        "tabs": tabs,
        "materials": materials_inv,
        "reagents": reagents_inv,
    }


def craft_item(puppet, recipe_key):
    """Validate + craft. Returns (ok, main_msg, broadcast_msg)."""
    recipe_key = (recipe_key or "").strip().upper()
    if not recipe_key:
        return False, "|430No recipe specified.|n", ""

    all_protos = _collect_prototypes()
    cs = None
    proto = None
    for source, protos in all_protos.items():
        if recipe_key in protos:
            cs = source
            proto = protos[recipe_key]
            break
    if not proto:
        return False, f"|400Unknown recipe: {recipe_key}|n", ""

    skill_attr, kit_type, station_cls, label = CRAFT_SOURCES[cs]
    is_su = _is_superuser(puppet)

    skill_level = getattr(puppet.db, skill_attr, 0) or 0
    req_level = proto.get("level", 0) or 0
    if not is_su:
        if skill_level <= 0:
            return False, f"|400You do not have the {label} skill.|n", ""
        if skill_level < req_level:
            return False, (
                f"|400Your {label} skill (level {skill_level}) is too low; "
                f"recipe requires level {req_level}.|n"
            ), ""

    if not is_su:
        known_upper, known_lower = _known_keys(puppet)
        if recipe_key not in known_upper and (proto.get("key") or "").lower() not in known_lower:
            return False, "|400You don't know this recipe.|n", ""

    if not is_su and not _room_has_station(puppet, station_cls):
        return False, f"|430You need a {label} station to craft this.|n", ""

    kit, kit_ready = _equipped_kit(puppet, kit_type)
    if not is_su:
        if not kit or getattr(kit.db, "type", None) != kit_type:
            return False, f"|430You need a {label} kit equipped.|n", ""
        if not kit_ready:
            return False, f"|400Your {kit.key} is out of uses.|n", ""

    # Consume
    if cs == "apothecary":
        reagents = puppet.db.reagents or {}
        required = {}
        for i in range(1, 6):
            rn = proto.get(f"reagent_{i}")
            rq = proto.get(f"reagent_{i}_qty", 0) or 0
            if rn and rq > 0:
                required[rn] = required.get(rn, 0) + rq
        missing = [
            f"{n} (need {q}, have {reagents.get(n, 0)})"
            for n, q in required.items()
            if reagents.get(n, 0) < q
        ]
        if missing and not is_su:
            return False, "|400Missing reagents: " + ", ".join(missing) + "|n", ""
        if not is_su:
            for n, q in required.items():
                reagents[n] = reagents.get(n, 0) - q
            puppet.db.reagents = reagents
    else:
        required = {mf: (proto.get(mf, 0) or 0) for mf in MATERIAL_FIELDS}
        required = {mf: q for mf, q in required.items() if q > 0}
        missing = []
        for mf, q in required.items():
            have = getattr(puppet.db, mf, 0) or 0
            if have < q:
                missing.append(f"{mf.replace('_', ' ')} (need {q}, have {have})")
        if missing and not is_su:
            return False, "|400Missing materials: " + ", ".join(missing) + "|n", ""
        if not is_su:
            for mf, q in required.items():
                setattr(puppet.db, mf, (getattr(puppet.db, mf, 0) or 0) - q)

    if kit and not is_su:
        try:
            kit.db.uses = max(0, (kit.db.uses or 0) - 1)
        except Exception:
            pass

    qty = proto.get("qty_produced", 1) or 1
    name = proto.get("key", recipe_key)
    for _ in range(qty):
        items = ev_spawn(proto)
        if items:
            items[0].move_to(puppet, quiet=True)

    if cs == "apothecary":
        dose = "dose" if qty == 1 else "doses"
        msg = f"|230You carefully brew {qty} {dose} of |430{name}|230.|n"
        bcast = (
            f"|230{puppet.key} works carefully over their apothecary kit, "
            f"producing a batch of {name}.|n"
        )
    else:
        verb = "forge" if cs == "blacksmith" else "craft"
        if qty > 1:
            msg = f"|gYou {verb} {qty} x |w{name}|g.|n"
        else:
            msg = f"|gYou {verb} a |w{name}|g.|n"
        bcast = f"|025{puppet.key} {verb}s {name}.|n"

    return True, msg, bcast
