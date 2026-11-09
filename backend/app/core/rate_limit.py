"""
Rate Limiter & Account Lockout Engine
Supports Redis-backed progressive lockout with in-memory fallback for local testing.
"""
import time
from typing import Optional, Tuple
import redis.asyncio as aioredis
from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger("mind.core.rate_limit")
_redis_client: Optional[aioredis.Redis] = None
_local_memory_cache: dict = {}


async def get_redis_client() -> Optional[aioredis.Redis]:
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=1.0,
            )
            await _redis_client.ping()
        except Exception as e:
            logger.debug(f"Redis not available for rate limiting ({e}). Using in-memory fallback.")
            _redis_client = None
    return _redis_client


class RateLimiter:
    @staticmethod
    async def check_login_lockout(email: str, client_ip: str, max_attempts: int = 5, window_seconds: int = 900) -> Tuple[bool, int]:
        """
        Checks if account or IP is locked out due to excessive failed login attempts.
        Returns (is_locked, seconds_remaining).
        """
        key = f"ratelimit:login:{email.lower().strip()}"
        redis = await get_redis_client()

        if redis:
            try:
                attempts = await redis.get(key)
                if attempts and int(attempts) >= max_attempts:
                    ttl = await redis.ttl(key)
                    return True, max(1, ttl)
                return False, 0
            except Exception as e:
                logger.warning(f"Redis lockout check failed ({e}).")

        # In-memory fallback
        now = time.time()
        record = _local_memory_cache.get(key)
        if record:
            attempts, expire_at = record
            if now < expire_at:
                if attempts >= max_attempts:
                    return True, int(expire_at - now)
            else:
                _local_memory_cache.pop(key, None)
        return False, 0

    @staticmethod
    async def record_login_failure(email: str, client_ip: str, window_seconds: int = 900) -> int:
        """Increments failed login counter with expiration window."""
        key = f"ratelimit:login:{email.lower().strip()}"
        redis = await get_redis_client()

        if redis:
            try:
                pipe = redis.pipeline()
                pipe.incr(key)
                pipe.expire(key, window_seconds)
                results = await pipe.execute()
                return int(results[0])
            except Exception as e:
                logger.warning(f"Redis failed to record login failure ({e}).")

        # In-memory fallback
        now = time.time()
        record = _local_memory_cache.get(key)
        if record and now < record[1]:
            count = record[0] + 1
            _local_memory_cache[key] = (count, record[1])
            return count
        else:
            _local_memory_cache[key] = (1, now + window_seconds)
            return 1

    @staticmethod
    async def reset_login_failures(email: str) -> None:
        """Clears failed login attempts upon successful authentication."""
        key = f"ratelimit:login:{email.lower().strip()}"
        redis = await get_redis_client()
        if redis:
            try:
                await redis.delete(key)
            except Exception:
                pass
        _local_memory_cache.pop(key, None)

    @staticmethod
    async def check_rate_limit(key: str, max_requests: int = 10, window_seconds: int = 60) -> Tuple[bool, int]:
        """Generic sliding window rate limiter."""
        redis = await get_redis_client()
        if redis:
            try:
                val = await redis.incr(key)
                if val == 1:
                    await redis.expire(key, window_seconds)
                if val > max_requests:
                    ttl = await redis.ttl(key)
                    return False, max(1, ttl)
                return True, 0
            except Exception:
                pass

        now = time.time()
        record = _local_memory_cache.get(key)
        if record and now < record[1]:
            val = record[0] + 1
            _local_memory_cache[key] = (val, record[1])
            if val > max_requests:
                return False, int(record[1] - now)
            return True, 0
        else:
            _local_memory_cache[key] = (1, now + window_seconds)
            return True, 0

