"""Codex app-server 連携の Infrastructure 実装."""

import os
from collections import defaultdict
from typing import Any

from codex_httpd.infrastructure.app_server_manager import AppServerProcessManager
from codex_httpd.infrastructure.jsonrpc_client import JsonRpcClient
from codex_httpd.usecases.errors import BackendUnavailableError
from codex_httpd.usecases.ports.codex_backend import CodexBackendPort


class CodexBackendStub(CodexBackendPort):
    """Codex バックエンド接続のスケルトン実装."""

    def __init__(self) -> None:
        """起動状態を初期化する."""
        self.started = False
        self._event_queues: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

        disable_app_server = os.getenv("CODEX_HTTPD_DISABLE_APP_SERVER", "").lower() in {"1", "true", "yes"}
        if disable_app_server:
            self._app_server_manager = None
            self._jsonrpc_client = None
            return

        codex_bin = os.getenv("CODEX_BIN", "codex")
        rpc_timeout_sec = float(os.getenv("CODEX_HTTPD_RPC_TIMEOUT_SEC", "120"))
        self._app_server_manager = AppServerProcessManager(command=(codex_bin, "app-server"))
        self._jsonrpc_client = JsonRpcClient(
            process_getter=self._get_app_server_process,
            timeout_sec=rpc_timeout_sec,
            notification_handler=self._handle_notification,
        )

    async def startup(self) -> None:
        """起動時に接続準備を行う."""
        if self._app_server_manager is not None:
            await self._app_server_manager.startup()
        if self._jsonrpc_client is not None:
            await self._jsonrpc_client.startup()
        self.started = True

    async def shutdown(self) -> None:
        """停止時に接続を破棄する."""
        if self._jsonrpc_client is not None:
            await self._jsonrpc_client.shutdown()
        if self._app_server_manager is not None:
            await self._app_server_manager.shutdown()
        self.started = False

    async def start_thread(self) -> dict[str, Any]:
        """Thread 作成を JSON-RPC に中継する."""
        return await self._request(method="thread/start", params={})

    async def list_threads(
        self,
        *,
        cursor: str | None,
        limit: int | None,
        sort_key: str | None,
        source_kinds: list[str] | None,
    ) -> dict[str, Any]:
        """Thread 一覧取得を JSON-RPC に中継する."""
        params = self._compact_params(
            {
                "cursor": cursor,
                "limit": limit,
                "sortKey": sort_key,
                "sourceKinds": source_kinds,
            }
        )
        return await self._request(method="thread/list", params=params)

    async def get_thread(self, *, thread_id: str, include_turns: bool | None) -> dict[str, Any]:
        """Thread 詳細取得を JSON-RPC に中継する."""
        params = self._compact_params(
            {
                "threadId": thread_id,
                "includeTurns": include_turns,
            }
        )
        return await self._request(method="thread/read", params=params)

    async def resume_thread(self, *, thread_id: str) -> dict[str, Any]:
        """Thread 再開を JSON-RPC に中継する."""
        return await self._request(method="thread/resume", params={"threadId": thread_id})

    async def start_turn(self, *, thread_id: str, turn_input: str, stream: bool) -> dict[str, Any]:
        """Turn 開始を JSON-RPC に中継する."""
        return await self._request(
            method="turn/start",
            params={
                "threadId": thread_id,
                "input": turn_input,
                "stream": stream,
            },
        )

    async def stream_turn_events(self, *, thread_id: str, turn_id: str) -> dict[str, Any]:
        """通知キューから Turn イベントを取り出す."""
        _ = self._require_client()
        key = (thread_id, turn_id)
        events = list(self._event_queues.get(key, []))
        return {"threadId": thread_id, "turnId": turn_id, "events": events}

    async def interrupt_turn(self, *, thread_id: str, turn_id: str) -> dict[str, Any]:
        """Turn 中断を JSON-RPC に中継する."""
        return await self._request(
            method="turn/interrupt",
            params={
                "threadId": thread_id,
                "turnId": turn_id,
            },
        )

    async def _request(self, *, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """JSON-RPC request を送信して result を返す."""
        client = self._require_client()
        return await client.request(method=method, params=params)

    def _require_client(self) -> JsonRpcClient:
        """利用可能な JSON-RPC クライアントを返す."""
        if self._jsonrpc_client is None:
            raise BackendUnavailableError()
        return self._jsonrpc_client

    def _get_app_server_process(self):
        """現在の app-server プロセスを返す."""
        if self._app_server_manager is None:
            return None
        return self._app_server_manager.process

    async def _handle_notification(self, payload: dict[str, Any]) -> bool:
        """既知 notification を threadId/turnId 単位でキューへ振り分ける."""
        method = payload.get("method")
        if method not in {"agent_message_delta", "turn/completed", "error"}:
            return False

        params = payload.get("params")
        thread_id = self._find_first_string(params, "threadId")
        turn_id = self._find_first_string(params, "turnId")
        if thread_id is None or turn_id is None:
            return True

        self._event_queues[(thread_id, turn_id)].append(payload)
        return True

    @staticmethod
    def _find_first_string(payload: Any, key: str) -> str | None:
        """ネスト構造から最初に見つかった文字列値を返す."""
        if isinstance(payload, dict):
            value = payload.get(key)
            if isinstance(value, str):
                return value
            for nested in payload.values():
                found = CodexBackendStub._find_first_string(nested, key)
                if found is not None:
                    return found
            return None
        if isinstance(payload, list):
            for item in payload:
                found = CodexBackendStub._find_first_string(item, key)
                if found is not None:
                    return found
            return None
        return None

    @staticmethod
    def _compact_params(params: dict[str, Any]) -> dict[str, Any]:
        """`None` の項目を除いた JSON-RPC パラメータを返す."""
        return {key: value for key, value in params.items() if value is not None}
