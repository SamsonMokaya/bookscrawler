from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from app.config import settings
from app.tasks import (
    scrape_book,
    scrape_multiple_books,
    long_running_task,
    scheduled_book_scrape
)
from celery.result import AsyncResult
from app.celery_app import celery_app
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A book scraping API with Celery and Celery Beat"
)


# Pydantic models
class BookScrapeRequest(BaseModel):
    url: HttpUrl


class MultipleBooksRequest(BaseModel):
    urls: List[HttpUrl]


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Book Scraper API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        celery_app.backend.client.ping()
        return {
            "status": "healthy",
            "redis": "connected",
            "celery": "active"
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


@app.post("/scrape/book", response_model=TaskResponse)
async def trigger_book_scrape(request: BookScrapeRequest):
    """
    Trigger a book scraping task
    
    Args:
        request: BookScrapeRequest with URL to scrape
        
    Returns:
        TaskResponse with task_id
    """
    try:
        task = scrape_book.delay(str(request.url))
        return TaskResponse(
            task_id=task.id,
            status="pending",
            message=f"Scraping task created for {request.url}"
        )
    except Exception as e:
        logger.error(f"Error creating scraping task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape/books", response_model=TaskResponse)
async def trigger_multiple_books_scrape(request: MultipleBooksRequest):
    """
    Trigger scraping of multiple books
    
    Args:
        request: MultipleBooksRequest with list of URLs
        
    Returns:
        TaskResponse with task_id
    """
    try:
        urls = [str(url) for url in request.urls]
        task = scrape_multiple_books.delay(urls)
        return TaskResponse(
            task_id=task.id,
            status="pending",
            message=f"Scraping task created for {len(urls)} books"
        )
    except Exception as e:
        logger.error(f"Error creating multiple scraping tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of a Celery task
    
    Args:
        task_id: The ID of the task
        
    Returns:
        TaskStatusResponse with task status and result
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        response = TaskStatusResponse(
            task_id=task_id,
            status=task_result.status
        )
        
        if task_result.ready():
            if task_result.successful():
                response.result = task_result.result
            else:
                response.error = str(task_result.info)
        elif task_result.state == 'PROGRESS':
            response.result = task_result.info
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test/long-task")
async def trigger_long_task(duration: int = 10):
    """
    Trigger a long-running test task
    
    Args:
        duration: Duration in seconds (default: 10)
        
    Returns:
        TaskResponse with task_id
    """
    try:
        task = long_running_task.delay(duration)
        return TaskResponse(
            task_id=task.id,
            status="pending",
            message=f"Long-running task created for {duration} seconds"
        )
    except Exception as e:
        logger.error(f"Error creating long-running task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trigger/scheduled-scrape")
async def manual_trigger_scheduled_scrape():
    """
    Manually trigger the scheduled book scrape
    (This normally runs automatically via Celery Beat)
    """
    try:
        task = scheduled_book_scrape.delay()
        return TaskResponse(
            task_id=task.id,
            status="pending",
            message="Manually triggered scheduled scrape"
        )
    except Exception as e:
        logger.error(f"Error triggering scheduled scrape: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/celery/active-tasks")
async def get_active_tasks():
    """Get list of active Celery tasks"""
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()
        
        return {
            "active": active_tasks,
            "scheduled": scheduled_tasks
        }
    except Exception as e:
        logger.error(f"Error getting active tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/celery/stats")
async def get_celery_stats():
    """Get Celery worker statistics"""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        registered_tasks = inspect.registered()
        
        return {
            "stats": stats,
            "registered_tasks": registered_tasks
        }
    except Exception as e:
        logger.error(f"Error getting celery stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

