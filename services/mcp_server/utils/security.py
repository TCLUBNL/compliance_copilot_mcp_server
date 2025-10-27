""" (utils/security.py) """
import re
import os
import hmac
import hashlib

PII_PATTERNS = [
    re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    re.compile(r"\+?\d[\d\-\s]{6,}\d"),
    re.compile(r"\b[A-Z]{2}\s*\d{8,}\b")
]

_SECRET_KEY = os.getenv("PII_HASH_KEY", "local-dev-key")

def redact_pii(text: str) -> str:
    if not text:
        return text
    out = text
    for pat in PII_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out

def hash_identifier(value: str) -> str:
    if not value:
        return ""
    key = (_SECRET_KEY or "default-key").encode("utf-8")
    return hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()
