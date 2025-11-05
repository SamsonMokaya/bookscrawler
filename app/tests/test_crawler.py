"""
Unit tests for web crawler
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.crawler.parser import (
    parse_book_detail,
    parse_book_list,
    extract_pagination_info
)
from app.crawler.scraper import BookScraper
from app.utils.helpers import (
    parse_price,
    parse_rating,
    parse_availability,
    generate_content_hash,
    normalize_url
)


class TestHelpers:
    """Test utility helper functions"""
    
    def test_parse_price(self):
        """Test price parsing"""
        assert parse_price("£51.77") == 51.77
        assert parse_price("$99.99") == 99.99
        assert parse_price("51.77") == 51.77
        assert parse_price("invalid") is None
    
    def test_parse_rating(self):
        """Test rating extraction from CSS class"""
        assert parse_rating("star-rating One") == 1
        assert parse_rating("star-rating Three") == 3
        assert parse_rating("star-rating Five") == 5
        assert parse_rating("no-rating") == 0
    
    def test_parse_availability(self):
        """Test availability parsing"""
        status, qty = parse_availability("In stock (22 available)")
        assert status == "In stock"
        assert qty == 22
        
        status, qty = parse_availability("In stock")
        assert status == "In stock"
        assert qty == 0
    
    def test_generate_content_hash(self):
        """Test content hash generation"""
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
        
        # Same data should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hash length
        
        # Different data should produce different hash
        book_data['price_incl_tax'] = 99.99
        hash3 = generate_content_hash(book_data)
        assert hash1 != hash3
    
    def test_normalize_url(self):
        """Test URL normalization"""
        base = "https://books.toscrape.com"
        
        # Relative URL
        url = normalize_url("catalogue/page-2.html", base)
        assert url == "https://books.toscrape.com/catalogue/page-2.html"
        
        # Absolute URL
        url = normalize_url("https://example.com/test", base)
        assert url == "https://example.com/test"


class TestParser:
    """Test HTML parser functions"""
    
    def test_parse_book_list(self):
        """Test parsing book URLs from catalog page"""
        # Sample HTML with product pods
        html = """
        <html>
        <body>
            <article class="product_pod">
                <h3><a href="catalogue/test-book_1/index.html">Test Book</a></h3>
            </article>
            <article class="product_pod">
                <h3><a href="catalogue/another-book_2/index.html">Another Book</a></h3>
            </article>
        </body>
        </html>
        """
        
        urls = parse_book_list(html, "https://books.toscrape.com")
        assert len(urls) == 2
        assert "test-book_1" in urls[0]
        assert "another-book_2" in urls[1]
    
    def test_extract_pagination_info(self):
        """Test pagination info extraction"""
        html = """
        <html>
        <body>
            <ul class="pager">
                <li class="previous"><a href="page-1.html">previous</a></li>
                <li class="current">Page 2 of 50</li>
                <li class="next"><a href="page-3.html">next</a></li>
            </ul>
        </body>
        </html>
        """
        
        info = extract_pagination_info(html, "https://books.toscrape.com/catalogue/page-2.html")
        
        assert info['current_page'] == 2
        assert info['total_pages'] == 50
        assert info['next'] is not None
        assert "page-3.html" in info['next']


class TestScraper:
    """Test BookScraper class"""
    
    @pytest.mark.asyncio
    async def test_scraper_init(self):
        """Test scraper initialization"""
        async with BookScraper() as scraper:
            assert scraper.client is not None
            assert scraper.base_url == "https://books.toscrape.com"
    
    @pytest.mark.asyncio
    async def test_fetch_page_success(self):
        """Test successful page fetch"""
        async with BookScraper() as scraper:
            html = await scraper.fetch_page("https://books.toscrape.com/")
            
            assert html is not None
            assert "Books to Scrape" in html
    
    @pytest.mark.asyncio
    async def test_fetch_page_404(self):
        """Test fetching non-existent page"""
        async with BookScraper() as scraper:
            html = await scraper.fetch_page("https://books.toscrape.com/nonexistent")
            
            # Should return None for 404 errors
            assert html is None
    
    @pytest.mark.asyncio
    async def test_scrape_catalog_page(self):
        """Test scraping catalog page for book URLs"""
        async with BookScraper() as scraper:
            urls = await scraper.scrape_catalog_page(1)
            
            assert len(urls) == 20  # 20 books per page
            assert all("catalogue/" in url for url in urls)
    
    @pytest.mark.asyncio
    async def test_get_total_pages(self):
        """Test getting total pages"""
        async with BookScraper() as scraper:
            total = await scraper.get_total_pages()
            
            assert total == 50  # Site has 50 pages


class TestChangeDetection:
    """Test change detection functionality"""
    
    def test_tracked_fields(self):
        """Test that all critical fields are tracked"""
        from app.utils.helpers import TRACKED_FIELDS
        
        required_fields = ['price_incl_tax', 'availability', 'category']
        for field in required_fields:
            assert field in TRACKED_FIELDS
    
    @pytest.mark.asyncio
    async def test_detect_no_changes(self):
        """Test when no changes are detected"""
        from app.utils.change_detection import detect_changes
        
        # Create mock book
        book = Mock()
        book.id = "test-id"
        book.name = "Test Book"
        book.price_incl_tax = 51.77
        book.price_excl_tax = 51.77
        book.availability = "In stock"
        book.num_reviews = 0
        book.rating = 3
        book.category = "Poetry"
        
        # Same data
        new_data = {
            'price_incl_tax': 51.77,
            'price_excl_tax': 51.77,
            'availability': 'In stock',
            'num_reviews': 0,
            'rating': 3,
            'category': 'Poetry'
        }
        
        changes = await detect_changes(book, new_data)
        assert len(changes) == 0
    
    @pytest.mark.asyncio
    async def test_detect_price_change(self):
        """Test price change detection"""
        from app.utils.change_detection import detect_changes
        
        # Create mock book
        book = Mock()
        book.id = "test-id"
        book.name = "Test Book"
        book.price_incl_tax = 51.77
        book.price_excl_tax = 51.77
        book.availability = "In stock"
        book.num_reviews = 0
        book.rating = 3
        book.category = "Poetry"
        
        # Changed price
        new_data = {
            'price_incl_tax': 99.99,
            'price_excl_tax': 51.77,
            'availability': 'In stock',
            'num_reviews': 0,
            'rating': 3,
            'category': 'Poetry'
        }
        
        changes = await detect_changes(book, new_data)
        assert len(changes) == 1
        assert changes[0]['field_changed'] == 'price_incl_tax'
        assert changes[0]['old_value'] == 51.77
        assert changes[0]['new_value'] == 99.99
