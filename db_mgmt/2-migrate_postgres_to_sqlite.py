"""One-off migration: copy discobase's live data from the Windows-side
PostgreSQL instance into the project's new SQLite database.

Uses DuckDB's postgres/sqlite extensions to copy tables directly, without
staging through pandas. Only the actual application data is copied
(discobase_* tables + users_customuser); Django/allauth-internal tables
(auth_permission, django_content_type, django_session, ...) are left alone
so the schema created by `manage.py migrate` stays authoritative.

Usage (from the `app` directory, after `manage.py migrate` has created a
fresh db.sqlite3):

    uv run python ../db_mgmt/2-migrate_postgres_to_sqlite.py

Safe to re-run: it refuses to touch a table that already has rows.
"""

import sqlite3
from pathlib import Path

import duckdb
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config_dev.yaml"
SQLITE_PATH = BASE_DIR / "app" / "db.sqlite3"

# Ordered so that every FK target is copied before the table that references it.
TABLES = [
    "discobase_country",
    "discobase_genre",
    "discobase_recordformat",
    "discobase_label",
    "discobase_artist",
    "users_customuser",
    "discobase_record",
    "discobase_record_artists",
    "discobase_record_labels",
    "discobase_song",
    "discobase_trxcredit",
    "discobase_dump",
]


def load_postgres_conn_str() -> str:
    """Build a libpq connection string from config_dev.yaml."""
    cfg = yaml.safe_load(CONFIG_PATH.read_text())["POSTGRES"]
    return (
        f"host={cfg['HOST']} port={cfg['PORT']} dbname={cfg['DATABASE']} "
        f"user={cfg['USER']} password={cfg['PASSWORD']}"
    )


def assert_sqlite_ready() -> None:
    """Fail fast if db.sqlite3 is missing, or if any target table already
    has data (re-running the copy would create duplicates)."""
    if not SQLITE_PATH.exists():
        raise SystemExit(
            f"{SQLITE_PATH} does not exist yet. Run `manage.py migrate` first."
        )
    con = sqlite3.connect(SQLITE_PATH)
    try:
        for table in TABLES:
            (count,) = con.execute(f"SELECT count(*) FROM {table}").fetchone()
            if count:
                raise SystemExit(
                    f"{table} already has {count} row(s) in {SQLITE_PATH}. "
                    "Refusing to re-run the copy over existing data."
                )
    finally:
        con.close()


def copy_tables(pg_conn_str: str) -> None:
    """Copy each table's data from Postgres into the SQLite file via DuckDB."""
    con = duckdb.connect()
    con.execute("INSTALL postgres; LOAD postgres;")
    con.execute("INSTALL sqlite; LOAD sqlite;")
    con.execute(f"ATTACH '{pg_conn_str}' AS pg (TYPE postgres, READ_ONLY)")
    con.execute(f"ATTACH '{SQLITE_PATH}' AS sq (TYPE sqlite)")

    for table in TABLES:
        # BY NAME matches columns by name rather than position, so column
        # order differences between the two schemas can't silently swap data.
        con.execute(f'INSERT INTO sq.{table} BY NAME SELECT * FROM pg.public."{table}"')
        (count,) = con.execute(f"SELECT count(*) FROM sq.{table}").fetchone()
        print(f"  {table}: {count} rows copied")

    con.close()


def fix_autoincrement_sequences() -> None:
    """DuckDB inserts explicit ids but doesn't know about SQLite's
    AUTOINCREMENT bookkeeping table. Without this, the next INSERT made
    through Django would restart ids at 1 and collide with existing rows.
    """
    con = sqlite3.connect(SQLITE_PATH)
    try:
        for table in TABLES:
            (max_id,) = con.execute(f"SELECT max(id) FROM {table}").fetchone()
            if max_id is None:
                continue
            # sqlite_sequence has no PRIMARY KEY/UNIQUE constraint to upsert
            # against, so check for an existing row explicitly instead.
            cur = con.execute(
                "UPDATE sqlite_sequence SET seq = ? WHERE name = ?", (max_id, table)
            )
            if cur.rowcount == 0:
                con.execute(
                    "INSERT INTO sqlite_sequence (name, seq) VALUES (?, ?)",
                    (table, max_id),
                )
        con.commit()
    finally:
        con.close()


def main() -> None:
    assert_sqlite_ready()
    pg_conn_str = load_postgres_conn_str()
    print(f"Copying data from Postgres into {SQLITE_PATH} ...")
    copy_tables(pg_conn_str)
    fix_autoincrement_sequences()
    print("Done. Autoincrement counters fixed up for all copied tables.")


if __name__ == "__main__":
    main()
