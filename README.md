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
