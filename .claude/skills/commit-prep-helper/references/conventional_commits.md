# Conventional Commits 仕様

このスキルで使用するConventional Commitsのルールとテンプレート。

## 基本形式

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## 主要なType

### feat (新機能)
- 新しい機能追加
- APIの追加
- 新しいコンポーネント

例:
```
feat(auth): add JWT authentication
feat(api): add user profile endpoint
feat(ui): add dark mode toggle
```

### fix (バグ修正)
- バグの修正
- 既存機能の修正

例:
```
fix(auth): resolve token expiration issue
fix(ui): fix button hover state
fix(api): handle null response correctly
```

### docs (ドキュメント)
- ドキュメントの追加・更新
- READMEの更新
- コメントの追加

例:
```
docs: update API documentation
docs: add installation guide
docs: update getting started guide
```

### test (テスト)
- テストの追加・更新
- テストカバレッジの改善

例:
```
test: add unit tests for auth service
test: improve test coverage
test: fix failing integration tests
```

### chore (その他)
- 依存関係の更新
- 設定ファイルの変更
- ビルドスクリプトの変更

例:
```
chore: update npm dependencies
chore: add linting configuration
chore: update dockerfile
```

## スコープ (Optional)

変更の影響範囲を特定するために使用:

- `feat(auth):` - 認証関連の変更
- `feat(api):` - APIエンドポイントの変更
- `feat(ui):` - UIコンポーネントの変更
- `feat(db):` - データベース関連の変更
- `feat(config):` - 設定関連の変更

## Body (Optional)

変更の詳細を説明:

```
feat(api): add user profile endpoint

- Add GET /api/users/:id endpoint
- Include user profile information
- Add authentication middleware
- Update OpenAPI documentation
```

## Footer (Optional)

BREAKING CHANGESや関連Issueを記載:

```
feat(api): add user profile endpoint

BREAKING CHANGE: The user data structure has been updated

Closes #123
```

## このスキルでのコミットメッセージ生成ルール

1. **Typeの自動判定**:
   - `package.json`, `requirements.txt` → `chore`
   - `README.md`, `*.md` → `docs`
   - `test/`, `spec/` → `test`
   - 通常のソースコード → `feat`

2. **Scopeの自動付与**:
   - 1ファイル変更時、ディレクトリ名から推測
   - `src/components/` → `(components)`
   - `test/` → `(tests)`

3. **Bodyの自動生成**:
   - 変更ファイル数
   - テスト結果
   - Lint結果
   - コードレビュー結果

## 品質基準

### Lintチェック
- ESLint/Black: エラーがないこと
- Prettier: フォーマットが整っていること

### テストチェック
- テスト実行が成功すること
- カバレッジ80%以上を推奨

### コードレビュー
- セキュリティ問題がないこと
- 品質問題が最小限であること
- 複雑度が適切であること