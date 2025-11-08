"""
Celery tasks for web crawling with transaction support
"""
import asyncio
import logging
from typing import Dict, List
from datetime import datetime
import redis

from app.celery_app import celery_app
from app.crawler.scraper import BookScraper
from app.models import Book, ChangeLog
from app.database.mongo import init_db, get_db_client
from app.utils.change_detection import detect_changes, save_changes_to_log
from app.utils.rate_limit import get_redis_client
from app.utils.email import send_new_books_alert, send_book_changes_alert
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)


async def save_book_to_db(book_data: Dict) -> Dict[str, any]:
    """
    Save or update a book in the database with change detection using transactions
    
    Ensures atomic operation: book + changelog are saved together or not at all
    
    Args:
        book_data: Dictionary with book information
        
    Returns:
        Dictionary with operation result and changes detected
    """
    try:
        # Get MongoDB client for transaction
        client = get_db_client()
        
        # Start a transaction session
        async with await client.start_session() as session:
            async with session.start_transaction():
                # Check if book already exists
                existing_book = await Book.find_one(
                    Book.source_url == book_data['source_url'],
                    session=session
                )
                
                if existing_book:
                    # Detect changes before updating
                    changes = await detect_changes(existing_book, book_data)
                    
                    # Update existing book
                    for key, value in book_data.items():
                        if key not in ['_id', 'crawled_at']:  # Preserve original crawl date
                            setattr(existing_book, key, value)
                    
                    existing_book.updated_at = datetime.utcnow()
                    await existing_book.save(session=session)
                    
                    # Save changes to ChangeLog
                    changes_saved = 0
                    if changes:
                        changes_saved = await save_changes_to_log(changes, session=session)
                        
                        # Enhanced logging for significant changes
                        change_summary = []
                        for change in changes:
                            field = change.get('field_changed')
                            old_val = change.get('old_value')
                            new_val = change.get('new_value')
                            change_summary.append(f"{field}: {old_val} -> {new_val}")
                        
                        logger.info(f"CHANGE DETECTED and updated: '{book_data['name']}' - {', '.join(change_summary)} ({changes_saved} changes logged)")
                   
                    # Transaction commits automatically here
                    return {
                        'status': 'updated',
                        'book_id': str(existing_book.id),
                        'changes_detected': len(changes),
                        'changes_saved': changes_saved,
                        'change_details': changes  # Return actual change data for email
                    }
                else:
                    # Create new book
                    book = Book(**book_data)
                    await book.insert(session=session)
                    
                    # Log as new book in ChangeLog
                    new_book_log = ChangeLog(
                        book_id=str(book.id),  # Convert ObjectId to string
                        book_name=book.name,
                        changed_at=datetime.utcnow(),
                        change_type='new_book',
                        description=f"New book added: {book.name} in category {book.category}"
                    )
                    await new_book_log.insert(session=session)
                    
                    # Enhanced logging for new books
                    logger.info(f"NEW BOOK DETECTED and inserted: '{book_data['name']}' in category '{book_data['category']}' - £{book_data['price_incl_tax']}")
                    
                    # Transaction commits automatically here
                    return {
                        'status': 'inserted',
                        'book_id': str(book.id),
                        'book_data': book_data,  # Return book data for email
                        'changes_detected': 0,
                        'changes_saved': 1
                    }
            
    except DuplicateKeyError:
        logger.warning(f"Duplicate book found: {book_data.get('source_url')}")
        return {'status': 'duplicate', 'book_id': None, 'changes_detected': 0}
    except Exception as e:
        logger.error(f"Error saving book {book_data.get('name')}: {e}", exc_info=True)
        return {'status': 'error', 'error': str(e), 'changes_detected': 0}


async def async_crawl_all_books(start_page: int = 1, end_page: int = None) -> Dict:
    """
    Async function to crawl all books and save to database
    
    Args:
        start_page: Starting page number
        end_page: Ending page number (None = all pages)
        
    Returns:
        Summary dictionary with statistics
    """
    summary = {
        'total_scraped': 0,
        'inserted': 0,
        'updated': 0,
        'failed': 0,
        'duplicates': 0,
        'total_changes_detected': 0,
        'total_changes_logged': 0,
        'start_time': datetime.utcnow().isoformat(),
        'end_time': None,
        'duration_seconds': 0
    }
    
    start_time = datetime.utcnow()
    
    try:
        # Initialize database connection
        await init_db()
        
        # Create scraper and crawl
        async with BookScraper() as scraper:
            books = await scraper.crawl_all_books(start_page, end_page)
            summary['total_scraped'] = len(books)
            
            logger.info(f"Scraped {len(books)} books, saving to database...")
            
            # Collect new books and changes for email notifications
            new_books_for_email = []
            all_changes_for_email = []
            
            # Save books to database
            for book_data in books:
                result = await save_book_to_db(book_data)
                
                if result['status'] == 'inserted':
                    summary['inserted'] += 1
                    summary['total_changes_logged'] += result.get('changes_saved', 0)
                    # Collect new book for email
                    if result.get('book_data'):
                        new_books_for_email.append(result['book_data'])
                        
                elif result['status'] == 'updated':
                    summary['updated'] += 1
                    summary['total_changes_detected'] += result.get('changes_detected', 0)
                    summary['total_changes_logged'] += result.get('changes_saved', 0)
                    # Collect changes for email
                    if result.get('change_details'):
                        all_changes_for_email.extend(result['change_details'])
                        
                elif result['status'] == 'duplicate':
                    summary['duplicates'] += 1
                else:
                    summary['failed'] += 1
            
            end_time = datetime.utcnow()
            summary['end_time'] = end_time.isoformat()
            summary['duration_seconds'] = (end_time - start_time).total_seconds()
            
            logger.info(f"Crawl completed: {summary}")
            
            # Send email notifications (fail-safe - won't crash if email fails)
            try:
                if new_books_for_email:
                    logger.info(f"Sending new books email notification ({len(new_books_for_email)} books)")
                    send_new_books_alert(new_books_for_email)
                
                if all_changes_for_email:
                    logger.info(f"Sending book changes email notification ({len(all_changes_for_email)} changes)")
                    send_book_changes_alert(all_changes_for_email)
            except Exception as e:
                logger.error(f"Error sending email notifications: {e}", exc_info=True)
                # Don't fail the crawl if email fails
            
            return summary
            
    except Exception as e:
        logger.error(f"Error in crawl task: {e}", exc_info=True)
        summary['error'] = str(e)
        summary['end_time'] = datetime.utcnow().isoformat()
        return summary


@celery_app.task(bind=True, name='crawl_all_books')
def crawl_all_books_task(self, start_page: int = 1, end_page: int = None):
    """
    Celery task to crawl all books from the website with Redis locking
    
    Uses Redis distributed lock to prevent multiple crawls running simultaneously
    This prevents resource waste and ensures data consistency
    
    Args:
        start_page: Starting page number (default 1)
        end_page: Ending page number (default None = all pages)
        
    Returns:
        Summary dictionary with crawl statistics
    """
    logger.info(f"Starting crawl task: pages {start_page} to {end_page or 'end'}")
    
    # Acquire Redis lock to prevent multiple crawls
    redis_client = get_redis_client()
    lock_key = "lock:crawl_all_books"
    lock_timeout = 3600 * 6  # 6 hours max crawl time
    
    # Try to acquire lock
    lock = redis_client.lock(lock_key, timeout=lock_timeout, blocking=False)
    
    if not lock.acquire(blocking=False):
        logger.warning("Another crawl is already running. Skipping this task.")
        return {
            'status': 'skipped',
            'reason': 'Another crawl task is already in progress',
            'start_page': start_page,
            'end_page': end_page
        }
    
    try:
        logger.info("Crawl lock acquired. Starting crawl...")
        
        # Run async function in event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create new loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        summary = loop.run_until_complete(async_crawl_all_books(start_page, end_page))
        
        logger.info(f"Crawl task completed: {summary}")
        return summary
        
    except Exception as e:
        logger.error(f"Error in crawl task: {e}", exc_info=True)
        raise
    finally:
        # Always release lock
        try:
            lock.release()
            logger.info("Crawl lock released")
        except redis.exceptions.LockError:
            logger.warning("Lock was already released or expired")


@celery_app.task(bind=True, name='crawl_single_book')
def crawl_single_book_task(self, url: str):
    """
    Celery task to crawl a single book
    
    Args:
        url: URL of the book to crawl
        
    Returns:
        Book data or error message
    """
    logger.info(f"Starting single book crawl: {url}")
    
    async def async_crawl_single():
        await init_db()
        async with BookScraper() as scraper:
            book_data = await scraper.scrape_book(url)
            if book_data:
                result = await save_book_to_db(book_data)
                return {'book_data': book_data, 'db_result': result}
            return {'error': 'Failed to scrape book'}
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(async_crawl_single())
        logger.info(f"Single book crawl completed: {result.get('db_result', {}).get('status')}")
        return result
        
    except Exception as e:
        logger.error(f"Error crawling single book {url}: {e}", exc_info=True)
        return {'error': str(e)}


@celery_app.task(bind=True, name='crawl_page_range')
def crawl_page_range_task(self, start_page: int, end_page: int):
    """
    Celery task to crawl a specific range of pages
    Useful for distributed crawling
    
    Args:
        start_page: Starting page number
        end_page: Ending page number
        
    Returns:
        Summary dictionary
    """
    logger.info(f"Starting page range crawl: {start_page} to {end_page}")
    return crawl_all_books_task(start_page, end_page)
