from celery import Task
from app.celery_app import celery_app
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task with callbacks for logging"""
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {task_id} succeeded with result: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed with error: {exc}")


@celery_app.task(name='app.tasks.test_task')
def test_task():
    """
    Simple test task to verify Celery is working
    """
    logger.info("Running test task")
    
    return {
        'executed_at': datetime.utcnow().isoformat(),
        'status': 'success',
        'message': 'Celery is working correctly!'
    }

