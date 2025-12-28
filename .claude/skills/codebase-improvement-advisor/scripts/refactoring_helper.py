#!/usr/bin/env python3
"""
Refactoring Helper - リファクタリング支援ツール

使用方法:
python refactoring_helper.py --file path/to/file.ts --action extract-function --start-line 10 --end-line 25
python refactoring_helper.py --project-path /path/to/project --action suggest-refactoring

主な機能:
- 関数抽出の提案
- 変数名の改善提案
- 重複コードの統合支援
- 型定義の改善提案
"""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RefactoringSuggestion:
    """リファクタリング提案"""

    action: str
    title: str
    description: str
    before_code: str
    after_code: str
    line_start: int
    line_end: int
    impact: str  # 'high', 'medium', 'low'


class RefactoringHelper:
    """リファクタリング支援クラス"""

    def __init__(self, file_path: str | None = None, project_path: str | None = None):
        self.file_path = Path(file_path) if file_path else None
        self.project_path = Path(project_path) if project_path else None

    def analyze_file_for_refactoring(self) -> list[RefactoringSuggestion]:
        """ファイルを分析してリファクタリング提案を生成"""
        if not self.file_path:
            return []

        with open(self.file_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        suggestions = []

        # 長い関数を検出
        suggestions.extend(self._suggest_function_extraction(content, lines))

        # マジックナンバーを検出
        suggestions.extend(self._suggest_constant_extraction(content, lines))

        # 複雑な条件式を検出
        suggestions.extend(self._suggest_condition_simplification(content, lines))

        # 改善可能な変数名を検出
        suggestions.extend(self._suggest_variable_renaming(content, lines))

        # 重複したコードパターンを検出
        suggestions.extend(self._suggest_deduplication(content, lines))

        return suggestions

    def _suggest_function_extraction(
        self, content: str, lines: list[str]
    ) -> list[RefactoringSuggestion]:
        """関数抽出を提案"""
        suggestions = []

        # 長いコードブロックを検出
        functions = self._find_functions(content)
        for func_name, start_line, _end_line, func_content in functions:
            func_lines = func_content.count("\n")
            if func_lines > 30:  # 30行超過の関数
                # 関数内で繰り返し使われるパターンを探す
                patterns = self._find_repeated_patterns(func_content)
                for pattern, occurrences in patterns.items():
                    if len(occurrences) > 1 and len(pattern.split("\n")) > 2:
                        suggestions.append(
                            RefactoringSuggestion(
                                action="extract-function",
                                title="繰り返しパターンを関数として抽出",
                                description=f"`{func_name}`関数内で{len(occurrences)}回繰り返されるコードパターンを別関数として抽出します。",
                                before_code=pattern,
                                after_code="extractedPattern(/* params */)",
                                line_start=start_line + occurrences[0],
                                line_end=start_line
                                + occurrences[0]
                                + len(pattern.split("\n"))
                                - 1,
                                impact="medium",
                            )
                        )

        return suggestions

    def _suggest_constant_extraction(
        self, content: str, lines: list[str]
    ) -> list[RefactoringSuggestion]:
        """定数抽出を提案"""
        suggestions = []

        # マジックナンバーを検出
        re.findall(r"\b(?:[1-9]\d{2,}|10[0-9]{2,})\b", content)
        for i, line in enumerate(lines, 1):
            numbers = re.findall(r"\b(?:[1-9]\d{2,}|10[0-9]{2,})\b", line)
            for num in numbers:
                # 除外するパターン
                if not any(
                    exclusion in line.lower()
                    for exclusion in ["port", "timeout", "limit", "max", "min"]
                ):
                    suggestions.append(
                        RefactoringSuggestion(
                            action="extract-constant",
                            title=f"マジックナンバー {num} を定数に",
                            description=f"数値 {num} を意味のある名前の定数として定義します。",
                            before_code=line.strip(),
                            after_code=f"const MEANINGFUL_CONSTANT = {num};",
                            line_start=i,
                            line_end=i,
                            impact="low",
                        )
                    )

        return suggestions

    def _suggest_condition_simplification(
        self, content: str, lines: list[str]
    ) -> list[RefactoringSuggestion]:
        """条件式の単純化を提案"""
        suggestions = []

        # 複雑な条件式を検出
        for i, line in enumerate(lines, 1):
            # 多重ネストのif文
            if re.search(r"if\s*\([^)]+\)\s*\{[^}]*if\s*\(", line):
                suggestions.append(
                    RefactoringSuggestion(
                        action="simplify-condition",
                        title="複雑な条件式の単純化",
                        description="複雑な条件式を早期リターンやガード節で単純化します。",
                        before_code=line.strip(),
                        after_code="# 早期リターンやガード節を検討",
                        line_start=i,
                        line_end=i,
                        impact="medium",
                    )
                )

            # 長い条件式
            if "&&" in line and line.count("&&") > 2:
                suggestions.append(
                    RefactoringSuggestion(
                        action="extract-condition",
                        title="長い条件式の抽出",
                        description="複数の条件をまとめた変数や関数として抽出します。",
                        before_code=line.strip(),
                        after_code="const isValidCondition = condition1 && condition2 && condition3;",
                        line_start=i,
                        line_end=i,
                        impact="medium",
                    )
                )

        return suggestions

    def _suggest_variable_renaming(
        self, content: str, lines: list[str]
    ) -> list[RefactoringSuggestion]:
        """変数名の改善を提案"""
        suggestions = []

        # 改善が必要な変数名パターン
        bad_name_patterns = [
            (r"\b[a-z]\b", "単一文字の変数名"),
            (r"\btemp\b", "temp変数"),
            (r"\bdata\d*\b", "一般的なdata変数名"),
            (r"\bobj\b", "一般的なobj変数名"),
            (r"\bresult\b", "result変数名"),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, description in bad_name_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    # 変数宣言のみを対象
                    if re.search(r"(?:const|let|var)\s+" + re.escape(match), line):
                        suggestions.append(
                            RefactoringSuggestion(
                                action="rename-variable",
                                title=f"変数名の改善: {match}",
                                description=f"{description}をより具体的な名前に変更します。",
                                before_code=line.strip(),
                                after_code=f"const {match} -> const descriptiveVariableName",
                                line_start=i,
                                line_end=i,
                                impact="low",
                            )
                        )

        return suggestions

    def _suggest_deduplication(
        self, content: str, lines: list[str]
    ) -> list[RefactoringSuggestion]:
        """重複コードの統合を提案"""
        suggestions = []

        # 似たようなコードブロックを検出
        code_blocks = []
        block_size = 5  # 5行単位で比較

        for i in range(len(lines) - block_size + 1):
            block = "\n".join(lines[i : i + block_size])
            code_blocks.append((i + 1, block))

        # 類似ブロックを探す
        for i, (line1, block1) in enumerate(code_blocks):
            for _j, (line2, block2) in enumerate(code_blocks[i + 1 :], i + 1):
                similarity = self._calculate_similarity(block1, block2)
                if similarity > 0.8:  # 80%以上の類似度
                    suggestions.append(
                        RefactoringSuggestion(
                            action="deduplicate",
                            title=f"重複コードの統合 ({similarity:.0%}類似)",
                            description=f"{line1}行目と{line2}行目で類似コードが見つかりました。共通関数として抽出します。",
                            before_code=block1[:100] + "...",
                            after_code="extractedCommonFunction()",
                            line_start=line1,
                            line_end=line1 + block_size - 1,
                            impact="high",
                        )
                    )

        return suggestions

    def _find_functions(self, content: str) -> list[tuple[str, int, int, str]]:
        """関数を見つける"""
        functions = []

        # TypeScript/JavaScriptの関数パターン
        patterns = [
            r"function\s+(\w+)\s*\([^)]*\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}",
            r"const\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}",
            r"(\w+)\s*:\s*\([^)]*\)\s*=>\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}",
        ]

        content.split("\n")

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                func_name = match.group(1)
                start_line = content[: match.start()].count("\n") + 1
                func_content = match.group(0)
                end_line = start_line + func_content.count("\n") - 1

                functions.append((func_name, start_line, end_line, func_content))

        return functions

    def _find_repeated_patterns(self, content: str) -> dict[str, list[int]]:
        """繰り返しパターンを見つける"""
        lines = content.split("\n")
        patterns = {}

        # 2-5行のパターンを検索
        for pattern_length in range(2, 6):
            for i in range(len(lines) - pattern_length + 1):
                pattern = "\n".join(lines[i : i + pattern_length])
                if len(pattern.strip()) < 20:  # 短すぎるパターンは無視
                    continue

                if pattern not in patterns:
                    patterns[pattern] = []
                patterns[pattern].append(i)

        # 複数回出現するパターンのみを返す
        return {k: v for k, v in patterns.items() if len(v) > 1}

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """テキストの類似度を計算"""
        # 簡易的な類似度計算
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0

    def apply_refactoring(self, suggestion: RefactoringSuggestion) -> str:
        """リファクタリングを適用したコードを生成"""
        if not self.file_path:
            return ""

        with open(self.file_path, encoding="utf-8") as f:
            lines = f.readlines()

        # 実際のリファクタリングロジック（ここでは簡易実装）
        if suggestion.action == "extract-constant":
            # 定数抽出の例
            lines.insert(
                0,
                f"const {suggestion.title.split()[-1]} = {suggestion.before_code.split()[-1]};\n",
            )

        elif suggestion.action == "extract-function":
            # 関数抽出の例
            func_signature = "function extractedFunction() {\n}"
            lines.insert(suggestion.line_start - 1, func_signature + "\n")

        return "".join(lines)


def generate_refactoring_report(
    suggestions: list[RefactoringSuggestion], output_path: str
):
    """リファクタリング提案レポートを生成"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(
            """# リファクタリング提案レポート

## 🎯 概要

このレポートはコードの品質向上のためのリファクタリング提案をまとめたものです。

## 📋 提案一覧

"""
        )

        # 影響度別にグループ化
        by_impact = {"high": [], "medium": [], "low": []}
        for suggestion in suggestions:
            by_impact[suggestion.impact].append(suggestion)

        for impact in ["high", "medium", "low"]:
            impact_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            impact_text = {"high": "高影響", "medium": "中影響", "low": "低影響"}

            if not by_impact[impact]:
                continue

            f.write(
                f"### {impact_emoji[impact]} {impact_text[impact]} ({len(by_impact[impact])}件)\n\n"
            )

            for i, suggestion in enumerate(by_impact[impact], 1):
                f.write(f"#### {i}. {suggestion.title}\n\n")
                f.write(f"**説明**: {suggestion.description}\n\n")
                f.write(
                    f"**場所**: {suggestion.line_start}行目-{suggestion.line_end}行目\n\n"
                )
                f.write(f"**影響度**: {suggestion.impact}\n\n")

                if suggestion.before_code and suggestion.after_code:
                    f.write("**変更例**:\n")
                    f.write("```diff\n")
                    f.write(f"- {suggestion.before_code}\n")
                    f.write(f"+ {suggestion.after_code}\n")
                    f.write("```\n\n")

                f.write("---\n\n")


def main():
    parser = argparse.ArgumentParser(description="リファクタリング支援ツール")
    parser.add_argument("--file", help="分析するファイル")
    parser.add_argument("--project-path", help="分析するプロジェクトパス")
    parser.add_argument(
        "--action", choices=["analyze", "suggest-refactoring"], default="analyze"
    )
    parser.add_argument(
        "--output", default="refactoring_suggestions.md", help="出力ファイル"
    )
    parser.add_argument("--start-line", type=int, help="開始行")
    parser.add_argument("--end-line", type=int, help="終了行")

    args = parser.parse_args()

    if not args.file and not args.project_path:
        print("❌ エラー: --file または --project-path のいずれかを指定してください")
        sys.exit(1)

    helper = RefactoringHelper(args.file, args.project_path)

    if args.action == "analyze":
        suggestions = helper.analyze_file_for_refactoring()
        generate_refactoring_report(suggestions, args.output)
        print(f"✅ リファクタリング提案を生成しました: {args.output}")
        print(f"   {len(suggestions)}件の提案があります")


if __name__ == "__main__":
    main()
