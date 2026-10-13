from unittest.mock import patch

from app.main import ChatRequest, chat


# Проверяем, что API передаёт сообщение агенту и возвращает его ответ.
def test_chat_returns_agent_response():
    with patch(
        "app.main.agent.run",
        return_value="Тестовый ответ",
    ) as mock_run:
        result = chat(
            ChatRequest(
                user_id="test-user",
                message="Привет",
            )
        )

    assert result == {"response": "Тестовый ответ"}

    mock_run.assert_called_once_with(
        user_message="Привет",
        user_id="test-user",
    )

    print("test_chat_returns_agent_response: OK")


if __name__ == "__main__":
    test_chat_returns_agent_response()