#!/usr/bin/env python3
"""
Code Review

簡易的な静的解析とコードレビューを実行するスクリプト。
"""

import json
import os
import re
import subprocess
from typing import Any


def get_staged_files() -> list[str]:
    """Get list of staged files"""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        files = result.stdout.strip().split("\n")
        return [f for f in files if f and f.endswith((".js", ".ts", ".tsx", ".py"))]
    except subprocess.CalledProcessError:
        return []


def get_staged_content(file_path: str) -> str:
    """Get staged content of file"""
    try:
        result = subprocess.run(
            ["git", "show", f":{file_path}"], capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""


def analyze_security_issues(content: str, file_path: str) -> list[dict[str, Any]]:
    """Analyze security issues with improved pattern matching"""
    issues = []
    lines = content.split("\n")

    # More sophisticated security patterns with context
    security_patterns = [
        # Hardcoded credentials (more specific patterns)
        {
            "pattern": r'(?:password|passwd|pwd)\s*[:=]\s*["\'][^"\']{4,}["\']',
            "message": "Hardcoded password detected",
            "severity": "high",
            "exclude_comments": True,
        },
        {
            "pattern": r'(?:api[_-]?key|apikey)\s*[:=]\s*["\'][^"\']{10,}["\']',
            "message": "Hardcoded API key detected",
            "severity": "high",
            "exclude_comments": True,
        },
        {
            "pattern": r'(?:secret|token)\s*[:=]\s*["\'][^"\']{8,}["\']',
            "message": "Hardcoded secret/token detected",
            "severity": "high",
            "exclude_comments": True,
        },
        # Dangerous functions
        {
            "pattern": r"\beval\s*\(",
            "message": "Use of eval() detected - potential code injection",
            "severity": "medium",
            "exclude_comments": False,
        },
        {
            "pattern": r"\bexec\s*\(",
            "message": "Use of exec() detected - potential code injection",
            "severity": "medium",
            "exclude_comments": False,
        },
        {
            "pattern": r"shell\s*=\s*True",
            "message": "Shell injection risk (shell=True)",
            "severity": "medium",
            "exclude_comments": False,
        },
        # XSS vulnerabilities
        {
            "pattern": r"innerHTML\s*=",
            "message": "XSS vulnerability - innerHTML assignment",
            "severity": "medium",
            "exclude_comments": False,
        },
        {
            "pattern": r"document\.write\s*\(",
            "message": "XSS vulnerability - document.write usage",
            "severity": "medium",
            "exclude_comments": False,
        },
        # SQL injection patterns
        {
            "pattern": r'(?:query|execute)\s*\(\s*["\'][^"\']*\+[^"\']*["\']',
            "message": "Potential SQL injection - string concatenation in query",
            "severity": "high",
            "exclude_comments": True,
        },
    ]

    for i, line in enumerate(lines, 1):
        stripped_line = line.strip()

        # Skip comment lines if configured
        is_comment = stripped_line.startswith(
            ("#", "//", "/*", "*")
        ) or stripped_line.endswith("*/")

        for pattern_config in security_patterns:
            pattern = pattern_config["pattern"]
            message = pattern_config["message"]
            severity = pattern_config["severity"]
            exclude_comments = pattern_config["exclude_comments"]

            # Skip if it's a comment and comments should be excluded
            if is_comment and exclude_comments:
                continue

            if re.search(pattern, line, re.IGNORECASE):
                # Additional check: exclude obvious false positives
                if any(
                    keyword in line.lower()
                    for keyword in ["example", "demo", "test", "sample", "placeholder"]
                ):
                    continue

                issues.append(
                    {
                        "type": "security",
                        "severity": severity,
                        "line": i,
                        "file": file_path,
                        "message": message,
                        "code": line.strip(),
                        "context": "comment" if is_comment else "code",
                    }
                )

    return issues


def analyze_code_quality(content: str, file_path: str) -> list[dict[str, Any]]:
    """Analyze code quality issues"""
    issues = []
    lines = content.split("\n")

    # Quality patterns
    quality_patterns = [
        (r"console\.log", "Debug console.log found"),
        (r"print\s*\(", "Debug print statement found"),
        (r"TODO:", "TODO comment found"),
        (r"FIXME:", "FIXME comment found"),
        (r"HACK:", "HACK comment found"),
        (r"^.{120,}", "Line too long (>120 characters)"),
    ]

    for i, line in enumerate(lines, 1):
        # Skip comments for some patterns
        stripped_line = line.strip()
        if stripped_line.startswith(("#", "//", "/*", "*")):
            continue

        for pattern, message in quality_patterns:
            if re.search(pattern, line):
                issues.append(
                    {
                        "type": "quality",
                        "severity": "medium",
                        "line": i,
                        "file": file_path,
                        "message": message,
                        "code": line.strip(),
                    }
                )

    return issues


def analyze_complexity(content: str, file_path: str) -> list[dict[str, Any]]:
    """Analyze code complexity"""
    issues = []

    # Function detection
    if file_path.endswith(".py"):
        func_pattern = r"def\s+(\w+)\s*\([^)]*\):"
    else:  # JS/TS
        func_pattern = r"function\s+(\w+)\s*\(|const\s+(\w+)\s*=\s*\([^)]*\)\s*=>"

    functions = re.finditer(func_pattern, content)

    for func_match in functions:
        func_name = func_match.group(1) or func_match.group(2)
        start_pos = func_match.start()

        # Find function end (simplified)
        remaining_content = content[start_pos:]
        if file_path.endswith(".py"):
            lines = remaining_content.split("\n")
            func_lines = 0
            for line in lines[1:]:
                if (
                    line.strip()
                    and not line.startswith(" ")
                    and not line.startswith("\t")
                ):
                    break
                func_lines += 1
        else:
            # JS/TS - find closing brace
            brace_count = 0
            func_lines = 0
            for char in remaining_content:
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        break
                func_lines += 1

        if func_lines > 50:
            issues.append(
                {
                    "type": "complexity",
                    "severity": "medium",
                    "function": func_name,
                    "lines": func_lines,
                    "file": file_path,
                    "message": f"Function {func_name} is too long ({func_lines} lines)",
                }
            )

    return issues


def run_code_review() -> dict[str, Any]:
    """Main code review function"""
    files = get_staged_files()
    all_issues = []
    file_summaries = []

    for file_path in files:
        content = get_staged_content(file_path)

        if not content:
            continue

        # Run different analyses
        security_issues = analyze_security_issues(content, file_path)
        quality_issues = analyze_code_quality(content, file_path)
        complexity_issues = analyze_complexity(content, file_path)

        all_issues.extend(security_issues)
        all_issues.extend(quality_issues)
        all_issues.extend(complexity_issues)

        file_summaries.append(
            {
                "file": file_path,
                "lines_of_code": len(content.split("\n")),
                "security_issues": len(security_issues),
                "quality_issues": len(quality_issues),
                "complexity_issues": len(complexity_issues),
            }
        )

    # Count severity
    severity_counts = {
        "high": sum(1 for issue in all_issues if issue["severity"] == "high"),
        "medium": sum(1 for issue in all_issues if issue["severity"] == "medium"),
        "low": sum(1 for issue in all_issues if issue["severity"] == "low"),
    }

    return {
        "success": True,
        "files_reviewed": len(files),
        "total_issues": len(all_issues),
        "severity_breakdown": severity_counts,
        "files": file_summaries,
        "issues": all_issues,
        "recommendation": "commit" if severity_counts["high"] == 0 else "review_needed",
    }


def save_results(result: dict[str, Any]) -> None:
    """Save results to temp file for create_commit.py to read"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(script_dir, "..", "temp")
    os.makedirs(temp_dir, exist_ok=True)

    temp_file = os.path.join(temp_dir, "review_results.json")
    try:
        with open(temp_file, "w") as f:
            json.dump(result, f, indent=2)
    except OSError:
        pass  # Continue execution even if saving fails


def main():
    """Main function"""
    result = run_code_review()
    save_results(result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
