# 📋 Implementation Plan - Book Scraper Project

## ✅ COMPLETED

### Phase 0: Setup

- [x] Docker setup (Redis, MongoDB, FastAPI, Celery, Celery Beat)
- [x] Folder structure created
- [x] env.template with API keys configuration
- [x] Book model (Beanie) with all required fields
- [x] ChangeLog model (Beanie) for tracking changes

---

## 🔄 IN PROGRESS

### Phase 1: Database Foundation

#### Step 1.3: Database Connection ⏳ NEXT

**File:** `app/database/mongo.py`

- [ ] Implement `init_db()` function
- [ ] Initialize Beanie with Book and ChangeLog models
- [ ] Create indexes
- [ ] Handle connection errors

**File:** `app/main.py`

- [ ] Add startup event to call `init_db()`
- [ ] Add shutdown event to call `close_db()`

**Verification:** Backend connects to MongoDB, models registered

---

## 📝 TODO

### Phase 2: Web Crawler

#### Step 2.1: HTML Parser

**File:** `app/crawler/parser.py`

- [ ] Parse book name
- [ ] Parse description
- [ ] Parse category
- [ ] Parse prices (incl/excl tax)
- [ ] Parse availability
- [ ] Parse number of reviews
- [ ] Parse image URL
- [ ] Parse rating (convert stars to 1-5)
- [ ] Handle missing fields gracefully

**Verification:** Test with sample HTML

#### Step 2.2: Async Scraper

**File:** `app/crawler/scraper.py`

- [ ] Async function to fetch URL with httpx
- [ ] Retry logic (3 retries with exponential backoff)
- [ ] Error handling (network errors, timeouts)
- [ ] Pagination handling (detect next page)
- [ ] Store raw HTML
- [ ] Concurrent requests (10 at a time)

**Verification:** Scrape one book successfully

#### Step 2.3: Crawl All Books Task

**File:** `app/scheduler/crawl_tasks.py`

- [ ] Celery task: `crawl_all_books()`
- [ ] Loop through all pages
- [ ] Save each book to MongoDB
- [ ] Deduplication (check source_url)
- [ ] Resume logic (track last successful page)
- [ ] Error handling and logging

**Verification:** Run task, verify books in MongoDB

---

### Phase 3: Change Detection

#### Step 3.1: Change Detection Task

**File:** `app/scheduler/change_tasks.py`

- [ ] Task: `detect_changes()`
- [ ] Fetch current site data
- [ ] Compare with database using content_hash
- [ ] Detect new books
- [ ] Detect updated books (price/availability)
- [ ] Save changes to ChangeLog
- [ ] Log significant changes

**Verification:** Modify book data, detect change

#### Step 3.2: Scheduler Configuration

**File:** `app/celery_app.py`

- [ ] Add daily crawl schedule (2 AM)
- [ ] Add daily change detection schedule
- [ ] Update task includes

**Verification:** Celery Beat shows scheduled tasks

#### Step 3.3: Change Reports

**File:** `app/utils/helpers.py`

- [ ] Generate JSON change report
- [ ] Generate CSV change report
- [ ] Optional: Email alerts

**Verification:** Generate report, verify format

---

### Phase 4: API Endpoints

#### Step 4.1: Security Implementation

**File:** `app/utils/auth.py`

- [ ] API key validation dependency
- [ ] Check against valid_api_keys list
- [ ] Check against blocked_api_keys list
- [ ] Return 401 for invalid keys
- [ ] Return 403 for blocked keys

**File:** `app/utils/rate_limit.py`

- [ ] Redis-based rate limiter
- [ ] Track requests per API key per hour
- [ ] Return 429 when limit exceeded
- [ ] Dependency function for FastAPI

**Verification:** Test auth and rate limiting

#### Step 4.2: Books Endpoints

**File:** `app/api/books.py`

- [ ] `GET /books` - List books
  - [ ] Filter by category
  - [ ] Filter by min_price, max_price
  - [ ] Filter by rating
  - [ ] Sort by (rating, price, reviews)
  - [ ] Pagination (page, limit)
- [ ] `GET /books/{book_id}` - Get single book
- [ ] Apply authentication
- [ ] Apply rate limiting

**Verification:** Test in Swagger UI

#### Step 4.3: Changes Endpoint

**File:** `app/api/changes.py`

- [ ] `GET /changes` - List recent changes
  - [ ] Filter by date range
  - [ ] Filter by change_type
  - [ ] Pagination
- [ ] Apply authentication
- [ ] Apply rate limiting

**Verification:** See change log entries

#### Step 4.4: Wire Up Routes

**File:** `app/main.py`

- [ ] Import and include books router
- [ ] Import and include changes router
- [ ] Update API description

**Verification:** All endpoints in /docs

---

### Phase 5: Testing & Documentation

#### Step 5.1: Unit Tests

**File:** `app/tests/test_crawler.py`

- [ ] Test HTML parsing
- [ ] Test scraper with mock responses
- [ ] Test pagination handling

**File:** `app/tests/test_api.py`

- [ ] Test GET /books with filters
- [ ] Test GET /books/{id}
- [ ] Test GET /changes
- [ ] Test authentication
- [ ] Test rate limiting

**File:** `app/tests/test_tasks.py`

- [ ] Test crawl_all_books task
- [ ] Test detect_changes task
- [ ] Test deduplication

**Verification:** pytest passes

#### Step 5.2: Documentation

**File:** `README.md`

- [ ] Update setup instructions
- [ ] Document API endpoints
- [ ] Add MongoDB document examples
- [ ] Add testing instructions
- [ ] Add screenshots/logs

**Verification:** Follow README, everything works

#### Step 5.3: Additional Deliverables

- [ ] Add pytest to requirements.txt
- [ ] Create sample MongoDB document JSON
- [ ] Take screenshots of successful crawl
- [ ] Take screenshots of Swagger UI

---

## 📊 Progress Tracking

**Total Steps:** ~25
**Completed:** 5 (20%)
**In Progress:** 1
**Remaining:** 19

---

## 🎯 Current Status

**Next Step:** Step 1.3 - Database Connection
**Ready to implement:** YES
**Blockers:** None
