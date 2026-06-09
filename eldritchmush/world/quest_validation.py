"""
Quest/world cross-validator.

Quest objectives bind to world entities by case-insensitive substring
match (see commands/quests.py hooks), so a renamed room, a typo'd NPC
key, or an em-dash/hyphen swap silently strands a quest with no error.
This module turns that failure class into a startup warning.

Checks
------
Static (no DB needed):
  - prereq quest keys (and required outcome keys) exist
  - parent/subquests links are symmetric
  - faction names in faction_rep / faction prereqs are canonical
  - reward item prototype keys exist in world.prototypes /
    world.alchemy_prototypes
  - objective dicts are well-formed and use a known type

World (needs a running Evennia / loaded DB):
  - every giver resolves to an NPC in the world (key or alias)
  - kill/deliver/duel/talk targets substring-match at least one
    non-room object key
  - explore targets substring-match at least one room key
  - gather targets match an object key or a prototype key
  - AMBIGUITY: a target that substring-matches more than one distinct
    key is flagged — it will tick on whichever entity fires first

Usage
-----
Runs automatically at server start (server/conf/at_server_startstop.py).
Manual run from the shell:

    python3 -c "import evennia; evennia._init()" ...   # or simpler:
    evennia shell  →  from world.quest_validation import run_and_report
                      run_and_report()
"""

# Canonical faction keys — must match typeclasses/characters.py
# at_object_creation faction_rep initialisation.
FACTIONS = {"crown", "cirque", "rangers", "crows", "outlaws", "outsider"}

OBJECTIVE_TYPES = {"kill", "gather", "deliver", "explore", "duel", "talk"}


def _collect_prototype_keys():
    """Uppercase prototype keys spawnable via evennia.spawn()."""
    keys = set()
    for mod_name in ("world.prototypes", "world.alchemy_prototypes"):
        try:
            import importlib
            mod = importlib.import_module(mod_name)
        except Exception:
            continue
        for attr, val in vars(mod).items():
            if attr.startswith("_") or not isinstance(val, dict):
                continue
            keys.add(attr.upper())
            pk = val.get("prototype_key")
            if pk:
                keys.add(str(pk).upper())
    return keys


def _collect_world_names():
    """Return (rooms, objects) where each is {name_lower: canonical_key}.
    Object names include aliases, all mapping back to the object's
    canonical key so ambiguity counting is per-object, not per-alias."""
    rooms, objects = {}, {}
    try:
        from evennia.objects.models import ObjectDB
    except Exception:
        return None, None
    try:
        for obj in ObjectDB.objects.all():
            key = (obj.db_key or "").lower()
            if not key:
                continue
            path = obj.db_typeclass_path or ""
            if ".rooms." in path:
                rooms[key] = key
            elif ".exits." in path:
                continue
            else:
                objects[key] = key
                try:
                    for alias in obj.aliases.all():
                        if alias:
                            objects[alias.lower()] = key
                except Exception:
                    pass
    except Exception:
        return None, None
    return rooms, objects


def _matches(target, names):
    """Canonical keys the quest engine's substring match would hit.
    `names` maps name_lower -> canonical_key."""
    t = target.lower()
    return sorted({canon for name, canon in names.items() if t in name})


def _iter_objective_sets(qdef):
    """Yield (path_label, objectives_list) for linear + every outcome."""
    if qdef.get("outcomes"):
        for okey, odef in qdef["outcomes"].items():
            yield f"outcome '{okey}'", odef.get("objectives", []) or []
    else:
        yield "objectives", qdef.get("objectives", []) or []


def _iter_faction_maps(qdef):
    if qdef.get("outcomes"):
        for okey, odef in qdef["outcomes"].items():
            yield f"outcome '{okey}'", odef.get("faction_rep", {}) or {}
    yield "top-level", qdef.get("faction_rep", {}) or {}


def _iter_reward_items(qdef):
    if qdef.get("outcomes"):
        for okey, odef in qdef["outcomes"].items():
            for proto in (odef.get("rewards", {}) or {}).get("items", []) or []:
                yield f"outcome '{okey}'", proto
    for proto in (qdef.get("rewards", {}) or {}).get("items", []) or []:
        yield "rewards", proto


def validate_quests(check_world=True):
    """Run all checks. Returns a list of (level, message) where level
    is "ERROR" (content is broken/unreachable) or "WARN" (suspicious).
    """
    from world.quest_data import QUESTS

    issues = []
    err = lambda m: issues.append(("ERROR", m))
    warn = lambda m: issues.append(("WARN", m))

    proto_keys = _collect_prototype_keys()

    # ── Static checks ────────────────────────────────────────────────
    for key, qdef in QUESTS.items():
        where = f"quest '{key}'"
        if qdef.get("key") != key:
            err(f"{where}: dict key != 'key' field ({qdef.get('key')!r})")

        # prereqs
        for prereq in qdef.get("prereqs", []) or []:
            if isinstance(prereq, dict):
                if "faction" in prereq:
                    if prereq["faction"] not in FACTIONS:
                        err(f"{where}: prereq faction {prereq['faction']!r} "
                            f"is not one of {sorted(FACTIONS)}")
                    continue
                pq = prereq.get("quest")
                if pq not in QUESTS:
                    err(f"{where}: prereq quest {pq!r} does not exist")
                elif prereq.get("outcome") and prereq["outcome"] not in (
                        QUESTS[pq].get("outcomes") or {}):
                    err(f"{where}: prereq outcome {prereq['outcome']!r} "
                        f"not an outcome of {pq!r}")
            elif prereq not in QUESTS:
                err(f"{where}: prereq quest {prereq!r} does not exist")

        # parent/subquest symmetry
        for child_key in qdef.get("subquests", []) or []:
            child = QUESTS.get(child_key)
            if not child:
                err(f"{where}: subquest {child_key!r} does not exist")
            elif child.get("parent") != key:
                err(f"{where}: subquest {child_key!r} has parent="
                    f"{child.get('parent')!r}, expected {key!r}")
        parent_key = qdef.get("parent")
        if parent_key:
            parent = QUESTS.get(parent_key)
            if not parent:
                err(f"{where}: parent {parent_key!r} does not exist")
            elif key not in (parent.get("subquests") or []):
                err(f"{where}: parent {parent_key!r} does not list it "
                    f"in subquests")

        # factions
        for label, fmap in _iter_faction_maps(qdef):
            for faction in fmap:
                if faction not in FACTIONS:
                    err(f"{where} {label}: faction {faction!r} is not one "
                        f"of {sorted(FACTIONS)} — rep delta would apply "
                        f"to a phantom faction")

        # reward prototypes
        for label, proto in _iter_reward_items(qdef):
            if str(proto).upper() not in proto_keys:
                err(f"{where} {label}: reward prototype {proto!r} not "
                    f"found — spawn() will silently grant nothing")

        # objective shape
        for label, objectives in _iter_objective_sets(qdef):
            if not objectives and not qdef.get("subquests"):
                warn(f"{where} {label}: no objectives (quest can never "
                     f"complete)")
            for obj in objectives:
                otype = obj.get("type")
                if otype not in OBJECTIVE_TYPES:
                    err(f"{where} {label}: unknown objective type "
                        f"{otype!r} (known: {sorted(OBJECTIVE_TYPES)})")
                if not obj.get("target"):
                    err(f"{where} {label}: objective missing target")
                if not obj.get("qty"):
                    err(f"{where} {label}: objective missing/zero qty")
                tgt = (obj.get("target") or "")
                if len(tgt) <= 3:
                    warn(f"{where} {label}: target {tgt!r} is very short "
                         f"— substring matching may over-match")

        # giver
        if not qdef.get("parent") and not (qdef.get("giver") or "").strip():
            err(f"{where}: no giver (quest can never be offered)")

    # ── World checks (need DB) ───────────────────────────────────────
    if check_world:
        rooms, objects = _collect_world_names()
        if rooms is None:
            warn("world checks skipped — Evennia DB not available")
            return issues
        for key, qdef in QUESTS.items():
            where = f"quest '{key}'"
            giver = (qdef.get("giver") or "").lower()
            if giver and giver not in objects:
                err(f"{where}: giver {giver!r} matches no object key or "
                    f"alias in the world — quest is unobtainable")
            for label, objectives in _iter_objective_sets(qdef):
                for obj in objectives:
                    tgt = obj.get("target") or ""
                    otype = obj.get("type")
                    if not tgt or otype not in OBJECTIVE_TYPES:
                        continue
                    if obj.get("synthetic"):
                        # Ticked by scripted hooks (puzzle CmdSets etc.),
                        # not by a real-world entity match.
                        continue
                    if otype == "explore":
                        hits = _matches(tgt, rooms)
                        kind = "room"
                    elif otype == "gather":
                        hits = _matches(tgt, objects)
                        if not hits and tgt.upper().replace(" ", "_") in proto_keys:
                            hits = ["<prototype>"]
                        kind = "item"
                    else:  # kill / deliver / duel / talk
                        hits = _matches(tgt, objects)
                        kind = "npc"
                    if not hits:
                        err(f"{where}: {otype} target {tgt!r} matches no "
                            f"{kind} in the world — objective can never "
                            f"tick")
                    elif len(hits) > 1 and "<prototype>" not in hits:
                        warn(f"{where}: {otype} target {tgt!r} matches "
                             f"{len(hits)} distinct objects {hits[:4]} — "
                             f"may tick on the wrong entity")
    return issues


def run_and_report(check_world=True, out=print):
    """Run validation and print a human-readable report. Returns the
    number of ERROR-level issues."""
    try:
        issues = validate_quests(check_world=check_world)
    except Exception as exc:
        out(f"[quest_validation] validator crashed: {exc!r}")
        return 0
    errors = [m for lvl, m in issues if lvl == "ERROR"]
    warns = [m for lvl, m in issues if lvl == "WARN"]
    if not issues:
        out("[quest_validation] OK — all quest content cross-checks pass.")
        return 0
    out(f"[quest_validation] {len(errors)} error(s), {len(warns)} "
        f"warning(s):")
    for m in errors:
        out(f"  ERROR: {m}")
    for m in warns:
        out(f"  WARN:  {m}")
    return len(errors)
