from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


# ORM-модель задачи: SQLAlchemy связывает класс с таблицей tasks в БД.
class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100))  # Владелец задачи.
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None]
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",  # Новая задача по умолчанию ожидает выполнения.
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime)  # Срок выполнения.
    reminder_at: Mapped[datetime | None] = mapped_column(DateTime)  # Время напоминания.

    # Временные метки создания и последнего обновления записи.
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )