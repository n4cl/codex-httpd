"""Interrupt API のエンドポイント群."""

from typing import Annotated

from fastapi import APIRouter, Depends

from codex_httpd.api.dependencies import get_interrupt_use_case
from codex_httpd.api.schemas import InterruptTurnResponse
from codex_httpd.usecases.interrupt import InterruptUseCase

router = APIRouter(prefix="/threads/{threadId}/turns/{turnId}", tags=["interrupt"])
InterruptUseCaseDep = Annotated[InterruptUseCase, Depends(get_interrupt_use_case)]


@router.post("/interrupt")
async def interrupt_turn(
    threadId: str,
    turnId: str,
    use_case: InterruptUseCaseDep,
) -> InterruptTurnResponse:
    """実行中 Turn の中断を要求する."""
    return await use_case.interrupt_turn(thread_id=threadId, turn_id=turnId)
