import json
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from app.agent.agent import TaskAgent
from app.db.database import SessionLocal
from app.schemas.task import Task


def test_agent_update_task():
    user_id = "test_agent_update_task"
    db = SessionLocal()

    try:
        # Создаём задачу, которую агент должен обновить.
        task = Task(
            user_id=user_id,
            title="Старое название",
            status="pending",
            due_at=datetime(2026, 10, 15, 14, 30),
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        task_id = task.id

        # Имитируем вызов update_task со стороны LLM.
        tool_call = SimpleNamespace(
            function=SimpleNamespace(
                name="update_task",
                arguments=json.dumps({
                    "task_id": task_id,
                    "title": "Новое название",
                    "status": "completed",
                }),
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
                user_message="Переименуй задачу и отметь её выполненной",
                user_id=user_id,
            )

        # Проверяем ответ агента.
        assert "Задача обновлена" in result
        assert "Новое название" in result
        assert "completed" in result

        # Проверяем, что изменения действительно сохранились в БД.
        db.expire_all()
        updated_task = db.get(Task, task_id)

        assert updated_task is not None
        assert updated_task.title == "Новое название"
        assert updated_task.status == "completed"

        # Срок не должен измениться, поскольку его не передавали.
        assert updated_task.due_at == datetime(2026, 10, 15, 14, 30)

        print("Agent update_task test passed:", result)

    finally:
        # Удаляем тестовые данные.
        db.query(Task).filter(
            Task.user_id == user_id
        ).delete()
        db.commit()
        db.close()


if __name__ == "__main__":
    test_agent_update_task()