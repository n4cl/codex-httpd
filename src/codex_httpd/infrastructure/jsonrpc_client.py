"""stdio 経由で Codex app-server と JSON-RPC を中継する."""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
from asyncio.subprocess import Process
from collections.abc import Awaitable, Callable
from contextlib import suppress
from typing import Any

from codex_httpd.usecases.errors import BackendUnavailableError, RpcProtocolError, RpcResponseError, RpcTimeoutError

logger = logging.getLogger("codex_httpd.jsonrpc")

NotificationHandler = Callable[[dict[str, Any]], bool | Awaitable[bool]]


class JsonRpcClient:
    """app-server の stdio を利用して JSON-RPC 通信を行うクライアント."""

    def __init__(
        self,
        *,
        process_getter: Callable[[], Process | None],
        timeout_sec: float = 120.0,
        notification_handler: NotificationHandler | None = None,
    ) -> None:
        """JSON-RPC クライアントの依存を初期化する."""
        self._process_getter = process_getter
        self._timeout_sec = timeout_sec
        self._notification_handler = notification_handler

        self._next_request_id = 0
        self._pending_responses: dict[int, asyncio.Future[dict[str, Any]]] = {}
        self._reader_task: asyncio.Task[None] | None = None
        self._write_lock = asyncio.Lock()
        self._stopping = False

    async def startup(self) -> None:
        """response/notification を購読する reader タスクを開始する."""
        if self._reader_task is not None and not self._reader_task.done():
            return
        self._stopping = False
        self._reader_task = asyncio.create_task(self._reader_loop(), name="codex-jsonrpc-reader")

    async def shutdown(self) -> None:
        """Reader タスクを停止し、未完了 request を失敗させる."""
        self._stopping = True
        reader_task = self._reader_task
        if reader_task is not None:
            reader_task.cancel()
            with suppress(asyncio.CancelledError):
                await reader_task
        self._reader_task = None
        self._fail_all_pending(
            BackendUnavailableError("JSON-RPC クライアントが停止したため、応答待ちを中断しました。"),
        )

    async def request(self, *, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """JSON-RPC request を送信し、`result` を返す."""
        process = self._process_getter()
        if process is None or process.stdin is None or process.stdout is None or process.returncode is not None:
            raise BackendUnavailableError()

        request_id = self._next_request_id + 1
        self._next_request_id = request_id

        loop = asyncio.get_running_loop()
        response_future: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending_responses[request_id] = response_future

        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        }
        encoded = (json.dumps(payload) + "\n").encode("utf-8")

        try:
            async with self._write_lock:
                process.stdin.write(encoded)
                await process.stdin.drain()
        except (BrokenPipeError, ConnectionResetError) as exc:
            self._pending_responses.pop(request_id, None)
            raise BackendUnavailableError() from exc

        try:
            response = await asyncio.wait_for(response_future, timeout=self._timeout_sec)
        except TimeoutError as exc:
            self._pending_responses.pop(request_id, None)
            raise RpcTimeoutError(request_id=request_id, method=method, timeout_sec=self._timeout_sec) from exc

        if "error" in response:
            error_payload = response.get("error")
            if not isinstance(error_payload, dict):
                raise RpcProtocolError(
                    "JSON-RPC error の形式が不正です。",
                    payload={"requestId": request_id, "method": method, "response": response},
                )
            raise RpcResponseError(request_id=request_id, method=method, error=error_payload)

        result = response.get("result")
        if not isinstance(result, dict):
            raise RpcProtocolError(
                "JSON-RPC result の形式が不正です。",
                payload={"requestId": request_id, "method": method, "response": response},
            )
        return result

    async def _reader_loop(self) -> None:
        """app-server から届く response/notification を継続購読する."""
        while not self._stopping:
            process = self._process_getter()
            if process is None or process.stdout is None:
                await asyncio.sleep(0.05)
                continue

            raw_line = await process.stdout.readline()
            if raw_line == b"":
                if process.returncode is not None:
                    self._fail_all_pending(BackendUnavailableError())
                await asyncio.sleep(0.05)
                continue

            try:
                payload = json.loads(raw_line.decode("utf-8"))
            except json.JSONDecodeError:
                logger.warning("invalid json message ignored payload=%s", raw_line.decode("utf-8", errors="replace").strip())
                continue

            if not isinstance(payload, dict):
                logger.warning("invalid json-rpc message ignored payload=%s", payload)
                continue

            if "id" in payload:
                self._handle_response(payload)
                continue
            if "method" in payload:
                await self._handle_notification(payload)
                continue

            logger.warning("unknown json-rpc payload ignored payload=%s", payload)

    def _handle_response(self, payload: dict[str, Any]) -> None:
        """Response を対応する request future へ解決する."""
        response_id = payload.get("id")
        if not isinstance(response_id, int):
            logger.warning("response id is not int payload=%s", payload)
            return

        future = self._pending_responses.pop(response_id, None)
        if future is None:
            logger.warning("response id does not match pending request id=%s", response_id)
            return
        if not future.done():
            future.set_result(payload)

    async def _handle_notification(self, payload: dict[str, Any]) -> None:
        """Notification を上位へ引き渡し、未知のものは警告ログを出す."""
        if self._notification_handler is None:
            logger.warning("unknown notification ignored method=%s", payload.get("method"))
            return

        handled_or_awaitable = self._notification_handler(payload)
        if inspect.isawaitable(handled_or_awaitable):
            handled = bool(await handled_or_awaitable)
        else:
            handled = bool(handled_or_awaitable)

        if not handled:
            logger.warning("unknown notification ignored method=%s", payload.get("method"))

    def _fail_all_pending(self, exc: Exception) -> None:
        """未完了 request を例外で失敗させる."""
        pending_items = list(self._pending_responses.items())
        self._pending_responses.clear()
        for _, future in pending_items:
            if not future.done():
                future.set_exception(exc)
