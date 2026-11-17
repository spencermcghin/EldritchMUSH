"""
Tests for the AI spend-safety layer (world/ai_npc.py, world/ai_safety.py,
world/ai_pricing.py, the fortune cabinet in world/living_world.py).

Run from eldritchmush/:

    DJANGO_SECRET_KEY=<any local test value> evennia test --settings settings.py world.tests

No test makes a network call: provider calls, urlopen and admin alerts
are all mocked.
"""
import json
import os
import shutil
import tempfile
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase
from evennia.utils.test_resources import EvenniaTest

from world import ai_npc, ai_pricing, ai_safety, living_world, telemetry


# Env vars that steer the AI layer. Each test starts from none of them
# set, then adds what it needs.
_AI_ENV = [
    "NPC_LLM_ENABLED", "NPC_LLM_PROVIDER", "NPC_LLM_API_KEY",
    "NPC_LLM_BASE_URL", "NPC_LLM_MODEL", "NPC_LLM_FALLBACK_MODELS",
    "NPC_LLM_MAX_TOKENS", "NPC_LLM_DAILY_BUDGET_USD",
    "NPC_LLM_GLOBAL_HOURLY_LIMIT", "NPC_ACCT_RATE_LIMIT",
    "NPC_LLM_MODERATE", "NPC_MODERATE_API_KEY", "NPC_MODERATE_BASE_URL",
    "NPC_LLM_MODERATE_MODEL", "NPC_AI_REQUIRE_VERIFIED", "NPC_AUDIT_PATH",
    "RAILWAY_VOLUME_MOUNT_PATH", "RAILWAY_ENVIRONMENT_NAME",
]

# A fake value only; never a real key.
_FAKE_ANTHROPIC_KEY = "sk-ant-test-not-a-real-key"
_FAKE_GROQ_KEY = "gsk-test-not-a-real-key"


class _AIEnvMixin:
    """Isolates env vars, the spend store, the global cap and alerts."""

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp(prefix="ai_spend_test_")
        env = {k: v for k, v in os.environ.items() if k not in _AI_ENV}
        env["RAILWAY_VOLUME_MOUNT_PATH"] = self.tmp
        env["NPC_AUDIT_PATH"] = os.path.join(self.tmp, "npc_audit.log")
        self._env = mock.patch.dict(os.environ, env, clear=True)
        self._env.start()
        self._alert = mock.patch.object(telemetry, "alert")
        self.alert = self._alert.start()
        # Run reply callbacks inline (no reactor in tests).
        self._dispatch = mock.patch.object(
            ai_npc, "_dispatch", side_effect=lambda fn, *a: fn(*a))
        self._dispatch.start()
        self._reset_state()

    def tearDown(self):
        self._dispatch.stop()
        self._alert.stop()
        self._env.stop()
        self._reset_state()
        shutil.rmtree(self.tmp, ignore_errors=True)
        super().tearDown()

    def _reset_state(self):
        with ai_npc._SPEND_LOCK:
            ai_npc._SPEND.update(day=None, usd=0.0, warned=False)
        ai_npc._STORE.update(ok=True, error=None, last_retry=0.0)
        with ai_npc._GLOBAL_LOCK:
            ai_npc._GLOBAL_HITS.clear()
        ai_safety._MOD_WARNED.clear()

    def spend_today(self):
        with ai_npc._SPEND_LOCK:
            return ai_npc._SPEND["usd"]


def _anthropic_response(model, inp, out, cw=0, cr=0, text="Aye."):
    return SimpleNamespace(
        model=model,
        content=[SimpleNamespace(type="text", text=text)],
        usage=SimpleNamespace(
            input_tokens=inp, output_tokens=out,
            cache_creation_input_tokens=cw, cache_read_input_tokens=cr),
    )


class _FakeHTTPResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


# ---------------------------------------------------------------------------
# 1. Budget priced by the model actually used
# ---------------------------------------------------------------------------
class PricingTableTests(SimpleTestCase):

    def test_prices_differ_by_model(self):
        args = dict(input_tokens=1_000_000, output_tokens=1_000_000)
        haiku = ai_pricing.cost_usd("claude-haiku-4-5", **args)
        sonnet = ai_pricing.cost_usd("claude-sonnet-4-6", **args)
        opus = ai_pricing.cost_usd("claude-opus-4-8", **args)
        self.assertAlmostEqual(haiku, 6.00)
        self.assertAlmostEqual(sonnet, 18.00)
        self.assertAlmostEqual(opus, 30.00)

    def test_cache_tokens_priced(self):
        usd = ai_pricing.cost_usd(
            "claude-haiku-4-5", cache_write_tokens=1_000_000,
            cache_read_tokens=1_000_000)
        self.assertAlmostEqual(usd, 1.25 + 0.10)

    def test_groq_models_in_use_are_priced(self):
        for m in ai_npc.DEFAULT_FALLBACK_MODELS.split(","):
            self.assertTrue(ai_pricing.is_priced(m), m)
        self.assertTrue(ai_pricing.is_priced(ai_npc.DEFAULT_MODEL))
        self.assertTrue(ai_pricing.is_priced(ai_npc.DEFAULT_ANTHROPIC_MODEL))
        self.assertTrue(ai_pricing.is_priced("llama-guard-4-12b"))
        self.assertAlmostEqual(
            ai_pricing.cost_usd("openai/gpt-oss-120b",
                                input_tokens=1_000_000,
                                output_tokens=1_000_000),
            0.15 + 0.60)

    def test_dated_anthropic_id_matches_alias(self):
        self.assertEqual(ai_pricing.price_for("claude-haiku-4-5-20251001"),
                         ai_pricing.PRICES["claude-haiku-4-5"])

    def test_unknown_model_raises(self):
        self.assertFalse(ai_pricing.is_priced("claude-mystery-9"))
        with self.assertRaises(ai_pricing.UnknownModelError):
            ai_pricing.cost_usd("claude-mystery-9", input_tokens=10)


class ModelPricedSpendTests(_AIEnvMixin, SimpleTestCase):

    def _npc(self):
        return SimpleNamespace(key="Gerald", id=1)

    def test_unpriced_model_refuses_to_start(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY
        os.environ["NPC_LLM_MODEL"] = "claude-mystery-9"
        self.assertIsNotNone(ai_npc._config_error())
        self.assertFalse(ai_npc._enabled())
        ai_npc._check_config_at_start()
        self.assertTrue(self.alert.called)
        with mock.patch.object(ai_npc, "_generate_anthropic") as gen:
            self.assertIsNone(ai_npc.generate_sync("sys", "user"))
            gen.assert_not_called()

    def test_priced_model_starts(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY
        os.environ["NPC_LLM_MODEL"] = "claude-sonnet-4-6"
        self.assertIsNone(ai_npc._config_error())
        self.assertTrue(ai_npc._enabled())

    def test_sonnet_call_charged_at_sonnet_rates(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY
        os.environ["NPC_LLM_MODEL"] = "claude-sonnet-4-6"
        client = mock.Mock()
        client.messages.create.return_value = _anthropic_response(
            "claude-sonnet-4-6", inp=10_000, out=500, cw=2_000, cr=6_000)
        with mock.patch.object(ai_npc, "_anthropic_client",
                               return_value=client):
            text = ai_npc.generate_sync("sys", "user", max_tokens=500)
        self.assertEqual(text, "Aye.")
        expected = (10_000 * 3.00 + 500 * 15.00 + 2_000 * 3.75
                    + 6_000 * 0.30) / 1_000_000
        self.assertAlmostEqual(self.spend_today(), expected)
        # The old code would have charged Haiku rates: a third of this.
        haiku = ai_pricing.cost_usd("claude-haiku-4-5", 10_000, 500,
                                    2_000, 6_000)
        self.assertGreater(self.spend_today(), 2.9 * haiku)

    def test_openai_fallback_charged_at_the_model_that_answered(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_GROQ_KEY
        os.environ["NPC_LLM_PROVIDER"] = "openai"
        os.environ["NPC_LLM_MODEL"] = "openai/gpt-oss-120b"
        os.environ["NPC_LLM_FALLBACK_MODELS"] = (
            "openai/gpt-oss-20b,unpriced/model")
        calls = []

        def fake_urlopen(req, timeout=None):
            body = json.loads(req.data.decode("utf-8"))
            calls.append(body["model"])
            content = "" if body["model"] == "openai/gpt-oss-120b" else "Hm."
            return _FakeHTTPResponse({
                "choices": [{"message": {"content": content}}],
                "usage": {"prompt_tokens": 1_000, "completion_tokens": 100},
            })

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            text = ai_npc.generate_sync("sys", "user", max_tokens=100)
        self.assertEqual(text, "Hm.")
        self.assertEqual(calls, ["openai/gpt-oss-120b", "openai/gpt-oss-20b"])
        expected = (
            ai_pricing.cost_usd("openai/gpt-oss-120b", 1_000, 100)
            + ai_pricing.cost_usd("openai/gpt-oss-20b", 1_000, 100))
        self.assertAlmostEqual(self.spend_today(), expected)

    def test_unpriced_fallback_model_is_skipped(self):
        os.environ["NPC_LLM_PROVIDER"] = "openai"
        os.environ["NPC_LLM_MODEL"] = "openai/gpt-oss-120b"
        os.environ["NPC_LLM_FALLBACK_MODELS"] = "unpriced/model"
        self.assertEqual(ai_npc._model_candidates(), ["openai/gpt-oss-120b"])

    def test_moderation_call_counts_against_budget(self):
        os.environ["NPC_LLM_MODERATE"] = "1"
        os.environ["NPC_MODERATE_API_KEY"] = _FAKE_GROQ_KEY
        payload = {
            "choices": [{"message": {"content": "safe"}}],
            "usage": {"prompt_tokens": 400, "completion_tokens": 2},
        }
        with mock.patch("urllib.request.urlopen",
                        return_value=_FakeHTTPResponse(payload)):
            ok, cat = ai_safety.check_moderation("hello there")
        self.assertTrue(ok)
        self.assertAlmostEqual(
            self.spend_today(),
            ai_pricing.cost_usd("llama-guard-4-12b", 400, 2))


# ---------------------------------------------------------------------------
# 2. Daily spend survives restarts; unreadable store = budget exhausted
# ---------------------------------------------------------------------------
class SpendStoreTests(_AIEnvMixin, SimpleTestCase):

    def _simulate_restart(self):
        with ai_npc._SPEND_LOCK:
            ai_npc._SPEND.update(day=None, usd=0.0, warned=False)
        ai_npc._STORE.update(ok=True, error=None, last_retry=0.0)
        ai_npc._load_spend()

    def test_spend_survives_restart(self):
        ai_npc.charge("claude-haiku-4-5", 1_000_000, 0)
        self._simulate_restart()
        self.assertAlmostEqual(self.spend_today(), 1.00)
        with open(os.path.join(self.tmp, "llm_spend.json")) as fp:
            self.assertAlmostEqual(json.load(fp)["usd"], 1.00)

    def test_budget_reached_stays_reached_after_restart(self):
        os.environ["NPC_LLM_DAILY_BUDGET_USD"] = "1.0"
        ai_npc.charge("claude-haiku-4-5", 1_000_000, 0)
        self._simulate_restart()
        self.assertFalse(ai_npc._spend_ok())

    def test_corrupt_store_means_budget_exhausted(self):
        with open(os.path.join(self.tmp, "llm_spend.json"), "w") as fp:
            fp.write("{not json")
        self._simulate_restart()
        self.assertFalse(ai_npc._STORE["ok"])
        self.assertFalse(ai_npc._spend_ok())

    def test_deployed_without_volume_means_budget_exhausted(self):
        del os.environ["RAILWAY_VOLUME_MOUNT_PATH"]
        os.environ["RAILWAY_ENVIRONMENT_NAME"] = "uat"
        self._simulate_restart()
        self.assertFalse(ai_npc._spend_ok())

    def test_store_recovers_once_readable(self):
        path = os.path.join(self.tmp, "llm_spend.json")
        with open(path, "w") as fp:
            fp.write("{not json")
        self._simulate_restart()
        self.assertFalse(ai_npc._spend_ok())
        os.remove(path)
        ai_npc._STORE["last_retry"] = 0.0
        self.assertTrue(ai_npc._spend_ok())


# ---------------------------------------------------------------------------
# 3. Verified email or Google sign-in required
# ---------------------------------------------------------------------------
class VerifiedAccountTests(_AIEnvMixin, EvenniaTest):

    def _verify_email(self):
        from allauth.account.models import EmailAddress
        EmailAddress.objects.create(
            user=self.account, email="tester@example.com",
            verified=True, primary=True)

    def test_unverified_account_not_eligible(self):
        self.assertFalse(ai_safety.account_ai_eligible(self.account))

    def test_unverified_email_not_eligible(self):
        from allauth.account.models import EmailAddress
        EmailAddress.objects.create(
            user=self.account, email="tester@example.com",
            verified=False, primary=True)
        self.assertFalse(ai_safety.account_ai_eligible(self.account))

    def test_verified_email_eligible(self):
        self._verify_email()
        self.assertTrue(ai_safety.account_ai_eligible(self.account))

    def test_google_signin_eligible(self):
        from allauth.socialaccount.models import SocialAccount
        SocialAccount.objects.create(
            user=self.account, provider="google", uid="1234567890")
        self.assertTrue(ai_safety.account_ai_eligible(self.account))

    def test_no_account_not_eligible(self):
        self.assertFalse(ai_safety.account_ai_eligible(None))

    def test_unverified_chat_gets_canned_line_and_hint_without_ai_call(self):
        from world import email_verification
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY
        npc = SimpleNamespace(key="Gerald", id=99,
                              db=SimpleNamespace(body=None, bleed_points=None))
        char = SimpleNamespace(key="Tester", id=7, account=self.account,
                               msg=mock.Mock())
        replies = []
        with mock.patch.object(ai_npc, "_call_llm") as call_llm, \
                mock.patch.object(ai_npc._EXECUTOR, "submit") as submit:
            ai_npc.chat(npc, char, "Good evening", replies.append)
        call_llm.assert_not_called()
        submit.assert_not_called()
        self.assertEqual(len(replies), 1)
        canned = [c.format(name="Gerald") for c in ai_npc.CANNED_FALLBACKS]
        self.assertIn(replies[0], canned)
        char.msg.assert_called_once()
        self.assertIn(email_verification.VERIFY_HINT, char.msg.call_args[0][0])

    def test_verified_chat_is_queued(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY
        self._verify_email()
        npc = SimpleNamespace(key="Gerald", id=99,
                              db=SimpleNamespace(body=None, bleed_points=None))
        char = SimpleNamespace(key="Tester", id=7, account=self.account)
        with mock.patch.object(ai_npc._EXECUTOR, "submit") as submit:
            ai_npc.chat(npc, char, "Good evening", lambda r: None)
        submit.assert_called_once()

    def test_unverified_fortune_is_canned(self):
        char = SimpleNamespace(key="Tester", account=self.account,
                               msg=mock.Mock())
        out = []
        with mock.patch.object(ai_npc, "generate") as gen:
            living_world.true_fortune(char, out.append)
        gen.assert_not_called()
        self.assertIn(out[0], living_world.FORTUNE_FALLBACKS)
        char.msg.assert_called_once()

    def _letter_char(self, account_for_lock):
        return SimpleNamespace(
            key="Thief", account=None,
            locks=SimpleNamespace(
                get=lambda k: (f"puppet:id(50) or pid({account_for_lock.id})"
                               f" or perm(Developer)")),
            db=SimpleNamespace(faction_rep={}))

    def test_unverified_letter_is_canned(self):
        char = self._letter_char(self.account)
        with mock.patch.object(ai_npc, "generate") as gen, \
                mock.patch.object(living_world, "_spawn_letter") as spawn, \
                mock.patch.object(living_world, "_schedule_letter"):
            living_world.deliver_letter(char, 0)
        gen.assert_not_called()
        body = spawn.call_args[0][2]
        self.assertEqual(body,
                         living_world._CANNED_LETTERS[0].format(name="Thief"))

    def test_verified_letter_uses_ai_even_when_offline(self):
        self._verify_email()
        char = self._letter_char(self.account)  # not puppeted
        self.assertEqual(ai_safety.account_for_character(char).id,
                         self.account.id)
        with mock.patch.object(ai_npc, "generate") as gen, \
                mock.patch.object(living_world, "_spawn_letter"), \
                mock.patch.object(living_world, "_schedule_letter"):
            living_world.deliver_letter(char, 0)
        gen.assert_called_once()


# ---------------------------------------------------------------------------
# 4. Global hourly cap
# ---------------------------------------------------------------------------
class GlobalHourlyCapTests(_AIEnvMixin, SimpleTestCase):

    def test_default_is_300(self):
        self.assertEqual(ai_npc._global_limit(), 300)

    def test_cap_blocks_after_limit(self):
        os.environ["NPC_LLM_GLOBAL_HOURLY_LIMIT"] = "3"
        self.assertEqual([ai_npc._global_rate_ok() for _ in range(4)],
                         [True, True, True, False])
        self.assertTrue(self.alert.called)

    def test_old_hits_expire(self):
        os.environ["NPC_LLM_GLOBAL_HOURLY_LIMIT"] = "1"
        with ai_npc._GLOBAL_LOCK:
            ai_npc._GLOBAL_HITS.append(0.0)  # far older than an hour
        self.assertTrue(ai_npc._global_rate_ok())

    def test_generate_sync_blocked_when_cap_full(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY
        os.environ["NPC_LLM_GLOBAL_HOURLY_LIMIT"] = "1"
        client = mock.Mock()
        client.messages.create.return_value = _anthropic_response(
            "claude-haiku-4-5", 100, 10)
        with mock.patch.object(ai_npc, "_anthropic_client",
                               return_value=client):
            self.assertEqual(ai_npc.generate_sync("s", "u"), "Aye.")
            self.assertIsNone(ai_npc.generate_sync("s", "u"))
        self.assertEqual(client.messages.create.call_count, 1)


class _InlineChatMixin:
    """Runs ai_npc.chat()'s worker inline with a fake Anthropic client
    and the prompt/history plumbing stubbed out."""

    def setUp(self):
        super().setUp()
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY
        os.environ["NPC_AI_REQUIRE_VERIFIED"] = "0"
        self.client = mock.Mock()
        self.client.messages.create.return_value = _anthropic_response(
            "claude-haiku-4-5", 1_000, 50)
        self._patches = [
            mock.patch.object(ai_npc, "_anthropic_client",
                              return_value=self.client),
            mock.patch.object(ai_npc, "_build_prompt_blocks",
                              return_value=("static", "npc", "")),
            mock.patch.object(ai_npc, "_get_history", return_value=[]),
            mock.patch.object(ai_npc, "_save_history"),
            mock.patch.object(ai_npc, "_rate_check", return_value=(True, 0)),
        ]
        for p in self._patches:
            p.start()
        self.npc = SimpleNamespace(
            key="Gerald", id=99,
            db=SimpleNamespace(body=None, bleed_points=None))

    def tearDown(self):
        for p in self._patches:
            p.stop()
        super().tearDown()

    def chat_inline(self, char, text="Evening"):
        replies = []
        with mock.patch.object(ai_npc._EXECUTOR, "submit",
                               side_effect=lambda fn: fn()):
            ai_npc.chat(self.npc, char, text, replies.append)
        return replies


class GlobalCapChatTests(_InlineChatMixin, _AIEnvMixin, EvenniaTest):

    def test_chat_from_many_accounts_hits_global_cap(self):
        os.environ["NPC_LLM_GLOBAL_HOURLY_LIMIT"] = "2"
        chars = [SimpleNamespace(key=f"C{i}", id=i, account=acct)
                 for i, acct in enumerate([self.account, self.account2,
                                           self.account, self.account2])]
        replies = [self.chat_inline(c)[0] for c in chars]
        self.assertEqual(self.client.messages.create.call_count, 2)
        canned = [c.format(name="Gerald") for c in ai_npc.CANNED_FALLBACKS]
        self.assertEqual(replies[:2], ["Aye.", "Aye."])
        self.assertIn(replies[2], canned)
        self.assertIn(replies[3], canned)

    def test_slot_taken_at_provider_call_not_before_npc_limit(self):
        os.environ["NPC_LLM_GLOBAL_HOURLY_LIMIT"] = "1"
        char = SimpleNamespace(key="C", id=1, account=self.account)
        with mock.patch.object(ai_npc, "_rate_check",
                               return_value=(False, 5)):
            self.chat_inline(char)  # refused by the per-NPC limit
        self.assertEqual(len(ai_npc._GLOBAL_HITS), 0)
        self.assertEqual(self.chat_inline(char), ["Aye."])

    def test_moderation_takes_its_own_slot(self):
        os.environ["NPC_LLM_GLOBAL_HOURLY_LIMIT"] = "1"
        os.environ["NPC_LLM_MODERATE"] = "1"
        os.environ["NPC_MODERATE_API_KEY"] = _FAKE_GROQ_KEY
        payload = {"choices": [{"message": {"content": "safe"}}],
                   "usage": {"prompt_tokens": 10, "completion_tokens": 1}}
        char = SimpleNamespace(key="C", id=1, account=self.account)
        with mock.patch("urllib.request.urlopen",
                        return_value=_FakeHTTPResponse(payload)):
            replies = self.chat_inline(char)
        # Moderation used the only slot, so the main call was refused.
        self.client.messages.create.assert_not_called()
        canned = [c.format(name="Gerald") for c in ai_npc.CANNED_FALLBACKS]
        self.assertIn(replies[0], canned)


class BudgetRecheckTests(_InlineChatMixin, _AIEnvMixin, EvenniaTest):

    def test_budget_spent_while_queued_blocks_the_call(self):
        os.environ["NPC_LLM_DAILY_BUDGET_USD"] = "1.0"
        char = SimpleNamespace(key="C", id=1, account=self.account)
        queued = []
        replies = []
        with mock.patch.object(ai_npc._EXECUTOR, "submit",
                               side_effect=queued.append):
            ai_npc.chat(self.npc, char, "Evening", replies.append)
        self.assertEqual(len(queued), 1)
        ai_npc.charge("claude-haiku-4-5", 1_000_000, 0)  # $1: budget gone
        queued[0]()
        self.client.messages.create.assert_not_called()
        canned = [c.format(name="Gerald") for c in ai_npc.CANNED_FALLBACKS]
        self.assertIn(replies[0], canned)

    def test_budget_rechecked_between_fallback_attempts(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_GROQ_KEY
        os.environ["NPC_LLM_PROVIDER"] = "openai"
        os.environ["NPC_LLM_MODEL"] = "openai/gpt-oss-120b"
        os.environ["NPC_LLM_FALLBACK_MODELS"] = "openai/gpt-oss-20b"
        os.environ["NPC_LLM_DAILY_BUDGET_USD"] = "0.10"
        calls = []

        def fake_urlopen(req, timeout=None):
            calls.append(json.loads(req.data.decode("utf-8"))["model"])
            # Empty reply that costs more than the whole budget.
            return _FakeHTTPResponse({
                "choices": [{"message": {"content": ""}}],
                "usage": {"prompt_tokens": 1_000_000,
                          "completion_tokens": 0}})

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            self.assertIsNone(ai_npc.generate_sync("s", "u"))
        self.assertEqual(calls, ["openai/gpt-oss-120b"])


# ---------------------------------------------------------------------------
# 5. Fortune pulls count against the per-account rate limit
# ---------------------------------------------------------------------------
class FortuneAccountRateTests(_AIEnvMixin, EvenniaTest):

    def test_pulls_consume_account_limit(self):
        os.environ["NPC_ACCT_RATE_LIMIT"] = "2"
        os.environ["NPC_AI_REQUIRE_VERIFIED"] = "0"
        # Three characters on one account, so the per-character cooldown
        # is not what stops the third pull.
        chars = [SimpleNamespace(key=f"Teller{i}", account=self.account)
                 for i in range(3)]
        out = []
        with mock.patch.object(ai_npc, "generate") as gen, \
                mock.patch.object(living_world, "_fortune_digest",
                                  return_value="A stranger"):
            for c in chars:
                living_world.true_fortune(c, out.append)
        self.assertEqual(gen.call_count, 2)
        self.assertEqual(len(out), 1)
        self.assertIn(out[0], living_world.FORTUNE_FALLBACKS)
        state = self.account.attributes.get("ai_acct_rate_state")
        self.assertEqual(len(state["hits"]), 2)

    def test_fortune_and_chat_share_the_account_limit(self):
        os.environ["NPC_ACCT_RATE_LIMIT"] = "1"
        os.environ["NPC_AI_REQUIRE_VERIFIED"] = "0"
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY
        char = SimpleNamespace(key="Teller", id=5, account=self.account)
        with mock.patch.object(ai_npc, "generate"), \
                mock.patch.object(living_world, "_fortune_digest",
                                  return_value="A stranger"):
            living_world.true_fortune(char, lambda f: None)
        npc = SimpleNamespace(key="Gerald", id=99,
                              db=SimpleNamespace(body=None, bleed_points=None))
        replies = []
        with mock.patch.object(ai_npc._EXECUTOR, "submit") as submit:
            ai_npc.chat(npc, char, "Evening", replies.append)
        submit.assert_not_called()
        self.assertIn("Come back in about", replies[0])


# ---------------------------------------------------------------------------
# 6. The main key is never sent to the moderation provider
# ---------------------------------------------------------------------------
class ModerationKeyTests(_AIEnvMixin, SimpleTestCase):

    def test_no_fallback_to_main_key(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY
        os.environ["NPC_LLM_MODERATE"] = "1"
        self.assertIsNone(ai_safety._moderation_key())
        with mock.patch("builtins.print") as pr:
            self.assertFalse(ai_safety.moderation_enabled())
        self.assertTrue(any("NPC_MODERATE_API_KEY is not set" in str(c)
                            for c in pr.call_args_list))

    def test_check_moderation_makes_no_request_without_key(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY
        os.environ["NPC_LLM_MODERATE"] = "1"
        with mock.patch("urllib.request.urlopen") as urlopen:
            self.assertEqual(ai_safety.check_moderation("hello"), (True, None))
        urlopen.assert_not_called()

    def test_moderation_uses_its_own_key(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY
        os.environ["NPC_LLM_MODERATE"] = "1"
        os.environ["NPC_MODERATE_API_KEY"] = _FAKE_GROQ_KEY
        seen = []

        def fake_urlopen(req, timeout=None):
            seen.append(req.get_header("Authorization"))
            return _FakeHTTPResponse({
                "choices": [{"message": {"content": "safe"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 1}})

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            ai_safety.check_moderation("hello")
        self.assertEqual(seen, [f"Bearer {_FAKE_GROQ_KEY}"])
        self.assertNotIn(_FAKE_ANTHROPIC_KEY, seen[0])

    def test_unpriced_moderation_model_disables_moderation(self):
        os.environ["NPC_LLM_MODERATE"] = "1"
        os.environ["NPC_MODERATE_API_KEY"] = _FAKE_GROQ_KEY
        os.environ["NPC_LLM_MODERATE_MODEL"] = "unpriced-guard"
        self.assertFalse(ai_safety.moderation_enabled())


# ---------------------------------------------------------------------------
# Review fixes: failed attempts charged, no hidden retries, alerts, tiers
# ---------------------------------------------------------------------------
class FailedAttemptChargeTests(_AIEnvMixin, SimpleTestCase):

    def _estimate(self, model, max_tokens):
        return ai_pricing.cost_usd(
            model, ai_npc._MISSING_USAGE_INPUT_TOKENS, max_tokens)

    def test_anthropic_timeout_is_charged(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY
        client = mock.Mock()
        client.messages.create.side_effect = TimeoutError("read timed out")
        with mock.patch.object(ai_npc, "_anthropic_client",
                               return_value=client):
            self.assertIsNone(ai_npc.generate_sync("s", "u", max_tokens=200))
        self.assertAlmostEqual(self.spend_today(),
                               self._estimate("claude-haiku-4-5", 200))

    def test_anthropic_rejected_request_is_not_charged(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY

        class BadRequest(Exception):
            status_code = 400

        client = mock.Mock()
        client.messages.create.side_effect = BadRequest("nope")
        with mock.patch.object(ai_npc, "_anthropic_client",
                               return_value=client):
            self.assertIsNone(ai_npc.generate_sync("s", "u"))
        self.assertEqual(self.spend_today(), 0.0)

    def test_anthropic_client_has_no_hidden_retries(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY
        with mock.patch.object(ai_npc, "_ANTH_CLIENT", None), \
                mock.patch("anthropic.Anthropic") as ctor:
            ai_npc._anthropic_client()
        self.assertEqual(ctor.call_args.kwargs["max_retries"], 0)

    def _groq_env(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_GROQ_KEY
        os.environ["NPC_LLM_PROVIDER"] = "openai"
        os.environ["NPC_LLM_MODEL"] = "openai/gpt-oss-120b"
        os.environ["NPC_LLM_FALLBACK_MODELS"] = ""

    def test_groq_timeout_is_charged(self):
        import socket
        self._groq_env()
        with mock.patch("urllib.request.urlopen",
                        side_effect=socket.timeout("timed out")):
            self.assertIsNone(ai_npc.generate_sync("s", "u", max_tokens=100))
        self.assertAlmostEqual(self.spend_today(),
                               self._estimate("openai/gpt-oss-120b", 100))

    def _http_error(self, code):
        import io
        import urllib.error
        return urllib.error.HTTPError(
            "https://api.groq.com/openai/v1/chat/completions", code, "err",
            {}, io.BytesIO(b"{}"))

    def test_groq_server_error_is_charged(self):
        self._groq_env()
        with mock.patch("urllib.request.urlopen",
                        side_effect=self._http_error(503)):
            self.assertIsNone(ai_npc.generate_sync("s", "u", max_tokens=100))
        self.assertAlmostEqual(self.spend_today(),
                               self._estimate("openai/gpt-oss-120b", 100))

    def test_groq_rate_limit_is_not_charged(self):
        self._groq_env()
        with mock.patch("urllib.request.urlopen",
                        side_effect=self._http_error(429)):
            self.assertIsNone(ai_npc.generate_sync("s", "u"))
        self.assertEqual(self.spend_today(), 0.0)

    def test_moderation_timeout_is_charged(self):
        import socket
        os.environ["NPC_LLM_MODERATE"] = "1"
        os.environ["NPC_MODERATE_API_KEY"] = _FAKE_GROQ_KEY
        with mock.patch("urllib.request.urlopen",
                        side_effect=socket.timeout("timed out")):
            self.assertEqual(ai_safety.check_moderation("hi"), (True, None))
        self.assertAlmostEqual(
            self.spend_today(),
            ai_pricing.cost_usd("llama-guard-4-12b", 1002, 32))


class TelemetryAlertTests(SimpleTestCase):

    def setUp(self):
        telemetry._ALERT_SENT.pop("test_kind", None)

    def tearDown(self):
        telemetry._ALERT_SENT.pop("test_kind", None)

    def test_cooldown_checked_first_and_email_sent_off_thread(self):
        with mock.patch.object(telemetry.threading, "Thread") as thread, \
                mock.patch("builtins.print") as pr:
            self.assertTrue(telemetry.alert("test_kind", "subj", "body"))
            self.assertFalse(telemetry.alert("test_kind", "subj", "body"))
        self.assertEqual(thread.call_count, 1)
        thread.return_value.start.assert_called_once()
        self.assertEqual(thread.call_args.kwargs["target"],
                         telemetry._send_alert_email)
        alert_lines = [c for c in pr.call_args_list
                       if "ALERT (test_kind)" in str(c)]
        self.assertEqual(len(alert_lines), 1)


class LongPromptTierTests(SimpleTestCase):

    def test_haiku_5_5_short_prompt(self):
        self.assertAlmostEqual(
            ai_pricing.cost_usd("claude-haiku-5-5", 100_000, 1_000_000),
            (100_000 * 0.10 + 1_000_000 * 0.50) / 1_000_000)

    def test_haiku_5_5_long_prompt_counts_cache_tokens(self):
        usd = ai_pricing.cost_usd("claude-haiku-5-5", input_tokens=50_000,
                                  output_tokens=1_000,
                                  cache_write_tokens=30_000,
                                  cache_read_tokens=30_000)
        expected = (50_000 * 0.50 + 1_000 * 2.50 + 30_000 * 0.625
                    + 30_000 * 0.05) / 1_000_000
        self.assertAlmostEqual(usd, expected)

    def test_other_models_have_no_tier(self):
        self.assertEqual(ai_pricing.price_for("claude-haiku-4-5", 500_000),
                         ai_pricing.PRICES["claude-haiku-4-5"])


class PreSendErrorTests(_AIEnvMixin, SimpleTestCase):
    """Errors raised before anything reached the provider aren't charged."""

    def test_anthropic_value_error_not_charged(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY
        client = mock.Mock()
        client.messages.create.side_effect = ValueError("bad argument")
        with mock.patch.object(ai_npc, "_anthropic_client",
                               return_value=client):
            self.assertIsNone(ai_npc.generate_sync("s", "u"))
        self.assertEqual(self.spend_today(), 0.0)

    def test_anthropic_auth_error_not_charged(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY

        class AuthError(Exception):
            status_code = 401

        client = mock.Mock()
        client.messages.create.side_effect = AuthError("bad key")
        with mock.patch.object(ai_npc, "_anthropic_client",
                               return_value=client):
            self.assertIsNone(ai_npc.generate_sync("s", "u"))
        self.assertEqual(self.spend_today(), 0.0)

    def test_groq_refused_connection_not_charged(self):
        import urllib.error
        os.environ["NPC_LLM_API_KEY"] = _FAKE_GROQ_KEY
        os.environ["NPC_LLM_PROVIDER"] = "openai"
        os.environ["NPC_LLM_FALLBACK_MODELS"] = ""
        with mock.patch("urllib.request.urlopen",
                        side_effect=urllib.error.URLError(
                            ConnectionRefusedError("refused"))):
            self.assertIsNone(ai_npc.generate_sync("s", "u"))
        self.assertEqual(self.spend_today(), 0.0)

    def test_maybe_billed_classification(self):
        import socket
        import urllib.error
        self.assertTrue(ai_npc.maybe_billed(socket.timeout()))
        self.assertTrue(ai_npc.maybe_billed(ConnectionResetError()))
        self.assertTrue(ai_npc.maybe_billed(
            urllib.error.URLError(socket.timeout())))
        self.assertFalse(ai_npc.maybe_billed(TypeError()))
        self.assertFalse(ai_npc.maybe_billed(
            urllib.error.URLError(socket.gaierror())))
