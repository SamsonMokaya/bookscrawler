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
    # Example scheduled task - runs every 2 minutes
    'test-task-every-2-minutes': {
        'task': 'app.tasks.test_task',
        'schedule': 120.0,  # Every 120 seconds (2 minutes)
    },
    # You can also use crontab for more complex schedules:
    # 'daily-task-example': {
    #     'task': 'app.tasks.some_task',
    #     'schedule': crontab(hour=2, minute=0),  # Every day at 2:00 AM
    # },
    # 'hourly-task-example': {
    #     'task': 'app.tasks.another_task',
    #     'schedule': crontab(minute=0),  # Every hour at minute 0
    # },
}

if __name__ == '__main__':
    celery_app.start()

