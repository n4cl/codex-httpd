"""API 層のリクエスト/レスポンススキーマ."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ThreadIdResponse(BaseModel):
    """Thread 作成/再開レスポンス."""

    thread_id: str = Field(alias="threadId")

    model_config = ConfigDict(populate_by_name=True)


class ThreadSummary(BaseModel):
    """Thread 一覧の要素."""

    thread_id: str = Field(alias="threadId")

    # Codex 由来の値を透過するため、未知項目も保持可能にする。
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ListThreadsResponse(BaseModel):
    """Thread 一覧レスポンス."""

    threads: list[ThreadSummary]
    next_cursor: str | None = Field(default=None, alias="nextCursor")

    model_config = ConfigDict(populate_by_name=True)


class ThreadDetailResponse(BaseModel):
    """Thread 詳細レスポンス."""

    thread_id: str = Field(alias="threadId")
    turns: list[dict[str, Any]] | None = None

    # thread/read の透過項目を保持する。
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class CreateTurnRequest(BaseModel):
    """Turn 作成リクエスト."""

    input: str = Field(min_length=1)
    stream: bool = False


class CreateTurnNonStreamingResponse(BaseModel):
    """非ストリーミング実行時のレスポンス."""

    turn_id: str = Field(alias="turnId")
    output: str

    model_config = ConfigDict(populate_by_name=True)


class CreateTurnStreamingResponse(BaseModel):
    """ストリーミング実行時のレスポンス."""

    turn_id: str = Field(alias="turnId")
    events_url: str = Field(alias="eventsUrl")

    model_config = ConfigDict(populate_by_name=True)


class InterruptTurnResponse(BaseModel):
    """Turn 中断レスポンス."""

    thread_id: str = Field(alias="threadId")
    turn_id: str = Field(alias="turnId")
    status: Literal["interrupting"]

    model_config = ConfigDict(populate_by_name=True)
