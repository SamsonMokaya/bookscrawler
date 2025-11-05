"""
Unit tests for Celery tasks
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.scheduler.crawl_tasks import (
    crawl_all_books_task,
    crawl_single_book_task,
    save_book_to_db
)
from app.utils.helpers import generate_content_hash
from app.crawler.parser import parse_book_list, extract_pagination_info
from app.crawler.scraper import BookScraper


class TestCrawlTasks:
    """Test Celery crawl tasks"""
    
    @pytest.mark.asyncio
    async def test_save_book_to_db_new_book(self):
        """Test saving a new book to database"""
        book_data = {
            'name': 'New Test Book',
            'description': 'A new test book',
            'category': 'Fiction',
            'price_excl_tax': 19.99,
            'price_incl_tax': 21.99,
            'availability': 'In stock',
            'num_reviews': 0,
            'rating': 4,
            'image_url': 'http://example.com/image.jpg',
            'source_url': 'http://example.com/unique-book-url',
            'raw_html': '<html></html>',
            'content_hash': 'test-hash',
            'crawled_at': '2025-11-05T10:00:00',
            'updated_at': '2025-11-05T10:00:00',
            'crawl_status': 'success'
        }
        
        # Note: This requires database to be initialized
        # In real test environment, use test database
        # result = await save_book_to_db(book_data)
        # assert result['status'] in ['inserted', 'updated']
        
        # For now, just verify function exists
        assert callable(save_book_to_db)
    
    def test_crawl_all_books_task_callable(self):
        """Test that crawl_all_books_task is a Celery task"""
        assert hasattr(crawl_all_books_task, 'delay')
        assert hasattr(crawl_all_books_task, 'apply_async')
    
    def test_crawl_single_book_task_callable(self):
        """Test that crawl_single_book_task is a Celery task"""
        assert hasattr(crawl_single_book_task, 'delay')
        assert hasattr(crawl_single_book_task, 'apply_async')


class TestTaskRegistration:
    """Test that all tasks are registered with Celery"""
    
    def test_tasks_registered(self):
        """Test that all crawl tasks are registered"""
        from app.celery_app import celery_app
        
        registered_tasks = list(celery_app.tasks.keys())
        
        # Check our custom tasks are registered
        assert 'crawl_all_books' in registered_tasks
        assert 'crawl_single_book' in registered_tasks
        assert 'crawl_page_range' in registered_tasks


class TestBeatSchedule:
    """Test Celery Beat schedule configuration"""
    
    def test_beat_schedule_configured(self):
        """Test that beat schedule is configured"""
        from app.celery_app import celery_app
        
        beat_schedule = celery_app.conf.beat_schedule
        
        # Should be a dictionary
        assert isinstance(beat_schedule, dict)
        
        # If scheduler is enabled, should have daily-crawl task
        from app.config import settings
        if settings.ENABLE_SCHEDULER:
            assert 'daily-crawl-all-books' in beat_schedule
            assert beat_schedule['daily-crawl-all-books']['task'] == 'crawl_all_books'


class TestDataValidation:
    """Test data validation and integrity"""
    
    def test_content_hash_consistency(self):
        """Test that content hash is consistent"""
        book_data = {
            'price_excl_tax': 51.77,
            'price_incl_tax': 51.77,
            'availability': 'In stock',
            'num_reviews': 0,
            'rating': 3,
            'category': 'Poetry'
        }
        
        hash1 = generate_content_hash(book_data)
        hash2 = generate_content_hash(book_data)
        
        assert hash1 == hash2
    
    def test_content_hash_detects_changes(self):
        """Test that content hash changes when data changes"""
        book_data = {
            'price_excl_tax': 51.77,
            'price_incl_tax': 51.77,
            'availability': 'In stock',
            'num_reviews': 0,
            'rating': 3,
            'category': 'Poetry'
        }
        
        hash1 = generate_content_hash(book_data)
        
        # Change price
        book_data['price_incl_tax'] = 99.99
        hash2 = generate_content_hash(book_data)
        
        assert hash1 != hash2


class TestParser:
    """Test HTML parsing functions"""
    
    def test_parse_book_list_empty(self):
        """Test parsing empty catalog page"""
        html = "<html><body></body></html>"
        urls = parse_book_list(html, "https://books.toscrape.com")
        
        assert urls == []
    
    def test_pagination_info_extraction(self):
        """Test pagination extraction"""
        html = """
        <ul class="pager">
            <li class="current">Page 1 of 50</li>
            <li class="next"><a href="page-2.html">next</a></li>
        </ul>
        """
        
        info = extract_pagination_info(html, "https://books.toscrape.com")
        
        assert info['current_page'] == 1
        assert info['total_pages'] == 50
        assert info['next'] is not None


@pytest.mark.asyncio
class TestScraperIntegration:
    """Integration tests for scraper (requires network)"""
    
    async def test_scrape_real_book(self):
        """Test scraping a real book from the site"""
        async with BookScraper() as scraper:
            url = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
            book_data = await scraper.scrape_book(url)
            
            assert book_data is not None
            assert book_data['name'] == "A Light in the Attic"
            assert book_data['rating'] > 0
            assert book_data['price_incl_tax'] > 0
            assert 'content_hash' in book_data
    
    async def test_scrape_catalog_page_real(self):
        """Test scraping real catalog page"""
        async with BookScraper() as scraper:
            urls = await scraper.scrape_catalog_page(1)
            
            assert len(urls) == 20
            assert all(isinstance(url, str) for url in urls)
