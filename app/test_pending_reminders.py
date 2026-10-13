from datetime import datetime, timedelta

from app.db.database import SessionLocal
from app.schemas.task import Task
from app.tools.tasks import list_pending_reminders


def test_list_pending_reminders():
    db = SessionLocal()
    test_user_id = "test_reminders_user"

    try:
        # Создаём напоминание, время которого уже наступило.
        task = Task(
            user_id=test_user_id,
            title="Тестовое напоминание",
            status="pending",
            reminder_at=datetime.now() - timedelta(minutes=5),
            reminder_sent_at=None,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        task_id = task.id

        # Проверяем, что напоминание попало в выборку.
        reminders = list_pending_reminders()
        reminder_ids = [reminder["task_id"] for reminder in reminders]

        assert task_id in reminder_ids

        reminder = next(
            item for item in reminders
            if item["task_id"] == task_id
        )

        assert reminder["user_id"] == test_user_id
        assert reminder["title"] == "Тестовое напоминание"

        print("Pending reminders test passed:", reminder)

    finally:
        # Удаляем тестовую запись, чтобы она не мешала следующим проверкам.
        if "task_id" in locals():
            test_task = db.get(Task, task_id)
            if test_task is not None:
                db.delete(test_task)
                db.commit()

        db.close()


if __name__ == "__main__":
    test_list_pending_reminders()