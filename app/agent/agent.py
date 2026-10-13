import json
import logging

from app.llm.client import LLMClient
from app.tools.tasks import (
    create_task,
    list_overdue,
    list_today,
    update_task,
)


# Настраиваем логгер для записи технических ошибок агента.
logger = logging.getLogger(__name__)


# Описания инструментов, которые LLM может вызвать для управления задачами.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new task",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Task title",
                    },
                    "due_at": {
                        "type": "string",
                        "description": "Task due date in ISO 8601 format",
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_today",
            "description": "List the user's tasks scheduled for today",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_overdue",
            "description": "List the user's overdue and incomplete tasks",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": (
                "Update an existing task belonging to the user. "
                "Use task_id to identify the task. "
                "Only provide fields that should change. "
                "Use clear_due_at=true to remove the due date."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "ID of the task to update",
                    },
                    "title": {
                        "type": "string",
                        "description": "New task title",
                    },
                    "due_at": {
                        "type": "string",
                        "description": "New due date in ISO 8601 format",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "completed"],
                        "description": "New task status",
                    },
                    "clear_due_at": {
                        "type": "boolean",
                        "description": "Set true to remove the due date",
                    },
                },
                "required": ["task_id"],
            },
        },
    },
]


class TaskAgent:
    def __init__(self):
        # Клиент для обращения к LLM через OpenRouter.
        self.llm = LLMClient()

    def run(self, user_message: str, user_id: str) -> str:
        # Передаём сообщение пользователя модели вместе с доступными инструментами.
        try:
            response = self.llm.client.chat.completions.create(
                model="openrouter/free",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a task management assistant. "
                            "Use tools when the user wants to manage a task."
                        ),
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    },
                ],
                tools=TOOLS,
                tool_choice="auto",
            )
        except Exception:
            # Записываем технические подробности ошибки обращения к LLM.
            logger.exception("LLM API request failed")
            return "Не удалось обработать запрос. Попробуй ещё раз."

        # Проверяем, что модель вернула хотя бы один вариант ответа.
        if not response.choices:
            logger.error("LLM returned an empty choices list")
            return "Не удалось получить ответ. Попробуй ещё раз."

        message = response.choices[0].message

        # Если инструмент не нужен, возвращаем обычный текстовый ответ модели.
        if not message.tool_calls:
            return message.content or "Не удалось сформировать ответ."

        # Берём первый вызванный инструмент и определяем действие.
        tool_call = message.tool_calls[0]
        tool_name = tool_call.function.name

        if tool_name == "create_task":
            # Преобразуем аргументы инструмента из JSON в словарь Python.
            try:
                arguments = json.loads(tool_call.function.arguments)
            except (json.JSONDecodeError, TypeError):
                logger.exception("Invalid JSON arguments for create_task")
                return "Не удалось разобрать параметры задачи. Попробуй ещё раз."

            # Проверяем структуру аргументов, полученных от модели.
            if not isinstance(arguments, dict):
                logger.warning("create_task arguments must be a JSON object")
                return "Не удалось создать задачу: неверные параметры."

            # Разрешаем только параметры, поддерживаемые функцией create_task.
            if set(arguments) - {"title", "due_at"}:
                logger.warning("Unexpected arguments for create_task")
                return "Не удалось создать задачу: неверные параметры."

            # Проверяем название задачи до обращения к базе данных.
            title = arguments.get("title")
            if not isinstance(title, str) or not title.strip():
                logger.warning("Missing or invalid task title")
                return "Не удалось создать задачу: укажи её название."

            # Проверяем тип срока выполнения, если он передан.
            due_at = arguments.get("due_at")
            if due_at is not None and not isinstance(due_at, str):
                logger.warning("Invalid due_at argument type")
                return "Не удалось создать задачу: проверь формат даты."

            # Создаём задачу от имени текущего пользователя.
            try:
                result = create_task(
                    user_id=user_id,
                    title=title.strip(),
                    due_at=due_at,
                )
            except ValueError:
                # Например, дата не соответствует формату ISO 8601.
                logger.exception("Invalid task data")
                return "Не удалось создать задачу: проверь формат даты."
            except Exception:
                # Записываем ошибки выполнения инструмента, включая ошибки БД.
                logger.exception("create_task tool failed")
                return "Не удалось создать задачу. Попробуй ещё раз."

            # Возвращаем пользователю результат создания задачи.
            return (
                f"Task created: {result['title']}"
                + (
                    f" (due: {result['due_at']})"
                    if result.get("due_at")
                    else ""
                )
            )

        if tool_name == "list_today":
            # Получаем задачи текущего пользователя, запланированные на сегодня.
            try:
                tasks = list_today(user_id=user_id)
            except Exception:
                # Записываем ошибку получения задач из базы данных.
                logger.exception("list_today tool failed")
                return "Не удалось получить задачи. Попробуй ещё раз."

            if not tasks:
                return "На сегодня задач нет."

            # Формируем читаемый список задач для ответа пользователю.
            lines = ["Твои задачи на сегодня:"]

            for task in tasks:
                lines.append(
                    f"- {task['title']} ({task['status']})"
                )

            return "\n".join(lines)

        if tool_name == "list_overdue":
            # Получаем просроченные задачи текущего пользователя.
            try:
                tasks = list_overdue(user_id=user_id)
            except Exception:
                # Записываем ошибку получения задач из базы данных.
                logger.exception("list_overdue tool failed")
                return "Не удалось получить просроченные задачи. Попробуй ещё раз."

            if not tasks:
                return "Просроченных задач нет."

            # Формируем читаемый список просроченных задач.
            lines = ["Твои просроченные задачи:"]

            for task in tasks:
                lines.append(
                    f"- {task['title']} ({task['status']}, "
                    f"срок: {task['due_at']})"
                )

            return "\n".join(lines)

        if tool_name == "update_task":
            try:
                arguments = json.loads(tool_call.function.arguments)
            except (json.JSONDecodeError, TypeError):
                logger.exception("Invalid JSON arguments for update_task")
                return "Не удалось разобрать параметры изменения задачи."

            if not isinstance(arguments, dict):
                return "Не удалось изменить задачу: неверные параметры."

            allowed_fields = {
                "task_id",
                "title",
                "due_at",
                "status",
                "clear_due_at",
            }

            if set(arguments) - allowed_fields:
                return "Не удалось изменить задачу: неверные параметры."

            task_id = arguments.get("task_id")

            if (
                isinstance(task_id, bool)
                or not isinstance(task_id, int)
                or task_id <= 0
            ):
                return "Не удалось изменить задачу: неверный ID."

            title = arguments.get("title")
            due_at = arguments.get("due_at")
            status = arguments.get("status")
            clear_due_at = arguments.get("clear_due_at", False)

            if title is not None and not isinstance(title, str):
                return "Не удалось изменить задачу: неверное название."

            if due_at is not None and not isinstance(due_at, str):
                return "Не удалось изменить задачу: неверный формат даты."

            if status is not None and status not in {"pending", "completed"}:
                return "Не удалось изменить задачу: неверный статус."

            if not isinstance(clear_due_at, bool):
                return "Не удалось изменить задачу: неверный параметр срока."

            try:
                result = update_task(
                    task_id=task_id,
                    user_id=user_id,
                    title=title,
                    due_at=due_at,
                    status=status,
                    clear_due_at=clear_due_at,
                )
            except ValueError:
                logger.exception("Invalid update_task arguments")
                return "Не удалось изменить задачу: проверь название, срок и статус."
            except Exception:
                logger.exception("update_task tool failed")
                return "Не удалось изменить задачу. Попробуй ещё раз."

            if result is None:
                return "Задача не найдена."

            return (
                f"Задача обновлена: {result['title']} "
                f"(статус: {result['status']}, "
                f"срок: {result['due_at'] or 'не указан'})."
            )

        # Записываем информацию о неизвестном инструменте.
        logger.warning("Unknown tool requested: %s", tool_name)
        return "Не удалось выполнить действие: неизвестный инструмент."
