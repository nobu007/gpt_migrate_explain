#!/usr/bin/env python3
"""Code Review Agent - Automatically reviews Pull Requests using Claude"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# --- Common Library Setup ---


def setup_common_library():
    """Setup common library path and imports"""
    # Find and setup common library path
    current = Path(__file__).resolve()
    for _ in range(10):  # Search up to 10 levels
        claude_lib = current / ".claude" / "lib"
        if claude_lib.exists():
            if str(claude_lib) not in sys.path:
                sys.path.insert(0, str(claude_lib))
            break
        current = current.parent
        if current == current.parent:  # Filesystem root reached
            break


# Setup common library
setup_common_library()

# Try to import GitHubClient from common lib
try:
    from python.github_client import GitHubClient

    COMMON_LIB_AVAILABLE = True
except ImportError:
    COMMON_LIB_AVAILABLE = False
    # We will fallback to internal implementation if needed,
    # but for now let's just fail if we can't find it since we just created it
    # print("Warning: Could not import GitHubClient from common library")

# If still not available (e.g. path issue), define minimal one or fail
if "GitHubClient" not in locals():
    try:
        # Try importing from local file if in same dir (unlikely)
        from github_client import GitHubClient
    except ImportError:
        # Fallback: Re-implement minimal GitHubClient or import it from relative path
        # For this refactor, we assume the common lib is set up correctly.
        pass


# --- Code Reviewer ---


@dataclass
class ReviewComment:
    path: str
    line: int
    body: str
    priority: str  # 'high', 'medium', 'low'


@dataclass
class ReviewResult:
    summary: str
    comments: list[ReviewComment]
    score: int  # 0-100
    decision: str  # 'approve', 'request_changes', 'comment'


class CodeReviewer:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        if not api_key:
            msg = "ANTHROPIC_API_KEY is required"
            raise ValueError(msg)

        # Import here to avoid dependency if not used
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def review_diff(self, diff: str, pr_details: dict[str, Any]) -> ReviewResult:
        # Truncate diff if too large
        if len(diff) > 80000:
            diff = diff[:80000] + "\n... [Diff truncated due to length]"

        prompt = f"""You are an expert Senior Software Engineer performing a code review.
Review the following Pull Request.

**Title:** {pr_details.get('title')}
**Description:** {pr_details.get('body')}
**Repository:** {pr_details.get('base', {}).get('repo', {}).get('full_name')}

**Diff:**
```diff
{diff}
```

**Instructions:**
1. Analyze the code for bugs, security vulnerabilities, performance issues, and code quality.
2. Provide specific comments on specific lines if possible.
3. Provide a summary of the changes and the overall quality.
4. Assign a quality score (0-100). 80+ is passing.
5. Recommend a decision: 'approve', 'request_changes', or 'comment'.

**Output Format:**
Respond with ONLY valid JSON in the following format:
{{
  "summary": "Overall summary of the review...",
  "score": 85,
  "decision": "approve",
  "comments": [
    {{
      "path": "src/utils.ts",
      "line": 45,
      "body": "This function is not handling null values correctly.",
      "priority": "high"
    }}
  ]
}}

Notes:
- If you cannot identify specific lines easily from the diff, put comments in the summary or use line 1 of the file.
- Be constructive and professional.
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            content = response.content[0].text.strip()
            # Extract JSON
            json_match = re.search(r"\{[\s\S]*\}", content)
            data = json.loads(json_match.group()) if json_match else json.loads(content)

            comments = []
            for c in data.get("comments", []):
                comments.append(
                    ReviewComment(
                        path=c["path"],
                        line=c.get("line", 1),
                        body=c["body"],
                        priority=c.get("priority", "medium"),
                    )
                )

            return ReviewResult(
                summary=data.get("summary", "No summary provided"),
                comments=comments,
                score=data.get("score", 0),
                decision=data.get("decision", "comment"),
            )

        except Exception as e:
            print(f"Error during Claude review: {e}")
            return ReviewResult(
                summary=f"Review failed: {str(e)}",
                comments=[],
                score=0,
                decision="comment",
            )


def main():
    parser = argparse.ArgumentParser(description="Code Review Agent")
    parser.add_argument("--repo", required=True, help="Repository owner/name")
    parser.add_argument("--pr", type=int, help="PR number")
    parser.add_argument("--issue", type=int, help="Issue/PR number (alias for --pr)")
    parser.add_argument("--token", help="GitHub Token")
    parser.add_argument("--output", choices=["json", "text"], default="text")
    parser.add_argument("--dry-run", action="store_true", help="Do not post comments")

    # Compatibility args for runtime
    parser.add_argument(
        "--update-title", action="store_true", help="Ignored (compatibility)"
    )
    parser.add_argument(
        "--update-body", action="store_true", help="Ignored (compatibility)"
    )

    args = parser.parse_args()

    pr_number = args.pr or args.issue
    if not pr_number:
        print("Error: Either --pr or --issue is required")
        sys.exit(1)

    try:
        # Allow allow_read_only to be passed if the shared client supports it
        gh = GitHubClient(token=args.token, allow_read_only=args.dry_run)
        reviewer = CodeReviewer()

        # 1. Fetch PR details
        pr = gh.get_pr(args.repo, pr_number)
        print(f"Reviewing PR #{pr_number}: {pr['title']}")

        # 2. Fetch Diff
        diff = gh.get_pr_diff(args.repo, pr_number)
        if not diff:
            print("Empty diff, nothing to review.")
            return

        # 3. Review
        result = reviewer.review_diff(diff, pr)

        # 4. Output
        if args.output == "json":
            output_data = {
                "summary": result.summary,
                "score": result.score,
                "decision": result.decision,
                "comments": [
                    {
                        "path": c.path,
                        "line": c.line,
                        "body": c.body,
                        "priority": c.priority,
                    }
                    for c in result.comments
                ],
            }
            print(json.dumps(output_data, indent=2))
        else:
            print(f"\n📊 Score: {result.score}/100 ({result.decision})")
            print(f"📝 Summary:\n{result.summary}\n")
            if result.comments:
                print(f"💬 Comments ({len(result.comments)}):")
                for c in result.comments:
                    print(f"  - {c.path}:{c.line} [{c.priority.upper()}] {c.body}")

        # 5. Post comments (if not dry run)
        if not args.dry_run:
            print("\nPosting comments to GitHub...")
            # Post summary
            summary_body = f"## 🤖 AI Code Review\n\n**Score:** {result.score}/100\n**Decision:** {result.decision.upper()}\n\n{result.summary}"
            gh.create_general_comment(args.repo, pr_number, summary_body)

            # Post inline comments (limited to avoid spam)
            # Note: Need commit_id for inline comments. usually pr['head']['sha']
            commit_id = pr["head"]["sha"]
            count = 0
            for c in result.comments:
                if count >= 10:  # Limit max comments
                    break
                try:
                    # Only post high priority or if few comments
                    if c.priority == "high" or len(result.comments) < 5:
                        gh.create_review_comment(
                            args.repo, pr_number, c.body, commit_id, c.path, c.line
                        )
                        count += 1
                except Exception as e:
                    print(f"Failed to post comment on {c.path}:{c.line}: {e}")

            print(f"Posted {count} inline comments and 1 summary.")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
