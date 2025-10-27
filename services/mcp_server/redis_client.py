""" (redis_client.py) """
import os
import logging
try:
    import aioredis
except Exception:
    aioredis = None

logger = logging.getLogger("redis_client")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

_redis = None

async def get_redis():
    global _redis
    if _redis:
        return _redis
    if not aioredis:
        logger.debug("aioredis not installed; returning None")
        return None
    try:
        if REDIS_PASSWORD:
            _redis = await aioredis.from_url(REDIS_URL, password=REDIS_PASSWORD, decode_responses=True)
        else:
            _redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
        return _redis
    except Exception as e:
        logger.warning("Failed to connect to Redis: %s", e)
        _redis = None
        return None
