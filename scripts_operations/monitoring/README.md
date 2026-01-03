# Module Monitoring & Compliance System

## 概要

プロジェクトの憲法的整合性と品質を自動監視するシステム。Module Filtering System と統合し、Git履歴ベースの優先度付けで効率的な監視を実現。

## クイックスタート

```bash
# 最重要10モジュールを監視（推奨）
python scripts_operations/monitoring/constitutional_compliance_checker_enhanced.py

# 全モジュール包括監視
python scripts_operations/monitoring/constitutional_compliance_checker_enhanced.py --all

# 重要問題のみ表示（CI/CD用）
python scripts_operations/monitoring/constitutional_compliance_checker_enhanced.py --quiet
```

## 主要機能

### Constitutional Compliance Checker Enhanced

憲法ファイル（SYSTEM_CONSTITUTION.md、AGENTS.md、CLAUDE.md）と.moduleファイルセット（8ファイル）の整合性を監視。

**監視項目:**

- 必須ファイルの存在確認
- .moduleファイル完全性（TASKS.md、MODULE_GOALS.md等）
- LOGICアンカー一貫性
- 更新状況と品質メトリクス

**出力レベル:**

- 🔴 Critical: 必須ファイル欠落、構造違反
- 🟡 Warning: 古いファイル、不整合
- 🔵 Info: 統計情報、改善提案

### 実行例

正常時は`✅ Overall compliance: PASS`、問題検出時は`❌ Overall compliance: FAIL`と詳細な問題リストが表示されます。

## オプション

| オプション | 説明 | デフォルト |
|------------|------|------------|
| `--all` | 全モジュール監視 | top 10 |
| `--limit=N` | 監視対象数指定 | 10 |
| `--quiet` | 重要問題のみ | false |
| `--verbose` | 詳細出力 | false |
| `--output=FILE` | 結果保存先 | stdout |
| `--format=FORMAT` | 出力形式 | text |

## CI/CD統合

```bash
# crontab設定例
0 2 * * * cd /path/to/ucg-devops && python3 scripts_operations/monitoring/constitutional_compliance_checker_enhanced.py --all
```

GitHub Actions統合は[.github/workflows/compliance_check.yml](../../.github/workflows/compliance_check.yml)参照。

## トラブルシューティング

| 問題 | 解決策 |
|-----|--------|
| `.module`ディレクトリ未検出 | プロジェクトルートから実行 |
| パーミッションエラー | `chmod -R 644 .module/` |
| メモリ不足 | `--limit=20`でバッチ実行 |

詳細は`--verbose --debug`オプションで確認。

## パフォーマンス

| 監視モード | モジュール数 | 実行時間 |
|------------|-------------|----------|
| Default | 10 | ~1.8秒 |
| Limited | 5 | ~0.9秒 |
| All | 48 | ~7.2秒 |

メモリ使用量: ~12MB、CPU: 3-8%（I/O集約的）

## 詳細情報

- [設定ファイル例](docs/compliance_config_example.yaml)
- [API仕様](docs/api_specification.md)
- [Module Filter Core](../common/README.md)
- [Quality Assurance](../quality_assurance/README.md)

---

**Module Monitoring & Compliance System** - プロジェクト品質の継続的保証
