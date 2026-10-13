import os

from dotenv import load_dotenv
from openai import OpenAI

# Загружаем переменные окружения из файла .env.
load_dotenv()


class LLMClient:
    def __init__(self):
        # Получаем API-ключ; без него подключение к OpenRouter невозможно.
        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is not set")

        # Используем OpenAI SDK для обращения к API OpenRouter.
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    def chat(self, message: str) -> str:
        # Отправляем сообщение модели и получаем её текстовый ответ.
        response = self.client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {
                    "role": "user",
                    "content": message,
                }
            ],
        )

        return response.choices[0].message.content