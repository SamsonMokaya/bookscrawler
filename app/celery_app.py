from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Create Celery instance
celery_app = Celery(
    "bookscrawler",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks']
)

# Configure Celery
celery_app.conf.update(
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    result_expires=3600,  # Results expire after 1 hour
    timezone='UTC',
    enable_utc=True,
)

# Configure Celery Beat schedule
celery_app.conf.beat_schedule = {
    'scrape-books-every-hour': {
        'task': 'app.tasks.scheduled_book_scrape',
        'schedule': crontab(minute=0),  # Every hour at minute 0
    },
    'cleanup-old-data-daily': {
        'task': 'app.tasks.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0),  # Every day at 2:00 AM
    },
    'health-check-every-5-minutes': {
        'task': 'app.tasks.health_check',
        'schedule': 300.0,  # Every 5 minutes (in seconds)
    },
}

if __name__ == '__main__':
    celery_app.start()

