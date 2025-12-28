"""Main codebase analyzer with comprehensive analysis capabilities."""

import os
import re
import time
from collections import defaultdict
from pathlib import Path

from .advanced_analyzer import ROPE_AVAILABLE, AdvancedCodeAnalyzer, AnalyzerConfig
from .jscpd_analyzer import JSCPD_AVAILABLE, JSCPDAnalyzer, JSCPDConfig
from .models import ClassInfo, CodeIssue, FileMetrics, FunctionInfo


class CodebaseAnalyzer:
    """コードベース分析クラス"""

    def __init__(
        self,
        project_path: str,
        config: AnalyzerConfig | None = None,
        jscpd_config: JSCPDConfig | None = None,
    ):
        self.project_path = Path(project_path).resolve()
        self.config = config or AnalyzerConfig()
        self.jscpd_config = jscpd_config or JSCPDConfig()

        self.issues: list[CodeIssue] = []
        self.file_metrics: list[FileMetrics] = []
        self.timing_info: dict = {}

        self.advanced_analyzer = AdvancedCodeAnalyzer(
            str(self.project_path), self.config
        )

    def analyze_project(self, max_workers: int = 4) -> dict:
        """プロジェクト全体を分析"""
        start_time = time.time()
        print(f"🔍 Analyzing project: {self.project_path}")

        # Step 1: ファイル収集
        step1_start = time.time()
        files = self._collect_files()
        self.timing_info["file_collection"] = {
            "time": time.time() - step1_start,
            "description": "File discovery and filtering",
        }
        print(f"📁 Found {len(files)} files to analyze")

        # Step 2: ファイル分析
        step2_start = time.time()
        all_functions: list[FunctionInfo] = []
        all_classes: list[ClassInfo] = []

        for file_path in files:
            print(f"  Analyzing: {file_path.relative_to(self.project_path)}")
            result = self.advanced_analyzer.analyze_python_file(file_path)
            if result["success"]:
                all_functions.extend(result["functions"])
                all_classes.extend(result["classes"])
            self._analyze_file_basic(file_path)

        self.timing_info["file_analysis"] = {
            "time": time.time() - step2_start,
            "description": "File analysis",
        }

        # Step 3: 重複コード検出
        step3_start = time.time()
        self._detect_duplicates(all_functions, all_classes, files)
        self.timing_info["duplicate_detection"] = {
            "time": time.time() - step3_start,
            "description": "Duplication detection",
        }

        # Step 4: プロジェクト分析
        step4_start = time.time()
        self._analyze_project_issues()
        self.timing_info["project_analysis"] = {
            "time": time.time() - step4_start,
            "description": "Project-wide analysis",
        }

        total_time = time.time() - start_time
        self.timing_info["total"] = {
            "time": total_time,
            "description": "Complete analysis",
            "files_processed": len(files),
            "functions_found": len(all_functions),
            "classes_found": len(all_classes),
        }

        return self._generate_report()

    def _collect_files(self) -> list[Path]:
        """分析対象ファイルを収集"""
        files = []
        for root, dirs, filenames in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in self.config.ignore_dirs]
            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.suffix in self.config.target_extensions:
                    files.append(file_path)
        return files

    def _analyze_file_basic(self, file_path: Path):
        """基本ファイル分析"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            metrics = self._calculate_metrics(file_path, content, lines)
            self.file_metrics.append(metrics)

            self._detect_complex_functions(file_path, content, lines)
            self._scan_security_issues(file_path, content, lines)

        except Exception as e:
            print(f"    ⚠️  Error analyzing {file_path}: {e}")

    def _detect_duplicates(
        self, functions: list[FunctionInfo], classes: list[ClassInfo], files: list[Path]
    ):
        """重複コード検出"""
        self._detect_duplicate_functions(functions)
        self._detect_duplicate_classes(classes)

        # jscpd analysis
        if JSCPD_AVAILABLE:
            jscpd_analyzer = JSCPDAnalyzer(str(self.project_path), self.jscpd_config)
            jscpd_duplications = jscpd_analyzer.run_jscpd_analysis(files)
            self._process_jscpd_results(jscpd_duplications)

    def _detect_duplicate_functions(self, functions: list[FunctionInfo]):
        """重複関数を検出"""
        hash_groups = defaultdict(list)
        for func in functions:
            hash_groups[func.body_hash].append(func)

        for _hash_val, funcs in hash_groups.items():
            if len(funcs) > 1:
                for func in funcs[1:]:
                    self.issues.append(
                        CodeIssue(
                            file_path=func.file,
                            line_number=func.lineno,
                            issue_type="duplication",
                            severity="medium",
                            title=f"重複関数: {func.name}",
                            description=f"この関数は{funcs[0].file}の関数と同一実装です。",
                            suggestion="共通ユーティリティ関数として抽出してください。",
                            effort_estimate="1h",
                        )
                    )

    def _detect_duplicate_classes(self, classes: list[ClassInfo]):
        """重複クラスを検出"""
        hash_groups = defaultdict(list)
        for cls in classes:
            hash_groups[cls.body_hash].append(cls)

        for _hash_val, classes_group in hash_groups.items():
            if len(classes_group) > 1:
                for cls in classes_group[1:]:
                    self.issues.append(
                        CodeIssue(
                            file_path=cls.file,
                            line_number=cls.lineno,
                            issue_type="duplication",
                            severity="high",
                            title=f"重複クラス: {cls.name}",
                            description=f"このクラスは{classes_group[0].file}のクラスと同一実装です。",
                            suggestion="基底クラスとして抽出してください。",
                            effort_estimate="4h",
                        )
                    )

    def _process_jscpd_results(self, jscpd_duplications: list[dict]):
        """jscpd結果を処理"""
        if not jscpd_duplications:
            return

        print(f"📊 Found {len(jscpd_duplications)} duplications via jscpd")

        for dup in jscpd_duplications:
            try:
                first_occurrence = dup.get("first_occurrence", {})
                description = (
                    f"このコードブロックは {first_occurrence.get('file', 'unknown')}:"
                    f"{first_occurrence.get('line', '?')} と {dup['similarity']:.1f}% 類似しています。"
                    f"({dup['lines_count']} 行)"
                )

                self.issues.append(
                    CodeIssue(
                        file_path=dup["file_path"],
                        line_number=dup["line_number"],
                        issue_type="duplication",
                        severity=dup["severity"],
                        title=f"jscpd検出重複コード ({dup['lines_count']}行)",
                        description=description,
                        suggestion="共通の関数として抽出してください。",
                        effort_estimate=dup["effort_estimate"],
                    )
                )
            except Exception as e:
                print(f"Warning: Error processing jscpd result: {e}")

    def _calculate_metrics(
        self, file_path: Path, content: str, lines: list[str]
    ) -> FileMetrics:
        """メトリクス計算"""
        loc = len([line for line in lines if line.strip()])
        language = self._detect_language(file_path)

        functions = (
            len(re.findall(r"def\s+\w+", content)) if file_path.suffix == ".py" else 0
        )
        classes = (
            len(re.findall(r"class\s+\w+", content)) if file_path.suffix == ".py" else 0
        )

        max_complexity = self._estimate_complexity(content)

        return FileMetrics(
            file_path=str(file_path.relative_to(self.project_path)),
            lines_of_code=loc,
            functions=functions,
            classes=classes,
            max_complexity=max_complexity,
            language=language,
        )

    def _detect_language(self, file_path: Path) -> str:
        """言語検出"""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
        }
        return extension_map.get(file_path.suffix, "unknown")

    def _estimate_complexity(self, content: str) -> int:
        """複雑度推定"""
        complexity_keywords = ["if", "else", "for", "while", "try", "catch"]
        complexity = 1
        for keyword in complexity_keywords:
            complexity += len(re.findall(r"\b" + re.escape(keyword) + r"\b", content))
        return min(complexity, 50)

    def _detect_complex_functions(
        self, file_path: Path, content: str, lines: list[str]
    ):
        """複雑な関数を検出"""
        long_threshold = 50

        for match in re.finditer(
            r"def\s+(\w+).*\n((?:[^\n]*\n)*?)\ndef|\Z", content, re.MULTILINE
        ):
            func_content = match.group(0)
            func_lines = func_content.count("\n")

            if func_lines > long_threshold:
                start_line = content[: match.start()].count("\n") + 1
                severity = "high" if func_lines > 100 else "medium"
                effort = "4h" if func_lines > 100 else "2h"

                self.issues.append(
                    CodeIssue(
                        file_path=str(file_path.relative_to(self.project_path)),
                        line_number=start_line,
                        issue_type="complexity",
                        severity=severity,
                        title="関数が長すぎます",
                        description=f"この関数は{func_lines}行あり、推奨される{long_threshold}行を超えています。",
                        suggestion="関数を複数の小さな関数に分割してください。",
                        effort_estimate=effort,
                    )
                )

    def _scan_security_issues(self, file_path: Path, content: str, lines: list[str]):
        """セキュリティスキャン"""
        if file_path.name in ["codebase_analyzer.py"]:
            return

        security_patterns = [
            (r"eval\s*\(", "eval()の使用はセキュリティリスク", "high", "4h"),
            (r"console\.log\s*\(", "本番コードにconsole.log", "low", "15min"),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, description, severity, effort in security_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.issues.append(
                        CodeIssue(
                            file_path=str(file_path.relative_to(self.project_path)),
                            line_number=i,
                            issue_type="security",
                            severity=severity,
                            title="セキュリティ上の懸念",
                            description=description,
                            suggestion="より安全な代替方法を使用してください。",
                            effort_estimate=effort,
                        )
                    )

    def _analyze_project_issues(self):
        """プロジェクト全体の問題分析"""
        total_files = len(self.file_metrics)

        # テストファイル比率
        test_files = len([m for m in self.file_metrics if "test" in m.file_path])
        test_ratio = test_files / total_files if total_files > 0 else 0

        if test_ratio < 0.1:
            self.issues.append(
                CodeIssue(
                    file_path="プロジェクト全体",
                    line_number=0,
                    issue_type="testing",
                    severity="high",
                    title="テストカバレッジ不足",
                    description=f"テストファイル比率: {test_ratio:.1%} (推奨: 20%+)",
                    suggestion="ユニットテスト、統合テストを追加してください。",
                    effort_estimate="2d",
                )
            )

    def _generate_report(self) -> dict:
        """レポート生成"""
        issues_by_severity = {"high": [], "medium": [], "low": []}
        for issue in self.issues:
            issues_by_severity[issue.severity].append(issue)

        issues_by_type = {}
        for issue in self.issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)

        language_stats = {}
        for metrics in self.file_metrics:
            lang = metrics.language
            if lang not in language_stats:
                language_stats[lang] = {
                    "files": 0,
                    "lines": 0,
                    "functions": 0,
                    "classes": 0,
                    "avg_complexity": 0,
                }

            stats = language_stats[lang]
            stats["files"] += 1
            stats["lines"] += metrics.lines_of_code
            stats["functions"] += metrics.functions
            stats["classes"] += metrics.classes

        for lang, stats in language_stats.items():
            lang_files = [m for m in self.file_metrics if m.language == lang]
            if lang_files:
                stats["avg_complexity"] = sum(
                    m.max_complexity for m in lang_files
                ) / len(lang_files)

        return {
            "summary": {
                "total_files": len(self.file_metrics),
                "total_lines": sum(m.lines_of_code for m in self.file_metrics),
                "total_issues": len(self.issues),
                "high_priority_issues": len(issues_by_severity["high"]),
                "medium_priority_issues": len(issues_by_severity["medium"]),
                "low_priority_issues": len(issues_by_severity["low"]),
                "languages_supported": len(language_stats),
                "rope_available": ROPE_AVAILABLE,
                "jscpd_available": JSCPD_AVAILABLE,
            },
            "issues_by_severity": issues_by_severity,
            "issues_by_type": issues_by_type,
            "file_metrics": self.file_metrics,
            "detailed_issues": self.issues,
            "language_statistics": language_stats,
            "timing_info": self.timing_info,
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> list[str]:
        """改善推奨事項"""
        recommendations = []

        high_count = len([i for i in self.issues if i.severity == "high"])
        if high_count > 0:
            recommendations.append(
                f"🔴 優先度の高い問題が{high_count}件あります。まずこれらの対処を推奨します。"
            )

        total_effort = sum(
            1
            if issue.effort_estimate == "15min"
            else 4
            if issue.effort_estimate == "1h"
            else 32
            if issue.effort_estimate == "4h"
            else 40
            if issue.effort_estimate == "1d"
            else 0
            for issue in self.issues
        )

        if total_effort > 0:
            recommendations.append(
                f"⏱️ 全問題の修正には約{total_effort / 8:.1f}日を見積もります。"
            )

        return recommendations
