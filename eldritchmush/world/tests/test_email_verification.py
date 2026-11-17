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
        os.environ.pop("RAILWAY_ENVIRONMENT_NAME", None)
        # Test accounts are seconds old; the age gate has its own test.
        self._age = mock.patch.object(
            email_verification, "VERIFY_MIN_ACCOUNT_AGE", 0)
        self._age.start()
        mail.outbox = []

    def tearDown(self):
        self._age.stop()
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

    def test_new_account_must_wait(self):
        with mock.patch.object(email_verification,
                               "VERIFY_MIN_ACCOUNT_AGE", 3600):
            replies = []
            email_verification.request_verification(
                self.account, reply=replies.append)
            self.assertEqual(mail.outbox, [])
            self.assertIn("after 10 minutes", replies[0])
            # Having a character lifts the wait.
            self.account.characters.add(self.char1)
            email_verification.request_verification(self.account)
        self.assertEqual(len(mail.outbox), 1)

    def test_failed_send_releases_slot_and_replies_after(self):
        from world.email import EmailNotSent
        replies = []
        with mock.patch("django.core.mail.EmailMultiAlternatives.send",
                        side_effect=EmailNotSent("daily_cap")):
            email_verification.request_verification(
                self.account, reply=replies.append)
        self.assertEqual(len(replies), 1)  # only the result, nothing before
        self.assertIn("sent all the email it can", replies[0])
        self.assertEqual(
            self.account.attributes.get("email_verify_sends"), [])
        # The cooldown was given back, so a retry goes straight out.
        email_verification.request_verification(self.account)
        self.assertEqual(len(mail.outbox), 1)

    def test_site_url_required_on_unknown_deployed_env(self):
        os.environ.pop("SITE_BASE_URL")
        os.environ["RAILWAY_ENVIRONMENT_NAME"] = "staging"
        with self.assertRaises(email_verification.SiteURLNotConfigured):
            email_verification.site_base_url()
        replies = []
        email_verification.request_verification(
            self.account, reply=replies.append)
        self.assertEqual(mail.outbox, [])
        self.assertIn("aren't set up", replies[0])
        os.environ["RAILWAY_ENVIRONMENT_NAME"] = "uat"
        self.assertEqual(email_verification.site_base_url(),
                         "https://uat.eldritchmush.com")

    def test_sync_site(self):
        from django.contrib.sites.models import Site
        email_verification.sync_site()
        site = Site.objects.get_current()
        self.assertEqual(site.name, "Eldritch MUSH")
        self.assertEqual(site.domain, "game.example.test")

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

    def test_verified_address_of_another_account_refused(self):
        from allauth.account.models import EmailAddress
        EmailAddress.objects.create(user=self.account2,
                                    email="player.two@example.com",
                                    verified=True, primary=True)
        replies = []
        email_verification.request_verification(
            self.account, email="player.two@example.com",
            reply=replies.append)
        self.assertEqual(mail.outbox, [])
        self.assertIn("already verified on another account", replies[0])
        self.assertNotIn("Google", replies[0])

    def test_unverified_claim_is_not_a_squat(self):
        # account2 merely typed the address; account (the real owner)
        # can still verify it, and doing so removes account2's claim.
        from allauth.account.models import EmailAddress
        EmailAddress.objects.create(user=self.account2,
                                    email="player.two@example.com",
                                    verified=False, primary=True)
        email_verification.request_verification(
            self.account, email="player.two@example.com")
        self.assertEqual(mail.outbox[0].to, ["player.two@example.com"])
        path = self._link(mail.outbox[0]).replace(
            "https://game.example.test", "")
        self.client.post(path)
        self.assertEqual(email_verification.email_status(self.account),
                         "verified")
        self.assertFalse(EmailAddress.objects.filter(
            user=self.account2, email="player.two@example.com").exists())
        self.account2.refresh_from_db()
        self.assertEqual(self.account2.email, "")

    def test_switching_address_drops_old_unverified_rows(self):
        from allauth.account.models import EmailAddress
        email_verification.request_verification(self.account)
        with mock.patch.object(email_verification, "VERIFY_COOLDOWN", 0):
            email_verification.request_verification(
                self.account, email="second@example.com")
        rows = list(EmailAddress.objects.filter(user=self.account))
        self.assertEqual([(r.email, r.primary) for r in rows],
                         [("second@example.com", True)])
        self.account.refresh_from_db()
        self.assertEqual(self.account.email, "second@example.com")

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

    def test_bulk_email_has_working_link(self):
        with mock.patch("time.sleep"):
            email_verification.send_bulk(limit=1, send=True,
                                         out=lambda *_: None)
        link = self._link(mail.outbox[0])
        self.assertTrue(link.startswith(
            "https://game.example.test/accounts/confirm-email/"))
        self.client.post(link.replace("https://game.example.test", ""))
        self.assertEqual(email_verification.email_status(self.account),
                         "verified")

    def test_failed_send_is_reported(self):
        out = []
        with mock.patch("time.sleep"), \
                mock.patch("django.core.mail.EmailMultiAlternatives.send",
                           return_value=0):
            n = email_verification.send_bulk(limit=1, send=True,
                                             out=out.append)
        self.assertEqual(n, 0)
        self.assertTrue(any("failed #" in line for line in out))

    def test_script_initialises_evennia_and_defaults_to_dry_run(self):
        import importlib.util
        import sys
        path = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))),
            "scripts", "send_verification_emails.py")
        spec = importlib.util.spec_from_file_location("svm_script", path)
        script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(script)
        with mock.patch.object(sys, "argv", ["send_verification_emails.py"]), \
                mock.patch("django.setup") as setup, \
                mock.patch("evennia._init") as init, \
                mock.patch("world.email_verification.send_bulk") as bulk:
            script.main()
        setup.assert_called_once()
        init.assert_called_once()
        self.assertEqual(bulk.call_args.kwargs["send"], False)

    def test_shared_address_skipped(self):
        self.account2.email = "PLAYER.ONE@example.com"
        self.account2.save()
        self.assertEqual(email_verification.bulk_candidates(), [])


class ResendBackendTests(SimpleTestCase):

    @override_settings(EMAIL_BACKEND="world.email_backend.ResendEmailBackend")
    def test_sends_text_html_cc_bcc_through_resend(self):
        from django.core.mail import EmailMultiAlternatives
        with mock.patch("world.email.send_email_result",
                        return_value=(True, None)) as send:
            msg = EmailMultiAlternatives(
                "Verify", "Open this link:\n\nhttps://x.test/confirm/abc/",
                "noreply@eldritchmush.com", ["p@example.com"],
                cc=["c@example.com"], bcc=["b@example.com"])
            self.assertEqual(msg.send(), 1)
        to, subject, html_body = send.call_args[0]
        self.assertEqual(to, ["p@example.com"])
        self.assertEqual(subject, "Verify")
        self.assertIn('<a href="https://x.test/confirm/abc/">', html_body)
        kw = send.call_args.kwargs
        self.assertIn("Open this link:", kw["text_body"])
        self.assertEqual(kw["cc"], ["c@example.com"])
        self.assertEqual(kw["bcc"], ["b@example.com"])

    @override_settings(EMAIL_BACKEND="world.email_backend.ResendEmailBackend")
    def test_failed_send_raises_unless_fail_silently(self):
        from django.core.mail import EmailMessage, get_connection
        from world.email import EmailNotSent
        with mock.patch("world.email.send_email_result",
                        return_value=(False, "daily_cap")):
            with self.assertRaises(EmailNotSent) as ctx:
                EmailMessage("s", "b", None, ["p@example.com"]).send()
            self.assertEqual(ctx.exception.reason, "daily_cap")
            quiet = get_connection(fail_silently=True)
            self.assertEqual(
                EmailMessage("s", "b", None, ["p@example.com"],
                             connection=quiet).send(), 0)


class SharedMailQuotaTests(SimpleTestCase):
    """world.email.send_email_result: one daily + hourly cap for all mail,
    saved on the volume, failing closed."""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp(prefix="mail_quota_test_")
        env = {k: v for k, v in os.environ.items()
               if k not in ("RAILWAY_ENVIRONMENT_NAME", "EMAIL_DAILY_LIMIT",
                            "EMAIL_HOURLY_LIMIT")}
        env["RAILWAY_VOLUME_MOUNT_PATH"] = self.tmp
        self._env = mock.patch.dict(os.environ, env, clear=True)
        self._env.start()
        from world import email as wemail
        self.wemail = wemail
        self._key = mock.patch.object(wemail, "RESEND_API_KEY",
                                      "re_test_not_a_real_key")
        self._key.start()
        self.posts = []

        class _Resp:
            def read(self_inner):
                return b'{"id": "test"}'

        def fake_urlopen(req, timeout=None):
            self.posts.append(req)
            return _Resp()

        self._urlopen = mock.patch("urllib.request.urlopen",
                                   side_effect=fake_urlopen)
        self._urlopen.start()
        self._alert = mock.patch("world.telemetry.alert")
        self._alert.start()

    def tearDown(self):
        import shutil
        self._alert.stop()
        self._urlopen.stop()
        self._key.stop()
        self._env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _send(self, to="p@example.com"):
        return self.wemail.send_email_result(to, "s", "<p>b</p>")

    def test_daily_cap_with_admin_reserve(self):
        os.environ["EMAIL_DAILY_LIMIT"] = "7"  # 2 for players, 5 reserved
        self.assertEqual(self._send(), (True, None))
        self.assertEqual(self._send(), (True, None))
        self.assertEqual(self._send(), (False, "daily_cap"))
        self.assertEqual(self._send(self.wemail.ADMIN_EMAIL), (True, None))
        self.assertEqual(len(self.posts), 3)

    def test_hourly_burst_cap(self):
        os.environ["EMAIL_HOURLY_LIMIT"] = "2"
        self._send()
        self._send()
        self.assertEqual(self._send(), (False, "hourly_cap"))

    def test_count_survives_restart_and_counts_recipients(self):
        os.environ["EMAIL_DAILY_LIMIT"] = "8"
        self.wemail.send_email_result(["a@x.test", "b@x.test"], "s", "h",
                                      cc=["c@x.test"])
        with open(os.path.join(self.tmp, "mail_quota.json")) as fp:
            import json
            self.assertEqual(json.load(fp)["count"], 3)
        # 3 used + 3 limit for players (8 - 5 reserve) = full.
        self.assertEqual(self._send(), (False, "daily_cap"))

    def test_corrupt_store_fails_closed(self):
        with open(os.path.join(self.tmp, "mail_quota.json"), "w") as fp:
            fp.write("{nope")
        self.assertEqual(self._send(), (False, "store_error"))
        self.assertEqual(self.posts, [])

    def test_deployed_without_volume_fails_closed(self):
        del os.environ["RAILWAY_VOLUME_MOUNT_PATH"]
        os.environ["RAILWAY_ENVIRONMENT_NAME"] = "production"
        self.assertEqual(self._send(), (False, "store_error"))

    def test_failed_send_gives_slot_back(self):
        os.environ["EMAIL_DAILY_LIMIT"] = "6"  # 1 player slot
        with mock.patch("urllib.request.urlopen",
                        side_effect=OSError("down")):
            self.assertEqual(self._send(), (False, "provider_error"))
        self.assertEqual(self._send(), (True, None))


class AllauthMailSettingsTests(SimpleTestCase):

    def test_settings(self):
        from django.conf import settings
        from allauth.account import app_settings
        self.assertFalse(settings.ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS)
        rls = app_settings.RATE_LIMITS
        self.assertEqual(rls["reset_password"], "10/h/ip,3/h/key")
        self.assertEqual(rls["signup"], "5/h/ip")
        self.assertEqual(rls["login"], "30/m/ip")  # defaults kept
        self.assertEqual(settings.ALLAUTH_TRUSTED_PROXY_COUNT, 0)  # local


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

    def test_mixed_case_verified_row_does_not_count(self):
        # allauth's own lookup matches lowercased addresses exactly, so a
        # row it wouldn't find must not unlock email authentication.
        from allauth.account.models import EmailAddress
        EmailAddress.objects.create(user=self.account,
                                    email="Victim@Gmail.com",
                                    verified=True, primary=True)
        login = SimpleNamespace(provider=self._provider_stub())
        self.assertFalse(
            self._adapter().can_authenticate_by_email(login,
                                                      "victim@gmail.com"))

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
