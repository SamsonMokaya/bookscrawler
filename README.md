# Book Scraper - Production Web Crawling Solution

A scalable, fault-tolerant web crawling system built with FastAPI, Celery, and MongoDB. Scrapes book information from `https://books.toscrape.com` with automated change detection and RESTful API access.

---

## Features

- **Async Web Crawler**: High-performance scraping with retry logic (50 pages, 1000 books)
- **Change Detection**: Automatic tracking of price, availability, rating, category, and review changes
- **RESTful API**: Comprehensive endpoints with filtering, pagination, and sorting
- **Scheduled Crawls**: Daily automated crawls using Celery Beat
- **API Security**: API key authentication and rate limiting (100 requests/hour)
- **Test Coverage**: 49 tests, all passing, with database isolation

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)

### Setup (3 Steps)

```bash
# 1. Navigate to project
cd /Users/nomad/PythonProjects/bookscrawler

# 2. Create .env file
cp env.template .env

# 3. Start all services
docker-compose up -d
```

**Done!** Services running:

- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- Flower (Celery): http://localhost:5555

### Verify Installation

```bash
curl http://localhost:8000/health
```

Expected:

```json
{
  "status": "healthy",
  "api": "running",
  "redis": "connected",
  "celery": "active",
  "mongodb": "connected"
}
```

---

## Project Structure

```
bookscrawler/
├── app/
│   ├── api/              # API endpoints (books, changes)
│   ├── crawler/          # Web scraping (parser, scraper)
│   ├── scheduler/        # Celery tasks
│   ├── models/           # Database models (Book, ChangeLog)
│   ├── database/         # MongoDB connection
│   ├── utils/            # Helpers (auth, rate_limit, change_detection)
│   └── tests/            # Test suite (49 tests)
├── docker-compose.yml    # Docker services
├── requirements.txt      # Python dependencies
└── .env                  # Environment configuration
```

---

## Configuration

Edit `.env` file (created from `env.template`):

### Key Settings

```bash
# API Keys (comma-separated)
API_KEYS=dev-key-001,dev-key-002,dev-key-003

# Rate Limiting
RATE_LIMIT_REQUESTS=100        # Requests per hour
RATE_LIMIT_WINDOW=3600         # Window in seconds

# Scheduler
ENABLE_SCHEDULER=true          # Enable daily crawls
CRAWL_SCHEDULE_HOUR=2          # UTC hour (2 AM)
CRAWL_SCHEDULE_MINUTE=0

# Crawler
CRAWLER_CONCURRENT_REQUESTS=5  # Parallel requests
CRAWLER_DELAY=0.5              # Delay between requests (seconds)
CRAWLER_MAX_RETRIES=3          # Retry attempts
```

All dependencies are in `requirements.txt`.

---

## API Documentation

### Authentication

All endpoints require API key in header:

```bash
X-API-Key: dev-key-001
```

### Core Endpoints

#### 1. GET /books - List Books

```bash
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?category=Poetry&rating=5&limit=10"
```

**Query Parameters:**

- `category`, `min_price`, `max_price`, `rating`, `availability`, `search`
- `sort_by` (price_incl_tax, rating, name), `order` (asc, desc)
- `page`, `limit` (max 100)

#### 2. GET /books/{id} - Single Book

```bash
curl -H "X-API-Key: dev-key-001" \
  http://localhost:8000/books/690b24fb9d8ccb72dea4ecfb
```

#### 3. GET /changes - Change History

```bash
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes?field_changed=price_incl_tax&limit=20"
```

**Query Parameters:**

- `book_id`, `change_type`, `field_changed`, `start_date`, `end_date`
- `page`, `limit` (max 200)

#### 4. GET /changes/books/{id}/history - Book History

```bash
curl -H "X-API-Key: dev-key-001" \
  http://localhost:8000/changes/books/690b24fb9d8ccb72dea4ecfb/history
```

### Rate Limiting

Every response includes:

- `X-RateLimit-Limit: 100`
- `X-RateLimit-Remaining: 95`
- `X-RateLimit-Reset: [timestamp]`

Returns `429 Too Many Requests` when limit exceeded.

---

## Database Schema

### Books Collection

```javascript
{
  "name": "A Light in the Attic",
  "category": "Poetry",
  "price_excl_tax": 51.77,
  "price_incl_tax": 51.77,
  "availability": "In stock",
  "num_reviews": 0,
  "rating": 3,
  "image_url": "https://...",
  "source_url": "https://...",
  "crawled_at": "2025-11-05T10:20:41",
  "content_hash": "a1b2c3..."
}
```

**Indexes:** `source_url` (unique), `name`, `category`, `rating`, `price_incl_tax`

### ChangeLogs Collection

```javascript
{
  "book_id": "690b24fb...",
  "book_name": "A Light in the Attic",
  "change_type": "update",
  "field_changed": "price_incl_tax",
  "old_value": 99.99,
  "new_value": 51.77,
  "changed_at": "2025-11-05T10:33:24"
}
```

**Indexes:** `book_id`, `changed_at`, `change_type`

**Tracked Fields:** `price_excl_tax`, `price_incl_tax`, `availability`, `num_reviews`, `rating`, `category`

---

## Running Tests

```bash
# Ensure services are running
docker-compose up -d

# Run all tests
docker-compose exec backend pytest app/tests/ -v
```

**Expected:** 49 tests pass in ~X seconds

Tests use separate databases:

- MongoDB: `bookscrawler_test` (auto-cleaned)
- Redis: DB 1 (auto-flushed)

---

## Manual Crawling

### Trigger Full Crawl (1000 books)

```bash
docker exec bookscrawler_backend python -c "
from app.scheduler.crawl_tasks import crawl_all_books_task
result = crawl_all_books_task.delay(start_page=1, end_page=50)
print(f'Task ID: {result.id}')
"
```

### Crawl Specific Pages

```bash
docker exec bookscrawler_backend python -c "
from app.scheduler.crawl_tasks import crawl_page_range_task
result = crawl_page_range_task.delay(start_page=1, end_page=5)
print(f'Task ID: {result.id}')
"
```

### Monitor Tasks

- Flower Dashboard: http://localhost:5555
- View logs: `docker logs -f bookscrawler_celery_worker`

---

## Docker Services

| Service       | Port  | Description          |
| ------------- | ----- | -------------------- |
| backend       | 8000  | FastAPI application  |
| mongodb       | 27017 | MongoDB database     |
| redis         | 6379  | Redis cache & broker |
| celery_worker | -     | Task processor       |
| celery_beat   | -     | Scheduler            |
| flower        | 5555  | Celery monitoring    |

### Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f backend

# Restart service
docker-compose restart backend
```

---

## Performance

- **Crawl Speed**: 20 books in ~5 seconds
- **Full Site**: 1000 books in ~5 minutes
- **Success Rate**: 100% with retry logic
- **API Response**: <100ms for most queries
- **Concurrent Requests**: 5 simultaneous

---

## Architecture

```
FastAPI API ←→ Redis ←→ Celery Worker/Beat ←→ MongoDB
     ↓           ↓              ↓               ↓
  REST API   Rate Limit   Background Tasks   Data Store
```

**Key Components:**

- **FastAPI**: REST API with async endpoints
- **Celery + Beat**: Distributed task queue with scheduler
- **MongoDB + Beanie**: Async ODM for data persistence
- **Redis**: Message broker and rate limiting
- **httpx**: Async HTTP client for scraping
- **BeautifulSoup**: HTML parsing

---

## Quick Reference

### Test API

```bash
# Get books
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?limit=5"

# Filter by category & rating
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?category=Poetry&rating=5"

# Get changes
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes"
```

### Check Status

```bash
# API health
curl http://localhost:8000/health

# View all endpoints
open http://localhost:8000/docs
```

---

Built as a production-ready web scraping solution demonstrating scalable architecture, fault tolerance, and modern Python async patterns.
