"""
confession.py — the Keeper of the Vault of Confessions.

A confessor NPC (db.is_confessor=True) keeps a vault of secrets that
players DELIBERATELY confess to him via the `confess` command. The
command itself warns that vaults can be robbed — confessing is an
explicit, informed gamble, never harvested from ambient chat.

A player with real espionage skill can `pry` at the vault and walk
away with a random secret another soul confessed: espionage 2 gets
the secret without the name; espionage 3 gets the name too. Failed
attempts are remembered by the Keeper.

Safety rails:
- only the confess command writes to the vault (never chat),
- confessions run through the banned-phrase filter,
- the Keeper's LLM dialogue NEVER sees vault contents (storage lives
  on db.confession_vault, which is not in any prompt block),
- a player can never pry out their own confession,
- vault capped, entries length-capped.
"""

import random
import time

from evennia import Command

VAULT_CAP = 50
CONFESSION_MAX_LEN = 240
PRY_COOLDOWN = 3600  # 1 hour


def _find_confessor(caller):
    if not caller.location:
        return None
    for obj in caller.location.contents:
        if obj != caller and obj.db.is_confessor:
            return obj
    return None


class CmdConfess(Command):
    """
    Confess a secret to the Keeper of the Vault.

    Usage: confess <your secret>

    The Keeper hears, and the Vault keeps. Confession lightens the
    soul — the Keeper thinks a little better of those who trust him.

    Be warned, and warned plainly: the Vault has been robbed before.
    A secret given is a secret that exists. Cunning hands and sharper
    ears have pried whispers loose from the Keeper's hoard, and what
    you say here may someday find its way to someone else's ear,
    with or without your name still attached. Confess nothing you
    cannot survive the world knowing.
    """

    key = "confess"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        caller = self.caller
        keeper = _find_confessor(caller)
        if not keeper:
            caller.msg("|430There is no one here to keep your secrets.|n")
            return
        secret = (self.args or "").strip()
        if not secret:
            caller.msg("|430Usage: confess <your secret>|n\n"
                       "|025(The Vault has been robbed before. Confess "
                       "nothing you cannot survive the world knowing.)|n")
            return
        if len(secret) > CONFESSION_MAX_LEN:
            caller.msg(f"|430The Keeper raises a hand. \"Brevity, child. "
                       f"The Vault is not a library.\" (max "
                       f"{CONFESSION_MAX_LEN} characters)|n")
            return
        try:
            from world.ai_safety import check_banned
            if check_banned(secret):
                caller.msg("|430The Keeper's face closes. \"The Vault "
                           "does not keep that.\"|n")
                return
        except Exception:
            pass

        vault = list(keeper.db.confession_vault or [])
        vault.append({
            "char": caller.key,
            "text": secret,
            "ts": time.time(),
        })
        if len(vault) > VAULT_CAP:
            vault = vault[-VAULT_CAP:]
        keeper.db.confession_vault = vault

        caller.msg(
            f"|025You speak low, and {keeper.key} inclines his head. "
            f"\"The Vault keeps it,\" he says. \"And the Vault keeps "
            f"what it keeps... for as long as it can.\"|n")
        caller.location.msg_contents(
            f"|025{caller.key} speaks quietly with {keeper.key}, too "
            f"low to hear.|n", exclude=caller)
        try:
            from commands.quests import _adjust_npc_rep
            _adjust_npc_rep(caller, (keeper.key or "").lower(), 1,
                            memory_tag="trusted the Vault with a secret")
        except Exception:
            pass
        try:
            from world import telemetry
            telemetry.incr("living_world.confessions")
        except Exception:
            pass


class CmdPry(Command):
    """
    Pry a secret loose from the Vault of Confessions.

    Usage: pry <keeper>

    A delicate, deniable crime. With enough skill in espionage (2+),
    you can work a confession loose from the Keeper's hoard — someone
    else's, never your own. The truly skilled (espionage 3) come away
    knowing whose secret it was. The unskilled come away remembered.
    """

    key = "pry"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        caller = self.caller
        keeper = _find_confessor(caller)
        if not keeper:
            caller.msg("|430There is no vault here to pry at.|n")
            return

        now = time.time()
        last = caller.db.pry_last or 0
        if now - last < PRY_COOLDOWN:
            caller.msg("|025The Keeper's eyes have not left you since "
                       "the last time. Not now. Not soon.|n")
            return

        skill = caller.attributes.get("espionage", default=0) or 0
        if skill < 2:
            caller.db.pry_last = now
            caller.msg(
                f"|430You angle for the Vault and {keeper.key} reads "
                f"you like a broadsheet. \"No,\" he says, simply. He "
                f"will remember this.|n")
            try:
                from commands.quests import _adjust_npc_rep
                _adjust_npc_rep(
                    caller, (keeper.key or "").lower(), -2,
                    memory_tag="tried to pry at the Vault of "
                               "Confessions and was caught")
            except Exception:
                pass
            return

        vault = [e for e in (keeper.db.confession_vault or [])
                 if e.get("char") != caller.key]
        if not vault:
            caller.db.pry_last = now
            caller.msg("|025You work the conversation like a lock — "
                       "and find the Vault empty of anything you "
                       "don't already know.|n")
            return

        caller.db.pry_last = now
        entry = random.choice(vault)
        if skill >= 3:
            attribution = f"|w{entry['char']}|n confessed it"
        else:
            attribution = "you could not catch whose voice it was"
        caller.msg(
            f"|025You keep the Keeper talking, and talking, and in the "
            f"seam between two sentences something slips loose:|n\n\n"
            f"|m\"{entry['text']}\"|n\n\n"
            f"|025— {attribution}. The Keeper suspects nothing. "
            f"Probably.|n")
        try:
            from world import living_world
            living_world.ledger_add("pried", char=caller.key,
                                    keeper=keeper.key)
        except Exception:
            pass
        try:
            from world import telemetry
            telemetry.incr("living_world.secrets_pried")
        except Exception:
            pass


class CmdSiege(Command):
    """
    Resolve the Siege of the North Gate (staff only).

    Usage:
      @siege held    — the gate held; Mystvale stands
      @siege fell    — the gate fell; the wall is breached
      @siege clear   — remove the siege state entirely

    The ONE shared-world consequence: sets the world flag, scars the
    North Gate's description for every player forever (or until
    cleared), and announces the outcome to every occupied room. Run
    this after the live wave-defense event resolves.
    """

    key = "@siege"
    locks = "cmd:perm(Builder)"
    help_category = "Admin"

    def func(self):
        outcome = (self.args or "").strip().lower()
        if outcome not in ("held", "fell", "clear"):
            self.caller.msg("|430Usage: @siege held|fell|clear|n")
            return
        from world.living_world import set_siege
        self.caller.msg(f"|y{set_siege(outcome)}|n")
