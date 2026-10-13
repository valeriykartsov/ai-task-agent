from datetime import datetime

from app.db.database import SessionLocal
from app.schemas.task import Task
from app.tools.tasks import update_task


def test_update_task():
    user_id = "test_user_update_task"
    other_user_id = "other_user_update_task"
    db = SessionLocal()

    try:
        # Создаём задачу для проверки обновления.
        task = Task(
            user_id=user_id,
            title="Старое название",
            status="pending",
            due_at=datetime(2026, 10, 15, 14, 30),
        )

        # Создаём задачу другого пользователя для проверки доступа.
        other_task = Task(
            user_id=other_user_id,
            title="Чужая задача",
            status="pending",
        )

        db.add_all([task, other_task])
        db.commit()
        db.refresh(task)
        db.refresh(other_task)

        task_id = task.id
        other_task_id = other_task.id

        # Проверяем изменение названия, срока и статуса.
        new_due_at = "2026-10-20T10:00:00"

        result = update_task(
            task_id=task_id,
            user_id=user_id,
            title="Новое название",
            due_at=new_due_at,
            status="completed",
        )

        assert result is not None
        assert result["title"] == "Новое название"
        assert result["status"] == "completed"
        assert result["due_at"] == new_due_at

        # Проверяем, что срок можно очистить.
        result = update_task(
            task_id=task_id,
            user_id=user_id,
            clear_due_at=True,
        )

        assert result is not None
        assert result["due_at"] is None

        # Проверяем, что нельзя обновить чужую задачу.
        result = update_task(
            task_id=other_task_id,
            user_id=user_id,
            title="Попытка изменить чужую задачу",
        )

        assert result is None

        # Проверяем отказ при недопустимом статусе.
        try:
            update_task(
                task_id=task_id,
                user_id=user_id,
                status="invalid",
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid status should raise ValueError")

        # Проверяем отказ, если не передано ни одного поля.
        try:
            update_task(
                task_id=task_id,
                user_id=user_id,
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Empty update should raise ValueError")

        # Проверяем, что пустое название недопустимо.
        try:
            update_task(
                task_id=task_id,
                user_id=user_id,
                title="   ",
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Empty title should raise ValueError")

        print("update_task test passed")

    finally:
        # Удаляем тестовые данные даже при ошибке проверки.
        db.query(Task).filter(
            Task.user_id.in_([user_id, other_user_id])
        ).delete(synchronize_session=False)
        db.commit()
        db.close()


if __name__ == "__main__":
    test_update_task()