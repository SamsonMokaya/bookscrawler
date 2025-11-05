# 📖 API Examples & Usage Guide

Complete collection of API request examples for the Book Scraper API.

---

## 🔑 Authentication

All requests (except `/` and `/health`) require an API key in the header:

```bash
X-API-Key: dev-key-001
```

---

## 📚 Books Endpoints

### 1. Get All Books (Basic)

```bash
curl -H "X-API-Key: dev-key-001" \
  http://localhost:8000/books
```

**Response:**

```json
{
  "total": 20,
  "page": 1,
  "limit": 20,
  "pages": 1,
  "books": [...]
}
```

---

### 2. Get Books with Pagination

```bash
# Page 2, 10 results per page
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?page=2&limit=10"
```

---

### 3. Filter by Category

```bash
# Get all Poetry books
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?category=Poetry"

# Get all Travel books
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?category=Travel"
```

---

### 4. Filter by Price Range

```bash
# Books between £20 and £50
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?min_price=20&max_price=50"

# Books under £30
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?max_price=30"

# Books over £50
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?min_price=50"
```

---

### 5. Filter by Rating

```bash
# 5-star books only
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?rating=5"

# 4-star and above (need to make 2 requests)
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?rating=4"
```

---

### 6. Filter by Availability

```bash
# In stock books
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?availability=In stock"

# Out of stock books
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?availability=Out of stock"
```

---

### 7. Search Books

```bash
# Search in name and description
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?search=light"

# Search for "Shakespeare"
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?search=shakespeare"
```

---

### 8. Sorting

```bash
# Sort by price (ascending)
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?sort_by=price_incl_tax&order=asc"

# Sort by price (descending)
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?sort_by=price_incl_tax&order=desc"

# Sort by rating (highest first)
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?sort_by=rating&order=desc"

# Sort by name (alphabetical)
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?sort_by=name&order=asc"

# Sort by recently crawled
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?sort_by=crawled_at&order=desc"
```

---

### 9. Combined Filters

```bash
# Poetry books, 4+ stars, under £40, sorted by price
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?category=Poetry&rating=4&max_price=40&sort_by=price_incl_tax&order=asc"

# Travel books in stock, sorted by rating
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?category=Travel&availability=In stock&sort_by=rating&order=desc"
```

---

### 10. Get Single Book

```bash
# Replace with actual book ID
curl -H "X-API-Key: dev-key-001" \
  http://localhost:8000/books/690b24fb9d8ccb72dea4ecfb
```

**Response:**

```json
{
  "id": "690b24fb9d8ccb72dea4ecfb",
  "name": "A Light in the Attic",
  "description": "It's hard to imagine...",
  "category": "Poetry",
  "price_excl_tax": 51.77,
  "price_incl_tax": 51.77,
  "availability": "In stock",
  "num_reviews": 0,
  "rating": 3,
  "image_url": "https://books.toscrape.com/media/...",
  "source_url": "https://books.toscrape.com/catalogue/...",
  "crawled_at": "2025-11-05T10:20:41",
  "updated_at": "2025-11-05T10:33:24"
}
```

---

## 📊 Changes Endpoints

### 1. Get All Changes

```bash
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes"
```

---

### 2. Get Recent Changes (Limited)

```bash
# Get last 10 changes
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes?limit=10"

# Get last 100 changes
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes?limit=100"
```

---

### 3. Filter by Change Type

```bash
# New books only
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes?change_type=new_book"

# Updates only
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes?change_type=update"
```

---

### 4. Filter by Field Changed

```bash
# Price changes only
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes?field_changed=price_incl_tax"

# Availability changes
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes?field_changed=availability"

# Rating changes
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes?field_changed=rating"

# Category changes
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes?field_changed=category"
```

---

### 5. Filter by Date Range

```bash
# Changes after specific date
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes?start_date=2025-11-05T00:00:00"

# Changes in date range
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes?start_date=2025-11-01T00:00:00&end_date=2025-11-05T23:59:59"
```

---

### 6. Get Change History for Specific Book

```bash
# Replace with actual book ID
curl -H "X-API-Key: dev-key-001" \
  http://localhost:8000/changes/books/690b24fb9d8ccb72dea4ecfb/history
```

**Response:**

```json
{
  "book_id": "690b24fb9d8ccb72dea4ecfb",
  "book_name": "A Light in the Attic",
  "total_changes": 2,
  "changes": [
    {
      "id": "690b27f4739a367662a28644",
      "book_id": "690b24fb9d8ccb72dea4ecfb",
      "book_name": "A Light in the Attic",
      "change_type": "update",
      "field_changed": "price_incl_tax",
      "old_value": 99.99,
      "new_value": 51.77,
      "changed_at": "2025-11-05T10:33:24"
    }
  ]
}
```

---

### 7. Combined Change Filters

```bash
# Price updates for specific book
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes?book_id=690b24fb9d8ccb72dea4ecfb&field_changed=price_incl_tax"

# Recent availability changes
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes?field_changed=availability&limit=20"
```

---

## 🚫 Error Examples

### Missing API Key

```bash
curl http://localhost:8000/books
```

**Response (401):**

```json
{
  "detail": "Missing API key. Include 'X-API-Key' header."
}
```

---

### Invalid API Key

```bash
curl -H "X-API-Key: wrong-key" \
  http://localhost:8000/books
```

**Response (401):**

```json
{
  "detail": "Invalid API key. Check your credentials."
}
```

---

### Rate Limit Exceeded

```bash
# After 100 requests in an hour
curl -H "X-API-Key: dev-key-001" \
  http://localhost:8000/books
```

**Response (429):**

```json
{
  "detail": "Rate limit exceeded. Try again in 3456 seconds."
}
```

**Headers:**

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1762346456
Retry-After: 3456
```

---

### Book Not Found

```bash
curl -H "X-API-Key: dev-key-001" \
  http://localhost:8000/books/000000000000000000000000
```

**Response (404):**

```json
{
  "detail": "Book with ID '000000000000000000000000' not found"
}
```

---

## 🎯 Common Use Cases

### Use Case 1: Find Cheapest 5-Star Books

```bash
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?rating=5&sort_by=price_incl_tax&order=asc&limit=10"
```

---

### Use Case 2: Monitor Price Drops

```bash
# Get all price changes
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes?field_changed=price_incl_tax&limit=50"

# Then check if new_value < old_value for price drops
```

---

### Use Case 3: Track New Arrivals

```bash
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes?change_type=new_book&limit=20"
```

---

### Use Case 4: Find Books in Stock by Category

```bash
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?category=Fiction&availability=In stock&limit=50"
```

---

### Use Case 5: Price Monitoring for Specific Book

```bash
# 1. Get book ID
BOOK_ID="690b24fb9d8ccb72dea4ecfb"

# 2. Get change history
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes/books/$BOOK_ID/history"

# 3. Filter for price changes only
curl -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/changes?book_id=$BOOK_ID&field_changed=price_incl_tax"
```

---

## 🔍 Rate Limit Headers

Every successful response includes rate limit information:

```bash
curl -i -H "X-API-Key: dev-key-001" \
  "http://localhost:8000/books?limit=1"
```

**Response Headers:**

```
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 93
X-RateLimit-Reset: 1762343019
```

**Interpret headers:**

- `X-RateLimit-Limit`: Total requests allowed per window (100)
- `X-RateLimit-Remaining`: Requests left in current window (93)
- `X-RateLimit-Reset`: Unix timestamp when counter resets

---

## 📱 Swagger/OpenAPI Documentation

Interactive API documentation available at:

```
http://localhost:8000/docs
```

Features:

- Try all endpoints interactively
- See request/response schemas
- Authentication support
- Built-in API testing

Alternative ReDoc documentation:

```
http://localhost:8000/redoc
```

---

## 🧪 Testing Rate Limiting

```bash
# Check current rate limit status
for i in {1..5}; do
  curl -i -H "X-API-Key: dev-key-001" \
    "http://localhost:8000/books?limit=1" 2>&1 | grep -i ratelimit
done
```

You'll see the `X-RateLimit-Remaining` value decrease with each request.

---

## 💡 Tips

### 1. Pretty Print JSON Responses

```bash
curl -H "X-API-Key: dev-key-001" \
  http://localhost:8000/books | python -m json.tool
```

Or use `jq`:

```bash
curl -H "X-API-Key: dev-key-001" \
  http://localhost:8000/books | jq
```

### 2. Extract Specific Fields

```bash
# Get only book names and prices
curl -H "X-API-Key: dev-key-001" \
  http://localhost:8000/books | jq '.books[] | {name, price: .price_incl_tax}'
```

### 3. Save Response to File

```bash
curl -H "X-API-Key: dev-key-001" \
  http://localhost:8000/books > books.json
```

### 4. Check Response Time

```bash
curl -w "\nTime: %{time_total}s\n" \
  -H "X-API-Key: dev-key-001" \
  http://localhost:8000/books
```

---

## 🔧 Advanced Usage

### Pagination Loop

```bash
#!/bin/bash
API_KEY="dev-key-001"
BASE_URL="http://localhost:8000"

for page in {1..5}; do
  echo "Fetching page $page..."
  curl -H "X-API-Key: $API_KEY" \
    "$BASE_URL/books?page=$page&limit=20" \
    > "books_page_$page.json"
  sleep 1
done
```

### Monitor Changes in Real-Time

```bash
#!/bin/bash
API_KEY="dev-key-001"
BASE_URL="http://localhost:8000"

while true; do
  echo "=== Changes at $(date) ==="
  curl -s -H "X-API-Key: $API_KEY" \
    "$BASE_URL/changes?limit=5" | jq '.changes[] | {book: .book_name, field: .field_changed, old: .old_value, new: .new_value}'
  sleep 60  # Check every minute
done
```

---

## 📊 Response Schemas

### Book Object

```typescript
{
  id: string,
  name: string,
  description: string | null,
  category: string,
  price_excl_tax: number,
  price_incl_tax: number,
  availability: string,
  num_reviews: number,
  rating: number,  // 1-5
  image_url: string,
  source_url: string,
  crawled_at: datetime,
  updated_at: datetime
}
```

### Change Object

```typescript
{
  id: string,
  book_id: string,
  book_name: string,
  change_type: "new_book" | "update" | "deleted",
  field_changed: string | null,
  old_value: any | null,
  new_value: any | null,
  changed_at: datetime
}
```

---

## 🐛 Debugging

### Check API Key

```bash
# Your configured keys (from .env)
grep "API_KEYS" .env
```

### Test Without Authentication

```bash
# These endpoints don't require auth
curl http://localhost:8000/
curl http://localhost:8000/health
```

### Verbose cURL Output

```bash
curl -v -H "X-API-Key: dev-key-001" \
  http://localhost:8000/books
```

---

## 📝 Notes

- All datetime values are in UTC
- Prices are in GBP (£)
- Pagination starts at page 1
- Maximum limit per request: 100 for books, 200 for changes
- Rate limit window: 1 hour (3600 seconds)
- Rate limit resets automatically after window expires
