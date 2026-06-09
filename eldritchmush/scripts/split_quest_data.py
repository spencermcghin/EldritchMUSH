"""One-shot refactor: split world/quest_data.py into per-event modules.

Reads the monolithic QUESTS dict, slices it at the per-event section
banners, writes world/quests/<event>.py modules plus an aggregating
__init__.py, rewrites quest_data.py as a compat shim, then verifies the
merged dict is byte-identical (same keys, same values) to the original.

Run from eldritchmush/:  python3 scripts/split_quest_data.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "world", "quest_data.py")
PKG = os.path.join(ROOT, "world", "quests")

# (module_name, banner_regex_that_starts_the_section, provenance_header)
SECTIONS = [
    ("event1_walkins",
     r"EVENT 1 — WALK-INS",
     "Event 1 — Relaunch / Friday Night walk-ins (Ship, Cirque, Noble, "
     "Explorer, Chain Gang) + rescue chain.\n"
     "Source: Drive / Reboot / Event 1 - Relaunch "
     "(folder 1MSWywuW2ZnzJVkYOFmUXoCIRd-vTGOAq)."),
    ("event1_saturday",
     r"EVENT 1 — SATURDAY ARC",
     "Event 1 — Relaunch / Saturday tutorials + investigations.\n"
     "Source: Drive / Reboot / Event 1 - Relaunch / Saturday Morning, "
     "Afternoon, Night (folder 1MSWywuW2ZnzJVkYOFmUXoCIRd-vTGOAq)."),
    ("event2_wrath",
     r"EVENT 2 — THE WRATH",
     "Event 2 — The Wrath (Friday Night + Saturday anchors).\n"
     "Source: Drive / Reboot / Event 2 - The Wrath "
     "(folder 1jxlA_zorcovQrAyMYU3paeNR6-m0pCl8)."),
    ("event5_trial",
     r"EVENT 5 .*TRIAL|Event 5 / \"Prologue: The Trial\"",
     "Event 5 — The Trial (partial: grizzled veteran prologue).\n"
     "Source: Drive / Reboot / Event 5 - The Trial "
     "(folder 1YqBD3cm5Y9swi4XqCMmMNh8I5ejf6QMs)."),
    ("event4_sacrifice",
     r"EVENT 4 .*SACRIFICE|Event 4 / \"Prologue: The Sacrifice\"",
     "Event 4 — The Sacrifice (prologue).\n"
     "Source: Drive / Reboot / Event 4 - The Sacrifice "
     "(folder 1Q1OvO_xXKvJgswfBTb4s0ZoZQchNxDRb)."),
    ("event3_awakening",
     r"EVENT 3 .*AWAKENING|Event 3 / \"Chapter III",
     "Event 3 — The Awakening (Chapter III).\n"
     "Source: Drive / Reboot / Event 3 - The Awakening "
     "(folder 1ncmu_zzlYnJNzEK7DPm0z17YkaJMKeel)."),
]


def main():
    with open(SRC, encoding="utf-8") as fp:
        lines = fp.readlines()

    # Locate "QUESTS = {" and the closing "}" line.
    open_idx = next(i for i, l in enumerate(lines) if l.startswith("QUESTS = {"))
    close_idx = max(i for i, l in enumerate(lines) if l.rstrip() == "}")
    header = lines[: open_idx]          # module docstring
    body = lines[open_idx + 1: close_idx]  # dict entries + comments

    # Find the body-relative line index where each section banner appears.
    # A banner is the "# ───" rule line immediately before the matching
    # comment; fall back to the comment line itself.
    starts = []
    for name, pattern, _prov in SECTIONS:
        rx = re.compile(pattern)
        hit = None
        for i, l in enumerate(body):
            if l.lstrip().startswith("#") and rx.search(l):
                hit = i
                break
        if hit is None:
            sys.exit(f"FATAL: banner not found for {name} ({pattern})")
        # back up over contiguous comment lines (the boxed banner)
        j = hit
        while j > 0 and body[j - 1].lstrip().startswith("#"):
            j -= 1
        # also swallow a single preceding blank line
        if j > 0 and not body[j - 1].strip():
            j -= 1
        starts.append((name, j))

    # Sanity: sections must be in file order.
    if [s for _, s in starts] != sorted(s for _, s in starts):
        sys.exit("FATAL: sections out of order; aborting")

    os.makedirs(PKG, exist_ok=True)
    bounds = [s for _, s in starts] + [len(body)]
    written = []
    for k, (name, _pat, prov) in enumerate(SECTIONS):
        chunk = body[bounds[k]: bounds[k + 1]]
        mod_path = os.path.join(PKG, f"{name}.py")
        with open(mod_path, "w", encoding="utf-8") as fp:
            fp.write(f'"""{prov}\n\nQuest dict format: see world/quests/__init__.py.\n"""\n\n')
            fp.write("QUESTS = {\n")
            fp.writelines(chunk)
            fp.write("}\n")
        written.append(name)

    # Aggregator
    init_path = os.path.join(PKG, "__init__.py")
    doc = "".join(header).strip()
    # Reuse the original format documentation in the package docstring.
    mod_list = ",\n    ".join(written)
    with open(init_path, "w", encoding="utf-8") as fp:
        fp.write(doc + "\n\n")
        fp.write("from world.quests import (\n    " + mod_list + ",\n)\n\n")
        fp.write(
            "_MODULES = (" + ", ".join(written) + ")\n\n"
            "QUESTS = {}\n"
            "for _mod in _MODULES:\n"
            "    for _key, _qdef in _mod.QUESTS.items():\n"
            "        if _key in QUESTS:\n"
            "            raise ValueError(\n"
            "                f\"Duplicate quest key {_key!r} in \"\n"
            "                f\"{_mod.__name__} — quest keys must be \"\n"
            "                f\"globally unique across event modules.\"\n"
            "            )\n"
            "        QUESTS[_key] = _qdef\n"
        )

    # Verify: exec original vs merged package result.
    orig_ns = {}
    with open(SRC, encoding="utf-8") as fp:
        exec(fp.read(), orig_ns)
    merged = {}
    for name in written:
        ns = {}
        with open(os.path.join(PKG, f"{name}.py"), encoding="utf-8") as fp:
            exec(fp.read(), ns)
        for key, qdef in ns["QUESTS"].items():
            if key in merged:
                sys.exit(f"FATAL: duplicate key {key} from {name}")
            merged[key] = qdef
    if merged != orig_ns["QUESTS"]:
        ok = set(merged) == set(orig_ns["QUESTS"])
        sys.exit(f"FATAL: merged dict != original (same keys: {ok})")
    if list(merged) != list(orig_ns["QUESTS"]):
        sys.exit("FATAL: key ORDER differs (journal display order would change)")

    # Rewrite quest_data.py as a shim only after verification passed.
    with open(SRC, "w", encoding="utf-8") as fp:
        fp.write(
            '"""Compat shim — quest content now lives in world/quests/.\n\n'
            "Quest definitions were split into per-event modules\n"
            "(world/quests/event1_walkins.py etc.) on 2026-06-09. Every\n"
            "existing `from world.quest_data import QUESTS` keeps working.\n"
            "Add new quests to the appropriate event module, or create a\n"
            "new module and register it in world/quests/__init__.py.\n"
            '"""\n'
            "from world.quests import QUESTS  # noqa: F401\n"
        )
    print(f"OK: {len(merged)} quests across {len(written)} modules; "
          "order + content verified identical.")


if __name__ == "__main__":
    main()
