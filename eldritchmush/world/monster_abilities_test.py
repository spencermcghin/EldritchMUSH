"""
monster_abilities_test.py — verifies world/monster_abilities.py wiring.

Run from the eldritchmush/ dir against the live DB:

    ../.venv/bin/evennia shell -c "exec(open('world/monster_abilities_test.py').read())"

Spawns throwaway NPCs (a flagged one per ability + a flagless control),
exercises the helpers, asserts behaviour, then deletes everything it made.
Prints PASS/FAIL per case and a final summary. No network; in-process only.

This file is a manual test helper, not imported by the game.
"""

import traceback
from evennia import create_object

from world import monster_abilities as ma

_results = []


def _check(name, ok, detail=""):
    _results.append((name, bool(ok), detail))
    flag = "PASS" if ok else "FAIL"
    print(f"[{flag}] {name}" + (f" — {detail}" if detail else ""))


def _mk(key, special=None, **db):
    npc = create_object("typeclasses.npc.Npc", key=key)
    npc.db.special = list(special or [])
    for k, v in db.items():
        npc.attributes.add(k, v)
    return npc


created = []
try:
    # Control NPC with NO special flags.
    control = _mk("ctrl-dummy", special=[], tough=4, av=4, body=3,
                  total_body=3, bleed_points=3)
    created.append(control)

    # --- Immunities -------------------------------------------------------
    for man in ("stun", "stagger", "disarm", "sunder"):
        flagged = _mk(f"imm-{man}", special=[f"immune_{man}"])
        created.append(flagged)
        _check(f"immune_{man}: flagged is immune",
               ma.is_immune(flagged, man) is True)
        _check(f"immune_{man}: control is NOT immune",
               ma.is_immune(control, man) is False)

    ranged = _mk("imm-ranged", special=["immune_ranged"])
    created.append(ranged)
    _check("immune_ranged: shoot blocked", ma.is_immune(ranged, "shoot") is True)
    _check("immune_ranged: strike NOT blocked",
           ma.is_immune(ranged, "strike") is False)
    _check("control: shoot NOT blocked", ma.is_immune(control, "shoot") is False)

    # immune_all — control verbs fizzle, damage verbs land.
    allimm = _mk("imm-all", special=["immune_all"])
    created.append(allimm)
    _check("immune_all: stun fizzles", ma.is_immune(allimm, "stun") is True)
    _check("immune_all: sunder fizzles", ma.is_immune(allimm, "sunder") is True)
    _check("immune_all: strike LANDS (not blocked)",
           ma.is_immune(allimm, "strike") is False)
    _check("immune_all: shoot LANDS (no immune_ranged)",
           ma.is_immune(allimm, "shoot") is False)
    _check("immune_all: cleave LANDS", ma.is_immune(allimm, "cleave") is False)

    # --- Regeneration -----------------------------------------------------
    regen = _mk("regen-lesser", special=["lesser_regeneration"],
                tough=4, av=4, body=3, total_body=3, bleed_points=3)
    created.append(regen)
    # Turn 1 at full tough establishes the regen cap (=4), mirroring real
    # combat where the monster starts undamaged.
    ma.apply_regen(regen)
    regen.db.tough = 1   # then took 3 tough damage (e.g. from sunder)
    regen.db.av = 1
    healed = ma.apply_regen(regen)
    _check("lesser_regeneration: heals +1 tough",
           healed == 1 and regen.db.tough == 2,
           f"healed={healed} tough={regen.db.tough}")
    # Cap: cannot exceed starting tough (cached cap = 4).
    regen.db.tough = 4
    capped = ma.apply_regen(regen)
    _check("lesser_regeneration: capped at start tough",
           capped == 0 and regen.db.tough == 4,
           f"healed={capped} tough={regen.db.tough}")
    # Killing condition: bleeding-out monster does not regen.
    regen.db.tough = 1
    regen.db.bleed_points = 0
    downed = ma.apply_regen(regen)
    _check("regeneration: no regen while bleeding out",
           downed == 0 and regen.db.tough == 1, f"healed={downed}")

    lycan = _mk("regen-lycan", special=["lycan_regeneration"],
                tough=10, av=10, bleed_points=3)
    created.append(lycan)
    ma.apply_regen(lycan)   # establish cap at 10
    lycan.db.tough = 5
    lh = ma.apply_regen(lycan)
    _check("lycan_regeneration: heals +2 tough",
           lh == 2 and lycan.db.tough == 7, f"healed={lh}")

    # Control NPC never regenerates.
    control.db.tough = 1
    cr = ma.apply_regen(control)
    _check("control: no regen", cr == 0 and control.db.tough == 1)

    # --- Fear -------------------------------------------------------------
    room = create_object("typeclasses.rooms.Room", key="ma-test-room")
    created.append(room)
    player = create_object("typeclasses.characters.Character", key="ma-test-pc")
    created.append(player)
    player.db.fear = False

    tfear = _mk("fear-target", special=["target_fear_2"])
    created.append(tfear)
    tfear.location = room
    player.location = room
    feared = ma.apply_fear(tfear, player, room)
    _check("target_fear_2: target gains db.fear",
           player.db.fear is True and player in feared)

    # Scope resolution (mass/sphere) — account-agnostic.
    mfear = _mk("fear-mass", special=["mass_fear_1"])
    created.append(mfear)
    _check("mass_fear_1: resolves to room scope",
           ma.fear_scope(mfear) == ("room", 1), f"scope={ma.fear_scope(mfear)}")
    sphere = _mk("fear-sphere", special=["sphere_of_terror", "target_fear_3"])
    created.append(sphere)
    _check("sphere_of_terror beats target_fear: room scope wins",
           ma.fear_scope(sphere)[0] == "room")

    # Control: no fear flag -> no fear, returns [].
    player.db.fear = False
    cf = ma.apply_fear(control, player, room)
    _check("control: no fear applied", cf == [] and player.db.fear is False)

except Exception:
    print("EXCEPTION during test:")
    traceback.print_exc()
finally:
    for obj in created:
        try:
            obj.delete()
        except Exception:
            pass

passed = sum(1 for _, ok, _ in _results if ok)
total = len(_results)
print("\n==== monster_abilities test summary ====")
print(f"{passed}/{total} checks passed")
if passed != total:
    print("FAILURES:")
    for name, ok, detail in _results:
        if not ok:
            print(f"  - {name} {detail}")
