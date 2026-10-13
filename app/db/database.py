import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Загружаем переменные окружения, включая строку подключения к БД.
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Создаём движок SQLAlchemy для взаимодействия с базой данных.
engine = create_engine(DATABASE_URL)

# Фабрика сессий: через неё код открывает сессии для работы с БД.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# Базовый класс для ORM-моделей, чьи таблицы отслеживает SQLAlchemy.
class Base(DeclarativeBase):
    pass


from app.schemas.task import Task

# Создаём таблицы, описанные в зарегистрированных ORM-моделях, если их ещё нет.
Base.metadata.create_all(bind=engine)