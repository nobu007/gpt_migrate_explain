#!/usr/bin/env python3
"""
Test script to verify token loading functionality
"""

import os
import sys
from pathlib import Path

# Add scripts directory to path
script_dir = Path(__file__).parent / "scripts"
sys.path.insert(0, str(script_dir))

from github_client import GitHubClient


def test_token_loading():
    """Test that tokens are loaded from various sources"""
    print("🔍 Testing GitHub Token Loading")
    print("=" * 50)

    # Test 1: Direct token parameter
    print("\n1. Testing direct token parameter:")
    try:
        client = GitHubClient(token="test-token-123", allow_read_only=True)
        print(f"   ✅ Token from parameter: {client.token[:10]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 2: Environment variable
    print("\n2. Testing environment variable:")
    original_token = os.getenv("GITHUB_TOKEN")
    os.environ["GITHUB_TOKEN"] = "env-token-456"
    try:
        client = GitHubClient(allow_read_only=True)
        print(f"   ✅ Token from environment: {client.token[:10]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    finally:
        if original_token:
            os.environ["GITHUB_TOKEN"] = original_token
        else:
            os.environ.pop("GITHUB_TOKEN", None)

    # Test 3: .env file loading
    print("\n3. Testing .env file loading:")
    env_files = [
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        Path(__file__).parent / ".env",
    ]

    found_env_files = []
    for env_file in env_files:
        if env_file.exists():
            found_env_files.append(str(env_file))

    if found_env_files:
        print(f"   📁 Found .env files: {found_env_files}")
        try:
            client = GitHubClient(allow_read_only=True)
            if client.token:
                print(f"   ✅ Token loaded: {client.token[:10]}...")
                print(f"   🎯 Token length: {len(client.token)} characters")
                print(
                    f"   🔒 Token format: {'Looks valid' if client.token.startswith('ghp_') else 'Unknown format'}"
                )
            else:
                print("   ⚠️  No token found in .env files")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    else:
        print("   ⚠️  No .env files found in expected locations")

    # Test 4: Dry-run functionality
    print("\n4. Testing dry-run functionality:")
    try:
        client = GitHubClient(allow_read_only=True)
        issue = client.get_issue("test/repo", 123)
        print(f"   ✅ Dry-run mock issue: {issue.title}")
        print(f"   ✅ Allow read-only: {client.allow_read_only}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 5: Priority order
    print("\n5. Testing priority order:")
    os.environ["GITHUB_TOKEN"] = "env-priority-test"
    try:
        # Direct parameter should take priority
        client = GitHubClient(token="priority-test", allow_read_only=True)
        if client.token == "priority-test":
            print("   ✅ Direct parameter has priority over environment")
        else:
            print("   ❌ Priority order is incorrect")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    finally:
        if original_token:
            os.environ["GITHUB_TOKEN"] = original_token
        else:
            os.environ.pop("GITHUB_TOKEN", None)

    print("\n" + "=" * 50)
    print("🎯 Token Loading Test Complete")


if __name__ == "__main__":
    test_token_loading()
