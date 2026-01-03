#!/usr/bin/env python3
"""
GitHub Issue Monitor Integration - CI/CD Issue監視とGitHub Issue改善機能の統合システム
パイプライン監視とIssue改善を連携させ、リポジトリの品質を包括的に管理する
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scripts_operations.ci_cd.issue_creator import GitHubIssueCreator
from src.common.cli.processors.github_issue_improver import GitHubIssueImprover
from src.common.cli.processors.periodic_issue_improver import PeriodicIssueImprover


class GitHubIssueMonitorIntegration:
    """GitHub Issue監視と改善機能の統合システム"""

    def __init__(self):
        self.issue_creator = GitHubIssueCreator()
        self.issue_improver = GitHubIssueImprover()
        self.periodic_improver = PeriodicIssueImprover()

    def run_integrated_monitoring(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """統合監視を実行"""
        results = {
            "pipeline_monitoring": {"success": False, "message": ""},
            "issue_improvement": {"success": False, "message": ""},
            "integration_summary": {"success": False, "issues_created": 0, "issues_improved": 0},
        }

        # 1. パイプライン監視（既存機能）
        try:
            pipeline_result = self._run_pipeline_monitoring(health_data)
            results["pipeline_monitoring"] = pipeline_result

            if pipeline_result["success"]:
                results["integration_summary"]["issues_created"] = pipeline_result.get("issues_created", 0)

        except Exception as e:
            results["pipeline_monitoring"] = {"success": False, "message": f"パイプライン監視失敗: {str(e)}"}

        # 2. Issue改善実行
        try:
            improvement_result = self._run_issue_improvement()
            results["issue_improvement"] = improvement_result

            if improvement_result["success"]:
                results["integration_summary"]["issues_improved"] = improvement_result.get("improved_count", 0)

        except Exception as e:
            results["issue_improvement"] = {"success": False, "message": f"Issue改善失敗: {str(e)}"}

        # 3. 統合サマリー
        pipeline_success = results["pipeline_monitoring"]["success"]
        improvement_success = results["issue_improvement"]["success"]

        results["integration_summary"]["success"] = pipeline_success or improvement_success

        return results

    def _run_pipeline_monitoring(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """パイプライン監視を実行"""
        if not hasattr(self.issue_creator, "create_critical_health_issue"):
            return {"success": False, "message": "Issue Creatorメソッドが利用できません"}

        # 健康度チェック
        health_percentage = health_data.get("health_percentage", 100)
        threshold = health_data.get("threshold", 50)

        if health_percentage >= threshold:
            return {
                "success": True,
                "message": f"パイプライン健康度は良好です ({health_percentage}%)",
                "issues_created": 0,
            }

        # Critical Issue作成
        issue_created = self.issue_creator.create_critical_health_issue(health_data)

        if issue_created:
            return {
                "success": True,
                "message": f"Critical Issueを作成しました (健康度: {health_percentage}%)",
                "issues_created": 1,
            }
        else:
            return {"success": False, "message": "Critical Issueの作成に失敗しました", "issues_created": 0}

    def _run_issue_improvement(self) -> Dict[str, Any]:
        """Issue改善を実行"""
        result = self.issue_improver.process()

        if result.success:
            # 改善数をメッセージから抽出
            improved_count = 0
            try:
                import re

                match = re.search(r"(\d+)/(\d+).*改善しました", result.message)
                if match:
                    improved_count = int(match.group(1))
            except:
                pass

            return {"success": True, "message": result.message, "improved_count": improved_count}
        else:
            return {"success": False, "message": result.message, "improved_count": 0}

    def start_periodic_monitoring(self, interval_hours: int = 24, cycles: int = 0) -> Dict[str, Any]:
        """周期監視を開始"""
        # 環境変数で設定
        os.environ["PERIODIC_INTERVAL"] = str(interval_hours)
        os.environ["PERIODIC_CYCLES"] = str(cycles)

        # 周期実行開始
        result = self.periodic_improver.process()

        return {"success": result.success, "message": result.message}

    def get_monitoring_status(self) -> Dict[str, Any]:
        """監視ステータスを取得"""
        status_file = "metrics/periodic_issue_improver_status.json"

        try:
            if os.path.exists(status_file):
                with open(status_file, "r", encoding="utf-8") as f:
                    status_data = json.load(f)

                # 時間を計算
                last_run = datetime.fromisoformat(status_data.get("last_run", ""))
                now = datetime.now()
                hours_since_last_run = (now - last_run).total_seconds() / 3600

                return {
                    "status": "active" if status_data.get("running", False) else "stopped",
                    "last_cycle": status_data.get("last_cycle", 0),
                    "last_run": status_data.get("last_run", ""),
                    "hours_since_last_run": hours_since_last_run,
                    "last_result": status_data.get("last_result", {}),
                    "next_run_estimate": (
                        f"{24 - hours_since_last_run:.1f}時間後" if hours_since_last_run < 24 else "即時実行推奨"
                    ),
                }
            else:
                return {"status": "not_started", "message": "監視ステータスファイルが存在しません"}

        except Exception as e:
            return {"status": "error", "message": f"ステータス取得に失敗: {str(e)}"}


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Issue Monitor Integration")
    parser.add_argument("--mode", choices=["integrated", "periodic", "status"], required=True, help="実行モード")
    parser.add_argument("--health-percentage", type=int, help="パイプライン健康度")
    parser.add_argument("--health-status", help="健康度ステータス")
    parser.add_argument("--total-score", type=int, help="合計スコア")
    parser.add_argument("--max-score", type=int, help="最大スコア")
    parser.add_argument("--duration", type=float, help="実行時間")
    parser.add_argument("--pipeline-mode", help="パイプラインモード")
    parser.add_argument("--phase-results", help="フェーズ結果（JSON）")
    parser.add_argument("--threshold", type=int, default=50, help="Issue作成閾値")
    parser.add_argument("--interval", type=int, default=24, help="周期実行間隔（時間）")
    parser.add_argument("--cycles", type=int, default=0, help="最大サイクル数")

    args = parser.parse_args()

    integration = GitHubIssueMonitorIntegration()

    if args.mode == "integrated":
        # 統合監視モード
        if not all(
            [
                args.health_percentage is not None,
                args.health_status,
                args.total_score is not None,
                args.max_score is not None,
                args.duration is not None,
                args.pipeline_mode,
            ]
        ):
            print("❌ 統合監視モードには健康度関連のパラメータがすべて必要です")
            sys.exit(1)

        health_data = {
            "health_percentage": args.health_percentage,
            "health_status": args.health_status,
            "total_score": args.total_score,
            "max_score": args.max_score,
            "duration": args.duration,
            "pipeline_mode": args.pipeline_mode,
            "threshold": args.threshold,
        }

        if args.phase_results:
            try:
                health_data["phase_results"] = json.loads(args.phase_results)
            except json.JSONDecodeError:
                print("❌ phase-resultsのJSON形式が不正です")
                sys.exit(1)

        results = integration.run_integrated_monitoring(health_data)

        # 結果表示
        print("=== GitHub Issue 統合監視結果 ===")
        pipeline_status = "✅" if results["pipeline_monitoring"]["success"] else "❌"
        improvement_status = "✅" if results["issue_improvement"]["success"] else "❌"
        print(f"パイプライン監視: {pipeline_status} {results['pipeline_monitoring']['message']}")
        print(f"Issue改善: {improvement_status} {results['issue_improvement']['message']}")
        print(
            f"統合サマリー: 作成Issue={results['integration_summary']['issues_created']}, 改善Issue={results['integration_summary']['issues_improved']}"
        )

        success = results["integration_summary"]["success"]

    elif args.mode == "periodic":
        # 周期監視モード
        result = integration.start_periodic_monitoring(args.interval, args.cycles)
        periodic_status = "✅" if result["success"] else "❌"
        print(f"周期監視: {periodic_status} {result['message']}")
        success = result["success"]

    elif args.mode == "status":
        # ステータス確認モード
        status = integration.get_monitoring_status()

        print("=== GitHub Issue 監視ステータス ===")
        print(f"ステータス: {status['status']}")
        if status["status"] == "active":
            print(f"最終サイクル: #{status.get('last_cycle', 0)}")
            print(f"最終実行: {status.get('last_run', '')}")
            print(f"経過時間: {status.get('hours_since_last_run', 0):.1f}時間")
            print(f"次回実行予定: {status.get('next_run_estimate', '')}")
        elif "message" in status:
            print(f"詳細: {status['message']}")

        success = status["status"] != "error"

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
