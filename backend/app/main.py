from fastapi import FastAPI

app = FastAPI(title="Weather Advisory Support Bot")


@app.get("/health")
def health_check():
    return {"status": "ok"}