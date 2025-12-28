#!/usr/bin/env python3
"""
Document Validator - Technical Documentation Quality Validator

This script provides comprehensive validation for technical markdown documents,
checking for completeness, structure, and quality issues.
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
from dataclasses import dataclass
import re

# 共通ライブラリパスを追加（.claudeディレクトリを動的に探す）
def find_claude_lib():
    current = Path(__file__).resolve()
    for _ in range(8):  # 最大8階層まで遡る
        claude_lib = current / '.claude' / 'lib'
        if claude_lib.exists():
            return str(claude_lib)
        current = current.parent
        if current == current.parent:  # ファイルシステムルートに到達
            break
    return None  # 見つからない場合

def main():
    # 環境初期化（試行）
    claude_lib_path = find_claude_lib()
    if claude_lib_path:
        sys.path.insert(0, claude_lib_path)
        try:
            from env_utils import setup_python_path, load_env_files
            setup_python_path()
            load_env_files()
        except ImportError:
            # 共通ライブラリが見つからない場合は続行
            pass

    return validate_document_cli()


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'structure', 'content', 'style', 'technical'
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class ValidationResult:
    """Complete validation result"""
    file_path: str
    overall_score: float  # 0.0 to 1.0
    issues: List[ValidationIssue]
    metrics: Dict[str, Any]
    recommendations: List[str]


class TechnicalDocumentValidator:
    """Comprehensive validator for technical documentation"""

    def __init__(self):
        self.validation_rules = self._load_validation_rules()
        self.required_sections = self._get_required_sections()
        self.quality_metrics = self._get_quality_metrics()

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules for technical documentation"""
        return {
            'structure': {
                'has_toc': {'required': False, 'weight': 0.1},
                'has_introduction': {'required': True, 'weight': 0.2},
                'has_examples': {'required': True, 'weight': 0.3},
                'has_troubleshooting': {'required': False, 'weight': 0.1},
                'heading_hierarchy': {'required': True, 'weight': 0.2},
                'proper_sections': {'required': True, 'weight': 0.1}
            },
            'content': {
                'has_code_blocks': {'required': True, 'weight': 0.2},
                'has_links': {'required': True, 'weight': 0.1},
                'has_images': {'required': False, 'weight': 0.1},
                'covers_errors': {'required': True, 'weight': 0.3},
                'covers_performance': {'required': False, 'weight': 0.1},
                'covers_security': {'required': True, 'weight': 0.2}
            },
            'style': {
                'line_length': {'max_length': 100, 'weight': 0.2},
                'consistency': {'weight': 0.3},
                'clarity': {'weight': 0.3},
                'grammar': {'weight': 0.2}
            },
            'technical': {
                'api_documentation': {'required': False, 'weight': 0.3},
                'version_info': {'required': False, 'weight': 0.2},
                'dependencies': {'required': False, 'weight': 0.2},
                'compatibility': {'required': False, 'weight': 0.3}
            }
        }

    def _get_required_sections(self) -> List[str]:
        """Get list of required sections for technical documentation"""
        return [
            '## Overview', '## Purpose', '## Introduction',
            '## Installation', '## Usage', '## Examples',
            '## Configuration', '## Troubleshooting'
        ]

    def _get_quality_metrics(self) -> Dict[str, Any]:
        """Get quality metrics to evaluate"""
        return {
            'readability': {
                'flesch_score': {'target': 60, 'weight': 0.3},
                'sentence_length': {'target': 20, 'weight': 0.3},
                'paragraph_length': {'target': 5, 'weight': 0.4}
            },
            'completeness': {
                'section_coverage': {'weight': 0.4},
                'example_quality': {'weight': 0.3},
                'error_coverage': {'weight': 0.3}
            },
            'accuracy': {
                'code_syntax': {'weight': 0.4},
                'link_validity': {'weight': 0.3},
                'consistency': {'weight': 0.3}
            }
        }

    def validate_document(self, file_path: Path) -> ValidationResult:
        """Perform comprehensive document validation"""
        print(f"🔍 Validating document: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        issues = []

        # Structure validation
        structure_issues = self._validate_structure(content)
        issues.extend(structure_issues)

        # Content validation
        content_issues = self._validate_content(content)
        issues.extend(content_issues)

        # Style validation
        style_issues = self._validate_style(content)
        issues.extend(style_issues)

        # Technical validation
        technical_issues = self._validate_technical(content, file_path)
        issues.extend(technical_issues)

        # Calculate metrics
        metrics = self._calculate_metrics(content, issues)

        # Calculate overall score
        overall_score = self._calculate_overall_score(issues, metrics)

        # Generate recommendations
        recommendations = self._generate_recommendations(issues, metrics)

        return ValidationResult(
            file_path=str(file_path),
            overall_score=overall_score,
            issues=issues,
            metrics=metrics,
            recommendations=recommendations
        )

    def _validate_structure(self, content: str) -> List[ValidationIssue]:
        """Validate document structure"""
        issues = []

        # Check for introduction/overview
        has_intro = any(pattern in content for pattern in ['# Overview', '# Purpose', '# Introduction', '## Overview', '## Purpose', '## Introduction'])
        if not has_intro:
            issues.append(ValidationIssue(
                severity='error',
                category='structure',
                message='Missing introduction or overview section',
                suggestion='Add an overview or introduction section at the beginning',
                auto_fixable=False
            ))

        # Check heading hierarchy
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        prev_level = 0
        for i, (level_hash, title) in enumerate(headings):
            level = len(level_hash)
            if level > prev_level + 1:
                issues.append(ValidationIssue(
                    severity='warning',
                    category='structure',
                    message=f'Skipped heading level from {prev_level} to {level} at: {title}',
                    line_number=self._find_line_number(content, f"{level_hash} {title}"),
                    suggestion='Use proper heading hierarchy (e.g., H1 → H2 → H3)',
                    auto_fixable=True
                ))
            prev_level = level

        # Check for table of contents
        has_toc = any(keyword in content.lower() for keyword in ['table of contents', 'contents', '## contents'])
        if len(headings) > 10 and not has_toc:
            issues.append(ValidationIssue(
                severity='info',
                category='structure',
                message='Long document without table of contents',
                suggestion='Consider adding a table of contents for better navigation',
                auto_fixable=True
            ))

        # Check for examples section
        has_examples = any(pattern in content for pattern in ['## Examples', '## Usage', '## Code Examples'])
        if not has_examples:
            issues.append(ValidationIssue(
                severity='warning',
                category='structure',
                message='Missing examples or usage section',
                suggestion='Add examples or usage section to help users understand implementation',
                auto_fixable=False
            ))

        return issues

    def _validate_content(self, content: str) -> List[ValidationIssue]:
        """Validate document content"""
        issues = []

        # Check for code blocks
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        if not code_blocks:
            issues.append(ValidationIssue(
                severity='error',
                category='content',
                message='No code examples found',
                suggestion='Add practical code examples to illustrate usage',
                auto_fixable=False
            ))

        # Check for external links
        external_links = re.findall(r'\[.*?\]\(https?://.*?\)', content)
        if not external_links:
            issues.append(ValidationIssue(
                severity='warning',
                category='content',
                message='No external references or links found',
                suggestion='Add links to external documentation, resources, or related materials',
                auto_fixable=False
            ))

        # Check error handling coverage
        error_keywords = ['error', 'exception', 'failure', 'issue', 'problem', 'troubleshooting']
        has_error_coverage = any(keyword.lower() in content.lower() for keyword in error_keywords)
        if not has_error_coverage:
            issues.append(ValidationIssue(
                severity='warning',
                category='content',
                message='No error handling or troubleshooting information',
                suggestion='Add information about error handling and common issues',
                auto_fixable=False
            ))

        # Check for security considerations
        security_keywords = ['security', 'authentication', 'authorization', 'token', 'credential']
        has_security = any(keyword.lower() in content.lower() for keyword in security_keywords)
        if not has_security:
            issues.append(ValidationIssue(
                severity='info',
                category='content',
                message='No security considerations mentioned',
                suggestion='Consider adding security best practices if applicable',
                auto_fixable=False
            ))

        return issues

    def _validate_style(self, content: str) -> List[ValidationIssue]:
        """Validate document style"""
        issues = []
        lines = content.split('\n')

        # Check line length
        max_line_length = 100
        long_lines = [(i + 1, line) for i, line in enumerate(lines) if len(line) > max_line_length]
        if len(long_lines) > 5:  # Only flag if there are multiple long lines
            issues.append(ValidationIssue(
                severity='info',
                category='style',
                message=f'{len(long_lines)} lines exceed {max_line_length} characters',
                suggestion='Break long lines for better readability',
                auto_fixable=False
            ))

        # Check for consistent heading capitalization
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        heading_styles = []
        for _, title in headings:
            # Determine capitalization style
            if title.istitle():
                heading_styles.append('title_case')
            elif title.isupper():
                heading_styles.append('upper_case')
            else:
                heading_styles.append('mixed_case')

        if len(set(heading_styles)) > 1:
            issues.append(ValidationIssue(
                severity='info',
                category='style',
                message='Inconsistent heading capitalization',
                suggestion='Use consistent capitalization for all headings',
                auto_fixable=True
            ))

        # Check for empty sections
        section_pattern = r'\n(##+)\s+(.+)\n'
        sections = re.finditer(section_pattern, content)
        for match in sections:
            start_pos = match.end()
            next_heading = re.search(r'\n#{1,6}\s+', content[start_pos:])
            if next_heading:
                section_content = content[start_pos:start_pos + next_heading.start()]
            else:
                section_content = content[start_pos:]

            # Remove empty lines and whitespace
            cleaned_content = section_content.strip()
            if len(cleaned_content) < 20:  # Very short section
                issues.append(ValidationIssue(
                    severity='warning',
                    category='style',
                    message=f'Section "{match.group(2)}" appears to be empty or very short',
                    suggestion='Add more content to the section',
                    line_number=self._find_line_number(content, match.group(0)),
                    auto_fixable=False
                ))

        return issues

    def _validate_technical(self, content: str, file_path: Path) -> List[ValidationIssue]:
        """Validate technical aspects"""
        issues = []

        # Check code block syntax
        code_blocks = re.finditer(r'```(\w+)?\n([\s\S]*?)```', content)
        for match in code_blocks:
            language = match.group(1)
            code = match.group(2)

            if not language:
                issues.append(ValidationIssue(
                    severity='info',
                    category='technical',
                    message='Code block without language specification',
                    line_number=self._find_line_number(content, match.group(0)),
                    suggestion='Specify the programming language for syntax highlighting',
                    auto_fixable=True
                ))

            # Basic syntax checks
            if language in ['python', 'py']:
                if code.strip() and not code.strip().endswith(':') and 'def ' in code and ':' not in code:
                    issues.append(ValidationIssue(
                        severity='warning',
                        category='technical',
                        message='Python code block may be missing function definition syntax',
                        suggestion='Check Python syntax in code blocks',
                        line_number=self._find_line_number(content, match.group(0)),
                        auto_fixable=False
                    ))

        # Check for API documentation indicators
        api_keywords = ['endpoint', 'method', 'request', 'response', 'parameter', 'status code']
        has_api_content = any(keyword.lower() in content.lower() for keyword in api_keywords)

        if has_api_content:
            # If there's API content, check for proper documentation
            has_proper_api_docs = any(pattern in content.lower()
                                    for pattern in ['## api', '## endpoints', '## reference'])
            if not has_proper_api_docs:
                issues.append(ValidationIssue(
                    severity='info',
                    category='technical',
                    message='API content found but no formal API documentation section',
                    suggestion='Consider adding a formal API documentation section',
                    auto_fixable=False
                ))

        # Check for version information
        version_patterns = [
            r'version\s*[:=]\s*([\d.]+)',
            r'v(\d+\.\d+)',
            r'release\s*[:=]\s*([\d.]+)'
        ]
        has_version = any(re.search(pattern, content, re.IGNORECASE) for pattern in version_patterns)

        if not has_version:
            issues.append(ValidationIssue(
                severity='info',
                category='technical',
                message='No version information found',
                suggestion='Add version information for better tracking and compatibility',
                auto_fixable=False
            ))

        return issues

    def _calculate_metrics(self, content: str, issues: List[ValidationIssue]) -> Dict[str, Any]:
        """Calculate quality metrics"""
        lines = content.split('\n')
        words = content.split()
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        links = re.findall(r'\[.*?\]\(.*?\)', content)

        # Basic metrics
        metrics = {
            'basic': {
                'line_count': len(lines),
                'word_count': len(words),
                'heading_count': len(headings),
                'code_block_count': len(code_blocks),
                'link_count': len(links)
            }
        }

        # Quality metrics
        error_count = len([i for i in issues if i.severity == 'error'])
        warning_count = len([i for i in issues if i.severity == 'warning'])
        info_count = len([i for i in issues if i.severity == 'info'])

        metrics['quality'] = {
            'error_count': error_count,
            'warning_count': warning_count,
            'info_count': info_count,
            'total_issues': len(issues)
        }

        # Completeness metrics
        completeness_score = self._calculate_completeness_score(content, issues)
        metrics['completeness'] = {
            'score': completeness_score,
            'has_examples': len(code_blocks) > 0,
            'has_links': len(links) > 0,
            'has_headings': len(headings) > 0
        }

        return metrics

    def _calculate_completeness_score(self, content: str, issues: List[ValidationIssue]) -> float:
        """Calculate completeness score"""
        # Base score starts at 1.0
        score = 1.0

        # Deductions for missing critical elements
        if not any(pattern in content for pattern in ['## Overview', '## Purpose', '## Introduction']):
            score -= 0.2

        if not re.findall(r'```[\s\S]*?```', content):
            score -= 0.2

        if not re.findall(r'\[.*?\]\(.*?\)', content):
            score -= 0.1

        if not any(keyword.lower() in content.lower() for keyword in ['error', 'troubleshooting', 'issue']):
            score -= 0.1

        # Penalty for errors
        error_count = len([i for i in issues if i.severity == 'error'])
        score -= error_count * 0.1

        return max(0.0, score)

    def _calculate_overall_score(self, issues: List[ValidationIssue], metrics: Dict[str, Any]) -> float:
        """Calculate overall quality score"""
        # Base score from completeness
        base_score = metrics['completeness']['score']

        # Penalty for issues
        error_penalty = len([i for i in issues if i.severity == 'error']) * 0.1
        warning_penalty = len([i for i in issues if i.severity == 'warning']) * 0.05
        info_penalty = len([i for i in issues if i.severity == 'info']) * 0.02

        final_score = base_score - error_penalty - warning_penalty - info_penalty
        return max(0.0, min(1.0, final_score))

    def _generate_recommendations(self, issues: List[ValidationIssue], metrics: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        # Categorize issues
        categories = {}
        for issue in issues:
            if issue.category not in categories:
                categories[issue.category] = []
            categories[issue.category].append(issue)

        # Top recommendations by category
        if 'structure' in categories:
            structure_issues = categories['structure']
            error_issues = [i for i in structure_issues if i.severity == 'error']
            if error_issues:
                recommendations.append("Improve document structure by fixing structural errors")

        if 'content' in categories:
            content_issues = categories['content']
            if len([i for i in content_issues if i.message == 'No code examples found']) > 0:
                recommendations.append("Add practical code examples to improve content quality")

        if 'style' in categories:
            style_issues = categories['style']
            if len(style_issues) > 2:
                recommendations.append("Review and improve document style consistency")

        # Metric-based recommendations
        if metrics['basic']['heading_count'] < 3:
            recommendations.append("Add more sections with clear headings for better organization")

        if metrics['basic']['link_count'] == 0:
            recommendations.append("Add external links and references for additional context")

        if not recommendations:
            recommendations.append("Document quality is good. Consider peer review for further improvements.")

        return recommendations

    def _find_line_number(self, content: str, text: str) -> Optional[int]:
        """Find line number for a given text snippet"""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if text in line:
                return i + 1
        return None


def validate_document_cli() -> int:
    """Command-line interface for document validation"""
    parser = argparse.ArgumentParser(
        description='Validate technical documentation quality',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a markdown document (no file output)
  python document_validator.py README.md

  # Export results to specific JSON file
  python document_validator.py docs/api.md --export-json validation_results.json

  # Automatically save to logs/ directory with timestamp
  python document_validator.py README.md --auto-log

  # Show only errors and warnings
  python document_validator.py README.md --severity error,warning
        """
    )

    parser.add_argument(
        'input_file',
        type=Path,
        help='Path to the markdown file to validate'
    )

    parser.add_argument(
        '--export-json',
        type=Path,
        default=None,
        help='Export validation results to JSON file (specify path or use --auto-log for automatic naming)'
    )

    parser.add_argument(
        '--auto-log',
        action='store_true',
        help='Automatically save results to logs/ directory with timestamp'
    )

    parser.add_argument(
        '--severity',
        type=str,
        default='error,warning,info',
        help='Comma-separated list of severity levels to show (default: error,warning,info)'
    )

    parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Only show summary, not detailed issues'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.input_file.exists():
        print(f"❌ Error: Input file '{args.input_file}' does not exist")
        return 1

    if not args.input_file.suffix.lower() == '.md':
        print(f"❌ Error: Input file must be a markdown file (.md)")
        return 1

    # Parse severity filter
    severity_levels = set(args.severity.lower().split(','))
    valid_severities = {'error', 'warning', 'info'}
    invalid_severities = severity_levels - valid_severities
    if invalid_severities:
        print(f"❌ Error: Invalid severity levels: {', '.join(invalid_severities)}")
        return 1

    try:
        # Validate document
        validator = TechnicalDocumentValidator()
        result = validator.validate_document(args.input_file)

        # Handle automatic logging
        if args.auto_log:
            import datetime
            logs_dir = args.input_file.parent / 'logs'
            logs_dir.mkdir(exist_ok=True)

            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"validation_{args.input_file.stem}_{timestamp}.json"
            auto_log_path = logs_dir / filename

            if not args.export_json:
                args.export_json = auto_log_path
            else:
                # User specified both --auto-log and --export-json
                print(f"⚠️  Warning: Both --auto-log and --export-json specified. Using --export-json path.")

        # Export to JSON if requested
        if args.export_json:
            result_dict = {
                'file_path': result.file_path,
                'overall_score': result.overall_score,
                'issues': [
                    {
                        'severity': issue.severity,
                        'category': issue.category,
                        'message': issue.message,
                        'line_number': issue.line_number,
                        'suggestion': issue.suggestion,
                        'auto_fixable': issue.auto_fixable
                    }
                    for issue in result.issues
                ],
                'metrics': result.metrics,
                'recommendations': result.recommendations
            }

            with open(args.export_json, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)
            print(f"📄 Results exported to: {args.export_json}")

        # Display results
        if args.format == 'json':
            print(json.dumps(result_dict, indent=2, ensure_ascii=False))
        else:
            print(f"\n📊 Validation Results for: {result.file_path}")
            print(f"   Overall Score: {result.overall_score:.2f}/1.00")

            if not args.quiet:
                # Filter issues by severity
                filtered_issues = [issue for issue in result.issues
                                 if issue.severity in severity_levels]

                if filtered_issues:
                    print(f"\n🔍 Issues Found ({len(filtered_issues)}):")

                    # Group by severity
                    for severity in ['error', 'warning', 'info']:
                        if severity in severity_levels:
                            severity_issues = [issue for issue in filtered_issues
                                             if issue.severity == severity]
                            if severity_issues:
                                icon = {'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}[severity]
                                print(f"\n{icon} {severity.title()}s ({len(severity_issues)}):")
                                for issue in severity_issues:
                                    line_info = f" (line {issue.line_number})" if issue.line_number else ""
                                    print(f"   • {issue.message}{line_info}")
                                    if issue.suggestion:
                                        print(f"     💡 {issue.suggestion}")
                else:
                    print("\n✅ No issues found!")

            print(f"\n📈 Metrics:")
            metrics = result.metrics
            print(f"   • Lines: {metrics['basic']['line_count']}")
            print(f"   • Words: {metrics['basic']['word_count']}")
            print(f"   • Sections: {metrics['basic']['heading_count']}")
            print(f"   • Code blocks: {metrics['basic']['code_block_count']}")
            print(f"   • Links: {metrics['basic']['link_count']}")

            print(f"\n💡 Top Recommendations:")
            for i, rec in enumerate(result.recommendations[:3], 1):
                print(f"   {i}. {rec}")

        # Return exit code based on results
        if result.overall_score < 0.7:
            return 1  # Poor quality
        elif result.overall_score < 0.85:
            return 0  # Acceptable quality
        else:
            return 0  # Good quality

    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())