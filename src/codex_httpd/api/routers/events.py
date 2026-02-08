"""Streaming API のエンドポイント群."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from codex_httpd.api.dependencies import get_events_use_case
from codex_httpd.usecases.events import EventsUseCase

router = APIRouter(prefix="/threads/{threadId}/turns/{turnId}", tags=["events"])
EventsUseCaseDep = Annotated[EventsUseCase, Depends(get_events_use_case)]


@router.get(
    "/events",
    responses={
        200: {
            "description": "SSE イベントストリーム",
            "content": {
                "text/event-stream": {
                    "schema": {"type": "string"},
                }
            },
        }
    },
)
async def stream_events(
    threadId: str,
    turnId: str,
    use_case: EventsUseCaseDep,
) -> dict[str, Any]:
    """指定 Turn のイベントストリームを取得する."""
    return await use_case.stream_events(thread_id=threadId, turn_id=turnId)
