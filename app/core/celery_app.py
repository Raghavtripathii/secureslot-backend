from celery import Celery
from app.core.config import settings

celery_app = Celery("secureslot", broker=settings.redis_url, backend=settings.redis_url)

from app.services import notifications  # noqa: E402,F401 — registers tasks with this worker