
from datetime import datetime

from app.tools.tasks import create_task
from app.db.database import SessionLocal
from app.schemas.task import Task


def test_create_task_with_due_date():
    user_id = "test_user_due_date"
    title = "Тест задачи со сроком"
    due_at = "2026-10-15T14:30:00"

    try:
        # Создаём задачу со сроком выполнения.
        result = create_task(
            user_id=user_id,
            title=title,
            due_at=due_at,
        )

        # Проверяем, что срок вернулся в результате.
        assert result["due_at"] == due_at

        # Проверяем, что срок действительно сохранился в БД.
        db = SessionLocal()
        try:
            task = db.get(Task, result["id"])

            assert task is not None
            assert task.due_at == datetime.fromisoformat(due_at)

        finally:
            db.close()

        print("Create task with due date test passed:", result)

    finally:
        # Удаляем тестовые данные после проверки.
        db = SessionLocal()
        try:
            db.query(Task).filter(
                Task.user_id == user_id
            ).delete()
            db.commit()
        finally:
            db.close()


if __name__ == "__main__":
    test_create_task_with_due_date()
