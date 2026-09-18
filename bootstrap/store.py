"""
Postgres-backed per-user config.

The handler needs exactly one thing from the database: the JSON config blob
for a given user, keyed by the Entra object id (`oid`) from the validated
token. That lookup lives in this file and nowhere else.

The default schema (schema.sql) is a single table:

    user_config(oid text PK, config jsonb, updated_at timestamptz)

`config` holds precisely what the endpoint should return for that user — the
sparse flat object from bootstrap.md, e.g.

    {
      "mcp_servers": [ ... ],
      "skills": [ ... ],
      "gateway_token": "...",
      "disabled_features": ["skills.authoring"]
    }

If your real source of truth looks different — normalized tables, a team or
group layer, per-Office-host overrides — change ONLY `lookup_config` below.
app.py calls it and knows nothing about the schema.
"""
import json

from asyncpg import Pool


class ConfigStore:
    def __init__(self, pool: Pool):
        self._pool = pool

    async def lookup_config(self, oid: str) -> dict:
        """
        Return the per-user config for `oid`, or {} if none is stored.

        asyncpg returns jsonb columns as JSON-encoded text, so decode them.
        """
        row = await self._pool.fetchrow(
            "SELECT config FROM user_config WHERE oid = $1", oid
        )
        if row is None:
            return {}
        config = row["config"]
        return json.loads(config) if isinstance(config, str) else config

    async def close(self) -> None:
        await self._pool.close()


async def create_store(database_url: str) -> ConfigStore:
    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=10)
    return ConfigStore(pool)
