-- Bootstrap per-user config — SQLite (local / debug).
-- Postgres equivalent: schema.sql. Keep the two in step.
--
-- `oid` is the Entra object id from the validated token — the stable lookup
-- key (email/upn can change; oid does not).
-- `config` is the sparse flat object the endpoint returns for that user.
-- See schema.sql for the full key vocabulary: mcp_servers, skills,
-- gateway_url, gateway_token, disabled_features, available_models,
-- access_policies, inference_headers, otlp_*, bootstrap_expires_at.
--
-- Applied automatically on startup by store.py — you do not need to run this
-- by hand. It is here so the schema is readable and reproducible.

CREATE TABLE IF NOT EXISTS user_config (
    oid        TEXT PRIMARY KEY,
    config     TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Example row — use a real object id from Entra admin center.
-- Note the key name must be `gateway_token`, not something litellm-specific:
-- the bootstrap response overrides manifest values *by key name*.
--
-- INSERT INTO user_config (oid, config) VALUES (
--   '00000000-0000-0000-0000-000000000000',
--   '{"gateway_token": "sk-your-key"}'
-- );
