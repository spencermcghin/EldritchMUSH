# Google OAuth Setup

How to enable "Sign in with Google" for EldritchMUSH and what to do
the first time you deploy this change.

## What this does

Players click **Sign in with Google** on the LoginScreen, go through
Google's consent flow, and land directly in-game with their character
auto-puppeted. No `connect username password` typing required.

The username/password login still works as a fallback (toggleable on
the LoginScreen) for the admin account, dev testing, and any legacy
players who created accounts before OAuth.

## Architecture

```
Player ─► LoginScreen "Sign in with Google" button
       ─► /accounts/google/login/  (django-allauth)
       ─► Google OAuth consent
       ─► /accounts/google/login/callback/
       ─► allauth creates an AccountDB row (one-time)
       ─► web.signals provisions an Evennia Character (one-time)
       ─► Redirect to /
       ─► React frontend fetches /api/webclient_session/
       ─► Opens WS with ?<csessid>
       ─► Evennia auto-puppets the character
```

## One-time install

```bash
cd eldritchmush/
pip install "django-allauth[socialaccount]>=0.58"
evennia migrate
```

The migrate creates the allauth tables (`socialaccount_socialaccount`,
`socialaccount_socialapp`, `socialaccount_socialtoken`,
`account_emailaddress`, etc.).

## Credentials

OAuth client ID and secret live in
`eldritchmush/server/conf/oauth_secrets.py` (gitignored). For Railway,
set them as env vars instead — `settings.py` checks `os.environ` first
and falls back to the local file:

- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`

The Google Cloud Console OAuth client must have the following
**Authorized redirect URIs** registered:

- `http://localhost:4001/accounts/google/login/callback/`  (local dev)
- `https://YOUR-RAILWAY-URL/accounts/google/login/callback/`  (prod)

If callbacks fail with "redirect_uri_mismatch", that means the URI on
Google's side doesn't match what Django sends — check the path
includes the trailing slash and the scheme is correct.

## Site object (one extra step on first deploy)

django-allauth uses `django.contrib.sites` to know its own domain.
After `evennia migrate`, log into Django admin and update
`Sites → example.com` to your actual domain (e.g.
`eldritchmush-production.up.railway.app`). Otherwise OAuth callbacks
work but emails / shareable links use "example.com".

```bash
evennia start
# Visit http://localhost:4001/admin/ → Sites → click example.com → set
# Domain Name = "localhost:4001", Display Name = "EldritchMUSH"
```

Repeat for the production site after deploying.

## How new-player onboarding works

`web/signals.py` listens for allauth's `user_signed_up` signal. The
first time someone signs in with Google, the handler:

1. Creates an Evennia Character keyed off their Google username
   (first word, capitalized — e.g. "spencer.mcghin@gmail.com" → "Spencer")
2. Drops the new character into the **ChargenRoom** (looked up by
   typeclass `typeclasses.rooms.ChargenRoom`)
3. Links the character to the AccountDB so `MULTISESSION_MODE=0`
   auto-puppets it on every subsequent login

Because the new character starts in the ChargenRoom, the React
frontend's existing chargen-detection logic in `useEvennia.js` fires
and shows the ChargenWizard automatically — welcome screen first,
then archetype/skill selection, then `done` to exit. After chargen
the player is moved to the regular starting room.

**Returning Google users** (who already have a character) bypass the
signal entirely — allauth fires `user_signed_up` only on the very
first sign-up. They land in whatever room their character was last
in, exactly like a returning username/password player.

If no ChargenRoom exists in the database, the signal falls back to
`settings.START_LOCATION` and skips chargen.

## Local testing

1. Make sure `oauth_secrets.py` exists with valid credentials
2. `cd eldritchmush && evennia migrate && evennia start`
3. `cd frontend && npm run dev` (Vite on :3000)
4. Visit http://localhost:3000
5. Click **Sign in with Google**
6. Consent → land back at the React app, auto-connected

If you see "redirect_uri_mismatch" or "invalid_client", double-check
the credentials and the redirect URI in Google Cloud Console.

## Reverting

To turn OAuth off without ripping it out:
- Comment out the four `allauth.*` entries in `INSTALLED_APPS`
- Comment out the `path("accounts/", ...)` line in `web/urls.py`
- Remove or comment-out the `<button onClick={handleGoogleSignIn}>` in
  `LoginScreen.jsx`

Existing username/password accounts continue to work because the
`ModelBackend` is still in `AUTHENTICATION_BACKENDS`.

## Security note

The OAuth client secret in `oauth_secrets.py` was transmitted through
Claude's chat session during initial setup. It is good hygiene to
rotate it: Google Cloud Console → Credentials → click your OAuth
client → "Reset Secret" → paste the new value into `oauth_secrets.py`
and the Railway env var.
