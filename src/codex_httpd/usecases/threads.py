"""Thread 系ユースケース."""

from typing import Any

from codex_httpd.usecases.errors import RpcProtocolError
from codex_httpd.usecases.ports.codex_backend import CodexBackendPort


class ThreadsUseCase:
    """Thread 系 API のユースケースをまとめる."""

    def __init__(self, backend: CodexBackendPort) -> None:
        """Port 経由で Infrastructure を受け取る."""
        self._backend = backend

    async def create_thread(self) -> dict[str, Any]:
        """Thread 作成処理を実行する."""
        result = await self._backend.start_thread()
        thread_id = self._extract_thread_id(result=result, method="thread/start")
        return {"threadId": thread_id}

    async def list_threads(
        self,
        *,
        cursor: str | None,
        limit: int | None,
        sort_key: str | None,
        source_kinds: list[str] | None,
    ) -> dict[str, Any]:
        """Thread 一覧取得処理を実行する."""
        return await self._backend.list_threads(
            cursor=cursor,
            limit=limit,
            sort_key=sort_key,
            source_kinds=source_kinds,
        )

    async def get_thread(self, *, thread_id: str, include_turns: bool | None) -> dict[str, Any]:
        """Thread 詳細取得処理を実行する."""
        return await self._backend.get_thread(thread_id=thread_id, include_turns=include_turns)

    async def resume_thread(self, *, thread_id: str) -> dict[str, Any]:
        """Thread 再開処理を実行する."""
        return await self._backend.resume_thread(thread_id=thread_id)

    @staticmethod
    def _extract_thread_id(*, result: dict[str, Any], method: str) -> str:
        """Codex 応答から threadId を抽出する."""
        direct_thread_id = result.get("threadId")
        if isinstance(direct_thread_id, str):
            return direct_thread_id

        thread_payload = result.get("thread")
        if isinstance(thread_payload, dict):
            nested_thread_id = thread_payload.get("id")
            if isinstance(nested_thread_id, str):
                return nested_thread_id

        raise RpcProtocolError(
            "threadId を含むレスポンス形式ではありません。",
            payload={"method": method, "result": result},
        )
