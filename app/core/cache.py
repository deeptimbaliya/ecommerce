import redis.asyncio as aioredis
import json
from typing import Any, Optional
from app.core.config import settings
from app.core.logger import setup_logger

logger = setup_logger(__name__)

# Redis client — async version for FastAPI
redis_client = aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True    # returns strings not bytes
)

class CacheTTL:
    SHORT = 60          # 1 minute  — frequently changing data
    MEDIUM = 300        # 5 minutes — semi-stable data
    LONG = 3600         # 1 hour    — stable data
    VERY_LONG = 86400   # 1 day     — rarely changing data


async def get_cache(key: str) -> Optional[Any]:
    """Get value from cache. Returns None if not found."""
    try:
        value = await redis_client.get(key)
        if value:
            logger.debug(f"Cache HIT: {key}")
            return json.loads(value)
        logger.debug(f"Cache MISS: {key}")
        return None
    except Exception as e:
        logger.warning(f"Cache GET failed for {key}: {e}")
        return None   # fail silently — cache errors shouldn't break your app


async def set_cache(key: str, value: Any, ttl: int = 300) -> None:
    """Store value in cache with TTL in seconds."""
    try:
        await redis_client.setex(
            key,
            ttl,
            json.dumps(value, default=str)   # default=str handles datetime etc.
        )
        logger.debug(f"Cache SET: {key} (TTL={ttl}s)")
    except Exception as e:
        logger.warning(f"Cache SET failed for {key}: {e}")


async def delete_cache(key: str) -> None:
    """Delete a specific cache key."""
    try:
        await redis_client.delete(key)
        logger.debug(f"Cache DELETE: {key}")
    except Exception as e:
        logger.warning(f"Cache DELETE failed for {key}: {e}")


async def delete_pattern(pattern: str) -> None:
    """Delete all keys matching a pattern. e.g. 'users:*' """
    try:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
            logger.debug(f"Cache DELETE pattern: {pattern} ({len(keys)} keys)")
    except Exception as e:
        logger.warning(f"Cache DELETE pattern failed: {e}")