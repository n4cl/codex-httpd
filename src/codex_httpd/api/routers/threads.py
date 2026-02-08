"""Thread API のエンドポイント群."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from codex_httpd.api.dependencies import get_threads_use_case
from codex_httpd.api.schemas import ListThreadsResponse, ThreadDetailResponse, ThreadIdResponse
from codex_httpd.usecases.threads import ThreadsUseCase

router = APIRouter(prefix="/threads", tags=["threads"])
ThreadsUseCaseDep = Annotated[ThreadsUseCase, Depends(get_threads_use_case)]
CursorQuery = Annotated[str | None, Query()]
LimitQuery = Annotated[int | None, Query(ge=1)]
SortKeyQuery = Annotated[str | None, Query(alias="sortKey")]
SourceKindsQuery = Annotated[list[str] | None, Query(alias="sourceKinds")]
IncludeTurnsQuery = Annotated[bool | None, Query(alias="includeTurns")]


@router.post("")
async def create_thread(use_case: ThreadsUseCaseDep) -> ThreadIdResponse:
    """新しい Thread を作成する."""
    return await use_case.create_thread()


@router.get("")
async def list_threads(
    use_case: ThreadsUseCaseDep,
    cursor: CursorQuery = None,
    limit: LimitQuery = None,
    sort_key: SortKeyQuery = None,
    source_kinds: SourceKindsQuery = None,
) -> ListThreadsResponse:
    """Thread 一覧を取得する."""
    return await use_case.list_threads(
        cursor=cursor,
        limit=limit,
        sort_key=sort_key,
        source_kinds=source_kinds,
    )


@router.get("/{threadId}")
async def get_thread(
    threadId: str,
    use_case: ThreadsUseCaseDep,
    include_turns: IncludeTurnsQuery = None,
) -> ThreadDetailResponse:
    """Thread 詳細を取得する."""
    return await use_case.get_thread(thread_id=threadId, include_turns=include_turns)


@router.post("/{threadId}/resume")
async def resume_thread(threadId: str, use_case: ThreadsUseCaseDep) -> ThreadIdResponse:
    """既存 Thread を再開する."""
    return await use_case.resume_thread(thread_id=threadId)
