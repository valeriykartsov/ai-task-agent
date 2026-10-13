import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from app.agent.agent import TaskAgent
from app.tools.tasks import list_pending_reminders, mark_reminder_sent


# Создаём FastAPI-приложение с названием AI Task Agent.
app = FastAPI(title="AI Task Agent")

# Создаём агента для обработки запросов пользователя.
agent = TaskAgent()

# Проверяем токен для доступа к внутренним API.
def verify_api_token(x_api_token: str = Header(default="")):
    expected_token = os.getenv("API_TOKEN", "")

    if not expected_token or not secrets.compare_digest(
        x_api_token,
        expected_token,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API token",
        )


# Схема входящего сообщения пользователя.
class ChatRequest(BaseModel):
    user_id: str
    message: str


# Healthcheck: проверяет, что приложение запущено и отвечает на HTTP-запросы.
@app.get("/health")
def health():
    return {"status": "ok"}


# Принимаем сообщение пользователя и передаём его агенту.
@app.post("/chat")
def chat(
    request: ChatRequest,
    _: None = Depends(verify_api_token),
):
    response = agent.run(
        user_message=request.message,
        user_id=request.user_id,
    )

    return {"response": response}


# Возвращаем напоминания, время которых наступило.
@app.get("/reminders/pending")
def get_pending_reminders(
    _: None = Depends(verify_api_token),
):
    reminders = list_pending_reminders()
    return {"reminders": reminders}


# Отмечаем напоминание отправленным после доставки в Telegram.
@app.post("/reminders/{task_id}/sent")
def confirm_reminder_sent(
    task_id: int,
    _: None = Depends(verify_api_token),
):
    marked = mark_reminder_sent(task_id)

    if not marked:
        return {"error": "Task not found"}

    return {"status": "sent", "task_id": task_id}
