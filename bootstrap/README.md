# Bootstrap endpoint — FastAPI + Postgres

A minimal FastAPI implementation of the Claude in Office `/bootstrap`
endpoint. It validates the caller's Entra ID token and returns per-user
config (skills, MCP servers, gateway overrides, …) read from Postgres.

- `app.py` — the HTTP layer: JWT validation, CORS, the `/bootstrap` route.
- `config.py` — environment-driven settings. Edit this.
- `store.py` — the Postgres lookup keyed by Entra `oid`.
- `schema.sql` — the default table.

## Setup

```bash
pip install -r requirements.txt
export TENANT_ID=<your-tenant-guid>
export DATABASE_URL=postgresql://user:pass@host:5432/bootstrap

# create the table
psql "$DATABASE_URL" -f schema.sql
```

Find your tenant id (or use `az account show --query tenantId`):

```python
# get_tenant_id.py in the reference example does the same via OIDC discovery.
```

## Run

```bash
python app.py
```

Deploy it anywhere that can reach Postgres (Cloud Run, App Service,
ECS, a VM). The add-in calls `GET /bootstrap` with:

```
Authorization: Bearer <entra_token>
X-Claude-User-Agent: claude-word/1.0.0
```

CORS is already pinned to `https://pivot.claude.ai` — do **not** relax
`allow_origins`; the bearer token is the only real auth.

## How the lookup works

1. `validate()` checks the JWT signature against Microsoft's JWKS, and
   verifies `aud`, `iss`, and `exp`.
2. The `oid` claim is the stable user key.
3. `store.lookup_config(oid)` returns the row's `config` jsonb, decoded to a
   dict, or `{}` when the user has no row — which means "org-wide config".
4. The dict is returned verbatim (plus `bootstrap_expires_at` when
   `BOOTSTRAP_TTL_SECONDS > 0`).

Return sparse: only keys that differ from the manifest defaults.

## Adapting to your real tables

The only place that knows the schema is `store.py`. If your source of truth
is normalized (users, teams, per-team entitlements) rather than a flat
`jsonb` blob, rewrite `lookup_config` to run those joins and assemble the
response dict. `app.py` does not change.

## Local dev with a fake token

```bash
pip install -r requirements.txt
export TENANT_ID=dev-tenant
export DATABASE_URL=postgresql://user:pass@localhost:5432/bootstrap
# (from the reference example) mint a self-signed token + JWKS:
TOKEN=$(python ../mint_dev_token.py --oid alice)
DEV_JWKS_PATH=dev_jwks.json python app.py &
curl -H "Authorization: Bearer $TOKEN" \
     -H "X-Claude-User-Agent: claude-word/1.0.0" \
     http://127.0.0.1:8080/bootstrap
```

## Security

- `DEV_JWKS_PATH` trusts a self-issued signing key instead of Microsoft's.
  It refuses to start unless bound to `127.0.0.1`. **Never** set it in a
  deployed environment.
- Do not hand-roll JWT verification beyond this — `jwt.decode` with
  `audience`/`issuer` plus the JWKS signature check is the boundary.
- If the manifest sets `entra_scope`, the bearer is an **access token**, not
  an ID token: set `AUDIENCE` to your API's Application ID URI
  (`api://<guid>`) and check the `scp` claim.
