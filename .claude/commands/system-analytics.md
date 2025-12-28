---
description: システム分析・監視コマンド
---

# System Analytics - システム稼働分析

システムの稼働履歴、パフォーマンス、品質指標を分析・監視します。

## コマンド

### 📊 全体サマリー表示

```bash
system-analytics summary
```

システム全体の健全性、処理件数、品質スコアなどを表示します。

### 📈 パフォーマンス詳細

```bash
system-analytics performance --days 7
```

指定した期間の詳細なパフォーマンスデータを表示します。

### 🎯 品質レポート生成

```bash
system-analytics quality-report --format markdown
```

品質分析レポートを生成します。

### 📋 デイリーレポート表示

```bash
system-analytics daily-report --date 2025-01-19
```

指定日付のデイリーレポートを表示します。

### 🔧 トレンド分析

```bash
system-analytics trends --metric quality --days 30
```

品質スコアのトレンドを分析します。

### ⚠️ 健全性チェック

```bash
system-analytics health-check
```

システムの健全性をチェックし、警告を表示します。

## 分析指標

### 📊 パフォーマンス指標
- **処理件数**: 総処理Issue数
- **成功率**: 処理成功率（%）
- **平均処理時間**: Issue1件あたりの平均処理時間
- **エージェント応答時間**: Claude Code Agentの応答時間
- **GitHub APIコール数**: API呼び出し回数

### 🎯 品質指標
- **リライト品質**: Issueリライトの品質スコア
- **ラベル精度**: 自動付与ラベルの精度
- **完全性**: タスク定義の完全性スコア
- **エラー率**: エラー発生率

### 📈 トレンド分析
- **品質スコア推移**: 日次での品質スコアの変化
- **処理時間推移**: 処理時間の傾向
- **成功率推移**: 成功率の変化パターン

## レポート出力形式

### JSON形式
```json
{
  "summary": {
    "totalIssues": 150,
    "successRate": 94.5,
    "qualityScore": 87.2,
    "averageProcessingTime": 8500
  },
  "health": {
    "status": "healthy",
    "message": "品質スコア: 87.2%, 成功率: 94.5%"
  }
}
```

### Markdown形式
```markdown
# 📊 システム分析レポート

## サマリー
- 処理件数: 150
- 成功率: 94.5%
- 品質スコア: 87.2/100
```

## 設定値と閾値

### 品質スコア
- **🟢 優秀**: 90-100点
- **🟡 良好**: 80-89点
- **🟠 要改善**: 60-79点
- **🔴 危機**: 0-59点

### 成功率
- **🟢 優秀**: 98-100%
- **🟡 良好**: 95-97%
- **🟠 要改善**: 80-94%
- **🔴 危機**: 0-79%

### 処理時間
- **🟢 高速**: 0-5秒
- **🟡 標準**: 5-10秒
- **🟠 遅延**: 10-30秒
- **🔴 遅延**: 30秒超

## 使い方

### 基本的な監視
```bash
# 1. 毎日の状態確認
system-analytics summary

# 2. 週次レポート確認
system-analytics weekly-report

# 3. 月次トレンド分析
system-analytics trends --days 30
```

### 問題発生時の分析
```bash
# 1. 健全性チェック
system-analytics health-check

# 2. 詳細なエラー分析
system-analytics errors --severity high

# 3. 品質低下の原因分析
system-analytics quality-analysis --period last-week
```

### レポート生成と共有
```bash
# 1. 日次レポート生成と保存
system-analytics generate-daily-report --output ./reports/

# 2. 週次サマリー生成
system-analytics weekly-summary --format markdown --output ./reports/

# 3. 月次分析レポート
system-analytics monthly-report --include trends --output ./reports/
```

## データ保存場所

- **メトリクス**: `./.analytics/system-metrics.json`
- **品質データ**: `./.analytics/quality-metrics.json`
- **日次レポート**: `./.analytics/daily-reports/YYYY-MM-DD.md`
- **週次レポート**: `./.analytics/weekly-reports/YYYY-WXX.md`

## 自動化

### 定期レポート
- 日次レポート: 毎日23:59に自動生成
- 週次サマリー: 毎週月曜日9:00に自動生成
- 月次分析: 毎月1日9:00に自動生成

### アラート設定
- 品質スコア80%未満: 即時通知
- 成功率90%未満: 警告通知
- エラー率5%超過: 緊急通知

---

*システム分析は継続的な改善の基盤となります*