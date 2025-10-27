""" (auth.py) """
import os
import hmac
from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED

API_KEY_HEADER = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)

def _load_allowed_keys() -> set:
    raw = os.getenv("API_KEYS_ALLOWED", "")
    if not raw:
        return set()
    return set([k.strip() for k in raw.split(",") if k.strip()])

ALLOWED_KEYS = _load_allowed_keys()

def verify_api_key(api_key: str) -> bool:
    if not api_key:
        return False
    for allowed in ALLOWED_KEYS:
        if hmac.compare_digest(allowed, api_key):
            return True
    return False

async def require_api_key(api_key: str = Security(api_key_header)):
    if not api_key or not verify_api_key(api_key):
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    return api_key
