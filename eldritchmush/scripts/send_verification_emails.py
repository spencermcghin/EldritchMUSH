"""One-off: email a verification link to every existing account that has
an email address but hasn't verified it (and has no Google sign-in).

This is a script rather than a Django management command because the
game deliberately registers no local Django app (see the note in
server/conf/settings.py), and management commands need one.

Dry run by default: it lists who would get an email and sends nothing.

Run from eldritchmush/, inside the deployed container (so it uses that
environment's database and RESEND_API_KEY):

    python scripts/send_verification_emails.py            # dry run
    python scripts/send_verification_emails.py --send     # send
    python scripts/send_verification_emails.py --send --limit 50 --delay 1

Each account gets at most one backfill email (re-runs skip it). Resend's
free plan allows 100 emails a day and about 2 a second, so keep --limit
at or under the day's remaining quota and --delay at 1 second or more.
Links point at SITE_BASE_URL (or the environment's default host).
"""
import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--send", action="store_true",
                        help="actually send (default is a dry run)")
    parser.add_argument("--limit", type=int, default=50,
                        help="most emails this run (default 50)")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="seconds between emails (default 1.0)")
    args = parser.parse_args()
    if args.delay < 0.5:
        parser.error("--delay must be at least 0.5 seconds")

    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(here))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.conf.settings")
    import django
    django.setup()

    from world.email_verification import send_bulk
    send_bulk(limit=args.limit, delay=args.delay, send=args.send)


if __name__ == "__main__":
    main()
