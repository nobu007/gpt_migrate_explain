---
description: 対話的なIssue作成とGitHub CLI統合
---

# Issue Creator Skill

GitHub Issueをテンプレートベースで対話的に作成するスキルです。

## 機能

- 対話的なIssue作成フロー
- 自動ラベル付与
- GitHub CLI統合
- Agent実行設定
- バッチ作成対応

## 使用方法

```python
from issue_creator import IssueCreator

creator = IssueCreator()
issue = creator.create_interactive()
```

## バッチ作成

```python
from issue_creator import IssueCreator

creator = IssueCreator()
issues = creator.create_batch("issues.yaml")
```