"""Codex バックエンドとの接続 Port."""

from typing import Any, Protocol


class CodexBackendPort(Protocol):
    """UseCase 層が依存する Codex バックエンド抽象."""

    async def startup(self) -> None:
        """バックエンド接続を初期化する."""

    async def shutdown(self) -> None:
        """バックエンド接続を終了する."""

    async def start_thread(self) -> dict[str, Any]:
        """Thread 作成を実行する."""

    async def list_threads(
        self,
        *,
        cursor: str | None,
        limit: int | None,
        sort_key: str | None,
        source_kinds: list[str] | None,
    ) -> dict[str, Any]:
        """Thread 一覧取得を実行する."""

    async def get_thread(self, *, thread_id: str, include_turns: bool | None) -> dict[str, Any]:
        """Thread 詳細取得を実行する."""

    async def resume_thread(self, *, thread_id: str) -> dict[str, Any]:
        """Thread 再開を実行する."""

    async def start_turn(self, *, thread_id: str, turn_input: str, stream: bool) -> dict[str, Any]:
        """Turn 開始を実行する."""

    async def stream_turn_events(self, *, thread_id: str, turn_id: str) -> dict[str, Any]:
        """Turn イベント取得を実行する."""

    async def interrupt_turn(self, *, thread_id: str, turn_id: str) -> dict[str, Any]:
        """Turn 中断を実行する."""
