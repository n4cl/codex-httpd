"""API スケルトン構成の挙動を検証する."""

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from codex_httpd.main import app


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("post", "/threads", None),
        ("get", "/threads", None),
        ("get", "/threads/thread-1", None),
        ("post", "/threads/thread-1/resume", None),
        ("post", "/threads/thread-1/turns", {"input": "hello", "stream": False}),
        ("get", "/threads/thread-1/turns/turn-1/events", None),
        ("post", "/threads/thread-1/turns/turn-1/interrupt", None),
    ],
)
def test_api_skeleton_endpoints_return_backend_unavailable(method: str, path: str, json_body: dict[str, str | bool] | None) -> None:
    """app-server 未接続時にエンドポイントが 503 を返すことを確認する."""

    async def scenario() -> None:
        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                if json_body is None:
                    response = await getattr(client, method)(path)
                else:
                    response = await getattr(client, method)(path, json=json_body)

        assert response.status_code == 503
        assert response.json()["error"]["code"] == "backend_unavailable"

    asyncio.run(scenario())


def test_lifespan_manages_infrastructure_lifecycle() -> None:
    """アプリの lifespan が Infrastructure の起動と停止を管理することを確認する."""

    async def scenario() -> None:
        async with app.router.lifespan_context(app):
            container = app.state.container
            assert container.backend.started is True

        assert container.backend.started is False

    asyncio.run(scenario())
