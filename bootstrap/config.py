"""
Edit this file to configure your bootstrap server. app.py should not need changes.
"""
import os
from pathlib import Path

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

# ─── Database ─────────────────────────────────────────────────────────
# Local debug runs on SQLite — the file is created on first start, so there
# is nothing to provision. Path resolves next to this file, not the cwd, so
# you get the same database wherever you launch from.
# To go back to Postgres, point this at postgresql://… and restore store.py
# from git (see the note at the top of store.py).
_DEFAULT_DB = Path(__file__).with_name("bootstrap.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_DEFAULT_DB.as_posix()}")

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
