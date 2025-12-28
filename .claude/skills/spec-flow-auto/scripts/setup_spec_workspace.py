#!/usr/bin/env python3
"""
Spec Workflow - SPECワークスペースを初期化するスクリプト

SpecWorkflowMcpで必要なディレクトリ構造と設定ファイルを自動生成
"""

import argparse
import json
import sys
from pathlib import Path


class SpecWorkspaceSetup:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.spec_workflow_dir = self.project_root / ".spec-workflow"
        self.specs_dir = self.spec_workflow_dir / "specs"
        self.logs_dir = self.spec_workflow_dir / "logs"

    def setup_workspace(self) -> bool:
        """ワークスペースをセットアップ"""
        print(f"🚀 Setting up SpecWorkflow workspace in {self.project_root}")

        try:
            # ディレクトリ構造作成
            self._create_directory_structure()

            # 設定ファイル生成
            self._create_config_files()

            # Git無視設定
            self._setup_git_ignore()

            print("✅ SpecWorkflow workspace setup completed!")
            print(f"📁 Workspace: {self.spec_workflow_dir}")
            return True

        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False

    def _create_directory_structure(self) -> None:
        """ディレクトリ構造を作成"""
        print("📁 Creating directory structure...")

        directories = [
            self.spec_workflow_dir,
            self.specs_dir,
            self.logs_dir,
            self.spec_workflow_dir / "approval-requests",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"   Created: {directory}")

    def _create_config_files(self) -> None:
        """設定ファイルを生成"""
        print("⚙️ Creating configuration files...")

        # spec-workflow.json
        config = {
            "version": "1.0.0",
            "workflowType": "spec-workflow",
            "projectRoot": str(self.project_root),
            "specsDirectory": str(self.specs_dir),
            "logsDirectory": str(self.logs_dir),
            "createdAt": str(Path.cwd()),
            "settings": {
                "autoSave": True,
                "generateApprovalRequests": True,
                "validateOnSave": True,
            },
        }

        config_file = self.spec_workflow_dir / "spec-workflow.json"
        config_file.write_text(
            json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"   Created: {config_file}")

        # README.md
        readme_content = """# Spec Workflow Workspace

This directory contains the Spec Workflow configuration and generated specifications.

## Directory Structure

```
.spec-workflow/
├── spec-workflow.json    # Main configuration file
├── specs/                # Generated specifications
│   └── [spec-name]/
│       ├── requirements.md
│       ├── design.md
│       └── tasks.md
├── logs/                 # Workflow logs
└── approval-requests/     # Approval request metadata
```

## Usage

1. **Create new specification**:
   ```
   "Create a spec from the PRD in README.md"
   ```

2. **Implement tasks**:
   ```
   "Implement the tasks in .spec-workflow/specs/[spec-name]/tasks.md"
   ```

3. **Check status**:
   ```
   /miyabi-status
   ```

## Integration with Miyabi Framework

This workspace is designed to work seamlessly with the Miyabi framework's autonomous agents:

- **IssueAgent**: Manages specification-related issues
- **CodeGenAgent**: Implements generated tasks
- **TestAgent**: Validates implementation
- **ReviewAgent**: Ensures quality standards

For more information, see the [SpecWorkflowMcp documentation](https://github.com/Pimzino/spec-workflow-mcp).
"""

        readme_file = self.spec_workflow_dir / "README.md"
        readme_file.write_text(readme_content, encoding="utf-8")
        print(f"   Created: {readme_file}")

    def _setup_git_ignore(self) -> None:
        """Git ignore設定"""
        print("🚫 Setting up git ignore...")

        gitignore_file = self.spec_workflow_dir / ".gitignore"
        gitignore_content = """# Spec Workflow ignore patterns

# Logs
logs/
*.log

# Temporary files
*.tmp
*.temp

# Approval request metadata (may contain sensitive info)
approval-requests/*.json

# IDE files
.vscode/
.idea/

# OS files
.DS_Store
Thumbs.db
"""

        gitignore_file.write_text(gitignore_content, encoding="utf-8")
        print(f"   Created: {gitignore_file}")


def main():
    parser = argparse.ArgumentParser(description="Setup SpecWorkflow workspace")
    parser.add_argument("--project-root", default=".", help="Project root directory")

    args = parser.parse_args()

    setup = SpecWorkspaceSetup(args.project_root)
    success = setup.setup_workspace()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
