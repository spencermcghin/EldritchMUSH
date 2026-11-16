"""
Per-model prices for the AI spend cap.

Every paid AI call (NPC chat, world-system generation, moderation) is
charged against NPC_LLM_DAILY_BUDGET_USD at the rates of the model that
actually ran. A model that is not in this table is never called: the
NPC layer refuses to start (canned lines only) rather than guess a price.

All prices are USD per million tokens:
    (input, output, cache_write_5m, cache_read)

Anthropic first-party rates, from Anthropic's model table (checked
2026-11-16). Cache writes are the 5-minute TTL rate (1.25x input); cache
reads are 0.1x input except where Anthropic prices them lower. Haiku 5.5
is priced at its up-to-100K-token rate; NPC prompts stay far below that.

Groq rates from console.groq.com/docs/models (checked 2026-11-16). Groq
reports cached prompt tokens inside prompt_tokens, so the cap charges
every prompt token at the full input rate (an overestimate, never under).

When you change NPC_LLM_MODEL to a model that is not listed here, add a
row first, with the provider's current published price.
"""
import re


class UnknownModelError(ValueError):
    """Raised when a model has no row in PRICES."""


PRICES = {
    # ── Anthropic ─────────────────────────────────────────────────────
    # Haiku
    "claude-haiku-4-5": (1.00, 5.00, 1.25, 0.10),
    "claude-haiku-5-5": (0.10, 0.50, 0.125, 0.01),
    # Sonnet
    "claude-sonnet-4-5": (3.00, 15.00, 3.75, 0.30),
    "claude-sonnet-4-6": (3.00, 15.00, 3.75, 0.30),
    "claude-sonnet-5": (2.00, 10.00, 2.50, 0.20),
    "claude-sonnet-5-5": (2.00, 10.00, 2.50, 0.20),
    # Opus
    "claude-opus-4-5": (5.00, 25.00, 6.25, 0.50),
    "claude-opus-4-6": (5.00, 25.00, 6.25, 0.50),
    "claude-opus-4-7": (5.00, 25.00, 6.25, 0.50),
    "claude-opus-4-8": (5.00, 25.00, 6.25, 0.50),
    "claude-opus-5": (5.00, 25.00, 6.25, 0.50),
    "claude-opus-5-5": (4.00, 20.00, 5.00, 0.20),

    # ── Groq (OpenAI-compatible path) ─────────────────────────────────
    "openai/gpt-oss-120b": (0.15, 0.60, 0.15, 0.15),
    "openai/gpt-oss-20b": (0.075, 0.30, 0.075, 0.075),
    # Llama Guard moderation (NPC_LLM_MODERATE_MODEL). Groq's last
    # published rate; Groq no longer lists this model on its models
    # page, so check it is still served before turning moderation on.
    "llama-guard-4-12b": (0.20, 0.20, 0.20, 0.20),
    "meta-llama/llama-guard-4-12b": (0.20, 0.20, 0.20, 0.20),
}

# Anthropic returns dated ids ("claude-haiku-4-5-20251001"); strip the
# date so they match the alias row.
_DATE_SUFFIX = re.compile(r"-\d{8}$")


def price_for(model):
    """Return the (in, out, cache_write, cache_read) row, or None."""
    m = (model or "").strip().lower()
    if not m:
        return None
    if m in PRICES:
        return PRICES[m]
    return PRICES.get(_DATE_SUFFIX.sub("", m))


def is_priced(model):
    return price_for(model) is not None


def cost_usd(model, input_tokens=0, output_tokens=0,
             cache_write_tokens=0, cache_read_tokens=0):
    """Dollar cost of one call. Raises UnknownModelError for an
    unlisted model so a pricing gap can never be silently charged $0."""
    row = price_for(model)
    if row is None:
        raise UnknownModelError(f"no price for model {model!r}")
    p_in, p_out, p_cw, p_cr = row
    return (
        (input_tokens or 0) * p_in
        + (output_tokens or 0) * p_out
        + (cache_write_tokens or 0) * p_cw
        + (cache_read_tokens or 0) * p_cr
    ) / 1_000_000
