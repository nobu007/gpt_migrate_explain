#!/usr/bin/env python3
"""Issue content analyzer and improver with real Claude API integration"""

import json
import os
import re
from dataclasses import dataclass
from enum import Enum

import anthropic
from anthropic import Anthropic


class IssueType(Enum):
    """Issue type classification"""

    BUG = "bug"
    FEATURE = "feature"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    TEST = "test"
    CHORE = "chore"
    QUESTION = "question"
    UNKNOWN = "unknown"


class IssueSeverity(Enum):
    """Issue severity classification"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class IssueAnalysis:
    """Analysis result for an issue"""

    type: IssueType
    severity: IssueSeverity
    components: list[str]
    missing_info: list[str]
    suggested_title: str
    suggested_body: str
    suggested_labels: list[str]
    confidence_score: float


class IssueAnalyzer:
    """Analyzes and improves GitHub issues using Claude API"""

    def __init__(self, fallback_to_keywords: bool = True):
        """
        Initialize the analyzer with Claude API client
        Args:
            fallback_to_keywords: If True, use keyword-based analysis when Claude API fails
        """
        self.fallback_to_keywords = fallback_to_keywords
        self.claude_client = None
        self.use_claude = False

        # Initialize Claude API client if available
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            try:
                self.claude_client = Anthropic(api_key=api_key)
                # Test the connection with a minimal API call to validate the key
                self.claude_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1,
                    messages=[{"role": "user", "content": "test"}],
                    temperature=0,
                )
                self.use_claude = True
            except anthropic.AuthenticationError as e:
                if not fallback_to_keywords:
                    msg = f"Invalid ANTHROPIC_API_KEY: {e}"
                    raise ValueError(msg)
                print(
                    f"Warning: Invalid ANTHROPIC_API_KEY, using keyword-based analysis: {e}"
                )
            except anthropic.APIConnectionError as e:
                if not fallback_to_keywords:
                    msg = f"Claude API connection failed: {e}"
                    raise ValueError(msg)
                print(
                    f"Warning: Claude API connection failed, using keyword-based analysis: {e}"
                )
            except Exception as e:
                print(f"Warning: Failed to initialize Claude API client: {e}")
                if not fallback_to_keywords:
                    msg = "Claude API initialization failed and fallback is disabled"
                    raise ValueError(msg)
        else:
            if not fallback_to_keywords:
                msg = "ANTHROPIC_API_KEY environment variable is required"
                raise ValueError(msg)
            print("Warning: ANTHROPIC_API_KEY not found, using keyword-based analysis")

        # Keep keyword-based analysis as fallback
        self.type_keywords = {
            IssueType.BUG: [
                "bug",
                "error",
                "fix",
                "broken",
                "crash",
                "issue",
                "problem",
                "not working",
            ],
            IssueType.FEATURE: [
                "feature",
                "add",
                "implement",
                "new",
                "support",
                "enhancement",
            ],
            IssueType.REFACTOR: [
                "refactor",
                "cleanup",
                "improve",
                "optimize",
                "performance",
            ],
            IssueType.DOCUMENTATION: [
                "docs",
                "documentation",
                "readme",
                "guide",
                "tutorial",
            ],
            IssueType.TEST: ["test", "testing", "coverage", "spec", "unit test"],
            IssueType.CHORE: ["chore", "maintenance", "dependency", "update"],
            IssueType.QUESTION: ["question", "how to", "help", "confused", "clarify"],
        }

        self.severity_keywords = {
            IssueSeverity.CRITICAL: [
                "critical",
                "urgent",
                "blocker",
                "production",
                "security",
            ],
            IssueSeverity.HIGH: ["high priority", "important", "major", "breaking"],
            IssueSeverity.MEDIUM: ["medium", "normal", "moderate"],
            IssueSeverity.LOW: ["low", "minor", "nice to have", "enhancement"],
        }

    def analyze_issue(self, title: str, body: str) -> IssueAnalysis:
        """Analyze issue content and generate improvements"""
        # Try Claude API first if available
        if self.use_claude and self.claude_client:
            try:
                return self._analyze_with_claude(title, body)
            except Exception as e:
                print(f"Warning: Claude API analysis failed: {e}")
                if not self.fallback_to_keywords:
                    msg = "Claude API analysis failed and fallback is disabled"
                    raise ValueError(msg)

        # Fallback to keyword-based analysis
        return self._analyze_with_keywords(title, body)

    def _sanitize_input(self, text: str) -> str:
        """Sanitize user input for Claude API"""
        if not text:
            return ""

        # Limit length to prevent token abuse
        if len(text) > 50000:
            text = text[:50000] + "... [truncated]"

        # Remove potentially dangerous content patterns
        # Add any specific sanitization needed for your use case
        return text.strip()

    def _validate_output(self, content: str, max_length: int = 10000) -> str:
        """Validate and sanitize output content to prevent duplication issues"""
        if not content:
            return content

        # Check for excessive length that indicates duplication
        if len(content) > max_length:
            print(
                f"Warning: Content length ({len(content)}) exceeds maximum ({max_length}), truncating..."
            )
            content = (
                content[:max_length] + "\n\n[Content truncated due to excessive length]"
            )

        # Detect potential duplicate patterns
        lines = content.split("\n")
        duplicate_threshold = 3  # Allow up to 3 similar lines
        seen_lines = {}

        for i, line in enumerate(lines):
            line_stripped = line.strip().lower()
            if not line_stripped or line_stripped.startswith("#"):
                continue  # Skip empty lines and headers

            if line_stripped in seen_lines:
                seen_lines[line_stripped] += 1
                if seen_lines[line_stripped] > duplicate_threshold:
                    print(
                        f"Warning: Detected duplicate line repeated {seen_lines[line_stripped]} times: '{line[:50]}...'"
                    )
                    # Remove subsequent duplicates
                    lines[i] = ""
            else:
                seen_lines[line_stripped] = 1

        # Rebuild content with duplicates removed
        cleaned_content = "\n".join(line for line in lines if line)

        # Check for repeated blocks (more sophisticated duplication detection)
        blocks = [
            block.strip() for block in cleaned_content.split("\n\n") if block.strip()
        ]
        if len(blocks) > 10:  # If there are many blocks, check for duplicates
            seen_blocks = {}
            final_blocks = []

            for block in blocks:
                block_key = block[:100].lower()  # First 100 chars as key
                if block_key in seen_blocks:
                    print(
                        f"Warning: Detected duplicate block, skipping: '{block[:50]}...'"
                    )
                    continue
                seen_blocks[block_key] = True
                final_blocks.append(block)

            cleaned_content = "\n\n".join(final_blocks)

        return cleaned_content

    def _analyze_with_claude(self, title: str, body: str) -> IssueAnalysis:
        """Analyze issue using Claude API"""
        # Sanitize inputs
        title = self._sanitize_input(title)
        body = self._sanitize_input(body)

        prompt = f"""You are an expert GitHub issue analyzer. Analyze the following GitHub issue and provide detailed analysis.

**Issue Title:**
{title}

**Issue Body:**
{body if body else "(No description provided)"}

Please analyze this issue and provide the following in JSON format:

1. **type**: One of: bug, feature, refactor, documentation, test, chore, question, unknown
2. **severity**: One of: critical, high, medium, low, unknown
3. **components**: List of technical components mentioned (e.g., api, frontend, backend, database)
4. **missing_info**: List of important information missing from the issue
5. **suggested_title**: Improved title following conventional commit format
6. **suggested_body**: Improved body with proper structure and sections
7. **suggested_labels**: List of appropriate labels for the issue
8. **confidence_score**: Your confidence in this analysis (0.0 to 1.0)

**Analysis Guidelines:**
- For bug reports: ensure steps to reproduce, expected/actual behavior, and environment info
- For feature requests: include use case, acceptance criteria, and proposed solution
- For documentation: identify what docs need updating and target audience
- Titles should start with type prefixes: "Fix:", "Feat:", "Docs:", "Refactor:", "Test:", "Chore:"
- Provide structured body with appropriate sections
- Consider the project context and best practices

Respond with valid JSON only:
{{
  "type": "...",
  "severity": "...",
  "components": [...],
  "missing_info": [...],
  "suggested_title": "...",
  "suggested_body": "...",
  "suggested_labels": [...],
  "confidence_score": 0.0
}}"""

        try:
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            response_text = response.content[0].text.strip()

            # Extract JSON from response
            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if json_match:
                json_str = json_match.group()
                analysis_data = json.loads(json_str)
            else:
                # If no JSON found, try to parse the entire response
                analysis_data = json.loads(response_text)

            # Convert to our internal types and validate output
            suggested_body = self._validate_output(
                analysis_data.get("suggested_body", body or "")
            )
            suggested_title = analysis_data.get("suggested_title", title)

            # Validate title length too
            if len(suggested_title) > 200:
                print(
                    f"Warning: Title length ({len(suggested_title)}) is excessive, truncating..."
                )
                suggested_title = suggested_title[:200] + "..."

            return IssueAnalysis(
                type=self._parse_issue_type(analysis_data.get("type", "unknown")),
                severity=self._parse_severity(analysis_data.get("severity", "unknown")),
                components=analysis_data.get("components", []),
                missing_info=analysis_data.get("missing_info", []),
                suggested_title=suggested_title,
                suggested_body=suggested_body,
                suggested_labels=analysis_data.get("suggested_labels", []),
                confidence_score=float(analysis_data.get("confidence_score", 0.5)),
            )

        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse Claude response as JSON: {e}")
            msg = f"Invalid JSON response from Claude API: {response_text}"
            raise ValueError(msg)
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            raise

    def _analyze_with_keywords(self, title: str, body: str) -> IssueAnalysis:
        """Fallback keyword-based analysis"""
        text = f"{title} {body}".lower()

        # Classify issue type
        issue_type = self._classify_issue_type(text)

        # Classify severity
        severity = self._classify_severity(text)

        # Extract components
        components = self._extract_components(text)

        # Identify missing information
        missing_info = self._identify_missing_info(title, body, issue_type)

        # Generate improvements
        suggested_title = self._suggest_title(title, issue_type)
        suggested_body = self._suggest_body(body, issue_type, missing_info)
        suggested_labels = self._suggest_labels(issue_type, severity, components)

        # Validate outputs to prevent duplication issues
        suggested_body = self._validate_output(suggested_body)

        # Validate title length too
        if len(suggested_title) > 200:
            print(
                f"Warning: Title length ({len(suggested_title)}) is excessive, truncating..."
            )
            suggested_title = suggested_title[:200] + "..."

        # Calculate confidence
        confidence_score = self._calculate_confidence(title, body, issue_type)

        return IssueAnalysis(
            type=issue_type,
            severity=severity,
            components=components,
            missing_info=missing_info,
            suggested_title=suggested_title,
            suggested_body=suggested_body,
            suggested_labels=suggested_labels,
            confidence_score=confidence_score,
        )

    def _parse_issue_type(self, type_str: str) -> IssueType:
        """Parse string to IssueType enum"""
        type_mapping = {
            "bug": IssueType.BUG,
            "feature": IssueType.FEATURE,
            "refactor": IssueType.REFACTOR,
            "documentation": IssueType.DOCUMENTATION,
            "docs": IssueType.DOCUMENTATION,
            "test": IssueType.TEST,
            "chore": IssueType.CHORE,
            "question": IssueType.QUESTION,
            "unknown": IssueType.UNKNOWN,
        }
        return type_mapping.get(type_str.lower(), IssueType.UNKNOWN)

    def _parse_severity(self, severity_str: str) -> IssueSeverity:
        """Parse string to IssueSeverity enum"""
        severity_mapping = {
            "critical": IssueSeverity.CRITICAL,
            "high": IssueSeverity.HIGH,
            "medium": IssueSeverity.MEDIUM,
            "low": IssueSeverity.LOW,
            "unknown": IssueSeverity.UNKNOWN,
        }
        return severity_mapping.get(severity_str.lower(), IssueSeverity.UNKNOWN)

    def _classify_issue_type(self, text: str) -> IssueType:
        """Classify issue type based on keywords"""
        scores = {}
        for issue_type, keywords in self.type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[issue_type] = score

        if max(scores.values()) == 0:
            return IssueType.UNKNOWN

        return max(scores, key=scores.get)

    def _classify_severity(self, text: str) -> IssueSeverity:
        """Classify issue severity based on keywords"""
        scores = {}
        for severity, keywords in self.severity_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[severity] = score

        if max(scores.values()) == 0:
            return IssueSeverity.UNKNOWN

        return max(scores, key=scores.get)

    def _extract_components(self, text: str) -> list[str]:
        """Extract mentioned components or areas"""
        # Common component patterns
        component_patterns = [
            r"\b(api|frontend|backend|ui|ux|database|db|server|client)\b",
            r"\b(auth|authentication|authorization|login|signup)\b",
            r"\b(component|service|controller|model|view)\b",
            r"\b(middleware|plugin|extension|integration)\b",
        ]

        components = set()
        for pattern in component_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            components.update(matches)

        return list(components)

    def _identify_missing_info(
        self, title: str, body: str, issue_type: IssueType
    ) -> list[str]:
        """Identify missing information based on issue type"""
        missing = []
        body_lower = body.lower()

        # Check for detailed description first
        if len(body.strip()) < 50:
            missing.append("Detailed description")
            return missing  # If description is too short, other checks may not be meaningful

        # Only do detailed missing info analysis for BUG and FEATURE types
        # For other types (refactor, documentation, etc.), be more conservative
        if issue_type == IssueType.BUG:
            # Look for various ways steps to reproduce might be mentioned
            steps_patterns = [
                "steps to reproduce",
                "reproduction steps",
                "how to reproduce",
                "steps to follow",
            ]
            if not any(pattern in body_lower for pattern in steps_patterns):
                missing.append("Steps to reproduce")

            # Look for expected/actual behavior patterns
            expected_patterns = [
                "expected behavior",
                "expected result",
                "what should happen",
            ]
            actual_patterns = [
                "actual behavior",
                "actual result",
                "what actually happens",
                "current behavior",
            ]

            if not any(pattern in body_lower for pattern in expected_patterns):
                missing.append("Expected behavior")
            if not any(pattern in body_lower for pattern in actual_patterns):
                missing.append("Actual behavior")

            # Screenshots or examples
            if (
                not re.search(r"https?://", body)
                and "screenshot" not in body_lower
                and "example" not in body_lower
            ):
                missing.append("Screenshots or examples")

        elif issue_type == IssueType.FEATURE:
            # Look for acceptance criteria patterns
            criteria_patterns = [
                "acceptance criteria",
                "requirements",
                "definition of done",
            ]
            if not any(pattern in body_lower for pattern in criteria_patterns):
                missing.append("Acceptance criteria")

            # Look for use case patterns
            usecase_patterns = ["use case", "user story", "scenario", "goal"]
            if not any(pattern in body_lower for pattern in usecase_patterns):
                missing.append("Use case description")

        # For other issue types, be very conservative about what's missing
        # Most refactor/docs/test issues can work with the existing content structure

        return missing

    def _suggest_title(self, original_title: str, issue_type: IssueType) -> str:
        """Suggest improved title"""
        # Add type prefix if missing
        type_prefixes = {
            IssueType.BUG: "Fix:",
            IssueType.FEATURE: "Feat:",
            IssueType.REFACTOR: "Refactor:",
            IssueType.DOCUMENTATION: "Docs:",
            IssueType.TEST: "Test:",
            IssueType.CHORE: "Chore:",
            IssueType.QUESTION: "Question:",
        }

        prefix = type_prefixes.get(issue_type, "")
        title = original_title.strip()

        # Remove existing prefixes
        for p in type_prefixes.values():
            if title.lower().startswith(p.lower()):
                title = title[len(p) :].strip()

        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:] if len(title) > 1 else title.upper()

        return f"{prefix} {title}".strip() if prefix else title

    def _suggest_body(
        self, original_body: str, issue_type: IssueType, missing_info: list[str]
    ) -> str:
        """Suggest improved body structure"""
        if not original_body.strip():
            return self._generate_template_body(issue_type, missing_info)

        # If body exists but is missing sections, add them
        improved_body = original_body.strip()
        body_lower = improved_body.lower()

        # Add missing sections only if they don't already exist
        templates = self._get_section_templates(issue_type)
        for section in missing_info:
            if section in templates:
                # Check if section already exists (case-insensitive)
                section_exists = False
                section_variants = [
                    section.lower(),
                    section.replace(" ", "").lower(),
                    section.replace(" ", "-").lower(),
                ]

                for variant in section_variants:
                    if variant in body_lower:
                        section_exists = True
                        break

                # Also check for common section header patterns
                if not section_exists:
                    common_patterns = [
                        f"### {section.lower()}",
                        f"## {section.lower()}",
                        f"**{section.lower()}**",
                        section.lower(),
                    ]
                    for pattern in common_patterns:
                        if pattern in body_lower:
                            section_exists = True
                            break

                if not section_exists:
                    improved_body += f"\n\n{templates[section]}"
                    body_lower = improved_body.lower()  # Update for next iteration

        return improved_body

    def _generate_template_body(
        self, issue_type: IssueType, missing_info: list[str]
    ) -> str:
        """Generate complete body template"""
        templates = self._get_section_templates(issue_type)

        body_parts = ["## Description"]

        if issue_type == IssueType.BUG:
            body_parts.extend(
                [
                    templates.get("Description", ""),
                    "## Steps to Reproduce",
                    "1. ",
                    "2. ",
                    "3. ",
                    "## Expected Behavior",
                    "",
                    "## Actual Behavior",
                    "",
                    "## Environment",
                    "- OS: ",
                    "- Browser: ",
                    "- Version: ",
                ]
            )
        elif issue_type == IssueType.FEATURE:
            body_parts.extend(
                [
                    templates.get("Description", ""),
                    "## Use Case",
                    "",
                    "## Acceptance Criteria",
                    "- [ ] ",
                    "- [ ] ",
                    "- [ ] ",
                    "## Proposed Solution",
                    "",
                ]
            )
        else:
            body_parts.extend([templates.get("Description", ""), "## Details", ""])

        return "\n".join(body_parts)

    def _get_section_templates(self, issue_type: IssueType) -> dict[str, str]:
        """Get template sections for issue type"""
        templates = {
            "Steps to reproduce": "### Steps to Reproduce\n1. \n2. \n3. ",
            "Expected behavior": "### Expected Behavior\n*Describe what should happen*",
            "Actual behavior": "### Actual Behavior\n*Describe what actually happens*",
            "Acceptance criteria": "### Acceptance Criteria\n- [ ] \n- [ ] \n- [ ] ",
            "Use case description": "### Use Case\n*Describe the user story or use case*",
            "Description": "### Description\n*Provide a clear and concise description*",
            "Detailed description": "### Description\n*Provide a detailed description of the issue or feature request*\n\n### Context\n*Additional context or information that might be helpful*",
            "Screenshots or examples": "### Screenshots or Examples\n*Add screenshots, code examples, or links to help illustrate the issue*",
        }

        if issue_type == IssueType.BUG:
            return {
                k: v
                for k, v in templates.items()
                if k
                in [
                    "Description",
                    "Steps to reproduce",
                    "Expected behavior",
                    "Actual behavior",
                ]
            }
        if issue_type == IssueType.FEATURE:
            return {
                k: v
                for k, v in templates.items()
                if k in ["Description", "Use case description", "Acceptance criteria"]
            }

        return {"Description": templates["Description"]}

    def _suggest_labels(
        self, issue_type: IssueType, severity: IssueSeverity, components: list[str]
    ) -> list[str]:
        """Suggest appropriate labels"""
        labels = []

        # Type label
        if issue_type != IssueType.UNKNOWN:
            labels.append(issue_type.value)

        # Severity label
        if severity != IssueSeverity.UNKNOWN:
            labels.append(f"priority: {severity.value}")

        # Component labels
        for component in components[:3]:  # Limit to avoid too many labels
            labels.append(f"area: {component}")

        return labels

    def _calculate_confidence(
        self, title: str, body: str, issue_type: IssueType
    ) -> float:
        """Calculate confidence score for the analysis"""
        score = 0.0

        # Title quality
        if len(title) >= 10 and len(title) <= 100:
            score += 0.2
        if any(
            keyword in title.lower()
            for keywords in self.type_keywords.values()
            for keyword in keywords
        ):
            score += 0.2

        # Body quality
        if len(body) >= 50:
            score += 0.2
        if "##" in body:  # Has structure
            score += 0.2

        # Type confidence
        if issue_type != IssueType.UNKNOWN:
            score += 0.2

        return min(score, 1.0)


if __name__ == "__main__":
    # CLI interface for testing
    import argparse

    parser = argparse.ArgumentParser(description="Issue Analyzer")
    parser.add_argument("--title", required=True, help="Issue title")
    parser.add_argument("--body", required=True, help="Issue body")
    parser.add_argument(
        "--output", choices=["json", "text"], default="text", help="Output format"
    )

    args = parser.parse_args()

    analyzer = IssueAnalyzer()
    analysis = analyzer.analyze_issue(args.title, args.body)

    if args.output == "json":
        print(
            json.dumps(
                {
                    "type": analysis.type.value,
                    "severity": analysis.severity.value,
                    "components": analysis.components,
                    "missing_info": analysis.missing_info,
                    "suggested_title": analysis.suggested_title,
                    "suggested_body": analysis.suggested_body,
                    "suggested_labels": analysis.suggested_labels,
                    "confidence_score": analysis.confidence_score,
                },
                indent=2,
            )
        )
    else:
        print(f"Issue Analysis (Confidence: {analysis.confidence_score:.2f})")
        print(f"Type: {analysis.type.value}")
        print(f"Severity: {analysis.severity.value}")
        print(f"Components: {', '.join(analysis.components)}")
        print(f"Missing Info: {', '.join(analysis.missing_info)}")
        print(f"Suggested Title: {analysis.suggested_title}")
        print(f"Suggested Labels: {', '.join(analysis.suggested_labels)}")
        print(f"Suggested Body:\n{analysis.suggested_body}")
