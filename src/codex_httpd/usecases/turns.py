"""Turn 系ユースケース."""

from typing import Any

from codex_httpd.usecases.ports.codex_backend import CodexBackendPort


class TurnsUseCase:
    """Turn 系 API のユースケースをまとめる."""

    def __init__(self, backend: CodexBackendPort) -> None:
        """Port 経由で Infrastructure を受け取る."""
        self._backend = backend

    async def create_turn(self, *, thread_id: str, turn_input: str, stream: bool) -> dict[str, Any]:
        """Turn 開始処理を実行する."""
        return await self._backend.start_turn(
            thread_id=thread_id,
            turn_input=turn_input,
            stream=stream,
        )
