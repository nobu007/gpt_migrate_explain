#!/usr/bin/env python3
"""
Agent Definition Validator

Validates agent definition files for proper structure and content.
"""

import argparse
import re
import sys
from pathlib import Path


# Setup common library access for Miyabi skills (dynamic discovery)
def find_claude_lib():
    current = Path(__file__).resolve()
    for _ in range(8):  # Search up to 8 levels
        claude_lib = current / ".claude" / "lib"
        if claude_lib.exists():
            return str(claude_lib)
        current = current.parent
        if current == current.parent:  # Filesystem root reached
            break
    return None  # Not found


class AgentValidator:
    """Validates agent definition files"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []

    def validate_agent_file(self, file_path: Path) -> bool:
        """Validate a single agent definition file"""
        self.errors.clear()
        self.warnings.clear()
        self.info.clear()

        print(f"🔍 Validating agent: {file_path.name}")

        # Check if file exists
        if not file_path.exists():
            self.errors.append(f"Agent file does not exist: {file_path}")
            return False

        # Check file extension
        if file_path.suffix != ".md":
            self.errors.append("Agent file must have .md extension")
            return False

        # Read file content
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"Could not read file: {e}")
            return False

        # Validate content structure
        self._validate_structure(content)
        self._validate_required_sections(content)
        self._validate_tool_references(content)
        self._validate_workflow_instructions(content)

        # Print results
        self._print_results()

        return len(self.errors) == 0

    def _validate_structure(self, content: str):
        """Validate basic markdown structure"""
        lines = content.split("\n")

        # Check for title
        if not lines or not lines[0].startswith("# "):
            self.errors.append("Missing or invalid title (must start with '# ')")
        else:
            title = lines[0][2:].strip()
            if not title:
                self.errors.append("Title cannot be empty")
            elif "agent" not in title.lower():
                self.warnings.append("Title should contain 'Agent' for clarity")

        # Check for description blockquote
        if "> " not in content:
            self.warnings.append("Consider adding a description using blockquote (> )")

        # Check for empty lines
        consecutive_empty = 0
        for i, line in enumerate(lines):
            if not line.strip():
                consecutive_empty += 1
                if consecutive_empty > 3:
                    self.warnings.append(
                        f"Too many consecutive empty lines at line {i+1}"
                    )
                    break
            else:
                consecutive_empty = 0

    def _validate_required_sections(self, content: str):
        """Validate required sections are present"""
        required_sections = [
            "## Capabilities",
            "## Tool Access",
            "## Workflow Instructions",
            "## Usage Patterns",
        ]

        for section in required_sections:
            if section not in content:
                self.errors.append(f"Missing required section: {section}")

        # Check for recommended sections
        recommended_sections = [
            "## When to Use This Agent",
            "## Typical Workflow",
            "## Integration with Miyabi Framework",
            "## Quality Standards",
        ]

        for section in recommended_sections:
            if section not in content:
                self.warnings.append(f"Missing recommended section: {section}")

    def _validate_tool_references(self, content: str):
        """Validate tool references in Tool Access section"""
        # Extract tool access section
        tool_match = re.search(
            r"## Tool Access\n\n(.*?)(?=\n## |\n$)", content, re.DOTALL
        )
        if not tool_match:
            self.errors.append("Could not find Tool Access section")
            return

        tools_content = tool_match.group(1)

        # Look for tool list items
        tool_lines = [
            line.strip()
            for line in tools_content.split("\n")
            if line.strip().startswith("- ")
        ]

        if not tool_lines:
            self.errors.append("No tools listed in Tool Access section")
            return

        valid_tools = [
            "Read",
            "Write",
            "Edit",
            "Glob",
            "Grep",
            "Bash",
            "WebSearch",
            "WebFetch",
            "TodoWrite",
            "AskUserQuestion",
            "ExitPlanMode",
            "SlashCommand",
            "Skill",
            "Task",
            "mcp__ide__getDiagnostics",
            "mcp__ide__executeCode",
            "mcp__spec-workflow__spec-workflow-guide",
            "mcp__spec-workflow__steering-guide",
            "mcp__spec-workflow__spec-status",
            "mcp__spec-workflow__approvals",
            "mcp__spec-workflow__log-implementation",
        ]

        for line in tool_lines:
            tool_name = line[2:].strip()  # Remove "- " prefix
            if tool_name == "*":
                self.info.append("Agent has access to all tools (*)")
                continue

            if tool_name not in valid_tools:
                self.warnings.append(f"Unknown tool reference: {tool_name}")

        self.info.append(f"Found {len(tool_lines)} tool(s) in access list")

    def _validate_workflow_instructions(self, content: str):
        """Validate workflow instructions quality"""
        # Extract workflow instructions section
        workflow_match = re.search(
            r"## Workflow Instructions\n\n(.*?)(?=\n## |\n$)", content, re.DOTALL
        )
        if not workflow_match:
            self.errors.append("Could not find Workflow Instructions section")
            return

        workflow_content = workflow_match.group(1)

        # Check for actionable instructions
        if len(workflow_content.strip()) < 100:
            self.warnings.append("Workflow instructions seem too short")

        # Look for numbered steps or bullet points
        has_steps = bool(re.search(r"\n\d+\.", workflow_content)) or bool(
            re.search(r"\n- ", workflow_content)
        )
        if not has_steps:
            self.warnings.append(
                "Consider using numbered steps or bullet points in workflow"
            )

        # Check for specific action verbs
        action_verbs = [
            "analyze",
            "check",
            "validate",
            "review",
            "execute",
            "perform",
            "identify",
            "assess",
        ]
        has_actions = any(verb in workflow_content.lower() for verb in action_verbs)
        if not has_actions:
            self.warnings.append(
                "Include specific action verbs in workflow instructions"
            )

        # Check for examples or patterns
        if "example" not in workflow_content.lower():
            self.warnings.append("Consider including examples in workflow instructions")

    def _print_results(self):
        """Print validation results"""
        if self.info:
            print("ℹ️  Information:")
            for info in self.info:
                print(f"   {info}")

        if self.warnings:
            print("⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   {warning}")

        if self.errors:
            print("❌ Errors:")
            for error in self.errors:
                print(f"   {error}")
        else:
            print("✅ Agent definition is valid!")

        # Summary
        total_issues = len(self.warnings) + len(self.errors)
        if total_issues == 0:
            print("\n🎉 Perfect! No issues found.")
        else:
            print(
                f"\n📊 Summary: {len(self.errors)} error(s), {len(self.warnings)} warning(s)"
            )


def validate_directory(agents_dir: Path):
    """Validate all agent files in a directory"""
    if not agents_dir.exists():
        print(f"❌ Agents directory does not exist: {agents_dir}")
        return False

    agent_files = list(agents_dir.glob("*.md"))
    agent_files = [f for f in agent_files if f.name != "README.md"]

    if not agent_files:
        print("📭 No agent files found to validate")
        return True

    print(f"🔍 Found {len(agent_files)} agent file(s) to validate\n")

    all_valid = True
    for agent_file in sorted(agent_files):
        validator = AgentValidator()
        is_valid = validator.validate_agent_file(agent_file)
        if not is_valid:
            all_valid = False
        print()  # Add spacing between agents

    return all_valid


def main():
    # Load environment and setup Python path
    claude_lib_path = find_claude_lib()
    if claude_lib_path:
        sys.path.insert(0, claude_lib_path)
        try:
            from env_utils import load_env_files, setup_python_path

            setup_python_path()
            load_env_files()
            print("Environment setup complete")
        except ImportError:
            print("Warning: Could not import Miyabi common libraries")
    else:
        import warnings

        warnings.warn("Miyabi common libraries not found", stacklevel=2)

    parser = argparse.ArgumentParser(description="Validate agent definition files")
    parser.add_argument("agent_file", nargs="?", help="Specific agent file to validate")
    parser.add_argument(
        "--all", action="store_true", help="Validate all agents in the directory"
    )
    parser.add_argument(
        "--directory", help="Agents directory path (default: .claude/agents)"
    )

    args = parser.parse_args()

    if args.agent_file:
        # Validate specific file
        agent_path = Path(args.agent_file)
        if not agent_path.is_absolute():
            # Try relative to current directory or agents directory
            if args.directory:
                agent_path = Path(args.directory) / agent_path
            else:
                # Look in .claude/agents
                current = Path.cwd()
                for _ in range(10):
                    agents_dir = current / ".claude" / "agents"
                    if agents_dir.exists():
                        agent_path = agents_dir / agent_path
                        break
                    current = current.parent
                    if current == current.parent:
                        break

        validator = AgentValidator()
        success = validator.validate_agent_file(agent_path)
        sys.exit(0 if success else 1)

    elif args.all:
        # Validate all agents
        if args.directory:
            agents_dir = Path(args.directory)
        else:
            # Find .claude/agents directory
            current = Path.cwd()
            agents_dir = None
            for _ in range(10):
                found_agents_dir = current / ".claude" / "agents"
                if found_agents_dir.exists():
                    agents_dir = found_agents_dir
                    break
                current = current.parent
                if current == current.parent:
                    break

            if not agents_dir:
                print("❌ Could not find .claude/agents directory")
                print("Use --directory to specify the path")
                sys.exit(1)

        success = validate_directory(agents_dir)
        sys.exit(0 if success else 1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
