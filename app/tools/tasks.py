from app.db.database import SessionLocal
from app.schemas.task import Task


def create_task(user_id: str, title: str) -> dict:
    db = SessionLocal()

    try:
        task = Task(
            user_id=user_id,
            title=title,
            status="pending",
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        return {
            "id": task.id,
            "title": task.title,
            "status": task.status,
        }

    finally:
        db.close()