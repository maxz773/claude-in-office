"""
Claude in Office — Bootstrap endpoint (FastAPI + Postgres).

The Office add-in calls GET /bootstrap with the user's Entra ID token.
This server validates the token, loads that user's config from Postgres, and
returns it. The config blob is returned as-is — the add-in does {{...}}
template interpolation client-side, so this server never rewrites values.

All customer-editable settings live in config.py; the database schema lives
in schema.sql; the user lookup lives in store.py.
"""
import re
import time
from contextlib import asynccontextmanager

import jwt  # PyJWT
from config import (
    AUDIENCE,
    BOOTSTRAP_TTL_SECONDS,
    DATABASE_URL,
    DEV_JWKS_PATH,
    HOST,
    ISSUER,
    JWKS_URL,
    PORT,
)
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from jwt import PyJWKClient
from store import create_store

_UA_RE = re.compile(r"^claude-(word|excel|powerpoint)/", re.I)


def parse_app(user_agent: str | None) -> str:
    """Which Office host the add-in is running in: word | excel | powerpoint."""
    m = _UA_RE.match(user_agent or "")
    return m.group(1).lower() if m else ""


# ─── Token validation ─────────────────────────────────────────────────
_jwks = PyJWKClient(JWKS_URL) if not DEV_JWKS_PATH else None


def validate(auth_header: str) -> dict:
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = auth_header.removeprefix("Bearer ").strip()
    if DEV_JWKS_PATH:
        import json
        with open(DEV_JWKS_PATH) as f:
            key = jwt.PyJWK(json.load(f)["keys"][0]).key
    else:
        key = _jwks.get_signing_key_from_jwt(token).key
    try:
        # audience= and issuer= verify `aud` and `iss`; PyJWT also checks `exp`.
        return jwt.decode(
            token, key, algorithms=["RS256"], audience=AUDIENCE, issuer=ISSUER
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(401, f"Invalid token: {e}")


# ─── HTTP ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.store = await create_store(DATABASE_URL)
    yield
    await app.state.store.close()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pivot.claude.ai"],
    allow_methods=["GET"],
    allow_headers=["*"],  # FastAPI reflects the preflight's requested headers
)


@app.get("/bootstrap")
async def bootstrap(
    authorization: str = Header(None),
    x_claude_user_agent: str = Header(None),
):
    claims = validate(authorization)
    oid = claims.get("oid", "")
    if not oid:
        raise HTTPException(401, "Token missing oid claim")

    # `app` (word/excel/powerpoint) is available if you want per-host config.
    # The default store keys by oid only — pass it through to lookup_config
    # in store.py if you extend the schema with an app dimension.
    app_name = parse_app(x_claude_user_agent)

    config = await app.state.store.lookup_config(oid)

    if BOOTSTRAP_TTL_SECONDS > 0:
        config = {**config, "bootstrap_expires_at": int(time.time()) + BOOTSTRAP_TTL_SECONDS}
    return config


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
