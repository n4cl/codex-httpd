"""codex-httpd の FastAPI エントリポイント."""

import logging
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request, Response

from codex_httpd.api.error_handlers import install_exception_handlers
from codex_httpd.api.router import api_router
from codex_httpd.app_container import build_container

logger = logging.getLogger("codex_httpd.request")


def configure_logging() -> None:
    """アプリ共通のログ出力形式を設定する."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリの起動時と停止時に依存オブジェクトを管理する."""
    configure_logging()
    container = build_container()
    app.state.container = container
    await container.startup()
    try:
        yield
    finally:
        await container.shutdown()


app = FastAPI(title="codex-httpd", lifespan=lifespan)
install_exception_handlers(app)
app.include_router(api_router)


@app.middleware("http")
async def log_request_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """HTTP リクエストの共通ログを出力する."""
    started_at = perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (perf_counter() - started_at) * 1000
        logger.exception(
            "request failed method=%s path=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = (perf_counter() - started_at) * 1000
    logger.info(
        "request completed method=%s path=%s status=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    """ヘルスチェックの状態を返す."""
    return {"status": "ok"}
