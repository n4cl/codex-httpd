"""Turn API のエンドポイント群."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from codex_httpd.api.dependencies import get_turns_use_case
from codex_httpd.usecases.turns import TurnsUseCase

router = APIRouter(prefix="/threads/{thread_id}/turns", tags=["turns"])
TurnsUseCaseDep = Annotated[TurnsUseCase, Depends(get_turns_use_case)]


@router.post("")
async def create_turn(thread_id: str, use_case: TurnsUseCaseDep) -> dict[str, Any]:
    """指定 Thread で Turn を開始する."""
    return await use_case.create_turn(thread_id=thread_id)
