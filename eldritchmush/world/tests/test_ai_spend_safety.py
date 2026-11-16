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

    def test_unverified_chat_gets_canned_line_without_ai_call(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY
        npc = SimpleNamespace(key="Gerald", id=99,
                              db=SimpleNamespace(body=None, bleed_points=None))
        char = SimpleNamespace(key="Tester", id=7, account=self.account)
        replies = []
        with mock.patch.object(ai_npc, "_call_llm") as call_llm, \
                mock.patch.object(ai_npc._EXECUTOR, "submit") as submit:
            ai_npc.chat(npc, char, "Good evening", replies.append)
        call_llm.assert_not_called()
        submit.assert_not_called()
        self.assertEqual(len(replies), 1)
        canned = [c.format(name="Gerald") for c in ai_npc.CANNED_FALLBACKS]
        self.assertIn(replies[0], canned)

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
        char = SimpleNamespace(key="Tester", account=self.account)
        out = []
        with mock.patch.object(ai_npc, "generate") as gen:
            living_world.true_fortune(char, out.append)
        gen.assert_not_called()
        self.assertIn(out[0], living_world.FORTUNE_FALLBACKS)


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


class GlobalCapChatTests(_AIEnvMixin, EvenniaTest):

    def test_chat_from_many_accounts_hits_global_cap(self):
        os.environ["NPC_LLM_API_KEY"] = _FAKE_ANTHROPIC_KEY
        os.environ["NPC_LLM_GLOBAL_HOURLY_LIMIT"] = "2"
        os.environ["NPC_AI_REQUIRE_VERIFIED"] = "0"
        npc = SimpleNamespace(key="Gerald", id=99,
                              db=SimpleNamespace(body=None, bleed_points=None))
        chars = [SimpleNamespace(key=f"C{i}", id=i, account=acct)
                 for i, acct in enumerate([self.account, self.account2,
                                           self.account, self.account2])]
        replies = []
        with mock.patch.object(ai_npc._EXECUTOR, "submit") as submit:
            for c in chars:
                ai_npc.chat(npc, c, "Evening", replies.append)
        self.assertEqual(submit.call_count, 2)
        self.assertEqual(len(replies), 2)  # the two refused get canned lines


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
