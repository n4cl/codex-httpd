"""Thread API のエンドポイント群."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from codex_httpd.api.dependencies import get_threads_use_case
from codex_httpd.usecases.threads import ThreadsUseCase

router = APIRouter(prefix="/threads", tags=["threads"])
ThreadsUseCaseDep = Annotated[ThreadsUseCase, Depends(get_threads_use_case)]


@router.post("")
async def create_thread(use_case: ThreadsUseCaseDep) -> dict[str, Any]:
    """新しい Thread を作成する."""
    return await use_case.create_thread()


@router.get("")
async def list_threads(use_case: ThreadsUseCaseDep) -> dict[str, Any]:
    """Thread 一覧を取得する."""
    return await use_case.list_threads()


@router.get("/{thread_id}")
async def get_thread(thread_id: str, use_case: ThreadsUseCaseDep) -> dict[str, Any]:
    """Thread 詳細を取得する."""
    return await use_case.get_thread(thread_id=thread_id)


@router.post("/{thread_id}/resume")
async def resume_thread(thread_id: str, use_case: ThreadsUseCaseDep) -> dict[str, Any]:
    """既存 Thread を再開する."""
    return await use_case.resume_thread(thread_id=thread_id)
