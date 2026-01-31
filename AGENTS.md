# AGENTS.md

これは codex-httpd プロジェクトです。
codex-httpd は、Codex CLI をバックエンドにした Codex API Server を提供する。

## コミットメッセージ
- ルール: [docs/commit-message.md](docs/commit-message.md)

## 技術スタック
- Python: 3.13+
- 依存管理: uv（原則 `pip install` を直接使わない）
- Lint/Format: ruff
- テスト: pytest

## 作業手順
### 共通
1. 関連ファイルを先に読む（構成を推測しない）。
2. 要求を満たす最小の変更を行う。
3. 変更内容と、実行したコマンド結果を報告する。

### 実装タスク時
- 振る舞いが変わる場合はテストを追加/更新する。
- TDD ルールに従う（`docs/tdd.md`）。VERIFY で format → lint → test を必ず実行する。
- 環境都合で実行できない場合は、原因とあわせて対応案を提案する。

## 実装タスク用コマンド
### セットアップ
- `uv sync`

### format / lint
- `uv run ruff format .`
- `uv run ruff check .`
- （必要な場合のみ自動修正）`uv run ruff check . --fix`

### テスト
- `uv run pytest -q`
- （詳細が欲しいとき）`uv run pytest -v`

## 実装タスクの依存追加
- 依存追加: `uv add <package>`
- dev依存追加: `uv add --dev <package>`
- 明示依頼がない限り、依存追加やロックファイル更新はしない

## 実装タスクのコード規約（最小）
- 新規・変更箇所は型ヒントを付ける（既存全体の一括整備はしない）。
- 既存の命名・構造・パターンを優先して合わせる。
- 「ついでの大規模リファクタ」「広範囲のリネーム」はしない。
- 秘密情報（トークン等）をコミットしない。

## ディレクトリ構成
- ソース: `src/`、テスト: `tests/`
- テストファイル命名: `tests/test_*.py`
- 仕様・設計・タスク: `docs/specs/<feature_name>/design.md` と `docs/specs/<feature_name>/task.md`

## 完了報告に含めること
- 変更概要（1〜5項目）
- 触ったファイル一覧
- 実行したコマンドと結果（成功/失敗）
