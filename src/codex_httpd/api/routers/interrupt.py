"""Interrupt API のエンドポイント群."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from codex_httpd.api.dependencies import get_interrupt_use_case
from codex_httpd.usecases.interrupt import InterruptUseCase

router = APIRouter(prefix="/threads/{thread_id}/turns/{turn_id}", tags=["interrupt"])
InterruptUseCaseDep = Annotated[InterruptUseCase, Depends(get_interrupt_use_case)]


@router.post("/interrupt")
async def interrupt_turn(
    thread_id: str,
    turn_id: str,
    use_case: InterruptUseCaseDep,
) -> dict[str, Any]:
    """実行中 Turn の中断を要求する."""
    return await use_case.interrupt_turn(thread_id=thread_id, turn_id=turn_id)
