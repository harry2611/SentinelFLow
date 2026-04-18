import time

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.entities import Base, Task
from app.db.session import engine
from app.seed.seed_data import seed_if_empty


def init_db() -> None:
    last_error = None
    for _ in range(12):
        try:
            with engine.begin() as connection:
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            Base.metadata.create_all(bind=engine)
            with Session(engine) as session:
                has_tasks = session.scalar(select(Task.id).limit(1))
                if not has_tasks:
                    seed_if_empty(session)
            return
        except Exception as exc:
            last_error = exc
            time.sleep(2)
    if last_error:
        raise last_error
