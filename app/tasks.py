from celery import Task
from app.celery_app import celery_app
import time
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task with callbacks"""
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {task_id} succeeded with result: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed with error: {exc}")


@celery_app.task(base=CallbackTask, bind=True, name='app.tasks.scrape_book')
def scrape_book(self, url: str) -> dict:
    """
    Scrape a single book from the given URL
    
    Args:
        url: The URL to scrape
        
    Returns:
        dict: Scraped book information
    """
    try:
        logger.info(f"Starting to scrape book from: {url}")
        
        # Simulate scraping with a delay
        time.sleep(2)
        
        # In a real scenario, you'd use requests and BeautifulSoup here
        # Example:
        # response = requests.get(url)
        # soup = BeautifulSoup(response.content, 'html.parser')
        # title = soup.find('h1', class_='book-title').text
        
        result = {
            'url': url,
            'title': f'Book from {url}',
            'scraped_at': datetime.utcnow().isoformat(),
            'task_id': self.request.id,
            'status': 'success'
        }
        
        logger.info(f"Successfully scraped book: {result['title']}")
        return result
        
    except Exception as e:
        logger.error(f"Error scraping book from {url}: {str(e)}")
        raise


@celery_app.task(base=CallbackTask, bind=True, name='app.tasks.scrape_multiple_books')
def scrape_multiple_books(self, urls: list) -> dict:
    """
    Scrape multiple books from a list of URLs
    
    Args:
        urls: List of URLs to scrape
        
    Returns:
        dict: Results summary
    """
    try:
        logger.info(f"Starting to scrape {len(urls)} books")
        
        results = []
        for url in urls:
            result = scrape_book.delay(url)
            results.append(result.id)
        
        return {
            'total_urls': len(urls),
            'task_ids': results,
            'status': 'dispatched',
            'message': f'Dispatched {len(results)} scraping tasks'
        }
        
    except Exception as e:
        logger.error(f"Error in scrape_multiple_books: {str(e)}")
        raise


@celery_app.task(name='app.tasks.scheduled_book_scrape')
def scheduled_book_scrape():
    """
    Scheduled task that runs periodically to scrape books
    This is triggered by Celery Beat
    """
    logger.info("Running scheduled book scrape")
    
    # Example URLs - in production, you'd get these from a database
    sample_urls = [
        'https://example.com/book1',
        'https://example.com/book2',
        'https://example.com/book3',
    ]
    
    result = scrape_multiple_books.delay(sample_urls)
    
    return {
        'scheduled_at': datetime.utcnow().isoformat(),
        'task_id': result.id,
        'message': 'Scheduled scrape initiated'
    }


@celery_app.task(name='app.tasks.cleanup_old_data')
def cleanup_old_data():
    """
    Scheduled task to cleanup old data
    Runs daily at 2:00 AM
    """
    logger.info("Running cleanup of old data")
    
    # Implement your cleanup logic here
    # For example, delete old scraping results, clear cache, etc.
    
    time.sleep(1)  # Simulate cleanup work
    
    return {
        'cleaned_at': datetime.utcnow().isoformat(),
        'status': 'success',
        'message': 'Old data cleaned up successfully'
    }


@celery_app.task(name='app.tasks.health_check')
def health_check():
    """
    Health check task that runs every 5 minutes
    """
    logger.info("Running health check")
    
    return {
        'checked_at': datetime.utcnow().isoformat(),
        'status': 'healthy',
        'message': 'All systems operational'
    }


@celery_app.task(bind=True, name='app.tasks.long_running_task')
def long_running_task(self, duration: int = 10):
    """
    Example of a long-running task with progress updates
    
    Args:
        duration: Duration in seconds
    """
    logger.info(f"Starting long-running task for {duration} seconds")
    
    for i in range(duration):
        time.sleep(1)
        # Update task state to show progress
        self.update_state(
            state='PROGRESS',
            meta={
                'current': i + 1,
                'total': duration,
                'status': f'Processing... {i + 1}/{duration}'
            }
        )
    
    return {
        'status': 'completed',
        'duration': duration,
        'completed_at': datetime.utcnow().isoformat()
    }

