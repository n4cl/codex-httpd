"""API スキーマ契約の挙動を検証する."""

from fastapi.testclient import TestClient

from codex_httpd.main import app


def test_create_turn_requires_input_field() -> None:
    """Turn 作成時に input が必須であることを確認する."""
    with TestClient(app) as client:
        response = client.post("/threads/thread-1/turns", json={"stream": False})

    assert response.status_code == 422


def test_openapi_defines_thread_list_query_params() -> None:
    """Thread 一覧 API のクエリパラメータが OpenAPI に定義されることを確認する."""
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    params = schema["paths"]["/threads"]["get"]["parameters"]
    param_names = {param["name"] for param in params}
    assert {"cursor", "limit", "sortKey", "sourceKinds"} <= param_names


def test_openapi_defines_thread_read_query_param() -> None:
    """Thread 詳細 API の includeTurns が OpenAPI に定義されることを確認する."""
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    params = schema["paths"]["/threads/{threadId}"]["get"]["parameters"]
    param_names = {param["name"] for param in params}
    assert "includeTurns" in param_names


def test_openapi_defines_turn_create_request_and_response() -> None:
    """Turn 作成 API の入出力スキーマが OpenAPI に定義されることを確認する."""
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    post_op = schema["paths"]["/threads/{threadId}/turns"]["post"]
    body_schema = post_op["requestBody"]["content"]["application/json"]["schema"]
    assert body_schema["$ref"] == "#/components/schemas/CreateTurnRequest"

    response_schema = post_op["responses"]["200"]["content"]["application/json"]["schema"]
    refs = {entry["$ref"] for entry in response_schema["anyOf"]}
    assert refs == {
        "#/components/schemas/CreateTurnStreamingResponse",
        "#/components/schemas/CreateTurnNonStreamingResponse",
    }
