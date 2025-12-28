"""Data models for codebase analysis."""

from dataclasses import dataclass


@dataclass
class CodeIssue:
    """コードの問題点を表現するデータクラス"""

    file_path: str
    line_number: int
    issue_type: str
    severity: str
    title: str
    description: str
    suggestion: str
    effort_estimate: str


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
