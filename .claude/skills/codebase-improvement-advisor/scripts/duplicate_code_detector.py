"""
Duplicate Code Detector - SDEC×2SCV×ACR Framework Implementation
Single Responsibility: Detect duplicate code using various algorithms
Implements evidence-based duplicate detection with AST hash analysis
"""

import re
from collections import defaultdict
from pathlib import Path
from typing import List

# Import from main analyzer
from codebase_analyzer import CodeIssue, FunctionInfo, ClassInfo, JSCPD_AVAILABLE


class DuplicateCodeDetector:
    """
    Single Responsibility: Detect duplicate code using various algorithms
    Implements SDEC×2SCV×ACR framework for evidence-based duplicate detection

    This class was extracted from CodebaseAnalyzer to follow Single Responsibility Principle
    as part of the SDEC×2SCV×ACR framework implementation.
    """

    def __init__(self, project_path: Path):
        """Initialize the duplicate detector with project context"""
        self.project_path = project_path
        self.issues: List[CodeIssue] = []

    def detect_all_duplicates(self, all_functions: List[FunctionInfo],
                            all_classes: List[ClassInfo]) -> List[CodeIssue]:
        """
        Detect all types of duplicate code across functions and classes

        Args:
            all_functions: List of function information from AST analysis
            all_classes: List of class information from AST analysis

        Returns:
            List of CodeIssue objects representing detected duplicates
        """
        self.issues = []

        # Evidence-based detection using multiple strategies
        self._detect_duplicate_functions(all_functions)
        self._detect_duplicate_classes(all_classes)
        self._detect_similar_function_names(all_functions)

        return self.issues

    def _detect_duplicate_functions(self, functions: List[FunctionInfo]):
        """
        Detect duplicate functions using AST hash (evidence-based approach)

        Spec: Group functions by their AST structural hash
        Data: Use AST body_hash as structural evidence
        Eval: Verify hash matches indicate actual code duplication
        Change: Report duplicates with actionable suggestions
        """
        hash_groups = defaultdict(list)

        # Data: Collect evidence by grouping functions by AST hash
        for func in functions:
            hash_groups[func.body_hash].append(func)

        # Eval: Filter groups with multiple functions (evidence of duplication)
        for _hash_val, funcs in hash_groups.items():
            if len(funcs) > 1:
                # Change: Generate actionable issues for each duplicate
                for func in funcs[1:]:  # Report 2nd and subsequent as duplicates
                    self.issues.append(CodeIssue(
                        file_path=func.file,
                        line_number=func.lineno,
                        issue_type="duplication",
                        severity="medium",
                        title=f"重複関数: {func.name}",
                        description=f"この関数は{funcs[0].file}の関数と同一実装です。",
                        suggestion="共通ユーティリティ関数として抽出することを検討してください。",
                        effort_estimate="1h",
                    ))

    def _detect_duplicate_classes(self, classes: List[ClassInfo]):
        """
        Detect duplicate classes using AST hash (evidence-based approach)

        Spec: Identify class-level code duplication
        Data: Use class body structural hash as evidence
        Eval: Verify structural similarity indicates actual duplication
        Change: Report with refactoring recommendations
        """
        hash_groups = defaultdict(list)

        # Data: Collect evidence by grouping classes by AST hash
        for cls in classes:
            hash_groups[cls.body_hash].append(cls)

        # Eval: Identify actual duplicates
        for _hash_val, classes_group in hash_groups.items():
            if len(classes_group) > 1:
                # Change: Generate actionable issues
                for cls in classes_group[1:]:  # Report 2nd and subsequent as duplicates
                    self.issues.append(CodeIssue(
                        file_path=cls.file,
                        line_number=cls.lineno,
                        issue_type="duplication",
                        severity="high",
                        title=f"重複クラス: {cls.name}",
                        description=f"このクラスは{classes_group[0].file}のクラスと同一実装です。",
                        suggestion="共通基底クラスまたはユーティリティとして抽出することを検討してください。",
                        effort_estimate="2h",
                    ))

    def _detect_similar_function_names(self, functions: List[FunctionInfo]):
        """
        Detect functions with similar names (naming inconsistency)

        Spec: Identify potential naming inconsistencies
        Data: Use normalized function names as evidence
        Eval: Check if similar names indicate the same functionality
        Change: Suggest naming convention improvements
        """
        name_groups = defaultdict(list)

        # Data: Normalize function names to detect similarities
        for func in functions:
            # Normalize by removing underscores and converting to lowercase
            normalized = re.sub(r'[_-]', '', func.name.lower())
            name_groups[normalized].append(func)

        # Eval: Identify potential naming issues
        for normalized, funcs in name_groups.items():
            if len(funcs) > 1 and len(set(f.name for f in funcs)) > 1:
                func_names = [f.name for f in funcs]
                # Change: Generate naming improvement suggestions
                for func in funcs:
                    self.issues.append(CodeIssue(
                        file_path=func.file,
                        line_number=func.lineno,
                        issue_type="naming",
                        severity="low",
                        title=f"類似関数名: {func.name}",
                        description=f"類似する名前の関数が存在します: {', '.join(func_names)}",
                        suggestion="命名規約を統一してください。",
                        effort_estimate="30m",
                    ))


# Export for backward compatibility
__all__ = ['DuplicateCodeDetector']