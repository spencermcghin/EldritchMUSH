# Deployment

EldritchMUSH runs on [Railway](https://railway.app). There are **two
environments** — both in the same Railway project:

| Env | Branch | URL | Purpose |
|-----|--------|-----|---------|
| `production` | `master` | eldritchmush.com | Live game |
| `uat` | `uat` | uat.eldritchmush.com (or `*.up.railway.app` fallback) | QA / pre-prod verification |

Both environments deploy the same `Dockerfile` + `start.sh`. All
per-environment differences live in Railway variables — **never in
code**.

## First-time UAT setup

Only done once per Railway project. If UAT already exists, skip to
"Deploying" below.

1. In the Railway project dashboard: **New → GitHub Repo → select
   EldritchMUSH**. Name the new service `eldritchmush-uat`.
2. **Settings → Environment**. Rename `production` (the one Railway
   auto-creates) to `uat`, OR create a new environment named `uat` and
   delete the auto one.
3. **Settings → Source**. Set `Watch paths` to the whole repo and
   `Branch` to `uat`.
4. **Settings → Volumes**. Add a volume, mount it at `/data`. Separate
   volume per env — UAT and prod must not share state.
5. **Settings → Variables**. Paste the block from `.env.example`, then
   fill in UAT-specific values:

   ```
   DEPLOY_ENV=uat
   SITE_DOMAIN=uat.eldritchmush.com    # or the railway.app URL
   ALLOWED_HOSTS=uat.eldritchmush.com,eldritchmush-uat.up.railway.app
   CSRF_TRUSTED_ORIGINS=https://uat.eldritchmush.com,https://eldritchmush-uat.up.railway.app
   DJANGO_SECRET_KEY=<fresh secret — different from prod>
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=<fresh password>
   GOOGLE_OAUTH_CLIENT_ID=<uat OAuth client>
   GOOGLE_OAUTH_CLIENT_SECRET=<uat OAuth client>
   MISTVALE_BUILD=1      # run world build on boot; set to 0 after verifying
   ```

   **Why separate OAuth creds:** Google OAuth client IDs allow a fixed
   set of redirect URIs. UAT needs its own client entry so
   `https://<uat-domain>/accounts/google/login/callback/` is authorized.

6. **Settings → Networking → Generate Domain** for the initial URL.
   Add a custom domain later if needed.

7. Push the `uat` branch (create it from master if it doesn't exist):

   ```bash
   git checkout -b uat
   git push -u origin uat
   ```

   Railway picks up the push and deploys. First boot runs migrations +
   world seed (because `MISTVALE_BUILD=1`). After the first successful
   deploy, set `MISTVALE_BUILD=0` to speed subsequent boots.

## Deploying

### Normal flow (SDLC)

```
feature-branch  ──PR──▶  uat  ──PR──▶  master
                  │               │
                  CI runs         CI runs
                  deploys UAT     deploys prod
```

1. Work on a `feature/*` branch.
2. Open a PR targeting `uat`. CI runs the Python playtest harness +
   frontend build. Merge once green.
3. Railway auto-deploys the new UAT.
4. QA verifies on UAT.
5. Open a PR from `uat` → `master`. CI runs again. Merge once QA has
   signed off.
6. Railway auto-deploys prod.

**Do not push directly to `master` or `uat`.** Both branches are
deploy targets; direct pushes skip CI and peer review.

### Hotfix

For an urgent prod fix that can't wait for the full cycle:

```
hotfix/*  ──PR──▶  master  (UAT catches up on next regular merge)
```

This is rare. If you do it, also cherry-pick the commit into `uat` so
the branches don't drift.

## Rollback

Railway keeps a deploy history.

1. Dashboard → the failing service → **Deployments** tab.
2. Find the last known good deploy → click **Redeploy**.
3. For a DB rollback: stop the service, `railway volume restore` (or
   manually copy a backup into the volume), restart. Always take a
   snapshot before running destructive migrations:

   ```bash
   railway run --service eldritchmush-prod -- cp /data/evennia.db3 /data/evennia.db3.$(date +%Y%m%d).bak
   ```

## Secrets

| Secret | Rotation | Stored in |
|--------|----------|-----------|
| `DJANGO_SECRET_KEY` | On breach | Railway variables (per env) |
| `GOOGLE_OAUTH_CLIENT_SECRET` | On breach / annual | Railway variables (per env) |
| `ADMIN_PASSWORD` | Quarterly | Railway variables (per env) |

Secrets are **never** committed. `.env.example` documents the var
names only. `secret_settings.py` is gitignored; the local dev copy
contains a throwaway `SECRET_KEY` that must not be used in deployed
environments.

## Runbook: common UAT operations

```bash
# Reset UAT to a clean state (wipe DB, re-seed from baked-in db3,
# re-run populate).
#   Set these in Railway dashboard, then trigger a redeploy:
#     FORCE_DB_SEED=1
#     MISTVALE_BUILD=1
#   Unset both after the boot completes.

# One-off admin shell on UAT
railway shell --service eldritchmush-uat
# then inside: evennia shell

# Stream logs
railway logs --service eldritchmush-uat
```

## Healthchecks

Each service exposes `GET /health` (served by nginx) returning `200
OK`. `railway.json` wires this up as the healthcheck endpoint — an
unhealthy deploy is rolled back automatically.

## Domain mapping (optional)

If you want `uat.eldritchmush.com` as the UAT URL:

1. Railway dashboard → UAT service → **Settings → Networking → Add
   Custom Domain**.
2. Add a `CNAME` record at your DNS provider pointing
   `uat.eldritchmush.com` → `<railway-provided-target>.up.railway.app`.
3. Wait for the domain to turn green in Railway's dashboard
   (certificate provision typically <5 min).
4. Update `SITE_DOMAIN` + `ALLOWED_HOSTS` + `CSRF_TRUSTED_ORIGINS` in
   Railway variables to include the new domain.
5. Redeploy.
