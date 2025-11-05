from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.config import settings
from app.celery_app import celery_app
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A production-ready book scraping API with Celery and MongoDB"
)


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
    Verifies Redis/Celery connection
    """
    try:
        # Check Redis connection via Celery
        celery_app.backend.client.ping()
        
        return {
            "status": "healthy",
            "redis": "connected",
            "celery": "active",
            "api": "running"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
