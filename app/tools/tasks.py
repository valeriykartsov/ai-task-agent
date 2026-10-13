from datetime import date, datetime, timedelta

from sqlalchemy import select

from app.db.database import SessionLocal
from app.schemas.task import Task


def create_task(
    user_id: str,
    title: str,
    due_at: str | None = None,
) -> dict:
    # Открываем сессию для работы с базой данных.
    db = SessionLocal()

    try:
        # Преобразуем строку с датой в datetime, если срок указан.
        # Если срок не передан, сохраняем None.
        parsed_due_at = (
            datetime.fromisoformat(due_at)
            if due_at
            else None
        )

        # Создаём объект задачи и указываем срок выполнения.
        task = Task(
            user_id=user_id,
            title=title,
            status="pending",
            due_at=parsed_due_at,
        )

        db.add(task)
        db.commit()  # Сохраняем новую задачу в БД.
        db.refresh(task)  # Получаем актуальные данные записи, включая ID.

        # Возвращаем данные задачи, включая срок выполнения.
        # Преобразуем дату в строку для удобной передачи агенту.
        return {
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "due_at": (
                task.due_at.isoformat()
                if task.due_at
                else None
            ),
        }

    finally:
        # Закрываем сессию даже в случае ошибки.
        db.close()


def list_today(user_id: str) -> list[dict]:
    db = SessionLocal()

    try:
        # Формируем границы текущего дня для фильтрации задач по сроку.
        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time())
        start_of_tomorrow = start_of_day + timedelta(days=1)

        # Выбираем только задачи пользователя со сроком в пределах сегодняшнего дня.
        statement = (
            select(Task)
            .where(
                Task.user_id == user_id,
                Task.due_at >= start_of_day,
                Task.due_at < start_of_tomorrow,
            )
            .order_by(Task.due_at)
        )

        tasks = db.scalars(statement).all()

        # Преобразуем ORM-объекты в словари для дальнейшей обработки агентом.
        return [
            {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "due_at": task.due_at.isoformat(),
            }
            for task in tasks
        ]

    finally:
        db.close()