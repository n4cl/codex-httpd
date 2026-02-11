"""Thread 作成 API の挙動を検証する."""

import asyncio
import importlib
from typing import Any

from httpx import ASGITransport, AsyncClient

from codex_httpd.app_container import AppContainer

main_module = importlib.import_module("codex_httpd.main")
app = main_module.app


class _FakeBackend:
    """Thread 作成 API テスト向けの最小バックエンド実装."""

    def __init__(self, start_thread_result: dict[str, Any]) -> None:
        """返却する `thread/start` 結果を保持する."""
        self._start_thread_result = start_thread_result
        self.start_thread_calls = 0

    async def startup(self) -> None:
        """テストでは起動処理を行わない."""

    async def shutdown(self) -> None:
        """テストでは停止処理を行わない."""

    async def start_thread(self) -> dict[str, Any]:
        """`thread/start` 呼び出しを記録して結果を返す."""
        self.start_thread_calls += 1
        return self._start_thread_result


def test_create_thread_returns_thread_id_from_thread_start_result(monkeypatch) -> None:
    """`thread/start` の `thread.id` を `threadId` として返すことを確認する."""
    backend = _FakeBackend(start_thread_result={"thread": {"id": "thread-123"}})
    container = AppContainer(backend=backend)  # type: ignore[arg-type]
    monkeypatch.setattr(main_module, "build_container", lambda: container)

    async def scenario() -> None:
        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                response = await client.post("/threads")

        assert response.status_code == 200
        assert response.json() == {"threadId": "thread-123"}
        assert backend.start_thread_calls == 1

    asyncio.run(scenario())


def test_create_thread_returns_502_when_thread_start_result_is_invalid(monkeypatch) -> None:
    """`thread/start` 結果が不正な場合に 502 を返すことを確認する."""
    backend = _FakeBackend(start_thread_result={"thread": {}})
    container = AppContainer(backend=backend)  # type: ignore[arg-type]
    monkeypatch.setattr(main_module, "build_container", lambda: container)

    async def scenario() -> None:
        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                response = await client.post("/threads")

        assert response.status_code == 502
        assert response.json()["error"]["code"] == "rpc_protocol_error"
        assert response.json()["error"]["details"]["method"] == "thread/start"
        assert backend.start_thread_calls == 1

    asyncio.run(scenario())
