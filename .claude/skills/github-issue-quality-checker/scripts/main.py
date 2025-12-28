#!/usr/bin/env python3
"""
GitHub Issue Quality Checker

Open状態のGitHub Issueから低品質・曖昧なIssueを検出するスクリプト。
環境変数で指定されたリポジトリのIssueを品質評価し、最もスコアの低いIssueを特定する。
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# 共通ライブラリパスを追加（.claudeディレクトリを動的に探す）
def find_claude_lib():
    current = Path(__file__).resolve()
    for _ in range(8):  # 最大8階層まで遡る
        claude_lib = current / ".claude" / "lib" / "python"
        if claude_lib.exists():
            return str(claude_lib)
        current = current.parent
        if current == current.parent:  # ファイルシステムルートに到達
            break
    return None  # 見つからない場合


claude_lib_path = find_claude_lib()
if claude_lib_path:
    sys.path.insert(0, claude_lib_path)
    try:
        from env_utils import load_env_files, setup_python_path

        # 環境初期化（必須）
        setup_python_path()
        load_env_files()
    except ImportError:
        import warnings

        warnings.warn("env_utilsモジュールが見つかりませんでした", stacklevel=2)
else:
    import warnings

    warnings.warn("Miyabi共通ライブラリが見つかりませんでした", stacklevel=2)

try:
    import requests
except ImportError:
    print(
        "エラー: requestsライブラリが必要です。`pip install requests`でインストールしてください。",
        file=sys.stderr,
    )
    sys.exit(1)


class GitHubIssueQualityChecker:
    """GitHub Issueの品質を評価するクラス"""

    def __init__(self, token: str | None = None, repository: str | None = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.repository = repository or os.getenv("GITHUB_REPOSITORY")

        # GITHUB_REPOSITORYがなければREPO_OWNERとREPO_NAMEから構築
        if not self.repository:
            repo_owner = os.getenv("REPO_OWNER")
            repo_name = os.getenv("REPO_NAME")
            if repo_owner and repo_name:
                self.repository = f"{repo_owner}/{repo_name}"

        if not self.token:
            msg = "GitHub Tokenが必要です。GITHUB_TOKEN環境変数を設定してください。"
            raise ValueError(msg)

        if not self.repository:
            msg = "リポジトリ名が必要です。GITHUB_REPOSITORYまたはREPO_OWNERとREPO_NAME環境変数を設定してください。"
            raise ValueError(msg)

        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "github-issue-quality-checker",
        }
        self.base_url = "https://api.github.com"

    def get_open_issues(self) -> list[dict]:
        """オープン状態のIssue一覧を取得"""
        url = f"{self.base_url}/repos/{self.repository}/issues"
        params = {
            "state": "open",
            "sort": "created",
            "direction": "desc",
            "per_page": 100,
        }

        all_issues = []
        page = 1

        while True:
            params["page"] = page
            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code != 200:
                msg = f"Issue取得エラー: {response.status_code} - {response.text}"
                raise Exception(msg)

            issues = response.json()
            if not issues:
                break

            all_issues.extend(issues)
            page += 1

            # 最初の100件で十分（パフォーマンス考慮）
            if len(all_issues) >= 100:
                break

        return all_issues

    def calculate_quality_score(self, issue: dict) -> tuple[float, list[str]]:
        """Issueの品質スコアを計算（0-100、高いほど品質良い）"""
        title = issue.get("title", "")
        body = issue.get("body", "") or ""

        score = 100.0  # 満点から減点方式
        reasons = []

        # タイトル評価（40点満点）
        if len(title) < 10:
            score -= 20
            reasons.append("タイトルが短い（10文字未満）")
        elif len(title) < 20:
            score -= 10
            reasons.append("タイトルがやや短い（20文字未満）")

        # 曖昧なタイトルパターン（15点減点）
        vague_patterns = [
            r"^(バグ|問題|不具合|bug|problem)$",
            r"^.{1,5}バグ",
            r"^.{1,5}問題",
            r"^(動かない|動作しない|できない|できない)$",
            r"^(助けて|help|sos)$",
            r"^(要望|request|feature)$",
            r"^.{1,10}要望",
            r"^(質問|question)$",
        ]

        for pattern in vague_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                score -= 15
                reasons.append(f"曖昧なタイトルパターン: {pattern}")
                break

        # 本文評価（60点満点）
        if not body.strip():
            score -= 60
            reasons.append("本文が空")
        elif len(body) < 50:
            score -= 30
            reasons.append("本文が短い（50文字未満）")
        elif len(body) < 100:
            score -= 15
            reasons.append("本文がやや短い（100文字未満）")

        # 情報量評価
        info_patterns = [
            (r"環境|environment", 5, "環境情報の記載"),
            (r"再現|reproduce|step|手順", 10, "再現手順の記載"),
            (r"エラー|error|例外|exception", 5, "エラー情報の記載"),
            (r"期待|expected|期望", 5, "期待動作の記載"),
            (r"実際|actual|実際の動作", 5, "実際の動作の記載"),
            (r"バージョン|version", 3, "バージョン情報の記載"),
            (r"https?://", 8, "参考URLの記載"),
        ]

        for pattern, points, description in info_patterns:
            if re.search(pattern, body, re.IGNORECASE):
                score = min(100, score + points)  # 減点方式なので上限あり
                # 情報がある場合は減点しない（理由から削除）
                reasons = [r for r in reasons if r != description]

        # ラベル評価
        labels = issue.get("labels", [])
        if len(labels) == 0:
            score -= 10
            reasons.append("ラベルが付与されていない")

        # コードブロックがあるか
        if "```" in body:
            score = min(100, score + 5)

        # 最低スコアは0
        score = max(0, score)

        return score, reasons

    def find_lowest_quality_issue(self) -> dict | None:
        """最も品質の低いIssueを特定"""
        issues = self.get_open_issues()

        if not issues:
            return None

        # Pull Requestは除外
        issues = [issue for issue in issues if "pull_request" not in issue]

        if not issues:
            return None

        best_candidate = None
        lowest_score = float("inf")
        lowest_reasons = []

        for issue in issues:
            score, reasons = self.calculate_quality_score(issue)

            if score < lowest_score:
                lowest_score = score
                best_candidate = issue
                lowest_reasons = reasons

        if best_candidate:
            return {
                "issue": best_candidate,
                "score": lowest_score,
                "reasons": lowest_reasons,
            }

        return None

    def format_output(self, result: dict) -> str:
        """結果出力のフォーマット"""
        issue = result["issue"]
        score = result["score"]
        reasons = result["reasons"]

        return f"""# 低品質Issue検出結果

## Issue情報
- **番号**: #{issue['number']}
- **タイトル**: {issue['title']}
- **状態**: {issue['state']}
- **作成者**: {issue['user']['login']}
- **作成日**: {issue['created_at'][:10]}
- **URL**: {issue['html_url']}

## 品質評価
- **スコア**: {score:.1f}/100 （低いほど品質が低い）
- **評価**: 低品質・曖昧なIssueとして特定

## 判断理由
{chr(10).join(f"- {reason}" for reason in reasons)}

## タイトル
```
{issue['title']}
```

## 本文（最初200文字）
```
{(issue.get('body') or '')[:200]}...
```
---
*分析時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="GitHub Issue Quality Checker")
    parser.add_argument("--repository", help="リポジトリ名 (owner/repo形式)")
    parser.add_argument("--token", help="GitHub Token")
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="出力形式 (デフォルト: text)",
    )

    args = parser.parse_args()

    try:
        checker = GitHubIssueQualityChecker(
            token=args.token, repository=args.repository
        )

        print(f"リポジトリ '{checker.repository}' のIssueを分析中...", file=sys.stderr)

        result = checker.find_lowest_quality_issue()

        if not result:
            print("対象のIssueが見つかりませんでした。", file=sys.stderr)
            sys.exit(1)

        if args.output_format == "json":
            output = {
                "issue_number": result["issue"]["number"],
                "title": result["issue"]["title"],
                "score": result["score"],
                "reasons": result["reasons"],
                "url": result["issue"]["html_url"],
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(checker.format_output(result))

    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
