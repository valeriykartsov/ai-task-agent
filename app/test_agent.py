from app.agent.agent import TaskAgent


agent = TaskAgent()

result = agent.run(
    user_message="Создай задачу Подготовить презентацию",
    user_id="test-user",
)

print(result)