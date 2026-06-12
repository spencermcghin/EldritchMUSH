"""
Scripts

Scripts are powerful jacks-of-all-trades. They have no in-game
existence and can be used to represent persistent game systems in some
circumstances. Scripts can also have a time component that allows them
to "fire" regularly or a limited number of times.

There is generally no "tree" of Scripts inheriting from each other.
Rather, each script tends to inherit from the base Script class and
just overloads its hooks to have it perform its function.

"""

import random
from evennia import DefaultScript


# ---------------------------------------------------------------------------
# SermonScript — periodic atmospheric broadcast of Aurorym sermon
# fragments to the room. Attached to Gateway — The Open Square via
# populate_mistvale.py so Brother Alaric's preaching spills into the
# ambient text even when players aren't directly conversing with him.
# ---------------------------------------------------------------------------
# Sermon fragments drawn from the canonical Book of Magnus. Each is
# either a direct quotation (with Chapter/Rune citation) or Brother
# Alaric's riff on a canonical teaching. Chapter/Rune references match
# the Book of Magnus text held in the Drive.
AURON_SERMONS = [
    # Chapter I Rune I — egalitarian opening
    "Brother Alaric raises his hands to the grey sky: |y\"Hear the First "
    "Rune of the First Chapter! 'Even the weak can be mighty. The poor "
    "peasant is as dear to this world as the mighty prince.' Magnus "
    "wrote that, friends — not I!\"|n",

    # Chapter I Rune IV — interior path
    "Brother Alaric calls out, voice carrying: |y\"'He who conquers "
    "others is strong. He who conquers himself is mighty.' Rune Four of "
    "the First Chapter! The Dawn does not wait at Highcourt's gate; it "
    "waits within YOU.\"|n",

    # Chapter I Rune V — the animus metaphor
    "Brother Alaric thumps his Book of Magnus: |y\"The animus is powerful "
    "but fragile — fed by virtue and valor, it ripens. Fed by malice and "
    "cowardice, it withers. You are your own orchard, bearer. What fruit "
    "have you grown this moon-cycle?\"|n",

    # Chapter I Rune VII — the New Dawn call
    "Brother Alaric intones, eyes half-closed: |y\"'A new Dawn is coming "
    "to Arnesse and we are its heralds. Take my hand, and do not fear, "
    "for death holds no horrors for the truly righteous.' The First "
    "Chapter, closing Rune.\"|n",

    # Chapter II Rune VI — crucible
    "Brother Alaric speaks low and steady: |y\"'From the fires of the "
    "crucible we emerge harder, sharper, and more honed to our purpose.' "
    "The Second Chapter. If the Mists have tested you, bearer, REJOICE. "
    "You are being forged.\"|n",

    # Chapter III Rune II — death as horizon
    "Brother Alaric murmurs, half to himself: |y\"'Death is only a "
    "horizon, and a horizon merely the limits of what one can see.' "
    "Chapter Three, Rune Two. A good Rune for the Mistwall, that one.\"|n",

    # Chapter III Rune III — the lamp
    "Brother Alaric lifts his begging bowl and speaks gently: |y\"'The "
    "world is a dark place, and so we carry a lamp. Our own light is "
    "not diminished by sharing it with another.' A copper to the bowl, "
    "then, and the night grows just a little less dark.\"|n",

    # Chapter IV Rune I — the gods are dead
    "Brother Alaric raises his voice to a passing merchant: |y\"The "
    "gods are dead and obsolete, friend! Magnus wrote it plain — 'we "
    "no longer need look to external forces for the power he nurtures "
    "within himself.' There is no master but your own animus!\"|n",

    # Chapter V Rune II — fall six, stand seven
    "Brother Alaric catches sight of a beggar and kneels to speak low: "
    "|y\"'Should you fall six times, stand up seven.' Chapter Five, "
    "Rune Two. You have not been defeated, sister. You have only been "
    "defeated YET.\"|n",

    # Chapter V Rune VI — be the candle
    "Brother Alaric preaches, soft and sure: |y\"'Be the candle that "
    "lights the way, that others may find the path in the dark.' Fifth "
    "Chapter, Sixth Rune. If every lamp in Gateway lit one other, the "
    "whole palisade would burn bright.\"|n",

    # Chapter VII Rune III — warning against the Resurrectionist
    "Brother Alaric's voice drops, troubled: |y\"Magnus warned us — "
    "'Seek not the Resurrectionist.' Chapter Seven, Rune Three. I tell "
    "you, brethren, there are stories from Mystvale I cannot unhear.\"|n",

    # Chapter IX — Eschaton prophecy (condensed)
    "Brother Alaric's voice hushes, awed: |y\"'The moon shall turn as "
    "blood and rule above the silence of the waters. The Heralds of "
    "Oblivion shall take up fel horns, and the King of Nothing shall "
    "come.' Chapter Nine. The Eschaton is not metaphor, friends. It is "
    "the road before us.\"|n",

    # Chapter IX Rune XI — closing warning
    "Brother Alaric cries out, all at once fierce: |y\"'Women and men "
    "of the Dawn, PREPARE YOURSELVES. They are coming.' The Ninth "
    "Chapter's final Rune. The Day of Mist was the herald. The Annwyn "
    "is where the Dawn is kindled — or where the Dark swallows the "
    "last Hallowed whole!\"|n",

    # Riff — on Paragons and the Hallowed
    "Brother Alaric gestures toward the palisade: |y\"The Hallowed walk "
    "among us, bearer. They live as we live and die as we die — but "
    "their animus Ascends. It is the BIRTHRIGHT of mankind to become "
    "Paragon unto itself, so Magnus wrote.\"|n",

    # Riff — on the Godslayers (Alaric dissenting)
    "Brother Alaric frowns at a Godslayer banner across the square: "
    "|y\"The Third Rune of the Thirteenth Chapter — 'false prophets... "
    "clothed in the countenance of the faithful, speaking words of honey "
    "that do not nourish.' Every Kindling novice knows that one. Every "
    "Godslayer should.\"|n",

    # Riff — on the lamp of Gateway
    "Brother Alaric accepts a coin from a ragged pilgrim, bows his head: "
    "|y\"May the lamp you carry today light another's tomorrow. The "
    "Dawn goes with you, bearer.\"|n",
]


class SermonScript(DefaultScript):
    """Broadcasts a random Auron sermon fragment to the room the script
    is attached to, every ~10 minutes.

    Silent if the attached Auron NPC isn't present in the room (e.g.
    admins moved them elsewhere). This avoids Gateway sermonizing
    itself when Brother Alaric is somewhere else.
    """

    def at_script_creation(self):
        self.key = "sermon_script"
        self.desc = "Brother Alaric's periodic sermonizing"
        self.interval = 600       # 10 minutes
        self.start_delay = True   # don't fire on server start
        self.persistent = True
        self.db.auron_key = "Brother Alaric"

    def at_repeat(self):
        room = self.obj
        if not room:
            return
        auron_key = self.db.auron_key or "Brother Alaric"
        # Only broadcast if the Auron is actually present.
        preacher = None
        for obj in room.contents:
            if getattr(obj, "key", None) == auron_key:
                preacher = obj
                break
        if not preacher:
            return
        line = random.choice(AURON_SERMONS)
        try:
            room.msg_contents(line)
        except Exception:
            pass


class QuestDeadlineScript(DefaultScript):
    """A timed-rescue deadline for a single quest objective.

    Armed by the quest engine when a 'deadline_starts_on' beat completes
    (e.g. the player reaches the dying man). If the deadline objective
    isn't finished before `interval` seconds elapse, the quest fails
    with the authored reason — the doc's "save him in ten minutes or he
    burns from the inside." Attached to the character; self-deletes once
    it fires or once the objective completes (the engine stops it).
    """

    def at_script_creation(self):
        self.key = "quest_deadline"
        self.desc = "Timed quest objective deadline"
        self.start_delay = True
        self.repeats = 1
        self.persistent = True

    def at_repeat(self):
        char = self.obj
        quest_key = self.db.quest_key
        tag = self.db.objective_tag
        reason = self.db.reason or ""
        try:
            from commands.quests import _deadline_expired
            _deadline_expired(char, quest_key, tag, reason)
        except Exception as exc:
            print(f"[quest_deadline] expiry error: {exc!r}", flush=True)
        self.stop()


class TelemetryHeartbeatScript(DefaultScript):
    """Operational telemetry heartbeat (world/telemetry.py).

    Every 5 minutes: logs one JSON line of process/session/DB/LLM-spend
    state to the volume + stdout, and runs the threshold checks that
    email the admin on runaway LLM spend, LLM error bursts, or DB
    growth. Bootstrapped at server start.
    """

    def at_script_creation(self):
        self.key = "telemetry_heartbeat"
        self.desc = "Operational telemetry heartbeat"
        self.interval = 300
        self.start_delay = True
        self.persistent = True

    def at_repeat(self):
        try:
            from world import telemetry
            telemetry.heartbeat()
        except Exception as exc:
            print(f"[telemetry] heartbeat script error: {exc!r}", flush=True)


class GossipScript(DefaultScript):
    """Nightly-ish rumor propagation (world/living_world.py).

    Every 6 hours, NPC memories about players spread to other NPCs the
    player knows, distorted in the retelling by the LLM (template
    fallback when the LLM is off). Bootstrapped at server start.
    """

    def at_script_creation(self):
        self.key = "living_world_gossip"
        self.desc = "Rumors spread between NPCs"
        self.interval = 21600  # 6 hours
        self.start_delay = True
        self.persistent = True

    def at_repeat(self):
        try:
            from world import living_world
            living_world.gossip_tick()
        except Exception as exc:
            print(f"[living_world] gossip script error: {exc!r}",
                  flush=True)


class LedgerStorageScript(DefaultScript):
    """Inert storage for the living-world deed ledger (db.events).
    Never fires; exists so the ledger survives reboots."""

    def at_script_creation(self):
        self.key = "living_world_ledger"
        self.desc = "World deed ledger storage"
        self.interval = -1  # no repeat
        self.persistent = True


class DreamScript(DefaultScript):
    """Weekly: Dierdra dreams the players' deeds (living_world.dream_tick)."""

    def at_script_creation(self):
        self.key = "living_world_dream"
        self.desc = "Dierdra's weekly dream"
        self.interval = 604800  # 7 days
        self.start_delay = True
        self.persistent = True

    def at_repeat(self):
        try:
            from world import living_world
            living_world.dream_tick()
        except Exception as exc:
            print(f"[living_world] dream script error: {exc!r}",
                  flush=True)


class ChronicleScript(DefaultScript):
    """Weekly: the Chronicler leaves a page of player-deed prose in the
    tavern (living_world.chronicle_tick). Offset from DreamScript so
    the two don't land the same moment."""

    def at_script_creation(self):
        self.key = "living_world_chronicle"
        self.desc = "The weekly Chronicle of the Vale"
        self.interval = 604800  # 7 days
        self.start_delay = True
        self.persistent = True

    def at_repeat(self):
        try:
            from world import living_world
            living_world.chronicle_tick()
        except Exception as exc:
            print(f"[living_world] chronicle script error: {exc!r}",
                  flush=True)


class VengefulReturnScript(DefaultScript):
    """One-shot: a slain vengeful NPC rises again after its interval
    (living_world.vengeful_return), remembering its killer."""

    def at_script_creation(self):
        self.key = "vengeful_return"
        self.desc = "A slain antagonist is coming back"
        self.interval = 345600  # overridden at schedule time
        self.start_delay = True
        self.repeats = 1
        self.persistent = True

    def at_repeat(self):
        try:
            npc = self.obj
            if npc:
                from world import living_world
                living_world.vengeful_return(npc)
        except Exception as exc:
            print(f"[living_world] vengeful script error: {exc!r}",
                  flush=True)


class MistPassageScript(DefaultScript):
    """Every 3 days the Mists move: close the old temporary passage,
    open a new one between two unconnected wild rooms
    (living_world.mist_tick)."""

    def at_script_creation(self):
        self.key = "living_world_mists"
        self.desc = "The Mists open and close passages"
        self.interval = 259200  # 3 days
        self.start_delay = True
        self.persistent = True

    def at_repeat(self):
        try:
            from world import living_world
            living_world.mist_tick()
        except Exception as exc:
            print(f"[living_world] mist script error: {exc!r}",
                  flush=True)


class WitheringMawScript(DefaultScript):
    """Hourly heartbeat of the roaming boss (living_world.maw_tick)."""

    def at_script_creation(self):
        self.key = "living_world_maw"
        self.desc = "The Withering Maw roams"
        self.interval = 3600
        self.start_delay = True
        self.persistent = True

    def at_repeat(self):
        try:
            from world import living_world
            living_world.maw_tick()
        except Exception as exc:
            print(f"[living_world] maw script error: {exc!r}",
                  flush=True)


class AdjudicatorLetterScript(DefaultScript):
    """One-shot delayed delivery of a Dark Forest letter (living_world).

    Attached to a character; fires once after its interval, spawns the
    letter via living_world.deliver_letter (which schedules the next
    letter in the chain), then stops.
    """

    def at_script_creation(self):
        self.key = "adjudicator_letter"
        self.desc = "A letter from the Dark Forest is on its way"
        self.interval = 7200  # overridden at schedule time
        self.start_delay = True
        self.repeats = 1
        self.persistent = True

    def at_repeat(self):
        try:
            char = self.obj
            index = int(self.db.letter_index or 0)
            if char:
                from world import living_world
                living_world.deliver_letter(char, index)
        except Exception as exc:
            print(f"[living_world] letter script error: {exc!r}",
                  flush=True)


class AmbientNpcScript(DefaultScript):
    """Global ambient-speech ticker for NPCs that have opted in.

    Walks every room containing at least one online player character
    and, for each such room, picks one eligible NPC (has a non-empty
    ``db.ambient_lines`` list, is not aggressive, and whose per-NPC
    cooldown has elapsed) to broadcast a random ambient line. Empty
    rooms (no players) are skipped — no point in NPCs talking to
    themselves and burning log space.

    Each NPC carries:
      - ``db.ambient_lines``  list[str] of mutter/shout lines
      - ``db.ambient_cooldown_s``  int seconds between speaks (default 120)
      - ``db.last_ambient_ts``  float epoch timestamp of last broadcast
                                (managed by this script)

    Bandits/hostiles (``db.is_aggressive == True``) are skipped — a
    bandit chatting about the weather kills the menace.
    """

    AMBIENT_VERBS = ("says", "mutters", "calls out", "remarks", "muses")
    DEFAULT_COOLDOWN_S = 120

    def at_script_creation(self):
        self.key = "ambient_npc_speech"
        self.desc = "Global NPC ambient-line ticker"
        self.interval = 30          # check every 30s
        self.start_delay = True
        self.persistent = True

    def at_repeat(self):
        import time

        now = time.time()
        # Collect rooms containing at least one online (sessioned) char.
        # Cheap-ish: iterate connected sessions and resolve their puppets'
        # locations. Avoids a full-table sweep of rooms.
        try:
            from evennia.server.sessionhandler import SESSIONS
            rooms_with_players = set()
            for sess in SESSIONS.all():
                puppet = getattr(sess, "puppet", None)
                loc = getattr(puppet, "location", None) if puppet else None
                if loc:
                    rooms_with_players.add(loc)
        except Exception:
            return

        for room in rooms_with_players:
            try:
                self._maybe_speak_in_room(room, now)
            except Exception:
                # Never let a bad NPC blow up the whole tick.
                continue

    def _maybe_speak_in_room(self, room, now):
        eligible = []
        for obj in room.contents:
            if not getattr(obj.db, "is_npc", False):
                continue
            if getattr(obj.db, "is_aggressive", False):
                continue
            lines = obj.db.ambient_lines or []
            if not lines:
                continue
            cooldown = obj.db.ambient_cooldown_s or self.DEFAULT_COOLDOWN_S
            last = obj.db.last_ambient_ts or 0.0
            if now - last < cooldown:
                continue
            eligible.append((obj, list(lines)))

        if not eligible:
            return

        npc, lines = random.choice(eligible)
        line = random.choice(lines)
        verb = random.choice(self.AMBIENT_VERBS)
        try:
            room.msg_contents(f'|c{npc.key}|n {verb}, "{line}"')
            npc.db.last_ambient_ts = now
        except Exception:
            pass


class Script(DefaultScript):
    """
    A script type is customized by redefining some or all of its hook
    methods and variables.

    * available properties

     key (string) - name of object
     name (string)- same as key
     aliases (list of strings) - aliases to the object. Will be saved
              to database as AliasDB entries but returned as strings.
     dbref (int, read-only) - unique #id-number. Also "id" can be used.
     date_created (string) - time stamp of object creation
     permissions (list of strings) - list of permission strings

     desc (string)      - optional description of script, shown in listings
     obj (Object)       - optional object that this script is connected to
                          and acts on (set automatically by obj.scripts.add())
     interval (int)     - how often script should run, in seconds. <0 turns
                          off ticker
     start_delay (bool) - if the script should start repeating right away or
                          wait self.interval seconds
     repeats (int)      - how many times the script should repeat before
                          stopping. 0 means infinite repeats
     persistent (bool)  - if script should survive a server shutdown or not
     is_active (bool)   - if script is currently running

    * Handlers

     locks - lock-handler: use locks.add() to add new lock strings
     db - attribute-handler: store/retrieve database attributes on this
                        self.db.myattr=val, val=self.db.myattr
     ndb - non-persistent attribute handler: same as db but does not
                        create a database entry when storing data

    * Helper methods

     start() - start script (this usually happens automatically at creation
               and obj.script.add() etc)
     stop()  - stop script, and delete it
     pause() - put the script on hold, until unpause() is called. If script
               is persistent, the pause state will survive a shutdown.
     unpause() - restart a previously paused script. The script will continue
                 from the paused timer (but at_start() will be called).
     time_until_next_repeat() - if a timed script (interval>0), returns time
                 until next tick

    * Hook methods (should also include self as the first argument):

     at_script_creation() - called only once, when an object of this
                            class is first created.
     is_valid() - is called to check if the script is valid to be running
                  at the current time. If is_valid() returns False, the running
                  script is stopped and removed from the game. You can use this
                  to check state changes (i.e. an script tracking some combat
                  stats at regular intervals is only valid to run while there is
                  actual combat going on).
      at_start() - Called every time the script is started, which for persistent
                  scripts is at least once every server start. Note that this is
                  unaffected by self.delay_start, which only delays the first
                  call to at_repeat().
      at_repeat() - Called every self.interval seconds. It will be called
                  immediately upon launch unless self.delay_start is True, which
                  will delay the first call of this method by self.interval
                  seconds. If self.interval==0, this method will never
                  be called.
      at_stop() - Called as the script object is stopped and is about to be
                  removed from the game, e.g. because is_valid() returned False.
      at_server_reload() - Called when server reloads. Can be used to
                  save temporary variables you want should survive a reload.
      at_server_shutdown() - called at a full server shutdown.

    """

    pass
