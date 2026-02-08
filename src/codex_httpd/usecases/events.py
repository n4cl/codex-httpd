"""Streaming 系ユースケース."""

from typing import Any

from codex_httpd.usecases.ports.codex_backend import CodexBackendPort


class EventsUseCase:
    """Streaming 系 API のユースケースをまとめる."""

    def __init__(self, backend: CodexBackendPort) -> None:
        """Port 経由で Infrastructure を受け取る."""
        self._backend = backend

    async def stream_events(self, *, thread_id: str, turn_id: str) -> dict[str, Any]:
        """Turn イベント取得処理を実行する."""
        return await self._backend.stream_turn_events(thread_id=thread_id, turn_id=turn_id)
