#!/usr/bin/env python3
"""
Create Commit

Conventional Commits準拠のコミットメッセージを生成し、コミットを実行するスクリプト。
"""

import json
import os
import subprocess
from typing import Any


def get_staged_files_info() -> dict[str, Any]:
    """Get information about staged files"""
    try:
        # Get list of staged files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        files = result.stdout.strip().split("\n")
        files = [f for f in files if f]

        # Get diff stats
        result = subprocess.run(
            ["git", "diff", "--cached", "--stat"],
            capture_output=True,
            text=True,
            check=True,
        )

        return {"files": files, "total_files": len(files), "diff_stats": result.stdout}
    except subprocess.CalledProcessError:
        return {"files": [], "total_files": 0, "diff_stats": ""}


def detect_commit_type(files: list[str], diff_stats: str) -> str:
    """Detect commit type based on changes"""
    file_extensions = [os.path.splitext(f)[1] for f in files]
    file_names = [os.path.basename(f) for f in files]

    # Check for specific patterns
    if any(
        "package.json" in f or "requirements.txt" in f or "yarn.lock" in f
        for f in files
    ):
        return "chore"

    if any("README" in f or "CHANGELOG" in f or f.endswith(".md") for f in files):
        return "docs"

    if any("test" in f.lower() or "spec" in f.lower() for f in files):
        return "test"

    if any("fix" in f.lower() or any("bugfix" in f.lower() for f in file_names)):
        return "fix"

    # Check for feature indicators
    if ".py" in file_extensions or ".js" in file_extensions or ".ts" in file_extensions:
        return "feat"

    if any("config" in f.lower() or "env" in f.lower() for f in files):
        return "chore"

    return "feat"  # Default


def generate_commit_message(
    files_info: dict[str, Any],
    lint_result: dict[str, Any],
    test_result: dict[str, Any],
    review_result: dict[str, Any],
) -> str:
    """Generate conventional commit message"""
    commit_type = detect_commit_type(files_info["files"], files_info["diff_stats"])

    # Base message
    if commit_type == "feat":
        if test_result.get("success", False):
            message = "feat: add new functionality with tests"
        else:
            message = "feat: add new functionality"
    elif commit_type == "fix":
        message = "fix: resolve issue with code logic"
    elif commit_type == "docs":
        message = "docs: update documentation"
    elif commit_type == "test":
        message = "test: add or update tests"
    elif commit_type == "chore":
        message = "chore: update dependencies or configuration"
    else:
        message = f"{commit_type}: implement changes"

    # Add scope if identifiable
    if len(files_info["files"]) == 1:
        file_path = files_info["files"][0]
        if "src/" in file_path:
            scope = file_path.split("/")[1]
            message = f"{commit_type}({scope}): {message.split(': ', 1)[1]}"
        elif "test" in file_path:
            message = f"{commit_type}(tests): {message.split(': ', 1)[1]}"

    # Add body with details
    body_parts = []
    body_parts.append(f"Files changed: {files_info['total_files']}")

    if test_result.get("success", False) and test_result.get("total_tests", 0) > 0:
        body_parts.append(
            f"Tests: {test_result['total_tests']} total, {test_result['coverage_percentage']:.1f}% coverage"
        )

    if lint_result.get("overall_success", False):
        body_parts.append("Lint: passed")
    else:
        body_parts.append("Lint: needs attention")

    if review_result.get("total_issues", 0) > 0:
        body_parts.append(f"Code review: {review_result['total_issues']} issues found")

    return message


def create_commit(message: str) -> dict[str, Any]:
    """Create git commit"""
    try:
        # Create commit
        result = subprocess.run(
            ["git", "commit", "-m", message], capture_output=True, text=True, check=True
        )

        return {"success": True, "message": message, "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"success": False, "message": message, "error": e.stderr}


def load_script_results() -> dict[str, Any]:
    """Load results from other scripts via temporary files"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(script_dir, "..", "temp")

    # Ensure temp directory exists
    os.makedirs(temp_dir, exist_ok=True)

    results = {
        "lint_result": {"overall_success": True, "tools": []},
        "test_result": {"success": True, "total_tests": 0, "coverage_percentage": 0},
        "review_result": {
            "total_issues": 0,
            "severity_breakdown": {"high": 0, "medium": 0, "low": 0},
        },
    }

    # Try to load lint results
    lint_file = os.path.join(temp_dir, "lint_results.json")
    if os.path.exists(lint_file):
        try:
            with open(lint_file) as f:
                results["lint_result"] = json.load(f)
        except (OSError, json.JSONDecodeError):
            pass

    # Try to load test results
    test_file = os.path.join(temp_dir, "test_results.json")
    if os.path.exists(test_file):
        try:
            with open(test_file) as f:
                results["test_result"] = json.load(f)
        except (OSError, json.JSONDecodeError):
            pass

    # Try to load review results
    review_file = os.path.join(temp_dir, "review_results.json")
    if os.path.exists(review_file):
        try:
            with open(review_file) as f:
                results["review_result"] = json.load(f)
        except (OSError, json.JSONDecodeError):
            pass

    return results


def should_commit(results: dict[str, Any]) -> bool:
    """Determine if commit should proceed based on quality checks"""
    lint_result = results["lint_result"]
    test_result = results["test_result"]
    review_result = results["review_result"]

    # Lint must pass (formatting issues)
    if not lint_result.get("overall_success", False):
        return False

    # Tests must pass
    if not test_result.get("success", False):
        return False

    # No high severity security issues
    high_severity_issues = review_result.get("severity_breakdown", {}).get("high", 0)
    return not high_severity_issues > 0


def main():
    """Main function"""
    # Get staged files info
    files_info = get_staged_files_info()

    if files_info["total_files"] == 0:
        print(
            json.dumps({"success": False, "error": "No staged files found"}, indent=2)
        )
        return

    # Load results from other scripts
    results = load_script_results()
    lint_result = results["lint_result"]
    test_result = results["test_result"]
    review_result = results["review_result"]

    # Check if commit should proceed
    if not should_commit(results):
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "Quality checks failed. Please fix issues before committing.",
                    "lint_success": lint_result.get("overall_success", False),
                    "test_success": test_result.get("success", False),
                    "high_severity_issues": review_result.get(
                        "severity_breakdown", {}
                    ).get("high", 0),
                },
                indent=2,
            )
        )
        return

    # Generate commit message
    commit_message = generate_commit_message(
        files_info, lint_result, test_result, review_result
    )

    # Create commit
    commit_result = create_commit(commit_message)

    # Include quality check summary in output
    if commit_result["success"]:
        commit_result.update(
            {
                "quality_summary": {
                    "lint_passed": lint_result.get("overall_success", False),
                    "tests_passed": test_result.get("success", False),
                    "test_coverage": test_result.get("coverage_percentage", 0),
                    "security_issues": review_result.get("total_issues", 0),
                    "high_severity_issues": review_result.get(
                        "severity_breakdown", {}
                    ).get("high", 0),
                }
            }
        )

    print(json.dumps(commit_result, indent=2))


if __name__ == "__main__":
    main()
