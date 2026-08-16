# app/services/cache.py
import json
import redis.asyncio as redis
from app.core.config import get_settings

_pool = redis.from_url(get_settings().redis_url, decode_responses=True)

async def cache_get(key: str):
    raw = await _pool.get(key)
    return json.loads(raw) if raw else None

async def cache_set(key: str, value, ttl_seconds: int = 300):
    await _pool.set(key, json.dumps(value), ex=ttl_seconds)



