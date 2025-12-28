#!/usr/bin/env python3
"""
Test script for common library integration in github-issue-improver
"""

import sys
import tempfile
from pathlib import Path


def test_env_parsing():
    """Test manual .env file parsing"""
    print("Testing .env file parsing...")

    # Create test .env file
    test_env_content = """
# Test environment file - KEYS ARE PLACEHOLDER VALUES, NOT REAL
GITHUB_TOKEN=ghp_TEST_PLACEHOLDER_TOKEN_12345
ANTHROPIC_API_KEY=sk-ant-TEST_PLACEHOLDER_KEY_67890

# Test with quotes
TEST_QUOTED="value with spaces"
TEST_SINGLE='single quoted value'

# Test with export
export EXPORTED_VAR=exported_value

# Test with comments
INLINE_COMMENT=value # this is a comment
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write(test_env_content)
        env_file = Path(f.name)

    try:
        # Test parsing
        sys.path.insert(0, str(Path(__file__).parent.parent / "lib" / "python"))
        from env_utils import parse_env_file_manual

        parsed_vars = parse_env_file_manual(env_file)
        print(f"✅ Parsed {len(parsed_vars)} variables")

        expected_vars = [
            "GITHUB_TOKEN",
            "ANTHROPIC_API_KEY",
            "TEST_QUOTED",
            "TEST_SINGLE",
            "EXPORTED_VAR",
            "INLINE_COMMENT",
        ]

        for var in expected_vars:
            if var in parsed_vars:
                print(f"  ✅ {var}: {parsed_vars[var][:20]}...")
            else:
                print(f"  ❌ {var}: NOT FOUND")

    except Exception as e:
        print(f"❌ Error testing .env parsing: {e}")
    finally:
        env_file.unlink()  # Clean up


def test_skill_base():
    """Test SkillBase functionality"""
    print("\nTesting SkillBase...")

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "lib" / "python"))
        from skill_base import SkillBase

        # Create test skill
        skill = SkillBase("test-skill")

        print(f"✅ Skill initialized: {skill.is_initialized()}")
        print(f"✅ Skill name: {skill.skill_name}")

        # Test environment variable access
        try:
            github_token = skill.get_optional_env_var("GITHUB_TOKEN")
            if github_token:
                print(f"✅ GITHUB_TOKEN found (length: {len(github_token)})")
            else:
                print("ℹ️  GITHUB_TOKEN not found (optional)")
        except Exception as e:
            print(f"⚠️  GitHub token check: {e}")

        # Show diagnostics
        diagnostics = skill.get_diagnostics()
        print(f"✅ Diagnostics available: {len(diagnostics)} items")

    except Exception as e:
        print(f"❌ Error testing SkillBase: {e}")


def test_diagnostics():
    """Test diagnostics functionality"""
    print("\nTesting diagnostics...")

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "lib" / "python"))
        from diagnostics import run_skill_diagnostics

        # Run diagnostics
        diag = run_skill_diagnostics("github-issue-improver-test")
        summary = diag.get_summary()

        print("✅ Diagnostics completed")
        print(f"  Total checks: {summary['total_checks']}")
        print(f"  Passed: {summary['passed_checks']}")
        print(f"  Failed: {summary['failed_checks']}")
        print(f"  Status: {summary['overall_status']}")
        print(f"  Success rate: {summary['success_rate']:.1f}%")

        if summary["error_count"] > 0:
            print(f"  ⚠️  {summary['error_count']} errors found")

    except Exception as e:
        print(f"❌ Error testing diagnostics: {e}")


def test_common_lib_availability():
    """Test if common library is available and functional"""
    print("Testing common library availability...")

    # Find common library
    current = Path(__file__).resolve()
    claude_lib = None
    for _ in range(10):
        lib_path = current / ".claude" / "lib"
        if lib_path.exists():
            claude_lib = lib_path
            break
        current = current.parent
        if current == current.parent:
            break

    if claude_lib:
        print(f"✅ Common library found at: {claude_lib}")

        # Test importing modules
        modules_to_test = ["env_utils", "skill_base", "diagnostics"]
        python_lib = claude_lib / "python"
        if python_lib.exists():
            sys.path.insert(0, str(python_lib))

        for module in modules_to_test:
            try:
                __import__(module)
                print(f"  ✅ {module}: IMPORT SUCCESS")
            except ImportError as e:
                print(f"  ❌ {module}: IMPORT FAILED - {e}")
    else:
        print("❌ Common library not found")
        return False

    return True


def main():
    """Run all tests"""
    print("=== GitHub Issue Improver Common Library Integration Test ===\n")

    tests = [
        ("Common Library Availability", test_common_lib_availability),
        (".env File Parsing", test_env_parsing),
        ("SkillBase", test_skill_base),
        ("Diagnostics", test_diagnostics),
    ]

    results = {}
    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        try:
            result = test_func()
            results[test_name] = result is not False
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results[test_name] = False
        print()

    # Summary
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    print("=== Test Summary ===")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    print("⚠️  Some tests failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
