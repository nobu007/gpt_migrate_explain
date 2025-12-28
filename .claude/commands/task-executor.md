# Task Executor Command

## Usage

```
/task-executor
```

## Description

Manually trigger the Task Executor system to search for GitHub issues with the `🤖 task-execution` label and delegate them to Claude Code for execution.

## What it does

1. **TypeScript Search**: Uses TypeScript implementation to search for open issues labeled `🤖 task-execution` assigned to `claude-code`
2. **Task Validation**: Validates that issues have proper execution steps defined in the template
3. **Claude Code Delegation**: Delegates execution to Claude Code Agent with detailed prompts
4. **Progress Tracking**: Adds status comments to issues during processing
5. **Claude Execution**: Claude Code Agent handles actual command execution and PR creation

## Implementation Details

- **Search Engine**: TypeScript (`src/TaskExecutor.ts`)
- **Label Filtering**: Searches for `🤖 task-execution` label only
- **Assignee Check**: Ensures issue is assigned to `claude-code`
- **Template Parsing**: Validates structured task execution template
- **Claude Integration**: Creates detailed prompts for Claude Code Agent
- **Error Handling**: Skips invalid tasks and reports errors

## Example Output

```
🤖 Task Executor System

🔍 Searching for task execution issues...
📋 Found 1 task execution issue

🤖 Processing issue #123: Fix TypeScript build errors
✅ Task has 3 valid execution steps
🚀 Delegating to Claude Code Agent...

✅ Issue #123 processing initiated
```

## Requirements

- `GITHUB_TOKEN` environment variable with repository access
- Claude Code CLI available in the execution environment
- Agent definition at `.claude/agents/task-executor.md`