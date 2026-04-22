# Security audit — post-merge followup

This branch (`security/fixes-2026-04-22`) fixes every Critical/High/Medium finding from `security/master-audit-2026-04-22.md` that can be resolved in code. A few items require operator action on deployed environments — those are listed here.

Order roughly from most urgent to least.

## 1. Rotate the Django SECRET_KEY (C2)

The value committed in `secret_settings.py` before this branch is in public git history and must be treated as compromised.

1. Generate a fresh key:
   ```
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
2. Set it on Railway (UAT + prod) as `DJANGO_SECRET_KEY`.
3. Redeploy. All existing Django sessions, CSRF tokens, and password-reset links issued before the redeploy become invalid — users will be logged out and need to sign in again.
4. Boot-time assertion in `settings.py` will now refuse to start if the committed placeholder is ever reused, so there's no silent regression risk.

## 2. Rotate superuser passwords (C1)

The DB that was committed to git contains the password hashes of every account that existed at the time of the commit. PBKDF2-SHA256 at 150k iterations is strong, but treat every hash as known to attackers.

1. Identify superusers:
   ```
   evennia shell -c "from evennia.accounts.models import AccountDB; print([(a.id, a.username, a.email) for a in AccountDB.objects.filter(is_superuser=True)])"
   ```
2. For each one: log in, change the password to something new and strong, and confirm old sessions are gone.
3. If a superuser no longer exists / is unreachable, demote them with `@perm/del <user> = superuser` from another superuser account.

## 3. Force-reset all player passwords (C1)

Options, ordered by friction:

- **Soft**: email every account with a "we had a security incident, please change your password" notice, then monitor the failed-login log for abuse.
- **Medium**: flag all accounts as `password_reset_required` and add a middleware that forces the flow on next login. (Not implemented in this branch — would need a new `forced_password_reset_required` attribute plus a signal handler.)
- **Hard**: mass-invalidate passwords by writing `set_password(get_random_string())` to every non-admin account. Users must then run the forgot-password flow to regain access. Effective, but cuts everyone off until they click through — time the comms carefully.

Pick based on your trust in the exposed hashes vs. the churn you're willing to take.

## 4. Purge the committed DB and SECRET_KEY from git history (optional but strongly recommended)

`git rm --cached` removes the files from the current tree but the old copies still live in every commit prior to this branch. Anyone with repo access can `git log -p` them out.

Plan:

1. Make a backup of the repo (`.git` included) before running history rewrite — this is destructive.
2. Use [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) (faster than `git filter-branch`):
   ```
   bfg --delete-files evennia.db3
   bfg --delete-files secret_settings.py --no-blob-protection
   git reflog expire --expire=now --all && git gc --prune=now --aggressive
   ```
   (The `--no-blob-protection` flag is needed because `secret_settings.py` is still the current HEAD copy of that filename — it's just gitignored now.)
3. `git push --force` every branch.
4. Ask every collaborator to delete their local clones and re-clone. Rebases will explode otherwise.
5. On GitHub: the rewritten history lives in git, but old blobs remain accessible via the REST API (`/repos/:owner/:repo/git/blobs/:sha`) for a while. Contact GitHub Support to request a garbage-collection run if you need the old blobs gone immediately; otherwise they'll age out.

If you skip this step, the old secrets are still reachable via history — the in-code rotations above are required regardless.

## 5. Rotate any other env-held secrets on Railway

While you're in the environment settings, also refresh anything that might have been logged or exposed adjacent to the leaked DB / SECRET_KEY:

- `RESEND_API_KEY` (email)
- `NPC_LLM_API_KEY` (LLM provider)
- OAuth client secret (Google Cloud Console → OAuth credentials)
- `ADMIN_PASSWORD` if it was ever used via the start.sh default path (it's now required explicitly, but a guessable value may already have been set on existing deploys).

## 6. Configure the new admin-promotion env vars (L1)

The hard-coded `spencer_admin`/`spencer2` promotions in `start.sh` are now env-driven:

- `SUPERUSER_USERNAMES=spencer_admin` (comma-separated list, promoted to is_superuser)
- `ADMIN_USERNAMES=spencer2` (comma-separated list, granted Admin permstring)

Set those on Railway for both UAT and prod so the same behaviour continues. Leaving them unset is now a no-op.

## 7. Deferred followups (tracked, not in this PR)

- **M2**: `webclient_session` converted to `@require_http_methods(["GET"])` for defense-in-depth; full POST + CSRF conversion still deserves a follow-up that also updates the frontend calls.
- **L3**: `__buy__` OOB handler and `CmdBuy` still duplicate purchase logic. Worth factoring into a shared helper next time shop code is touched.
- **L4**: Purse mutations remain read-modify-write. Low-impact under SQLite, but consider wrapping buy/sell/duel-payout in a `transaction.atomic()` + `select_for_update` if we move to PostgreSQL.
- **L6**: Add an automated test asserting every `admin_*` endpoint is POST-only.
- **Dependabot alerts**: cross-reference the 18 open alerts and bump any that touch a production code path.
- Session-fixation / logout-flow audit not yet performed.
