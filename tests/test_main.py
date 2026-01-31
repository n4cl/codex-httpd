"""ヘルスチェックの挙動を検証する."""

from fastapi.testclient import TestClient

from codex_httpd.main import app


def test_health_returns_ok() -> None:
    """/health が 200 と status を返すことを確認する."""
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
