"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from typing import Generator
from motor.motor_asyncio import AsyncIOMotorClient
from redis import Redis
import httpx

# Set testing mode FIRST - before any other app imports
from app.config import settings
settings.TESTING = True

from app.database.mongo import init_db, close_db
from app.models import Book, ChangeLog
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def setup_test_db():
    """
    Set up test database and Redis before EVERY test
    Automatically cleans up after test
    """
    # Reset Redis client to use test DB
    from app.utils.rate_limit import reset_redis_client
    reset_redis_client()
    
    # Clear test Redis database
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    redis_client.flushdb()  # Clear only the test DB (DB 1)
    
    # Initialize test database
    await init_db()
    
    yield  # Test runs here
    
    # Cleanup: Drop test database and clear Redis after each test
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await client.drop_database(settings.TEST_MONGODB_DB_NAME)
    await close_db()
    
    # Clear Redis test database
    redis_client.flushdb()
    redis_client.close()
    
    # Reset client for next test
    reset_redis_client()


@pytest.fixture
async def sample_book() -> Book:
    """
    Create a sample book for testing
    """
    book = Book(
        name="Test Book for Testing",
        description="This is a test book description",
        category="Fiction",
        price_excl_tax=19.99,
        price_incl_tax=23.99,
        availability="In stock",
        num_reviews=10,
        rating=4,
        image_url="http://example.com/test-image.jpg",
        source_url="http://example.com/test-book-unique-url",
        content_hash="test-hash-abc123"
    )
    await book.insert()
    return book


@pytest.fixture
async def sample_books() -> list[Book]:
    """
    Create multiple sample books for testing
    """
    books_data = [
        {
            "name": "Poetry Book",
            "category": "Poetry",
            "price_incl_tax": 25.50,
            "rating": 5
        },
        {
            "name": "Fiction Book",
            "category": "Fiction",
            "price_incl_tax": 35.00,
            "rating": 3
        },
        {
            "name": "Travel Book",
            "category": "Travel",
            "price_incl_tax": 45.00,
            "rating": 4
        }
    ]
    
    created_books = []
    for i, data in enumerate(books_data):
        book = Book(
            name=data["name"],
            description=f"Description for {data['name']}",
            category=data["category"],
            price_excl_tax=data["price_incl_tax"] * 0.9,
            price_incl_tax=data["price_incl_tax"],
            availability="In stock",
            num_reviews=5,
            rating=data["rating"],
            image_url=f"http://example.com/image-{i}.jpg",
            source_url=f"http://example.com/book-{i}",
            content_hash=f"hash-{i}"
        )
        await book.insert()
        created_books.append(book)
    
    return created_books


@pytest.fixture
async def sample_changelog(sample_book) -> ChangeLog:
    """
    Create a sample changelog entry for testing
    """
    changelog = ChangeLog(
        book_id=str(sample_book.id),
        book_name=sample_book.name,
        change_type="update",
        field_changed="price_incl_tax",
        old_value=29.99,
        new_value=23.99
    )
    await changelog.insert()
    return changelog


@pytest.fixture
def valid_api_key() -> str:
    """Return a valid API key for testing"""
    return "dev-key-001"


@pytest.fixture
def invalid_api_key() -> str:
    """Return an invalid API key for testing"""
    return "invalid-test-key-xyz"


@pytest.fixture
def blocked_api_key() -> str:
    """Return a blocked API key for testing"""
    # Note: Add this key to BLOCKED_API_KEYS in .env for this to work
    return "blocked-test-key"

