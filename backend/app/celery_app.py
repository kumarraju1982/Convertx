"""
Celery application instance for asynchronous task processing.

This module configures and initializes the Celery application with Redis
as the message broker and result backend.
"""

from celery import Celery
from celery.schedules import crontab
from app.config import Config, get_config


def create_celery_app(config: Config = None) -> Celery:
    """
    Create and configure a Celery application instance.
    
    Args:
        config: Configuration object. If None, uses default config.
        
    Returns:
        Celery: Configured Celery application instance
    """
    if config is None:
        config = get_config()
    
    # Create Celery instance
    celery_app = Celery('pdf_converter')
    
    # Get Redis URL with password support
    redis_url = config.get_redis_url()
    
    # Configure Celery with Redis broker and result backend
    celery_app.conf.update(
        # Broker and Result Backend
        broker_url=redis_url,
        result_backend=redis_url,
        
        # Task Serialization
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        
        # Result Expiration
        result_expires=86400,  # 24 hours in seconds
        
        # Task Execution
        task_track_started=True,
        task_time_limit=3600,  # 1 hour max per task
        task_soft_time_limit=3300,  # 55 minutes soft limit
        
        # Connection Settings
        broker_connection_retry_on_startup=True,
        broker_connection_retry=True,
        broker_connection_max_retries=10,
        
        # Result Backend Settings
        result_backend_transport_options={
            'master_name': 'mymaster',
        },
        
        # Worker Settings
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        
        # Timezone
        timezone='UTC',
        enable_utc=True,
        
        # Periodic Tasks (Beat Schedule)
        beat_schedule={
            'cleanup-old-files': {
                'task': 'app.tasks.cleanup_old_files_task',
                'schedule': crontab(minute=0),  # Run every hour at minute 0
                'args': (24,)  # Delete files older than 24 hours
            },
        },
    )
    
    # Auto-discover tasks from app.tasks module
    celery_app.autodiscover_tasks(['app'])
    
    return celery_app


# Create the default Celery app instance
celery_app = create_celery_app()
