"""UseCase 層の共通例外."""

from typing import Any


class ApplicationError(Exception):
    """API に返却可能なアプリケーション例外."""

    status_code = 500
    code = "internal_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        """例外の公開メッセージと補足情報を保持する."""
        super().__init__(message)
        self.message = message
        self.details = details

    def to_response(self) -> dict[str, Any]:
        """HTTP エラー応答へ変換する."""
        payload: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details is not None:
            payload["details"] = self.details
        return {"error": payload}


class FeatureNotImplementedError(ApplicationError):
    """未実装機能に対する例外."""

    status_code = 501
    code = "not_implemented"

    def __init__(self, operation: str) -> None:
        """未実装の操作名を補足情報に保持する."""
        super().__init__(
            message="この操作は未実装です。",
            details={"operation": operation},
        )
