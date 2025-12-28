# 目標分解の実例

このドキュメントは、様々な作業領域での目標分解の実例を示します。
これらの例を参考に、自分の目標を効果的に分解してください。

## ソフトウェア開発

### 例1: Webアプリケーション開発

**元の目標**: 「ユーザー認証機能付きのTodoリストアプリを作成する」

**分解結果**:

```json
{
  "original_goal": "ユーザー認証機能付きのTodoリストアプリを作成する",
  "steps": [
    {
      "step": 1,
      "title": "要件定義と技術選定",
      "description": "機能要件を明確化し、使用する技術スタック（フレームワーク、データベース等）を決定する",
      "estimated_effort": "small",
      "dependencies": []
    },
    {
      "step": 2,
      "title": "データベーススキーマ設計",
      "description": "ユーザーテーブルとTodoテーブルのスキーマを設計し、マイグレーションファイルを作成する",
      "estimated_effort": "small",
      "dependencies": [1]
    },
    {
      "step": 3,
      "title": "認証APIの実装",
      "description": "ユーザー登録、ログイン、ログアウトのAPIエンドポイントを実装する",
      "estimated_effort": "medium",
      "dependencies": [2]
    },
    {
      "step": 4,
      "title": "Todo CRUD APIの実装",
      "description": "Todo作成、取得、更新、削除のAPIエンドポイントを実装する",
      "estimated_effort": "medium",
      "dependencies": [2, 3]
    },
    {
      "step": 5,
      "title": "フロントエンド実装",
      "description": "React/Vueでログイン画面とTodoリスト画面を実装し、APIと接続する",
      "estimated_effort": "large",
      "dependencies": [3, 4]
    },
    {
      "step": 6,
      "title": "統合テストと修正",
      "description": "E2Eテストを実行し、発見されたバグを修正する",
      "estimated_effort": "medium",
      "dependencies": [5]
    },
    {
      "step": 7,
      "title": "デプロイとドキュメント作成",
      "description": "本番環境にデプロイし、README等のドキュメントを整備する",
      "estimated_effort": "small",
      "dependencies": [6]
    }
  ]
}
```

### 例2: レガシーコードのリファクタリング

**元の目標**: 「モノリシックなコードをマイクロサービスアーキテクチャに移行する」

**分解結果**:

```json
{
  "original_goal": "モノリシックなコードをマイクロサービスアーキテクチャに移行する",
  "steps": [
    {
      "step": 1,
      "title": "現状分析とドメイン境界の特定",
      "description": "既存コードを分析し、ビジネスドメインごとの境界を特定する",
      "estimated_effort": "large",
      "dependencies": []
    },
    {
      "step": 2,
      "title": "マイクロサービス設計",
      "description": "各サービスの責務、API仕様、データストアを設計する",
      "estimated_effort": "large",
      "dependencies": [1]
    },
    {
      "step": 3,
      "title": "共通ライブラリの抽出",
      "description": "複数サービスで共有するロジックを共通ライブラリとして抽出する",
      "estimated_effort": "medium",
      "dependencies": [2]
    },
    {
      "step": 4,
      "title": "最初のサービスを分離",
      "description": "最も独立性の高いサービス（例: 認証サービス）を分離し、動作確認する",
      "estimated_effort": "large",
      "dependencies": [3]
    },
    {
      "step": 5,
      "title": "残りのサービスを段階的に分離",
      "description": "依存関係を考慮しながら、他のサービスを1つずつ分離していく",
      "estimated_effort": "large",
      "dependencies": [4]
    },
    {
      "step": 6,
      "title": "サービス間通信の実装",
      "description": "REST API、gRPC、メッセージキュー等でサービス間通信を実装する",
      "estimated_effort": "medium",
      "dependencies": [5]
    },
    {
      "step": 7,
      "title": "統合テストと性能評価",
      "description": "全サービス統合後のテストを実行し、性能を評価する",
      "estimated_effort": "medium",
      "dependencies": [6]
    }
  ]
}
```

## データ分析

### 例3: データ分析レポート作成

**元の目標**: 「売上データを分析して月次レポートを作成する」

**分解結果**:

```json
{
  "original_goal": "売上データを分析して月次レポートを作成する",
  "steps": [
    {
      "step": 1,
      "title": "データ収集",
      "description": "データベースやCSVから必要な売上データを抽出する",
      "estimated_effort": "small",
      "dependencies": []
    },
    {
      "step": 2,
      "title": "データクレンジング",
      "description": "欠損値の処理、異常値の検出、データ型の統一を行う",
      "estimated_effort": "medium",
      "dependencies": [1]
    },
    {
      "step": 3,
      "title": "探索的データ分析",
      "description": "基本統計量の算出、分布の確認、相関分析を行う",
      "estimated_effort": "medium",
      "dependencies": [2]
    },
    {
      "step": 4,
      "title": "指標の算出",
      "description": "売上高、成長率、顧客単価等の主要指標を計算する",
      "estimated_effort": "small",
      "dependencies": [3]
    },
    {
      "step": 5,
      "title": "可視化の作成",
      "description": "グラフやチャートを作成し、トレンドやパターンを可視化する",
      "estimated_effort": "medium",
      "dependencies": [4]
    },
    {
      "step": 6,
      "title": "インサイトの抽出",
      "description": "データから得られた知見をまとめ、推奨アクションを提示する",
      "estimated_effort": "medium",
      "dependencies": [5]
    },
    {
      "step": 7,
      "title": "レポート作成",
      "description": "分析結果を文書化し、PowerPoint/PDF形式でレポートを作成する",
      "estimated_effort": "medium",
      "dependencies": [6]
    }
  ]
}
```

### 例4: 機械学習モデル開発

**元の目標**: 「顧客離反予測モデルを開発する」

**分解結果**:

```json
{
  "original_goal": "顧客離反予測モデルを開発する",
  "steps": [
    {
      "step": 1,
      "title": "問題定義と評価指標の設定",
      "description": "予測対象を明確化し、モデルの評価指標（精度、再現率等）を決定する",
      "estimated_effort": "small",
      "dependencies": []
    },
    {
      "step": 2,
      "title": "データ収集と統合",
      "description": "顧客データ、行動ログ、取引履歴等を収集・統合する",
      "estimated_effort": "medium",
      "dependencies": [1]
    },
    {
      "step": 3,
      "title": "特徴量エンジニアリング",
      "description": "有効な特徴量を設計・作成する（滞在時間、購入頻度等）",
      "estimated_effort": "large",
      "dependencies": [2]
    },
    {
      "step": 4,
      "title": "訓練データとテストデータの分割",
      "description": "データを訓練用・検証用・テスト用に分割する",
      "estimated_effort": "small",
      "dependencies": [3]
    },
    {
      "step": 5,
      "title": "ベースラインモデルの構築",
      "description": "シンプルなモデル（ロジスティック回帰等）でベースラインを作成する",
      "estimated_effort": "small",
      "dependencies": [4]
    },
    {
      "step": 6,
      "title": "高度なモデルの試行",
      "description": "Random Forest、XGBoost、ニューラルネット等を試行し比較する",
      "estimated_effort": "large",
      "dependencies": [5]
    },
    {
      "step": 7,
      "title": "ハイパーパラメータチューニング",
      "description": "最良のモデルのパラメータを最適化する",
      "estimated_effort": "medium",
      "dependencies": [6]
    },
    {
      "step": 8,
      "title": "モデル評価と解釈",
      "description": "テストデータで最終評価を行い、特徴量の重要度を分析する",
      "estimated_effort": "medium",
      "dependencies": [7]
    },
    {
      "step": 9,
      "title": "デプロイと監視",
      "description": "モデルを本番環境にデプロイし、性能監視の仕組みを構築する",
      "estimated_effort": "medium",
      "dependencies": [8]
    }
  ]
}
```

## ドキュメント作成

### 例5: 技術ドキュメント作成

**元の目標**: 「新しいAPIの包括的なドキュメントを作成する」

**分解結果**:

```json
{
  "original_goal": "新しいAPIの包括的なドキュメントを作成する",
  "steps": [
    {
      "step": 1,
      "title": "ドキュメント構成の設計",
      "description": "目次、セクション構成、対象読者を定義する",
      "estimated_effort": "small",
      "dependencies": []
    },
    {
      "step": 2,
      "title": "概要とクイックスタートの執筆",
      "description": "APIの概要と最小限の使用例を記述する",
      "estimated_effort": "small",
      "dependencies": [1]
    },
    {
      "step": 3,
      "title": "認証・認可の説明",
      "description": "API認証の方法、トークン取得、権限管理について記述する",
      "estimated_effort": "small",
      "dependencies": [1]
    },
    {
      "step": 4,
      "title": "エンドポイントリファレンス",
      "description": "各エンドポイントのURL、メソッド、パラメータ、レスポンスを詳細に記述する",
      "estimated_effort": "large",
      "dependencies": [1]
    },
    {
      "step": 5,
      "title": "コード例の作成",
      "description": "主要な言語（Python、JavaScript等）でのコード例を作成する",
      "estimated_effort": "medium",
      "dependencies": [4]
    },
    {
      "step": 6,
      "title": "エラーハンドリングの説明",
      "description": "エラーコード、エラーメッセージ、対処方法を記述する",
      "estimated_effort": "small",
      "dependencies": [4]
    },
    {
      "step": 7,
      "title": "レビューと修正",
      "description": "技術レビューを受けて内容を修正・改善する",
      "estimated_effort": "medium",
      "dependencies": [2, 3, 4, 5, 6]
    },
    {
      "step": 8,
      "title": "公開とフィードバック収集",
      "description": "ドキュメントを公開し、初期ユーザーからフィードバックを収集する",
      "estimated_effort": "small",
      "dependencies": [7]
    }
  ]
}
```

## インフラ・運用

### 例6: クラウド移行プロジェクト

**元の目標**: 「オンプレミスのアプリケーションをAWSに移行する」

**分解結果**:

```json
{
  "original_goal": "オンプレミスのアプリケーションをAWSに移行する",
  "steps": [
    {
      "step": 1,
      "title": "現状調査とインベントリ作成",
      "description": "現在のサーバー構成、アプリケーション、依存関係を調査・文書化する",
      "estimated_effort": "medium",
      "dependencies": []
    },
    {
      "step": 2,
      "title": "AWS アーキテクチャ設計",
      "description": "EC2、RDS、S3等のAWSサービスを使った新しいアーキテクチャを設計する",
      "estimated_effort": "large",
      "dependencies": [1]
    },
    {
      "step": 3,
      "title": "コスト見積もりと承認",
      "description": "AWS利用コストを見積もり、予算承認を得る",
      "estimated_effort": "small",
      "dependencies": [2]
    },
    {
      "step": 4,
      "title": "AWSアカウントとネットワーク設定",
      "description": "VPC、サブネット、セキュリティグループを設定する",
      "estimated_effort": "medium",
      "dependencies": [3]
    },
    {
      "step": 5,
      "title": "ステージング環境の構築",
      "description": "本番移行前のテスト環境をAWS上に構築する",
      "estimated_effort": "large",
      "dependencies": [4]
    },
    {
      "step": 6,
      "title": "データ移行戦略の策定とテスト",
      "description": "データベース移行の手順を策定し、ステージングで検証する",
      "estimated_effort": "medium",
      "dependencies": [5]
    },
    {
      "step": 7,
      "title": "アプリケーション移行とテスト",
      "description": "アプリケーションをステージングに移行し、動作確認する",
      "estimated_effort": "large",
      "dependencies": [6]
    },
    {
      "step": 8,
      "title": "本番移行計画の作成",
      "description": "ダウンタイム最小化のための詳細な移行手順を作成する",
      "estimated_effort": "medium",
      "dependencies": [7]
    },
    {
      "step": 9,
      "title": "本番移行実施",
      "description": "計画に従って本番環境を移行する",
      "estimated_effort": "large",
      "dependencies": [8]
    },
    {
      "step": 10,
      "title": "監視とオンプレ環境の廃止",
      "description": "AWS環境の監視を強化し、問題なければオンプレ環境を段階的に廃止する",
      "estimated_effort": "medium",
      "dependencies": [9]
    }
  ]
}
```

## その他

### 例7: 学習計画

**元の目標**: 「3ヶ月でPythonとデータサイエンスの基礎を習得する」

**分解結果**:

```json
{
  "original_goal": "3ヶ月でPythonとデータサイエンスの基礎を習得する",
  "steps": [
    {
      "step": 1,
      "title": "Python基礎文法の学習",
      "description": "変数、制御構文、関数、クラスなどの基本を学ぶ（2週間）",
      "estimated_effort": "medium",
      "dependencies": []
    },
    {
      "step": 2,
      "title": "NumPyとPandasの習得",
      "description": "データ操作ライブラリの使い方を学ぶ（2週間）",
      "estimated_effort": "medium",
      "dependencies": [1]
    },
    {
      "step": 3,
      "title": "データ可視化の学習",
      "description": "Matplotlib、Seabornを使ったグラフ作成を学ぶ（1週間）",
      "estimated_effort": "small",
      "dependencies": [2]
    },
    {
      "step": 4,
      "title": "統計学の基礎",
      "description": "記述統計、確率分布、仮説検定の基礎を学ぶ（2週間）",
      "estimated_effort": "medium",
      "dependencies": [2]
    },
    {
      "step": 5,
      "title": "機械学習入門",
      "description": "scikit-learnを使った基本的なモデル構築を学ぶ（3週間）",
      "estimated_effort": "large",
      "dependencies": [4]
    },
    {
      "step": 6,
      "title": "実践プロジェクト",
      "description": "Kaggleのチュートリアルコンペに参加して総合的に実践する（2週間）",
      "estimated_effort": "large",
      "dependencies": [3, 5]
    }
  ]
}
```

## 分解例から学ぶポイント

### 1. 適切な粒度

- **良い例**: ステップ4「Todo CRUD APIの実装」（明確な成果物）
- **悪い例**: 「コードを書く」（曖昧すぎる）

### 2. 依存関係の明確化

- **良い例**: ステップ5はステップ3と4に依存（フロントエンドはAPIが必要）
- **悪い例**: すべてのステップが前のステップに依存（並列化の機会を逃す）

### 3. 推定作業量の現実性

- **良い例**: 「large」は半日〜数日、「medium」は数時間、「small」は1時間以内
- **悪い例**: すべて「medium」（見積もりの意味がない）

### 4. 検証・テストの組み込み

- ほとんどの例で「テスト」「検証」のステップが含まれている
- 早めにテストすることでリスクを低減

### 5. 段階的なアプローチ

- 「一気に全部やる」ではなく、小さく始めて徐々に拡大
- 例: マイクロサービス移行で「最初の1サービスを分離」→「残りを段階的に」
