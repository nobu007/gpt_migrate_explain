#!/usr/bin/env python3
"""
Spec Workflow - PRDとSPECの整合性を検証するスクリプト

PRDドキュメントと生成されたSPECファイル間の整合性をチェックし、
品質問題を検出して修正提案を生成する
"""

import argparse
import json
import re
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path


class PRDSpecValidator:
    def __init__(self, prd_path: str, spec_path: str, output_path: str):
        self.prd_path = Path(prd_path)
        self.spec_path = Path(spec_path)
        self.output_path = Path(output_path)

        # SPECファイルパス
        self.requirements_md = self.spec_path / "requirements.md"
        self.design_md = self.spec_path / "design.md"
        self.tasks_md = self.spec_path / "tasks.md"

    def validate_all(self) -> dict:
        """全ての整合性チェックを実行"""
        validation_result = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "prd_file": str(self.prd_path),
            "spec_path": str(self.spec_path),
            "overall_status": "passed",
            "checks": {},
            "issues": [],
            "recommendations": [],
        }

        print("🔍 Starting PRD-SPEC validation...")

        # 基本ファイルチェック
        self._check_file_existence(validation_result)

        # 内容の網羅性チェック
        self._check_content_coverage(validation_result)

        # 技術的一貫性チェック
        self._check_technical_consistency(validation_result)

        # タスク網羅性チェック
        self._check_task_coverage(validation_result)

        # 品質メトリクス計算
        self._calculate_quality_metrics(validation_result)

        # レポート生成
        self._generate_validation_report(validation_result)

        return validation_result

    def _check_file_existence(self, result: dict) -> None:
        """ファイル存在チェック"""
        print("📁 Checking file existence...")

        check_result = {"passed": True, "missing_files": []}

        required_files = [self.requirements_md, self.design_md, self.tasks_md]

        for file_path in required_files:
            if not file_path.exists():
                check_result["missing_files"].append(str(file_path))
                check_result["passed"] = False

        if not check_result["passed"]:
            result["overall_status"] = "failed"
            result["issues"].append(
                {
                    "type": "missing_files",
                    "severity": "critical",
                    "description": f"Missing required SPEC files: {check_result['missing_files']}",
                    "recommendation": "Generate missing SPEC files using generate_spec_from_prd.py",
                }
            )

        result["checks"]["file_existence"] = check_result
        print(
            f"{'✅' if check_result['passed'] else '❌'} File existence check completed"
        )

    def _check_content_coverage(self, result: dict) -> None:
        """内容網羅性チェック"""
        print("📖 Checking content coverage...")

        if not self.prd_path.exists():
            result["overall_status"] = "failed"
            result["issues"].append(
                {
                    "type": "missing_prd",
                    "severity": "critical",
                    "description": f"PRD file not found: {self.prd_path}",
                    "recommendation": "Ensure PRD file exists and is accessible",
                }
            )
            return

        prd_content = self._extract_prd_content()
        spec_content = self._extract_spec_content()

        # キーワード網羅性チェック
        coverage_check = self._analyze_keyword_coverage(prd_content, spec_content)

        # 要件網羅性チェック
        requirements_check = self._analyze_requirements_coverage(
            prd_content, spec_content
        )

        check_result = {
            "passed": coverage_check["passed"] and requirements_check["passed"],
            "keyword_coverage": coverage_check,
            "requirements_coverage": requirements_check,
        }

        if not check_result["passed"]:
            result["overall_status"] = (
                "warning" if result["overall_status"] == "passed" else "failed"
            )

            if not coverage_check["passed"]:
                result["issues"].append(
                    {
                        "type": "insufficient_keyword_coverage",
                        "severity": "medium",
                        "description": f"Low keyword coverage: {coverage_check['coverage_percentage']:.1f}%",
                        "recommendation": "Review and expand SPEC content to better reflect PRD requirements",
                    }
                )

            if not requirements_check["passed"]:
                result["issues"].append(
                    {
                        "type": "missing_requirements",
                        "severity": "high",
                        "description": f"Missing key requirements: {requirements_check['missing_count']} items",
                        "recommendation": "Add missing functional and non-functional requirements to SPEC",
                    }
                )

        result["checks"]["content_coverage"] = check_result
        print(
            f"{'✅' if check_result['passed'] else '❌'} Content coverage check completed"
        )

    def _check_technical_consistency(self, result: dict) -> None:
        """技術的一貫性チェック"""
        print("🔧 Checking technical consistency...")

        if not self.design_md.exists():
            result["checks"]["technical_consistency"] = {
                "passed": False,
                "reason": "design.md missing",
            }
            return

        consistency_check = self._analyze_technical_consistency()

        check_result = {
            "passed": consistency_check["passed"],
            "inconsistencies": consistency_check["inconsistencies"],
            "technology_validation": consistency_check["technology_validation"],
        }

        if not consistency_check["passed"]:
            result["overall_status"] = (
                "warning" if result["overall_status"] == "passed" else "failed"
            )

            for inconsistency in consistency_check["inconsistencies"]:
                result["issues"].append(
                    {
                        "type": "technical_inconsistency",
                        "severity": "medium",
                        "description": f"Technical inconsistency: {inconsistency['description']}",
                        "recommendation": inconsistency["recommendation"],
                    }
                )

        result["checks"]["technical_consistency"] = check_result
        print(
            f"{'✅' if check_result['passed'] else '❌'} Technical consistency check completed"
        )

    def _check_task_coverage(self, result: dict) -> None:
        """タスク網羅性チェック"""
        print("🔨 Checking task coverage...")

        if not self.tasks_md.exists():
            result["checks"]["task_coverage"] = {
                "passed": False,
                "reason": "tasks.md missing",
            }
            return

        task_check = self._analyze_task_coverage()

        check_result = {
            "passed": task_check["passed"],
            "task_analysis": task_check,
            "coverage_metrics": task_check["coverage_metrics"],
        }

        if not task_check["passed"]:
            result["overall_status"] = (
                "warning" if result["overall_status"] == "passed" else "failed"
            )

            result["issues"].append(
                {
                    "type": "insufficient_task_coverage",
                    "severity": "high",
                    "description": f"Insufficient task coverage: {task_check['coverage_metrics']['task_count']} tasks",
                    "recommendation": "Expand tasks.md to include more detailed implementation tasks",
                }
            )

        result["checks"]["task_coverage"] = check_result
        print(
            f"{'✅' if check_result['passed'] else '❌'} Task coverage check completed"
        )

    def _extract_prd_content(self) -> dict:
        """PRDからキーコンテンツを抽出"""
        content = self.prd_path.read_text(encoding="utf-8")

        return {
            "text": content,
            "keywords": self._extract_keywords(content),
            "sections": self._extract_sections(content),
            "requirements": self._extract_requirements(content),
        }

    def _extract_spec_content(self) -> dict:
        """SPECからキーコンテンツを抽出"""
        spec_content = {}

        for file_path, file_key in [
            (self.requirements_md, "requirements"),
            (self.design_md, "design"),
            (self.tasks_md, "tasks"),
        ]:
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                spec_content[file_key] = {
                    "text": content,
                    "keywords": self._extract_keywords(content),
                    "sections": self._extract_sections(content),
                    "size": len(content),
                }

        return spec_content

    def _extract_keywords(self, text: str) -> set[str]:
        """テキストから重要キーワードを抽出"""
        # 技術キーワードリスト
        tech_keywords = {
            "api",
            "database",
            "security",
            "authentication",
            "authorization",
            "frontend",
            "backend",
            "ui",
            "ux",
            "performance",
            "scalability",
            "react",
            "typescript",
            "python",
            "fastapi",
            "postgresql",
            "docker",
            "aws",
            "azure",
            "cloud",
            "deployment",
            "testing",
            "integration",
            "monitoring",
            "logging",
            "cache",
            "queue",
        }

        # ビジネスキーワード抽出
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        word_freq = {}
        for word in words:
            if word in tech_keywords or len(word) > 6:  # 重要な長単語も含める
                word_freq[word] = word_freq.get(word, 0) + 1

        # 頻度が高いキーワードを返す
        return {word for word, freq in word_freq.items() if freq >= 2}

    def _extract_sections(self, text: str) -> list[dict]:
        """Markdownセクションを抽出"""
        sections = []
        lines = text.split("\n")

        for line in lines:
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                title = line.lstrip("# ").strip()
                sections.append({"level": level, "title": title})

        return sections

    def _extract_requirements(self, text: str) -> list[str]:
        """要件を抽出"""
        # 要件と思われる箇条書きを抽出
        requirements = []

        # 数字付きリスト
        numbered_items = re.findall(r"^\d+\.\s+(.+)$", text, re.MULTILINE)
        requirements.extend(
            [req.strip() for req in numbered_items if len(req.strip()) > 20]
        )

        # 箇条書き
        bullet_items = re.findall(r"^[•\-\*]\s+(.+)$", text, re.MULTILINE)
        requirements.extend(
            [req.strip() for req in bullet_items if len(req.strip()) > 20]
        )

        return requirements[:20]  # 上位20個

    def _analyze_keyword_coverage(self, prd_content: dict, spec_content: dict) -> dict:
        """キーワード網羅性を分析"""
        prd_keywords = prd_content["keywords"]
        spec_keywords = set()

        for spec_file in spec_content.values():
            spec_keywords.update(spec_file["keywords"])

        coverage = prd_keywords.intersection(spec_keywords)
        missing = prd_keywords - spec_keywords

        coverage_percentage = (
            (len(coverage) / len(prd_keywords) * 100) if prd_keywords else 100
        )

        return {
            "passed": coverage_percentage >= 70,  # 70%以上で合格
            "prd_keyword_count": len(prd_keywords),
            "spec_keyword_count": len(spec_keywords),
            "covered_keywords": list(coverage),
            "missing_keywords": list(missing),
            "coverage_percentage": coverage_percentage,
        }

    def _analyze_requirements_coverage(
        self, prd_content: dict, spec_content: dict
    ) -> dict:
        """要件網羅性を分析"""
        prd_requirements = prd_content["requirements"]

        # SPECから要件を抽出
        spec_requirements = []
        if "requirements" in spec_content:
            req_text = spec_content["requirements"]["text"]
            spec_requirements = self._extract_requirements(req_text)

        # テキスト類似度で要件の対応をチェック
        coverage_count = 0
        for prd_req in prd_requirements:
            for spec_req in spec_requirements:
                similarity = SequenceMatcher(
                    None, prd_req.lower(), spec_req.lower()
                ).ratio()
                if similarity > 0.6:  # 60%以上の類似度で対応とみなす
                    coverage_count += 1
                    break

        coverage_percentage = (
            (coverage_count / len(prd_requirements) * 100) if prd_requirements else 100
        )

        return {
            "passed": coverage_percentage >= 60,  # 60%以上で合格
            "prd_requirement_count": len(prd_requirements),
            "spec_requirement_count": len(spec_requirements),
            "covered_count": coverage_count,
            "missing_count": len(prd_requirements) - coverage_count,
            "coverage_percentage": coverage_percentage,
        }

    def _analyze_technical_consistency(self) -> dict:
        """技術的一貫性を分析"""
        design_content = self.design_md.read_text(encoding="utf-8")

        inconsistencies = []

        # 技術スタックの一貫性チェック
        tech_stack = self._extract_tech_stack(design_content)
        if len(tech_stack) < 3:
            inconsistencies.append(
                {
                    "description": "Insufficient technology stack specification",
                    "recommendation": "Define complete technology stack including frontend, backend, database",
                }
            )

        # アーキテクチャ一貫性チェック
        if "architecture" not in design_content.lower():
            inconsistencies.append(
                {
                    "description": "Missing architecture description",
                    "recommendation": "Add detailed system architecture section",
                }
            )

        # APIデザインチェック
        if "api" not in design_content.lower():
            inconsistencies.append(
                {
                    "description": "Missing API design specification",
                    "recommendation": "Add API endpoint definitions and data models",
                }
            )

        technology_validation = self._validate_technology_stack(tech_stack)

        return {
            "passed": len(inconsistencies) == 0 and technology_validation["passed"],
            "inconsistencies": inconsistencies,
            "technology_validation": technology_validation,
            "tech_stack": tech_stack,
        }

    def _extract_tech_stack(self, text: str) -> set[str]:
        """技術スタックを抽出"""
        tech_patterns = {
            "frontend": r"\b(react|vue|angular|typescript|javascript|html|css)\b",
            "backend": r"\b(python|java|node|fastapi|django|spring|express)\b",
            "database": r"\b(postgresql|mysql|mongodb|redis|sqlite)\b",
            "cloud": r"\b(aws|azure|gcp|docker|kubernetes)\b",
        }

        tech_stack = set()
        for _category, pattern in tech_patterns.items():
            matches = re.findall(pattern, text.lower())
            tech_stack.update(matches)

        return tech_stack

    def _validate_technology_stack(self, tech_stack: set[str]) -> dict:
        """技術スタックの妥当性を検証"""
        issues = []

        # 各レイヤーに技術が含まれているか
        layers = {
            "frontend": ["react", "vue", "angular", "typescript"],
            "backend": ["python", "java", "node", "fastapi"],
            "database": ["postgresql", "mysql", "mongodb"],
        }

        layer_coverage = {}
        for layer, technologies in layers.items():
            covered = any(tech in tech_stack for tech in technologies)
            layer_coverage[layer] = covered
            if not covered:
                issues.append(f"Missing {layer} technology specification")

        return {
            "passed": len(issues) == 0,
            "layer_coverage": layer_coverage,
            "issues": issues,
        }

    def _analyze_task_coverage(self) -> dict:
        """タスク網羅性を分析"""
        tasks_content = self.tasks_md.read_text(encoding="utf-8")

        # タスク数をカウント
        task_count = tasks_content.count("- [ ]")

        # フェーズ構造のチェック
        phases = re.findall(r"#{1,2}\s+Phase\s+\d+", tasks_content, re.IGNORECASE)

        # タスク詳細度のチェック
        task_details = re.findall(r"- \[ \] .+: .+", tasks_content)
        detailed_task_ratio = len(task_details) / task_count if task_count > 0 else 0

        # タイムラインのチェック
        has_timeline = any(
            keyword in tasks_content.lower()
            for keyword in ["week", "timeline", "schedule"]
        )

        return {
            "passed": task_count >= 10 and detailed_task_ratio >= 0.7,
            "task_count": task_count,
            "phase_count": len(phases),
            "detailed_task_count": len(task_details),
            "detailed_task_ratio": detailed_task_ratio,
            "has_timeline": has_timeline,
            "coverage_metrics": {
                "task_count": task_count,
                "minimum_required": 10,
                "detail_ratio": detailed_task_ratio,
                "phase_structure": len(phases) > 0,
            },
        }

    def _calculate_quality_metrics(self, result: dict) -> None:
        """品質メトリクスを計算"""
        metrics = {
            "completeness_score": 0,
            "consistency_score": 0,
            "detail_score": 0,
            "overall_score": 0,
        }

        # 完全性スコア
        if "file_existence" in result["checks"]:
            file_score = 100 if result["checks"]["file_existence"]["passed"] else 0
        else:
            file_score = 50

        if "content_coverage" in result["checks"]:
            content_score = 80 if result["checks"]["content_coverage"]["passed"] else 40
        else:
            content_score = 50

        metrics["completeness_score"] = (file_score + content_score) / 2

        # 一貫性スコア
        if "technical_consistency" in result["checks"]:
            metrics["consistency_score"] = (
                90 if result["checks"]["technical_consistency"]["passed"] else 50
            )
        else:
            metrics["consistency_score"] = 50

        # 詳細度スコア
        if "task_coverage" in result["checks"]:
            task_score = 90 if result["checks"]["task_coverage"]["passed"] else 60
        else:
            task_score = 50

        metrics["detail_score"] = task_score

        # 総合スコア
        metrics["overall_score"] = (
            metrics["completeness_score"] * 0.4
            + metrics["consistency_score"] * 0.3
            + metrics["detail_score"] * 0.3
        )

        result["quality_metrics"] = metrics

    def _generate_validation_report(self, validation_result: dict) -> None:
        """検証レポートを生成"""
        report = f"""# PRD-SPEC Validation Report

## Summary
- **Validation Timestamp**: {validation_result['timestamp']}
- **Overall Status**: {validation_result['overall_status'].upper()}
- **PRD File**: {validation_result['prd_file']}
- **Spec Path**: {validation_result['spec_path']}

## Quality Metrics
- **Completeness Score**: {validation_result['quality_metrics']['completeness_score']:.1f}/100
- **Consistency Score**: {validation_result['quality_metrics']['consistency_score']:.1f}/100
- **Detail Score**: {validation_result['quality_metrics']['detail_score']:.1f}/100
- **Overall Score**: {validation_result['quality_metrics']['overall_score']:.1f}/100

## Detailed Results

### File Existence Check
{self._format_check_result(validation_result.get('checks', {}).get('file_existence', {}))}

### Content Coverage Check
{self._format_check_result(validation_result.get('checks', {}).get('content_coverage', {}))}

### Technical Consistency Check
{self._format_check_result(validation_result.get('checks', {}).get('technical_consistency', {}))}

### Task Coverage Check
{self._format_check_result(validation_result.get('checks', {}).get('task_coverage', {}))}

## Issues Found ({len(validation_result['issues'])})
"""

        for i, issue in enumerate(validation_result["issues"], 1):
            report += f"""
### {i}. {issue['type'].replace('_', ' ').title()}
- **Severity**: {issue['severity'].upper()}
- **Description**: {issue['description']}
- **Recommendation**: {issue['recommendation']}
"""

        report += f"""

## Recommendations
{chr(10).join([f"- {rec}" for rec in validation_result['recommendations']])}

---
Generated by Spec Flow Auto Validator
"""

        # レポート保存
        self.output_path.mkdir(parents=True, exist_ok=True)
        report_file = self.output_path / "validation_report.md"
        report_file.write_text(report, encoding="utf-8")

        # JSON保存
        json_file = self.output_path / "validation_result.json"
        json_file.write_text(
            json.dumps(validation_result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print(f"📊 Validation report saved: {report_file}")

    def _format_check_result(self, check_result: dict) -> str:
        """チェック結果をフォーマット"""
        if not check_result:
            return "Not executed"

        status = "✅ PASSED" if check_result.get("passed", False) else "❌ FAILED"

        details = ""
        if "missing_files" in check_result and check_result["missing_files"]:
            details += f"\n- Missing files: {', '.join(check_result['missing_files'])}"

        if "coverage_percentage" in check_result:
            details += f"\n- Coverage: {check_result['coverage_percentage']:.1f}%"

        if "task_count" in check_result:
            details += f"\n- Tasks: {check_result['task_count']}"

        return f"{status}{details}"


def main():
    parser = argparse.ArgumentParser(description="Validate PRD-SPEC consistency")
    parser.add_argument("--prd", required=True, help="Path to PRD document")
    parser.add_argument("--spec", required=True, help="Path to SPEC directory")
    parser.add_argument("--output", required=True, help="Output directory for report")

    args = parser.parse_args()

    try:
        validator = PRDSpecValidator(args.prd, args.spec, args.output)
        result = validator.validate_all()

        # 終了コードを品質スコアに基づいて決定
        overall_score = result["quality_metrics"]["overall_score"]
        if overall_score >= 80:
            exit_code = 0  # 成功
        elif overall_score >= 60:
            exit_code = 1  # 警告
        else:
            exit_code = 2  # 失敗

        sys.exit(exit_code)

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
