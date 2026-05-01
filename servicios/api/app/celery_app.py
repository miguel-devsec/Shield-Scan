from celery import Celery
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery("shieldscan", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.task_routes = {"perform_audit": {"queue": "audits"}}
