"""
API Key authentication utilities
"""
from fastapi import Header, HTTPException, status
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Verify API key from request headers
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        The valid API key
        
    Raises:
        HTTPException: If API key is invalid, missing, or blocked
    """
    if not x_api_key:
        logger.warning("API request without API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include 'X-API-Key' header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    # Check if API key is blocked
    if x_api_key in settings.blocked_api_keys:
        logger.warning(f"Blocked API key attempted access: {x_api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is blocked. Contact support."
        )
    
    # Check if API key is valid
    if x_api_key not in settings.valid_api_keys:
        logger.warning(f"Invalid API key attempted access: {x_api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key. Check your credentials.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    logger.debug(f"Valid API key: {x_api_key[:8]}...")
    return x_api_key


def is_api_key_valid(api_key: str) -> bool:
    """
    Check if API key is valid without raising exceptions
    
    Args:
        api_key: API key to check
        
    Returns:
        True if valid, False otherwise
    """
    if not api_key:
        return False
    
    if api_key in settings.blocked_api_keys:
        return False
    
    return api_key in settings.valid_api_keys
