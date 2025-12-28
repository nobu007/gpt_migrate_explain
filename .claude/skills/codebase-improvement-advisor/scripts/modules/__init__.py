"""Modular codebase analyzer components."""

from .advanced_analyzer import AdvancedCodeAnalyzer, AnalyzerConfig
from .jscpd_analyzer import JSCPDAnalyzer, JSCPDConfig
from .main_analyzer import CodebaseAnalyzer
from .models import ClassInfo, CodeIssue, FileMetrics, FunctionInfo
from .report_generator import generate_markdown_report

__all__ = [
    "CodeIssue",
    "FunctionInfo",
    "ClassInfo",
    "FileMetrics",
    "AdvancedCodeAnalyzer",
    "AnalyzerConfig",
    "JSCPDAnalyzer",
    "JSCPDConfig",
    "CodebaseAnalyzer",
    "generate_markdown_report",
]
