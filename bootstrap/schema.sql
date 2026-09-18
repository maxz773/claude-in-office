-- Bootstrap per-user config.
--
-- `oid` is the Entra object id from the validated token — the stable lookup
-- key (email/upn can change; oid does not).
-- `config` is the sparse flat object the endpoint returns for that user.
-- See bootstrap.md for the full key vocabulary: mcp_servers, skills,
-- gateway_url, gateway_token, disabled_features, available_models,
-- access_policies, inference_headers, otlp_*, bootstrap_expires_at.

CREATE TABLE IF NOT EXISTS user_config (
    oid        text PRIMARY KEY,
    config     jsonb NOT NULL DEFAULT '{}'::jsonb,
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Example row — use a real object id from Entra admin center:
--
-- INSERT INTO user_config (oid, config) VALUES (
--   '00000000-0000-0000-0000-000000000000',
--   '{
--      "mcp_servers": [
--        {"url": "https://mcp.linear.app/sse", "label": "Linear"}
--      ],
--      "skills": [
--        {"name": "compliance-check",
--         "content": "IyBDb21wbGlhbmNlIGNoZWNrCgpSZXZpZXcgdGhlIGRvY3VtZW50Li4u"}
--      ]
--    }'::jsonb
-- );
