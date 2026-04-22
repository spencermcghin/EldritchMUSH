"""
One-shot migration: rename the local-dev tavern from "The Raven's Rest
Tavern" / "Raven & Candle" to "Songbird's Rest", and patch descriptions
on linked rooms + the Elara NPC. Idempotent — safe to run multiple times.

Run locally:
    cd eldritchmush && ../.venv/bin/evennia shell < world/rename_tavern.py

Run on UAT (as superuser, in-game):
    @py exec(open('world/rename_tavern.py').read())
"""
import evennia


def _sub(text, pairs):
    for old, new in pairs:
        text = text.replace(old, new)
    return text


PAIRS = [
    ("The Raven's Rest is", "Songbird's Rest is"),
    ("The Raven's Rest Tavern", "Songbird's Rest"),
    ("Raven's Rest Tavern", "Songbird's Rest"),
    ("Raven & Candle", "Songbird's Rest"),
]

# Rename the tavern room itself.
for r in evennia.search_object("The Raven's Rest Tavern"):
    r.key = "Songbird's Rest"
    if r.db.desc:
        r.db.desc = _sub(r.db.desc, PAIRS)
    print(f"  renamed room → {r.key} (#{r.id})")

# Patch descriptions on every room / NPC that mentions the old tavern
# names. Graveyard stays as "Raven's Rest Graveyard" — PAIRS only targets
# tavern-related phrases so the graveyard is unaffected.
touched = 0
for obj in evennia.search_object(""):
    desc = obj.db.desc
    if not desc:
        continue
    new = _sub(desc, PAIRS)
    if new != desc:
        obj.db.desc = new
        touched += 1
        print(f"  patched desc on {obj.key} (#{obj.id})")

print(f"\nDone. {touched} desc(s) rewritten.")
