"""
Tests for email verification (world/email_verification.py, the `verify`
flow, the Resend email backend) and the Google email-authentication
guard (web/allauth_adapters.SocialAccountAdapter).

Run from eldritchmush/:

    DJANGO_SECRET_KEY=<any local test value> evennia test --settings settings.py world.tests

Django's test runner swaps EMAIL_BACKEND for the in-memory backend, so
no email leaves the machine.
"""
import os
from types import SimpleNamespace
from unittest import mock

from django.core import mail
from django.test import SimpleTestCase, override_settings
from evennia.utils.test_resources import EvenniaTest

from world import ai_safety, email_verification


class _VerifyBase(EvenniaTest):

    def setUp(self):
        super().setUp()
        # EvenniaTest gives both accounts the same address; make them
        # distinct so the duplicate-address rule doesn't kick in.
        self.account.email = "player.one@example.com"
        self.account.save()
        self.account2.email = "player.two@example.com"
        self.account2.save()
        self._env = mock.patch.dict(os.environ, {
            "SITE_BASE_URL": "https://game.example.test",
        })
        self._env.start()
        os.environ.pop("NPC_AI_REQUIRE_VERIFIED", None)
        with email_verification._GLOBAL_LOCK:
            email_verification._GLOBAL_SENDS.clear()
        mail.outbox = []

    def tearDown(self):
        self._env.stop()
        super().tearDown()

    def _link(self, message):
        for line in message.body.splitlines():
            if line.startswith("https://game.example.test/"):
                return line.strip()
        self.fail("no confirmation link in the email")


class VerifyFlowTests(_VerifyBase):

    def test_link_verifies_and_unlocks_ai(self):
        self.assertFalse(ai_safety.account_ai_eligible(self.account))
        replies = []
        email_verification.request_verification(
            self.account, reply=replies.append)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["player.one@example.com"])
        self.assertEqual(message.subject, "Verify your email for EldritchMUSH")
        link = self._link(message)
        self.assertIn("/accounts/confirm-email/", link)
        self.assertIn("player.one@example.com", replies[0])

        path = link.replace("https://game.example.test", "")
        resp = self.client.post(path)
        self.assertIn(resp.status_code, (200, 302))
        self.assertEqual(email_verification.email_status(self.account),
                         "verified")
        self.assertTrue(ai_safety.account_ai_eligible(self.account))

    def test_cooldown_between_links(self):
        email_verification.request_verification(self.account)
        replies = []
        email_verification.request_verification(
            self.account, reply=replies.append)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("We just sent you a link", replies[0])

    def test_daily_cap(self):
        with mock.patch.object(email_verification, "VERIFY_COOLDOWN", 0):
            for _ in range(email_verification.VERIFY_DAILY_MAX + 2):
                email_verification.request_verification(self.account)
        self.assertEqual(len(mail.outbox), email_verification.VERIFY_DAILY_MAX)

    def test_global_hourly_cap(self):
        with mock.patch.object(email_verification,
                               "VERIFY_GLOBAL_HOURLY_MAX", 1):
            email_verification.request_verification(self.account)
            replies = []
            email_verification.request_verification(
                self.account2, reply=replies.append)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("try again in an hour", replies[0])

    def test_verify_new_address(self):
        self.account.email = ""
        self.account.save()
        self.assertEqual(email_verification.email_status(self.account),
                         "no_email")
        email_verification.request_verification(
            self.account, email="New.Address@Example.com")
        self.account.refresh_from_db()
        self.assertEqual(self.account.email, "new.address@example.com")
        self.assertEqual(mail.outbox[0].to, ["new.address@example.com"])

    def test_address_of_another_account_refused(self):
        replies = []
        email_verification.request_verification(
            self.account, email="player.two@example.com",
            reply=replies.append)
        self.assertEqual(mail.outbox, [])
        self.assertIn("already used by another account", replies[0])

    def test_bad_address_refused(self):
        replies = []
        email_verification.request_verification(
            self.account, email="not-an-address", reply=replies.append)
        self.assertEqual(mail.outbox, [])
        self.assertIn("doesn't look like an email address", replies[0])

    def test_google_account_needs_nothing(self):
        from allauth.socialaccount.models import SocialAccount
        SocialAccount.objects.create(user=self.account, provider="google",
                                     uid="g-1")
        replies = []
        email_verification.request_verification(
            self.account, reply=replies.append)
        self.assertEqual(mail.outbox, [])
        self.assertIn("already verified", replies[0])

    def test_login_note(self):
        note = email_verification.login_note(self.account)
        self.assertIn("verify", note)
        self.account.email = ""
        self.account.save()
        self.assertIn("verify you@example.com",
                      email_verification.login_note(self.account))
        os.environ["NPC_AI_REQUIRE_VERIFIED"] = "0"
        self.assertIsNone(email_verification.login_note(self.account))

    def test_verify_command_registered(self):
        from commands.account import CmdVerify
        from commands.default_cmdsets import AccountCmdSet
        cmdset = AccountCmdSet()
        cmdset.at_cmdset_creation()
        self.assertIn("verify", [c.key for c in cmdset.commands])
        self.assertTrue(CmdVerify.account_caller)


class BulkBackfillTests(_VerifyBase):

    def test_dry_run_sends_nothing(self):
        out = []
        n = email_verification.send_bulk(send=False, out=out.append)
        self.assertEqual(n, 2)
        self.assertEqual(mail.outbox, [])

    def test_send_once_per_account(self):
        with mock.patch("time.sleep"):
            n = email_verification.send_bulk(send=True, out=lambda *_: None)
            again = email_verification.send_bulk(send=True,
                                                 out=lambda *_: None)
        self.assertEqual(n, 2)
        self.assertEqual(again, 0)
        self.assertEqual(len(mail.outbox), 2)

    def test_limit_and_skips(self):
        from allauth.socialaccount.models import SocialAccount
        SocialAccount.objects.create(user=self.account2, provider="google",
                                     uid="g-2")
        with mock.patch("time.sleep"):
            n = email_verification.send_bulk(limit=5, send=True,
                                             out=lambda *_: None)
        self.assertEqual(n, 1)
        self.assertEqual(mail.outbox[0].to, ["player.one@example.com"])

    def test_shared_address_skipped(self):
        self.account2.email = "PLAYER.ONE@example.com"
        self.account2.save()
        self.assertEqual(email_verification.bulk_candidates(), [])


class ResendBackendTests(SimpleTestCase):

    @override_settings(EMAIL_BACKEND="world.email_backend.ResendEmailBackend")
    def test_sends_text_and_html_through_resend(self):
        from django.core.mail import EmailMultiAlternatives
        with mock.patch("world.email.send_email",
                        return_value=True) as send:
            msg = EmailMultiAlternatives(
                "Verify", "Open this link:\n\nhttps://x.test/confirm/abc/",
                "noreply@eldritchmush.com", ["p@example.com"])
            self.assertEqual(msg.send(), 1)
        to, subject, html_body = send.call_args[0]
        self.assertEqual(to, ["p@example.com"])
        self.assertEqual(subject, "Verify")
        self.assertIn('<a href="https://x.test/confirm/abc/">', html_body)
        self.assertIn("Open this link:", send.call_args.kwargs["text_body"])

    @override_settings(EMAIL_BACKEND="world.email_backend.ResendEmailBackend")
    def test_failed_send_counts_zero(self):
        from django.core.mail import EmailMessage
        with mock.patch("world.email.send_email", return_value=False):
            self.assertEqual(
                EmailMessage("s", "b", None, ["p@example.com"]).send(), 0)


class GoogleEmailAuthenticationTests(EvenniaTest):
    """A Google sign-in may only log into / connect to an existing local
    account by email when that local address is verified."""

    def setUp(self):
        super().setUp()
        self.account.email = "victim@gmail.com"
        self.account.save()

    def _login(self):
        from allauth.account.models import EmailAddress
        from allauth.socialaccount.models import SocialAccount, SocialLogin
        login = SocialLogin(
            account=SocialAccount(provider="google", uid="victim-google-id"),
            email_addresses=[EmailAddress(email="victim@gmail.com",
                                          verified=True, primary=True)],
            provider=self._provider_stub(),
        )
        return login

    def _adapter(self):
        from allauth.socialaccount.adapter import get_adapter
        from web.allauth_adapters import SocialAccountAdapter
        adapter = get_adapter()
        self.assertIsInstance(adapter, SocialAccountAdapter)
        return adapter

    def _provider_stub(self):
        return SimpleNamespace(app=None, get_settings=lambda: {})

    def test_unverified_local_address_is_not_used(self):
        from allauth.account.models import EmailAddress
        EmailAddress.objects.create(user=self.account,
                                    email="victim@gmail.com",
                                    verified=False, primary=True)
        login = SimpleNamespace(provider=self._provider_stub())
        self.assertFalse(
            self._adapter().can_authenticate_by_email(login,
                                                      "victim@gmail.com"))

    def test_legacy_email_field_only_is_not_used(self):
        # Account.email set but no allauth EmailAddress row at all.
        login = SimpleNamespace(provider=self._provider_stub())
        self.assertFalse(
            self._adapter().can_authenticate_by_email(login,
                                                      "victim@gmail.com"))

    def test_verified_local_address_is_used(self):
        from allauth.account.models import EmailAddress
        EmailAddress.objects.create(user=self.account,
                                    email="victim@gmail.com",
                                    verified=True, primary=True)
        login = SimpleNamespace(provider=self._provider_stub())
        self.assertTrue(
            self._adapter().can_authenticate_by_email(login,
                                                      "Victim@Gmail.com"))

    def test_lookup_by_email_skips_unverified_account(self):
        from allauth.account.models import EmailAddress
        EmailAddress.objects.create(user=self.account,
                                    email="victim@gmail.com",
                                    verified=False, primary=True)
        login = self._login()
        login._lookup_by_email()
        self.assertIsNone(login.user)

    def test_lookup_by_email_uses_verified_account(self):
        from allauth.account.models import EmailAddress
        EmailAddress.objects.create(user=self.account,
                                    email="victim@gmail.com",
                                    verified=True, primary=True)
        login = self._login()
        login._lookup_by_email()
        self.assertEqual(login.user.id, self.account.id)
