#!/usr/bin/env python3
"""
Refactored Codebase Analyzer - Modular and focused version

This is the refactored version of the original 1948-line monolithic analyzer.
Split into focused modules following single responsibility principle.
"""

import argparse
import multiprocessing
import sys
import time
from pathlib import Path

# Import the modular components
try:
    from modules.advanced_analyzer import (
        ROPE_AVAILABLE,
        AdvancedCodeAnalyzer,
        AnalyzerConfig,
    )
    from modules.jscpd_analyzer import JSCPD_AVAILABLE, JSCPDAnalyzer, JSCPDConfig
    from modules.main_analyzer import CodebaseAnalyzer
    from modules.report_generator import generate_markdown_report
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Please ensure all module files are properly created.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="コードベースを分析して改善提案を生成 (リファクタリング版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--path", required=True, help="分析するプロジェクトのパス (必須)"
    )
    parser.add_argument(
        "--output",
        default="improvement_tasks.md",
        help="出力ファイル名 (デフォルト: improvement_tasks.md)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="出力形式 (デフォルト: markdown)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="並列処理のワーカー数",
    )
    parser.add_argument("--verbose", action="store_true", help="詳細な分析情報を表示")

    args = parser.parse_args()

    # プロジェクトの存在確認
    try:
        project_path = Path(args.path).resolve()
        if not project_path.exists():
            print(f"❌ エラー: プロジェクトパスが存在しません: {project_path}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ エラー: パスの処理に失敗しました: {e}")
        sys.exit(1)

    if args.verbose:
        print("🔧 設定:")
        print(f"  - プロジェクトパス: {args.path}")
        print(f"  - ropeライブラリ: {'利用可能' if ROPE_AVAILABLE else '利用不可'}")
        print(f"  - jscpd (JS/TS): {'利用可能' if JSCPD_AVAILABLE else '利用不可'}")

    # 設定クラスを初期化
    config = AnalyzerConfig()
    jscpd_config = JSCPDConfig()

    # ワーカー数を決定
    max_workers = (
        args.workers
        or config.default_max_workers
        or min(multiprocessing.cpu_count(), 4)
    )

    # 分析実行
    start_time = time.time()
    analyzer = CodebaseAnalyzer(str(project_path), config, jscpd_config)
    result = analyzer.analyze_project(max_workers=max_workers)
    analysis_time = time.time() - start_time

    # 結果を出力
    if args.format == "json":
        import json

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    else:
        generate_markdown_report(result, args.output)

    # 完了メッセージ
    total_issues = result["summary"]["total_issues"]
    high_issues = result["summary"]["high_priority_issues"]

    print(f"\n🎉 分析完了! 時間: {analysis_time:.2f}秒")
    print(f"📋 発見された問題: {total_issues}件")
    print(f"  🔴 高優先度: {high_issues}件")


if __name__ == "__main__":
    main()
