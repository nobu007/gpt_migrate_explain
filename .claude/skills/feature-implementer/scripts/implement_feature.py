#!/usr/bin/env python3
"""Feature Implementer Skill - Generates feature implementation using Claude"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


# Setup common library path
def find_claude_lib():
    current = Path(__file__).resolve()
    for _ in range(8):
        claude_lib = current / ".claude" / "lib" / "python"
        if claude_lib.exists():
            return str(claude_lib)
        current = current.parent
        if current == current.parent:
            break
    return None


claude_lib_path = find_claude_lib()
if claude_lib_path:
    sys.path.insert(0, claude_lib_path)
    from env_utils import load_env_files, setup_python_path

    setup_python_path()
    load_env_files()


def implement_feature(title: str, body: str, instructions: str) -> dict[str, Any]:
    """Generate feature implementation using Claude CLI"""
    # Check API Key presence to avoid hanging on auth prompt
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
    obvious_placeholders = [
        "your_api_key",
        "placeholder",
        "test_key",
        "demo_key",
        "example_key",
    ]

    if not api_key or any(p in api_key.lower() for p in obvious_placeholders):
        return {"success": False, "error": "Missing or invalid ANTHROPIC_API_KEY"}

    # Construct the prompt
    prompt = f"""
{instructions}

Feature Request Details:
Title: {title}
Body:
{body}
"""

    try:
        # Use Claude CLI via subprocess
        print("DEBUG: Calling claude CLI for feature implementation", file=sys.stderr)
        result = subprocess.run(
            ["claude", "-p", prompt, "--setting-sources", "user"],
            capture_output=True,
            text=True,
            env={**os.environ, "CI": "true"},
            stdin=subprocess.DEVNULL,
            timeout=600,  # Longer timeout for features
        )

        if result.returncode != 0:
            return {"success": False, "error": f"Claude CLI failed: {result.stderr}"}

        response_text = result.stdout.strip()

        # Extract JSON
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()

        try:
            result_json = json.loads(response_text)
            if "success" not in result_json:
                result_json["success"] = True
            return result_json
        except json.JSONDecodeError:
            return {
                "success": True,
                "plan": response_text,
                "files": [],
                "error": "Output was not valid JSON",
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", help="Repository name")
    parser.add_argument("--issue", help="Issue number")

    args, unknown = parser.parse_known_args()

    title = os.environ.get("CLAUDE_INPUT_TITLE", "")
    body = os.environ.get("CLAUDE_INPUT_BODY", "")
    instructions = os.environ.get("CLAUDE_INSTRUCTIONS", "")

    if not instructions:
        instructions = (
            "Implement the requested feature. Return JSON with 'plan' and 'files'."
        )

    result = implement_feature(title, body, instructions)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
