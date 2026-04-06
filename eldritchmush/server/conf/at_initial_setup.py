"""
At_initial_setup module — runs exactly once when the server first starts
on a fresh database. Creates the admin account from environment variables
so Railway deployments don't need an interactive TTY.
"""

import os


def at_initial_setup():
    username = os.environ.get("ADMIN_USERNAME")
    password = os.environ.get("ADMIN_PASSWORD")
    email = os.environ.get("ADMIN_EMAIL", "admin@eldritchmush.com")

    if not username or not password:
        return

    try:
        from evennia.accounts.models import AccountDB
        from django.contrib.auth.hashers import make_password

        if not AccountDB.objects.filter(id=1).exists():
            acct = AccountDB(
                id=1,
                username=username,
                email=email,
                is_superuser=True,
                is_staff=True,
            )
            acct.password = make_password(password)
            acct.save()
            print(f"[at_initial_setup] Created admin account: {username}")
        else:
            print("[at_initial_setup] Admin account (id=1) already exists.")
    except Exception as e:
        print(f"[at_initial_setup] Warning: could not create admin account: {e}")
