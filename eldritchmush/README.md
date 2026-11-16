# Welcome to Evennia!

This is your game directory, set up to let you start with
your new game right away. An overview of this directory is found here:
https://github.com/evennia/evennia/wiki/Directory-Overview#the-game-directory

You can delete this readme file when you've read it and you can
re-arrange things in this game-directory to suit your own sense of
organisation (the only exception is the directory structure of the
`server/` directory, which Evennia expects). If you change the structure
you must however also edit/add to your settings file to tell Evennia
where to look for things.

Your game's main configuration file is found in
`server/conf/settings.py` (but you don't need to change it to get
started). If you just created this directory (which means you'll already
have a `virtualenv` running if you followed the default instructions),
`cd` to this directory then initialize a new database using

    evennia migrate

To start the server, stand in this directory and run

    evennia start

This will start the server, logging output to the console. Make
sure to create a superuser when asked. By default you can now connect
to your new game using a MUD client on `localhost`, port `4000`.  You can
also log into the web client by pointing a browser to
`http://localhost:4001`.

# Getting started

From here on you might want to look at one of the beginner tutorials:
http://github.com/evennia/evennia/wiki/Tutorials.

Evennia's documentation is here:
https://github.com/evennia/evennia/wiki.

Enjoy!

# AI NPC spend safety

NPC chat (`say`, `ask`, `whisper`, giving an item to an NPC, the React
dialogue panel), Artessa's fortune cabinet (`pull crank`), and the
scheduled world systems (gossip, dreams, chronicle, Adjudicator letters)
call a paid LLM: Anthropic Claude or Groq. The code lives in
`world/ai_npc.py`, `world/ai_safety.py` and `world/ai_pricing.py`.

## Limits, in the order they apply

1. **Verified accounts only.** An account needs a verified email address
   or a Google sign-in (or superuser status) before chat or the fortune
   cabinet reach the model. Every other account gets canned NPC lines and
   canned fortunes. Email/password sign-ups have no verification email
   today, so in practice that means Google. An admin can mark an address
   verified in Django admin (Accounts → Email addresses), and a player can
   sign in with Google using the same email address to link it.
2. **Per account:** 100 AI calls an hour across all of the account's
   characters, chat and fortune pulls together.
3. **Per character per NPC:** 30 messages an hour; fortune pulls have a
   120-second cooldown per character.
4. **Global:** 300 AI calls an hour across every account and the
   scheduled jobs.
5. **Daily budget:** $5.00 a day (UTC). Each call is priced at the rates
   of the model that actually ran (input, output, cache write and cache
   read tokens), from the table in `world/ai_pricing.py`. Moderation calls
   count too. When the budget is used up, NPCs give canned lines until
   UTC midnight and the admin gets one email.

The daily total is saved after every call to `llm_spend.json` on the
Railway volume (`$RAILWAY_VOLUME_MOUNT_PATH`), so reloads, restarts and
redeploys keep it. `start.sh` will not boot a deployed environment
without the volume. If the file can't be read or written, the budget
counts as used up (canned lines, admin email) until it works again.

## Environment variables

| Variable | Default | What it does |
|---|---|---|
| `NPC_LLM_ENABLED` | `1` | `0` turns every AI call off. |
| `NPC_LLM_API_KEY` | none | Provider key. No key means canned lines only. A key starting `sk-ant-` selects Anthropic. |
| `NPC_LLM_PROVIDER` | detected | `anthropic` or `openai` (any OpenAI-compatible API; Groq by default). |
| `NPC_LLM_MODEL` | `claude-haiku-4-5` (Anthropic) or `openai/gpt-oss-120b` (Groq) | Must have a row in `world/ai_pricing.py`. If it doesn't, the AI layer refuses to start: canned lines, a loud log line and an admin email. |
| `NPC_LLM_FALLBACK_MODELS` | `openai/gpt-oss-120b,openai/gpt-oss-20b` | Groq path only. Models without a price row are skipped. |
| `NPC_LLM_BASE_URL` | `https://api.groq.com/openai/v1` | OpenAI-compatible path only. |
| `NPC_LLM_MAX_TOKENS` | `600` | Longest NPC reply. |
| `NPC_LLM_WORKERS` | `4` | Calls that can run at once. |
| `NPC_LLM_DAILY_BUDGET_USD` | `5.0` | Daily spend cap, UTC. |
| `NPC_LLM_GLOBAL_HOURLY_LIMIT` | `300` | AI calls per rolling hour, all accounts and jobs together. |
| `NPC_ACCT_RATE_LIMIT` | `100` | AI calls per hour per account (chat and fortunes). |
| `NPC_AI_REQUIRE_VERIFIED` | `1` | `0` lets unverified accounts use AI. For local development only. |
| `NPC_LLM_MODERATE` | `0` | `1` turns on Llama Guard moderation of player messages. |
| `NPC_MODERATE_API_KEY` | none | Groq key for moderation. Required: the main `NPC_LLM_API_KEY` is never sent to the moderation provider. With moderation on and no key, moderation stays off and a warning is logged. |
| `NPC_MODERATE_BASE_URL` | `https://api.groq.com/openai/v1` | Moderation endpoint. |
| `NPC_LLM_MODERATE_MODEL` | `llama-guard-4-12b` | Must have a price row, or moderation stays off. |

To use a model that isn't in `world/ai_pricing.py`, add its row first,
with the provider's current published price.

## Owner steps (outside the code)

These are the hard ceiling. The limits above protect the budget; only
the provider can stop a bill outright.

- **Set a monthly spend limit at the provider.**
  - Anthropic: console.anthropic.com → **Settings → Limits** → set a
    monthly spend limit and email alerts. In **Settings → Billing**, turn
    **auto-reload off**, so the prepaid balance is a hard stop.
  - Groq: console.groq.com → **Settings → Billing → Limits** → set a
    monthly spend limit and alert thresholds.
- **Use separate keys for production and uat.** Create one key per
  environment (on Anthropic, ideally one workspace per environment, each
  with its own limit) and set each in that Railway environment's
  variables. A leaked or runaway uat key then can't spend production's
  budget, and you can revoke one without taking down the other.
- Keep `NPC_LLM_DAILY_BUDGET_USD` low and check the admin metrics page
  (`/api/admin/metrics/`) for real daily spend.
