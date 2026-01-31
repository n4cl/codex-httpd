"""codex-httpd package."""

from .main import app

__all__ = ["app", "main"]


def main() -> None:
    """Run a local development server."""
    import uvicorn

    uvicorn.run("codex_httpd.main:app", host="0.0.0.0", port=8000)
