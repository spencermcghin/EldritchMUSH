"""
playtest.py — autonomous smoke-test harness for EldritchMUSH.

Runs inside Evennia's Django context. Gives Claude (or a human) a small
API for puppeting a superuser test character, firing commands, invoking
OOB handlers, and scraping logs for tracebacks.

Usage (from the eldritchmush/ dir, with the server *stopped or running*):

    evennia shell --cmd "exec(open('../.claude/skills/playtest/playtest.py').read())"

Or to run a named scenario end-to-end and print a report:

    evennia shell --cmd "
import sys
sys.path.insert(0, '../.claude/skills/playtest')
from playtest import Harness, SCENARIOS
h = Harness()
h.run_scenario('crafting-modal')
"

The harness uses `character.execute_cmd()` for normal text commands and
calls the `inputfuncs.text` handler directly with a captured session for
OOB commands (so tests exercise the real dispatch path used by the web
client). It does NOT open a network connection — it manipulates in-process
state only, so the server can be stopped and this still runs against the
live DB.
"""

import os
import re
import time
import traceback
from pathlib import Path


# ---------------------------------------------------------------------------
# Log scraping
# ---------------------------------------------------------------------------

LOG_PATHS = [
    Path(__file__).resolve().parents[3] / "eldritchmush" / "server" / "logs" / "server.log",
    Path(__file__).resolve().parents[3] / "eldritchmush" / "server" / "logs" / "portal.log",
    Path("/data/diag.log"),  # Railway mount; no-op locally
]


def _log_offsets():
    offsets = {}
    for p in LOG_PATHS:
        try:
            offsets[p] = p.stat().st_size
        except (FileNotFoundError, PermissionError):
            offsets[p] = 0
    return offsets


def _new_log_tail(offsets):
    """Return text appended to each tracked log since `offsets` was taken."""
    out = []
    for p, prev in offsets.items():
        try:
            size = p.stat().st_size
            if size <= prev:
                continue
            with open(p, "rb") as f:
                f.seek(prev)
                chunk = f.read(size - prev).decode("utf-8", errors="replace")
            out.append(f"--- {p.name} (+{size - prev} bytes) ---\n{chunk}")
        except (FileNotFoundError, PermissionError):
            continue
    return "\n".join(out)


TRACE_RE = re.compile(r"Traceback \(most recent call last\):|^\w+Error: ", re.M)


def find_tracebacks(text):
    return bool(TRACE_RE.search(text or ""))


# ---------------------------------------------------------------------------
# Mock session — captures .msg() output from OOB handlers
# ---------------------------------------------------------------------------

class CapturingSession:
    """Stands in for an Evennia ServerSession so we can call inputfunc.text
    directly and collect everything a real session would receive."""

    def __init__(self, puppet, account=None):
        self.puppet = puppet
        self.account = account or getattr(puppet, "account", None)
        self.sessid = 999_999
        self.protocol_key = "test"
        self.text_frames = []
        self.events = []

    def msg(self, text=None, event=None, **kwargs):
        if text is not None:
            self.text_frames.append(text)
        if event is not None:
            self.events.append(event)
        for k, v in kwargs.items():
            if k not in ("text", "event"):
                self.events.append({k: v})

    def get_cmdset_providers(self):
        """Evennia's cmdhandler expects this on a session. Mirror the
        real ServerSession.get_cmdset_providers shape."""
        out = {"session": self}
        if self.account:
            out["account"] = self.account
        if self.puppet:
            out["object"] = self.puppet
        return out


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------

TEST_CHAR_KEY = "Playtester"


class Harness:
    def __init__(self, char_key=TEST_CHAR_KEY, start_location_key=None):
        from evennia import search_object
        from evennia.accounts.models import AccountDB

        self.char_key = char_key
        self.char = self._get_or_create_tester(char_key, start_location_key)
        self.session = CapturingSession(self.char)
        self._caller_msgs = []
        self._patch_msg_capture()
        self.log = []  # (step, summary) tuples

    # -- setup -----------------------------------------------------------------

    def _get_or_create_tester(self, key, start_location_key):
        from evennia import search_object, create_object
        from django.conf import settings as dj_settings
        from evennia.objects.models import ObjectDB

        existing = [c for c in search_object(key)
                    if c.typeclass_path.endswith(".Character")]
        if existing:
            char = existing[0]
        else:
            # Use the default Character typeclass; no account attached.
            char = create_object(
                dj_settings.BASE_CHARACTER_TYPECLASS,
                key=key,
            )
            # Bestow superuser-like permissions via a staff-tier lock bypass.
            char.permissions.add("Developer")

        # Teleport to the start room if asked
        if start_location_key:
            room = search_object(start_location_key)
            if room:
                char.move_to(room[0], quiet=True)

        return char

    def _patch_msg_capture(self):
        """Intercept self.char.msg() so execute_cmd output lands in
        self._caller_msgs. Restored on teardown()."""
        self._orig_msg = self.char.msg

        def capture(text=None, **kwargs):
            if text is not None:
                self._caller_msgs.append(str(text))
            # Still forward so other hooks that listen get signals if needed
            return None

        self.char.msg = capture

    def teardown(self):
        self.char.msg = self._orig_msg

    # -- driving ---------------------------------------------------------------

    def run(self, cmd):
        """Fire a regular text command as the tester. Returns captured msg
        text joined into a single string."""
        self._caller_msgs.clear()
        try:
            self.char.execute_cmd(cmd)
        except Exception:
            self._caller_msgs.append("EXCEPTION:\n" + traceback.format_exc())
        out = "\n".join(self._caller_msgs)
        self.log.append(("cmd", cmd, out[:400]))
        return out

    def run_oob(self, text_cmd):
        """Drive the input-func text handler for a recognized OOB string.

        We don't route through Evennia's cmdhandler (our mock session
        isn't complete enough for that) — instead we look for known
        OOB prefixes and call their helper modules directly. This
        exercises the same logic the real `text()` handler would.

        Returns dict {text: [...], events: [...]}.
        """
        self.session.text_frames.clear()
        self.session.events.clear()
        prev_msg = self.char.msg
        self.char.msg = lambda t=None, **k: (
            self.session.text_frames.append(t) if t else None
        )
        try:
            self._dispatch_oob(text_cmd)
        except Exception:
            self.session.text_frames.append("EXCEPTION:\n" + traceback.format_exc())
        finally:
            self.char.msg = prev_msg

        result = {
            "text": list(self.session.text_frames),
            "events": list(self.session.events),
        }
        self.log.append(("oob", text_cmd, _summary(result)))
        return result

    def _dispatch_oob(self, text_cmd):
        """Minimal OOB dispatcher — add branches here when testing new
        handlers. Mirrors the relevant logic from inputfuncs.text."""
        cmd = text_cmd.strip()
        low = cmd.lower()

        if low == "__crafting_ui__":
            from world.crafting_ui import build_payload
            self.session.msg(event=build_payload(self.char))
            return

        if low.startswith("__craft_item__ "):
            from world.crafting_ui import craft_item, build_payload
            key = cmd[len("__craft_item__ "):].strip()
            ok, msg, bcast = craft_item(self.char, key)
            if msg:
                self.session.msg(text=msg)
            self.session.msg(event=build_payload(self.char))
            return

        raise ValueError(
            f"run_oob doesn't know how to dispatch {text_cmd!r}. "
            f"Extend _dispatch_oob in playtest.py."
        )

    # -- full scenario ---------------------------------------------------------

    def run_scenario(self, name):
        steps = SCENARIOS.get(name)
        if steps is None:
            print(f"Unknown scenario: {name}. Known: {list(SCENARIOS)}")
            return False

        offsets = _log_offsets()
        print(f"\n=== Scenario: {name} ===")
        print(f"Tester: {self.char.key} (#{self.char.id}) in {self.char.location}")

        results = []
        ok = True
        for step in steps:
            kind = step[0]
            if kind == "cmd":
                out = self.run(step[1])
                broke = "EXCEPTION" in out or "|400" in out
                print(f"  > {step[1]!r}{'  !!' if broke else ''}")
            elif kind == "oob":
                out = self.run_oob(step[1])
                broke = any("EXCEPTION" in t for t in out["text"])
                print(f"  OOB {step[1]!r}{'  !!' if broke else ''}")
                if out["events"]:
                    ev = out["events"][0]
                    keys = sorted(ev.keys()) if isinstance(ev, dict) else []
                    print(f"      event keys: {keys}")
            elif kind == "goto":
                from evennia import search_object
                r = search_object(step[1])
                if r:
                    self.char.move_to(r[0], quiet=True)
                    broke = False
                    print(f"  goto {step[1]}")
                else:
                    broke = True
                    print(f"  goto {step[1]}  !! NOT FOUND")
                out = ""
            elif kind == "assert":
                probe, needle = step[1], step[2]
                haystack = self.run(probe) if probe else ""
                broke = needle not in haystack
                print(f"  assert {needle!r}{'  !!' if broke else ''}")
                out = haystack
            else:
                broke = True
                print(f"  ?? unknown step {step!r}")
                out = ""
            results.append((step, out, broke))
            ok = ok and not broke

        tail = _new_log_tail(offsets)
        if find_tracebacks(tail):
            ok = False
            print("\n!! Tracebacks appeared in server logs during run:")
            print(tail[-2000:])

        print(f"\n=== {name}: {'PASS' if ok else 'FAIL'} ===")
        return ok


def _summary(result):
    n_text = len(result["text"])
    n_ev = len(result["events"])
    return f"text={n_text} events={n_ev}"


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------
# A scenario is a list of ("cmd"|"oob"|"goto"|"assert", *args) tuples.
#
# When adding a scenario, pick a recently changed feature. Use `cmd` for
# text commands, `oob` for web-UI OOB strings (`__crafting_ui__` etc.),
# `goto` to teleport the tester, and `assert` to require a substring in
# output.

SCENARIOS = {
    "crafting-modal": [
        ("goto",   "The Crafter's Quarter"),
        ("oob",    "__crafting_ui__"),
        # Superuser sees all tabs; event should contain a tabs array.
    ],
    "crafting-modal-ironhaven": [
        ("goto",   "Ironhaven Forge"),
        ("oob",    "__crafting_ui__"),
    ],
    "schematic-shop-torben": [
        ("goto",   "The Crafter's Quarter"),
        ("assert", "browse recipes", "Schematic"),
    ],
    "alchemy-roundtrip": [
        ("goto",   "The Crafter's Quarter"),
        ("oob",    "__crafting_ui__"),
        ("cmd",    "reagents"),
    ],
}


# ---------------------------------------------------------------------------
# CLI convenience
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    scenario = sys.argv[1] if len(sys.argv) > 1 else "crafting-modal"
    h = Harness()
    try:
        h.run_scenario(scenario)
    finally:
        h.teardown()
