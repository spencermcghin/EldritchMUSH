"""SQLite -> Postgres row copy that preserves Evennia's pickled Attribute
values byte-for-byte.

Why not `dumpdata`/`loaddata`: Evennia stores Attribute/Tag values in a
custom PickledObjectField. Django's dumpdata serializes that field through
its JSON `value_to_string` path and loaddata's `to_python` does NOT reverse
it faithfully — complex values (strings, lists, dicts: ai_personality,
subscription_status, targetArray, shop_inventory, ...) come back as the raw
base64-pickle STRING that Evennia can no longer deserialize. Row counts
match while values are silently corrupt.

This module instead reads each row via the ORM `.values()` API on a second
`sqlite_src` connection (which applies the field's normal `from_db_value`,
yielding the real Python value and bypassing the idmapper instance cache),
then re-inserts via `bulk_create` on the Postgres connection (which applies
the field's normal `get_prep_value`). Read-then-write through the SAME field
class is a lossless round-trip. `bulk_create` also bypasses `post_save`, so
Evennia's `call_at_first_save` hook never fires (no crash, no default-attr
re-seed). The whole copy runs in one deferred-constraint transaction so
self-referential FKs (ObjectDB.db_location, exits' destinations) resolve at
commit regardless of insert order. Finally it resets Postgres sequences,
which explicit-PK inserts do not advance.

Invoked from start.sh's gated one-shot RESTORE path (PG_RESTORE=1). It must
run with DATABASE_URL pointing at Postgres and the source evennia.db3 still
present on the volume.
"""

import os
import django

# Tables migrate/post_migrate already populate on the fresh Postgres, and
# which nothing in Evennia references by integer PK (Attribute.db_model /
# Tag.db_model are CharFields, not ContentType FKs). Copying them would
# collide on PK; skip them and let migrate's versions stand.
EXCLUDE = {
    "contenttypes.contenttype",
    "auth.permission",
    "sessions.session",
    "admin.logentry",
    "sites.site",  # migrate creates pk=1; start.sh sets the real domain on boot
}


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.conf.settings")
    django.setup()
    import evennia
    evennia._init()  # load typeclass system so custom field classes resolve

    from django.conf import settings
    from django.core.management import call_command
    from django.db import connections, transaction
    from django.apps import apps

    engine = settings.DATABASES["default"]["ENGINE"]
    if "postgres" not in engine:
        raise SystemExit(f"pg_rowcopy: default DB is not Postgres ({engine})")

    # Clear the Postgres target so bulk_create can't PK-collide with a prior
    # (e.g. failed/partial) attempt. flush TRUNCATEs all tables (no signals),
    # then post_migrate recreates only the excluded contenttypes/permissions/
    # default site. Evennia's world objects are NOT created by migrate, so the
    # target is genuinely empty for every model we copy.
    call_command("flush", "--no-input", database="default")
    print("PG_FLUSHED target", flush=True)

    vol = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "")
    src = os.path.join(vol, "evennia.db3")
    if not os.path.exists(src):
        raise SystemExit(f"pg_rowcopy: source SQLite not found: {src}")

    connections.databases["sqlite_src"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": src,
        "ATOMIC_REQUESTS": False,
        "AUTOCOMMIT": True,
        "CONN_MAX_AGE": 0,
        "CONN_HEALTH_CHECKS": False,
        "OPTIONS": {},
        "TIME_ZONE": None,
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
        "TEST": {},
    }

    models = [
        m for m in apps.get_models(include_auto_created=True)
        if m._meta.label_lower not in EXCLUDE
    ]

    total = 0
    with transaction.atomic(using="default"):
        with connections["default"].cursor() as cur:
            cur.execute("SET CONSTRAINTS ALL DEFERRED")
        for model in models:
            # attname gives 'db_location_id' for FKs (settable on the model
            # ctor) and the plain name for value fields.
            attnames = [f.attname for f in model._meta.concrete_fields]
            rows = list(model.objects.using("sqlite_src").values(*attnames))
            if not rows:
                continue
            objs = [model(**row) for row in rows]
            model.objects.using("default").bulk_create(objs, batch_size=500)
            total += len(objs)
            print(f"COPY {model._meta.label_lower} = {len(objs)}", flush=True)
    print(f"COPY_TOTAL {total}", flush=True)

    # Reset every sequence to MAX(id); explicit-PK bulk_create does not
    # advance Postgres sequences, so the first in-game write would collide.
    reset = 0
    with connections["default"].cursor() as cur:
        for model in apps.get_models(include_auto_created=True):
            table = model._meta.db_table
            pk = model._meta.pk.column
            cur.execute("SELECT pg_get_serial_sequence(%s, %s)", [table, pk])
            row = cur.fetchone()
            seq = row[0] if row else None
            if seq:
                cur.execute(
                    f'SELECT setval(%s, (SELECT COALESCE(MAX("{pk}"), 1) '
                    f'FROM "{table}"))',
                    [seq],
                )
                reset += 1
    print(f"SEQ_RESET {reset}", flush=True)


if __name__ == "__main__":
    main()
