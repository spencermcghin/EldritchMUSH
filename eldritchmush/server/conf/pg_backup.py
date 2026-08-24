"""Cheap Postgres backups: gzipped pg_dump to the app volume.

Railway's native volume backups are plan-gated, so this does a free
logical backup instead. It runs `pg_dump` against DATABASE_URL and writes a
gzipped SQL dump to $RAILWAY_VOLUME_MOUNT_PATH/pg_backups/ — which lives on
the APP volume, a different physical volume than the Postgres data volume,
so it survives a Postgres-volume failure. Retention keeps the newest N.

Restore (manual):
    gunzip -c pg_backups/evennia-pg-<ts>.sql.gz | psql "$DATABASE_URL"
(into a freshly-provisioned empty Postgres.)

Invoked from start.sh on every boot and from PgBackupScript once a day.
No-op when not running on Postgres (e.g. local SQLite dev).
"""

import datetime
import glob
import gzip
import os
import shutil
import subprocess

RETENTION = 14  # keep the newest N dumps


def _backup_dir():
    vol = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "/tmp")
    d = os.path.join(vol, "pg_backups")
    os.makedirs(d, exist_ok=True)
    return d


def run_backup(reason="manual"):
    """Dump the Postgres DB to a gzipped file on the app volume.

    Returns the path written, or None if skipped/failed. Never raises —
    a backup failure must not take down a boot or a game tick.
    """
    db_url = os.environ.get("DATABASE_URL", "")
    if "postgres" not in db_url:
        return None  # not on Postgres — nothing to back up here
    if not shutil.which("pg_dump"):
        print("[pg_backup] pg_dump not installed — skipping", flush=True)
        return None
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
    out = os.path.join(_backup_dir(), f"evennia-pg-{ts}.sql.gz")
    try:
        # Stream pg_dump stdout straight into gzip to avoid a large temp file.
        with gzip.open(out, "wb") as gz:
            proc = subprocess.Popen(
                ["pg_dump", "--no-owner", "--no-privileges", db_url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            for chunk in iter(lambda: proc.stdout.read(65536), b""):
                gz.write(chunk)
            _, err = proc.communicate()
        if proc.returncode != 0:
            print(f"[pg_backup] pg_dump failed ({reason}): "
                  f"{err.decode(errors='replace')[:200]}", flush=True)
            try:
                os.remove(out)
            except OSError:
                pass
            return None
        size = os.path.getsize(out)
        print(f"[pg_backup] wrote {out} ({size} bytes, {reason})", flush=True)
        _prune()
        return out
    except Exception as exc:
        print(f"[pg_backup] error ({reason}): {exc!r}", flush=True)
        return None


def _prune():
    files = sorted(
        glob.glob(os.path.join(_backup_dir(), "evennia-pg-*.sql.gz")),
        reverse=True,
    )
    for old in files[RETENTION:]:
        try:
            os.remove(old)
        except OSError:
            pass


if __name__ == "__main__":
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.conf.settings")
    django.setup()
    run_backup(reason="cli")
