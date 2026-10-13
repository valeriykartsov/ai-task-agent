from fastapi import FastAPI

# Создаём FastAPI-приложение с названием AI Task Agent.
app = FastAPI(title="AI Task Agent")


# Healthcheck: проверяет, что приложение запущено и отвечает на HTTP-запросы.
@app.get("/health")
def health():
    return {"status": "ok"}