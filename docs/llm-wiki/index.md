# LLM Wiki

長期圧縮コンテキスト。原則: contracts `llm-wiki-discipline`（手本: defuddle
`docs/llm-wiki/`）。正本を複製せず、検証済み知識を出典付きで圧縮する。

## Verified Knowledge

- 成果物: コードベースを別フレームワーク・言語へ移行する OSS「GPT-Migrate」（上流 0xpayne/gpt-migrate）のローカルコピー。（出典: README.md の上流バッジ・リンク）
- カスタマイズ: 上流コードは保持し、自組織の開発基盤を大規模に追加（`_bmad` 458ファイル・`.claude` エージェント群・`scripts_operations/` 監視ツール群・ruff/mypy/pyproject 整備・`gpt_migrate/steps/explain.py` 追加）。up/main から 12 コミット先行。（出典: git log up/main..HEAD 12 commits / git diff --stat up/main...HEAD）
