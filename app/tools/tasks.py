from datetime import date, datetime, timedelta

from sqlalchemy import select

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


def list_today(user_id: str) -> list[dict]:
    db = SessionLocal()

    try:
        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time())
        start_of_tomorrow = start_of_day + timedelta(days=1)

        statement = (
            select(Task)
            .where(
                Task.user_id == user_id,
                Task.due_at >= start_of_day,
                Task.due_at < start_of_tomorrow,
            )
            .order_by(Task.due_at)
        )

        tasks = db.scalars(statement).all()

        return [
            {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "due_at": task.due_at.isoformat(),
            }
            for task in tasks
        ]

    finally:
        db.close()