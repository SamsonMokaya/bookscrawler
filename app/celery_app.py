from celery import Celery
from celery.schedules import crontab
from celery.signals import after_setup_logger, after_setup_task_logger
from app.config import settings
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    """Configure Celery logger to write to app.log (production only)"""
    # Skip file logging during tests
    if settings.TESTING:
        return
    
    # Ensure logs directory exists
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Add file handler
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(file_handler)


@after_setup_task_logger.connect
def setup_task_logger(logger, *args, **kwargs):
    """Configure task logger to write to app.log (production only)"""
    # Skip file logging during tests
    if settings.TESTING:
        return
    
    # Ensure logs directory exists
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Add file handler
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(file_handler)

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
    broker_connection_retry_on_startup=True,  # Explicit retry on startup (Celery 6.0+ compatibility)
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

