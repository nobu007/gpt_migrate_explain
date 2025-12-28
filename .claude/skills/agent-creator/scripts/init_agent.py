#!/usr/bin/env python3
"""
Agent Directory Initialization Tool

Sets up the .claude/agents directory structure if it doesn't exist,
and creates basic configuration files.
"""

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


def find_agents_directory():
    """Find or create the .claude/agents directory"""
    current = Path(__file__).resolve()

    # Search for .claude directory
    for _ in range(10):  # Search up to 10 levels
        claude_dir = current / ".claude"
        if claude_dir.exists():
            agents_dir = claude_dir / "agents"
            return agents_dir, claude_dir
        current = current.parent
        if current == current.parent:  # Filesystem root reached
            break

    return None, None


def create_agents_directory():
    """Create the agents directory and basic structure"""
    agents_dir, claude_dir = find_agents_directory()

    if not claude_dir:
        print("❌ Error: Could not find .claude directory")
        print("Please run this from within a Claude Code project")
        return False

    if agents_dir.exists():
        print(f"✅ Agents directory already exists: {agents_dir}")
        return True

    # Create the agents directory
    agents_dir.mkdir(exist_ok=True)
    print(f"✅ Created agents directory: {agents_dir}")

    # Create a README file in the agents directory
    readme_content = """# Agents Directory

This directory contains specialized agent definitions for Claude Code.

## Agent Structure

Each agent is defined as a single `.md` file with:

- Agent name and description
- Capabilities and tools
- Workflow instructions
- Usage patterns

## Available Agents

(Generated agents will appear here)

## Agent Development

When creating new agents:

1. Use the `agent-creator` skill to generate agent templates
2. Customize the workflow instructions for your specific needs
3. Test the agent with the Task tool
4. Iterate based on results

## Agent Types

Common agent types include:

- `code-review` - Code quality and architecture review
- `deployment` - CI/CD and deployment automation
- `testing` - Test automation and quality assurance
- `documentation` - Documentation generation and maintenance
- `security` - Security analysis and vulnerability assessment
- `general-purpose` - Research and complex multi-step tasks

---

*Generated with agent-creator skill*
"""

    readme_path = agents_dir / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    print(f"✅ Created agents README: {readme_path}")

    # Create a .gitignore file
    gitignore_content = """# Ignore temporary agent files
*.tmp
*.bak

# Ignore agent working directories
.work/
.temp/
"""

    gitignore_path = agents_dir / ".gitignore"
    with open(gitignore_path, "w", encoding="utf-8") as f:
        f.write(gitignore_content)

    print(f"✅ Created agents .gitignore: {gitignore_path}")

    return True


def list_agents():
    """List existing agents in the directory"""
    agents_dir, _ = find_agents_directory()

    if not agents_dir or not agents_dir.exists():
        print("❌ Agents directory does not exist")
        print("Run with --init to create it")
        return

    agent_files = list(agents_dir.glob("*.md"))

    if not agent_files:
        print("📭 No agents found")
        return

    print("🤖 Available agents:")
    for agent_file in sorted(agent_files):
        if agent_file.name == "README.md":
            continue
        agent_name = agent_file.stem
        print(f"  - {agent_name}")

    print(f"\n📍 Location: {agents_dir}")


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

    import argparse

    parser = argparse.ArgumentParser(
        description="Initialize and manage the agents directory"
    )
    parser.add_argument(
        "--init", action="store_true", help="Create the agents directory structure"
    )
    parser.add_argument("--list", action="store_true", help="List existing agents")
    parser.add_argument("--status", action="store_true", help="Show directory status")

    args = parser.parse_args()

    if args.init:
        success = create_agents_directory()
        if success:
            print("\n🎉 Agents directory initialized successfully!")
            print("You can now create agents using the agent-creator skill.")

    elif args.list:
        list_agents()

    elif args.status:
        agents_dir, claude_dir = find_agents_directory()

        if not claude_dir:
            print("❌ .claude directory not found")
            print("Please run this from within a Claude Code project")
            return

        if agents_dir and agents_dir.exists():
            print(f"✅ Agents directory exists: {agents_dir}")
            agent_files = list(agents_dir.glob("*.md"))
            agent_count = len([f for f in agent_files if f.name != "README.md"])
            print(f"📊 Found {agent_count} agent(s)")
        else:
            print("❌ Agents directory does not exist")
            print("Run with --init to create it")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
