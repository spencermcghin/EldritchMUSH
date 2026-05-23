"""
Account

The Account represents the game "account" and each login has only one
Account object. An Account is what chats on default channels but has no
other in-game-world existence. Rather the Account puppets Objects (such
as Characters) in order to actually participate in the game world.


Subscription gating
-------------------
EldritchMUSH is a paid game with a 30-day free trial. Each Account
carries subscription state via Evennia db attributes:

    db.subscription_status      "trialing" | "active" | "past_due"
                                | "canceled" | None
    db.trial_started_at         ISO-8601 string; set at account creation
    db.subscription_renewal_at  ISO-8601 string; set by PayPal webhook
    db.paypal_subscription_id   PayPal subscription resource id

`is_subscription_active()` and `should_be_paywalled()` on the Account
encapsulate the gating logic. The puppet hook denies character access
when the account is paywalled.
"""

import datetime

from evennia import DefaultAccount, DefaultGuest


TRIAL_DAYS = 30


def _now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _parse_iso(value):
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(value)
    except Exception:
        return None


class Account(DefaultAccount):
    """
    OOC account object. Holds subscription/billing state in addition to
    Evennia's default account behaviour.
    """

    # ── Subscription helpers ─────────────────────────────────────────

    def at_account_creation(self):
        """Set up subscription defaults the first time the account is
        saved. Existing accounts are migrated separately (see start.sh
        / a one-shot script) so we don't reset their trial here.
        """
        try:
            super().at_account_creation()
        except Exception:
            pass
        if not self.db.subscription_status:
            self.db.subscription_status = "trialing"
            self.db.trial_started_at = _now_iso()

    def is_subscription_active(self):
        """True if the account currently has an active paid subscription
        (i.e. PayPal says they're paid up). 'past_due' is treated as
        inactive — they get paywalled until they fix payment.
        """
        return (self.db.subscription_status or "") == "active"

    def is_in_trial(self):
        """True if the trial is currently running. Inactive accounts
        whose trial has not yet expired count as in-trial.
        """
        started = _parse_iso(self.db.trial_started_at)
        if not started:
            return False
        now = datetime.datetime.now(datetime.timezone.utc)
        elapsed = (now - started).total_seconds()
        return elapsed < TRIAL_DAYS * 86400

    def trial_days_remaining(self):
        """Integer days left in the trial, floored at 0. Returns 0 if
        the trial never started or has fully expired.
        """
        started = _parse_iso(self.db.trial_started_at)
        if not started:
            return 0
        now = datetime.datetime.now(datetime.timezone.utc)
        elapsed_days = (now - started).total_seconds() / 86400.0
        remaining = TRIAL_DAYS - elapsed_days
        return max(0, int(remaining))

    def should_be_paywalled(self):
        """True if the account should be blocked from puppeting a
        character: no active sub AND no remaining trial.

        Exemptions:
          - Superusers (set via SUPERUSER_USERNAMES env on Railway)
          - Django staff (is_staff=True — also covers all superusers)
          - Anyone holding the Admin or Developer Evennia permstring
        So operators and devs are never paywalled.
        """
        if getattr(self, "is_superuser", False):
            return False
        if getattr(self, "is_staff", False):
            return False
        try:
            perms = list(self.permissions.all())
            if "Admin" in perms or "Developer" in perms:
                return False
        except Exception:
            pass
        if self.is_subscription_active():
            return False
        if self.is_in_trial():
            return False
        return True

    # ── Puppet gate ──────────────────────────────────────────────────

    def puppet_object(self, session, obj):
        """Override Evennia's puppet hook to deny when paywalled.

        Returning early without calling super() means the puppet
        attempt fails. The frontend's /api/billing/status endpoint is
        the canonical check it should be using BEFORE attempting to
        puppet — this is a defense in depth so a player can't bypass
        the UI by sending an ic command directly.
        """
        if self.should_be_paywalled():
            session.msg(
                "|rYour free trial has ended.|n Subscribe to keep "
                "playing — open the pricing page from character "
                "select, or visit "
                "|whttps://eldritchmush.com/pricing|n."
            )
            return
        return super().puppet_object(session, obj)


class Guest(DefaultGuest):
    """
    This class is used for guest logins. Unlike Accounts, Guests and their
    characters are deleted after disconnection.
    """

    pass
