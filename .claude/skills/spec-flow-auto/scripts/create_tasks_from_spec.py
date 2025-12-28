#!/usr/bin/env python3
"""
Spec Workflow - SPECから実行タスクを分解するスクリプト

design.mdやtasks.mdから具体的な実行タスクを生成し、
Miyabiフレームワークのエージェント連携準備を行う
"""

import argparse
import json
import sys
from pathlib import Path


class SpecToTasksConverter:
    def __init__(self, spec_path: str, output_path: str):
        self.spec_path = Path(spec_path)
        self.output_path = Path(output_path)
        self.requirements_md = self.spec_path / "requirements.md"
        self.design_md = self.spec_path / "design.md"
        self.tasks_md = self.spec_path / "tasks.md"

    def parse_spec_files(self) -> dict:
        """SPECファイル群を解析"""
        spec_data = {}

        for file_path, file_key in [
            (self.requirements_md, "requirements"),
            (self.design_md, "design"),
            (self.tasks_md, "tasks"),
        ]:
            if file_path.exists():
                spec_data[file_key] = self._parse_markdown_file(file_path)

        return spec_data

    def _parse_markdown_file(self, file_path: Path) -> dict:
        """Markdownファイルを構造化して解析"""
        content = file_path.read_text(encoding="utf-8")

        # 見出しレベルごとにセクションを分割
        sections = {}
        current_section = None
        current_subsections = []

        for line in content.split("\n"):
            if line.startswith("#"):
                if current_section:
                    sections[current_section] = current_subsections
                    current_subsections = []

                level = len(line) - len(line.lstrip("#"))
                title = line.lstrip("# ").strip()
                current_section = {"level": level, "title": title, "content": []}
            else:
                if current_section and line.strip():
                    current_section["content"].append(line)

        if current_section:
            sections[current_section["title"]] = current_section

        return sections

    def generate_detailed_tasks(self, spec_data: dict) -> list[dict]:
        """詳細な実行タスクを生成"""
        tasks = []

        # design.mdから技術的タスクを抽出
        if "design" in spec_data:
            tasks.extend(self._extract_technical_tasks(spec_data["design"]))

        # requirements.mdから機能的タスクを抽出
        if "requirements" in spec_data:
            tasks.extend(self._extract_functional_tasks(spec_data["requirements"]))

        # 既存のtasks.mdからタスクを洗練
        if "tasks" in spec_data:
            tasks = self._refine_existing_tasks(tasks, spec_data["tasks"])

        return self._organize_tasks_by_priority(tasks)

    def _extract_technical_tasks(self, design_sections: dict) -> list[dict]:
        """design.mdから技術的実装タスクを抽出"""
        tasks = []

        for section_name, _section_data in design_sections.items():
            if "Architecture" in section_name:
                tasks.append(
                    {
                        "id": "ARCH-001",
                        "title": "アーキテクチャ実装",
                        "description": "設計書に基づいたシステムアーキテクチャの実装",
                        "type": "technical",
                        "priority": "high",
                        "estimated_hours": 16,
                        "dependencies": [],
                        "subtasks": [
                            "コンポーネント構造の実装",
                            "API Gatewayの設定",
                            "サービス間通信の実装",
                        ],
                    }
                )

            elif "Component Design" in section_name:
                tasks.append(
                    {
                        "id": "COMP-001",
                        "title": "コンポーネント開発",
                        "description": "各コンポーネントの具体的な実装",
                        "type": "development",
                        "priority": "high",
                        "estimated_hours": 24,
                        "dependencies": ["ARCH-001"],
                        "subtasks": [
                            "Frontendコンポーネント実装",
                            "Backendサービス実装",
                            "コンポーネント間連携テスト",
                        ],
                    }
                )

            elif "Database Design" in section_name:
                tasks.append(
                    {
                        "id": "DB-001",
                        "title": "データベース設計と実装",
                        "description": "データベーススキーマの実装とマイグレーション",
                        "type": "database",
                        "priority": "high",
                        "estimated_hours": 12,
                        "dependencies": [],
                        "subtasks": [
                            "スキーマ作成SQL",
                            "マイグレーションスクリプト",
                            "初期データ投入",
                        ],
                    }
                )

            elif "API Design" in section_name:
                tasks.append(
                    {
                        "id": "API-001",
                        "title": "APIエンドポイント実装",
                        "description": "RESTful APIの実装とテスト",
                        "type": "development",
                        "priority": "high",
                        "estimated_hours": 20,
                        "dependencies": ["DB-001"],
                        "subtasks": [
                            "エンドポイント実装",
                            "リクエスト/レスポンス検証",
                            "APIドキュメント作成",
                        ],
                    }
                )

        return tasks

    def _extract_functional_tasks(self, req_sections: dict) -> list[dict]:
        """requirements.mdから機能的タスクを抽出"""
        tasks = []

        for section_name, _section_data in req_sections.items():
            if "Functional Requirements" in section_name:
                # 機能要件から具体的な実装タスクを生成
                tasks.append(
                    {
                        "id": "FUNC-001",
                        "title": "機能要件実装",
                        "description": "要件定義に基づいた機能の実装",
                        "type": "feature",
                        "priority": "high",
                        "estimated_hours": 32,
                        "dependencies": ["API-001", "COMP-001"],
                        "subtasks": [
                            "コアビジネスロジック実装",
                            "ユースケース実装",
                            "機能テスト作成",
                        ],
                    }
                )

            elif "Security Requirements" in section_name:
                tasks.append(
                    {
                        "id": "SEC-001",
                        "title": "セキュリティ機能実装",
                        "description": "セキュリティ要件の実装",
                        "type": "security",
                        "priority": "critical",
                        "estimated_hours": 16,
                        "dependencies": ["FUNC-001"],
                        "subtasks": [
                            "認証認可機能実装",
                            "データ暗号化実装",
                            "セキュリティテスト",
                        ],
                    }
                )

        return tasks

    def _refine_existing_tasks(
        self, new_tasks: list[dict], existing_tasks: dict
    ) -> list[dict]:
        """既存タスクリストを洗練"""
        # 既存タスクの情報で新しいタスクを補強
        return new_tasks

    def _organize_tasks_by_priority(self, tasks: list[dict]) -> list[dict]:
        """優先順位でタスクを整理"""
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        sorted_tasks = sorted(
            tasks, key=lambda x: (priority_order.get(x["priority"], 99), x["id"])
        )

        # 依存関係に基づいてタスクを再配置
        ordered_tasks = []
        processed_ids = set()

        while len(ordered_tasks) < len(sorted_tasks):
            for task in sorted_tasks:
                if task["id"] in processed_ids:
                    continue

                # 依存タスクがすべて処理済みか確認
                deps_met = all(
                    dep in processed_ids for dep in task.get("dependencies", [])
                )

                if deps_met:
                    ordered_tasks.append(task)
                    processed_ids.add(task["id"])
                    break
            else:
                # 循環依存などで進まない場合、最初の未処理タスクを追加
                for task in sorted_tasks:
                    if task["id"] not in processed_ids:
                        ordered_tasks.append(task)
                        processed_ids.add(task["id"])
                        break

        return ordered_tasks

    def generate_miyabi_integration_tasks(self, detailed_tasks: list[dict]) -> dict:
        """Miyabiフレームワーク連携用のタスクを生成"""
        miyabi_tasks = {
            "coordinator_tasks": [],
            "issue_agent_tasks": [],
            "codegen_agent_tasks": [],
            "review_agent_tasks": [],
            "pr_agent_tasks": [],
            "deployment_agent_tasks": [],
            "test_agent_tasks": [],
        }

        for task in detailed_tasks:
            # CoordinatorAgent用タスク
            miyabi_tasks["coordinator_tasks"].append(
                {
                    "task_id": f"COORD-{task['id']}",
                    "title": f"調整: {task['title']}",
                    "description": f"{task['description']}の実行調整",
                    "type": "coordination",
                    "estimated_effort": "2h",
                }
            )

            # IssueAgent用タスク
            miyabi_tasks["issue_agent_tasks"].append(
                {
                    "task_id": f"ISSUE-{task['id']}",
                    "title": f"Issue: {task['title']}",
                    "description": "実装タスクのIssue作成とラベル管理",
                    "labels": ["implementation", task["type"], task["priority"]],
                    "complexity": self._estimate_complexity(task["estimated_hours"]),
                }
            )

            # CodeGenAgent用タスク
            if task["type"] in ["development", "feature", "technical"]:
                miyabi_tasks["codegen_agent_tasks"].append(
                    {
                        "task_id": f"CODE-{task['id']}",
                        "title": f"実装: {task['title']}",
                        "description": task["description"],
                        "subtasks": task["subtasks"],
                        "estimated_hours": task["estimated_hours"],
                    }
                )

            # TestAgent用タスク
            miyabi_tasks["test_agent_tasks"].append(
                {
                    "task_id": f"TEST-{task['id']}",
                    "title": f"テスト: {task['title']}",
                    "description": f"{task['title']}のテスト実施",
                    "test_types": ["unit", "integration"],
                    "coverage_target": 80,
                }
            )

        return miyabi_tasks

    def _estimate_complexity(self, hours: int) -> str:
        """工数から複雑度を推定"""
        if hours <= 8:
            return "small"
        if hours <= 24:
            return "medium"
        if hours <= 48:
            return "large"
        return "xlarge"

    def generate_task_files(self) -> None:
        """タスク関連ファイルを生成"""
        # SPEC解析
        spec_data = self.parse_spec_files()

        # 詳細タスク生成
        detailed_tasks = self.generate_detailed_tasks(spec_data)

        # Miyabi連携タスク生成
        miyabi_tasks = self.generate_miyabi_integration_tasks(detailed_tasks)

        # 出力ディレクトリ作成
        self.output_path.mkdir(parents=True, exist_ok=True)

        # 詳細タスクファイル
        self._write_detailed_tasks(detailed_tasks)

        # Miyabi連携ファイル
        self._write_miyabi_tasks(miyabi_tasks)

        # タスク実行計画
        self._write_execution_plan(detailed_tasks, miyabi_tasks)

        print("✅ Generated task files:")
        print(f"   📁 {self.output_path}")
        print("   📄 detailed_tasks.json")
        print("   📄 miyabi_integration.json")
        print("   📄 execution_plan.md")

    def _write_detailed_tasks(self, tasks: list[dict]) -> None:
        """詳細タスクをJSONファイルに出力"""
        output_file = self.output_path / "detailed_tasks.json"

        task_data = {
            "metadata": {
                "total_tasks": len(tasks),
                "total_estimated_hours": sum(t["estimated_hours"] for t in tasks),
                "generated_at": str(Path.cwd()),
            },
            "tasks": tasks,
        }

        output_file.write_text(
            json.dumps(task_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _write_miyabi_tasks(self, miyabi_tasks: dict) -> None:
        """Miyabi連携タスクをJSONファイルに出力"""
        output_file = self.output_path / "miyabi_integration.json"

        integration_data = {
            "metadata": {
                "framework": "Miyabi",
                "agents": list(miyabi_tasks.keys()),
                "generated_at": str(Path.cwd()),
            },
            "agent_tasks": miyabi_tasks,
        }

        output_file.write_text(
            json.dumps(integration_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _write_execution_plan(
        self, detailed_tasks: list[dict], miyabi_tasks: dict
    ) -> None:
        """実行計画をMarkdownファイルに出力"""
        output_file = self.output_path / "execution_plan.md"

        content = f"""# Implementation Execution Plan

## Overview

この実行計画は、SPECから生成された{len(detailed_tasks)}個のタスクを
Miyabiフレームワークの7エージェントで自律実行するための計画です。

## Task Summary

- **総タスク数**: {len(detailed_tasks)}
- **総工数**: {sum(t['estimated_hours'] for t in detailed_tasks)}時間
- **クリティカルパス**: {len([t for t in detailed_tasks if t['priority'] == 'critical'])}タスク

## Phase-by-Phase Execution

### Phase 1: Infrastructure Setup (Week 1)
{self._generate_phase_content([t for t in detailed_tasks if t['type'] in ['technical', 'database']])}

### Phase 2: Core Development (Week 2-3)
{self._generate_phase_content([t for t in detailed_tasks if t['type'] in ['development', 'feature']])}

### Phase 3: Integration & Testing (Week 4)
{self._generate_phase_content([t for t in detailed_tasks if t['type'] == 'testing'])}

### Phase 4: Security & Deployment (Week 5-6)
{self._generate_phase_content([t for t in detailed_tasks if t['type'] in ['security', 'deployment']])}

## Agent Assignment

### CoordinatorAgent
{chr(10).join([f"- {task['task_id']}: {task['title']}" for task in miyabi_tasks['coordinator_tasks']])}

### IssueAgent
{chr(10).join([f"- {task['task_id']}: {task['title']}" for task in miyabi_tasks['issue_agent_tasks']])}

### CodeGenAgent
{chr(10).join([f"- {task['task_id']}: {task['title']}" for task in miyabi_tasks['codegen_agent_tasks']])}

### TestAgent
{chr(10).join([f"- {task['task_id']}: {task['title']}" for task in miyabi_tasks['test_agent_tasks']])}

## Dependencies Graph

```
{self._generate_dependency_graph(detailed_tasks)}
```

## Risk Mitigation

### High Risk Items
- データベースパフォーマンス: 早期の負荷テストを実施
- セキュリティ実装: 定期的な脆弱性診断
- サードパーティ連携: モック環境での事前検証

## Success Metrics

- **品質目標**: コードカバレッジ80%以上
- **性能目標**: レスポンスタイム2秒以内
- **セキュリティ目標**: 高危険度脆弱性ゼロ
- **納期目標**: 6週間での完了
"""

        output_file.write_text(content, encoding="utf-8")

    def _generate_phase_content(self, tasks: list[dict]) -> str:
        """フェーズごとのコンテンツを生成"""
        if not tasks:
            return "該当タスクなし"

        content = ""
        for task in tasks:
            content += (
                f"- **{task['id']}**: {task['title']} ({task['estimated_hours']}h)\n"
            )

        return content

    def _generate_dependency_graph(self, tasks: list[dict]) -> str:
        """依存関係グラフを生成"""
        graph_lines = []
        for task in tasks:
            if task.get("dependencies"):
                for dep in task["dependencies"]:
                    graph_lines.append(f"{dep} -> {task['id']}")

        return "\n".join(graph_lines) if graph_lines else "No dependencies found"


def main():
    parser = argparse.ArgumentParser(
        description="Convert SPEC to detailed implementation tasks"
    )
    parser.add_argument("--spec-path", required=True, help="Path to SPEC directory")
    parser.add_argument("--output", required=True, help="Output directory for tasks")

    args = parser.parse_args()

    # SPECディレクトリ確認
    spec_path = Path(args.spec_path)
    if not spec_path.exists():
        print(f"❌ SPEC directory not found: {args.spec_path}")
        sys.exit(1)

    try:
        converter = SpecToTasksConverter(args.spec_path, args.output)
        converter.generate_task_files()

    except Exception as e:
        print(f"❌ Error converting SPEC to tasks: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
