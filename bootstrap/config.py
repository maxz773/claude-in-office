"""
Edit this file to configure your bootstrap server. app.py should not need changes.
"""
import os

# ─── Entra / JWT ──────────────────────────────────────────────────────
TENANT_ID = os.environ["TENANT_ID"]                         # your Entra tenant

# ID-token mode (entra_sso=1 with no entra_scope): the audience is the
# add-in's client app id. If you set entra_scope in the manifest, the Bearer
# becomes an ACCESS token — set AUDIENCE to your API's Application ID URI
# (api://<guid>) instead. iss/exp/oid/signature checks are unchanged.
AUDIENCE = os.getenv("AUDIENCE", "c2995f31-11e7-4882-b7a7-ef9def0a0266")
ISSUER   = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8080"))

# ─── Postgres ─────────────────────────────────────────────────────────
# postgresql://user:password@host:port/database
DATABASE_URL = os.environ["DATABASE_URL"]

# ─── Response tuning ──────────────────────────────────────────────────
# Seconds before the add-in re-fetches. 0 (default) omits
# bootstrap_expires_at, so the config lives until the taskpane reloads.
# Set it when you're vending short-lived tokens (e.g. 300).
BOOTSTRAP_TTL_SECONDS = int(os.getenv("BOOTSTRAP_TTL_SECONDS", "0"))

# Local-dev override: point at a self-issued JWKS instead of Entra.
# Signature verification still runs. Refuses to start on non-loopback.
DEV_JWKS_PATH = os.getenv("DEV_JWKS_PATH")
if DEV_JWKS_PATH and HOST != "127.0.0.1":
    raise SystemExit("DEV_JWKS_PATH may only be used when HOST=127.0.0.1")
