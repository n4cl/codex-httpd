"""ヘルスチェックの挙動を検証する."""

import asyncio

from httpx import ASGITransport, AsyncClient

from codex_httpd.main import app


def test_health_returns_ok() -> None:
    """/health が 200 と status を返すことを確認する."""

    async def scenario() -> None:
        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                response = await client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    asyncio.run(scenario())
