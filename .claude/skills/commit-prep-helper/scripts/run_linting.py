#!/usr/bin/env python3
"""
Run Linting

プロジェクトに応じたLint/Formatチェックを実行するスクリプト。
"""

import json
import os
import subprocess
from typing import Any


def detect_project_type() -> str:
    """Detect project type from files"""
    if os.path.exists("package.json"):
        return "node"
    if os.path.exists("requirements.txt") or os.path.exists("pyproject.toml"):
        return "python"
    if os.path.exists("Cargo.toml"):
        return "rust"
    if os.path.exists("go.mod"):
        return "go"
    return "unknown"


def run_eslint() -> dict[str, Any]:
    """Run ESLint with improved error handling"""
    try:
        result = subprocess.run(
            ["npx", "eslint", "--format=json", "."],
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
        )

        issues = []
        if result.stdout:
            try:
                issues = json.loads(result.stdout)
            except json.JSONDecodeError:
                # Try to parse as individual JSON objects (ESLint sometimes outputs this way)
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if line.strip():
                        try:
                            issues.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

        return {
            "tool": "eslint",
            "success": result.returncode == 0,
            "issues": issues,
            "error_output": result.stderr if result.returncode != 0 else None,
            "warning_count": len(
                [issue for issue in issues if issue.get("severity") == 1]
            ),
            "error_count": len(
                [issue for issue in issues if issue.get("severity") == 2]
            ),
        }
    except subprocess.TimeoutExpired:
        return {
            "tool": "eslint",
            "success": False,
            "issues": [],
            "error_output": "ESLint timed out after 30 seconds",
        }
    except FileNotFoundError:
        return {
            "tool": "eslint",
            "success": False,
            "issues": [],
            "error_output": "ESLint not found",
        }


def run_prettier_check() -> dict[str, Any]:
    """Run Prettier format check with improved error handling"""
    try:
        result = subprocess.run(
            ["npx", "prettier", "--check", "."],
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
        )

        # Parse prettier output to get list of unformatted files
        unformatted_files = []
        if result.returncode != 0 and result.stderr:
            # Prettier outputs unformatted files to stderr
            lines = result.stderr.strip().split("\n")
            for line in lines:
                if line.strip() and not line.startswith("["):
                    unformatted_files.append(line.strip())

        return {
            "tool": "prettier",
            "success": result.returncode == 0,
            "error_output": result.stderr if result.returncode != 0 else None,
            "unformatted_files": unformatted_files,
        }
    except subprocess.TimeoutExpired:
        return {
            "tool": "prettier",
            "success": False,
            "error_output": "Prettier timed out after 30 seconds",
        }
    except FileNotFoundError:
        return {
            "tool": "prettier",
            "success": False,
            "error_output": "Prettier not found",
        }


def run_flake8() -> dict[str, Any]:
    """Run flake8 for Python linting with timeout"""
    try:
        result = subprocess.run(
            ["flake8", "--format=json", "."],
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
        )

        # Parse flake8 output (it outputs plain text by default)
        issues = []
        if result.stdout:
            # Convert flake8 output to structured format
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split(":", 3)
                    if len(parts) >= 4:
                        try:
                            issues.append(
                                {
                                    "file": parts[0],
                                    "line": int(parts[1]),
                                    "column": int(parts[2]),
                                    "message": parts[3].strip(),
                                    "severity": "error",  # flake8 doesn't distinguish
                                }
                            )
                        except (ValueError, IndexError):
                            continue

        return {
            "tool": "flake8",
            "success": result.returncode == 0,
            "issues": issues,
            "error_output": result.stderr if result.returncode != 0 else None,
        }
    except subprocess.TimeoutExpired:
        return {
            "tool": "flake8",
            "success": False,
            "issues": [],
            "error_output": "flake8 timed out after 30 seconds",
        }
    except FileNotFoundError:
        return {
            "tool": "flake8",
            "success": False,
            "issues": [],
            "error_output": "flake8 not found",
        }


def run_pylint() -> dict[str, Any]:
    """Run pylint for Python linting with timeout"""
    try:
        result = subprocess.run(
            ["pylint", "--output-format=json", "."],
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
        )

        issues = []
        if result.stdout:
            try:
                issues = json.loads(result.stdout)
            except json.JSONDecodeError:
                # Fallback parsing if output is not valid JSON
                pass

        return {
            "tool": "pylint",
            "success": result.returncode == 0,
            "issues": issues,
            "error_output": result.stderr if result.returncode != 0 else None,
        }
    except subprocess.TimeoutExpired:
        return {
            "tool": "pylint",
            "success": False,
            "issues": [],
            "error_output": "pylint timed out after 30 seconds",
        }
    except FileNotFoundError:
        return {
            "tool": "pylint",
            "success": False,
            "issues": [],
            "error_output": "pylint not found",
        }


def run_black_check() -> dict[str, Any]:
    """Run Black format check with timeout"""
    try:
        result = subprocess.run(
            ["python", "-m", "black", "--check", "."],
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
        )

        return {
            "tool": "black",
            "success": result.returncode == 0,
            "error_output": result.stderr if result.returncode != 0 else None,
        }
    except subprocess.TimeoutExpired:
        return {
            "tool": "black",
            "success": False,
            "error_output": "Black timed out after 30 seconds",
        }
    except FileNotFoundError:
        return {"tool": "black", "success": False, "error_output": "Black not found"}


def run_linting() -> dict[str, Any]:
    """Main linting function"""
    project_type = detect_project_type()
    results = {"project_type": project_type, "tools": [], "overall_success": True}

    if project_type == "node":
        eslint_result = run_eslint()
        prettier_result = run_prettier_check()
        results["tools"].extend([eslint_result, prettier_result])

        results["overall_success"] = (
            eslint_result["success"] and prettier_result["success"]
        )

    elif project_type == "python":
        # Try different Python linting tools in order of preference
        flake8_result = run_flake8()
        pylint_result = run_pylint()
        black_result = run_black_check()
        results["tools"].extend([flake8_result, pylint_result, black_result])

        # At least one linting tool should pass for formatting
        results["overall_success"] = black_result["success"]
        # Include warnings from flake8/pylint but don't block commit
        if (
            not flake8_result["success"]
            and flake8_result["error_output"] != "flake8 not found"
        ):
            results["overall_success"] = False

    else:
        results["overall_success"] = False
        results["error"] = f"Unsupported project type: {project_type}"

    return results


def save_results(results: dict[str, Any]) -> None:
    """Save results to temp file for create_commit.py to read"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(script_dir, "..", "temp")
    os.makedirs(temp_dir, exist_ok=True)

    temp_file = os.path.join(temp_dir, "lint_results.json")
    try:
        with open(temp_file, "w") as f:
            json.dump(results, f, indent=2)
    except OSError:
        pass  # Continue execution even if saving fails


def main():
    """Main function"""
    results = run_linting()
    save_results(results)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
