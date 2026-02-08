"""API ルータの集約ポイント."""

from fastapi import APIRouter

from codex_httpd.api.routers.events import router as events_router
from codex_httpd.api.routers.interrupt import router as interrupt_router
from codex_httpd.api.routers.threads import router as threads_router
from codex_httpd.api.routers.turns import router as turns_router

api_router = APIRouter()
api_router.include_router(threads_router)
api_router.include_router(turns_router)
api_router.include_router(events_router)
api_router.include_router(interrupt_router)
