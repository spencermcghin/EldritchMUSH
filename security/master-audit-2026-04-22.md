# EldritchMUSH Security Audit — master HEAD

Audit date: 2026-04-22
Branch audited: `security/master-audit` (master HEAD at time of review)
Reviewer: automated static review, read-only

---

## 1. Executive summary

- Production SQLite database (`eldritchmush/server/evennia.db3`) is committed to the public git repo and contains ~80 real account password hashes (PBKDF2-SHA256), emails, and superuser flags for at least four accounts. This is also used as the seed DB on Railway cold deploy.
- A placeholder `SECRET_KEY` is checked into `server/conf/secret_settings.py` and is tracked in git (the file was not kept gitignored). Production deploys are expected to override via `DJANGO_SECRET_KEY` env var, but the committed value will be used on any environment that fails to set it.
- The admin REST API in `web/api_views.py` treats "Builder" as equivalent to "Admin" and lets Builder-level users grant themselves or others the Admin / Developer permission, delete arbitrary characters, and run the legacy-purge nuke. This is a horizontal / vertical privilege escalation chain.
- `CmdCreateNPC` / `CmdNPC` in `commands/npc.py` are attached to `AccountCmdSet` but only use `call:` locks, not `cmd:` locks. Any authenticated player can invoke `createnpc <name>` and spawn ObjectDB rows indefinitely (DoS / DB bloat). `editnpc` and `npc <name> = <cmd>` are gated by an object edit lock that does require `perm(Builders)`, which limits the blast radius, but the create hole is real.
- `start.sh` defaults `ADMIN_PASSWORD` to the hard-coded value `changeme123!` for Account #1 creation when no env var is set, and unconditionally promotes hard-coded usernames (`spencer_admin`, `spencer2`) to superuser / Admin if those rows exist. A clean environment seeded without `ADMIN_PASSWORD` will have a guessable superuser password.

---

## 2. Findings

### Critical

#### C1. Committed production SQLite database with real password hashes and emails
- Files: `.gitignore` (line whitelisting `!eldritchmush/server/evennia.db3`), `eldritchmush/server/evennia.db3` (6.5 MB, tracked).
- Class: credential disclosure / data exposure.
- Evidence: `git ls-files eldritchmush/server/evennia.db3` shows the DB is tracked. Enumerating `accounts_accountdb` from the committed file yields ~80 accounts, 4 with `is_superuser=1` (`eldritchadmin`, `johnadmin`, `jess`, plus default), plus PBKDF2-SHA256 hashes, real email addresses (e.g. `contact@eldritchlarp.com`), and the full game world in `objects_objectdb`.
- Impact: Anyone with repo access (and anyone who ever had it or will have it — the git history is permanent) can offline-crack passwords. Four superuser hashes and ~76 player hashes are exposed. PBKDF2 at 150k iterations is reasonable but not immune to GPU/ASIC attack on weak passwords. Emails are PII. Superuser cracking = full game + server takeover. The file is also copied to the Railway volume on cold deploy (see `start.sh` seed logic), so the public DB IS the production baseline unless `FORCE_DB_SEED=0` with an existing volume.
- Fix: remove the file from git (`git rm --cached eldritchmush/server/evennia.db3`), strip the whitelist exception from `.gitignore`, rotate every superuser password immediately, force-rotate player passwords on next login, and consider the entire repo history compromised. For seeding a new deploy, use migrations + populate scripts instead of a packaged DB.

#### C2. Hard-coded SECRET_KEY committed to git
- File: `eldritchmush/server/conf/secret_settings.py:17`.
- Class: secret disclosure / signed-token forgery.
- Evidence: the file exists in git history (first commit `bcd7a8e6`). Content is `SECRET_KEY = 'G~RcW6"H?pmqB=#9<,_lZ+5Ji%gsAh1LbF8z(!yN'`. `.gitignore` does NOT list `secret_settings.py` — the docstring says it's gitignored "by default" but the project's `.gitignore` never adds it.
- `settings.py:288-290` allows override via `DJANGO_SECRET_KEY` env var, so production on Railway should be using a rotated key — but any environment that does not set that env var (local dev mimicking prod, one-off containers, a forgotten staging box) will fall back to the committed key.
- Impact: Django signs session cookies, CSRF tokens, password-reset tokens, and PasswordResetTokenGenerator values with SECRET_KEY. An attacker knowing the key can forge session cookies, forge password-reset links, and bypass CSRF tokens. Because login is session-cookie-based, a forged session cookie is a full account takeover.
- Fix: add `eldritchmush/server/conf/secret_settings.py` to `.gitignore`, `git rm --cached` the file, rotate the production `DJANGO_SECRET_KEY` in Railway, and on the next deploy invalidate all existing sessions. Consider adding a boot-time assertion that `SECRET_KEY` is not the committed placeholder.

---

### High

#### H1. Admin REST API: Builder can promote to Admin / Developer (privilege escalation)
- File: `eldritchmush/web/api_views.py:191-200` (`_is_admin`), `:610-652` (`admin_set_role`).
- Class: broken access control (BOLA / vertical privilege escalation).
- Evidence:
  - `_is_admin()` returns True for superuser, Admin, OR Builder.
  - `admin_set_role` is gated by `_is_admin(user)`.
  - The endpoint accepts role values `Player | Builder | Admin | Developer` and calls `acct.permissions.add(role)` / `remove(role)` on any target account.
  - No check restricts the role being granted to strict sub-ordinate of the caller. A user holding "Builder" can POST `{"account_id": <self>, "role": "Developer", "action": "add"}` and escalate.
- Impact: Any Builder account, or any user the React admin panel exposes to, can grant themselves Admin or Developer. From Developer, `@py` is available in-game (via the default Evennia perm tiers), which is arbitrary Python execution → full server compromise.
- Fix: tighten `_is_admin` for mutation endpoints to `is_superuser or check_permstring("Admin")`. Restrict `admin_set_role` so only superusers can grant `Admin`/`Developer`, and so the target account cannot be the caller. Add an audit log entry for every role change.

#### H2. Admin REST API: Builder can delete any character, bulk-delete, and run the legacy purge
- File: `eldritchmush/web/api_views.py:_is_admin` + `admin_delete_character` (:294), `admin_bulk_delete_characters` (:362), `admin_purge_legacy` (:418).
- Class: broken access control / destructive action gating.
- Evidence: all three endpoints use `_is_admin`, which accepts Builder. `admin_purge_legacy` in `execute` mode iterates every non-Admin/Builder/Developer/superuser account and deletes it, plus their characters and orphan NPCs. A Builder can erase the playerbase.
- Impact: data loss, griefing, potential ransom scenarios. `admin_bulk_delete_characters` accepts an unbounded `character_ids` list and calls `char.delete()` in a loop.
- Fix: raise the permission bar for destructive endpoints to superuser or Admin only. Rate-limit. Add CSRF-verified confirmation step and an admin audit log.

#### H3. `CmdCreateNPC` is reachable by all authenticated accounts
- File: `eldritchmush/commands/npc.py:13-40`; registered in `commands/default_cmdsets.py:245` on `AccountCmdSet`.
- Class: broken access control / DoS.
- Evidence: `CmdCreateNPC.locks = "call:not perm(nonpcs)"`. The `call:` lock gates whether *another object* can call this command — it does not gate which player can run it. The missing `cmd:` lock falls through to Evennia's default `cmd:all()`, meaning any logged-in account can invoke `createnpc <name>`. Each call spawns an ObjectDB row via `create_object("characters.Character", ...)`.
- Impact: any player can spam-create Character rows (no rate-limit, no quota, no body/location guard beyond "must have a location"). This bloats the DB, pollutes room contents, and makes `ObjectDB.objects.filter(db_typeclass_path="typeclasses.characters.Character")` queries (used in the admin views) slow.
- Mitigation present: `CmdEditNPC` (`editnpc`) IS gated through `npc.access(caller, "edit")` against `"edit:id(<creator>) and perm(Builders);call:false()"`. The `and perm(Builders)` clause means a non-Builder creator cannot edit even their own NPC. Same for `CmdNPC` (`npc <name> = <cmd>`). So the create hole does not directly give arbitrary command execution as an NPC — but it still allows unbounded creation.
- Fix: change `CmdCreateNPC.locks` to `"cmd:perm(Builder)"`. Do the same for `CmdEditNPC` and `CmdNPC` for defense-in-depth.

#### H4. Default superuser password `changeme123!` in start.sh
- File: `eldritchmush/start.sh:134-144`.
- Class: weak credential / deployment hygiene.
- Evidence: `password = os.environ.get('ADMIN_PASSWORD', 'changeme123!')`. If `ADMIN_PASSWORD` is not set at deploy time, Account #1 is created as a superuser with this guessable password. No boot-time assertion enforces the env var.
- Impact: fresh deploys with missing config leave a superuser with a trivial password.
- Fix: refuse to boot (or skip the pre-create step) if `ADMIN_PASSWORD` is unset. Generate a random default and log it once, or require an explicit env var.

---

### Medium

#### M1. HTML injection in outgoing transactional emails (character name + reason)
- File: `eldritchmush/world/email.py:73-121`, used from `server/conf/inputfuncs.py:__finish_chargen__` and `web/api_views.py:admin_approve_character`.
- Class: stored / reflected HTML injection → phishing via email.
- Evidence: `send_approval_request` interpolates `character_name` and `account_name` directly into a raw HTML string (no escape). `send_approval_notification` interpolates `character_name` and `reason`. A player choosing a character name like `Aragorn <a href="https://evil">Click to verify</a>` will cause the admin's Gmail/Outlook to render that link in the HTML email — a phishing amplifier because the email is sent from `noreply@eldritchmush.com` and is inherently trusted.
- Impact: admin-targeted phishing. `reason` is admin-controlled so that end is safer, but character_name is player-chosen.
- Fix: `html.escape()` every interpolated field before rendering, or use a proper template engine (Django templates with autoescape, or `MIMEText(..., "html")` with Jinja autoescape).

#### M2. Session nonce written on GET request (weak CSRF posture)
- File: `eldritchmush/web/api_views.py:9-74` (`webclient_session`).
- Class: unsafe HTTP method / CSRF.
- Evidence: the view is registered as a plain GET, has no CSRF decorator, and mutates Django session state (`request.session["webclient_authenticated_uid"] = ...; request.session["webclient_authenticated_nonce"] = ...`).
- Impact: low practical — the mutation only mirrors the already-authenticated user's id, and SameSite=Lax session cookies block cross-site GETs from triggering credentialed calls. But it violates the "GETs are idempotent" rule and makes audit reasoning harder. An attacker who can force the victim's browser to issue same-origin GETs (e.g. XSS, subdomain takeover) could rotate the ws-nonce and potentially disrupt the victim's WS session.
- Fix: change the method to POST, require CSRF token, and only perform the writes if the nonce is absent/stale.

#### M3. Diag log path / file-based log readable via HTTP
- File: `eldritchmush/web/diag.py:91-128` (`diag_view`).
- Class: information disclosure (privileged-user only, but unrestricted content).
- Evidence: `/api/diag/` is gated behind `is_superuser or perm(Admin|Builder)`, and returns up to 2000 lines of `/data/diag.log`. The log is written via `diag_write` all over the codebase and includes every text frame every session sends (line 91-99), including raw player commands, character names, and stack traces. Builder accounts can read every player's chat / ask / whisper content.
- Impact: Builder-level staff can siphon PII and gameplay secrets from the audit stream. Combined with H1 (Builder-can-promote), it's trivial for any Builder to read player conversations.
- Fix: restrict `/api/diag/` to superuser-only. Stop logging full `text=<frame>` by default (or redact). Add per-session redaction rules so `ask` / `whisper` content is not captured.

#### M4. `npc_audit_log` endpoint readable by Builders
- File: `eldritchmush/web/api_views.py:203-224`.
- Class: information disclosure.
- Evidence: `npc_audit_log` is gated by `_is_admin` (accepts Builders) and returns up to 1000 records of the NPC conversation audit log, including player message text (truncated to 500 chars), character key, account username.
- Impact: Builder can read private player-NPC conversations. Not catastrophic but unexpected.
- Fix: reduce access to superuser+Admin, or scrub `msg`/`reply` fields before returning.

#### M5. Broad API error exposure
- File: `eldritchmush/web/api_views.py:221-223` (`npc_audit_log` returns `f"log_read_failed: {exc}"`), similar patterns in other endpoints.
- Class: information leakage.
- Evidence: several error branches echo the raw exception message or stack path into the JSON response. On a file-not-found this leaks absolute filesystem paths; on DB errors it may leak schema details.
- Fix: log verbosely server-side, return a generic error code to the client.

#### M6. `admin_purge_legacy` can be triggered with `mode="execute"` but caller self-preservation is via `acct.id == user.id` — incorrect when `user` is a Django AccountDB where `.id` might not match expectations
- File: `eldritchmush/web/api_views.py:463-464`.
- Class: logic bug with potential self-destruction of admin.
- Evidence: `if acct.id == getattr(user, "id", None): continue`. `user` IS the account, so `.id` lines up in the usual path. But if a future change swaps the `request.user` source (e.g. allauth social adapter), the id match may silently fail and the caller could delete themselves. No double-check like "caller is also not in admin_playable_pks" exists.
- Fix: add a defense-in-depth check: refuse execute mode for any doomed_account that holds Admin/Developer perms, and require an explicit `confirm_token` round-trip that the caller echoes back.

#### M7. Deprecated `eval()` in `CmdDice` (defense-in-depth)
- File: `eldritchmush/commands/dice.py:84,92`.
- Class: unsafe-looking API even though currently safe.
- Evidence: `eval("%s %s %s" % (result, mod, modvalue))`. Operands are validated (`mod in ("+","-","*","/")`, `modvalue = int(modvalue)`, `result` is `int` from `sum(rolls)`). No injection today.
- Impact: none currently; but future maintainers could relax the whitelist and introduce RCE.
- Fix: replace with `operator.add/sub/mul/floordiv` dispatch — idiomatic and eliminates the eval footgun.

---

### Low

#### L1. Hard-coded account promotion in start.sh
- File: `eldritchmush/start.sh:165-194`.
- Evidence: two usernames (`spencer_admin`, `spencer2`) are unconditionally promoted to superuser / Admin on every boot. Anyone who registers those usernames before the legit admin does takes over the role.
- Fix: move to config-driven `ADMIN_USERNAMES` env var; validate ownership via email or OAuth claim.

#### L2. `setalchemist` accepts 0–5 while docstring says 0–3
- File: `eldritchmush/commands/command.py:943-955`.
- Evidence: bounds check `0 <= alchemist <= 5` contradicts the documented range. Other Set* commands correctly use 0–3.
- Fix: align bounds to the documented range.

#### L3. Merchant / buy OOB handler in inputfuncs has redundant codepath duplication
- File: `eldritchmush/server/conf/inputfuncs.py:818-910`.
- Evidence: `__buy__` OOB bypasses the `CmdBuy` text flow and reimplements the purchase without any shared helper. Any future security fix to `CmdBuy` (e.g. anti-duplication lock, rate limit) must be duplicated in both places or attackers can bypass by using the OOB path.
- Fix: both paths should call a shared `purchase(puppet, item, merchant)` function that owns the atomic transaction.

#### L4. `setSilver` / purse mutations are not atomic
- Files: `commands/shop.py:218` (`caller.db.silver -= price`), `server/conf/inputfuncs.py:868`, `commands/duel.py` payouts.
- Evidence: all purse mutations are read-modify-write on `char.db.silver` without a lock. Two concurrent commands issued in parallel (e.g. `buy` from two clients) could double-spend.
- Impact: low — MUSH players rarely maintain two sessions, SQLite serializes writes at the file level. But the anti-pattern is present.
- Fix: wrap purse changes in a single DB transaction + row-level update, or use a lock object.

#### L5. `process_gift_markers` accepts wide alphanum + spaces — LLM can only ever gift allow-listed items, but marker leakage is possible
- File: `eldritchmush/world/npc_gifts.py:29` (`_GIFT_RE`).
- Evidence: the regex allows a marker like `[GIVE: FOO BAR]`. Claims are uppercased and matched against an NPC-specific allow-list, so spawning is safe. But if the LLM produces a benign-looking `[GIVE: WRITS_OF_PASSAGE]` inside a story quote, the marker is stripped AND the item is spawned even though the NPC was "only describing" the action. That's design intent per the docstring, so not a bug — noted for awareness.
- Fix: none required; monitor via audit log.

#### L6. Frontend reads CSRF token from cookie and sends via `X-CSRFToken`
- File: `frontend/src/components/AdminPanel.jsx:4-6`.
- Evidence: fine pattern, but the cookie is `SameSite=Lax` by Django default. If any admin endpoint is triggerable via GET or via simple-content-type POST, an attacker site could still do it. All admin mutation endpoints use POST with `application/json`, which forces preflight → safe in practice. Noting to confirm that no additional non-preflighted mutation routes are ever added.
- Fix: none required currently; add automated test asserting every `admin_*` endpoint is POST-only.

---

### Informational

- **OAuth signal handler (`web/oauth_signals.py`)** grants `PERMISSION_ACCOUNT_DEFAULT` (Player) to every new OAuth signup, then calls `set_class_from_typeclass` and sets `_playable_characters = []`. Looked correct. No signal-handler-based privilege assignment beyond Player.
- **LLM prompt-injection defenses (`world/ai_safety.py`)** are solid: banned-phrase filter, per-account rate limit, optional Llama-Guard moderation, audit log. The message is clipped to 600 chars before being forwarded. `process_gift_markers` uses a strict allow-list.
- **SSRF risk in LLM calls**: `NPC_LLM_BASE_URL` is env-controlled only (no player / request path touches it), so there's no SSRF vector from player input.
- **`rename_tavern.py` / `populate*.py`** use `exec(open(...))` but these are one-off admin scripts invoked manually via the Django shell — not reachable from the network. No vuln.
- **Upstream deps**: production `pip install evennia "django-allauth[socialaccount]>=0.58"` — Dockerfile pulls the current Evennia (not the vendored 0.9.0 in `./evennia/`). Frontend uses React 18.3, Vite 5.4, DOMPurify 3.3.3 — no obvious CVE hotspots but recommend running `pip list --outdated` and `npm audit` quarterly.
- **CSRF middleware** is confirmed active via Evennia's default `MIDDLEWARE`. `CSRF_TRUSTED_ORIGINS` is correctly set per environment.
- **ALLOWED_HOSTS** is explicitly set, not `"*"`.
- **`SECURE_PROXY_SSL_HEADER`** is set because the app is behind nginx + Railway edge.
- **DEBUG**: inherits `False` from `evennia.settings_default`. Good.

---

## 3. What looks OK (defensive practices observed)

- Django CSRF middleware is active, `CSRF_TRUSTED_ORIGINS` is explicit per environment, admin frontend sends `X-CSRFToken` on mutation POSTs.
- Player-facing text flowing to the React UI is rendered via `dangerouslySetInnerHTML` but only after `DOMPurify.sanitize(...)` — XSS via game text is blocked.
- LLM integration has layered defenses: prompt-injection regex filter, Llama-Guard moderation, per-account + per-char-per-NPC rate limits, audit log. `process_gift_markers` uses a strict per-NPC allow-list for item spawns.
- `CmdEditNPC` and `CmdNPC` use `npc.access(caller, "edit")` against an object lock that requires `perm(Builders)` — prevents the `createnpc` hole from escalating to arbitrary edit / command execution.
- Admin mutation endpoints are all POST-only with `@require_http_methods(["POST"])` and rely on Django session + CSRF.
- Shop / alchemy / crafting flows validate skill level, station presence, kit uses, material availability before state mutation, and use prototype allow-lists (no arbitrary `@spawn` from player input).
- Password hashes use PBKDF2-SHA256 at 150k iterations (Django default) — strong per-password, but see C1 for the disclosure issue.
- OAuth callback builds are forced to HTTPS via `ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"` — mitigates redirect_uri_mismatch attacks.

---

## 4. Out of scope / follow-ups

- Dependency CVE cross-reference: the task notes 18 dependabot alerts. I did not open the alerts; recommend mapping each to whether it touches prod code paths (`evennia`, `django`, `django-allauth`, `react-dom`, `vite`). The upstream `evennia` pin is unbounded in `eldritchmush/requirements.txt` — reproducibility concern, not a vuln per se.
- Did not deeply read all ~2960 lines of `commands/command.py`; I spot-checked command classes and locks but there may be additional `call:`-only lock misuses similar to H3.
- Did not audit `typeclasses/npc.py` (~1085 lines) for AI-hook abuses beyond `process_gift_markers`.
- Did not review the Playwright harness under `.claude/skills/playtest/` — assumed out of scope per the brief ("frontend/React is lower priority").
- Did not run `bandit` / `semgrep` — a targeted semgrep run (especially for Python `eval`, `pickle`, SSRF patterns, SQL concat) would likely surface additional low-severity hits.
- Did not validate every Django model `raw()` / `extra()` query — grep did not surface any, but the Evennia upstream may have some.
- Did not audit the `@py` / `@spawn` / `@typeclass` / `@tel` locks — these come from upstream Evennia and are assumed gated behind Developer perm. If H1 is fixed, `@py` remains a concern only for real Developers.
- Session fixation / logout flow: not audited. Suggest verifying that `/accounts/logout/` invalidates both the Django session AND any lingering Evennia WS session nonce.
