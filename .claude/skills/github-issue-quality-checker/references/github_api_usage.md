# GitHub API利用ガイド

## 概要

このスキルはGitHub REST API v3を使用してIssue情報を取得します。認証にはPersonal Access Token (PAT) を使用します。

## 必要な権限

- `public_repo`：パブリックリポジトリのIssue読み取り
- `repo`：プライベートリポジトリのIssue読み取り（プライベートリポジトリの場合）

## APIエンドポイント

### GET /repos/{owner}/{repo}/issues

リポジトリのIssue一覧を取得します。

#### パラメータ
- `state=open`: オープン状態のIssueのみ
- `sort=created`: 作成日時でソート
- `direction=desc`: 新しい順
- `per_page=100`: 1ページあたりの取得数

#### レスポンス形式
```json
[
  {
    "id": 1,
    "number": 123,
    "title": "Issueタイトル",
    "body": "Issue本文",
    "state": "open",
    "user": {
      "login": "username"
    },
    "labels": [
      {
        "name": "bug",
        "color": "d73a4a"
      }
    ],
    "created_at": "2024-01-01T00:00:00Z",
    "html_url": "https://github.com/owner/repo/issues/123"
  }
]
```

## レート制限

- 認証済み: 1時間あたり5,000リクエスト
- 未認証: 1時間あたり60リクエスト

このスキルでは認証済みリクエストを使用します。

## 環境変数設定

### 必須環境変数

```bash
# GitHub Personal Access Token
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# 対象リポジトリ (owner/repo形式)
export GITHUB_REPOSITORY="owner/repository-name"
```

### トークン生成方法

1. GitHubにログイン
2. Settings → Developer settings → Personal access tokens → Tokens (classic)
3. Generate new token をクリック
4. 必要な権限をチェック：
   - `public_repo`（パブリックリポジトリの場合）
   - `repo`（プライベートリポジトリの場合）
5. 生成されたトークンをコピーして環境変数に設定

## エラーハンドリング

### HTTPステータスコード
- `200`: 成功
- `401`: 認証失敗（トークン無効）
- `403`: 権限不足、レート制限超過
- `404`: リポジトリが存在しない
- `422`: リクエスト形式が不正

### エラー対応
- トークンの有効性チェック
- リポジトリアクセス権限の確認
- レート制限の監視（ヘッダーの `X-RateLimit-Remaining` を確認）

## セキュリティ考慮事項

1. **トークン管理**
   - トークンをコードに直接記述しない
   - 環境変数または設定ファイルから読み込む
   - トークンをリポジトリにコミットしない

2. **最小権限の原則**
   - 必要最小限の権限のみを付与
   - 読み取り専用権限が推奨

3. **トークンの有効期限**
   - 長期有効トークンは避ける
   - 定期的なトークン更新を推奨

## パフォーマンス最適化

- ページネーションを適切に処理（最大100件に制限）
- 不要なフィールドの取得を避ける
- キャッシュの活用（将来的な拡張）