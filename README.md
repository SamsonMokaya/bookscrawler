# Book Scraper

A web crawling system built with FastAPI, Celery, and MongoDB. Scrapes book information from `https://books.toscrape.com` with automated change detection and RESTful API access.

---

## Quick Start

### Prerequisites

- Docker

**Note:** Python 3.11 runtime is included in Docker containers.

### Setup (7 Steps)

```bash
# 1. Clone the repository
git clone https://github.com/nomad-ai/bookscrawler.git

# 2. Navigate to project
cd .../bookscrawler

# 3. Create .env file
cp env.template .env

# 4. Configure email settings (edit .env file)
# Required: Fill in these fields manually:
#   - SMTP_USER_EMAIL (your Gmail address)
#   - SMTP_PASSWORD (Gmail App Password)
#   - NOTIFICATION_EMAIL (where to receive alerts)

# 5. Generate MongoDB keyfile (required for replica set)
openssl rand -base64 756 > mongo-keyfile && chmod 400 mongo-keyfile

# 6. Start all services
docker-compose up -d

# 7. Initialize MongoDB replica set (one-time setup)
chmod +x mongo-init.sh  # Make script executable
./mongo-init.sh
```

**Note:** MongoDB replica set is required for transaction support (ensures atomic book + changelog saves).

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
│   ├── api/              # API endpoints (books, changes, reports)
│   ├── crawler/          # Web scraping (parser, scraper)
│   ├── scheduler/        # Celery tasks
│   ├── models/           # Database models (Book, ChangeLog)
│   ├── database/         # MongoDB connection
│   ├── utils/            # Helpers (auth, rate_limit, change_detection, email)
│   └── tests/            # Test suite (62 tests)
├── docker-compose.yml    # Docker services
├── mongo-init.sh         # MongoDB replica set setup
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

## Automated Scheduler

Based on the default `.env` configuration, the scheduler operates as follows:

| Setting             | Value                                             |
| ------------------- | ------------------------------------------------- |
| **Frequency**       | **Daily**                                         |
| **Time**            | **2:00 AM UTC**                                   |
| **Task**            | `crawl_all_books`                                 |
| **Pages**           | All (1 to end)                                    |
| **Purpose**         | Detect new books + changes, log everything        |
| **Lock Timeout**    | 6 hours max                                       |
| **Task Expiration** | 12 hours (task won't start if scheduled >12h ago) |

### How It Works

- **New Books:** Detected and logged in the ChangeLog collection
- **Changed Books:** Tracked fields (price, availability, reviews, rating, category) are compared and changes logged
- **Concurrent Crawls:** Prevented via Redis distributed lock
- **Data Consistency:** MongoDB transactions ensure atomic saves (book + changelog together)

### Note on Resuming from Failed Crawls

The scheduler does **not** resume from the last successful crawl position. Since we crawl the entire site daily to get fresh data, resuming from a partial crawl would be redundant. Instead, the system implements:

- **Retry logic** with exponential backoff for transient errors (network issues, timeouts, 5xx errors)
- **Redis locking** to prevent overlapping crawls
- **Comprehensive error logging** to identify and address persistent failures

If a crawl fails completely, the next scheduled run (2 AM the following day) will perform a fresh, full crawl.

---

## API Documentation

**Interactive Swagger Docs:** http://localhost:8000/docs

### Authentication

All endpoints require API key:

```bash
X-API-Key: dev-key-001
```

### Core Endpoints

- `GET /books` - List books (filters: category, price, rating, search; sorting, pagination)
- `GET /books/{id}` - Single book details
- `GET /changes` - Change history (filters: book_id, change_type, field, dates; pagination)
- `GET /reports/changes/daily` - Daily CSV/JSON reports

**See full interactive documentation at:** http://localhost:8000/docs

### Daily Reports (CSV/JSON Download)

Generate daily change reports in JSON or CSV format:

**JSON Report:**

```bash
# Get today's changes
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/reports/changes/daily"

# Get specific date
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/reports/changes/daily?date=2025-11-05"
```

**CSV Download:**

```bash
# Save CSV to file
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/reports/changes/daily?format=csv" \
  -o daily_changes.csv

# Then open in Excel/Sheets:
open daily_changes.csv
```

**Query Parameters:**

- `date` - Date in YYYY-MM-DD format (default: today)
- `format` - `json` (default) or `csv`

**JSON Response Example:**

```json
{
  "date": "2025-11-05",
  "summary": {
    "total_changes": 150,
    "new_books": 5,
    "updates": 145,
    "fields_changed": {
      "price_incl_tax": 80,
      "availability": 45
    }
  },
  "changes": [
    {
      "book_name": "Sample Book",
      "change_type": "update",
      "field_changed": "price_incl_tax",
      "old_value": "19.99",
      "new_value": "24.99",
      "description": "Price increased by £5.00"
    }
  ]
}
```

**CSV Output:**

```
Timestamp,Book Name,Change Type,Field Changed,Old Value,New Value,Description
2025-11-05 10:30:00,Sample Book,update,price_incl_tax,19.99,24.99,Price increased by £5.00
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

**Expected:** 62 tests pass in approximately ~23 seconds

Tests use separate databases:

- MongoDB: `bookscrawler_test` (auto-cleaned)
- Redis: DB 1 (auto-flushed)

---

## Logging

Application logs are written to `logs/app.log` (FastAPI + Celery + all tasks).

**Note:** Test execution does not write to `logs/app.log`.

**Production Note:** For production deployment, I would implement log rotation to prevent disk space issues:

- Python: `RotatingFileHandler` (max 10MB per file, keep 5 backups)
- Docker: Logging config in `docker-compose.yml` (`max-size: "10m"`, `max-file: "3"`)

---

## Manual Crawling

You can manually trigger crawls using Celery tasks. Tasks are queued and executed by Celery workers.

**Important:** Only one crawl can run at a time (Redis distributed lock). 
If a crawl is already running when a new crawl is triggered:
- The new crawl is **skipped** (not queued or retried)
- The running crawl continues unaffected
- You'll see "skipped" status in logs and Flower dashboard

### Trigger Full Crawl (1000 books)

```bash
docker exec bookscrawler_backend python -c "
from app.scheduler.crawl_tasks import crawl_all_books_task
result = crawl_all_books_task.delay(start_page=1, end_page=None)
print(f'Task ID: {result.id}')
"
```

This **queues** a crawl task to crawl all books from page 1 to the last page.

### Crawl Specific Pages

```bash
docker exec bookscrawler_backend python -c "
from app.scheduler.crawl_tasks import crawl_page_range_task
result = crawl_page_range_task.delay(start_page=1, end_page=5)
print(f'Task ID: {result.id}')
"
```

This **queues** a task to crawl pages 1-5 only.

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
