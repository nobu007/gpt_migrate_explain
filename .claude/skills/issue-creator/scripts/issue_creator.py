#!/usr/bin/env python3
"""Issue Creator Skill - GitHub Issueを対話的に作成する"""

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class IssueData:
    """Issueデータ構造"""

    title: str
    body: str
    labels: list[str]
    assignees: list[str] | None = None
    milestone: str | None = None


@dataclass
class IssueConfig:
    """Issue作成設定"""

    title: str
    issue_type: str
    requirements: list[str]
    tech_stack: str | None = None
    constraints: str | None = None
    auto_execute: bool = False
    priority: str = "medium"
    assignees: list[str] | None = None


class IssueCreator:
    """GitHub Issue作成クラス"""

    ISSUE_TYPES = {
        "1": {"key": "feature", "emoji": "🆕", "label": "feature"},
        "2": {"key": "bug", "emoji": "🐛", "label": "bug"},
        "3": {"key": "refactor", "emoji": "♻️", "label": "refactor"},
        "4": {"key": "docs", "emoji": "📝", "label": "documentation"},
        "5": {"key": "performance", "emoji": "⚡", "label": "performance"},
        "6": {"key": "security", "emoji": "🔒", "label": "security"},
        "7": {"key": "test", "emoji": "🧪", "label": "test"},
    }

    PRIORITIES = {
        "1": {"key": "high", "emoji": "🔴", "label": "priority-high"},
        "2": {"key": "medium", "emoji": "🟡", "label": "priority-medium"},
        "3": {"key": "low", "emoji": "🟢", "label": "priority-low"},
    }

    def __init__(self):
        self.repo = self._get_repo_info()
        self.github_token = os.getenv("GITHUB_TOKEN")

        if not self.github_token:
            print("⚠️  警告: GITHUB_TOKENが設定されていません")
            print("   GitHub CLIの認証が必要です: gh auth login")

    def _get_repo_info(self) -> str:
        """リポジトリ情報を取得"""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True,
            )
            remote_url = result.stdout.strip()

            # GitHub URLからowner/repoを抽出
            if "github.com" in remote_url:
                return remote_url.split("github.com/")[1].replace(".git", "")
            return "owner/repo"  # デフォルト値
        except subprocess.CalledProcessError:
            return "owner/repo"

    def _create_issue_body(self, config: IssueConfig) -> str:
        """Issue本文を生成"""
        issue_type_info = self.ISSUE_TYPES.get(
            config.issue_type, {"emoji": "📝", "key": "general"}
        )

        body = f"# {issue_type_info['emoji']} {config.title}\n\n"

        if config.requirements:
            body += "## 📋 要件\n\n"
            for req in config.requirements:
                body += f"- [ ] {req}\n"
            body += "\n"

        if config.tech_stack:
            body += "## 🛠️ 技術スタック\n\n"
            for tech in config.tech_stack.split(","):
                body += f"- {tech.strip()}\n"
            body += "\n"

        if config.constraints:
            body += f"## ⚠️ 制約事項\n\n{config.constraints}\n\n"

        body += "## 📊 成功条件\n\n"
        body += "- [ ] TypeScript エラー: 0件\n"
        body += "- [ ] テストカバレッジ: ≥80%\n"
        body += "- [ ] 品質スコア: ≥80点\n"
        body += "- [ ] セキュリティスキャン: 脆弱性0件\n\n"

        body += "## 🤖 Agent実行設定\n\n"
        body += f"- **自動実行**: {'有効' if config.auto_execute else '無効'}\n"

        priority_info = self.PRIORITIES.get(
            next(k for k, v in self.PRIORITIES.items() if v["key"] == config.priority),
            {"emoji": "🟡", "key": "medium"},
        )
        body += (
            f"- **優先度**: {priority_info['emoji']} {config.priority.capitalize()}\n"
        )
        body += "- **期待実行時間**: 3-5分\n\n"

        body += "---\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)"

        return body

    def _create_labels(self, config: IssueConfig) -> list[str]:
        """ラベルリストを生成"""
        labels = []

        # Issueタイプラベル
        issue_type_info = self.ISSUE_TYPES.get(config.issue_type)
        if issue_type_info:
            labels.append(f"{issue_type_info['emoji']}{issue_type_info['label']}")

            # featureの場合は追加ラベル
            if issue_type_info["key"] == "feature":
                labels.append("enhancement")

        # 優先度ラベル
        priority_info = self.PRIORITIES.get(
            next(k for k, v in self.PRIORITIES.items() if v["key"] == config.priority),
            {"label": "priority-medium"},
        )
        labels.append(priority_info["label"])

        # Agent実行ラベル
        if config.auto_execute:
            labels.append("🤖agent-execute")

        return labels

    def _create_github_issue(self, issue_data: IssueData) -> dict[str, Any]:
        """GitHub Issueを作成"""
        # Validate issue data before creating GitHub issue
        if not issue_data.title or issue_data.title.strip() == "":
            return {
                "success": False,
                "error": "Title cannot be empty",
                "message": "❌ Issueのタイトルは必須です",
            }

        if len(issue_data.title.strip()) < 10 and (
            not issue_data.body or len(issue_data.body.strip()) == 0
        ):
            return {
                "success": False,
                "error": "Title too short and no body provided",
                "message": "❌ タイトルが短すぎます。10文字以上のタイトルか、詳細な本文が必要です",
            }

        try:
            # 一時ファイルに本文を書き込み
            body_file = Path("/tmp/issue_body.md")
            body_file.write_text(issue_data.body, encoding="utf-8")

            # ghコマンドを構築
            cmd = [
                "gh",
                "issue",
                "create",
                "--title",
                issue_data.title,
                "--body",
                f"@{body_file}",
                "--repo",
                self.repo,
            ]

            if issue_data.labels:
                cmd.extend(["--label", ",".join(issue_data.labels)])

            if issue_data.assignees:
                cmd.extend(["--assignee", ",".join(issue_data.assignees)])

            if issue_data.milestone:
                cmd.extend(["--milestone", issue_data.milestone])

            # コマンド実行
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # 一時ファイルを削除
            body_file.unlink(missing_ok=True)

            # 結果を解析
            output = result.stdout.strip()
            issue_url = output

            # URLからIssue番号を抽出
            issue_number = None
            if "/issues/" in issue_url:
                issue_number = int(issue_url.split("/issues/")[1])

            return {
                "success": True,
                "issue_number": issue_number,
                "issue_url": issue_url,
                "message": f"✅ Issue #{issue_number} を作成しました",
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": e.stderr.strip() if e.stderr else str(e),
                "message": "❌ Issueの作成に失敗しました",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "❌ 予期せぬエラーが発生しました",
            }

    def create_interactive(self) -> dict[str, Any]:
        """対話的にIssueを作成"""
        print("🤖 Agent Issue Creator\n")

        try:
            # タイトル入力
            title = input("Issue タイトルを入力してください:\n> ").strip()
            if not title:
                return {"success": False, "message": "❌ タイトルは必須です"}

            # タイプ選択
            print("\nIssue タイプを選択してください:")
            for key, info in self.ISSUE_TYPES.items():
                print(f"{key}. {info['emoji']} {info['label']}")

            issue_type = input("\n選択 (1-7): ").strip()
            if issue_type not in self.ISSUE_TYPES:
                return {"success": False, "message": "❌ 無効な選択です"}

            # 要件入力
            print("\n要件を入力してください (完了したら空行):")
            requirements = []
            while True:
                req = input("> ").strip()
                if not req:
                    break
                requirements.append(req)

            if not requirements:
                return {"success": False, "message": "❌ 少なくとも1つの要件が必要です"}

            # 技術スタック (オプション)
            tech_stack = input(
                "\n使用する技術スタックを入力してください (任意): "
            ).strip()

            # 制約事項 (オプション)
            constraints = input("\n制約事項があれば入力してください (任意): ").strip()

            # Agent実行設定
            auto_execute = (
                input("\nAgent自動実行を有効にしますか? (y/n): ").strip().lower() == "y"
            )

            # 優先度設定
            print("\n優先度を選択してください:")
            for key, info in self.PRIORITIES.items():
                print(f"{key}. {info['emoji']} {info['key'].capitalize()}")

            priority_choice = input("\n選択 (1-3): ").strip()
            priority_info = self.PRIORITIES.get(priority_choice, self.PRIORITIES["2"])
            priority = priority_info["key"]

            # 担当者指定 (オプション)
            assignees_input = input(
                "\n担当者を指定しますか? (GitHubユーザー名、カンマ区切り、空でスキップ): "
            ).strip()
            assignees = (
                [a.strip() for a in assignees_input.split(",") if a.strip()]
                if assignees_input
                else None
            )

            # IssueConfigを作成
            config = IssueConfig(
                title=title,
                issue_type=issue_type,
                requirements=requirements,
                tech_stack=tech_stack if tech_stack else None,
                constraints=constraints if constraints else None,
                auto_execute=auto_execute,
                priority=priority,
                assignees=assignees,
            )

            # Issueデータを作成
            issue_data = IssueData(
                title=config.title,
                body=self._create_issue_body(config),
                labels=self._create_labels(config),
                assignees=config.assignees,
            )

            # GitHubにIssueを作成
            result = self._create_github_issue(issue_data)

            if result["success"]:
                print("\n✅ Issue作成完了")
                print(f"Issue番号: #{result['issue_number']}")
                print(f"URL: {result['issue_url']}")

                if config.auto_execute:
                    print("\n🤖 Agent実行が開始されます (約3-5分)")
                    print(
                        f"進捗確認: npm run agents:parallel:exec -- --issue {result['issue_number']} --dry-run"
                    )

            return result

        except KeyboardInterrupt:
            return {"success": False, "message": "❌ 操作がキャンセルされました"}
        except Exception as e:
            return {"success": False, "message": f"❌ エラーが発生しました: {str(e)}"}

    def create_batch(self, yaml_file: str) -> list[dict[str, Any]]:
        """バッチでIssueを作成"""
        try:
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "issues" not in data:
                return [{"success": False, "message": "❌ 無効なYAMLファイルです"}]

            issues = data["issues"]
            results = []

            print("🤖 Batch Issue Creator")
            print(f"\n{yaml_file} を読み込み中...")
            print(f"{len(issues)}件のIssueを作成します\n")

            for i, issue_config in enumerate(issues, 1):
                print(f"{i}/{len(issues)}: {issue_config['title']}")

                # IssueConfigを作成
                config = IssueConfig(
                    title=issue_config["title"],
                    issue_type=str(
                        next(
                            k
                            for k, v in self.ISSUE_TYPES.items()
                            if v["key"] == issue_config["type"]
                        )
                    ),
                    requirements=issue_config.get("requirements", []),
                    tech_stack=issue_config.get("tech_stack"),
                    constraints=issue_config.get("constraints"),
                    auto_execute=issue_config.get("autoExecute", False),
                    priority=issue_config.get("priority", "medium"),
                    assignees=issue_config.get("assignees"),
                )

                # Issueデータを作成
                issue_data = IssueData(
                    title=config.title,
                    body=self._create_issue_body(config),
                    labels=self._create_labels(config),
                    assignees=config.assignees,
                )

                # GitHubにIssueを作成
                result = self._create_github_issue(issue_data)
                results.append(result)

                if result["success"]:
                    print(f"   ✅ Issue #{result['issue_number']} 作成")
                    if config.auto_execute:
                        print("   🤖 Agent実行開始")
                else:
                    print(f"   ❌ 作成失敗: {result['message']}")

            # サマリー表示
            success_count = sum(1 for r in results if r["success"])
            auto_count = sum(
                1
                for i, r in enumerate(results)
                if r["success"] and issues[i].get("autoExecute", False)
            )

            print("\n✅ バッチ作成完了")
            print(f"作成数: {success_count}件")
            print(f"Agent自動実行: {auto_count}件")
            print(f"手動実行待ち: {success_count - auto_count}件")

            return results

        except FileNotFoundError:
            return [
                {
                    "success": False,
                    "message": f"❌ ファイルが見つかりません: {yaml_file}",
                }
            ]
        except yaml.YAMLError as e:
            return [{"success": False, "message": f"❌ YAML解析エラー: {str(e)}"}]
        except Exception as e:
            return [{"success": False, "message": f"❌ エラーが発生しました: {str(e)}"}]


def main():
    """メイン実行関数"""
    if len(sys.argv) < 2:
        print("Usage: python issue_creator.py [interactive|batch <yaml_file>]")
        sys.exit(1)

    command = sys.argv[1]
    creator = IssueCreator()

    if command == "interactive":
        result = creator.create_interactive()
        sys.exit(0 if result["success"] else 1)

    elif command == "batch" and len(sys.argv) >= 3:
        yaml_file = sys.argv[2]
        results = creator.create_batch(yaml_file)
        success_count = sum(1 for r in results if r["success"])
        sys.exit(0 if success_count > 0 else 1)

    else:
        print("Usage: python issue_creator.py [interactive|batch <yaml_file>]")
        sys.exit(1)


if __name__ == "__main__":
    main()
