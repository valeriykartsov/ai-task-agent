from datetime import datetime, timedelta

from app.db.database import SessionLocal
from app.schemas.task import Task
from app.tools.tasks import list_overdue


def test_list_overdue():
    user_id = "test_user_list_overdue"
    db = SessionLocal()

    try:
        # Создаём просроченную задачу.
        overdue_task = Task(
            user_id=user_id,
            title="Просроченная задача",
            status="pending",
            due_at=datetime.now() - timedelta(days=1),
        )

        # Создаём задачу со сроком в будущем.
        future_task = Task(
            user_id=user_id,
            title="Будущая задача",
            status="pending",
            due_at=datetime.now() + timedelta(days=1),
        )

        # Создаём просроченную, но уже выполненную задачу.
        completed_task = Task(
            user_id=user_id,
            title="Выполненная задача",
            status="completed",
            due_at=datetime.now() - timedelta(days=2),
        )

        # Создаём задачу без срока выполнения.
        no_due_date_task = Task(
            user_id=user_id,
            title="Задача без срока",
            status="pending",
            due_at=None,
        )

        db.add_all([
            overdue_task,
            future_task,
            completed_task,
            no_due_date_task,
        ])
        db.commit()

        # Получаем просроченные задачи пользователя.
        tasks = list_overdue(user_id)

        # В результате должна остаться только невыполненная просроченная задача.
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Просроченная задача"
        assert tasks[0]["status"] == "pending"

        print("list_overdue test passed:", tasks)

    finally:
        # Удаляем тестовые данные, чтобы они не мешали другим тестам.
        db.query(Task).filter(
            Task.user_id == user_id
        ).delete()
        db.commit()
        db.close()


if __name__ == "__main__":
    test_list_overdue()