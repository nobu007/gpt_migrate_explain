#!/usr/bin/env python3
"""
Run Tests

プロジェクトのテストを実行し、カバレッジを確認するスクリプト。
"""

import json
import os
import re
import subprocess
from typing import Any


def detect_test_framework() -> str:
    """Detect test framework"""
    if os.path.exists("package.json"):
        with open("package.json") as f:
            package = json.load(f)
            deps = {
                **package.get("dependencies", {}),
                **package.get("devDependencies", {}),
            }

            if "jest" in deps:
                return "jest"
            if "vitest" in deps:
                return "vitest"
            if "mocha" in deps:
                return "mocha"

    elif os.path.exists("pyproject.toml"):
        return "pytest"

    return "unknown"


def run_jest_tests(coverage: bool = True) -> dict[str, Any]:
    """Run Jest tests"""
    cmd = ["npx", "jest"]
    if coverage:
        cmd.extend(["--coverage", "--passWithNoTests"])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5分タイムアウト
        )

        # Parse Jest output
        passed_tests = 0
        failed_tests = 0
        coverage_pct = 0

        # Test results parsing
        test_match = re.search(
            r"Tests:\s+(\d+)\s+failed,\s+(\d+)\s+passed", result.stdout
        )
        if test_match:
            failed_tests = int(test_match.group(1))
            passed_tests = int(test_match.group(2))
        else:
            # Alternative pattern
            test_match = re.search(r"(\d+)\s+passing\s*\((\d+)\)", result.stdout)
            if test_match:
                passed_tests = int(test_match.group(1))

        # Coverage parsing
        coverage_match = re.search(
            r"All files\s+\|\s+(\d+(?:\.\d+)?)\s*\|", result.stdout
        )
        if coverage_match:
            coverage_pct = float(coverage_match.group(1))

        return {
            "framework": "jest",
            "success": result.returncode == 0,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "total_tests": passed_tests + failed_tests,
            "coverage_percentage": coverage_pct,
            "output": result.stdout,
            "error_output": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "framework": "jest",
            "success": False,
            "error": "Test execution timed out",
        }
    except FileNotFoundError:
        return {"framework": "jest", "success": False, "error": "Jest not found"}


def run_vitest_tests(coverage: bool = True) -> dict[str, Any]:
    """Run Vitest tests"""
    cmd = ["npx", "vitest", "run"]
    if coverage:
        cmd.append("--coverage")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        # Parse Vitest output
        passed_tests = 0
        failed_tests = 0

        test_match = re.search(r"✓ (\d+).*✗ (\d+)", result.stdout)
        if test_match:
            passed_tests = int(test_match.group(1))
            failed_tests = int(test_match.group(2))

        return {
            "framework": "vitest",
            "success": result.returncode == 0,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "total_tests": passed_tests + failed_tests,
            "output": result.stdout,
            "error_output": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "framework": "vitest",
            "success": False,
            "error": "Test execution timed out",
        }
    except FileNotFoundError:
        return {"framework": "vitest", "success": False, "error": "Vitest not found"}


def run_pytest_tests(coverage: bool = True) -> dict[str, Any]:
    """Run pytest"""
    cmd = ["python", "-m", "pytest", "-v"]
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=term-missing"])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        # Parse pytest output
        passed_tests = 0
        failed_tests = 0
        coverage_pct = 0

        # Test results
        test_match = re.search(r"(\d+)\s+passed.*?(\d+)\s+failed", result.stdout)
        if test_match:
            passed_tests = int(test_match.group(1))
            failed_tests = int(test_match.group(2))
        else:
            # Single result case
            test_match = re.search(r"(\d+)\s+(passed|failed)", result.stdout)
            if test_match:
                count = int(test_match.group(1))
                status = test_match.group(2)
                if status == "passed":
                    passed_tests = count
                else:
                    failed_tests = count

        # Coverage
        coverage_match = re.search(
            r"TOTAL\s+\d+\s+\d+\s+(\d+(?:\.\d+)?)%", result.stdout
        )
        if coverage_match:
            coverage_pct = float(coverage_match.group(1))

        return {
            "framework": "pytest",
            "success": result.returncode == 0,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "total_tests": passed_tests + failed_tests,
            "coverage_percentage": coverage_pct,
            "output": result.stdout,
            "error_output": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "framework": "pytest",
            "success": False,
            "error": "Test execution timed out",
        }
    except FileNotFoundError:
        return {"framework": "pytest", "success": False, "error": "pytest not found"}


def save_results(result: dict[str, Any]) -> None:
    """Save results to temp file for create_commit.py to read"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(script_dir, "..", "temp")
    os.makedirs(temp_dir, exist_ok=True)

    temp_file = os.path.join(temp_dir, "test_results.json")
    try:
        with open(temp_file, "w") as f:
            json.dump(result, f, indent=2)
    except OSError:
        pass  # Continue execution even if saving fails


def main():
    """Main function"""
    framework = detect_test_framework()
    result = None

    if framework == "jest":
        result = run_jest_tests()
    elif framework == "vitest":
        result = run_vitest_tests()
    elif framework == "pytest":
        result = run_pytest_tests()
    else:
        result = {
            "success": False,
            "error": f"No supported test framework found. Detected: {framework}",
        }

    save_results(result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
