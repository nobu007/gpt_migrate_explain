"""Advanced code analysis with AST support."""

import ast
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

try:
    import rope.base.project

    ROPE_AVAILABLE = True
except ImportError:
    ROPE_AVAILABLE = False

from .models import ClassInfo, FunctionInfo


@dataclass
class AnalyzerConfig:
    """アナライザー設定"""

    def __init__(self):
        self.target_extensions = {".py", ".js", ".ts", ".tsx", ".jsx"}
        self.ignore_dirs = {"node_modules", ".git", "__pycache__", ".pytest_cache"}
        self.parallel_processing_threshold = 10
        self.default_max_workers = 4


class AdvancedCodeAnalyzer:
    """高度なコード分析クラス"""

    def __init__(self, project_path: str, config: AnalyzerConfig | None = None):
        self.project_path = Path(project_path).resolve()
        self.config = config or AnalyzerConfig()
        self.functions: list[FunctionInfo] = []
        self.classes: list[ClassInfo] = []
        self.current_file: str | None = None

        if ROPE_AVAILABLE:
            try:
                self.rope_project = rope.base.project.Project(str(self.project_path))
            except Exception:
                self.rope_project = None
        else:
            self.rope_project = None

    def analyze_python_file(self, file_path: Path) -> dict:
        """Pythonファイルを分析"""
        if file_path.suffix != ".py":
            return self._basic_analysis(file_path)

        try:
            return self._ast_analysis(file_path)
        except Exception as e:
            print(f"Warning: AST analysis failed for {file_path}: {e}")
            return self._basic_analysis(file_path)

    def _ast_analysis(self, file_path: Path) -> dict:
        """ASTベースの分析"""
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

    def _basic_analysis(self, file_path: Path) -> dict:
        """基本的な分析"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            if file_path.suffix == ".py":
                return self._ast_analysis(file_path)
            else:
                return self._generic_analysis(content, str(file_path))

        except Exception as e:
            print(f"Basic analysis failed for {file_path}: {e}")
            return {"functions": [], "classes": [], "success": False}

    def _generic_analysis(self, content: str, file_path: str) -> dict:
        """汎用的な分析"""
        functions = []
        classes = []

        func_patterns = [
            r"function\s+(\w+)\s*\(",
            r"def\s+(\w+)\s*\(",
        ]

        class_patterns = [
            r"class\s+(\w+)",
            r"interface\s+(\w+)",
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

    def set_file(self, filepath: str) -> None:
        """現在分析中のファイルパスを設定"""
        self.current_file = filepath

    def _walk_ast(self, node):
        """ASTをウォーク"""
        for child in ast.walk(node):
            if isinstance(child, ast.FunctionDef):
                self._extract_function(child)
            elif isinstance(child, ast.ClassDef):
                self._extract_class(child)

    def _extract_function(self, node):
        """関数情報を抽出"""
        func_info = FunctionInfo(
            name=node.name,
            file=self.current_file or "unknown",
            lineno=node.lineno,
            args=[arg.arg for arg in node.args.args],
            body_hash=self._get_node_hash(node),
            body_lines=(
                node.end_lineno - node.lineno + 1 if hasattr(node, "end_lineno") else 0
            ),
            complexity=self._calculate_complexity(node),
        )
        self.functions.append(func_info)

    def _extract_class(self, node):
        """クラス情報を抽出"""
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)

        class_info = ClassInfo(
            name=node.name,
            file=self.current_file or "unknown",
            lineno=node.lineno,
            methods=methods,
            body_hash=self._get_node_hash(node),
            body_lines=(
                node.end_lineno - node.lineno + 1 if hasattr(node, "end_lineno") else 0
            ),
            complexity=self._calculate_complexity(node),
        )
        self.classes.append(class_info)

    def _get_node_hash(self, node) -> str:
        """ASTノードのハッシュを生成"""
        node_str = ast.dump(node, include_attributes=False)
        return hashlib.md5(node_str.encode()).hexdigest()

    def _calculate_complexity(self, node) -> int:
        """循環的複雑度を計算"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
        return complexity
