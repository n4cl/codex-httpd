"""API 共通の例外ハンドリングを提供する."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from codex_httpd.usecases.errors import ApplicationError

logger = logging.getLogger("codex_httpd.error")


def install_exception_handlers(app: FastAPI) -> None:
    """FastAPI に共通例外ハンドラーを登録する."""

    @app.exception_handler(ApplicationError)
    async def handle_application_error(request: Request, exc: ApplicationError) -> JSONResponse:
        logger.warning("application error method=%s path=%s code=%s", request.method, request.url.path, exc.code)
        return JSONResponse(status_code=exc.status_code, content=exc.to_response())

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unexpected error method=%s path=%s", request.method, request.url.path, exc_info=exc)
        internal_error = ApplicationError(message="内部エラーが発生しました。")
        return JSONResponse(status_code=internal_error.status_code, content=internal_error.to_response())
