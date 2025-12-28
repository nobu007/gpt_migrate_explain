#!/usr/bin/env python3
"""
Agent Generator - Creates specialized agents from templates

This script generates new agent definition files (.md) based on parameters,
following the Miyabi framework patterns for autonomous agents.
"""

import argparse
import sys
from pathlib import Path
from typing import Any

from agent_workflows import AgentWorkflows


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


class AgentTemplate:
    """Base template for agent creation"""

    def __init__(self):
        self.templates = {
            "code-review": {
                "description": "Comprehensive code review specialist covering architecture, code quality, security, performance, testing, and documentation",
                "capabilities": [
                    "Architecture & design analysis",
                    "Code quality assessment",
                    "Security vulnerability detection",
                    "Performance & scalability evaluation",
                    "Testing coverage analysis",
                    "Documentation & API design review",
                ],
                "tools": ["Read", "Grep", "Glob", "Bash", "Edit"],
            },
            "deployment": {
                "description": "CI/CD automation specialist with deployment pipeline management",
                "capabilities": [
                    "Automated deployment execution",
                    "Health check monitoring",
                    "Automatic rollback functionality",
                    "Environment configuration management",
                    "Deployment validation",
                ],
                "tools": ["Bash", "Read", "Grep", "WebFetch"],
            },
            "testing": {
                "description": "Test automation and coverage analysis specialist",
                "capabilities": [
                    "Automated test execution",
                    "Coverage report generation",
                    "Test result analysis",
                    "Quality assurance validation",
                    "Performance testing",
                ],
                "tools": ["Bash", "Read", "Grep", "Glob", "Edit"],
            },
            "documentation": {
                "description": "Documentation generation and maintenance specialist",
                "capabilities": [
                    "API documentation generation",
                    "README creation",
                    "Code documentation analysis",
                    "Technical writing assistance",
                    "Documentation maintenance",
                ],
                "tools": ["Read", "Grep", "Glob", "Write", "Edit"],
            },
            "security": {
                "description": "Security analysis and vulnerability assessment specialist",
                "capabilities": [
                    "Security vulnerability scanning",
                    "OWASP Top 10 analysis",
                    "Code security review",
                    "Dependency security analysis",
                    "Security best practices validation",
                ],
                "tools": ["Read", "Grep", "Glob", "Bash", "WebSearch"],
            },
            "general-purpose": {
                "description": "General-purpose agent for research and complex multi-step tasks",
                "capabilities": [
                    "Complex research tasks",
                    "Information gathering",
                    "Multi-step task coordination",
                    "Problem analysis",
                    "Solution development",
                ],
                "tools": ["*"],  # All tools available
            },
        }

    def get_template(self, agent_type: str) -> dict[str, Any] | None:
        """Get agent template by type"""
        return self.templates.get(agent_type)

    def list_templates(self) -> list[str]:
        """List available agent templates"""
        return list(self.templates.keys())


class AgentGenerator:
    """Generates agent definition files from templates and parameters"""

    def __init__(self):
        self.template = AgentTemplate()
        self.base_path = self.find_agents_directory()

    def find_agents_directory(self) -> Path | None:
        """Find the .claude/agents directory"""
        current = Path(__file__).resolve()
        for _ in range(10):  # Search up to 10 levels
            agents_dir = current / ".claude" / "agents"
            if agents_dir.exists():
                return agents_dir
            current = current.parent
            if current == current.parent:  # Filesystem root reached
                break
        return None

    def generate_agent_md(
        self,
        name: str,
        agent_type: str,
        custom_description: str | None = None,
        custom_capabilities: list[str] | None = None,
        tools: list[str] | None = None,
        workflow_instructions: str | None = None,
    ) -> str:
        """Generate agent definition markdown content"""
        template = self.template.get_template(agent_type)
        if not template:
            msg = f"Unknown agent type: {agent_type}"
            raise ValueError(msg)

        # Use custom values if provided, otherwise use template defaults
        description = custom_description or template["description"]
        capabilities = custom_capabilities or template["capabilities"]
        tool_list = tools or template["tools"]

        # Build workflow instructions based on agent type
        if not workflow_instructions:
            workflow_instructions = AgentWorkflows.get_workflow(agent_type)

        # Assemble markdown sections
        sections = [
            self._generate_header(name, description),
            self._generate_capabilities(capabilities),
            self._generate_tools(tool_list),
            self._generate_workflow(workflow_instructions),
            self._generate_usage(capabilities),
            self._generate_integration(),
            self._generate_quality(),
            self._generate_footer(),
        ]

        return "\n".join(sections)

    def _generate_header(self, name: str, description: str) -> str:
        return f"""# {name.replace('-', ' ').title()} Agent

> {description}
"""

    def _generate_capabilities(self, capabilities: list[str]) -> str:
        content = "## Capabilities\n\n"
        for capability in capabilities:
            content += f"- {capability}\n"
        return content

    def _generate_tools(self, tools: list[str]) -> str:
        content = """
## Tool Access

This agent has access to the following tools:

"""
        for tool in tools:
            content += f"- {tool}\n"
        return content

    def _generate_workflow(self, instructions: str) -> str:
        return f"""
## Workflow Instructions

{instructions}
"""

    def _generate_usage(self, capabilities: list[str]) -> str:
        content = """
## Usage Patterns

### When to Use This Agent

Use this agent when you need to:

"""
        for capability in capabilities:
            content += f"- {capability.lower()}\n"

        content += """
### Typical Workflow

1. **Initial Assessment**: Analyze the current state and requirements
2. **Execution**: Apply specialized expertise using available tools
3. **Validation**: Verify results meet quality standards
4. **Reporting**: Provide clear recommendations and next steps
"""
        return content

    def _generate_integration(self) -> str:
        return """
## Integration with Miyabi Framework

This agent integrates with the Miyabi framework through:

- **CoordinatorAgent**: Task delegation and orchestration
- **Issue Management**: Automatic issue assignment and status tracking
- **Quality Gates**: 80+ quality score requirement for progression
- **Documentation**: Automatic logging of actions and decisions
"""

    def _generate_quality(self) -> str:
        return """
## Quality Standards

- Maintain 80+ quality score in reviews
- Provide clear, actionable feedback
- Follow established coding standards
- Document all significant decisions
- Ensure security best practices
"""

    def _generate_footer(self) -> str:
        return """
---

*Generated with agent-creator skill*
"""


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

    parser = argparse.ArgumentParser(
        description="Generate specialized agents from templates"
    )
    parser.add_argument("name", help="Agent name (e.g., 'code-review-expert')")
    parser.add_argument(
        "type",
        choices=[
            "code-review",
            "deployment",
            "testing",
            "documentation",
            "security",
            "general-purpose",
        ],
        help="Agent type template",
    )
    parser.add_argument("--description", help="Custom description for the agent")
    parser.add_argument("--capabilities", nargs="*", help="Custom capabilities list")
    parser.add_argument("--tools", nargs="*", help="Custom tools list")
    parser.add_argument("--workflow", help="Custom workflow instructions")
    parser.add_argument(
        "--list-templates", action="store_true", help="List available agent templates"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Generate content without saving to file"
    )

    args = parser.parse_args()

    if args.list_templates:
        generator = AgentGenerator()
        templates = generator.template.list_templates()
        print("Available agent templates:")
        for template in templates:
            print(f"  - {template}")
        return

    try:
        generator = AgentGenerator()

        if args.dry_run:
            content = generator.generate_agent_md(
                args.name,
                args.type,
                args.description,
                args.capabilities,
                args.tools,
                args.workflow,
            )
            print("=" * 60)
            print(f"Generated content for {args.name}:")
            print("=" * 60)
            print(content)
        else:
            agent_file = generator.save_agent(
                args.name,
                generator.generate_agent_md(
                    args.name,
                    args.type,
                    args.description,
                    args.capabilities,
                    args.tools,
                    args.workflow,
                ),
            )

            if agent_file:
                print(f"\n🤖 Agent '{args.name}' created successfully!")
                print(f"📍 Location: {agent_file}")
                print(f"🎯 Type: {args.type}")
                print("\nTo use this agent:")
                print("  1. Restart Claude Code to load the new agent")
                print(f"  2. Use with: Task tool and subagent_type='{args.name}'")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
