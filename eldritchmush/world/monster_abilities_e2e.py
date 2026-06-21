"""
End-to-end: spawn a real bestiary monster and drive the actual combat
commands at it to confirm the in-command immunity hooks fire (not just the
helper functions).

    ../.venv/bin/evennia shell -c "exec(open('world/monster_abilities_e2e.py').read())"
"""
import traceback
from evennia import create_object
from evennia.prototypes.spawner import spawn

results = []
def chk(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

created = []
msgs = []
try:
    room = create_object("typeclasses.rooms.Room", key="e2e-room")
    created.append(room)

    # A capturing PC stand-in.
    pc = create_object("typeclasses.characters.Character", key="e2e-pc")
    created.append(pc)
    pc.location = room
    # capture broadcasts the room sends
    orig = room.msg_contents
    def cap(text="", **kw):
        try:
            msgs.append(str(text))
        except Exception:
            pass
        return orig(text, **kw)
    room.msg_contents = cap

    # Give the PC combat skills + a weapon so maneuvers are usable.
    for k in ("stun", "stagger", "disarm", "sunder", "cleave"):
        pc.attributes.add(k, 3)
    pc.db.master_of_arms = 5  # bias rolls to hit
    pc.db.combat_turn = 1
    pc.db.in_combat = 0

    # Spawn the WEREWOLF (immune_ranged/sunder/disarm/stun + lycan_regen).
    wolf = spawn("WEREWOLF")[0]
    created.append(wolf)
    wolf.location = room
    wolf.db.is_aggressive = False  # don't let it auto-attack during the test

    from world import monster_abilities as ma
    chk("WEREWOLF carries immune_stun", ma.is_immune(wolf, "stun"))
    chk("WEREWOLF carries immune_disarm", ma.is_immune(wolf, "disarm"))
    chk("WEREWOLF carries immune_sunder", ma.is_immune(wolf, "sunder"))
    chk("WEREWOLF carries immune_ranged (shoot)", ma.is_immune(wolf, "shoot"))
    chk("WEREWOLF NOT immune to strike", not ma.is_immune(wolf, "strike"))
    chk("WEREWOLF carries a regen flag",
        "lycan_regeneration" in (wolf.db.special or []))

    # Drive a real `stun` command at the wolf and look for the fizzle line.
    msgs.clear()
    pc.db.combat_turn = 1
    pc.execute_cmd(f"stun {wolf.key}")
    fizzled = any("cannot be" in m or "shrugs off" in m for m in msgs)
    chk("stun command fizzles vs WEREWOLF (in-command hook fired)", fizzled,
        f"msgs={[m[:60] for m in msgs[-3:]]}")

    # Control: a vanilla aggressive NPC with no flags should NOT fizzle stun.
    grunt = create_object("typeclasses.npc.Npc", key="e2e-grunt")
    created.append(grunt)
    grunt.location = room
    grunt.db.special = []
    grunt.db.bleed_points = 3
    msgs.clear()
    # reset PC turn (combat loop may have toggled it)
    for c in (pc, grunt, wolf):
        c.db.in_combat = 0
        c.db.combat_turn = 1
    if wolf in (room.db.combat_loop or []):
        room.db.combat_loop.clear()
    pc.execute_cmd(f"stun {grunt.key}")
    control_fizzled = any("cannot be" in m or "shrugs off" in m for m in msgs)
    chk("stun on flagless grunt does NOT fizzle (control unaffected)",
        not control_fizzled, f"msgs={[m[:60] for m in msgs[-4:]]}")

except Exception:
    print("EXCEPTION:")
    traceback.print_exc()
finally:
    for o in created:
        try:
            o.delete()
        except Exception:
            pass

passed = sum(1 for _, ok, _ in results if ok)
print(f"\n==== e2e summary: {passed}/{len(results)} passed ====")
for n, ok, d in results:
    if not ok:
        print(f"  FAIL {n} {d}")
