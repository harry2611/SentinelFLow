from redis import Redis
from rq import Connection, Worker

from app.core.config import get_settings
from app.services.queue_service import QUEUE_NAME


def main() -> None:
    settings = get_settings()
    redis_connection = Redis.from_url(settings.redis_url)
    with Connection(redis_connection):
        worker = Worker([QUEUE_NAME])
        worker.work()


if __name__ == "__main__":
    main()

