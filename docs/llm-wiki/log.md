# GoalDev Log

永続的決定と完了記録を追記する。各エントリに日付と検証を必ず付ける
（原則: contracts `llm-wiki-discipline` の log-is-append-with-correction）。

## 2026-09-26 — llm-wiki スキャフォールド

contracts の llm-wiki-discipline 原則に基づき `docs/llm-wiki/` を新設した。

- **Verification**: 原則 `registry/principles/llm-wiki-discipline.yaml`（contracts リポ commit 3ab5768）。

## 2026-09-26 — fork カスタマイズ調査（upstream joshpxyne/gpt-migrate）

上流 `up/main` と HEAD を比較し、12 コミット先行を確認。上流コード自体の書き換えは最小限で、差分の大半は自組織の開発基盤追加: `_bmad`（458ファイル）・`.claude` エージェント（192ファイル）・`scripts_operations/` 監視ツール群（ucg-devops 同期）・Python 品質ツール整備（ruff/mypy/pyproject）・`gpt_migrate/steps/explain.py` の追加修正。

- **Verification**: git log up/main..HEAD = 12 commits, git diff --stat up/main...HEAD = 700 files changed, +137295/-600（差分集中: _bmad・.claude・scripts_operations/monitoring）。
