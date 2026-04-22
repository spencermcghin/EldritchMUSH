"""
File-based diagnostic logger.

Why this exists
---------------
Railway's log capture pipeline only catches output from start.sh and
nginx. Anything written by the Evennia server subprocess — including
print() to stdout, evennia.utils.logger calls to server.log, and even
the `tail -F` of server.log we set up in start.sh — is silently lost.
Repeated debugging rounds with [server]-prefixed log lines never made
it back to the user.

To break out of that black hole, every diagnostic point in the project
calls `diag_write(msg)` from this module. It appends a timestamped line
to a plain file on the persistent volume (/data/diag.log on Railway,
/tmp/diag.log otherwise). The HTTP endpoint defined in `diag_view`
serves the last N lines of that file as text/plain so we can read it
straight from a browser without grepping through Railway dashboards.

Usage
-----
    from web.diag import diag_write
    diag_write("CmdCharCreate.func ENTRY", caller="charcreate")

Then visit:
    https://eldritchmush-production.up.railway.app/api/diag/

Optional query: ?lines=N to control how many tail lines to return
(default 200, max 2000).
"""
import os
import sys
import time
import threading

from django.http import HttpResponse


def _resolve_log_path():
    """Pick a writable location for the diag log."""
    candidates = []
    volume = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
    if volume:
        candidates.append(os.path.join(volume, "diag.log"))
    candidates.append("/data/diag.log")
    candidates.append("/tmp/diag.log")
    for path in candidates:
        try:
            parent = os.path.dirname(path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)
            # touch
            with open(path, "a"):
                pass
            return path
        except Exception:
            continue
    return None


_LOG_PATH = _resolve_log_path()
_LOCK = threading.Lock()


def diag_write(msg, **fields):
    """Append a timestamped diagnostic line to the diag log file.

    Args:
        msg (str): Free-form message.
        **fields: Optional structured fields appended as key=value pairs.
    """
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    parts = [ts, msg]
    for k, v in fields.items():
        parts.append(f"{k}={v!r}")
    line = " | ".join(parts) + "\n"
    if _LOG_PATH is None:
        # Fallback: stderr only.
        sys.stderr.write(line)
        sys.stderr.flush()
        return
    try:
        with _LOCK:
            with open(_LOG_PATH, "a") as fh:
                fh.write(line)
    except Exception as exc:
        sys.stderr.write(f"[diag_write FAILED: {exc}] {line}")
        sys.stderr.flush()


def diag_view(request):
    """HTTP endpoint that returns the last N lines of the diag log.

    Superuser-only. The diag log captures raw player commands, ask /
    whisper text, and stack traces — treat it as PII-bearing. Builders
    and Admins are explicitly excluded so the audit trail cannot be
    siphoned by content-moderation staff.

    Plain text response so it's easy to read in a browser.
    Visit /api/diag/ — optionally append ?lines=N to control how much.
    """
    user = request.user
    if not user.is_authenticated:
        return HttpResponse("Authentication required", status=401, content_type="text/plain")
    if not user.is_superuser:
        return HttpResponse("Superuser access required", status=403, content_type="text/plain")
    try:
        n = int(request.GET.get("lines", "200"))
    except ValueError:
        n = 200
    n = max(1, min(n, 2000))

    if _LOG_PATH is None or not os.path.exists(_LOG_PATH):
        return HttpResponse(
            f"diag log not available (path={_LOG_PATH!r})",
            content_type="text/plain",
        )

    try:
        with open(_LOG_PATH, "r") as fh:
            lines = fh.readlines()
        body = "".join(lines[-n:])
    except Exception as exc:
        body = f"failed to read {_LOG_PATH}: {exc}"

    header = f"# diag log: {_LOG_PATH}\n# showing last {n} lines\n# ---\n"
    return HttpResponse(header + body, content_type="text/plain; charset=utf-8")
