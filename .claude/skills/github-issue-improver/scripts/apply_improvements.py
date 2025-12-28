#!/usr/bin/env python3
"""Utility script to apply specific improvements to issues"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Try to load python-dotenv
try:
    from dotenv import load_dotenv

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    load_dotenv = None

from issue_improver import IssueImprover


def load_env_files():
    """Load .env files from multiple locations"""
    if not DOTENV_AVAILABLE:
        return

    # Priority order for .env files
    env_locations = [
        # Script directory (for skill execution)
        Path(__file__).parent / ".env",
        # Current working directory (for direct execution)
        Path.cwd() / ".env",
        # Parent directory (for project root)
        Path.cwd().parent / ".env",
        # Two levels up (for nested execution)
        Path.cwd().parent.parent / ".env",
    ]

    loaded_files = []
    for env_path in env_locations:
        if env_path.exists() and str(env_path) not in loaded_files:
            try:
                load_dotenv(env_path, override=False)
                loaded_files.append(str(env_path))
            except Exception:
                continue


def apply_improvements_from_file(
    repo: str, improvements_file: str, token: str | None = None, dry_run: bool = False
) -> dict[str, Any]:
    """Apply improvements from a JSON file"""
    # Load improvements file
    try:
        with open(improvements_file, encoding="utf-8") as f:
            improvements = json.load(f)
    except Exception as e:
        return {
            "error": f"Failed to load improvements file: {e}",
            "improvements_file": improvements_file,
        }

    # Initialize improver
    improver = IssueImprover(token=token, allow_read_only=dry_run)
    results = {
        "improvements_file": improvements_file,
        "total_issues": len(improvements),
        "results": [],
    }

    for issue_data in improvements:
        issue_number = issue_data.get("issue_number")
        if not issue_number:
            continue

        # Get current issue
        try:
            issue = improver.github_client.get_issue(repo, issue_number)

            if dry_run:
                # Show what would be updated
                result = {
                    "issue_number": issue_number,
                    "dry_run": True,
                    "current_title": issue.title,
                    "current_body": issue.body,
                    "current_labels": issue.labels,
                    "suggested_title": issue_data.get("suggested_title"),
                    "suggested_body": issue_data.get("suggested_body"),
                    "suggested_labels": issue_data.get("suggested_labels", []),
                }

                # Calculate what would change
                result["title_changed"] = (
                    issue_data.get("suggested_title") != issue.title
                )
                result["body_changed"] = issue_data.get("suggested_body") != issue.body
                result["labels_changed"] = set(
                    issue_data.get("suggested_labels", [])
                ) != set(issue.labels)

            else:
                # Apply actual updates
                result = improver.improve_issue(
                    repo=repo,
                    issue_number=issue_number,
                    update_title=bool(issue_data.get("suggested_title")),
                    update_body=bool(issue_data.get("suggested_body")),
                    update_labels=bool(issue_data.get("suggested_labels")),
                    mode="update",
                )

            results["results"].append(result)

        except Exception as e:
            results["results"].append({"issue_number": issue_number, "error": str(e)})

    return results


def create_improvements_template(
    repo: str, issue_numbers: list[int], token: str | None = None
) -> dict[str, Any]:
    """Generate improvements template for given issues"""
    improver = IssueImprover(token=token, allow_read_only=True)
    template = []

    for issue_number in issue_numbers:
        try:
            issue = improver.github_client.get_issue(repo, issue_number)
            analysis = improver.analyzer.analyze_issue(issue.title, issue.body)

            improvement = {
                "issue_number": issue_number,
                "current_title": issue.title,
                "current_body": issue.body,
                "current_labels": issue.labels,
                "suggested_title": analysis.suggested_title,
                "suggested_body": analysis.suggested_body,
                "suggested_labels": analysis.suggested_labels,
                "analysis": {
                    "type": analysis.type.value,
                    "severity": analysis.severity.value,
                    "confidence_score": analysis.confidence_score,
                    "needs_improvement": (
                        analysis.suggested_title != issue.title
                        or analysis.suggested_body != issue.body
                        or set(analysis.suggested_labels) != set(issue.labels)
                    ),
                },
            }

            template.append(improvement)

        except Exception as e:
            template.append({"issue_number": issue_number, "error": str(e)})

    return {"improvements": template}


def main():
    """CLI interface"""
    # Load environment files first
    load_env_files()

    parser = argparse.ArgumentParser(
        description="Apply GitHub Issue improvements from predefined data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate template for issues 123 and 124
  python apply_improvements.py --repo owner/repo --template --issues 123 124

  # Apply improvements from improvements.json
  python apply_improvements.py --repo owner/repo --apply improvements.json

  # Preview what would be applied
  python apply_improvements.py --repo owner/repo --apply improvements.json --dry-run
        """,
    )

    parser.add_argument("--repo", required=True, help="Repository in format owner/repo")
    parser.add_argument(
        "--token", help="GitHub token (optional, will also check .env file)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying"
    )

    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    # Template generation
    template_parser = subparsers.add_parser(
        "template", help="Generate improvements template"
    )
    template_parser.add_argument(
        "--issues",
        nargs="+",
        type=int,
        required=True,
        help="Issue numbers to generate template for",
    )
    template_parser.add_argument(
        "--output", help="Output file for template (default: stdout)"
    )

    # Apply improvements
    apply_parser = subparsers.add_parser("apply", help="Apply improvements from file")
    apply_parser.add_argument(
        "--improvements-file",
        required=True,
        help="JSON file containing improvements to apply",
    )

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    try:
        if args.action == "template":
            # Generate template
            template_data = create_improvements_template(
                repo=args.repo, issue_numbers=args.issues, token=args.token
            )

            template_json = json.dumps(template_data, indent=2, ensure_ascii=False)

            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(template_json)
                print(f"Template saved to {args.output}")
            else:
                print(template_json)

        elif args.action == "apply":
            # Apply improvements
            results = apply_improvements_from_file(
                repo=args.repo,
                improvements_file=args.improvements_file,
                token=args.token,
                dry_run=args.dry_run,
            )

            print(json.dumps(results, indent=2, ensure_ascii=False))

            # Summary
            if "results" in results:
                successful = sum(1 for r in results["results"] if "error" not in r)
                failed = len(results["results"]) - successful
                print(f"\nSummary: {successful} successful, {failed} failed")

                if args.dry_run:
                    print("This was a dry-run. No changes were applied.")
                else:
                    print("Changes have been applied to GitHub.")

    except Exception as e:
        print(f"Error: {e}")

        # Add helpful hint about token setup
        if "GitHub token is required" in str(e) or "GitHub token required" in str(e):
            print("\n💡 Token Setup Help:")
            print("1. Create a .env file with: GITHUB_TOKEN=your_token_here")
            print("2. Install python-dotenv: pip install python-dotenv")
            print("3. Or use --token parameter directly")
            print("4. Or set environment variable: export GITHUB_TOKEN=your_token")

        sys.exit(1)


if __name__ == "__main__":
    main()
