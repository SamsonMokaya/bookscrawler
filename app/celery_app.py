from celery import Celery
from celery.schedules import crontab
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery instance
celery_app = Celery(
    "bookscrawler",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks', 'app.scheduler.crawl_tasks']
)

# Configure Celery
celery_app.conf.update(
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    result_expires=3600,  # Results expire after 1 hour
    timezone='UTC',
    enable_utc=True,
)

logger.info(f"Celery configured with broker: {settings.CELERY_BROKER_URL}")

# Configure Celery Beat schedule
celery_app.conf.beat_schedule = {}

# Only configure scheduled crawls if enabled
if settings.ENABLE_SCHEDULER:
    celery_app.conf.beat_schedule['daily-crawl-all-books'] = {
        'task': 'crawl_all_books',
        'schedule': crontab(
            hour=settings.CRAWL_SCHEDULE_HOUR,
            minute=settings.CRAWL_SCHEDULE_MINUTE
        ),
        'args': (1, None),  # Crawl all pages (1 to end)
        'options': {'expires': 3600 * 12}  # Task expires after 12 hours
    }
    logger.info(f"Scheduler enabled: Daily crawl at {settings.CRAWL_SCHEDULE_HOUR:02d}:{settings.CRAWL_SCHEDULE_MINUTE:02d} UTC")
    
# Optional: Add test task for development/debugging
# Uncomment to enable:
# celery_app.conf.beat_schedule['test-task-every-5-minutes'] = {
#     'task': 'app.tasks.test_task',
#     'schedule': 300.0,  # Every 5 minutes
# }

if __name__ == '__main__':
    celery_app.start()

