from fastapi import FastAPI

app = FastAPI(title="codex-httpd")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
