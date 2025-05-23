

import os
import sys
from celery import Celery
from app.core.config import settings

def create_celery() -> Celery:
    celery = Celery(
        "worker",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=["app.tasks"],
    )
    '''celery Intialization'''

    celery.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=50,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        task_queue_max_priority=10,
    )

    return celery

if __name__ == "__main__":
    # Add the project directory to Python path
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_dir)

    app = create_celery()
    app.start()
