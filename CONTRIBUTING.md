# Contributing to EldritchMUSH

## Branching model

```
feature/<topic>  ──PR──▶  uat  ──PR──▶  master
                   │                ▲
                   CI + review      QA sign-off
```

- **`master`** — production. Auto-deploys to eldritchmush.com.
- **`uat`** — pre-prod. Auto-deploys to the UAT Railway environment.
- **`feature/*`** — your work-in-progress. Name them something
  descriptive (`feature/alchemy-scroll-rework`, not `feature/x`).

### Workflow

1. `git checkout uat && git pull`
2. `git checkout -b feature/my-change`
3. Do the work, commit, push.
4. Open PR **targeting `uat`**. CI runs automatically; merging requires:
   - ✅ Python playtest harness passes
   - ✅ Frontend builds
   - ✅ At least one reviewer approves
5. After merge, Railway deploys UAT. Verify your change on UAT.
6. Open a PR from `uat` → `master` when ready to ship. QA sign-off
   gates this merge.
7. After merge to `master`, Railway deploys prod.

**Never push directly to `uat` or `master`.** Both are auto-deploy
branches; direct pushes skip review and CI.

### Hotfixes

For a time-critical prod fix:

1. Branch from `master`: `git checkout -b hotfix/<desc> master`
2. PR to `master` directly. Mark clearly as a hotfix.
3. Immediately after merge, cherry-pick onto `uat` so branches don't
   drift: `git checkout uat && git cherry-pick <sha> && git push`.

## Before opening a PR

- Run the Python playtest harness locally: `make playtest`
- If the change touches the UI, run the Playwright harness too:
  `make playtest-ui` (requires the dev server running — see
  `.claude/skills/playtest/SKILL.md`).
- Add or update a scenario in `.claude/skills/playtest/playtest.py` if
  your change introduces a new user-facing path.

## Commit hygiene

- One logical change per commit. A PR can have multiple commits.
- Short, imperative commit messages: `Add <feature>` / `Fix <bug>`, not
  `changes` or `wip`.
- No "co-authored-by" trailers unless there was an actual collaborator.

## What not to commit

- `.venv/`, `node_modules/`, `dist/` — gitignored already.
- `secret_settings.py` with real secrets — gitignored; local copy has
  a throwaway `SECRET_KEY` only.
- `auth-state.json`, `playtest/ui/screenshots/` — gitignored.
- `evennia.db3` — gitignored; prod state belongs in Railway volume, not
  the repo. (The baked-in `/app/server/evennia.db3` in the Docker image
  is a separate seed snapshot — update it deliberately, not as a
  side-effect of local testing.)

## Getting set up

See the top-level README and `make help` for the full local setup
flow. TL;DR:

```bash
make dev          # one-time: venv + deps + migrate
make server       # terminal 1
make frontend     # terminal 2
open http://localhost:3000
```

For testing:

```bash
make playtest           # server-side smoke test
make playtest-ui        # full browser (needs PLAYTEST_USER/PASS)
```
