import json
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from app.agent.agent import TaskAgent
from app.db.database import SessionLocal
from app.schemas.task import Task


def test_agent_list_overdue():
    user_id = "test_agent_list_overdue"
    db = SessionLocal()

    try:
        # Создаём просроченную задачу для тестового пользователя.
        task = Task(
            user_id=user_id,
            title="Просрочить оплату счёта",
            status="pending",
            due_at=datetime.now() - timedelta(days=1),
        )

        db.add(task)
        db.commit()

        # Имитируем вызов инструмента list_overdue со стороны LLM.
        tool_call = SimpleNamespace(
            function=SimpleNamespace(
                name="list_overdue",
                arguments=json.dumps({}),
            )
        )
        message = SimpleNamespace(
            tool_calls=[tool_call],
            content=None,
        )
        response = SimpleNamespace(
            choices=[
                SimpleNamespace(message=message),
            ]
        )

        agent = TaskAgent()

        with patch.object(
            agent.llm.client.chat.completions,
            "create",
            return_value=response,
        ):
            result = agent.run(
                user_message="Какие у меня просроченные задачи?",
                user_id=user_id,
            )

        # Проверяем, что агент вызвал инструмент и вернул задачу.
        assert "Твои просроченные задачи:" in result
        assert "Просрочить оплату счёта" in result

        print("Agent list_overdue test passed:", result)

    finally:
        # Удаляем тестовые данные.
        db.query(Task).filter(
            Task.user_id == user_id
        ).delete()
        db.commit()
        db.close()


if __name__ == "__main__":
    test_agent_list_overdue()