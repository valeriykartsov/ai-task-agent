from datetime import datetime, timedelta

from app.db.database import SessionLocal
from app.schemas.task import Task
from app.tools.tasks import mark_reminder_sent


def test_mark_reminder_sent():
    db = SessionLocal()
    task_id = None

    try:
        # Создаём отдельную тестовую задачу с наступившим напоминанием.
        task = Task(
            user_id="test_reminders_user",
            title="Тест подтверждения отправки",
            status="pending",
            reminder_at=datetime.now() - timedelta(minutes=5),
            reminder_sent_at=None,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        task_id = task.id

        # Проверяем функцию подтверждения отправки.
        result = mark_reminder_sent(task_id)
        assert result is True

        # Проверяем, что время отправки сохранено в базе.
        db.refresh(task)
        assert task.reminder_sent_at is not None

        # Проверяем, что отправленное напоминание больше не ожидает отправки.
        from app.tools.tasks import list_pending_reminders

        pending_ids = [
            reminder["task_id"]
            for reminder in list_pending_reminders()
        ]
        assert task_id not in pending_ids

        # Проверяем обработку несуществующей задачи.
        assert mark_reminder_sent(-1) is False

        print("Mark reminder sent test passed")

    finally:
        # Удаляем только созданную тестовую задачу.
        if task_id is not None:
            test_task = db.get(Task, task_id)
            if test_task is not None:
                db.delete(test_task)
                db.commit()

        db.close()


if __name__ == "__main__":
    test_mark_reminder_sent()