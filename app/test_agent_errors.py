from types import SimpleNamespace
from unittest.mock import patch

from app.agent.agent import TaskAgent


def test_llm_api_error():
    # Создаём агента.
    agent = TaskAgent()

    # Имитируем сбой при обращении к LLM API.
    with patch.object(
        agent.llm.client.chat.completions,
        "create",
        side_effect=RuntimeError("Simulated API failure"),
    ):
        response = agent.run(
            user_message="Создай задачу",
            user_id="test_user_errors",
        )

    # Проверяем, что агент вернул понятное сообщение.
    assert response == "Не удалось обработать запрос. Попробуй ещё раз."

    print("LLM API error test passed:", response)


def test_invalid_tool_json():
    # Создаём агента.
    agent = TaskAgent()

    # Имитируем вызов инструмента с некорректным JSON.
    fake_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    tool_calls=[
                        SimpleNamespace(
                            function=SimpleNamespace(
                                name="create_task",
                                arguments='{"title": ',
                            )
                        )
                    ]
                )
            )
        ]
    )

    with patch.object(
        agent.llm.client.chat.completions,
        "create",
        return_value=fake_response,
    ):
        response = agent.run(
            user_message="Создай задачу",
            user_id="test_user_errors",
        )

    # Проверяем, что агент обработал ошибку без необработанного исключения.
    assert response == (
        "Не удалось разобрать параметры задачи. Попробуй ещё раз."
    )

    print("Invalid tool JSON test passed:", response)


if __name__ == "__main__":
    test_llm_api_error()
    test_invalid_tool_json()