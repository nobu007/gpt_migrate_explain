#!/usr/bin/env python3
"""
Codebase Analyzer - コードベース全体を分析し、改善提案を生成するスクリプト

使用方法:
python codebase_analyzer.py --path /path/to/project --output improvement_tasks.md

主な機能:
- Python/TypeScript/JavaScriptコードの品質分析 (Advanced AST-based analysis for Python)
- リファクタリング候補の特定
- 複雑度の高い関数/メソッドの検出
- 重複コードの発見 (AST hash-based sophisticated detection)
- テストカバレッジ分析
- セキュリティ問題のスキャン
- パフォーマンス最適化 (Parallel processing support)
"""

import argparse
import ast
import builtins
import contextlib
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Python AST analysis imports - Other languages can be added as needed
try:
    import rope.base.project

    ROPE_AVAILABLE = True
except ImportError:
    ROPE_AVAILABLE = False
    print("Warning: rope library not available. Advanced Python analysis disabled.")

# jscpd for JavaScript/TypeScript duplication detection
JSCPD_AVAILABLE = False
try:
    # Check if jscpd is available
    result = subprocess.run(
        ["jscpd", "--version"], capture_output=True, text=True, timeout=10
    )
    if result.returncode == 0:
        JSCPD_AVAILABLE = True
        print(f"✅ jscpd available: {result.stdout.strip()}")
    else:
        print("Warning: jscpd not found in PATH")
except (subprocess.TimeoutExpired, FileNotFoundError):
    print("Warning: jscpd not available. Install with: npm install -g jscpd")
    print("JavaScript/TypeScript duplication detection will use basic regex analysis")


@dataclass
class CodeIssue:
    """コードの問題点を表現するデータクラス"""

    file_path: str
    line_number: int
    issue_type: str  # 'complexity', 'duplication', 'security', 'testing', 'performance'
    severity: str  # 'high', 'medium', 'low'
    title: str
    description: str
    suggestion: str
    effort_estimate: str  # '15min', '1h', '4h', '1d'


@dataclass
class FunctionInfo:
    """関数の詳細情報"""

    name: str
    file: str
    lineno: int
    args: list[str]
    body_hash: str
    body_lines: int
    complexity: int = 0


@dataclass
class ClassInfo:
    """クラスの詳細情報"""

    name: str
    file: str
    lineno: int
    methods: list[str]
    body_hash: str
    body_lines: int
    complexity: int = 0


@dataclass
class FileMetrics:
    """ファイルごとのメトリクス"""

    file_path: str
    lines_of_code: int
    functions: int
    classes: int
    max_complexity: int
    test_coverage: float | None = None
    language: str = "unknown"


class JSCPDConfig:
    """jscpdの設定を管理するクラス"""

    def __init__(self):
        # JavaScript/TypeScript拡張子
        self.js_ts_extensions = {".js", ".jsx", ".ts", ".tsx"}

        # デフォルトの無視パターン
        self.default_ignore_patterns = [
            "**/node_modules/**",
            "**/dist/**",
            "**/build/**",
            "**/coverage/**",
            "**/.git/**",
            "**/.next/**",
            "**/.nuxt/**",
            "**/vendor/**",
        ]

        # 設定値
        self.threshold = 0  # 0%以上の重複を検出
        self.timeout_seconds = 300  # 5分タイムアウト
        self.min_lines_for_high_severity = 50
        self.min_lines_for_medium_severity = 20
        self.temp_file_prefix = ".jscpd_files"
        self.temp_file_suffix = ".txt"

        # 重複重要度の工数見積もり
        self.effort_estimates = {"high": "4h", "medium": "2h", "low": "1h"}


class JSCPDAnalyzer:
    """jscpdを使用したJavaScript/TypeScript重複コード分析クラス"""

    def __init__(self, project_path: str, config: JSCPDConfig = None):
        self.project_path = Path(project_path).resolve()
        self.config = config or JSCPDConfig()
        self.temp_files: list[Path] = []  # クリーンアップ用の追跡リスト

    def run_jscpd_analysis(self, files: list[Path]) -> list[dict]:
        """jscpdを実行して重複コードを検出"""
        if not JSCPD_AVAILABLE:
            return []

        # JavaScript/TypeScriptファイルのみをフィルタリング
        js_ts_files = [f for f in files if f.suffix in self.config.js_ts_extensions]
        if not js_ts_files:
            return []

        try:
            # jscpdコマンドを構築
            cmd = self._build_jscpd_command(js_ts_files, files)

            # jscpdを実行
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                cwd=str(self.project_path),
            )

            # 一時ファイルをクリーンアップ
            self._cleanup_temp_files()

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                print(f"jscpd failed (exit code {result.returncode}): {error_msg}")
                return []

            # JSON結果を解析
            try:
                jscpd_result = json.loads(result.stdout)
                return self._parse_jscpd_results(jscpd_result, js_ts_files)
            except json.JSONDecodeError as e:
                # デバッグ用にエラー出力の一部を表示
                stderr_preview = result.stderr[:200] if result.stderr else "No stderr"
                print(f"Failed to parse jscpd JSON output: {e}")
                print(f"Stderr preview: {stderr_preview}")
                stdout_preview = result.stdout[:200] if result.stdout else "No stdout"
                print(f"Stdout preview: {stdout_preview}")
                return []

        except subprocess.TimeoutExpired:
            print(
                f"jscpd analysis timed out after {self.config.timeout_seconds} seconds"
            )
            self._cleanup_temp_files()
            return []
        except Exception as e:
            print(f"jscpd analysis failed: {e}")
            self._cleanup_temp_files()
            return []

    def _build_jscpd_command(
        self, js_ts_files: list[Path], all_files: list[Path]
    ) -> list[str]:
        """jscpdコマンドを構築"""
        cmd = [
            "jscpd",
            str(self.project_path),
            "--format",
            "json",
            "--output",
            "-",
            "--threshold",
            str(self.config.threshold),
        ]

        # 無視パターンを追加
        for pattern in self.config.default_ignore_patterns:
            cmd.extend(["--ignore", pattern])

        # 特定のファイルのみを対象にする場合
        if len(js_ts_files) < len(all_files):
            try:
                file_list_file = self._create_temp_file_list(js_ts_files)
                cmd.extend(["--files-list", str(file_list_file)])
            except Exception as e:
                print(f"Warning: Could not create file list for jscpd: {e}")

        return cmd

    def _create_temp_file_list(self, js_ts_files: list[Path]) -> Path:
        """一時ファイルリストを作成"""
        import uuid

        # プロジェクトディレクトリに一時ファイルを作成
        temp_filename = f"{self.config.temp_file_prefix}_{uuid.uuid4().hex[:8]}{self.config.temp_file_suffix}"
        temp_file = self.project_path / temp_filename

        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                for js_file in js_ts_files:
                    try:
                        rel_path = js_file.relative_to(self.project_path)
                        f.write(f"{rel_path}\n")
                    except ValueError:
                        # プロジェクト外のファイルの場合は絶対パスを使用
                        f.write(f"{js_file}\n")

            # クリーンアップリストに追加
            self.temp_files.append(temp_file)
            return temp_file

        except Exception as e:
            # 作成失敗時はクリーンアップを試みる
            with contextlib.suppress(builtins.BaseException):
                temp_file.unlink(missing_ok=True)
            raise e

    def _cleanup_temp_files(self):
        """一時ファイルをクリーンアップ"""
        for temp_file in self.temp_files:
            try:
                temp_file.unlink(missing_ok=True)
            except Exception as e:
                print(f"Warning: Could not delete temp file {temp_file}: {e}")
        self.temp_files.clear()

    def _parse_jscpd_results(
        self, jscpd_result: dict, target_files: list[Path]
    ) -> list[dict]:
        """jscpdの結果を解析してCodeIssue形式に変換"""
        duplications = []

        # jscpdの結果形式を検証
        if not isinstance(jscpd_result, dict):
            print("Warning: jscpd result is not a dictionary")
            return duplications

        # 異なる可能性のある結果形式に対応
        duplications_key = (
            "duplication" if "duplication" in jscpd_result else "duplications"
        )
        if duplications_key not in jscpd_result:
            print("No duplications found in jscpd result")
            return duplications

        duplication_list = jscpd_result[duplications_key]
        if not isinstance(duplication_list, list):
            print(
                f"Warning: Expected list for '{duplications_key}', got {type(duplication_list)}"
            )
            return duplications

        for i, dup in enumerate(duplication_list):
            try:
                if not isinstance(dup, dict):
                    print(f"Warning: Duplication {i} is not a dictionary")
                    continue

                if "fragments" not in dup or not isinstance(dup["fragments"], list):
                    continue

                fragments = dup["fragments"]
                if len(fragments) < 2:
                    continue

                first_fragment = self._validate_fragment(fragments[0], i, 0)
                if not first_fragment:
                    continue

                # 重複フラグメントを処理
                for j, fragment in enumerate(fragments[1:], 1):
                    duplication_info = self._process_fragment(
                        fragment, first_fragment, dup, target_files, i, j
                    )
                    if duplication_info:
                        duplications.append(duplication_info)

            except Exception as e:
                print(f"Error parsing jscpd duplication {i}: {e}")
                continue

        return duplications

    def _validate_fragment(
        self, fragment: dict, dup_index: int, frag_index: int
    ) -> dict | None:
        """フラグメントのデータを検証"""
        if not isinstance(fragment, dict):
            print(
                f"Warning: Fragment {frag_index} in duplication {dup_index} is not a dictionary"
            )
            return None

        file_path = fragment.get("file", "")
        if not file_path:
            print(
                f"Warning: Fragment {frag_index} in duplication {dup_index} has no file path"
            )
            return None

        return fragment

    def _process_fragment(
        self,
        fragment: dict,
        first_fragment: dict,
        dup: dict,
        target_files: list[Path],
        dup_index: int,
        frag_index: int,
    ) -> dict | None:
        """個別の重複フラグメントを処理"""
        try:
            file_path = fragment.get("file", "")
            if not file_path:
                return None

            # パスを正規化
            try:
                abs_file_path = (self.project_path / file_path).resolve()
            except (ValueError, OSError) as e:
                print(f"Warning: Invalid file path '{file_path}': {e}")
                return None

            # ターゲットファイルに含まれているか確認
            if not self._is_target_file(abs_file_path, target_files):
                return None

            # 重複の重要度を判定
            lines_count = fragment.get("size", 0)
            severity = self._determine_severity(lines_count)
            effort = self.config.effort_estimates[severity]

            # 相対パスを計算
            try:
                rel_file_path = abs_file_path.relative_to(self.project_path)
            except ValueError:
                # プロジェクト外のファイルの場合は絶対パスを使用
                rel_file_path = abs_file_path

            return {
                "file_path": str(rel_file_path),
                "line_number": max(1, fragment.get("start", 0) + 1),
                "end_line": max(1, fragment.get("start", 0) + lines_count),
                "lines_count": max(0, lines_count),
                "similarity": max(0.0, min(100.0, dup.get("similarity", 0))),
                "first_occurrence": {
                    "file": first_fragment.get("file", "unknown"),
                    "line": max(1, first_fragment.get("start", 0) + 1),
                },
                "severity": severity,
                "effort_estimate": effort,
                "duplication_id": f"{dup_index}_{frag_index}",
            }

        except Exception as e:
            print(f"Error processing fragment {frag_index}: {e}")
            return None

    def _is_target_file(self, abs_file_path: Path, target_files: list[Path]) -> bool:
        """ファイルがターゲットファイルリストに含まれているか確認"""
        try:
            return any(
                abs_file_path.samefile(target_file.resolve())
                for target_file in target_files
            )
        except (ValueError, OSError):
            return False

    def _determine_severity(self, lines_count: int) -> str:
        """重複の重要度を判定"""
        if lines_count >= self.config.min_lines_for_high_severity:
            return "high"
        if lines_count >= self.config.min_lines_for_medium_severity:
            return "medium"
        return "low"


class AnalyzerConfig:
    """アナライザー全体の設定を管理するクラス"""

    def __init__(self):
        # 分析対象のファイル拡張子
        self.target_extensions = {
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
            ".vue",
            ".py",
            ".java",
            ".cpp",
            ".c",
            ".cs",
            ".php",
            ".rb",
            ".go",
            ".rs",
            ".swift",
            ".kt",
        }

        # 無視するディレクトリ
        self.ignore_dirs = {
            "node_modules",
            ".git",
            "dist",
            "build",
            "coverage",
            ".next",
            ".nuxt",
            "__pycache__",
            ".pytest_cache",
            "vendor",
            ".vscode",
            ".idea",
        }

        # 並列処理のしきい値
        self.parallel_processing_threshold = 10
        self.default_max_workers = 4

        # 複雑度のしきい値
        self.high_complexity_threshold = 20
        self.medium_complexity_threshold = 10

        # 関数の行数しきい値
        self.long_function_threshold = 50
        self.very_long_function_threshold = 100


class AdvancedCodeAnalyzer:
    """高度なコード分析クラス (AST-based for Python + jscpd for JS/TS)"""

    def __init__(
        self,
        project_path: str,
        config: AnalyzerConfig = None,
        jscpd_config: JSCPDConfig = None,
    ):
        self.project_path = Path(project_path).resolve()
        self.config = config or AnalyzerConfig()
        self.jscpd_config = jscpd_config or JSCPDConfig()

        # 分析結果の格納
        self.functions: list[FunctionInfo] = []
        self.classes: list[ClassInfo] = []
        self.current_file = None

        # Python用ropeプロジェクト (ropeが利用可能な場合)
        self.rope_project = None
        if ROPE_AVAILABLE:
            try:
                self.rope_project = rope.base.project.Project(str(self.project_path))
            except Exception as e:
                print(f"Warning: Could not initialize rope project: {e}")

        # jscpdアナライザー
        self.jscpd_analyzer = JSCPDAnalyzer(str(self.project_path), self.jscpd_config)

    def __del__(self):
        """クリーンアップ処理"""
        if hasattr(self, "rope_project") and self.rope_project:
            with contextlib.suppress(builtins.BaseException):
                self.rope_project.close()

    def set_file(self, file_path: str) -> None:
        """現在分析中のファイルパスを設定"""
        self.current_file = file_path

    def analyze_python_file(self, file_path: Path) -> dict:
        """Pythonファイルを高度に分析 (rope + AST)"""
        # Future: Add similar implementations for other languages (JavaScript/TypeScript, etc.)
        if not ROPE_AVAILABLE or file_path.suffix != ".py":
            return self._basic_analysis(file_path)

        try:
            # ropeによる分析
            if self.rope_project:
                return self._rope_analysis(file_path)
            return self._ast_analysis(file_path)
        except Exception as e:
            print(f"Warning: Advanced analysis failed for {file_path}: {e}")
            return self._basic_analysis(file_path)

    def _ast_analysis(self, file_path: Path) -> dict:
        """ASTベースの分析実装"""
        self.set_file(str(file_path))

        try:
            with open(file_path, encoding="utf-8") as f:
                source_code = f.read()

            tree = ast.parse(source_code)
            self._walk_ast(tree)

            return {
                "functions": self.functions.copy(),
                "classes": self.classes.copy(),
                "success": True,
            }
        except Exception as e:
            print(f"AST analysis failed for {file_path}: {e}")
            return {"functions": [], "classes": [], "success": False}

    def _rope_analysis(self, file_path: Path) -> dict:
        """ropeを使用した高度な分析"""
        try:
            # ropeでモジュールを取得
            resource = self.rope_project.get_resource(
                str(file_path.relative_to(self.project_path))
            )
            if not resource:
                return self._ast_analysis(file_path)

            module = self.rope_project.get_pymodule(resource)
            if not module:
                return self._ast_analysis(file_path)

            # AST分析にフォールバック
            return self._ast_analysis(file_path)
        except Exception:
            return self._ast_analysis(file_path)

    def _basic_analysis(self, file_path: Path) -> dict:
        """基本的なテキスト分析 (全言語共通)"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # 各言語に特化したパーサーを実装
            if file_path.suffix in {".ts", ".tsx", ".js", ".jsx"}:
                # jscpd利用可能の場合は基本解析にフォールバック
                # jscpdの重複検出は別途実行
                return self._js_basic_analysis(content, str(file_path))
            if file_path.suffix == ".vue":
                # Note: Vue SFC parser could leverage jscpd for script block duplication detection
                return self._vue_basic_analysis(content, str(file_path))
            if file_path.suffix == ".py":
                return self._ast_analysis(file_path)
            # Future: Implement specialized parsers for other languages
            return self._generic_analysis(content, str(file_path))

        except Exception as e:
            print(f"Basic analysis failed for {file_path}: {e}")
            return {"functions": [], "classes": [], "success": False}

    def _generic_analysis(self, content: str, file_path: str) -> dict:
        """汎用的なコード分析 (言語不明の場合)"""
        functions = []
        classes = []

        # 汎用的な関数・クラスパターンで検出
        func_patterns = [
            r"function\s+(\w+)\s*\(",
            r"def\s+(\w+)\s*\(",
            r"(\w+)\s*\([^)]*\)\s*\{",
            r"public\s+\w+\s+(\w+)\s*\(",
            r"private\s+\w+\s+(\w+)\s*\(",
        ]

        class_patterns = [
            r"class\s+(\w+)",
            r"interface\s+(\w+)",
            r"type\s+(\w+)",
            r"struct\s+(\w+)",
            r"enum\s+(\w+)",
        ]

        for pattern in func_patterns:
            for match in re.finditer(pattern, content):
                func_info = FunctionInfo(
                    name=match.group(1),
                    file=file_path,
                    lineno=content[: match.start()].count("\n") + 1,
                    args=[],
                    body_hash=hashlib.md5(match.group(0).encode()).hexdigest(),
                    body_lines=match.group(0).count("\n") + 1,
                )
                functions.append(func_info)

        for pattern in class_patterns:
            for match in re.finditer(pattern, content):
                class_info = ClassInfo(
                    name=match.group(1),
                    file=file_path,
                    lineno=content[: match.start()].count("\n") + 1,
                    methods=[],
                    body_hash=hashlib.md5(match.group(0).encode()).hexdigest(),
                    body_lines=match.group(0).count("\n") + 1,
                )
                classes.append(class_info)

        return {"functions": functions, "classes": classes, "success": True}

    def _js_basic_analysis(self, content: str, file_path: str) -> dict:
        """JavaScript/TypeScriptの基本的な正規表現ベース分析"""
        # Future: Consider using @babel/parser or TypeScript compiler API for AST parsing
        functions = []
        classes = []

        # 関数の抽出 (正規表現ベースの暫定実装)
        func_patterns = [
            r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)",
            r"const\s+(\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)\s*)?=>",
            r"(\w+)\s*:\s*(?:async\s*)?(?:\([^)]*\)\s*)?=>",
            r"(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{",
        ]

        for pattern in func_patterns:
            for match in re.finditer(pattern, content):
                # Skip comments (simple check)
                line_start = content.rfind("\n", 0, match.start()) + 1
                line = content[line_start : match.end()]
                if line.strip().startswith("//") or line.strip().startswith("*"):
                    continue

                func_info = FunctionInfo(
                    name=match.group(1),
                    file=file_path,
                    lineno=content[: match.start()].count("\n") + 1,
                    args=[],  # Placeholder: Argument extraction could be improved with AST parsing
                    body_hash=hashlib.md5(match.group(0).encode()).hexdigest(),
                    body_lines=match.group(0).count("\n") + 1,
                )
                functions.append(func_info)

        # クラスの抽出 (定義のみを対象とし、re-exportを除外)
        class_patterns = [
            r"(?:class|interface)\s+(\w+)[^{]*\{",  # class/interface definition start
            r"type\s+(\w+)\s*=",  # type alias definition
        ]

        for pattern in class_patterns:
            for match in re.finditer(pattern, content):
                # Skip comments
                line_start = content.rfind("\n", 0, match.start()) + 1
                line = content[line_start : match.end()]
                if line.strip().startswith("//") or line.strip().startswith("*"):
                    continue

                class_info = ClassInfo(
                    name=match.group(1),
                    file=file_path,
                    lineno=content[: match.start()].count("\n") + 1,
                    methods=[],  # Placeholder: Method extraction could be improved with AST parsing
                    body_hash=hashlib.md5(match.group(0).encode()).hexdigest(),
                    body_lines=match.group(0).count("\n") + 1,
                )
                classes.append(class_info)

        return {"functions": functions, "classes": classes, "success": True}

    def _vue_basic_analysis(self, content: str, file_path: str) -> dict:
        """Vue SFCファイルの基本的な分析 - scriptブロックから関数とクラスを抽出"""
        functions = []
        classes = []

        try:
            # Vue SFCから<script>ブロックを抽出
            script_patterns = [
                r"<script[^>]*>(.*?)</script>",
                r"<script[^>]*setup[^>]*>(.*?)</script>",
            ]

            script_content = ""
            for pattern in script_patterns:
                matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    script_content += match.group(1) + "\n"

            if script_content.strip():
                # JavaScript/TypeScriptのパターンで関数とクラスを抽出
                func_patterns = [
                    r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)",
                    r"const\s+(\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)\s*)?=>",
                    r"(\w+)\s*:\s*(?:async\s*)?(?:\([^)]*\)\s*)?=>",
                    r"(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{",
                ]

                # 関数の抽出
                for pattern in func_patterns:
                    for match in re.finditer(pattern, script_content):
                        # コメントをスキップ
                        line_start = script_content.rfind("\n", 0, match.start()) + 1
                        line = script_content[line_start : match.end()]
                        if line.strip().startswith("//") or line.strip().startswith("*"):
                            continue

                        # VueのSFCコンテキストでの行番号を計算
                        script_block_start = content.find(match.group(0))
                        if script_block_start != -1:
                            line_no = content[: script_block_start].count("\n") + 1
                        else:
                            line_no = script_content[: match.start()].count("\n") + 1

                        func_info = FunctionInfo(
                            name=match.group(1),
                            file=file_path,
                            lineno=line_no,
                            args=[],  # 引数抽出の改善は将来実装
                            body_hash="",  # Vue SFC用の簡易ハッシュ
                            body_lines=1,  # 簡易的な行数カウント
                            complexity=1,
                        )
                        functions.append(func_info)

                # クラスの抽出
                class_pattern = r"(?:export\s+)?(?:default\s+)?class\s+(\w+)"
                for match in re.finditer(class_pattern, script_content):
                    line_start = script_content.rfind("\n", 0, match.start()) + 1
                    line = script_content[line_start : match.end()]
                    if line.strip().startswith("//") or line.strip().startswith("*"):
                        continue

                    script_block_start = content.find(match.group(0))
                    if script_block_start != -1:
                        line_no = content[: script_block_start].count("\n") + 1
                    else:
                        line_no = script_content[: match.start()].count("\n") + 1

                    class_info = ClassInfo(
                        name=match.group(1),
                        file=file_path,
                        lineno=line_no,
                        methods=[],  # メソッド抽出の改善は将来実装
                        body_hash="",  # Vue SFC用の簡易ハッシュ
                        body_lines=1,  # 簡易的な行数カウント
                        complexity=1,
                    )
                    classes.append(class_info)

                return {"functions": functions, "classes": classes, "success": True}
            else:
                # <script>ブロックがない場合
                return {"functions": [], "classes": [], "success": True}

        except Exception as e:
            print(f"Warning: Vue SFC analysis failed for {file_path}: {e}")
            return {"functions": [], "classes": [], "success": False}

    def _walk_ast(self, node):
        """ASTをウォークして関数とクラスを抽出"""
        for child in ast.walk(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                self._extract_function(child)
            elif isinstance(child, ast.ClassDef):
                self._extract_class(child)

    def _extract_function(self, node):
        """関数情報を抽出"""
        func_info = FunctionInfo(
            name=node.name,
            file=self.current_file,
            lineno=node.lineno,
            args=[arg.arg for arg in node.args.args],
            body_hash=self._get_node_hash(node),
            body_lines=node.end_lineno - node.lineno + 1
            if hasattr(node, "end_lineno")
            else 0,
            complexity=self._calculate_ast_complexity(node),
        )
        self.functions.append(func_info)

    def _extract_class(self, node):
        """クラス情報を抽出"""
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                methods.append(item.name)

        class_info = ClassInfo(
            name=node.name,
            file=self.current_file,
            lineno=node.lineno,
            methods=methods,
            body_hash=self._get_node_hash(node),
            body_lines=node.end_lineno - node.lineno + 1
            if hasattr(node, "end_lineno")
            else 0,
            complexity=self._calculate_ast_complexity(node),
        )
        self.classes.append(class_info)

    def _get_node_hash(self, node) -> str:
        """ASTノードのハッシュを生成"""
        node_str = ast.dump(node, include_attributes=False)
        return hashlib.md5(node_str.encode()).hexdigest()

    def _calculate_ast_complexity(self, node) -> int:
        """ASTノードの循環的複雑度を計算"""
        complexity = 1  # 基本複雑度

        for child in ast.walk(node):
            if isinstance(
                child, ast.If | ast.While | ast.For | ast.AsyncFor | ast.ExceptHandler
            ):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.With, ast.AsyncWith):
                complexity += 1

        return complexity


class CodebaseAnalyzer:
    """コードベース分析クラス"""

    def __init__(
        self,
        project_path: str,
        config: AnalyzerConfig = None,
        jscpd_config: JSCPDConfig = None,
    ):
        self.project_path = Path(project_path).resolve()
        self.config = config or AnalyzerConfig()
        self.jscpd_config = jscpd_config or JSCPDConfig()

        # 分析結果の格納
        self.issues: list[CodeIssue] = []
        self.file_metrics: list[FileMetrics] = []
        self.timing_info: dict = {}

        # 高度なアナライザーを初期化
        self.advanced_analyzer = AdvancedCodeAnalyzer(
            str(self.project_path), self.config, self.jscpd_config
        )

    def analyze_project(self, max_workers: int = 4) -> dict:
        """プロジェクト全体を分析 (パフォーマンス最適化版)"""
        start_time = time.time()

        print(f"🔍 Analyzing project: {self.project_path}")
        if ROPE_AVAILABLE:
            print("🐍 Using advanced Python AST analysis (rope)")

        # Step 1: ファイル収集
        step1_start = time.time()
        files = self._collect_files()
        self.timing_info["file_collection"] = {
            "time": time.time() - step1_start,
            "description": "File discovery and filtering",
        }
        print(f"📁 Found {len(files)} files to analyze")

        # Step 2: 高度なファイル分析 (並列処理)
        step2_start = time.time()
        all_functions: list[FunctionInfo] = []
        all_classes: list[ClassInfo] = []

        if len(files) > self.config.parallel_processing_threshold:
            print(f"🚀 Using parallel processing with {max_workers} workers")
            all_functions, all_classes = self._analyze_files_parallel(
                files, max_workers
            )
        else:
            print("🔧 Using sequential processing (small dataset)")
            for file_path in files:
                print(f"  Analyzing: {file_path.relative_to(self.project_path)}")
                result = self.advanced_analyzer.analyze_python_file(file_path)
                if result["success"]:
                    all_functions.extend(result["functions"])
                    all_classes.extend(result["classes"])
                self._analyze_file_basic(file_path)

        self.timing_info["file_analysis"] = {
            "time": time.time() - step2_start,
            "workers": max_workers
            if len(files) > self.config.parallel_processing_threshold
            else 1,
            "description": "Advanced AST and basic analysis",
        }

        # Step 3: 高度な重複コード検出
        step3_start = time.time()
        self._detect_advanced_duplicates(all_functions, all_classes, files)
        self.timing_info["duplicate_detection"] = {
            "time": time.time() - step3_start,
            "description": "AST hash-based (Python) + jscpd (JS/TS) duplication detection",
        }

        # Step 4: プロジェクト全体の問題分析
        step4_start = time.time()
        self._analyze_project_issues()
        self.timing_info["project_analysis"] = {
            "time": time.time() - step4_start,
            "description": "Project-wide issue analysis",
        }

        # 結果を集計
        total_time = time.time() - start_time
        self.timing_info["total"] = {
            "time": total_time,
            "description": "Complete analysis pipeline",
            "files_processed": len(files),
            "functions_found": len(all_functions),
            "classes_found": len(all_classes),
        }

        return self._generate_report()

    def _analyze_files_parallel(
        self, files: list[Path], max_workers: int
    ) -> tuple[list[FunctionInfo], list[ClassInfo]]:
        """ファイルを並列処理で分析"""
        all_functions = []
        all_classes = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 分析タスクを投入
            future_to_file = {
                executor.submit(
                    self._analyze_single_file_advanced, file_path
                ): file_path
                for file_path in files
            }

            # 結果を収集
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    if result["success"]:
                        all_functions.extend(result["functions"])
                        all_classes.extend(result["classes"])

                    # ALWAYS run basic analysis to populate file_metrics and detect other issues
                    self._analyze_file_basic(file_path)

                    print(f"  ✓ Analyzed: {file_path.relative_to(self.project_path)}")
                except Exception as e:
                    print(
                        f"    ⚠️  Error analyzing {file_path.relative_to(self.project_path)}: {e}"
                    )
                    # フォールバックして基本分析を実行
                    self._analyze_file_basic(file_path)

        return all_functions, all_classes

    def _analyze_single_file_advanced(self, file_path: Path) -> dict:
        """単一ファイルの高度な分析 (並列処理用)"""
        try:
            # 新しいAnalyzerインスタンスを作成（スレッドセーフのため）
            analyzer = AdvancedCodeAnalyzer(str(self.project_path))
            return analyzer.analyze_python_file(file_path)
        except Exception as e:
            print(f"Error in advanced analysis for {file_path}: {e}")
            return {"functions": [], "classes": [], "success": False}

    def _collect_files(self) -> list[Path]:
        """分析対象のファイルを収集"""
        files = []
        for root, dirs, filenames in os.walk(self.project_path):
            # 無視ディレクトリを除外
            dirs[:] = [d for d in dirs if d not in self.config.ignore_dirs]

            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.suffix in self.config.target_extensions:
                    files.append(file_path)

        return files

    def _analyze_file_basic(self, file_path: Path):
        """個別ファイルの基本分析 (フォールバック用)"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            metrics = self._calculate_metrics(file_path, content, lines)
            self.file_metrics.append(metrics)

            # 複雑度の高い関数を検出
            self._detect_complex_functions(file_path, content, lines)

            # セキュリティ問題をスキャン
            self._scan_security_issues(file_path, content, lines)

            # パフォーマンス問題を検出
            self._detect_performance_issues(file_path, content, lines)

            # テストカバレッジを分析
            if "test" in file_path.name or "spec" in file_path.name:
                self._analyze_test_coverage(file_path, content)

        except Exception as e:
            print(f"    ⚠️  Error analyzing {file_path}: {e}")

    def _detect_advanced_duplicates(
        self,
        all_functions: list[FunctionInfo],
        all_classes: list[ClassInfo],
        files: list[Path],
    ):
        """高度な重複コード検出 (ASTハッシュベース + jscpd)"""
        # Pythonの重複検出 (ASTハッシュベース)
        self._detect_duplicate_functions(all_functions)
        self._detect_duplicate_classes(all_classes)
        self._detect_similar_function_names(all_functions)

        # JavaScript/TypeScriptの重複検出 (jscpd)
        if JSCPD_AVAILABLE:
            print("🔍 Running jscpd for JavaScript/TypeScript duplication detection...")
            jscpd_duplications = (
                self.advanced_analyzer.jscpd_analyzer.run_jscpd_analysis(files)
            )
            self._process_jscpd_results(jscpd_duplications)
        else:
            # jscpdが利用できない場合は基本テキストベースの重複検出にフォールバック
            print(
                "⚠️ jscpd not available, using basic text-based duplication detection for JS/TS"
            )
            self._detect_js_ts_basic_duplicates(files)

    def _detect_duplicate_functions(self, functions: list[FunctionInfo]):
        """重複関数をASTハッシュで検出"""
        hash_groups = defaultdict(list)

        # ASTハッシュで関数をグループ化
        for func in functions:
            hash_groups[func.body_hash].append(func)

        # 重複を報告
        for _hash_val, funcs in hash_groups.items():
            if len(funcs) > 1:
                for func in funcs[1:]:  # 2番目以降を報告
                    self.issues.append(
                        CodeIssue(
                            file_path=func.file,
                            line_number=func.lineno,
                            issue_type="duplication",
                            severity="medium",
                            title=f"重複関数: {func.name}",
                            description=f"この関数は{funcs[0].file}の関数と同一実装です。",
                            suggestion="共通ユーティリティ関数として抽出することを検討してください。",
                            effort_estimate="1h",
                        )
                    )

    def _detect_duplicate_classes(self, classes: list[ClassInfo]):
        """重複クラスをASTハッシュで検出"""
        hash_groups = defaultdict(list)

        # ASTハッシュでクラスをグループ化
        for cls in classes:
            hash_groups[cls.body_hash].append(cls)

        # 重複を報告
        for _hash_val, classes_group in hash_groups.items():
            if len(classes_group) > 1:
                for cls in classes_group[1:]:  # 2番目以降を報告
                    self.issues.append(
                        CodeIssue(
                            file_path=cls.file,
                            line_number=cls.lineno,
                            issue_type="duplication",
                            severity="high",
                            title=f"重複クラス: {cls.name}",
                            description=f"このクラスは{classes_group[0].file}のクラスと同一実装です。",
                            suggestion="基底クラスとして抽出するか、ユーティリティクラスを検討してください。",
                            effort_estimate="4h",
                        )
                    )

    def _detect_similar_function_names(self, functions: list[FunctionInfo]):
        """類似名前の関数を検出"""
        name_groups = defaultdict(list)

        # 関数名でグループ化
        for func in functions:
            name_groups[func.name].append(func)

        # 同名で異なる実装の関数を報告
        for _name, funcs in name_groups.items():
            if len(funcs) > 1:
                # 異なる実装かチェック
                hashes = {func.body_hash for func in funcs}
                if len(hashes) > 1:
                    for func in funcs[1:]:  # 2番目以降を報告
                        self.issues.append(
                            CodeIssue(
                                file_path=func.file,
                                line_number=func.lineno,
                                issue_type="duplication",
                                severity="medium",
                                title=f"類似関数名: {func.name}",
                                description="同名関数が複数存在し、実装が異なります。",
                                suggestion="関数名をより具体的にするか、実装を統一してください。",
                                effort_estimate="30min",
                            )
                        )

    def _process_jscpd_results(self, jscpd_duplications: list[dict]):
        """jscpdの重複検出結果を処理してIssueに変換"""
        if not jscpd_duplications:
            print("📊 No duplications found by jscpd")
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

                suggestion = (
                    "共通の関数またはユーティリティとして抽出することを検討してください。"
                    "または、重複を避けるためにコードの設計を見直してください。"
                )

                self.issues.append(
                    CodeIssue(
                        file_path=dup["file_path"],
                        line_number=dup["line_number"],
                        issue_type="duplication",
                        severity=dup["severity"],
                        title=f'jscpd検出重複コード ({dup["lines_count"]}行)',
                        description=description,
                        suggestion=suggestion,
                        effort_estimate=dup["effort_estimate"],
                    )
                )
            except KeyError as e:
                print(f"Warning: Missing key in jscpd result: {e}")
                continue

    def _detect_js_ts_basic_duplicates(self, files: list[Path]):
        """jscpdが利用できない場合の基本的なJS/TS重複検出（フォールバック）"""
        [f for f in files if f.suffix in {".js", ".jsx", ".ts", ".tsx"}]

        # 元の重複検出メソッドを呼び出し（フォールバック）
        print("⚠️ Using basic text-based duplication detection for JS/TS files")
        # この実装は既存の_detect_duplicatesメソッドを流用できる
        self._detect_duplicates()

    def _calculate_metrics(
        self, file_path: Path, content: str, lines: list[str]
    ) -> FileMetrics:
        """ファイルの基本メトリクスを計算"""
        loc = len([line for line in lines if line.strip()])

        # 言語を検出
        language = self._detect_language(file_path)

        # 関数とクラスの数をカウント（簡易的な実装）
        if file_path.suffix in {".ts", ".tsx", ".js", ".jsx"}:
            # Current: Regex-based counting - could be improved with TypeScript/JavaScript AST parser
            functions = len(
                re.findall(
                    r"(?:function\s+\w+|const\s+\w+\s*=\s*(?:\([^)]*\)\s*)?=>|\w+\s*:\s*\([^)]*\)\s*=>)",
                    content,
                )
            )
            classes = len(
                re.findall(r"(?:class\s+\w+|interface\s+\w+|type\s+\w+)", content)
            )
        elif file_path.suffix == ".py":
            # Current: Regex-based counting - could use AST parser results for improved accuracy
            functions = len(re.findall(r"def\s+\w+", content))
            classes = len(re.findall(r"class\s+\w+", content))
        elif file_path.suffix == ".vue":
            # Future: Implement Vue SFC parser for better analysis
            functions = 0
            classes = 0
        else:
            # Future: Add support for other languages
            functions = 0
            classes = 0

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
        """ファイルの言語を検出"""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".vue": "vue",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".cs": "csharp",
            ".php": "php",
            ".rb": "ruby",
            ".go": "go",
            ".rs": "rust",
            ".swift": "swift",
            ".kt": "kotlin",
            # More languages can be added as needed
        }

        return extension_map.get(file_path.suffix, "unknown")

    def _estimate_complexity(self, content: str) -> int:
        """コードの複雑度を簡易的に推定"""
        # 制御構造の数をカウント
        complexity_keywords = [
            "if",
            "else",
            "for",
            "while",
            "do",
            "switch",
            "case",
            "try",
            "catch",
            "&&",
            "||",
            "?",
            "??",
            "break",
            "continue",
            "return",
        ]

        complexity = 1  # 基本複雑度
        for keyword in complexity_keywords:
            complexity += len(re.findall(r"\b" + re.escape(keyword) + r"\b", content))

        return min(complexity, 50)  # 上限を設定

    def _detect_complex_functions(
        self, file_path: Path, content: str, lines: list[str]
    ):
        """複雑度の高い関数を検出"""
        # 長い関数を検出（50行超過）
        functions = re.finditer(
            r"(?:function\s+\w+|const\s+\w+\s*=\s*(?:\([^)]*\)\s*)?=>|\w+\s*:\s*\([^)]*\)\s*=>|def\s+\w+)[^{]*\{((?:[^{}]*\{[^{}]*\})*[^{}]*)",
            content,
            re.MULTILINE,
        )

        for match in functions:
            func_content = match.group(0)
            func_lines = func_content.count("\n")

            if func_lines > self.config.long_function_threshold:
                start_line = content[: match.start()].count("\n") + 1
                severity = (
                    "high"
                    if func_lines > self.config.very_long_function_threshold
                    else "medium"
                )
                effort = (
                    "4h"
                    if func_lines > self.config.very_long_function_threshold
                    else "2h"
                )

                self.issues.append(
                    CodeIssue(
                        file_path=str(file_path.relative_to(self.project_path)),
                        line_number=start_line,
                        issue_type="complexity",
                        severity=severity,
                        title="関数が長すぎます",
                        description=f"この関数は{func_lines}行あり、推奨される{self.config.long_function_threshold}行を大幅に超えています。",
                        suggestion="関数を複数の小さな関数に分割することを検討してください。",
                        effort_estimate=effort,
                    )
                )

    def _scan_security_issues(self, file_path: Path, content: str, lines: list[str]):
        """セキュリティ問題をスキャン"""
        # Skip security scan for analyzer scripts to avoid self-detection of patterns
        if file_path.name in ["codebase_analyzer.py", "code_review.py"]:
            return

        # テストファイルかどうか判定
        is_test_file = (
            "test" in str(file_path).lower() or "spec" in str(file_path).lower()
        )

        security_patterns = [
            (r"eval\s*\(", "eval()の使用はセキュリティリスクがあります", "high", "4h"),
            (
                r"innerHTML\s*=",
                "innerHTMLの直接代入はXSSリスクがあります",
                "high",
                "2h",
            ),
            (
                r"document\.write\s*\(",
                "document.write()はセキュリティリスクがあります",
                "high",
                "2h",
            ),
            (
                r"console\.log\s*\(",
                "本番コードにconsole.logが含まれています",
                "low",
                "15min",
            ),
            # Ignore mock/test values
            (
                r'password\s*[:=]\s*["\'](?!(?:mock|test|placeholder|dummy|env|process))[^"\']+["\']',
                "ハードコードされたパスワードがあります",
                "high",
                "1h",
            ),
            (
                r'api[_-]?key\s*[:=]\s*["\'](?!(?:mock|test|placeholder|dummy|env|process))[^"\']+["\']',
                "ハードコードされたAPIキーがあります",
                "high",
                "1h",
            ),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, description, severity, effort in security_patterns:
                # テストファイルでのハードコードパスワード/キーは無視
                if is_test_file and ("password" in pattern or "api" in pattern):
                    continue

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

    def _detect_performance_issues(
        self, file_path: Path, content: str, lines: list[str]
    ):
        """パフォーマンス問題を検出"""
        performance_patterns = [
            (
                r"for\s*\([^)]*\bin\b[^)]+\)",
                "for...inループはパフォーマンスが低い場合があります",
                "medium",
                "30min",
            ),
            (
                r"Array\.prototype\.forEach\.call",
                "Array.forEach.callは最適ではありません",
                "low",
                "15min",
            ),
            (
                r'setTimeout\s*\(\s*["\']',
                "setTimeoutに文字列を使用しないでください",
                "medium",
                "30min",
            ),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, description, severity, effort in performance_patterns:
                if re.search(pattern, line):
                    self.issues.append(
                        CodeIssue(
                            file_path=str(file_path.relative_to(self.project_path)),
                            line_number=i,
                            issue_type="performance",
                            severity=severity,
                            title="パフォーマンスの改善可能性",
                            description=description,
                            suggestion="より効率的な実装方法を検討してください。",
                            effort_estimate=effort,
                        )
                    )

    def _detect_duplicates(self):
        """重複コードを検出（簡易的な実装）"""
        code_blocks = {}

        BLOCK_SIZE = 10
        MIN_CHARS = 100

        for metrics in self.file_metrics:
            file_path = self.project_path / metrics.file_path
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                lines = content.split("\n")
                if len(lines) < BLOCK_SIZE:
                    continue

                for i in range(len(lines) - (BLOCK_SIZE - 1)):
                    window_lines = lines[i : i + BLOCK_SIZE]

                    # Skip if any line is an import/export/package statement (reduce noise)
                    if any(
                        l.strip().startswith(
                            (
                                "import ",
                                "export ",
                                "from ",
                                "package ",
                                "using ",
                                "include ",
                            )
                        )
                        for l in window_lines
                    ):
                        continue

                    # Skip if mostly comments
                    if (
                        sum(
                            1
                            for l in window_lines
                            if l.strip().startswith(("/", "*", "#"))
                        )
                        > BLOCK_SIZE / 2
                    ):
                        continue

                    block = "\n".join(window_lines).strip()

                    if len(block) > MIN_CHARS:
                        if block in code_blocks:
                            code_blocks[block].append((metrics.file_path, i + 1))
                        else:
                            code_blocks[block] = [(metrics.file_path, i + 1)]
            except (SyntaxError, ValueError, UnicodeDecodeError):
                continue

        # 重複ブロックを報告
        for block, locations in code_blocks.items():
            if len(locations) > 1:
                for file_path, line_num in locations[1:]:  # 2番目以降の場所を報告
                    self.issues.append(
                        CodeIssue(
                            file_path=file_path,
                            line_number=line_num,
                            issue_type="duplication",
                            severity="medium",
                            title="重複コードの可能性",
                            description=f"このコードブロック（{BLOCK_SIZE}行）は他の場所でも見つかりました。",
                            suggestion="共通関数として抽出することを検討してください。",
                            effort_estimate="1h",
                        )
                    )

    def _analyze_project_issues(self):
        """プロジェクト全体の問題を分析"""
        total_files = len(self.file_metrics)
        sum(m.lines_of_code for m in self.file_metrics)

        # テストファイルの比率
        test_files = len(
            [
                m
                for m in self.file_metrics
                if "test" in m.file_path or "spec" in m.file_path
            ]
        )
        test_ratio = test_files / total_files if total_files > 0 else 0

        if test_ratio < 0.1:  # 10%未満
            self.issues.append(
                CodeIssue(
                    file_path="プロジェクト全体",
                    line_number=0,
                    issue_type="testing",
                    severity="high",
                    title="テストカバレッジが不足しています",
                    description=f"テストファイルの比率: {test_ratio:.1%} (推奨: 20%+)",
                    suggestion="ユニットテスト、統合テストを追加してください。",
                    effort_estimate="2d",
                )
            )

        # 平均複雑度
        avg_complexity = (
            sum(m.max_complexity for m in self.file_metrics) / total_files
            if total_files > 0
            else 0
        )
        if avg_complexity > self.config.high_complexity_threshold:
            self.issues.append(
                CodeIssue(
                    file_path="プロジェクト全体",
                    line_number=0,
                    issue_type="complexity",
                    severity="medium",
                    title="平均複雑度が高いです",
                    description=f"平均複雑度: {avg_complexity:.1f} (推奨: {self.config.medium_complexity_threshold}以下)",
                    suggestion="コードの単純化、関数分割などを検討してください。",
                    effort_estimate="1d",
                )
            )

    def _analyze_test_coverage(self, file_path: Path, content: str):
        """テストファイルのカバレッジを分析"""
        # 簡易的なテストカバレッジ分析
        test_patterns = [
            r"describe\s*\(",
            r"it\s*\(",
            r"test\s*\(",
            r"expect\s*\(",
        ]

        coverage_score = 0
        for pattern in test_patterns:
            coverage_score += len(re.findall(pattern, content))

        # 対応するソースファイルを探す
        source_file = None
        for metrics in self.file_metrics:
            if metrics.file_path.replace("test/", "").replace("spec/", "").replace(
                ".test.", "."
            ).replace(".spec.", ".") == str(
                file_path.relative_to(self.project_path)
            ).replace("test/", "").replace("spec/", "").replace(".test.", ".").replace(
                ".spec.", "."
            ):
                source_file = metrics
                break

        if source_file and coverage_score < 5:  # テストが少ない場合
            self.issues.append(
                CodeIssue(
                    file_path=str(file_path.relative_to(self.project_path)),
                    line_number=0,
                    issue_type="testing",
                    severity="medium",
                    title="テストが不十分です",
                    description=f"このテストファイルのテストケースが少ないです (スコア: {coverage_score})",
                    suggestion="更多のテストケースを追加してください。",
                    effort_estimate="1h",
                )
            )

    def _generate_report(self) -> dict:
        """分析レポートを生成 (パフォーマンス情報付き)"""
        # 重要度でグループ化
        issues_by_severity = {"high": [], "medium": [], "low": []}
        for issue in self.issues:
            issues_by_severity[issue.severity].append(issue)

        # タイプでグループ化
        issues_by_type = {}
        for issue in self.issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)

        # 言語別統計
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

        # 平均複雑度を計算
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
            "performance_summary": self._generate_performance_summary(),
        }

    def _generate_performance_summary(self) -> dict:
        """パフォーマンスサマリーを生成"""
        if not self.timing_info:
            return {}

        total_time = self.timing_info.get("total", {}).get("time", 0)
        total_files = self.timing_info.get("total", {}).get("files_processed", 0)

        return {
            "total_analysis_time": f"{total_time:.2f}s",
            "files_per_second": f"{total_files / total_time:.1f}"
            if total_time > 0
            else "N/A",
            "timing_breakdown": {
                step: info["time"]
                for step, info in self.timing_info.items()
                if step != "total"
            },
            "bottleneck": max(
                [
                    (step, info["time"])
                    for step, info in self.timing_info.items()
                    if step != "total"
                ],
                key=lambda x: x[1],
                default=("N/A", 0),
            )[0],
        }

    def _generate_recommendations(self) -> list[str]:
        """改善推奨事項を生成"""
        recommendations = []

        high_count = len([i for i in self.issues if i.severity == "high"])
        if high_count > 0:
            recommendations.append(
                f"🔴 優先度の高い問題が{high_count}件あります。まずこれらの対処を推奨します。"
            )

        # 最も多い問題タイプ
        type_counts = {}
        for issue in self.issues:
            type_counts[issue.issue_type] = type_counts.get(issue.issue_type, 0) + 1

        if type_counts:
            most_common = max(type_counts.items(), key=lambda x: x[1])
            recommendations.append(
                f"📊 {most_common[0]}関連の問題が{most_common[1]}件と最も多いです。"
            )

        # 工数見積もり
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
                f"⏱️ 全問題の修正には約{total_effort/8:.1f}日を見積もります。"
            )

        return recommendations


def generate_markdown_report(analysis_result: dict, output_path: str):
    """Markdown形式のレポートを生成 (機能強化版)"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(
            f"""# コードベース改善提案レポート

生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 サマリー

- **分析ファイル数**: {analysis_result['summary']['total_files']} ファイル
- **総コード行数**: {analysis_result['summary']['total_lines']:,} 行
- **発見された問題**: {analysis_result['summary']['total_issues']} 件
  - 🔴 高優先度: {analysis_result['summary']['high_priority_issues']} 件
  - 🟡 中優先度: {analysis_result['summary']['medium_priority_issues']} 件
  - 🟢 低優先度: {analysis_result['summary']['low_priority_issues']} 件
- **サポート言語**: {analysis_result['summary']['languages_supported']} 種類
- **高度なPython分析**: {'有効' if analysis_result['summary']['rope_available'] else '無効'}
- **jscpd (JS/TS重複検出)**: {'有効' if analysis_result['summary']['jscpd_available'] else '無効'}

"""
        )

        # 推奨事項
        if analysis_result["recommendations"]:
            f.write("## 💡 推奨事項\n\n")
            for rec in analysis_result["recommendations"]:
                f.write(f"- {rec}\n")
            f.write("\n")

        # 優先度別タスクリスト
        f.write("## 🎯 優先度別タスクリスト\n\n")

        for severity in ["high", "medium", "low"]:
            issues = analysis_result["issues_by_severity"][severity]
            if not issues:
                continue

            severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            severity_text = {
                "high": "高優先度",
                "medium": "中優先度",
                "low": "低優先度",
            }

            f.write(
                f"### {severity_emoji[severity]} {severity_text[severity]} ({len(issues)}件)\n\n"
            )

            for i, issue in enumerate(issues, 1):
                f.write(f"#### {i}. {issue.title}\n\n")
                f.write(f"**ファイル**: `{issue.file_path}:{issue.line_number}`\n\n")
                f.write(f"**説明**: {issue.description}\n\n")
                f.write(f"**提案**: {issue.suggestion}\n\n")
                f.write(f"**見積もり**: {issue.effort_estimate}\n\n")
                f.write("---\n\n")

        # 問題タイプ別分析
        f.write("## 📈 問題タイプ別分析\n\n")

        for issue_type, issues in analysis_result["issues_by_type"].items():
            if not issues:
                continue

            type_names = {
                "complexity": "複雑度",
                "duplication": "重複コード",
                "security": "セキュリティ",
                "performance": "パフォーマンス",
                "testing": "テスト",
            }

            type_name = type_names.get(issue_type, issue_type)
            f.write(f"### {type_name} ({len(issues)}件)\n\n")

            # ファイル別集計
            file_counts = {}
            for issue in issues:
                if issue.file_path not in file_counts:
                    file_counts[issue.file_path] = 0
                file_counts[issue.file_path] += 1

            f.write("**問題の多いファイル**:\n")
            for file_path, count in sorted(
                file_counts.items(), key=lambda x: x[1], reverse=True
            )[:5]:
                f.write(f"- `{file_path}`: {count}件\n")
            f.write("\n")

        # 言語別統計
        if "language_statistics" in analysis_result:
            f.write("## 🌐 言語別統計\n\n")
            f.write(
                "| 言語 | ファイル数 | コード行数 | 関数数 | クラス数 | 平均複雑度 |\n"
            )
            f.write("|------|----------|----------|--------|--------|------------|\n")

            for lang, stats in sorted(
                analysis_result["language_statistics"].items(),
                key=lambda x: x[1]["lines"],
                reverse=True,
            ):
                f.write(
                    f"| {lang} | {stats['files']} | {stats['lines']:,} | {stats['functions']} | {stats['classes']} | {stats['avg_complexity']:.1f} |\n"
                )

        # パフォーマンスサマリー
        if (
            "performance_summary" in analysis_result
            and analysis_result["performance_summary"]
        ):
            perf = analysis_result["performance_summary"]
            f.write("## ⚡ パフォーマンスサマリー\n\n")
            f.write(f"- **総分析時間**: {perf['total_analysis_time']}\n")
            f.write(f"- **処理速度**: {perf['files_per_second']} ファイル/秒\n")
            f.write(f"- **ボトルネック**: {perf['bottleneck']}\n\n")

            f.write("### 処理時間の内訳\n\n")
            f.write("| ステップ | 時間 (秒) | 説明 |\n")
            f.write("|--------|-----------|------|\n")

            for step, time_taken in perf["timing_breakdown"].items():
                # タイミング情報から説明を取得
                desc = (
                    analysis_result.get("timing_info", {})
                    .get(step, {})
                    .get("description", step)
                )
                f.write(f"| {step} | {time_taken:.3f} | {desc} |\n")
            f.write("\n")

        # ファイルメトリクス
        f.write("## 📁 ファイル別メトリクス\n\n")
        f.write("| ファイル | 言語 | コード行数 | 関数数 | クラス数 | 最大複雑度 |\n")
        f.write("|--------|------|----------|--------|--------|------------|\n")

        # 複雑度順にソート
        sorted_metrics = sorted(
            analysis_result["file_metrics"],
            key=lambda x: x.max_complexity,
            reverse=True,
        )

        for metrics in sorted_metrics[:20]:  # 上位20件を表示
            f.write(
                f"| `{metrics.file_path}` | {metrics.language} | {metrics.lines_of_code:,} | {metrics.functions} | {metrics.classes} | {metrics.max_complexity} |\n"
            )

        if len(sorted_metrics) > 20:
            f.write(f"| ... など {len(sorted_metrics)-20}ファイル | | | | | |\n")

    print(f"📝 レポートを生成しました: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="コードベースを分析して改善提案を生成 (機能強化版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  python codebase_analyzer.py --path /path/to/project
  python codebase_analyzer.py --path . --workers 8 --verbose --format json
  python codebase_analyzer.py --path . --output custom_report.md

注意事項:
  - jscpdを使用するには: npm install -g jscpd
  - ropeを使用するには: pip install rope
        """,
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
        help="並列処理のワーカー数 (デフォルト: CPUコア数または4)",
    )
    parser.add_argument("--verbose", action="store_true", help="詳細な分析情報を表示")
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="jscpdのタイムアウト秒数 (デフォルト: 300)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0,
        help="重複検出のしきい値パーセンテージ (デフォルト: 0)",
    )

    args = parser.parse_args()

    # プロジェクトの存在確認とパスの検証
    try:
        project_path = Path(args.path).resolve()
        if not project_path.exists():
            print(f"❌ エラー: プロジェクトパスが存在しません: {project_path}")
            sys.exit(1)
        if not project_path.is_dir():
            print(
                f"❌ エラー: 指定されたパスはディレクトリではありません: {project_path}"
            )
            sys.exit(1)
    except Exception as e:
        print(f"❌ エラー: パスの処理に失敗しました: {e}")
        sys.exit(1)

    if args.verbose:
        print("🔧 設定:")
        print(f"  - プロジェクトパス: {args.path}")
        print(f"  - 出力ファイル: {args.output}")
        print(f"  - 出力形式: {args.format}")
        print(f"  - 並列ワーカー数: {args.workers}")
        print(
            f"  - ropeライブラリ (Python): {'利用可能' if ROPE_AVAILABLE else '利用不可'}"
        )
        print(f"  - jscpd (JS/TS): {'利用可能' if JSCPD_AVAILABLE else '利用不可'}")
        if not JSCPD_AVAILABLE:
            print("    💡 インストール方法: npm install -g jscpd")
        print()

    # 設定クラスを初期化
    config = AnalyzerConfig()
    jscpd_config = JSCPDConfig()

    # コマンドライン引数で設定を上書き
    if args.timeout is not None:
        jscpd_config.timeout_seconds = args.timeout
    if args.threshold is not None:
        jscpd_config.threshold = args.threshold

    # ワーカー数を決定
    import multiprocessing

    default_workers = min(multiprocessing.cpu_count(), 8)
    max_workers = args.workers or config.default_max_workers or default_workers

    if args.verbose:
        print(f"  - 並列ワーカー数: {max_workers}")
        print(f"  - jscpdタイムアウト: {jscpd_config.timeout_seconds}秒")
        print(f"  - 重複検出しきい値: {jscpd_config.threshold}%")
        print()

    # 分析実行
    start_time = time.time()
    analyzer = CodebaseAnalyzer(str(project_path), config, jscpd_config)
    result = analyzer.analyze_project(max_workers=max_workers)
    analysis_time = time.time() - start_time

    # 結果を出力
    if args.format == "json":
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    else:
        generate_markdown_report(result, args.output)

    # 完了メッセージ
    total_issues = result["summary"]["total_issues"]
    high_issues = result["summary"]["high_priority_issues"]
    medium_issues = result["summary"]["medium_priority_issues"]
    low_issues = result["summary"]["low_priority_issues"]

    print(f"\n🎉 分析完了! 時間: {analysis_time:.2f}秒")
    print(f"📋 発見された問題: {total_issues}件")
    print(f"  🔴 高優先度: {high_issues}件")
    print(f"  🟡 中優先度: {medium_issues}件")
    print(f"  🟢 低優先度: {low_issues}件")

    if args.verbose and "performance_summary" in result:
        perf = result["performance_summary"]
        print(f"⚡ 処理速度: {perf.get('files_per_second', 'N/A')} ファイル/秒")

    # 次のステップ提案
    if high_issues > 0:
        print("\n🎯 次のアクション:")
        print(f"  1. 高優先度の{high_issues}件から対処することを推奨します")
        print(f"  2. レポートを確認: {args.output}")
    elif medium_issues > 0:
        print(
            f"\n💡 良い状態です! 中優先度の{medium_issues}件から改善するとさらに良くなります"
        )
    else:
        print("\n🌟 素晴らしい! クリーンなコードベースのようです")


if __name__ == "__main__":
    main()
