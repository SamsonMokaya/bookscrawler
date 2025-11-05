"""
Async web scraper with retry logic and rate limiting
"""
import asyncio
from typing import List, Dict, Optional
import httpx
import logging
from datetime import datetime

from app.config import settings
from app.crawler.parser import parse_book_detail, parse_book_list, extract_pagination_info
from app.utils.helpers import generate_content_hash, normalize_url

logger = logging.getLogger(__name__)


class BookScraper:
    """
    Asynchronous book scraper with retry logic and rate limiting
    """
    
    def __init__(self):
        self.base_url = settings.TARGET_URL
        self.delay = settings.CRAWLER_DELAY
        self.max_retries = settings.CRAWLER_MAX_RETRIES
        self.timeout = settings.CRAWLER_TIMEOUT
        self.max_concurrent = settings.CRAWLER_CONCURRENT_REQUESTS
        
        # Create async HTTP client
        self.client = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; BookScraperBot/1.0)'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()
    
    async def fetch_page(self, url: str, retry_count: int = 0) -> Optional[str]:
        """
        Fetch a page with retry logic and exponential backoff
        
        Args:
            url: URL to fetch
            retry_count: Current retry attempt
            
        Returns:
            HTML content or None if all retries fail
        """
        try:
            logger.debug(f"Fetching: {url} (attempt {retry_count + 1})")
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Add delay to respect rate limits
            await asyncio.sleep(self.delay)
            
            return response.text
            
        except httpx.HTTPStatusError as e:
            # Handle specific HTTP errors
            if e.response.status_code == 429:  # Too Many Requests
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.warning(f"Rate limited on {url}, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
                
            elif e.response.status_code >= 500:  # Server errors
                logger.warning(f"Server error {e.response.status_code} on {url}")
            
            else:
                logger.error(f"HTTP error {e.response.status_code} on {url}")
                return None  # Don't retry client errors (4xx)
            
            # Retry logic
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count
                await asyncio.sleep(wait_time)
                return await self.fetch_page(url, retry_count + 1)
            else:
                logger.error(f"Max retries exceeded for {url}")
                return None
                
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching {url}")
            if retry_count < self.max_retries:
                return await self.fetch_page(url, retry_count + 1)
            return None
            
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}", exc_info=True)
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)
                return await self.fetch_page(url, retry_count + 1)
            return None
    
    async def scrape_book(self, url: str) -> Optional[Dict]:
        """
        Scrape a single book detail page
        
        Args:
            url: Book detail page URL
            
        Returns:
            Book data dictionary or None if scraping fails
        """
        html = await self.fetch_page(url)
        if not html:
            return None
        
        book_data = parse_book_detail(html, url)
        if not book_data:
            return None
        
        # Generate content hash for change detection
        content_hash = generate_content_hash(book_data)
        book_data['content_hash'] = content_hash
        book_data['crawled_at'] = datetime.utcnow()
        book_data['updated_at'] = datetime.utcnow()
        book_data['crawl_status'] = 'success'
        
        return book_data
    
    async def scrape_catalog_page(self, page_num: int = 1) -> List[str]:
        """
        Scrape a catalog page and return book URLs
        
        Args:
            page_num: Page number (1-50)
            
        Returns:
            List of book URLs
        """
        if page_num == 1:
            url = self.base_url
        else:
            url = f"{self.base_url}/catalogue/page-{page_num}.html"
        
        html = await self.fetch_page(url)
        if not html:
            return []
        
        book_urls = parse_book_list(html, url)
        return book_urls
    
    async def get_total_pages(self) -> int:
        """
        Get total number of pages to scrape
        
        Returns:
            Total pages (default 50 if parsing fails)
        """
        html = await self.fetch_page(self.base_url)
        if not html:
            return 50  # Default fallback
        
        pagination_info = extract_pagination_info(html, self.base_url)
        return pagination_info.get('total_pages', 50)
    
    async def crawl_all_books(
        self,
        start_page: int = 1,
        end_page: Optional[int] = None
    ) -> List[Dict]:
        """
        Crawl all books from the website
        
        Args:
            start_page: Starting page number
            end_page: Ending page number (None = all pages)
            
        Returns:
            List of book data dictionaries
        """
        logger.info("Starting full site crawl...")
        
        # Get total pages
        total_pages = await self.get_total_pages()
        if end_page is None:
            end_page = total_pages
        
        logger.info(f"Will crawl pages {start_page} to {end_page}")
        
        all_books = []
        
        # Step 1: Collect all book URLs from catalog pages
        all_book_urls = []
        for page_num in range(start_page, end_page + 1):
            logger.info(f"Fetching catalog page {page_num}/{end_page}")
            book_urls = await self.scrape_catalog_page(page_num)
            all_book_urls.extend(book_urls)
        
        logger.info(f"Found {len(all_book_urls)} books to scrape")
        
        # Step 2: Scrape book details concurrently (with limit)
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def scrape_with_semaphore(url: str) -> Optional[Dict]:
            async with semaphore:
                return await self.scrape_book(url)
        
        # Process books in batches
        batch_size = 50
        for i in range(0, len(all_book_urls), batch_size):
            batch_urls = all_book_urls[i:i + batch_size]
            logger.info(f"Scraping batch {i//batch_size + 1} ({len(batch_urls)} books)")
            
            tasks = [scrape_with_semaphore(url) for url in batch_urls]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out None and exceptions
            for result in batch_results:
                if isinstance(result, dict):
                    all_books.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Exception in batch: {result}")
            
            logger.info(f"Progress: {len(all_books)}/{len(all_book_urls)} books scraped")
        
        logger.info(f"Crawl complete! Scraped {len(all_books)} books successfully")
        return all_books
