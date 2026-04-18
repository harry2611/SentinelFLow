from __future__ import annotations

from redis import Redis
from rq import Queue

from app.core.config import get_settings
from app.orchestration.pipeline import process_task_job


QUEUE_NAME = "sentinelflow"


def get_queue() -> Queue:
    settings = get_settings()
    redis_connection = Redis.from_url(settings.redis_url)
    return Queue(name=QUEUE_NAME, connection=redis_connection)


def enqueue_task(task_id: str, start_stage: str = "decision") -> dict:
    try:
        queue = get_queue()
        job = queue.enqueue(process_task_job, task_id, start_stage, job_timeout=180)
        return {"queued": True, "job_id": job.id}
    except Exception:
        process_task_job(task_id, start_stage)
        return {"queued": False, "job_id": None}

