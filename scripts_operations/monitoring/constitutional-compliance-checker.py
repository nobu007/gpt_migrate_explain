#!/usr/bin/env python3
"""
憲法コンプライアンスチェックスクリプト (高度検証版)
.moduleシステムの完全性とアーキテクチャ一貫性を検証
"""

import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ValidationSeverity(Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ValidationResult:
    severity: ValidationSeverity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None


class ConstitutionalComplianceChecker:
    """憲法コンプライアンスチェッカー - .moduleシステムの高度検証"""

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

    # 必須メタデータフィールド
    REQUIRED_METADATA_FIELDS = [
        "目的 (Purpose)",
        "上位文書 (Parent Document)",
        "必読文書 (Required Reading)",
        "状態 (Status)",
        "最終更新日時 (Last Updated)",
    ]

    # 階層依存関係 (MODULE_GOALS -> ARCHITECTURE -> MODULE_STRUCTURE -> ...)
    DESIGN_FLOW_DEPENDENCIES = {
        "ARCHITECTURE.md": ["MODULE_GOALS.md"],
        "MODULE_STRUCTURE.md": ["ARCHITECTURE.md"],
        "BEHAVIOR.md": ["MODULE_STRUCTURE.md"],
        "IMPLEMENTATION.md": ["BEHAVIOR.md"],
        "TEST.md": ["IMPLEMENTATION.md", "BEHAVIOR.md"],
        "FEEDBACK.md": ["TEST.md"],
    }

    def __init__(self):
        self.validation_results: List[ValidationResult] = []

    def check_constitutional_files(self) -> List[ValidationResult]:
        """基本憲法ファイルの存在チェック"""
        required_files = ["AGENTS.md", "SYSTEM_CONSTITUTION.md"]
        optional_files = ["CLAUDE.md", "README.md"]

        for file in required_files:
            if not Path(file).is_file():
                self.validation_results.append(
                    ValidationResult(
                        ValidationSeverity.CRITICAL,
                        f"Missing required constitutional file: {file}",
                    )
                )
            else:
                self.validation_results.append(
                    ValidationResult(
                        ValidationSeverity.INFO,
                        f"Found required constitutional file: {file}",
                    )
                )

        for file in optional_files:
            if not Path(file).is_file():
                self.validation_results.append(
                    ValidationResult(ValidationSeverity.WARNING, f"Missing optional file: {file}")
                )

        return self.validation_results

    def find_module_directories(self) -> List[Path]:
        """全ての.moduleディレクトリを検索"""
        module_dirs = []
        for path in Path(".").rglob(".module"):
            if path.is_dir():
                module_dirs.append(path)
        return module_dirs

    def validate_module_file_existence(self, module_dir: Path) -> List[ValidationResult]:
        """モジュール内必須ファイル存在チェック"""
        results = []
        missing_files = []

        for required_file in self.REQUIRED_MODULE_FILES:
            file_path = module_dir / required_file
            if not file_path.is_file():
                missing_files.append(required_file)
                results.append(
                    ValidationResult(
                        ValidationSeverity.CRITICAL,
                        f"Missing required .module file: {required_file}",
                        str(module_dir),
                    )
                )

        if not missing_files:
            results.append(
                ValidationResult(
                    ValidationSeverity.INFO,
                    "All 8 required .module files present",
                    str(module_dir),
                )
            )

        return results

    def extract_metadata(self, file_path: Path) -> Dict[str, str]:
        """ファイルからメタデータを抽出"""
        metadata = {}
        if not file_path.is_file():
            return metadata

        try:
            content = file_path.read_text(encoding="utf-8")

            # メタデータセクションを抽出
            metadata_pattern = r"## 1\. メタデータ\s*\n(.*?)(?=\n## |\n---|\Z)"
            metadata_match = re.search(metadata_pattern, content, re.DOTALL)

            if metadata_match:
                metadata_section = metadata_match.group(1)

                # 各フィールドを抽出
                field_pattern = r"- \*\*(.*?)\*\*:\s*(.*?)(?=\n- \*\*|\n\n|\Z)"
                for match in re.finditer(field_pattern, metadata_section, re.DOTALL):
                    field_name = match.group(1).strip()
                    field_value = match.group(2).strip()
                    metadata[field_name] = field_value

        except Exception:
            pass  # ファイル読み取りエラーは無視

        return metadata

    def validate_metadata_fields(self, file_path: Path) -> List[ValidationResult]:
        """メタデータフィールドの完全性チェック"""
        results = []
        metadata = self.extract_metadata(file_path)

        missing_fields = []
        for required_field in self.REQUIRED_METADATA_FIELDS:
            if required_field not in metadata:
                missing_fields.append(required_field)

        if missing_fields:
            results.append(
                ValidationResult(
                    ValidationSeverity.WARNING,
                    f"Missing metadata fields: {', '.join(missing_fields)}",
                    str(file_path),
                )
            )
        else:
            results.append(
                ValidationResult(
                    ValidationSeverity.INFO,
                    "All required metadata fields present",
                    str(file_path),
                )
            )

        return results

    def validate_architectural_consistency(self, module_dir: Path) -> List[ValidationResult]:
        """アーキテクチャ一貫性チェック - ファイル間参照関係"""
        results = []

        for dependent_file, dependency_files in self.DESIGN_FLOW_DEPENDENCIES.items():
            dependent_path = module_dir / dependent_file

            if not dependent_path.is_file():
                continue  # ファイルが存在しない場合はスキップ

            try:
                dependent_path.read_text(encoding="utf-8")
                metadata = self.extract_metadata(dependent_path)
                parent_doc = metadata.get("上位文書 (Parent Document)", "")

                # 上位文書が依存関係に合致しているかチェック
                found_valid_reference = False
                for dependency_file in dependency_files:
                    if dependency_file in parent_doc or dependency_file.replace(".md", "") in parent_doc:
                        found_valid_reference = True
                        break

                if not found_valid_reference and dependency_files:
                    results.append(
                        ValidationResult(
                            ValidationSeverity.WARNING,
                            f"Architectural consistency issue: {dependent_file} should reference one of {dependency_files} as parent document, but references: '{parent_doc}'",
                            str(dependent_path),
                        )
                    )
                else:
                    results.append(
                        ValidationResult(
                            ValidationSeverity.INFO,
                            f"Architectural consistency OK: {dependent_file} properly references parent document",
                            str(dependent_path),
                        )
                    )

            except Exception as e:
                results.append(
                    ValidationResult(
                        ValidationSeverity.WARNING,
                        f"Could not validate architectural consistency for {dependent_file}: {str(e)}",
                        str(dependent_path),
                    )
                )

        return results

    def validate_tasks_integration(self, module_dir: Path) -> List[ValidationResult]:
        """TASKS.mdと他ファイルの統合チェック"""
        results = []
        tasks_path = module_dir / "TASKS.md"

        if not tasks_path.is_file():
            results.append(
                ValidationResult(
                    ValidationSeverity.CRITICAL,
                    "TASKS.md missing - central task coordination impossible",
                    str(module_dir),
                )
            )
            return results

        try:
            tasks_content = tasks_path.read_text(encoding="utf-8")

            # タスクが定義されているかチェック
            task_pattern = r"- \[[ x]\].*?(?=\n- \[|\n\n|\Z)"
            tasks = re.findall(task_pattern, tasks_content, re.DOTALL)

            if not tasks:
                results.append(
                    ValidationResult(
                        ValidationSeverity.WARNING,
                        "No tasks defined in TASKS.md",
                        str(tasks_path),
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        ValidationSeverity.INFO,
                        f"Found {len(tasks)} tasks in TASKS.md",
                        str(tasks_path),
                    )
                )

        except Exception as e:
            results.append(
                ValidationResult(
                    ValidationSeverity.WARNING,
                    f"Could not validate TASKS.md: {str(e)}",
                    str(tasks_path),
                )
            )

        return results

    def validate_feedback_quality(self, module_dir: Path) -> List[ValidationResult]:
        """FEEDBACK.md品質スコア検証"""
        results = []
        feedback_path = module_dir / "FEEDBACK.md"

        if not feedback_path.is_file():
            results.append(
                ValidationResult(
                    ValidationSeverity.WARNING,
                    "FEEDBACK.md missing - quality tracking impossible",
                    str(feedback_path),
                )
            )
            return results

        try:
            feedback_content = feedback_path.read_text(encoding="utf-8")

            # 品質スコアパターンをチェック
            quality_score_pattern = r"品質スコア.*?(\d+(?:\.\d+)?)[%％]"
            quality_matches = re.findall(quality_score_pattern, feedback_content, re.IGNORECASE)

            if quality_matches:
                latest_score = float(quality_matches[-1])  # 最後のスコアを使用

                if latest_score < 90:
                    results.append(
                        ValidationResult(
                            ValidationSeverity.CRITICAL,
                            f"Low quality score detected: {latest_score}% (threshold: 90%)",
                            str(feedback_path),
                        )
                    )
                elif latest_score < 95:
                    results.append(
                        ValidationResult(
                            ValidationSeverity.WARNING,
                            f"Quality score below optimal: {latest_score}% (optimal: ≥95%)",
                            str(feedback_path),
                        )
                    )
                else:
                    results.append(
                        ValidationResult(
                            ValidationSeverity.INFO,
                            f"Quality score excellent: {latest_score}%",
                            str(feedback_path),
                        )
                    )
            else:
                results.append(
                    ValidationResult(
                        ValidationSeverity.WARNING,
                        "No quality score found in FEEDBACK.md",
                        str(feedback_path),
                    )
                )

        except Exception as e:
            results.append(
                ValidationResult(
                    ValidationSeverity.WARNING,
                    f"Could not validate FEEDBACK.md quality: {str(e)}",
                    str(feedback_path),
                )
            )

        return results

    def run_comprehensive_validation(self) -> Tuple[bool, List[ValidationResult]]:
        """包括的検証の実行

        .moduleシステムの全体的な整合性とアーキテクチャ一貫性を検証します。
        基本憲法ファイル、モジュールディレクトリ、必須ファイル、メタデータ、
        アーキテクチャ依存関係、タスク統合、フィードバック品質を順次チェックします。

        検証プロセスは以下の順序で実行されます:
        1. 基本憲法ファイル（AGENTS.md, SYSTEM_CONSTITUTION.md）の存在確認
        2. .moduleディレクトリの検索と必須8ファイルセットの存在確認
        3. 各ファイルのメタデータフィールドの完全性確認
        4. アーキテクチャ依存関係の一貫性確認（設計フロー準拠）
        5. TASKS.mdとの統合状況確認
        6. FEEDBACK.mdの品質スコア確認

        Args:
            なし

        Returns:
            Tuple[bool, List[ValidationResult]]:
                - 第1要素: 検証成功フラグ（CRITICALエラーがなければTrue）
                - 第2要素: 全ての検証結果を含むValidationResultのリスト
                          severity順（CRITICAL -> WARNING -> INFO）で分類可能

        Raises:
            FileNotFoundError: 憲法ファイルが見つからない場合
            PermissionError: ファイル読み取り権限がない場合
            UnicodeDecodeError: ファイルエンコーディングエラーが発生した場合
            Exception: その他のファイル読み取りエラーや解析エラーが発生した場合
                      （個別の例外は内部で処理され、検証結果として記録）

        Note:
            本メソッドは複数の検証責務を持つため、将来的な保守性向上のため以下の改善を推奨:
            - MetadataValidator: メタデータ検証専用クラス
            - ArchitectureValidator: アーキテクチャ一貫性検証専用クラス
            - QualityValidator: 品質スコア検証専用クラス

        TODO: クラス分離提案 - 各検証タイプ（メタデータ、アーキテクチャ、品質等）を
              独立したValidatorクラスに分離し、責務を明確化することを検討
        """
        all_results = []

        # 1. 基本憲法ファイルチェック
        all_results.extend(self.check_constitutional_files())

        # 2. .moduleディレクトリ検索と検証
        module_dirs = self.find_module_directories()

        if not module_dirs:
            all_results.append(
                ValidationResult(
                    ValidationSeverity.WARNING,
                    "No .module directories found in project",
                )
            )
            return True, all_results

        # LOGIC_004_性能制約監視とアラート自動化システム - 各.moduleディレクトリに対する多層検証プロセス
        for module_dir in module_dirs:
            # ファイル存在チェック
            all_results.extend(self.validate_module_file_existence(module_dir))

            # メタデータ検証
            for file_name in self.REQUIRED_MODULE_FILES:
                file_path = module_dir / file_name
                if file_path.is_file():
                    all_results.extend(self.validate_metadata_fields(file_path))

            # アーキテクチャ一貫性チェック
            all_results.extend(self.validate_architectural_consistency(module_dir))

            # TASKS.md統合チェック
            all_results.extend(self.validate_tasks_integration(module_dir))

            # FEEDBACK.md品質チェック
            all_results.extend(self.validate_feedback_quality(module_dir))

        # 成功判定: CRITICALエラーがないかチェック
        has_critical_errors = any(result.severity == ValidationSeverity.CRITICAL for result in all_results)

        return not has_critical_errors, all_results

    def print_validation_report(self, success: bool, results: List[ValidationResult]) -> None:
        """検証結果レポートの出力"""
        print("🔍 Constitutional Compliance Check Report")
        print("=" * 60)

        # 結果をseverity別に分類
        critical_results = [r for r in results if r.severity == ValidationSeverity.CRITICAL]
        warning_results = [r for r in results if r.severity == ValidationSeverity.WARNING]
        info_results = [r for r in results if r.severity == ValidationSeverity.INFO]

        # サマリー
        print("📊 Validation Summary:")
        print(f"   • Critical Issues: {len(critical_results)}")
        print(f"   • Warnings: {len(warning_results)}")
        print(f"   • Info Messages: {len(info_results)}")
        print(f"   • Overall Status: {'✅ PASS' if success else '❌ FAIL'}")
        print()

        # CRITICAL issues
        if critical_results:
            print("🚨 CRITICAL ISSUES:")
            for result in critical_results:
                location = f" ({result.file_path})" if result.file_path else ""
                print(f"   ❌ {result.message}{location}")
            print()

        # WARNINGS
        if warning_results:
            print("⚠️ WARNINGS:")
            for result in warning_results:
                location = f" ({result.file_path})" if result.file_path else ""
                print(f"   ⚠️ {result.message}{location}")
            print()

        # INFO (最初の10件のみ表示)
        if info_results:
            print("ℹ️ VALIDATION SUCCESS (first 10):")
            for result in info_results[:10]:
                location = f" ({result.file_path})" if result.file_path else ""
                print(f"   ✅ {result.message}{location}")
            if len(info_results) > 10:
                print(f"   ... and {len(info_results) - 10} more successful validations")
            print()


def main() -> None:
    """メイン実行関数 - 憲法コンプライアンスチェックのエントリーポイント

    憲法コンプライアンスチェックを実行し、.moduleシステムの整合性とアーキテクチャ一貫性を検証します。
    検証結果に基づいて適切な終了コードを設定します。

    このスクリプトは.moduleシステムの完全性を検証するためのエントリーポイントとして機能し、
    継続的インテグレーション（CI/CD）パイプラインでの品質ゲートとしても使用できます。

    実行フロー:
    1. ConstitutionalComplianceCheckerインスタンスを生成
    2. 包括的検証プロセスを実行
    3. 検証結果レポートをコンソール出力
    4. 検証結果に応じた終了コード設定（成功:0, 失敗:1）

    使用例:
        python constitutional-compliance-checker.py

    CI/CD統合例:
        ./constitutional-compliance-checker.py || exit 1

    Args:
        なし - コマンドライン引数は現在未対応

    Returns:
        None: 関数は値を返しませんが、sys.exit()で終了コードを設定します
               終了コード0: 検証成功（CRITICALエラーなし）
               終了コード1: 検証失敗（CRITICALエラーあり）

    Raises:
        SystemExit: 検証結果に基づいて終了コード0（成功）または1（失敗）で終了

    Side Effects:
        - 標準出力への検証結果レポート出力
        - プロセス終了コードの設定

    Note:
        本関数は複数の責務（実行制御、出力、終了処理）を持つため、
        将来的な拡張性向上のため以下のクラス分離を推奨:
        - ApplicationRunner: アプリケーション実行制御
        - ReportFormatter: レポート出力フォーマット制御
        - ExitHandler: 終了コード制御

    TODO: クラス分離提案 - ConstitutionalComplianceCheckerを複数の責務別クラスに分離し、
          各検証タイプの独立性と再利用性を向上させることを検討
    """
    # LOGIC_200_.moduleシステム全体の検証プロセスを開始
    checker = ConstitutionalComplianceChecker()

    print("🔍 Starting Comprehensive Constitutional Compliance Check...")
    print("Validating .module system integrity and architectural consistency...")
    print()

    # LOGIC_002_処理中のmdファイル1つのみを.processing_stateに上書き記録 - 全ての検証項目を順次実行し結果を収集
    success, results = checker.run_comprehensive_validation()
    checker.print_validation_report(success, results)

    # LOGIC_003_処理済みmd状態をリセットする - 検証結果に基づいた適切な終了コードの設定
    if success:
        print("✅ Constitutional compliance validation completed successfully!")
        sys.exit(0)
    else:
        print("❌ Constitutional compliance validation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
