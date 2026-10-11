from datetime import date, datetime, timedelta

from app.db.database import SessionLocal
from app.schemas.task import Task
from app.tools.tasks import list_today


def test_list_today():
    user_id = "test_user_list_today"
    db = SessionLocal()

    try:
        today = date.today()
        due_at = datetime.combine(today, datetime.min.time()) + timedelta(hours=12)

        task = Task(
            user_id=user_id,
            title="Тестовая задача на сегодня",
            status="pending",
            due_at=due_at,
        )

        db.add(task)
        db.commit()

        tasks = list_today(user_id)

        assert len(tasks) == 1
        assert tasks[0]["title"] == "Тестовая задача на сегодня"
        assert tasks[0]["status"] == "pending"

        print("list_today test passed:", tasks)

    finally:
        db.query(Task).filter(
            Task.user_id == user_id
        ).delete()
        db.commit()
        db.close()


if __name__ == "__main__":
    test_list_today()