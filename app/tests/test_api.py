"""
Full E2E tests for API endpoints with database integration
"""
import pytest
import httpx
from fastapi.testclient import TestClient

from app.main import app


class TestHealthEndpoint:
    """Test health check endpoint (no auth required)"""
    
    def test_root_endpoint(self):
        """Test GET / (no auth required)"""
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data


class TestAuthentication:
    """Test API key authentication"""
    
    def test_missing_api_key(self):
        """Test request without API key returns 401"""
        client = TestClient(app)
        response = client.get("/books")
        
        assert response.status_code == 401
        assert "Missing API key" in response.json()["detail"]
    
    def test_invalid_api_key(self):
        """Test request with invalid API key returns 401"""
        client = TestClient(app)
        response = client.get(
            "/books",
            headers={"X-API-Key": "invalid-test-key-xyz"}
        )
        
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]


# Async tests using httpx.AsyncClient
@pytest.mark.asyncio
class TestBooksEndpointsAsync:
    """Test books API endpoints with database"""
    
    async def test_get_books_empty_db(self):
        """Test GET /books with empty database"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/books",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["books"] == []
    
    async def test_get_books_with_data(self, sample_books):
        """Test GET /books with sample data"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/books",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["books"]) == 3
    
    async def test_filter_by_category(self, sample_books):
        """Test filtering by category"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/books?category=Poetry",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["books"][0]["category"] == "Poetry"
    
    async def test_filter_by_rating(self, sample_books):
        """Test filtering by rating"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/books?rating=5",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["books"][0]["rating"] == 5
    
    async def test_filter_by_price_range(self, sample_books):
        """Test filtering by price range"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/books?min_price=30&max_price=40",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert 30 <= data["books"][0]["price_incl_tax"] <= 40
    
    async def test_search_books(self, sample_books):
        """Test search functionality"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/books?search=Poetry",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
    
    async def test_sort_by_price_asc(self, sample_books):
        """Test sorting by price ascending"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/books?sort_by=price_incl_tax&order=asc",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        assert response.status_code == 200
        data = response.json()
        prices = [book["price_incl_tax"] for book in data["books"]]
        assert prices == sorted(prices)
    
    async def test_sort_by_price_desc(self, sample_books):
        """Test sorting by price descending"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/books?sort_by=price_incl_tax&order=desc",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        assert response.status_code == 200
        data = response.json()
        prices = [book["price_incl_tax"] for book in data["books"]]
        assert prices == sorted(prices, reverse=True)
    
    async def test_pagination(self, sample_books):
        """Test pagination"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/books?page=1&limit=2",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 2
        assert len(data["books"]) == 2
        assert data["pages"] == 2  # 3 books / 2 per page = 2 pages
    
    async def test_get_single_book(self, sample_book):
        """Test GET /books/{id}"""
        book_id = str(sample_book.id)
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/books/{book_id}",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == book_id
        assert data["name"] == sample_book.name
        assert data["price_incl_tax"] == sample_book.price_incl_tax
    
    async def test_get_nonexistent_book(self):
        """Test GET /books/{id} with invalid ID"""
        fake_id = "000000000000000000000000"
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/books/{fake_id}",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        # Should return 404 or 500
        assert response.status_code in [404, 500]


@pytest.mark.asyncio
class TestChangesEndpointsAsync:
    """Test changes API endpoints with database"""
    
    async def test_get_changes_empty(self):
        """Test GET /changes with no changes"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/changes",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["changes"] == []
    
    async def test_get_changes_with_data(self, sample_changelog):
        """Test GET /changes with sample changelog (flat format)"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/changes",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["changes"]) == 1
        assert data["changes"][0]["field_changed"] == "price_incl_tax"
    
    async def test_filter_changes_by_type(self, sample_changelog):
        """Test filtering changes by type (flat format)"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/changes?change_type=update",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert all(c["change_type"] == "update" for c in data["changes"])
    
    async def test_filter_changes_by_field(self, sample_changelog):
        """Test filtering changes by field (flat format)"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/changes?field_changed=price_incl_tax",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert all(c["field_changed"] == "price_incl_tax" for c in data["changes"])
    
    async def test_changes_pagination(self):
        """Test changes pagination"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/changes?page=1&limit=10",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 10


@pytest.mark.asyncio
class TestCombinedFilters:
    """Test combined filter functionality"""
    
    async def test_category_and_rating(self, sample_books):
        """Test filtering by category and rating together"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/books?category=Poetry&rating=5",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        assert response.status_code == 200
        data = response.json()
        for book in data["books"]:
            assert book["category"] == "Poetry"
            assert book["rating"] == 5
    
    async def test_price_range_and_sort(self, sample_books):
        """Test price filtering with sorting"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/books?min_price=20&max_price=50&sort_by=price_incl_tax&order=asc",
                headers={"X-API-Key": "dev-key-001"}
            )
        
        assert response.status_code == 200
        data = response.json()
        for book in data["books"]:
            assert 20 <= book["price_incl_tax"] <= 50


@pytest.mark.asyncio
class TestRateLimitingAsync:
    """Test rate limiting with async client"""
    
    async def test_rate_limit_headers(self):
        """Test rate limit headers are present"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/books?limit=1",
                headers={"X-API-Key": "dev-key-003"}
            )
        
        assert response.status_code == 200
        assert "x-ratelimit-limit" in response.headers
        assert "x-ratelimit-remaining" in response.headers
        assert "x-ratelimit-reset" in response.headers
        assert int(response.headers["x-ratelimit-limit"]) == 100
    
    async def test_rate_limit_enforcement(self):
        """Test that rate limit actually blocks requests after limit exceeded"""
        # Use a unique API key for this test to avoid interference
        test_api_key = "dev-key-001"
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            # Make 100 requests (the limit)
            for i in range(100):
                response = await client.get(
                    "/books?limit=1",
                    headers={"X-API-Key": test_api_key}
                )
                assert response.status_code == 200
            
            # The 101st request should be rate limited
            response = await client.get(
                "/books?limit=1",
                headers={"X-API-Key": test_api_key}
            )
            
            assert response.status_code == 429
            assert "retry-after" in response.headers
            data = response.json()
            assert "rate limit exceeded" in data["detail"].lower()
