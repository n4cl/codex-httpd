"""Codex app-server 連携の Infrastructure 実装."""

from typing import Any

from codex_httpd.usecases.errors import FeatureNotImplementedError
from codex_httpd.usecases.ports.codex_backend import CodexBackendPort


class CodexBackendStub(CodexBackendPort):
    """3.1 時点の接続スケルトン実装."""

    def __init__(self) -> None:
        """起動状態を初期化する."""
        self.started = False

    async def startup(self) -> None:
        """起動時に接続準備を行う."""
        self.started = True

    async def shutdown(self) -> None:
        """停止時に接続を破棄する."""
        self.started = False

    async def start_thread(self) -> dict[str, Any]:
        """Thread 作成の雛形処理."""
        self._raise_not_implemented("thread/start")

    async def list_threads(
        self,
        *,
        cursor: str | None,
        limit: int | None,
        sort_key: str | None,
        source_kinds: list[str] | None,
    ) -> dict[str, Any]:
        """Thread 一覧取得の雛形処理."""
        _ = (cursor, limit, sort_key, source_kinds)
        self._raise_not_implemented("thread/list")

    async def get_thread(self, *, thread_id: str, include_turns: bool | None) -> dict[str, Any]:
        """Thread 詳細取得の雛形処理."""
        _ = (thread_id, include_turns)
        self._raise_not_implemented("thread/read")

    async def resume_thread(self, *, thread_id: str) -> dict[str, Any]:
        """Thread 再開の雛形処理."""
        _ = thread_id
        self._raise_not_implemented("thread/resume")

    async def start_turn(self, *, thread_id: str, turn_input: str, stream: bool) -> dict[str, Any]:
        """Turn 開始の雛形処理."""
        _ = (thread_id, turn_input, stream)
        self._raise_not_implemented("turn/start")

    async def stream_turn_events(self, *, thread_id: str, turn_id: str) -> dict[str, Any]:
        """Turn イベント配信の雛形処理."""
        _ = (thread_id, turn_id)
        self._raise_not_implemented("turn/events")

    async def interrupt_turn(self, *, thread_id: str, turn_id: str) -> dict[str, Any]:
        """Turn 中断の雛形処理."""
        _ = (thread_id, turn_id)
        self._raise_not_implemented("turn/interrupt")

    @staticmethod
    def _raise_not_implemented(operation: str) -> None:
        """未実装機能の共通例外を送出する."""
        raise FeatureNotImplementedError(operation=operation)
