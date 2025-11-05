from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.celery_app import celery_app
from app.database.mongo import init_db, close_db, get_db_client
from app.api import books, changes
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting Book Scraper API...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down Book Scraper API...")
    try:
        await close_db()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A production-ready book scraping API with Celery and MongoDB",
    lifespan=lifespan
)

# Include API routers
app.include_router(books.router)
app.include_router(changes.router)


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "message": "Welcome to Book Scraper API",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    Verifies Redis/Celery and MongoDB connections
    """
    health_status = {
        "status": "healthy",
        "api": "running",
        "redis": "unknown",
        "celery": "unknown",
        "mongodb": "unknown"
    }
    
    is_healthy = True
    
    # Check Redis/Celery
    try:
        celery_app.backend.client.ping()
        health_status["redis"] = "connected"
        health_status["celery"] = "active"
    except Exception as e:
        logger.error(f"Redis/Celery health check failed: {str(e)}")
        health_status["redis"] = "disconnected"
        health_status["celery"] = "inactive"
        is_healthy = False
    
    # Check MongoDB
    try:
        db_client = get_db_client()
        if db_client:
            await db_client[settings.mongodb_database_name].command("ping")
            health_status["mongodb"] = "connected"
        else:
            health_status["mongodb"] = "not_initialized"
            is_healthy = False
    except Exception as e:
        logger.error(f"MongoDB health check failed: {str(e)}")
        health_status["mongodb"] = "disconnected"
        is_healthy = False
    
    if not is_healthy:
        health_status["status"] = "unhealthy"
        return JSONResponse(
            status_code=503,
            content=health_status
        )
    
    return health_status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
