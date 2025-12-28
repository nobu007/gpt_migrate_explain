---
description: Automatically designs, implements, and installs new single-file commands (.md) from a high-level description.
allowed-tools: Task, Write, Read, Ls, Glob, Grep, Bash
argument-hint: "[command idea] - e.g. 'Create a command to check PR status' or 'Update the code-review command'"
---

# Command Creator Auto

This command automates the creation and update of **single-file commands** in `.claude/commands/`.
It acts as a meta-command that takes a high-level description from the user and turns it into a production-ready `.md` command file, following the Miyabi framework standards.

## Core Philosophy
- **One File, One Command**: Commands should be self-contained in a single Markdown file.
- **Agent-Centric**: Instructions are written for the agent (Claude), not the user.
- **Minimal Interaction**: Ask clarifying questions only when absolutely necessary. Default to best practices.

## Workflow

### Step 1: Analyze Request & Mode
Determine if this is a **New Creation** or an **Update**.

- **New Creation**: User wants a new capability.
  - *Action*: Determine a unique kebab-case filename (e.g., `pr-status-checker.md`).
- **Update**: User wants to modify an existing command.
  - *Action*: Identify the target file (e.g., `code-review.md`) and read its current content.

### Step 2: Design Command
Plan the command structure before writing.

#### Frontmatter Design
- `description`: Concise summary of "when to use this command".
- `allowed-tools`: **Restrictive list**. Only include tools absolutely needed (e.g., `Bash`, `Read`, `Task`).
  - *Note*: If the command needs to run git, include `Bash`. If it needs to read files, include `Read`.
- `argument-hint`: Helpful string showing expected arguments (e.g., `[target_dir]`).

#### Body Design
- **Prerequisites**: Use `!` syntax for auto-running context checks (e.g., `!git status -s`).
- **Step-by-Step Logic**: Numbered steps for the agent to follow.
- **Sub-Agent Delegation**: Use `Task` blocks for complex reasoning or parallel work.
  - *Example*:
    ```markdown
    ## Analysis
    ```
    Subagent: code-review-expert
    Prompt: Analyze...
    ```
    ```

### Step 3: Implement & Install
1.  **Generate Content**: Create the full Markdown content.
2.  **Write File**: Save to `.claude/commands/<filename>.md`.
    - *Path*: Always use absolute path or relative to project root.
    - *Overwrite*: If updating, set `Overwrite: true`.

### Step 4: Verification
1.  **Check Existence**: Verify the file was created/updated.
2.  **Syntax Check**: Ensure frontmatter is valid YAML and sections are clear.

## Example Output Structure

```markdown
---
description: Checks the status of the current PR and lists failing checks.
allowed-tools: Bash
argument-hint: ""
---

# PR Status Checker

## 1. Context Check
!`git branch --show-current && gh pr view --json url,state,statusCheckRollup`

## 2. Analysis
If the PR is merged, report success.
If checks are failing, list them and suggest fixes.
```

## Instructions for the Agent (You)
1.  **Parse Input**: specific requirements vs. vague intent.
2.  **Propose/Execute**:
    - If simple: "I will create `xxx.md`." -> **Write immediately**.
    - If complex: "I will design a command for X. Key features: A, B, C." -> **Write**.
3.  **Refinement**: If updating, preserve existing custom logic unless asked to remove it.
4.  **Completion**: Report the full path of the created command.
