from datetime import date, datetime, timedelta

from sqlalchemy import select

from app.db.database import SessionLocal
from app.schemas.task import Task


def create_task(
    user_id: str,
    title: str,
    due_at: str | None = None,
    reminder_at: str | None = None,
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

        # Преобразуем время напоминания в datetime, если оно указано.
        parsed_reminder_at = (
            datetime.fromisoformat(reminder_at)
            if reminder_at
            else None
        )

        # Создаём объект задачи и указываем срок выполнения.
        task = Task(
            user_id=user_id,
            title=title,
            status="pending",
            due_at=parsed_due_at,
            reminder_at=parsed_reminder_at,
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
            "reminder_at": (
                task.reminder_at.isoformat()
                if task.reminder_at
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


def list_overdue(user_id: str) -> list[dict]:
    # Открываем сессию для работы с базой данных.
    db = SessionLocal()

    try:
        # Получаем текущую дату и время для определения просроченных задач.
        now = datetime.now()

        # Выбираем просроченные невыполненные задачи конкретного пользователя.
        statement = (
            select(Task)
            .where(
                Task.user_id == user_id,
                Task.due_at < now,
                Task.status != "completed",
            )
            .order_by(Task.due_at)
        )

        tasks = db.scalars(statement).all()

        # Преобразуем ORM-объекты в словари для передачи агенту.
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
        # Закрываем сессию даже в случае ошибки.
        db.close()


def update_task(
    task_id: int,
    user_id: str,
    title: str | None = None,
    due_at: str | None = None,
    status: str | None = None,
    clear_due_at: bool = False,
    reminder_at: str | None = None,
    clear_reminder_at: bool = False,
) -> dict | None:
    # Обновить существующую задачу, принадлежащую указанному пользователю.
    db = SessionLocal()

    try:
        task = db.scalar(
            select(Task).where(
                Task.id == task_id,
                Task.user_id == user_id,
            )
        )

        if task is None:
            return None

        if title is not None:
            if not isinstance(title, str) or not title.strip():
                raise ValueError("Task title cannot be empty")

            task.title = title.strip()

        # Нельзя одновременно задать и удалить напоминание.
        if clear_reminder_at and reminder_at is not None:
            raise ValueError(
                "reminder_at and clear_reminder_at cannot be used together"
            )

        if clear_reminder_at:
            task.reminder_at = None
            task.reminder_sent_at = None
        elif reminder_at is not None:
            task.reminder_at = datetime.fromisoformat(reminder_at)
            # Новое время требует новой отправки напоминания.
            task.reminder_sent_at = None

        if clear_due_at:
            task.due_at = None
        elif due_at is not None:
            task.due_at = datetime.fromisoformat(due_at)

        if status is not None:
            if status not in {"pending", "completed"}:
                raise ValueError("Invalid task status")

            task.status = status

        if (
            title is None
            and due_at is None
            and status is None
            and not clear_due_at
            and reminder_at is None
            and not clear_reminder_at
        ):
            raise ValueError("No fields provided for update")

        db.commit()
        db.refresh(task)

        return {
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "due_at": (
                task.due_at.isoformat()
                if task.due_at
                else None
            ),
            "reminder_at": (
                task.reminder_at.isoformat()
                if task.reminder_at
                else None
            ),
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def list_pending_reminders(limit: int = 100) -> list[dict]:
    # Открываем сессию для работы с базой данных.
    db = SessionLocal()

    try:
        # Получаем текущее время для поиска наступивших напоминаний.
        now = datetime.now()

        # Выбираем напоминания, которые пора отправить и ещё не отправляли.
        statement = (
            select(Task)
            .where(
                Task.reminder_at <= now,
                Task.reminder_sent_at.is_(None),
                Task.status != "completed",
            )
            .order_by(Task.reminder_at)
            .limit(limit)
        )

        tasks = db.scalars(statement).all()

        # Возвращаем данные, необходимые для доставки напоминаний.
        return [
            {
                "task_id": task.id,
                "user_id": task.user_id,
                "title": task.title,
                "reminder_at": task.reminder_at.isoformat(),
            }
            for task in tasks
        ]

    finally:
        # Закрываем сессию даже в случае ошибки.
        db.close()


def mark_reminder_sent(task_id: int) -> bool:
    # Открываем сессию для работы с базой данных.
    db = SessionLocal()

    try:
        # Находим задачу по ID.
        task = db.get(Task, task_id)

        # Если задача не найдена, подтверждать отправку нечего.
        if task is None:
            return False

        # Фиксируем время успешной отправки напоминания.
        task.reminder_sent_at = datetime.now()

        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
