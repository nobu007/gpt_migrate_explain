# プロジェクトタイプ別ツール設定

プロジェクトの種類に応じて使用するLint/Testツールのマッピング。

## プロジェクトタイプ検出アルゴリズム

### 検出優先順位
1. `package.json` 存在 → Node.js/TypeScript
2. `requirements.txt` または `pyproject.toml` 存在 → Python
3. `Cargo.toml` 存在 → Rust
4. `go.mod` 存在 → Go
5. `pom.xml` または `build.gradle` 存在 → Java
6. その他 → Unknown

## Node.js/TypeScript プロジェクト

### Lintツール
```json
{
  "eslint": {
    "command": "npx eslint",
    "options": ["--format=json"],
    "files": ".",
    "priority": 1
  },
  "prettier": {
    "command": "npx prettier",
    "options": ["--check"],
    "files": ".",
    "priority": 2
  }
}
```

### テストフレームワーク
```json
{
  "jest": {
    "command": "npx jest",
    "options": ["--coverage", "--passWithNoTests"],
    "config_files": ["jest.config.js", "jest.config.json", "package.json"],
    "priority": 1
  },
  "vitest": {
    "command": "npx vitest run",
    "options": ["--coverage"],
    "config_files": ["vitest.config.js", "vitest.config.ts", "vite.config.js"],
    "priority": 2
  },
  "mocha": {
    "command": "npx mocha",
    "options": ["--recursive"],
    "config_files": ["mocha.opts"],
    "priority": 3
  }
}
```

### ファイル拡張子
- JavaScript: `.js`, `.jsx`
- TypeScript: `.ts`, `.tsx`
- 設定ファイル: `.json`, `.js`, `.ts`
- ドキュメント: `.md`

## Python プロジェクト

### Lintツール
```json
{
  "black": {
    "command": "python -m black",
    "options": ["--check"],
    "files": ".",
    "priority": 1
  },
  "flake8": {
    "command": "flake8",
    "options": [],
    "files": ".",
    "priority": 2
  },
  "pylint": {
    "command": "pylint",
    "options": [],
    "files": ".",
    "priority": 3
  }
}
```

### テストフレームワーク
```json
{
  "pytest": {
    "command": "python -m pytest",
    "options": ["-v", "--cov=.", "--cov-report=term-missing"],
    "config_files": ["pytest.ini", "pyproject.toml", "setup.cfg"],
    "priority": 1
  },
  "unittest": {
    "command": "python -m unittest",
    "options": ["discover"],
    "config_files": [],
    "priority": 2
  }
}
```

### ファイル拡張子
- Python: `.py`
- 設定ファイル: `.ini`, `.cfg`, `.toml`
- ドキュメント: `.md`, `.rst`

## Rust プロジェクト

### Lintツール
```json
{
  "cargo-clippy": {
    "command": "cargo clippy",
    "options": ["--", "-D warnings"],
    "files": ".",
    "priority": 1
  },
  "rustfmt": {
    "command": "cargo fmt",
    "options": ["--", "--check"],
    "files": ".",
    "priority": 2
  }
}
```

### テストフレームワーク
```json
{
  "cargo-test": {
    "command": "cargo test",
    "options": [],
    "config_files": ["Cargo.toml"],
    "priority": 1
  }
}
```

### ファイル拡張子
- Rust: `.rs`
- 設定ファイル: `.toml`
- ドキュメント: `.md`

## Go プロジェクト

### Lintツール
```json
{
  "gofmt": {
    "command": "gofmt",
    "options": ["-d"],
    "files": ".",
    "priority": 1
  },
  "golint": {
    "command": "golint",
    "options": [],
    "files": "./...",
    "priority": 2
  }
}
```

### テストフレームワーク
```json
{
  "go-test": {
    "command": "go test",
    "options": ["./..."],
    "config_files": [],
    "priority": 1
  }
}
```

### ファイル拡張子
- Go: `.go`
- 設定ファイル: `.mod`, `.sum`
- ドキュメント: `.md`

## Java プロジェクト

### Lintツール
```json
{
  "checkstyle": {
    "command": "checkstyle",
    "options": ["-c", "checkstyle.xml"],
    "files": "src",
    "priority": 1
  }
}
```

### テストフレームワーク
```json
{
  "junit": {
    "command": "mvn test",
    "options": [],
    "config_files": ["pom.xml"],
    "priority": 1
  },
  "gradle": {
    "command": "gradle test",
    "options": [],
    "config_files": ["build.gradle"],
    "priority": 2
  }
}
```

## ツール選択ロジック

### Lintツール選択
1. プロジェクトタイプを検出
2. 利用可能なツールを確認 (コマンド存在チェック)
3. 設定ファイルの存在を確認
4. 優先順位に従って選択

### テストフレームワーク選択
1. プロジェクトタイプを検出
2. 設定ファイルからフレームワークを特定
3. 依存関係を確認 (package.json, requirements.txtなど)
4. 優先順位に従って選択

## 実行順序

### 品質チェックの標準フロー
1. **Lintチェック** (優先度: 高)
   - コードスタイルと構文チェック
   - フォーマット検証

2. **テスト実行** (優先度: 高)
   - ユニットテスト実行
   - カバレッジ測定

3. **コードレビュー** (優先度: 中)
   - 静的解析
   - セキュリティチェック

### 各ツールのタイムアウト設定
- Lintツール: 30秒
- テストフレームワーク: 5分
- コードレビュー: 1分

## エラーハンドリング

### ツールが見つからない場合
- 警告を表示
- 次の優先度のツールを試行
- 代替手段を提案

### 設定ファイルが見つからない場合
- デフォルト設定を使用
- プロジェクトルートを探索
- 基本的なチェックのみ実行

### タイムアウトした場合
- プロセスを強制終了
- エラーとして記録
- 品質スコアに反映

## カスタマイズ設定

### プロジェクト固有の設定
プロジェクトルートに `.commit-prep-config.json` を配置:

```json
{
  "project_type": "custom",
  "lint_tools": [
    {
      "name": "custom-linter",
      "command": "custom-lint",
      "options": ["--strict"],
      "priority": 1
    }
  ],
  "test_framework": {
    "name": "custom-test",
    "command": "custom-test",
    "options": ["--coverage"],
    "coverage_parser": "custom"
  },
  "file_patterns": {
    "include": ["**/*.custom"],
    "exclude": ["**/*.test.custom"]
  }
}
```