# Book Scraper API

A scalable book scraping service built with FastAPI, Celery, and Celery Beat, containerized with Docker.

## Features

- 🚀 **FastAPI Backend**: Modern, fast web framework for building APIs
- 📦 **Celery**: Distributed task queue for handling async operations
- ⏰ **Celery Beat**: Scheduler for periodic tasks
- 🌺 **Flower**: Web-based tool for monitoring Celery tasks
- 🐳 **Docker**: Fully containerized application
- 📊 **Redis**: Message broker and result backend

## Architecture

The application consists of 5 Docker containers:

1. **Backend (FastAPI)**: REST API server (port 8000)
2. **Redis**: Message broker and result backend (port 6379)
3. **Celery Worker**: Processes background tasks
4. **Celery Beat**: Scheduler for periodic tasks
5. **Flower**: Monitoring dashboard (port 5555)

## Prerequisites

- Docker
- Docker Compose

## Quick Start

### 1. Clone and Setup

```bash
cd /Users/nomad/PythonProjects/bookscrawler
cp .env.example .env
```

### 2. Build and Run

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### 3. Access Services

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Flower Dashboard**: http://localhost:5555
- **API Root**: http://localhost:8000

## API Endpoints

### Health Check

```bash
curl http://localhost:8000/health
```

### Scrape a Single Book

```bash
curl -X POST "http://localhost:8000/scrape/book" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/book1"}'
```

### Scrape Multiple Books

```bash
curl -X POST "http://localhost:8000/scrape/books" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com/book1", "https://example.com/book2"]}'
```

### Check Task Status

```bash
curl http://localhost:8000/task/{task_id}
```

### Get Active Tasks

```bash
curl http://localhost:8000/celery/active-tasks
```

### Get Celery Stats

```bash
curl http://localhost:8000/celery/stats
```

### Trigger Long-Running Task (for testing)

```bash
curl -X POST "http://localhost:8000/test/long-task?duration=30"
```

### Manually Trigger Scheduled Scrape

```bash
curl -X POST "http://localhost:8000/trigger/scheduled-scrape"
```

## Scheduled Tasks

The following tasks are scheduled via Celery Beat:

1. **Book Scraping** - Runs every hour at minute 0
2. **Data Cleanup** - Runs daily at 2:00 AM UTC
3. **Health Check** - Runs every 5 minutes

You can view and modify schedules in `app/celery_app.py`.

## Project Structure

```
bookscrawler/
├── app/
│   ├── __init__.py          # Package initializer
│   ├── main.py              # FastAPI application
│   ├── celery_app.py        # Celery configuration
│   ├── tasks.py             # Celery tasks
│   └── config.py            # Application settings
├── docker-compose.yml       # Docker services configuration
├── Dockerfile               # Container image definition
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Docker Commands

### Start Services

```bash
docker-compose up -d
```

### Stop Services

```bash
docker-compose down
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

### Rebuild After Code Changes

```bash
docker-compose up -d --build
```

### Access Container Shell

```bash
docker exec -it bookscrawler_backend /bin/bash
```

## Development

### Adding New Tasks

1. Add your task function in `app/tasks.py`:

```python
@celery_app.task(name='app.tasks.my_new_task')
def my_new_task():
    # Your task logic here
    pass
```

2. For scheduled tasks, add to `beat_schedule` in `app/celery_app.py`:

```python
celery_app.conf.beat_schedule = {
    'my-scheduled-task': {
        'task': 'app.tasks.my_new_task',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
}
```

### Adding New API Endpoints

Add endpoints in `app/main.py`:

```python
@app.get("/my-endpoint")
async def my_endpoint():
    return {"message": "Hello"}
```

## Monitoring with Flower

Flower provides a web interface to monitor Celery tasks:

- View active, scheduled, and completed tasks
- Monitor worker status
- View task details and results
- Retry failed tasks
- Access at: http://localhost:5555

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs

# Rebuild containers
docker-compose down
docker-compose up --build
```

### Redis connection issues

```bash
# Check Redis is running
docker-compose ps

# Test Redis connection
docker exec -it bookscrawler_redis redis-cli ping
```

### Celery tasks not executing

```bash
# Check worker logs
docker-compose logs celery_worker

# Check beat logs
docker-compose logs celery_beat

# Verify tasks are registered
docker exec -it bookscrawler_celery_worker celery -A app.celery_app.celery_app inspect registered
```

## Production Considerations

Before deploying to production:

1. Update `.env` with secure credentials
2. Set `DEBUG=False` in config
3. Use a production-grade ASGI server (already using uvicorn)
4. Add authentication/authorization
5. Implement rate limiting
6. Set up proper logging and monitoring
7. Use a persistent volume for Redis data
8. Configure proper security headers
9. Set up HTTPS/SSL certificates
10. Implement proper error handling and retries

## License

MIT License
