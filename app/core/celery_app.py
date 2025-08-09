from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "cliporaai",
    broker=str(settings.celery_broker_url) if settings.celery_broker_url else None,
    backend=str(settings.celery_result_backend) if settings.celery_result_backend else None,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
