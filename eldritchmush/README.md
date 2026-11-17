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
   or a Google sign-in (or superuser status) before chat, the fortune
   cabinet or the Adjudicator's letters reach the model. Every other
   account gets canned NPC lines, canned fortunes and canned letters,
   plus the hint "Verify your email to talk with NPCs. Check your inbox or
   type `verify`." See "Email verification" below.
2. **Per account:** 100 AI calls an hour across all of the account's
   characters, chat and fortune pulls together.
3. **Per character per NPC:** 30 messages an hour; fortune pulls have a
   120-second cooldown per character.
4. **Global:** 300 provider calls an hour across every account and the
   scheduled jobs. Each request counts, including moderation and each
   fallback-model attempt, and the slot is taken just before the request
   goes out.
5. **Daily budget:** $5.00 a day (UTC). Each call is priced at the rates
   of the model that actually ran (input, output, cache write and cache
   read tokens), from the table in `world/ai_pricing.py`. Moderation calls
   count too. A request that times out or fails after it was sent is
   charged as a large prompt plus a full-length reply, since the provider
   may have billed it; a plain rejection (400, 401, 403, 404, 429) is not
   charged. The budget is checked again just before every request
   (including between fallback attempts), and the Anthropic client makes
   no automatic retries, so nothing slips past it. When the budget is
   used up, NPCs give canned lines until UTC midnight and the admin gets
   one email.

The daily total is saved after every call to `llm_spend.json` on the
Railway volume (`$RAILWAY_VOLUME_MOUNT_PATH`), so reloads, restarts and
redeploys keep it. `start.sh` will not boot a deployed environment
without the volume. If the file can't be read or written, the budget
counts as used up (canned lines, admin email) until it works again.
The counter assumes a single game process writes it (Evennia's Server
process). Don't run two game servers against the same volume: each
would keep its own total and overwrite the other's file.

Admin alert emails go out on a background thread and at most once per
6 hours per kind; the `ALERT` log line is printed only when an email is
actually sent.

## Email verification

- New sign-ups through the web form get a verification email
  (`ACCOUNT_EMAIL_VERIFICATION = "optional"`: nobody is locked out while
  unverified). Google sign-ins count as verified.
- In the game, `verify` sends a link to the address on the account, and
  `verify you@example.com` switches the account to a new address (its
  other unverified addresses are dropped) and sends a link to it.
  Unverified players see a note at login and, in the web client, a
  "Send me a verification link" box. Limits: the account must be 10
  minutes old or have a character; one email per account every 10
  minutes and 5 a day; and the shared mail caps below. A send that fails
  doesn't use up the player's slot, and the player is told the result.
- An address counts as taken only when another account has it verified
  or signs in with Google using it. Typing someone else's address does
  not block them: whoever verifies first owns it, and verifying removes
  the address from every other account's unverified entries.
- **Shared mail caps.** All game mail (verification links, allauth web
  mail such as password resets, character approvals, admin alerts)
  counts against one daily cap, `EMAIL_DAILY_LIMIT` (default 60, below
  Resend's free 100 a day), and one hourly cap, `EMAIL_HOURLY_LIMIT`
  (default 20). Mail to `ADMIN_EMAIL` can use the last 5 daily slots and
  skips the hourly cap, so alerts still get out. Hitting either cap
  emails the admin. The count is saved in `mail_quota.json` on the
  volume, guarded by a lock file (`mail_quota.lock`); if it can't be read
  or written, no mail is sent. A corrupt file is rewritten as "today is
  full", so mail resumes the next UTC day.
- allauth only mails addresses that belong to an account
  (`ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = False`). Password resets are limited
  to 10 an hour per IP and 3 an hour per address, sign-ups to 5 an hour
  per IP, and changes on the account email page to 3 an hour and 6 a day
  per account. An account can hold at most 2 addresses. If an email
  can't be sent, allauth's pages carry on (a sign-up still completes)
  and show "We couldn't send the email right now. Please try again
  later."
- Client IPs for those limits come from the `X-Real-IP` header on
  Railway: Railway's edge sets it, and the container's nginx passes it
  through unchanged (`start.sh`). Locally, and if the header is ever
  missing, the connection address is used. Override with
  `ALLAUTH_TRUSTED_CLIENT_IP_HEADER` (empty for none). To check the
  proxy setup on uat, set `LOG_CLIENT_IP_HEADERS=1`: the next allauth
  request logs `X-Real-IP` and `X-Forwarded-For` once (look for
  `[client_ip]` in the logs), then remove the variable.
- **One account per verified address.** An address can be verified on
  only one account, so alt accounts that share an email address can
  verify it on only one of them; the others need their own address (or
  Google sign-in).
- Emails go through Resend (`RESEND_API_KEY`), from
  `noreply@eldritchmush.com`. Links point at `SITE_BASE_URL`, which
  defaults to `https://eldritchmush.com` on production,
  `https://uat.eldritchmush.com` on uat and `http://localhost:4001`
  locally. Any other Railway environment must set `SITE_BASE_URL`, or
  the game logs an error and sends no links. At startup the Django Site
  is renamed "Eldritch MUSH" with this domain, so allauth's emails and
  pages don't say "example.com".
- An admin can also mark an address verified in Django admin (Accounts →
  Email addresses).
- One-off backfill for existing accounts (not run automatically): from
  `eldritchmush/` inside the deployed container,
  `python scripts/send_verification_emails.py` lists who would get an
  email; add `--send` to send (default at most 50 per run, 1 second
  apart; each account gets one backfill email at most). Resend's free
  plan allows 100 emails a day.
- Google sign-in only logs into, or links to, an existing password
  account with the same email when that account's address is verified.
  An unverified password account can't capture someone's Google login.

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
| `SITE_BASE_URL` | per environment (see "Email verification") | Host used in verification links. |
| `RESEND_API_KEY` | none | Sends verification and alert emails. Without it, emails are logged and skipped. |
| `EMAIL_DAILY_LIMIT` | `60` | Emails per UTC day for the whole game (all kinds); the last 5 are kept for the admin. |
| `EMAIL_HOURLY_LIMIT` | `20` | Emails per rolling hour for the whole game. |
| `ALLAUTH_TRUSTED_CLIENT_IP_HEADER` | `X-Real-IP` on Railway, none locally | Header allauth reads the client IP from, for its per-IP limits. |
| `LOG_CLIENT_IP_HEADERS` | `0` | `1` logs the client-IP headers once, to check the proxy setup. |

To use a model that isn't in `world/ai_pricing.py`, add its row first,
with the provider's current published price.

**Temperature.** The NPC code sends `temperature` (0.85 to 1.0) with
every call. These listed models reject a non-default temperature with
HTTP 400, so NPCs would only give canned lines on them:
`claude-haiku-5-5`, `claude-sonnet-5`, `claude-sonnet-5-5`,
`claude-opus-4-7`, `claude-opus-4-8`, `claude-opus-5`, `claude-opus-5-5`.
Remove `temperature` from the calls in `world/ai_npc.py` before
switching to one of them. `requirements.txt` pins `anthropic<1`: from
1.0 the Python SDK no longer accepts `temperature`, and 2.0 moves to API
version 2026-10-21, which rejects it on every model.

**The Docker image ignores `requirements.txt`.** The `Dockerfile`
installs its own pinned list (Evennia, django-allauth 65.18.0, psycopg2,
dj-database-url), and it doesn't include `anthropic`. Production and uat
run NPCs on Groq (`NPC_LLM_MODEL=openai/gpt-oss-120b`), which uses plain
HTTP and needs no SDK. Before switching an environment to Anthropic, add
`"anthropic>=0.69,<1"` to the Dockerfile's `pip install` line; until
then, Anthropic calls fail at import and NPCs give canned lines (nothing
is charged).

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
