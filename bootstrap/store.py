"""
SQLite-backed per-user config (local / debug).

The handler needs exactly one thing from the database: the JSON config blob
for a given user, keyed by the Entra object id (`oid`) from the validated
token. That lookup lives in this file and nowhere else.

This is the **SQLite variant**. The table is created on first start from
schema.sqlite.sql sitting next to this file, so there is nothing to
provision and no migration step:

    python app.py                       # uses bootstrap/bootstrap.db

The schema mirrors the Postgres one in schema.sql:

    user_config(oid text PK, config text, updated_at text)

`config` holds precisely what the endpoint should return for that user — the
sparse flat object from bootstrap.md, e.g.

    {
      "mcp_servers": [ ... ],
      "skills": [ ... ],
      "gateway_token": "...",
      "disabled_features": ["skills.authoring"]
    }

Going back to Postgres — restore this file and the driver:

    git show fa00ec7:bootstrap/store.py > bootstrap/store.py
    # then swap aiosqlite back for asyncpg in requirements.txt

The only thing that changes between the two is `lookup_config`. app.py calls
it and knows nothing about the schema.
"""
import json
import re
from pathlib import Path

import aiosqlite

_SCHEMA_PATH = Path(__file__).with_name("schema.sqlite.sql")


class ConfigStore:
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def lookup_config(self, oid: str) -> dict:
        """
        Return the per-user config for `oid`, or {} if none is stored.

        `config` is a TEXT column, so it comes back as a JSON string — decode it.
        """
        async with self._conn.execute(
            "SELECT config FROM user_config WHERE oid = ?", (oid,)
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return {}
        config = row[0]
        return json.loads(config) if isinstance(config, str) else config

    async def close(self) -> None:
        await self._conn.close()


def db_path(database_url: str) -> str:
    """
    Turn a sqlite URL into a filesystem path; a bare path passes through.

        sqlite:///./bootstrap.db   ->  ./bootstrap.db
        sqlite:///E:/tmp/dev.db    ->  E:/tmp/dev.db
        sqlite:////tmp/dev.db      ->  /tmp/dev.db
        ./bootstrap.db             ->  ./bootstrap.db
    """
    if "://" not in database_url:
        return database_url
    rest = database_url.split("://", 1)[1]
    if rest.startswith("//"):            # sqlite:////abs  ->  /abs
        return rest[1:]
    if re.match(r"^/[A-Za-z]:", rest):   # sqlite:///E:/..  ->  E:/..
        return rest[1:]
    return rest[1:] if rest.startswith("/") else rest


async def create_store(database_url: str) -> ConfigStore:
    conn = await aiosqlite.connect(db_path(database_url))
    # CREATE TABLE IF NOT EXISTS, so this is safe to run on every start — no
    # separate migration step for local work.
    await conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
    await conn.commit()
    return ConfigStore(conn)
