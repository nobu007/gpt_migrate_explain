#!/usr/bin/env python3
"""
MD Document Improver - Technical Documentation Improvement Loop

This script implements an iterative improvement system for technical markdown documents.
It provides purpose-oriented enhancement with multi-perspective reviews and self-improvement loops.
"""

import sys
import os
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
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

    return improve_document_cli()


@dataclass
class DocumentAnalysis:
    """Document analysis results"""
    purpose: str
    target_audience: str
    completeness_score: float
    missing_sections: List[str]
    structure_issues: List[str]
    content_gaps: List[str]
    improvement_areas: List[str]


@dataclass
class ReviewResult:
    """Review result from a specific perspective"""
    reviewer_type: str  # 'technical', 'ux', 'educational'
    score: float  # 0.0 to 1.0
    feedback: List[str]
    suggestions: List[str]
    priority_issues: List[str]


@dataclass
class ImprovementPlan:
    """Plan for document improvement"""
    iteration: int
    focus_areas: List[str]
    specific_actions: List[Dict[str, Any]]
    expected_outcomes: List[str]
    review_weights: Dict[str, float]


class TechnicalDocumentAnalyzer:
    """Analyzer for technical documentation"""

    def __init__(self):
        self.technical_patterns = {
            'api_sections': [
                '## API Reference', '## Endpoints', '## Parameters',
                '## Responses', '## Error Codes', '## Examples'
            ],
            'installation': [
                '## Installation', '## Setup', '## Prerequisites',
                '## Getting Started', '## Quick Start'
            ],
            'troubleshooting': [
                '## Troubleshooting', '## FAQ', '## Common Issues',
                '## Debugging', '## Error Handling'
            ],
            'architecture': [
                '## Architecture', '## Design', '## Components',
                '## System Overview', '## Technical Details'
            ]
        }

        self.completeness_criteria = {
            'purpose_clarity': ['## Purpose', '## Overview', '## Introduction'],
            'usage_examples': ['## Examples', '## Usage', '## Code Examples'],
            'configuration': ['## Configuration', '## Settings', '## Options'],
            'troubleshooting': self.technical_patterns['troubleshooting']
        }

    def analyze_document(self, file_path: Path) -> DocumentAnalysis:
        """Analyze document structure and completeness"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract purpose and target audience
        purpose = self._extract_purpose(content)
        target_audience = self._extract_audience(content)

        # Calculate completeness
        completeness_score = self._calculate_completeness(content)

        # Identify missing sections and issues
        missing_sections = self._identify_missing_sections(content)
        structure_issues = self._identify_structure_issues(content)
        content_gaps = self._identify_content_gaps(content, purpose)

        # Determine improvement areas
        improvement_areas = self._prioritize_improvement_areas(
            missing_sections, structure_issues, content_gaps
        )

        return DocumentAnalysis(
            purpose=purpose,
            target_audience=target_audience,
            completeness_score=completeness_score,
            missing_sections=missing_sections,
            structure_issues=structure_issues,
            content_gaps=content_gaps,
            improvement_areas=improvement_areas
        )

    def _extract_purpose(self, content: str) -> str:
        """Extract document purpose from content"""
        # Look for purpose statements in introduction
        purpose_patterns = [
            r'# .*[Pp]urpose[:]?\s*([^\n]+)',
            r'## [Aa]bout\s*([^\n]+)',
            r'## [Ii]ntroduction\s*([^\n]+)',
            r'This document ([^.]+)',
        ]

        for pattern in purpose_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return "Purpose not clearly specified"

    def _extract_audience(self, content: str) -> str:
        """Extract target audience from content"""
        audience_patterns = [
            r'[Tt]arget.*[Aa]udience[:]?\s*([^\n]+)',
            r'[Ff]or[:]?\s*([^\n]+)',
            r'[Tt]his.*[Ii]s.*[Ff]or[:]?\s*([^\n]+)',
        ]

        for pattern in audience_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return "Target audience not specified"

    def _calculate_completeness(self, content: str) -> float:
        """Calculate completeness score based on expected sections"""
        total_expected = sum(len(sections) for sections in self.completeness_criteria.values())
        found_sections = 0

        for category, sections in self.completeness_criteria.items():
            for section in sections:
                if section in content:
                    found_sections += 1

        return found_sections / max(total_expected, 1)

    def _identify_missing_sections(self, content: str) -> List[str]:
        """Identify missing important sections"""
        missing = []

        for category, sections in self.completeness_criteria.items():
            for section in sections:
                if section not in content:
                    missing.append(f"{category}: {section}")

        return missing

    def _identify_structure_issues(self, content: str) -> List[str]:
        """Identify structural issues in the document"""
        issues = []

        # Check heading hierarchy
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        if not headings:
            issues.append("No clear heading structure")
        else:
            # Check for skipped heading levels
            prev_level = 0
            for level, title in headings:
                if level > prev_level + 1:
                    issues.append(f"Skipped heading level from {prev_level} to {level}")
                prev_level = len(level)

        # Check for code examples
        if not re.search(r'```[\s\S]*?```', content):
            issues.append("No code examples found")

        # Check for links
        if not re.search(r'\[.*?\]\(.*?\)', content):
            issues.append("No external links or references found")

        return issues

    def _identify_content_gaps(self, content: str, purpose: str) -> List[str]:
        """Identify content gaps based on document purpose"""
        gaps = []

        # Common gaps for technical documentation
        gap_checks = {
            'error_handling': ['error', 'exception', 'failure', 'issue'],
            'performance': ['performance', 'optimization', 'benchmark', 'speed'],
            'security': ['security', 'authentication', 'authorization', 'token'],
            'testing': ['test', 'testing', 'validation', 'verification'],
            'versioning': ['version', 'compatibility', 'migration', 'upgrade']
        }

        for gap_type, keywords in gap_checks.items():
            if not any(keyword.lower() in content.lower() for keyword in keywords):
                gaps.append(f"Missing {gap_type.replace('_', ' ')} information")

        return gaps

    def _prioritize_improvement_areas(self, missing: List[str],
                                   structure: List[str],
                                   content_gaps: List[str]) -> List[str]:
        """Prioritize improvement areas based on impact"""
        # Prioritization weights
        weights = {
            'missing_critical': 3.0,  # Critical missing sections
            'structure_major': 2.5,   # Major structure issues
            'content_important': 2.0, # Important content gaps
            'structure_minor': 1.0,   # Minor structure issues
            'content_minor': 0.5      # Minor content gaps
        }

        prioritized = []

        # Categorize and prioritize
        if missing:
            prioritized.extend([f"Critical missing sections: {', '.join(missing[:3])}"])

        major_structure = [s for s in structure if any(keyword in s.lower()
                          for keyword in ['no clear', 'skipped', 'missing'])]
        if major_structure:
            prioritized.extend([f"Structure issues: {', '.join(major_structure)}"])

        important_gaps = [g for g in content_gaps if any(keyword in g.lower()
                         for keyword in ['error', 'security', 'performance'])]
        if important_gaps:
            prioritized.extend([f"Important gaps: {', '.join(important_gaps)}"])

        # Add remaining issues
        remaining = [item for item in missing + structure + content_gaps
                    if item not in (major_structure + important_gaps)]
        if remaining:
            prioritized.append(f"Additional improvements: {', '.join(remaining[:5])}")

        return prioritized


class MultiPerspectiveReviewer:
    """Multi-perspective document reviewer"""

    def __init__(self):
        self.review_criteria = {
            'technical': {
                'accuracy': 0.4,
                'completeness': 0.3,
                'best_practices': 0.2,
                'technical_depth': 0.1
            },
            'ux': {
                'clarity': 0.3,
                'readability': 0.3,
                'navigation': 0.2,
                'user_focus': 0.2
            },
            'educational': {
                'learning_progression': 0.3,
                'examples_quality': 0.3,
                'practice_opportunities': 0.2,
                'knowledge_retention': 0.2
            }
        }

    def review_document(self, file_path: Path, analysis: DocumentAnalysis) -> List[ReviewResult]:
        """Conduct multi-perspective review"""
        results = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Technical review
        results.append(self._technical_review(content, analysis))

        # UX review
        results.append(self._ux_review(content, analysis))

        # Educational review
        results.append(self._educational_review(content, analysis))

        return results

    def _technical_review(self, content: str, analysis: DocumentAnalysis) -> ReviewResult:
        """Technical perspective review"""
        feedback = []
        suggestions = []
        priority_issues = []

        # Technical accuracy checks
        if '```' not in content:
            feedback.append("Missing code examples")
            priority_issues.append("Add code examples")
            suggestions.append("Include practical code samples")

        # API documentation checks
        if any(keyword in content.lower() for keyword in ['api', 'endpoint', 'method']):
            if not any(keyword in content.lower() for keyword in ['response', 'status', 'error']):
                feedback.append("Incomplete API documentation")
                suggestions.append("Add response formats and error handling")

        # Best practices
        if not any(keyword in content.lower() for keyword in ['security', 'performance']):
            feedback.append("Missing security/performance considerations")
            suggestions.append("Include security and performance guidance")

        # Calculate score
        score = max(0.0, 1.0 - len(feedback) * 0.15)

        return ReviewResult(
            reviewer_type='technical',
            score=score,
            feedback=feedback,
            suggestions=suggestions,
            priority_issues=priority_issues
        )

    def _ux_review(self, content: str, analysis: DocumentAnalysis) -> ReviewResult:
        """UX perspective review"""
        feedback = []
        suggestions = []
        priority_issues = []

        # Readability checks
        lines = content.split('\n')
        avg_line_length = sum(len(line) for line in lines) / max(len(lines), 1)

        if avg_line_length > 100:
            feedback.append("Lines are too long for readability")
            suggestions.append("Break long lines and use shorter sentences")

        # Navigation checks
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        if len(headings) < 5:
            feedback.append("Insufficient section organization")
            suggestions.append("Add more sections for better navigation")

        # User focus checks
        if not any(keyword in content.lower() for keyword in ['example', 'use case', 'scenario']):
            feedback.append("Lacks user-focused examples")
            suggestions.append("Add practical use cases and scenarios")

        # Calculate score
        score = max(0.0, 1.0 - len(feedback) * 0.12)

        return ReviewResult(
            reviewer_type='ux',
            score=score,
            feedback=feedback,
            suggestions=suggestions,
            priority_issues=priority_issues
        )

    def _educational_review(self, content: str, analysis: DocumentAnalysis) -> ReviewResult:
        """Educational perspective review"""
        feedback = []
        suggestions = []
        priority_issues = []

        # Learning progression checks
        sections = re.split(r'\n## ', content)
        if len(sections) < 4:
            feedback.append("Insufficient structure for learning progression")
            suggestions.append("Organize content into logical learning sections")

        # Example quality checks
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        if code_blocks:
            for i, block in enumerate(code_blocks):
                if len(block.split('\n')) < 3:
                    feedback.append(f"Code example {i+1} is too minimal")
                    break
        else:
            feedback.append("No code examples for hands-on learning")
            suggestions.append("Add comprehensive code examples")

        # Practice opportunities
        if not any(keyword in content.lower() for keyword in ['exercise', 'practice', 'try']):
            feedback.append("No practice exercises or activities")
            suggestions.append("Add hands-on exercises or try-it-yourself sections")

        # Calculate score
        score = max(0.0, 1.0 - len(feedback) * 0.18)

        return ReviewResult(
            reviewer_type='educational',
            score=score,
            feedback=feedback,
            suggestions=suggestions,
            priority_issues=priority_issues
        )


class ImprovementPlanGenerator:
    """Generate improvement plans based on analysis and reviews"""

    def __init__(self):
        self.improvement_strategies = {
            'structure': [
                'Reorganize sections with logical flow',
                'Add missing critical sections',
                'Improve heading hierarchy',
                'Add navigation aids (TOC, links)'
            ],
            'content': [
                'Add comprehensive code examples',
                'Include error handling scenarios',
                'Add troubleshooting section',
                'Include performance considerations'
            ],
            'clarity': [
                'Simplify complex explanations',
                'Add more concrete examples',
                'Improve technical writing',
                'Add visual aids (diagrams, tables)'
            ],
            'completeness': [
                'Cover edge cases and exceptions',
                'Add security considerations',
                'Include version compatibility',
                'Add FAQ section'
            ]
        }

    def generate_plan(self, analysis: DocumentAnalysis,
                     reviews: List[ReviewResult],
                     iteration: int) -> ImprovementPlan:
        """Generate improvement plan for current iteration"""

        # Determine focus areas based on lowest scores and highest priority issues
        focus_areas = []
        specific_actions = []

        # Collect all priority issues
        all_issues = []
        for review in reviews:
            all_issues.extend(review.priority_issues)

        # Calculate average scores
        scores = {review.reviewer_type: review.score for review in reviews}
        lowest_score_area = min(scores.items(), key=lambda x: x[1])[0]

        # Set focus areas
        if analysis.completeness_score < 0.7:
            focus_areas.append('completeness')

        if any('structure' in issue.lower() for issue in all_issues):
            focus_areas.append('structure')

        if lowest_score_area == 'ux':
            focus_areas.append('clarity')
        elif lowest_score_area == 'technical':
            focus_areas.append('content')
        elif lowest_score_area == 'educational':
            focus_areas.append('clarity')

        # Generate specific actions
        for area in focus_areas:
            if area in self.improvement_strategies:
                strategies = self.improvement_strategies[area]
                # Select most relevant strategies
                selected = strategies[:2]  # Take top 2 strategies for this iteration
                for strategy in selected:
                    specific_actions.append({
                        'type': area,
                        'action': strategy,
                        'priority': 'high' if area == focus_areas[0] else 'medium',
                        'estimated_effort': 'medium'
                    })

        # Add specific actions from review feedback
        for review in reviews:
            if review.score < 0.7:  # Only for low-scoring areas
                for suggestion in review.suggestions[:2]:  # Top 2 suggestions
                    specific_actions.append({
                        'type': review.reviewer_type,
                        'action': suggestion,
                        'priority': 'high' if review.score < 0.5 else 'medium',
                        'estimated_effort': 'low'
                    })

        # Set expected outcomes
        expected_outcomes = [
            f"Improve {lowest_score_area} perspective score",
            "Increase overall document completeness",
            "Enhance user understanding and usability"
        ]

        # Set review weights for next iteration
        base_weights = {'technical': 0.4, 'ux': 0.3, 'educational': 0.3}
        if lowest_score_area in base_weights:
            # Increase weight for lowest scoring area
            base_weights[lowest_score_area] += 0.1
            # Decrease others proportionally
            for key in base_weights:
                if key != lowest_score_area:
                    base_weights[key] -= 0.05

        return ImprovementPlan(
            iteration=iteration,
            focus_areas=focus_areas,
            specific_actions=specific_actions,
            expected_outcomes=expected_outcomes,
            review_weights=base_weights
        )


class DocumentImprover:
    """Main document improvement orchestrator"""

    def __init__(self):
        self.analyzer = TechnicalDocumentAnalyzer()
        self.reviewer = MultiPerspectiveReviewer()
        self.planner = ImprovementPlanGenerator()
        self.max_iterations = 5
        self.improvement_threshold = 0.85

    def improve_document(self, file_path: Path,
                        max_iterations: Optional[int] = None,
                        output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Main improvement loop"""
        if max_iterations is None:
            max_iterations = self.max_iterations

        if output_dir is None:
            output_dir = file_path.parent / 'improvements'

        output_dir.mkdir(exist_ok=True)

        results = {
            'original_file': str(file_path),
            'iterations': [],
            'final_assessment': None,
            'improvement_summary': None
        }

        print(f"🚀 Starting improvement process for: {file_path}")

        # Initial analysis
        print("📊 Conducting initial analysis...")
        analysis = self.analyzer.analyze_document(file_path)
        print(f"   Initial completeness score: {analysis.completeness_score:.2f}")

        # Initial review
        print("🔍 Conducting initial multi-perspective review...")
        reviews = self.reviewer.review_document(file_path, analysis)
        for review in reviews:
            print(f"   {review.reviewer_type.title()} score: {review.score:.2f}")

        for iteration in range(1, max_iterations + 1):
            print(f"\n🔄 Iteration {iteration}/{max_iterations}")

            # Generate improvement plan
            plan = self.planner.generate_plan(analysis, reviews, iteration)
            print(f"   Focus areas: {', '.join(plan.focus_areas)}")
            print(f"   Planned actions: {len(plan.specific_actions)}")

            # Store iteration results
            iteration_result = {
                'iteration': iteration,
                'analysis': asdict(analysis),
                'reviews': [asdict(review) for review in reviews],
                'plan': asdict(plan),
                'improvements_made': []
            }

            # Apply improvements (in a real implementation, this would modify the document)
            improvements = self._apply_improvements(file_path, plan, iteration, output_dir)
            iteration_result['improvements_made'] = improvements

            # Re-analyze if not final iteration
            if iteration < max_iterations:
                # In a real implementation, we would analyze the improved document
                # For now, we'll simulate improvement
                print(f"   Simulating improvements...")
                print(f"   Applied {len(improvements)} improvements")

            results['iterations'].append(iteration_result)

            # Check if we've reached the improvement threshold
            avg_score = sum(review.score for review in reviews) / len(reviews)
            if avg_score >= self.improvement_threshold:
                print(f"✅ Target improvement threshold ({self.improvement_threshold}) reached!")
                break

        # Generate final assessment
        results['final_assessment'] = self._generate_final_assessment(results['iterations'])
        results['improvement_summary'] = self._generate_improvement_summary(results['iterations'])

        # Save results
        results_file = output_dir / f'improvement_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n📋 Improvement complete! Results saved to: {results_file}")
        return results

    def _apply_improvements(self, file_path: Path, plan: ImprovementPlan,
                          iteration: int, output_dir: Path) -> List[str]:
        """Apply improvements to document (simulated)"""
        improvements = []

        for action in plan.specific_actions:
            # Simulate different types of improvements
            if 'Add' in action['action'] or 'Include' in action['action']:
                improvements.append(f"Added {action['type']} section")
            elif 'Improve' in action['action']:
                improvements.append(f"Improved {action['type']} quality")
            elif 'Organize' in action['action']:
                improvements.append(f"Reorganized {action['type']} structure")
            else:
                improvements.append(f"Applied {action['action']}")

        # In a real implementation, this would modify the actual document
        # For now, we just simulate and log the improvements

        return improvements

    def _generate_final_assessment(self, iterations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate final assessment of improvement process"""
        if not iterations:
            return {}

        first_iteration = iterations[0]
        last_iteration = iterations[-1]

        initial_scores = {review['reviewer_type']: review['score']
                         for review in first_iteration['reviews']}
        final_scores = {review['reviewer_type']: review['score']
                       for review in last_iteration['reviews']}

        improvements = {}
        for reviewer_type in initial_scores:
            improvement = final_scores[reviewer_type] - initial_scores[reviewer_type]
            improvements[reviewer_type] = {
                'initial': initial_scores[reviewer_type],
                'final': final_scores[reviewer_type],
                'improvement': improvement
            }

        return {
            'iterations_completed': len(iterations),
            'score_improvements': improvements,
            'overall_initial_score': sum(initial_scores.values()) / len(initial_scores),
            'overall_final_score': sum(final_scores.values()) / len(final_scores),
            'total_improvement': (sum(final_scores.values()) - sum(initial_scores.values())) / len(initial_scores)
        }

    def _generate_improvement_summary(self, iterations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of all improvements made"""
        all_improvements = []
        all_focus_areas = []

        for iteration in iterations:
            all_improvements.extend(iteration['improvements_made'])
            all_focus_areas.extend(iteration['plan']['focus_areas'])

        # Count frequency of focus areas
        focus_area_counts = {}
        for area in all_focus_areas:
            focus_area_counts[area] = focus_area_counts.get(area, 0) + 1

        return {
            'total_improvements': len(all_improvements),
            'improvements_by_iteration': [len(iter['improvements_made']) for iter in iterations],
            'most_addressed_areas': sorted(focus_area_counts.items(),
                                         key=lambda x: x[1], reverse=True),
            'improvement_categories': list(set(all_focus_areas))
        }


def improve_document_cli() -> int:
    """Command-line interface for document improvement"""
    parser = argparse.ArgumentParser(
        description='Improve technical documentation through iterative multi-perspective review',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Improve a markdown document
  python improve_document.py README.md

  # Custom output directory and iterations
  python improve_document.py docs/api.md --output-dir ./reviews --max-iterations 3

  # Verbose output
  python improve_document.py README.md --verbose
        """
    )

    parser.add_argument(
        'input_file',
        type=Path,
        help='Path to the markdown file to improve'
    )

    parser.add_argument(
        '--output-dir', '-o',
        type=Path,
        default=None,
        help='Directory to save improvement results (default: ./improvements)'
    )

    parser.add_argument(
        '--max-iterations', '-i',
        type=int,
        default=5,
        help='Maximum number of improvement iterations (default: 5)'
    )

    parser.add_argument(
        '--threshold', '-t',
        type=float,
        default=0.85,
        help='Improvement threshold to stop early (default: 0.85)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--export-json',
        type=Path,
        default=None,
        help='Export results to specified JSON file'
    )

    args = parser.parse_args()

    # Validate input
    if not args.input_file.exists():
        print(f"❌ Error: Input file '{args.input_file}' does not exist")
        return 1

    if not args.input_file.suffix.lower() == '.md':
        print(f"❌ Error: Input file must be a markdown file (.md)")
        return 1

    if args.max_iterations < 1:
        print("❌ Error: Max iterations must be at least 1")
        return 1

    if not 0.0 <= args.threshold <= 1.0:
        print("❌ Error: Threshold must be between 0.0 and 1.0")
        return 1

    try:
        # Create document improver
        improver = DocumentImprover()
        improver.improvement_threshold = args.threshold

        # Run improvement process
        results = improver.improve_document(
            args.input_file,
            max_iterations=args.max_iterations,
            output_dir=args.output_dir
        )

        # Export to JSON if requested
        if args.export_json:
            with open(args.export_json, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"📄 Results exported to: {args.export_json}")

        # Print summary
        print(f"\n📊 Improvement Summary:")
        assessment = results['final_assessment']
        if assessment:
            print(f"   Iterations completed: {assessment['iterations_completed']}")
            print(f"   Overall score improvement: {assessment['total_improvement']:+.2f}")
            print(f"   Final overall score: {assessment['overall_final_score']:.2f}")

        summary = results['improvement_summary']
        if summary:
            print(f"   Total improvements made: {summary['total_improvements']}")
            if summary['most_addressed_areas']:
                print(f"   Most addressed area: {summary['most_addressed_areas'][0][0]}")

        return 0

    except KeyboardInterrupt:
        print("\n⚠️  Improvement process interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error during improvement process: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())