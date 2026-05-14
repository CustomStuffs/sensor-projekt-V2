"""aiosqlite connection pool and schema initialisation."""

import aiosqlite
import os

_DB_PATH = os.environ.get("DB_PATH", "sensor_hub.db")
_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

_conn: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _conn
    if _conn is None:
        _conn = await aiosqlite.connect(_DB_PATH)
        _conn.row_factory = aiosqlite.Row
        await _conn.execute("PRAGMA foreign_keys = ON")
        await _init_schema(_conn)
    return _conn


async def _init_schema(conn: aiosqlite.Connection):
    with open(_SCHEMA_PATH) as f:
        schema = f.read()
    await conn.executescript(schema)
    await _migrate(conn)
    await conn.commit()


async def _migrate(conn: aiosqlite.Connection):
    # Each entry is a one-shot ALTER TABLE — silently skipped if column exists.
    migrations = [
        "ALTER TABLE readings ADD COLUMN water_level REAL",
    ]
    for sql in migrations:
        try:
            await conn.execute(sql)
        except Exception:
            pass


async def close_db():
    global _conn
    if _conn:
        await _conn.close()
        _conn = None
