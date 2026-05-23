"""Create the EldritchMUSH subscription Product + Plan in PayPal.

One-off script — run it locally once, paste the printed Plan ID into
Railway as PAYPAL_PLAN_ID. Idempotent in spirit: re-running creates a
NEW plan (PayPal doesn't dedupe by name), so only run when you mean it.

Prerequisites
-------------
You need:
  - A PayPal Business account (you have this — Eldritch Workshop, L.L.C.)
  - A REST API App in the PayPal Developer Dashboard, which gives you
    a Client ID and Secret (see PAYPAL setup steps in the conversation)

Usage
-----
Sandbox (recommended first):

    PAYPAL_CLIENT_ID=AXXX... \\
    PAYPAL_SECRET=EXXX... \\
    PAYPAL_MODE=sandbox \\
    python3 create_paypal_plan.py

Live (when you've tested sandbox end-to-end):

    PAYPAL_CLIENT_ID=AXXX... \\
    PAYPAL_SECRET=EXXX... \\
    PAYPAL_MODE=live \\
    python3 create_paypal_plan.py

What it does
------------
1. Creates a Product 'EldritchMUSH Subscription' (PayPal requires a
   Product before a Plan).
2. Creates a Plan: $5.00 USD per month, indefinite billing cycles,
   auto-renew until cancelled. NO built-in trial — the 30-day trial
   is handled server-side in the EldritchMUSH Account typeclass, so
   players don't need to put in a payment method during trial.
3. Prints the Plan ID. Paste this into Railway as PAYPAL_PLAN_ID.

If you want to change the price/cycle later, you have to create a new
plan (PayPal plans are immutable for pricing). Just re-run the script
with the new constants below.
"""

import base64
import os
import sys

import requests


# ── Plan configuration ──────────────────────────────────────────────
PRODUCT_NAME = "EldritchMUSH Subscription"
PRODUCT_DESC = "Monthly access to EldritchMUSH, the dark-fantasy MUSH."
PLAN_NAME = "Monthly — $5/mo"
PLAN_DESC = "$5/month subscription to EldritchMUSH. Cancel anytime."
PRICE_USD = "5.00"
CURRENCY = "USD"


def _base_url(mode):
    if mode == "live":
        return "https://api-m.paypal.com"
    return "https://api-m.sandbox.paypal.com"


def _get_access_token(client_id, secret, base):
    basic = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    resp = requests.post(
        f"{base}/v1/oauth2/token",
        headers={
            "Authorization": f"Basic {basic}",
            "Accept": "application/json",
            "Accept-Language": "en_US",
        },
        data={"grant_type": "client_credentials"},
        timeout=15,
    )
    if resp.status_code != 200:
        sys.stderr.write(
            f"\nERROR: failed to authenticate with PayPal "
            f"(HTTP {resp.status_code})\n"
            f"Response: {resp.text}\n\n"
            "Double-check PAYPAL_CLIENT_ID and PAYPAL_SECRET are correct "
            "and match the PAYPAL_MODE you set (sandbox vs live use "
            "DIFFERENT credentials).\n"
        )
        sys.exit(1)
    return resp.json()["access_token"]


def _create_product(token, base):
    resp = requests.post(
        f"{base}/v1/catalogs/products",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
        json={
            "name": PRODUCT_NAME,
            "description": PRODUCT_DESC,
            "type": "SERVICE",
            "category": "ONLINE_GAMING",
        },
        timeout=15,
    )
    if resp.status_code not in (200, 201):
        sys.stderr.write(f"Create product failed: HTTP {resp.status_code}\n{resp.text}\n")
        sys.exit(1)
    return resp.json()["id"]


def _create_plan(token, base, product_id):
    body = {
        "product_id": product_id,
        "name": PLAN_NAME,
        "description": PLAN_DESC,
        "status": "ACTIVE",
        "billing_cycles": [
            {
                "frequency": {"interval_unit": "MONTH", "interval_count": 1},
                "tenure_type": "REGULAR",
                "sequence": 1,
                # total_cycles=0 → renew indefinitely until cancelled
                "total_cycles": 0,
                "pricing_scheme": {
                    "fixed_price": {
                        "value": PRICE_USD,
                        "currency_code": CURRENCY,
                    }
                },
            }
        ],
        "payment_preferences": {
            "auto_bill_outstanding": True,
            "setup_fee": {"value": "0", "currency_code": CURRENCY},
            "setup_fee_failure_action": "CONTINUE",
            "payment_failure_threshold": 3,
        },
    }
    resp = requests.post(
        f"{base}/v1/billing/plans",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
        json=body,
        timeout=15,
    )
    if resp.status_code not in (200, 201):
        sys.stderr.write(f"Create plan failed: HTTP {resp.status_code}\n{resp.text}\n")
        sys.exit(1)
    return resp.json()


def main():
    client_id = os.environ.get("PAYPAL_CLIENT_ID")
    secret = os.environ.get("PAYPAL_SECRET")
    mode = (os.environ.get("PAYPAL_MODE") or "sandbox").lower()
    if not client_id or not secret:
        sys.stderr.write(
            "ERROR: set PAYPAL_CLIENT_ID and PAYPAL_SECRET in the "
            "environment before running this script.\n"
            "\nExample:\n"
            "  PAYPAL_CLIENT_ID=AXXX... PAYPAL_SECRET=EXXX... \\\n"
            "  PAYPAL_MODE=sandbox python3 create_paypal_plan.py\n"
        )
        sys.exit(2)

    base = _base_url(mode)
    print(f"Mode: {mode}  (base URL: {base})")
    print(f"Authenticating...")
    token = _get_access_token(client_id, secret, base)
    print(f"  ✓ access token acquired")

    print(f"Creating product '{PRODUCT_NAME}'...")
    product_id = _create_product(token, base)
    print(f"  ✓ product id: {product_id}")

    print(f"Creating plan '{PLAN_NAME}' (${PRICE_USD}/mo, indefinite cycles)...")
    plan = _create_plan(token, base, product_id)
    plan_id = plan["id"]
    print(f"  ✓ plan id: {plan_id}")
    print(f"  status: {plan.get('status')}")

    print()
    print("=" * 60)
    print(f"  Done. Set this in Railway as PAYPAL_PLAN_ID:")
    print()
    print(f"    {plan_id}")
    print()
    print(f"  Also set:")
    print(f"    PAYPAL_CLIENT_ID  = (your {mode} client id)")
    print(f"    PAYPAL_SECRET     = (your {mode} secret)")
    print(f"    PAYPAL_WEBHOOK_ID = (from PayPal dashboard after you")
    print(f"                         create the webhook)")
    print(f"    PAYPAL_MODE       = {mode}")
    print("=" * 60)


if __name__ == "__main__":
    main()
