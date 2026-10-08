from fastapi import FastAPI

app = FastAPI(title="AI Task Agent")


@app.get("/health")
def health():
    return {"status": "ok"}
