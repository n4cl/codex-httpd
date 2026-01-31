"""codex-httpd の FastAPI エントリポイント."""

from fastapi import FastAPI

app = FastAPI(title="codex-httpd")


@app.get("/health")
def health() -> dict[str, str]:
    """ヘルスチェックの状態を返す."""
    return {"status": "ok"}
