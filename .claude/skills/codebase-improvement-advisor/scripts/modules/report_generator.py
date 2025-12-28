"""Report generation for codebase analysis results."""

from datetime import datetime


def generate_markdown_report(analysis_result: dict, output_path: str):
    """Markdown形式のレポートを生成"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(
            f"""# コードベース改善提案レポート

生成日時: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📊 サマリー

- **分析ファイル数**: {analysis_result["summary"]["total_files"]} ファイル
- **総コード行数**: {analysis_result["summary"]["total_lines"]:,} 行
- **発見された問題**: {analysis_result["summary"]["total_issues"]} 件
  - 🔴 高優先度: {analysis_result["summary"]["high_priority_issues"]} 件
  - 🟡 中優先度: {analysis_result["summary"]["medium_priority_issues"]} 件
  - 🟢 低優先度: {analysis_result["summary"]["low_priority_issues"]} 件

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

            for i, issue in enumerate(issues[:10], 1):  # Show first 10 issues
                f.write(f"#### {i}. {issue.title}\n\n")
                f.write(f"**ファイル**: `{issue.file_path}:{issue.line_number}`\n\n")
                f.write(f"**説明**: {issue.description}\n\n")
                f.write(f"**提案**: {issue.suggestion}\n\n")
                f.write(f"**見積もり**: {issue.effort_estimate}\n\n")
                f.write("---\n\n")

            if len(issues) > 10:
                f.write(f"... さらに {len(issues) - 10} 件の問題\n\n")

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

    print(f"📝 レポートを生成しました: {output_path}")
