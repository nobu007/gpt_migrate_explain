#!/usr/bin/env python3
"""
GitHub API client for issue management
Enhanced with common library integration and improved environment handling
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


# Try to load common library for enhanced environment handling
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


# Try to setup common library
setup_common_library()

# Try to import from common library
try:
    from python.github_client import GitHubClient as SharedGitHubClient
    from python.github_client import Issue as SharedIssue

    COMMON_LIB_AVAILABLE = True

    # Re-export
    GitHubClient = SharedGitHubClient
    Issue = SharedIssue

except ImportError:
    COMMON_LIB_AVAILABLE = False

    # Check env_utils if available
    try:
        from env_utils import load_env_files

        ENV_UTILS_AVAILABLE = True
    except ImportError:
        ENV_UTILS_AVAILABLE = False
        # Fallback to python-dotenv
        try:
            from dotenv import load_dotenv

            DOTENV_AVAILABLE = True
        except ImportError:
            DOTENV_AVAILABLE = False
            load_dotenv = None

    @dataclass
    class Issue:
        """Issue data structure"""

        number: int
        title: str
        body: str
        state: str
        labels: list[str]
        assignees: list[str]
        html_url: str
        repository: str

    class GitHubClient:
        """GitHub API client for issue operations"""

        def __init__(self, token: str | None = None, allow_read_only: bool = True):
            # Load .env files from multiple locations
            self._load_env_files()

            # Try to get token from multiple sources
            self.token = self._get_token(token)
            self.allow_read_only = allow_read_only

            if not self.token and not self.allow_read_only:
                msg = (
                    "GitHub token is required. Set GITHUB_TOKEN environment variable, "
                    "create a .env file with GITHUB_TOKEN, or use --dry-run mode."
                )
                raise ValueError(msg)

            self.headers = {
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            }

            if self.token:
                self.headers["Authorization"] = f"token {self.token}"

            self.base_url = "https://api.github.com"

        def _load_env_files(self) -> None:
            """Load .env files from multiple locations using common library if available"""
            if ENV_UTILS_AVAILABLE:
                # Use enhanced environment loading
                try:
                    env_result = load_env_files(start_path=Path(__file__).parent)
                    self._env_info = env_result
                    return
                except Exception:
                    pass

            # Fallback to original method
            if not DOTENV_AVAILABLE:
                self._env_info = {"method": "none", "loaded_files": []}
                return

            # Priority order for .env files
            env_locations = [
                Path(__file__).parent / ".env",
                Path.cwd() / ".env",
                Path.cwd().parent / ".env",
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

            self._env_info = {"method": "python-dotenv", "loaded_files": loaded_files}

        def _get_token(self, token: str | None = None) -> str | None:
            sources = [
                lambda: token,
                lambda: os.getenv("GITHUB_TOKEN"),
            ]
            for source in sources:
                try:
                    result = source()
                    if result and result.strip():
                        return result.strip()
                except Exception:
                    continue
            return None

        def get_issue(self, repo: str, issue_number: int) -> Issue:
            if not self.token or self.allow_read_only:
                return Issue(
                    number=issue_number,
                    title=f"Issue #{issue_number} (dry-run mode - would fetch from GitHub)",
                    body="Dry run: Would fetch actual issue content from GitHub",
                    state="open",
                    labels=[],
                    assignees=[],
                    html_url=f"https://github.com/{repo}/issues/{issue_number}",
                    repository=repo,
                )

            url = f"{self.base_url}/repos/{repo}/issues/{issue_number}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            return Issue(
                number=data["number"],
                title=data["title"],
                body=data.get("body", ""),
                state=data["state"],
                labels=[label["name"] for label in data.get("labels", [])],
                assignees=[assignee["login"] for assignee in data.get("assignees", [])],
                html_url=data["html_url"],
                repository=repo,
            )

        def update_issue(
            self,
            repo: str,
            issue_number: int,
            title: str = None,
            body: str = None,
            labels: list[str] = None,
            assignees: list[str] = None,
        ) -> Issue:
            if not self.token:
                if self.allow_read_only:
                    msg = "GitHub token required for issue updates. This is dry-run mode - use --dry-run to preview changes only."
                    raise ValueError(msg)
                msg = "GitHub token is required. Set GITHUB_TOKEN environment variable."
                raise ValueError(msg)

            url = f"{self.base_url}/repos/{repo}/issues/{issue_number}"

            data = {}
            if title is not None:
                data["title"] = title
            if body is not None:
                data["body"] = body
            if labels is not None:
                data["labels"] = labels
            if assignees is not None:
                data["assignees"] = assignees

            response = requests.patch(url, headers=self.headers, json=data)
            response.raise_for_status()

            return self.get_issue(repo, issue_number)

        def add_comment(
            self, repo: str, issue_number: int, body: str
        ) -> dict[str, Any]:
            if self.allow_read_only:
                return {
                    "id": f"dry-run-{issue_number}",
                    "html_url": f"https://github.com/{repo}/issues/{issue_number}#issuecomment-dry-run",
                    "body": body,
                }

            if not self.token:
                msg = "GitHub token is required. Set GITHUB_TOKEN environment variable."
                raise ValueError(msg)

            url = f"{self.base_url}/repos/{repo}/issues/{issue_number}/comments"
            data = {"body": body}

            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()

        def get_repo_labels(self, repo: str) -> list[dict[str, Any]]:
            url = f"{self.base_url}/repos/{repo}/labels"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()


if __name__ == "__main__":
    # CLI interface for testing
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Issue Client")
    parser.add_argument("--repo", required=True, help="Repository in format owner/repo")
    parser.add_argument("--issue", type=int, required=True, help="Issue number")
    parser.add_argument(
        "--action", choices=["get", "comment"], default="get", help="Action to perform"
    )
    parser.add_argument("--message", help="Comment message (for comment action)")

    args = parser.parse_args()

    try:
        client = GitHubClient()

        if args.action == "get":
            issue = client.get_issue(args.repo, args.issue)
            print(f"Issue #{issue.number}: {issue.title}")
            print(f"State: {issue.state}")
            print(f"Labels: {', '.join(issue.labels)}")
            print(f"Body:\n{issue.body}")

        elif args.action == "comment":
            if not args.message:
                print("Error: --message is required for comment action")
                exit(1)
            result = client.add_comment(args.repo, args.issue, args.message)
            print(f"Comment added: {result['html_url']}")

    except Exception as e:
        print(f"Error: {e}")
        exit(1)
