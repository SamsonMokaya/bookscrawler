"""
Celery tasks for change detection

Tasks to implement:
- detect_changes: Compare current site with database
- generate_change_report: Create daily JSON/CSV report
- send_alerts: Email notifications for significant changes
"""

from app.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


# TODO: Implement change detection tasks here

