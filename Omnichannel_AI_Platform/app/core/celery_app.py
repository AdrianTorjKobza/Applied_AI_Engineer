from celery import Celery
from app.core.config import settings

# Initialize Celery and configure it to use Redis as the broker and backend
celery = Celery(
    "ai_platform_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.worker.tasks']
)

# Optional configuration for task routing or retries can be added here
celery.conf.task_routes = {'app.worker.tasks.*': {'queue': 'ai_tasks'}}