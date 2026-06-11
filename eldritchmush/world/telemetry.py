"""
Operational telemetry — counters, heartbeats, and threshold alerts.

Guards against runaway costs and silent infra failures:

- `incr(name, value)` — thread-safe in-process counters, wired into the
  AI layer (calls, tokens, $cost, cache hits, refusals, errors), the
  quest engine, and anything else that wants visibility.
- A heartbeat (TelemetryHeartbeatScript, every 5 min) appends one JSON
  line to {volume}/telemetry.log with process RSS, session count, DB
  size, day's LLM spend, and the counter snapshot — greppable history
  in `railway logs` and on the volume.
- Threshold checks ride the heartbeat: LLM spend nearing the daily
  budget, LLM error bursts, and oversized DB all alert via Resend
  email to ADMIN_EMAIL (rate-limited to one email per alert type per
  6h, and always printed loudly for `railway logs`).
- Admins can read the live snapshot at /api/admin/metrics/.

Env vars:
    TELEMETRY_PATH            — heartbeat log path; defaults to
                                $RAILWAY_VOLUME_MOUNT_PATH/telemetry.log
                                or /tmp/telemetry.log
    TELEMETRY_DB_ALERT_MB     — alert when evennia.db3 exceeds (default 512)
    TELEMETRY_LLM_ERR_ALERT   — alert when llm.errors grows by more than
                                this between heartbeats (default 10)
"""
import json
import os
import sys
import threading
import time

_LOCK = threading.Lock()
_COUNTERS = {}
_LAST_HEARTBEAT_COUNTERS = {}
_ALERT_SENT = {}          # kind -> last sent ts
_ALERT_COOLDOWN = 6 * 3600
_STARTED_AT = time.time()


def incr(name, value=1):
    """Increment a counter. Never raises."""
    try:
        with _LOCK:
            _COUNTERS[name] = _COUNTERS.get(name, 0) + value
    except Exception:
        pass


def counters():
    with _LOCK:
        return dict(_COUNTERS)


def _telemetry_path():
    p = os.environ.get("TELEMETRY_PATH")
    if p:
        return p
    vol = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
    if vol:
        return os.path.join(vol, "telemetry.log")
    return "/tmp/telemetry.log"


def _rss_mb():
    try:
        import resource
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # ru_maxrss is KB on Linux, bytes on macOS.
        return round(rss / (1024 if sys.platform != "darwin" else 1024 * 1024), 1)
    except Exception:
        return None


def _db_mb():
    try:
        from django.conf import settings
        path = settings.DATABASES["default"]["NAME"]
        return round(os.path.getsize(path) / (1024 * 1024), 1)
    except Exception:
        return None


def _session_count():
    try:
        from evennia.server.sessionhandler import SESSIONS
        return SESSIONS.count()
    except Exception:
        return None


def _llm_spend():
    """Today's LLM spend + budget from ai_npc's kill-switch state."""
    try:
        from world import ai_npc
        with ai_npc._SPEND_LOCK:
            spent = ai_npc._SPEND["usd"] if ai_npc._SPEND["day"] == ai_npc._spend_day() else 0.0
        return round(spent, 4), ai_npc._budget_usd()
    except Exception:
        return None, None


def snapshot():
    """Current state — served by /api/admin/metrics/."""
    spent, budget = _llm_spend()
    return {
        "ts": int(time.time()),
        "uptime_s": int(time.time() - _STARTED_AT),
        "sessions": _session_count(),
        "rss_mb": _rss_mb(),
        "db_mb": _db_mb(),
        "llm_spend_usd_today": spent,
        "llm_budget_usd": budget,
        "counters": counters(),
    }


def alert(kind, subject, body):
    """Loud print + admin email, rate-limited per alert kind."""
    print(f"[telemetry] ALERT ({kind}): {subject} — {body}", flush=True)
    now = time.time()
    with _LOCK:
        last = _ALERT_SENT.get(kind, 0)
        if now - last < _ALERT_COOLDOWN:
            return
        _ALERT_SENT[kind] = now
    try:
        from world.email import send_email, ADMIN_EMAIL
        send_email(
            ADMIN_EMAIL,
            f"[EldritchMUSH telemetry] {subject}",
            f"<p><b>{subject}</b></p><p>{body}</p>"
            f"<pre>{json.dumps(snapshot(), indent=2)}</pre>",
        )
    except Exception as exc:
        print(f"[telemetry] alert email failed: {exc!r}", flush=True)


def heartbeat():
    """Write one JSON line of state; run threshold checks. Called by
    TelemetryHeartbeatScript every 5 minutes. Never raises."""
    global _LAST_HEARTBEAT_COUNTERS
    try:
        record = snapshot()
        line = json.dumps(record, ensure_ascii=False)
        print(f"[telemetry] {line}", flush=True)
        try:
            path = _telemetry_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8") as fp:
                fp.write(line + "\n")
        except Exception:
            pass

        # ── Threshold checks ─────────────────────────────────────────
        spent, budget = record["llm_spend_usd_today"], record["llm_budget_usd"]
        if spent is not None and budget and spent >= 0.8 * budget:
            alert(
                "llm_budget_80",
                f"LLM spend at ${spent:.2f} of ${budget:.2f} daily budget",
                "NPCs fall back to canned lines when the budget exhausts. "
                "Raise NPC_LLM_DAILY_BUDGET_USD if this is legitimate traffic.",
            )

        cur = record["counters"]
        prev = _LAST_HEARTBEAT_COUNTERS
        err_delta = cur.get("llm.errors", 0) - prev.get("llm.errors", 0)
        try:
            err_cap = int(os.environ.get("TELEMETRY_LLM_ERR_ALERT", "10"))
        except ValueError:
            err_cap = 10
        if err_delta > err_cap:
            alert(
                "llm_error_burst",
                f"{int(err_delta)} LLM errors in the last heartbeat window",
                "Provider outage, bad key, or rate limiting — players are "
                "seeing canned fallback lines. Check railway logs for "
                "[ai_npc] error lines.",
            )

        db_mb = record["db_mb"]
        try:
            db_cap = int(os.environ.get("TELEMETRY_DB_ALERT_MB", "512"))
        except ValueError:
            db_cap = 512
        if db_mb and db_mb > db_cap:
            alert(
                "db_size",
                f"evennia.db3 is {db_mb} MB (cap {db_cap} MB)",
                "SQLite growth — check ai_conversations bloat, audit "
                "log-style attributes, or runaway object spawning.",
            )

        _LAST_HEARTBEAT_COUNTERS = dict(cur)
        return record
    except Exception as exc:
        print(f"[telemetry] heartbeat failed: {exc!r}", flush=True)
        return None


def read_heartbeat_tail(limit=72):
    """Last `limit` heartbeat records (default ~6h), newest first."""
    try:
        with open(_telemetry_path(), "r", encoding="utf-8") as fp:
            lines = fp.readlines()[-limit:]
    except Exception:
        return []
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    out.reverse()
    return out
