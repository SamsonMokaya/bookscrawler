"""
Rate limiting utilities using Redis
"""
import time
from fastapi import HTTPException, status, Response
from redis import Redis
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create Redis client
redis_client = Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)


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
        # Create Redis key for this API key
        redis_key = f"rate_limit:{api_key}"
        
        # Get current count
        current_count = redis_client.get(redis_key)
        
        if current_count is None:
            # First request in this window
            redis_client.setex(
                redis_key,
                settings.RATE_LIMIT_WINDOW,  # seconds
                1
            )
            remaining = settings.RATE_LIMIT_REQUESTS - 1
            ttl = settings.RATE_LIMIT_WINDOW
        else:
            current_count = int(current_count)
            
            if current_count >= settings.RATE_LIMIT_REQUESTS:
                # Rate limit exceeded
                ttl = redis_client.ttl(redis_key)
                reset_time = int(time.time()) + ttl
                
                logger.warning(f"Rate limit exceeded for API key: {api_key[:8]}...")
                
                # Add rate limit headers
                response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
                response.headers["X-RateLimit-Remaining"] = "0"
                response.headers["X-RateLimit-Reset"] = str(reset_time)
                
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
            
            # Increment counter
            redis_client.incr(redis_key)
            remaining = settings.RATE_LIMIT_REQUESTS - current_count - 1
            ttl = redis_client.ttl(redis_key)
        
        # Add rate limit headers to response
        reset_time = int(time.time()) + ttl
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
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
        redis_key = f"rate_limit:{api_key}"
        redis_client.delete(redis_key)
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
        redis_key = f"rate_limit:{api_key}"
        current_count = redis_client.get(redis_key)
        
        if current_count is None:
            return {
                "limit": settings.RATE_LIMIT_REQUESTS,
                "remaining": settings.RATE_LIMIT_REQUESTS,
                "reset_in_seconds": settings.RATE_LIMIT_WINDOW
            }
        
        current_count = int(current_count)
        ttl = redis_client.ttl(redis_key)
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
