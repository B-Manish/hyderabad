"""Redis caching layer for map viewport queries and cache invalidation."""
import json
import redis.asyncio as aioredis
from app.core.config import get_settings

settings = get_settings()

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return _redis_client


async def get_cached_map(key: str) -> dict | None:
    """Get cached map query result."""
    try:
        r = await get_redis()
        data = await r.get(key)
        if data:
            return json.loads(data)
    except Exception:
        pass  # Redis unavailable, skip cache
    return None


async def set_cached_map(key: str, value: dict, ttl: int = 60):
    """Cache map query result with TTL."""
    try:
        r = await get_redis()
        await r.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass  # Redis unavailable, skip cache


async def invalidate_map_cache():
    """Invalidate all map viewport caches. Called when issues are created/updated."""
    try:
        r = await get_redis()
        cursor = 0
        while True:
            cursor, keys = await r.scan(cursor, match="map:*", count=100)
            if keys:
                await r.delete(*keys)
            if cursor == 0:
                break
        # Also invalidate hotspot and stats caches
        for pattern in ["hotspots:*", "public_stats"]:
            cursor = 0
            while True:
                cursor, keys = await r.scan(cursor, match=pattern, count=100)
                if keys:
                    await r.delete(*keys)
                if cursor == 0:
                    break
    except Exception:
        pass  # Redis unavailable, skip invalidation
