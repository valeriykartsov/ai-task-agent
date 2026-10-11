from datetime import date, datetime, timedelta

from app.agent.agent import TaskAgent
from app.db.database import SessionLocal
from app.schemas.task import Task


def test_agent_list_today():
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

        agent = TaskAgent()

        response = agent.run(
            user_message="Какие у меня задачи на сегодня?",
            user_id=user_id,
        )

        print("Agent response:", response)

        assert "Тестовая задача на сегодня" in response

    finally:
        db.query(Task).filter(
            Task.user_id == user_id
        ).delete()
        db.commit()
        db.close()


if __name__ == "__main__":
    test_agent_list_today()