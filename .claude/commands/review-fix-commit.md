---
description: Reviews current changes for regressions and superficial fixes, applies necessary corrections, and commits changes in granular logical units.
allowed-tools: Task, Bash, Write, Read, Edit, Ls, Grep
argument-hint: "[optional: specific files to focus on]"
---

# Review, Fix, and Commit

This command automates the quality assurance loop before committing. It ensures that changes are robust (no regressions), deep (no band-aid fixes), and well-organized (granular commits).

## 1. Context Analysis
!`git status --short && echo "---" && git diff --stat`

## 2. Quality Review
Analyze the current changes.

```
Subagent: code-review-expert
Prompt: Review the current changes (visible in git diff).
Focus specifically on:
1. **Regressions**: Does this change break existing functionality? Check related tests or logic.
2. **Superficial Fixes**: Is this a "band-aid" fix? (e.g., just adding a null check without understanding why it's null, or silencing an error).
3. **Root Cause**: Does the fix address the root cause?

If issues are found, list them clearly. If the code is solid, confirm it.
```

## 3. Fix Application (Conditional)
If the review above identified issues (Regressions or Superficial Fixes):

1.  **Plan Fix**: Decide how to address the root cause.
2.  **Apply Fix**: Use `Edit` or `Write` to correct the code.
3.  **Verify**: Run relevant tests to ensure the fix works and doesn't introduce new regressions.
    - *Hint*: Use `pytest` or `npm test` as appropriate.

*Repeat this step until the Reviewer is satisfied.*

## 4. Granular Committing
Once the code is verified and clean, commit the changes. **Do not squash everything into one commit unless it's a single atomic change.**

1.  **Identify Logical Units**: Look at the modified files. Can they be grouped?
    - Example: Refactoring `utils.py` is one unit. Updating `main.py` to use the new utils is another.
    - Example: Fixing a bug in `auth.ts` and adding a test in `auth.test.ts` is one unit.
2.  **Commit Loop**:
    For each logical unit:
    a. Stage files: `git add <files>`
    b. Commit: `git commit -m "<type>: <description>"`
       - Use Conventional Commits (feat, fix, refactor, docs, chore, etc.).
       - The message should explain *why*, not just *what*.

## 5. Final Status
!`git status`
Report the commits created.
