FROM python:3.13-slim

ARG CODEX_CLI_VERSION=0.98.0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    CODEX_HTTPD_HOST=0.0.0.0 \
    CODEX_HTTPD_PORT=8000 \
    CODEX_HTTPD_LOG_LEVEL=info \
    CODEX_HTTPD_APP_SERVER_STARTUP_TIMEOUT_SEC=15 \
    CODEX_HTTPD_RPC_TIMEOUT_SEC=60 \
    CODEX_BIN=codex \
    CODEX_HOME=/home/app/.codex

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl nodejs npm \
    && npm install -g "@openai/codex@${CODEX_CLI_VERSION}" \
    && pip install --no-cache-dir uv \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
COPY src ./src

RUN uv sync --frozen --no-dev

RUN useradd --create-home --shell /usr/sbin/nologin app \
    && mkdir -p "${CODEX_HOME}" \
    && chown -R app:app /app "${CODEX_HOME}"

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${CODEX_HTTPD_PORT:-8000}/health" || exit 1

CMD ["sh", "-c", "uv run uvicorn codex_httpd.main:app --host ${CODEX_HTTPD_HOST:-0.0.0.0} --port ${CODEX_HTTPD_PORT:-8000} --log-level ${CODEX_HTTPD_LOG_LEVEL:-info}"]
