#!/usr/bin/env python3
"""
Main issue improvement script
Enhanced with common library integration and improved .env handling
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


# Setup common library path (enhanced discovery)
def find_claude_lib():
    current = Path(__file__).resolve()
    for _ in range(10):  # Search up to 10 levels
        claude_lib = current / ".claude" / "lib"
        if claude_lib.exists():
            return str(claude_lib)
        current = current.parent
        if current == current.parent:  # Filesystem root reached
            break
    return None  # Not found


claude_lib_path = find_claude_lib()
if claude_lib_path:
    python_lib_path = Path(claude_lib_path) / "python"
    if python_lib_path.exists():
        sys.path.insert(0, str(python_lib_path))
    else:
        sys.path.insert(0, claude_lib_path)

    try:
        from diagnostics import run_skill_diagnostics
        from env_utils import load_env_files, setup_python_path
        from skill_base import SkillBase

        COMMON_LIB_AVAILABLE = True
    except ImportError as e:
        # Fallback to legacy behavior
        print(f"Warning: Common library import failed: {e}", file=sys.stderr)
        try:
            from env_utils import load_env_files, setup_python_path
        except ImportError:
            # Create minimal implementations
            def load_env_files(*args, **kwargs):
                return []

            def setup_python_path(*args, **kwargs):
                pass

        COMMON_LIB_AVAILABLE = False

        # Create a minimal fallback base class
        class SkillBase:
            def __init__(self, skill_name: str, start_path: Path | None = None):
                self.skill_name = skill_name
                self.start_path = start_path or Path(__file__).resolve().parent
                self.env_info = load_env_files(start_path=self.start_path) or {}
                setup_python_path()

            def ensure_env_var(
                self, var_name: str, required: bool = True
            ) -> str | None:
                value = os.environ.get(var_name)
                if required and not value:
                    msg = f"Required environment variable '{var_name}' is not set"
                    raise ValueError(msg)
                return value

            def is_initialized(self) -> bool:
                return True
else:
    # No common library available - use minimal implementation
    print("Warning: Miyabi common libraries not found", file=sys.stderr)
    COMMON_LIB_AVAILABLE = False

    class SkillBase:
        def __init__(self, skill_name: str, start_path: Path | None = None):
            self.skill_name = skill_name
            self.start_path = start_path or Path(__file__).resolve().parent

        def ensure_env_var(self, var_name: str, required: bool = True) -> str | None:
            value = os.environ.get(var_name)
            if required and not value:
                msg = f"Required environment variable '{var_name}' is not set"
                raise ValueError(msg)
            return value

        def is_initialized(self) -> bool:
            return True


from github_client import GitHubClient
from issue_analyzer import IssueAnalysis, IssueAnalyzer


class IssueImprover(SkillBase):
    """Main issue improvement orchestrator with enhanced common library integration"""

    def __init__(self, token: str | None = None, allow_read_only: bool = True):
        # Initialize skill base first
        super().__init__("github-issue-improver")

        # Ensure GitHub token is available
        if not token:
            try:
                token = self.ensure_env_var("GITHUB_TOKEN", required=False)
            except ValueError:
                if not allow_read_only:
                    msg = "GitHub token is required for write operations"
                    raise ValueError(msg)
                token = None

        # Initialize components
        self.github_client = GitHubClient(token, allow_read_only)
        self.analyzer = IssueAnalyzer()

        # Log initialization status
        # if self.is_initialized():
        #     self.log(f"Initialized successfully with common library support")
        # else:
        #     self.warn("Initialization completed with limited functionality")

        # Show diagnostics in debug mode
        if os.environ.get("DEBUG"):
            self.print_diagnostics()

    def improve_issue(
        self,
        repo: str,
        issue_number: int,
        update_title: bool = True,
        update_body: bool = True,
        update_labels: bool = True,
        mode: str = "update",
    ) -> dict[str, Any]:
        """
        Improve a GitHub issue

        Args:
            repo: Repository in format owner/repo
            issue_number: Issue number
            update_title: Whether to update the title
            update_body: Whether to update the body
            update_labels: Whether to update labels
            mode: 'update' to modify issue, 'comment' to add suggestion comment

        Returns:
            Dict with improvement results
        """
        try:
            # Get current issue
            issue = self.github_client.get_issue(repo, issue_number)

            # Analyze issue
            analysis = self.analyzer.analyze_issue(issue.title, issue.body)

            # Prepare improvements
            improvements = {
                "original_title": issue.title,
                "original_body": issue.body,
                "original_labels": issue.labels,
                "suggested_title": analysis.suggested_title,
                "suggested_body": analysis.suggested_body,
                "suggested_labels": analysis.suggested_labels,
                "analysis": {
                    "type": analysis.type.value,
                    "severity": analysis.severity.value,
                    "components": analysis.components,
                    "missing_info": analysis.missing_info,
                    "confidence_score": analysis.confidence_score,
                },
            }

            # Check if improvements are needed
            title_changed = analysis.suggested_title != issue.title
            body_changed = analysis.suggested_body != issue.body
            labels_changed = set(analysis.suggested_labels) != set(issue.labels)

            improvements["needs_improvement"] = (
                title_changed or body_changed or labels_changed
            )
            improvements["changes"] = {
                "title": title_changed,
                "body": body_changed,
                "labels": labels_changed,
            }

            if mode == "update":
                # Apply improvements
                if improvements["needs_improvement"]:
                    updated_issue = self._apply_improvements(
                        repo,
                        issue_number,
                        analysis,
                        update_title,
                        update_body,
                        update_labels,
                    )
                    improvements["updated"] = True
                    improvements["updated_issue"] = {
                        "title": updated_issue.title,
                        "body": updated_issue.body,
                        "labels": updated_issue.labels,
                    }
                else:
                    improvements["updated"] = False
                    improvements[
                        "message"
                    ] = "Issue is already well-structured. No changes needed."

            elif mode == "comment":
                # Add improvement suggestion as comment
                comment = self._generate_suggestion_comment(analysis, issue)
                comment_result = self.github_client.add_comment(
                    repo, issue_number, comment
                )
                improvements["comment_added"] = True
                improvements["comment_url"] = comment_result["html_url"]

            return improvements

        except Exception as e:
            return {"error": str(e), "repo": repo, "issue_number": issue_number}

    def _apply_improvements(
        self,
        repo: str,
        issue_number: int,
        analysis: IssueAnalysis,
        update_title: bool,
        update_body: bool,
        update_labels: bool,
    ):
        """Apply improvements to the issue"""
        title = analysis.suggested_title if update_title else None
        body = analysis.suggested_body if update_body else None
        labels = analysis.suggested_labels if update_labels else None

        return self.github_client.update_issue(repo, issue_number, title, body, labels)

    def _generate_suggestion_comment(self, analysis: IssueAnalysis, issue) -> str:
        """Generate improvement suggestion comment"""
        return f"""## 🔧 Issue Improvement Suggestions

**Analysis Confidence:** {analysis.confidence_score:.1%}

### **Suggested Title:**
```
{analysis.suggested_title}
```

### **Suggested Labels:**
{', '.join(f'`{label}`' for label in analysis.suggested_labels)}

### **Missing Information:**
{chr(10).join(f'- {info}' for info in analysis.missing_info) if analysis.missing_info else 'None - well documented!'}

### **Improved Description:**
{analysis.suggested_body}

---

*This comment was generated by GitHub Issue Improver skill to help create more actionable issues.*"""

    def batch_improve_issues(
        self, repo: str, issue_numbers: list, mode: str = "comment", **kwargs
    ) -> dict[str, Any]:
        """Improve multiple issues"""
        results = {"repo": repo, "total_issues": len(issue_numbers), "results": []}

        for issue_number in issue_numbers:
            result = self.improve_issue(repo, issue_number, mode=mode, **kwargs)
            results["results"].append({"issue_number": issue_number, "result": result})

        return results


def main():
    """CLI interface with enhanced diagnostics"""
    parser = argparse.ArgumentParser(
        description="GitHub Issue Improver - Automatically improve issue quality and structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview improvements (no token needed)
  python issue_improver.py --repo owner/repo --issue 123 --dry-run

  # Add suggestion comment
  python issue_improver.py --repo owner/repo --issue 123 --mode comment

  # Directly update issue (requires token)
  python issue_improver.py --repo owner/repo --issue 123 --mode update --update-title --update-body

  # Batch improve multiple issues
  python issue_improver.py --repo owner/repo --issues 123 124 125 --mode comment
        """,
    )

    parser.add_argument(
        "--repo",
        required=False,
        help="Repository in format owner/repo (not required for diagnostics)",
    )
    parser.add_argument("--issue", type=int, help="Single issue number to improve")
    parser.add_argument(
        "--issues", nargs="+", type=int, help="Multiple issue numbers to improve"
    )
    parser.add_argument(
        "--mode",
        choices=["update", "comment"],
        default="comment",
        help="How to apply improvements (update=modify issue, comment=add suggestion)",
    )
    parser.add_argument(
        "--update-title", action="store_true", help="Update issue title"
    )
    parser.add_argument("--update-body", action="store_true", help="Update issue body")
    parser.add_argument(
        "--update-labels", action="store_true", help="Update issue labels"
    )
    parser.add_argument(
        "--output", choices=["json", "text"], default="text", help="Output format"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without doing it",
    )
    parser.add_argument(
        "--token", help="GitHub token (optional, will also check .env file)"
    )
    parser.add_argument(
        "--diagnostics", action="store_true", help="Run diagnostics and exit"
    )
    parser.add_argument(
        "--verbose-diagnostics", action="store_true", help="Run verbose diagnostics"
    )

    args = parser.parse_args()

    # Handle diagnostics mode
    if args.diagnostics or args.verbose_diagnostics:
        try:
            if COMMON_LIB_AVAILABLE:
                diag = run_skill_diagnostics("github-issue-improver")
                diag.print_report(verbose=args.verbose_diagnostics)

                # Save diagnostic report
                report_file = Path("issue_improver_diagnostics.json")
                diag.save_report(report_file, verbose=args.verbose_diagnostics)
                print(f"\n📄 Diagnostic report saved to: {report_file}")
            else:
                print("❌ Diagnostics require common library support")
                print("Install Miyabi common libraries to enable diagnostics.")

        except Exception as e:
            print(f"❌ Diagnostic error: {e}")

        sys.exit(0)

    # For normal operation, repo is required
    if not args.repo:
        print(
            "Error: --repo is required for non-diagnostics operations", file=sys.stderr
        )
        sys.exit(1)

    if not args.issue and not args.issues:
        print("Error: Either --issue or --issues must be specified", file=sys.stderr)
        sys.exit(1)

    try:
        # Set read-only mode for dry-run
        allow_read_only = args.dry_run
        improver = IssueImprover(token=args.token, allow_read_only=allow_read_only)

        if args.issue:
            result = improver.improve_issue(
                args.repo,
                args.issue,
                update_title=args.update_title,
                update_body=args.update_body,
                update_labels=args.update_labels,
                mode="comment" if args.dry_run else args.mode,
            )

            if args.output == "json":
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print_improvement_result(args.issue, result)

        elif args.issues:
            results = improver.batch_improve_issues(
                args.repo,
                args.issues,
                mode="comment" if args.dry_run else args.mode,
                update_title=args.update_title,
                update_body=args.update_body,
                update_labels=args.update_labels,
            )

            if args.output == "json":
                print(json.dumps(results, indent=2, ensure_ascii=False))
            else:
                print_batch_results(results)

    except Exception as e:
        print(f"Error: {e}")
        if args.dry_run:
            print(
                "💡 Note: This is dry-run mode. Some features require GitHub token for full functionality."
            )
        sys.exit(1)


def print_improvement_result(issue_number: int, result: dict[str, Any]):
    """Print improvement result in human readable format"""
    if "error" in result:
        print(f"❌ Issue #{issue_number}: {result['error']}")
        return

    print(f"📋 Issue #{issue_number} Analysis")
    print(f"   Type: {result['analysis']['type']}")
    print(f"   Severity: {result['analysis']['severity']}")
    print(f"   Confidence: {result['analysis']['confidence_score']:.1%}")

    if result.get("needs_improvement"):
        print("   ✨ Improvements suggested:")
        if result["changes"]["title"]:
            print(f"     📝 Title: {result['suggested_title']}")
        if result["changes"]["body"]:
            print("     📄 Body: Updated with structure")
            if len(result["suggested_body"]) > 200:
                print(f"     Preview: {result['suggested_body'][:200]}...")
        if result["changes"]["labels"]:
            print(f"     🏷️  Labels: {', '.join(result['suggested_labels'])}")
    else:
        print("   ✅ Issue is already well-structured")

    if result.get("comment_added"):
        print(f"   💬 Suggestion comment added: {result['comment_url']}")

    if result.get("updated"):
        print("   🔄 Issue updated successfully")

    print()


def print_batch_results(results: dict[str, Any]):
    """Print batch improvement results"""
    print(f"🔧 Batch Improvement Results for {results['repo']}")
    print(f"   Total Issues: {results['total_issues']}")
    print()

    for item in results["results"]:
        issue_number = item["issue_number"]
        result = item["result"]
        print_improvement_result(issue_number, result)


if __name__ == "__main__":
    main()
