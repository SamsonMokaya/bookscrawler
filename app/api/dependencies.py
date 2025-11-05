"""
FastAPI dependencies for authentication and rate limiting
"""
from fastapi import Depends, Response
from typing import Annotated

from app.utils.auth import verify_api_key
from app.utils.rate_limit import check_rate_limit


async def get_api_key_with_rate_limit(
    api_key: Annotated[str, Depends(verify_api_key)],
    response: Response
) -> str:
    """
    Combined dependency for API key authentication and rate limiting
    
    Args:
        api_key: Verified API key from authentication
        response: FastAPI response object
        
    Returns:
        The verified API key
        
    Raises:
        HTTPException: If authentication or rate limit fails
    """
    # Check rate limit
    await check_rate_limit(api_key, response)
    
    return api_key


# Type alias for cleaner endpoint signatures
APIKey = Annotated[str, Depends(get_api_key_with_rate_limit)]

