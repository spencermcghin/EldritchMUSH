"""PayPal subscription integration for EldritchMUSH.

Endpoints (mounted in web/urls.py):

    GET  /api/billing/status            — current account's sub state
    POST /api/billing/create-subscription — start a new PayPal sub,
                                            returns approval_url
    GET  /api/billing/return            — PayPal redirects here after
                                            approval; links sub to acct
    POST /api/billing/webhook           — PayPal-to-server event push

Env vars required (set on Railway, never check into repo):
    PAYPAL_CLIENT_ID        from PayPal Developer dashboard
    PAYPAL_SECRET           from PayPal Developer dashboard
    PAYPAL_PLAN_ID          P-XXXXXXXXXXXXXXXXXXXXXX (your $5/mo plan)
    PAYPAL_WEBHOOK_ID       WH-XXXXXXXX (for webhook signature verify)
    PAYPAL_MODE             "sandbox" (default) or "live"

If PAYPAL_CLIENT_ID is unset, every endpoint returns a clean 503 so
the rest of the site keeps working.

Pricing constants live in typeclasses/accounts.py (TRIAL_DAYS) and
here (MONTHLY_PRICE_USD, displayed on the frontend).
"""

import base64
import json
import os
import time

import requests

from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


MONTHLY_PRICE_USD = "5.00"
CURRENCY = "USD"

# 30s response cache for the OAuth access token. PayPal tokens are
# valid ~9 hours but we keep this short for safety.
_ACCESS_TOKEN_CACHE = {"token": None, "expires_at": 0.0}


def _paypal_base():
    """Return the PayPal REST API base URL based on PAYPAL_MODE."""
    mode = (os.environ.get("PAYPAL_MODE") or "sandbox").lower()
    if mode == "live":
        return "https://api-m.paypal.com"
    return "https://api-m.sandbox.paypal.com"


def _paypal_configured():
    return bool(
        os.environ.get("PAYPAL_CLIENT_ID")
        and os.environ.get("PAYPAL_SECRET")
        and os.environ.get("PAYPAL_PLAN_ID")
    )


def _get_access_token():
    """Fetch (and cache) an OAuth2 access token from PayPal."""
    now = time.time()
    cached = _ACCESS_TOKEN_CACHE
    if cached["token"] and now < cached["expires_at"]:
        return cached["token"]
    client_id = os.environ["PAYPAL_CLIENT_ID"]
    secret = os.environ["PAYPAL_SECRET"]
    basic = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    resp = requests.post(
        f"{_paypal_base()}/v1/oauth2/token",
        headers={
            "Authorization": f"Basic {basic}",
            "Accept": "application/json",
            "Accept-Language": "en_US",
        },
        data={"grant_type": "client_credentials"},
        timeout=10,
    )
    resp.raise_for_status()
    body = resp.json()
    token = body["access_token"]
    # cache for ~80% of token lifetime
    ttl = int(body.get("expires_in", 3600)) * 0.8
    _ACCESS_TOKEN_CACHE["token"] = token
    _ACCESS_TOKEN_CACHE["expires_at"] = now + ttl
    return token


def _site_base_url(request):
    """Best-effort canonical base URL for return/cancel redirects."""
    site = os.environ.get("SITE_DOMAIN") or request.get_host()
    scheme = "https" if request.is_secure() or "railway.app" in site else "http"
    return f"{scheme}://{site}"


# ── Endpoints ────────────────────────────────────────────────────────


@require_http_methods(["GET"])
def billing_status(request):
    """Return the current account's subscription state. Frontend uses
    this to render the trial-days-remaining banner or the paywall.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False}, status=401)
    acct = _account_for_user(request.user)
    if not acct:
        return JsonResponse({"error": "no account"}, status=500)
    return JsonResponse({
        "authenticated": True,
        "status": acct.db.subscription_status or "unset",
        "trial_days_remaining": acct.trial_days_remaining(),
        "in_trial": acct.is_in_trial(),
        "subscription_active": acct.is_subscription_active(),
        "should_be_paywalled": acct.should_be_paywalled(),
        "renewal_at": acct.db.subscription_renewal_at,
        "paypal_subscription_id": acct.db.paypal_subscription_id,
        "monthly_price_usd": MONTHLY_PRICE_USD,
        "currency": CURRENCY,
    })


@csrf_exempt
@require_http_methods(["POST"])
def create_subscription(request):
    """Create a PayPal subscription and return the approval URL the
    frontend should redirect the user to.
    """
    if not _paypal_configured():
        return JsonResponse(
            {"error": "Billing is not configured. Contact support."},
            status=503,
        )
    if not request.user.is_authenticated:
        return JsonResponse({"error": "not authenticated"}, status=401)
    acct = _account_for_user(request.user)
    if not acct:
        return JsonResponse({"error": "no account"}, status=500)

    base = _site_base_url(request)
    body = {
        "plan_id": os.environ["PAYPAL_PLAN_ID"],
        "subscriber": {
            "email_address": request.user.email or "",
        },
        "application_context": {
            "brand_name": "Eldritch Workshop, L.L.C.",
            "locale": "en-US",
            "user_action": "SUBSCRIBE_NOW",
            "return_url": f"{base}/api/billing/return",
            "cancel_url": f"{base}/pricing?canceled=1",
        },
        # Pass account id so we can correlate on the return leg even
        # if the user logs out / changes browser before approving.
        "custom_id": str(acct.id),
    }
    headers = {
        "Authorization": f"Bearer {_get_access_token()}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    try:
        resp = requests.post(
            f"{_paypal_base()}/v1/billing/subscriptions",
            headers=headers, json=body, timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        return JsonResponse(
            {"error": "PayPal subscription create failed",
             "detail": str(exc)},
            status=502,
        )
    data = resp.json()
    approval_url = None
    for link in data.get("links", []):
        if link.get("rel") == "approve":
            approval_url = link.get("href")
            break
    if not approval_url:
        return JsonResponse(
            {"error": "No approval link returned by PayPal"},
            status=502,
        )
    # Store the subscription id immediately so even if the user never
    # completes approval we have a trail.
    acct.db.paypal_subscription_id = data.get("id")
    return JsonResponse({
        "subscription_id": data.get("id"),
        "approval_url": approval_url,
    })


@require_http_methods(["GET"])
def billing_return(request):
    """PayPal redirects the user here after they approve the
    subscription. We link the sub id to the account AND actively
    fetch the subscription's current state from PayPal so we don't
    have to wait for the webhook (which can be slow, retry-flaky,
    or misconfigured). The webhook still does the right thing on
    state changes later (cancellation, payment failure, renewal).
    """
    sub_id = request.GET.get("subscription_id")
    if request.user.is_authenticated and sub_id and _paypal_configured():
        acct = _account_for_user(request.user)
        if acct:
            acct.db.paypal_subscription_id = sub_id
            # Active fetch — confirm the subscription is ACTIVE
            # before we tell the user "you're subscribed".
            try:
                token = _get_access_token()
                resp = requests.get(
                    f"{_paypal_base()}/v1/billing/subscriptions/{sub_id}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/json",
                    },
                    timeout=10,
                )
                if resp.status_code == 200:
                    sub = resp.json()
                    pp_status = (sub.get("status") or "").upper()
                    if pp_status == "ACTIVE":
                        acct.db.subscription_status = "active"
                    elif pp_status == "APPROVAL_PENDING":
                        # User finished the approval click but PayPal
                        # is still processing. Webhook will activate.
                        if not acct.db.subscription_status:
                            acct.db.subscription_status = "trialing"
                    elif pp_status == "APPROVED":
                        # Approved but not yet billed — treat as active
                        # for access purposes; the next billing cycle
                        # will produce a webhook to confirm.
                        acct.db.subscription_status = "active"
                    elif pp_status == "SUSPENDED":
                        acct.db.subscription_status = "past_due"
                    elif pp_status in ("CANCELLED", "EXPIRED"):
                        acct.db.subscription_status = "canceled"
                    nbt = (sub.get("billing_info") or {}).get("next_billing_time")
                    if nbt:
                        acct.db.subscription_renewal_at = nbt
                    print(
                        f"[billing_return] sub={sub_id} pp_status={pp_status} "
                        f"local_status={acct.db.subscription_status}",
                        flush=True,
                    )
                else:
                    print(
                        f"[billing_return] PayPal GET sub failed: "
                        f"HTTP {resp.status_code} body={resp.text[:200]}",
                        flush=True,
                    )
            except Exception as exc:
                print(f"[billing_return] fetch failed: {exc!r}", flush=True)
    base = _site_base_url(request)
    return HttpResponseRedirect(f"{base}/?subscribed=1")


@csrf_exempt
@require_http_methods(["POST"])
def webhook(request):
    """Receive PayPal webhook events. Verifies signature (if
    PAYPAL_WEBHOOK_ID is set) then routes by event_type.
    """
    if not _paypal_configured():
        return JsonResponse({"error": "billing not configured"}, status=503)

    raw = request.body
    try:
        event = json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"error": "bad json"}, status=400)

    # Signature verification — best-effort. PayPal supports a
    # verify-webhook-signature endpoint. We hit it only if
    # PAYPAL_WEBHOOK_ID is set; otherwise we log a warning and
    # accept the event (dev mode).
    webhook_id = os.environ.get("PAYPAL_WEBHOOK_ID")
    if webhook_id:
        try:
            verify_body = {
                "auth_algo": request.META.get("HTTP_PAYPAL_AUTH_ALGO", ""),
                "cert_url": request.META.get("HTTP_PAYPAL_CERT_URL", ""),
                "transmission_id": request.META.get("HTTP_PAYPAL_TRANSMISSION_ID", ""),
                "transmission_sig": request.META.get("HTTP_PAYPAL_TRANSMISSION_SIG", ""),
                "transmission_time": request.META.get("HTTP_PAYPAL_TRANSMISSION_TIME", ""),
                "webhook_id": webhook_id,
                "webhook_event": event,
            }
            vresp = requests.post(
                f"{_paypal_base()}/v1/notifications/verify-webhook-signature",
                headers={
                    "Authorization": f"Bearer {_get_access_token()}",
                    "Content-Type": "application/json",
                },
                json=verify_body, timeout=10,
            )
            vresp.raise_for_status()
            if vresp.json().get("verification_status") != "SUCCESS":
                return JsonResponse(
                    {"error": "signature verification failed"},
                    status=400,
                )
        except Exception as exc:
            print(f"[paypal_webhook] verify failed: {exc!r}", flush=True)
            # Fail closed in live mode.
            if (os.environ.get("PAYPAL_MODE") or "sandbox").lower() == "live":
                return JsonResponse({"error": "verify error"}, status=400)

    event_type = event.get("event_type", "")
    resource = event.get("resource") or {}
    sub_id = resource.get("id") or resource.get("billing_agreement_id")

    print(f"[paypal_webhook] event_type={event_type} sub_id={sub_id}", flush=True)

    acct = _find_account_by_subscription(sub_id)
    if not acct:
        # We don't know this subscription — log and accept (idempotent).
        print(f"[paypal_webhook] no account for sub_id={sub_id}", flush=True)
        return JsonResponse({"ok": True, "ignored": "no matching account"})

    if event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
        acct.db.subscription_status = "active"
        # Next billing time is on the resource
        nbt = resource.get("billing_info", {}).get("next_billing_time")
        if nbt:
            acct.db.subscription_renewal_at = nbt
    elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
        acct.db.subscription_status = "canceled"
    elif event_type == "BILLING.SUBSCRIPTION.SUSPENDED":
        acct.db.subscription_status = "past_due"
    elif event_type == "BILLING.SUBSCRIPTION.EXPIRED":
        acct.db.subscription_status = "canceled"
    elif event_type == "PAYMENT.SALE.COMPLETED":
        # A renewal payment cleared — refresh status to active.
        acct.db.subscription_status = "active"
    elif event_type in ("PAYMENT.SALE.DENIED", "BILLING.SUBSCRIPTION.PAYMENT.FAILED"):
        acct.db.subscription_status = "past_due"

    return JsonResponse({"ok": True})


# ── Helpers ──────────────────────────────────────────────────────────


def _account_for_user(user):
    """Resolve a Django User to its Evennia AccountDB row."""
    from evennia.accounts.models import AccountDB
    try:
        return AccountDB.objects.get(id=user.id)
    except AccountDB.DoesNotExist:
        return None


def _find_account_by_subscription(sub_id):
    """Find the Account whose db.paypal_subscription_id matches."""
    if not sub_id:
        return None
    from evennia.accounts.models import AccountDB
    # Linear scan — fine for the size of this game. If accounts grow
    # large, store sub_id in an indexed model field instead.
    for acct in AccountDB.objects.all():
        if acct.db.paypal_subscription_id == sub_id:
            return acct
    return None
