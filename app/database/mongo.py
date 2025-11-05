"""
MongoDB connection and initialization using Beanie ODM
"""
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.models import Book, ChangeLog
from app.config import settings

logger = logging.getLogger(__name__)

# Global MongoDB client instance
_mongodb_client: Optional[AsyncIOMotorClient] = None


async def init_db():
    """
    Initialize MongoDB connection and Beanie ODM
    
    This should be called during FastAPI startup
    """
    global _mongodb_client
    
    try:
        logger.info(f"Connecting to MongoDB at: {settings.MONGODB_URL}")
        
        # Create Motor client
        _mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
        
        # Get database
        database = _mongodb_client[settings.MONGODB_DB_NAME]
        
        # Initialize Beanie with document models
        await init_beanie(
            database=database,
            document_models=[Book, ChangeLog]
        )
        
        logger.info(f"Successfully connected to MongoDB database: {settings.MONGODB_DB_NAME}")
        logger.info("Beanie ODM initialized with models: Book, ChangeLog")
        
        # Test connection
        await database.command("ping")
        logger.info("MongoDB ping successful")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_db():
    """
    Close MongoDB connection
    
    This should be called during FastAPI shutdown
    """
    global _mongodb_client
    
    if _mongodb_client:
        try:
            _mongodb_client.close()
            logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
            raise
    else:
        logger.warning("No active MongoDB connection to close")


def get_db_client() -> Optional[AsyncIOMotorClient]:
    """
    Get the current MongoDB client instance
    
    Returns:
        AsyncIOMotorClient or None if not initialized
    """
    return _mongodb_client
