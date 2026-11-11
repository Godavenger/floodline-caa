from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from threading import RLock

from .config import ROOT, stamp, wall_now


class Database:
    """One transactional contract, with SQLite and PostgreSQL implementations."""

    def __init__(self, url: str):
        self.url = url
        self.postgres = url.startswith(("postgresql://", "postgres://"))
        self.lock = RLock()
        if not self.postgres and not url.startswith("sqlite:///"):
            raise ValueError("DATABASE_URL must use sqlite:/// or postgresql://.")
        self.path = None if self.postgres else Path(url.removeprefix("sqlite:///"))

    def connect(self):
        if self.postgres:
            import psycopg
            from psycopg.rows import dict_row
            return psycopg.connect(self.url, row_factory=dict_row)
        result = sqlite3.connect(str(self.path), timeout=20, check_same_thread=False)
        result.row_factory = sqlite3.Row
        result.execute("PRAGMA foreign_keys = ON")
        result.execute("PRAGMA busy_timeout = 20000")
        return result

    @contextmanager
    def transaction(self):
        with self.lock:
            connection = self.connect()
            try:
                yield connection
                connection.commit()
            except BaseException:
                connection.rollback()
                raise
            finally:
                connection.close()

    def execute(self, connection, sql: str, params=()):
        return connection.execute(sql.replace("?", "%s") if self.postgres else sql, params)

    def one(self, connection, sql: str, params=()):
        row = self.execute(connection, sql, params).fetchone()
        return dict(row) if row is not None else None

    def all(self, connection, sql: str, params=()):
        return [dict(row) for row in self.execute(connection, sql, params).fetchall()]

    def meta(self, connection, key: str, default=None):
        row = self.one(connection, "SELECT value FROM settings WHERE key = ?", (key,))
        return json.loads(row["value"]) if row else default

    def set_meta(self, connection, key: str, value):
        self.execute(connection, "INSERT INTO settings(key, value) VALUES (?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, json.dumps(value)))

    def migrate(self):
        with self.transaction() as connection:
            self.execute(connection, "CREATE TABLE IF NOT EXISTS schema_migrations "
                         "(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
            migrations = [("001", ROOT / "backend" / "migrations" / "001_core.sql")]
            if self.postgres:
                migrations.append(("002-postgis", ROOT / "backend" / "migrations" / "002_postgis.sql"))
            for version, path in migrations:
                if self.one(connection, "SELECT version FROM schema_migrations WHERE version = ?", (version,)):
                    continue
                script = path.read_text(encoding="utf-8")
                if self.postgres:
                    connection.execute(script)
                else:
                    # No executescript implicit COMMIT: migrations remain in this transaction.
                    for statement in script.split(";"):
                        if statement.strip():
                            connection.execute(statement)
                self.execute(connection, "INSERT INTO schema_migrations VALUES (?, ?)", (version, stamp(wall_now())))

    def backup(self, destination: Path):
        if self.postgres:
            raise ValueError("Use pg_dump for the PostgreSQL adapter, as documented in the runbook.")
        with self.lock:
            source = self.connect()
            target = sqlite3.connect(str(destination))
            try:
                source.backup(target)
            finally:
                source.close()
                target.close()
