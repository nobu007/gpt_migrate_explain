#!/usr/bin/env python3
"""
Enhanced Constitutional Compliance Checker with Integrated Module Discovery

既存のconstitutional-compliance-checker.pyを強化し、新しい統合モジュール発見サービスを使用。
デフォルトで上位10個のモジュールをチェックし、--allフラグで全モジュール対応。
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts_operations.common.module_discovery_service import ModuleDiscoveryService

logger = logging.Logger(__name__)


class EnhancedConstitutionalComplianceChecker:
    """強化版憲法コンプライアンスチェッカー - 統合モジュール発見サービス使用"""

    # 必須.moduleファイルセット
    REQUIRED_MODULE_FILES = [
        "TASKS.md",
        "MODULE_GOALS.md",
        "ARCHITECTURE.md",
        "MODULE_STRUCTURE.md",
        "BEHAVIOR.md",
        "IMPLEMENTATION.md",
        "TEST.md",
        "FEEDBACK.md",
    ]

    def __init__(self, project_root: Optional[Path] = None) -> None:
        """強化版憲法コンプライアンスチェッカーの初期化

        Args:
            project_root: プロジェクトのルートディレクトリパス
                         Noneの場合は現在の作業ディレクトリを使用
        """
        self.project_root = project_root or Path.cwd()
        self.module_discovery = ModuleDiscoveryService(self.project_root)
        self.logger = logging.Logger(__name__)

    def find_module_directories_filtered(self, all_modules: bool = False, limit: int = 10) -> List[Path]:
        """フィルタリングされた.moduleディレクトリを検索

        統合モジュール発見サービスを使用して、プロジェクト内の.moduleディレクトリを
        フィルタリングして取得します。

        Args:
            all_modules: 全モジュールを対象とする場合はTrue、制限する場合はFalse
            limit: チェック対象モジュールの上限数（all_modules=Falseの場合に適用）

        Returns:
            発見された.moduleディレクトリのパスのリスト
        """
        # 統合サービスで親ディレクトリを取得
        parent_modules = self.module_discovery.get_filtered_modules(
            all_modules=all_modules,
            limit=limit,
            discovery_method="rglob",  # 既存実装との互換性維持
        )

        # .moduleディレクトリパスを返す（既存実装との互換性）
        module_dirs = []
        for parent_dir in parent_modules:
            module_config_dir = parent_dir / ".module"
            if module_config_dir.exists():
                module_dirs.append(module_config_dir)

        self.logger.info(f"Found {len(module_dirs)} .module directories for compliance check")
        return module_dirs

    def check_constitutional_files(self) -> List[Dict[str, Any]]:
        """基本憲法ファイルの存在チェック

        プロジェクトルートに必須の憲法ファイル（SYSTEM_CONSTITUTION.md、
        AGENTS.md、CLAUDE.md）の存在を確認します。

        Returns:
            憲法ファイルの検証結果リスト。各要素は辞書形式で
            severity、message、locationキーを含む
        """
        results = []
        constitutional_files = ["SYSTEM_CONSTITUTION.md", "AGENTS.md", "CLAUDE.md"]

        for filename in constitutional_files:
            file_path = self.project_root / filename
            if file_path.exists():
                results.append(
                    {
                        "severity": "INFO",
                        "message": f"Constitutional file present: {filename}",
                        "location": str(file_path),
                    }
                )
            else:
                results.append(
                    {
                        "severity": "CRITICAL",
                        "message": f"Missing constitutional file: {filename}",
                        "location": str(self.project_root),
                    }
                )

        return results

    def check_module_files(self, module_dir: Path) -> List[Dict[str, Any]]:
        """モジュールファイルの存在チェック

        指定された.moduleディレクトリ内の必須ファイル（8ファイルセット）の
        存在を確認します。

        Args:
            module_dir: チェック対象の.moduleディレクトリのパス

        Returns:
            モジュールファイルの検証結果リスト。各要素は辞書形式で
            severity、message、locationキーを含む
        """
        results = []
        missing_files = []

        for required_file in self.REQUIRED_MODULE_FILES:
            file_path = module_dir / required_file
            if not file_path.exists():
                missing_files.append(required_file)

        if missing_files:
            results.append(
                {
                    "severity": "CRITICAL",
                    "message": f"Missing required .module files: {', '.join(missing_files)}",
                    "location": str(module_dir),
                }
            )
        else:
            results.append(
                {
                    "severity": "INFO",
                    "message": "All 8 required .module files present",
                    "location": str(module_dir),
                }
            )

        return results

    def check_comprehensive_compliance(
        self, all_modules: bool = False, limit: int = 10
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """包括的検証の実行（フィルタリング対応版）

        プロジェクト全体の憲法コンプライアンスを検証します。
        基本憲法ファイルと.moduleディレクトリの必須ファイルセットの存在を確認します。

        Args:
            all_modules (bool): True の場合は全モジュールをチェック、
                               False の場合は上位 limit 個のモジュールのみをチェック
            limit (int): チェック対象モジュールの上限数（all_modules=False の場合に適用）
                        デフォルトは10

        Returns:
            Tuple[bool, List[Dict[str, Any]]]: タプルの最初の要素は全体的な合格/不合格判定（bool）、
                                              二番目の要素は詳細な検証結果のリスト

        Raises:
            FileNotFoundError: プロジェクトルートディレクトリが見つからない場合
        """
        all_results = []

        # 1. 基本憲法ファイル検証
        all_results.extend(self.check_constitutional_files())

        # 2. フィルタリングされた.moduleディレクトリ検索と検証
        module_dirs = self.find_module_directories_filtered(all_modules=all_modules, limit=limit)

        if not module_dirs:
            all_results.append(
                {
                    "severity": "WARNING",
                    "message": "No .module directories found for compliance check",
                    "location": str(self.project_root),
                }
            )
            return True, all_results

        # フィルタリング情報を結果に追加
        filter_info = f"{'All' if all_modules else f'Top {limit}'} modules selected for compliance check"
        all_results.append(
            {
                "severity": "INFO",
                "message": f"Compliance check scope: {filter_info} ({len(module_dirs)} modules)",
                "location": str(self.project_root),
            }
        )

        # 各.moduleディレクトリに対する多層検証プロセス
        critical_issues = 0
        for module_dir in module_dirs:
            # ファイル存在チェック
            file_results = self.check_module_files(module_dir)
            all_results.extend(file_results)

            # LOGIC_CC01_クリティカル問題集計: 各モジュールのクリティカル問題数を累積
            critical_issues += sum(1 for result in file_results if result["severity"] == "CRITICAL")

        # LOGIC_CC02_全体判定: クリティカル問題が一つでもあれば全体として不合格
        overall_pass = critical_issues == 0

        return overall_pass, all_results

    def print_results(self, results: List[Dict[str, Any]], show_summary: bool = True) -> None:
        """コンプライアンスチェック結果の表示

        検証結果を整形してコンソールに出力します。サマリー表示の有無を
        選択することができます。

        Args:
            results: 検証結果のリスト。各要素は辞書形式で
                    severity、message、locationキーを含む
            show_summary: サマリー情報を表示する場合はTrue
        """
        if show_summary:
            total = len(results)
            critical = sum(1 for r in results if r["severity"] == "CRITICAL")
            warnings = sum(1 for r in results if r["severity"] == "WARNING")
            info = sum(1 for r in results if r["severity"] == "INFO")

            print("\n📊 Compliance Check Summary")
            print(f"Total issues: {total}")
            print(f"🔴 Critical: {critical}")
            print(f"🟡 Warning: {warnings}")
            print(f"🔵 Info: {info}")
            print("-" * 60)

        for result in results:
            severity_icon = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🔵"}.get(result["severity"], "⚪")
            print(f"{severity_icon} [{result['severity']}] {result['message']}")
            if result.get("location"):
                print(f"   📁 {result['location']}")


def main() -> int:
    """メイン実行関数 - フィルタリング対応版

    コマンドライン引数を解析し、強化版憲法コンプライアンスチェックを実行します。
    デフォルトで上位10個のモジュールをチェックし、--allフラグで全モジュール対応。

    Returns:
        int: 終了コード（0: 合格、1: 不合格）

    Raises:
        SystemExit: argparse がコマンドライン引数の解析に失敗した場合
        FileNotFoundError: プロジェクトルートまたは必要なモジュールファイルが見つからない場合
    """
    parser = argparse.ArgumentParser(description="Enhanced Constitutional Compliance Check with Module Filtering")
    parser.add_argument("--all", action="store_true", help="Check all modules instead of top 10")
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of top modules to check (default: 10)",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress summary output")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # ロギング設定
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    checker = EnhancedConstitutionalComplianceChecker()

    if not args.quiet:
        print("🔍 Starting Enhanced Constitutional Compliance Check...")
        if args.all:
            print("📋 Mode: Checking ALL modules")
        else:
            print(f"📋 Mode: Checking top {args.limit} recently updated modules")
        print()

    # 包括的検証実行
    overall_pass, results = checker.check_comprehensive_compliance(all_modules=args.all, limit=args.limit)

    # 結果表示
    checker.print_results(results, show_summary=not args.quiet)

    if not args.quiet:
        print()
        if overall_pass:
            print("✅ Overall compliance: PASS")
            print("All critical compliance requirements are satisfied.")
        else:
            print("❌ Overall compliance: FAIL")
            print("Critical compliance issues require immediate attention.")

    # 終了コードを設定（0: 合格, 1: 不合格）
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
