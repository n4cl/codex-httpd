"""Turn API のエンドポイント群."""

from typing import Annotated

from fastapi import APIRouter, Depends

from codex_httpd.api.dependencies import get_turns_use_case
from codex_httpd.api.schemas import CreateTurnNonStreamingResponse, CreateTurnRequest, CreateTurnStreamingResponse
from codex_httpd.usecases.turns import TurnsUseCase

router = APIRouter(prefix="/threads/{threadId}/turns", tags=["turns"])
TurnsUseCaseDep = Annotated[TurnsUseCase, Depends(get_turns_use_case)]


@router.post("")
async def create_turn(
    threadId: str,
    request: CreateTurnRequest,
    use_case: TurnsUseCaseDep,
) -> CreateTurnNonStreamingResponse | CreateTurnStreamingResponse:
    """指定 Thread で Turn を開始する."""
    return await use_case.create_turn(
        thread_id=threadId,
        turn_input=request.input,
        stream=request.stream,
    )
