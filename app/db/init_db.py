from app.db.database import Base, engine
from app.schemas.task import Task

Base.metadata.create_all(bind=engine)

print("Database initialized")