# codex-httpd

Codex CLI をバックエンドにした Codex API Server。

## ローカル開発環境セットアップ
### 前提
- Python 3.13+
- uv
- Codex CLI（導入方法は環境に合わせて選択）

### セットアップ
```bash
uv sync
```

### Codex CLI 認証
ChatGPT サインインが基本。ヘッドレス環境は device 認証を利用する。
```bash
codex login
# または
codex login --device-auth
```

API キー方式を使う場合は以下。
```bash
printenv OPENAI_API_KEY | codex login --with-api-key
```

認証情報は `~/.codex/auth.json` などに保存されるため、**機密情報として扱い、リポジトリに含めない**こと。

### 起動
```bash
uv run uvicorn codex_httpd.main:app --reload
```

### 品質チェック
```bash
uv run ruff format .
uv run ruff check .
uv run pytest -q
```

## Docker 運用（設計）
### 起動方式
- `codex app-server` と FastAPI を同一コンテナで運用する。

### 環境変数
- `CODEX_HTTPD_HOST`（任意, 既定値: `0.0.0.0`）: FastAPI の bind host
- `CODEX_HTTPD_PORT`（任意, 既定値: `8000`）: FastAPI の listen port
- `CODEX_HTTPD_LOG_LEVEL`（任意, 既定値: `info`）: API Server のログレベル
- `CODEX_HTTPD_APP_SERVER_STARTUP_TIMEOUT_SEC`（任意, 既定値: `15`）: `codex app-server` 起動待ちタイムアウト（秒）
- `CODEX_HTTPD_RPC_TIMEOUT_SEC`（任意, 既定値: `120`）: JSON-RPC 応答待ちタイムアウト（秒）
- `CODEX_BIN`（任意, 既定値: `codex`）: Codex CLI 実行バイナリ名/パス
- `CODEX_HOME`（必須, 既定値なし）: 認証情報 `auth.json` を含む Codex のホームディレクトリ

ローカルと Docker で共通化する環境変数は `.env` にまとめる運用を推奨する。
```bash
cp .env.example .env
set -a
source .env
set +a
```

`CODEX_HOME` は環境ごとに異なるため、実行時に別途指定する。
```bash
export CODEX_HOME="$HOME/.codex"
```

### 認証情報の扱い
- `CODEX_HOME/auth.json` はコンテナに read-only でマウントする。
- `auth.json` は機密情報として扱い、イメージには含めない。

### 非要件
- 本サーバーは利用者認証・独自トークン管理を行わない。

### Docker イメージ作成
```bash
docker build -t codex-httpd:latest .
```

### Docker 起動例
`~/.codex/auth.json` を read-only でマウントして起動する。
```bash
docker run --rm \
  -p 8000:8000 \
  --env-file .env \
  -e CODEX_HOME=/home/app/.codex \
  -v ~/.codex/auth.json:/home/app/.codex/auth.json:ro \
  codex-httpd:latest
```

### Codex CLI バージョン
Docker では `@openai/codex@0.98.0` に固定してインストールする（`Dockerfile` の `CODEX_CLI_VERSION`）。
