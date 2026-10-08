from app.tools.tasks import create_task


result = create_task(
    user_id="test-user",
    title="Подготовить README",
)

print(result)