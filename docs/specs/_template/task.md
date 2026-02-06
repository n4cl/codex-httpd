# Task（実装タスク）

このドキュメントは「実装する内容」をタスク化して記載する。
ここでの「定義する」は、ドキュメント作成ではなく実装として定義することを指す。
仕様変更があれば内容を更新する。

## 実装計画（チェックリスト）
- タスクは機能単位（API の振る舞い単位）で起票する。
- 具体化できていない項目は「[要確認]」「[後回し]」で明示し、確定後に削除する。
- 完了条件は「実装が反映され、必要なテストが通ること」を基準に書く。

### Major + Sub-task
- [ ] {{MAJOR_NUMBER}}. {{MAJOR_TASK_SUMMARY}}
- [ ] {{MAJOR_NUMBER}}.{{SUB_NUMBER}} {{SUB_TASK_DESCRIPTION}} {{STATUS_TAG_OPTIONAL}}
  - {{DETAIL_ITEM_1}}
  - {{DETAIL_ITEM_2}}
  - 設計参照: {{DESIGN_SECTION}}
  - 完了の定義: {{COMPLETION_CRITERIA}}
