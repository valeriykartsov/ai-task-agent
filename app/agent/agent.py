import json

from app.llm.client import LLMClient
from app.tools.tasks import create_task, list_today


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
                        "description": "Task due date",
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
]


class TaskAgent:
    def __init__(self):
        self.llm = LLMClient()

    def run(self, user_message: str, user_id: str) -> str:
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

        message = response.choices[0].message

        # if not message.tool_calls:
        #    return message.content

        if not message.tool_calls:
            return message.content

        tool_call = message.tool_calls[0]
        tool_name = tool_call.function.name

        # Диагностика
        # print("Tool called:", tool_call.function.name)
        # print("Tool arguments:", tool_call.function.arguments)

        if tool_name == "create_task":
            arguments = json.loads(tool_call.function.arguments)

            result = create_task(
                user_id=user_id,
                **arguments,
            )

            return (
                f"Task created: {result['title']}"
                + (
                    f" (due: {result['due_at']})"
                    if result.get("due_at")
                    else ""
                )
            )

        if tool_name == "list_today":
            tasks = list_today(user_id=user_id)

            if not tasks:
                return "На сегодня задач нет."

            lines = ["Твои задачи на сегодня:"]

            for task in tasks:
                lines.append(
                    f"- {task['title']} ({task['status']})"
                )

            return "\n".join(lines)

        return "Unknown tool."