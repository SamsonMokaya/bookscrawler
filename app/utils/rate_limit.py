"""
Rate limiting utilities using Redis
"""
import time
from fastapi import HTTPException, status, Response
from redis import Redis
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Redis client instance (created lazily)
_redis_client = None


def get_redis_client() -> Redis:
    """Get or create Redis client (lazy initialization)"""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.redis_url,  # Uses property for test/prod switching
            decode_responses=True
        )
    return _redis_client


def reset_redis_client():
    """Reset Redis client (for testing)"""
    global _redis_client
    if _redis_client:
        try:
            _redis_client.close()
        except:
            pass
    _redis_client = None


async def check_rate_limit(api_key: str, response: Response) -> None:
    """
    Check if API key has exceeded rate limit
    
    Args:
        api_key: The API key to check
        response: FastAPI Response object to add headers
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    try:
        redis = get_redis_client()
        
        # Create Redis key for this API key
        redis_key = f"rate_limit:{api_key}"
        
        # Atomic rate limit check using Lua script
        # This ensures check-and-increment is atomic (prevents race conditions)
        lua_script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        
        local current = redis.call('GET', key)
        
        -- Check if limit exceeded
        if current and tonumber(current) >= limit then
            local ttl = redis.call('TTL', key)
            return {tonumber(current), ttl, 0}
        end
        
        -- Increment counter
        local count = redis.call('INCR', key)
        
        -- Set expiry on first request
        if count == 1 then
            redis.call('EXPIRE', key, window)
        end
        
        local ttl = redis.call('TTL', key)
        return {count, ttl, 1}
        """
        
        # Execute atomic operation
        result = redis.eval(
            lua_script,
            1,  # Number of keys
            redis_key,
            settings.RATE_LIMIT_REQUESTS,
            settings.RATE_LIMIT_WINDOW
        )
        
        current_count, ttl, allowed = result
        
        # Calculate remaining requests
        remaining = max(0, settings.RATE_LIMIT_REQUESTS - current_count)
        reset_time = int(time.time()) + (ttl if ttl > 0 else settings.RATE_LIMIT_WINDOW)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        # Check if request was allowed
        if not allowed:
            logger.warning(f"Rate limit exceeded for API key: {api_key[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {ttl} seconds.",
                headers={
                    "Retry-After": str(ttl),
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_REQUESTS),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time)
                }
            )
        
        logger.debug(f"Rate limit check passed: {remaining}/{settings.RATE_LIMIT_REQUESTS} remaining")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        # On error, allow request (fail open)
        pass


def reset_rate_limit(api_key: str) -> bool:
    """
    Reset rate limit for a specific API key (admin function)
    
    Args:
        api_key: API key to reset
        
    Returns:
        True if reset successful
    """
    try:
        redis = get_redis_client()
        redis_key = f"rate_limit:{api_key}"
        redis.delete(redis_key)
        logger.info(f"Rate limit reset for API key: {api_key[:8]}...")
        return True
    except Exception as e:
        logger.error(f"Failed to reset rate limit: {e}")
        return False


def get_rate_limit_status(api_key: str) -> dict:
    """
    Get current rate limit status for API key
    
    Args:
        api_key: API key to check
        
    Returns:
        Dictionary with limit, remaining, and reset time
    """
    try:
        redis = get_redis_client()
        redis_key = f"rate_limit:{api_key}"
        current_count = redis.get(redis_key)
        
        if current_count is None:
            return {
                "limit": settings.RATE_LIMIT_REQUESTS,
                "remaining": settings.RATE_LIMIT_REQUESTS,
                "reset_in_seconds": settings.RATE_LIMIT_WINDOW
            }
        
        current_count = int(current_count)
        ttl = redis.ttl(redis_key)
        remaining = max(0, settings.RATE_LIMIT_REQUESTS - current_count)
        
        return {
            "limit": settings.RATE_LIMIT_REQUESTS,
            "remaining": remaining,
            "reset_in_seconds": ttl
        }
    except Exception as e:
        logger.error(f"Failed to get rate limit status: {e}")
        return {
            "limit": settings.RATE_LIMIT_REQUESTS,
            "remaining": settings.RATE_LIMIT_REQUESTS,
            "reset_in_seconds": settings.RATE_LIMIT_WINDOW
        }
