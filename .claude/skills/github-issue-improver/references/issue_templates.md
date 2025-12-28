# GitHub Issue Templates Reference

## Standard Issue Types and Templates

### Bug Report Template
```markdown
## Bug Description
A clear and concise description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
A clear and concise description of what you expected to happen.

## Actual Behavior
A clear and concise description of what actually happened.

## Screenshots
If applicable, add screenshots to help explain your problem.

## Environment
- OS: [e.g. iOS]
- Browser [e.g. chrome, safari]
- Version [e.g. 22]

## Additional Context
Add any other context about the problem here.
```

### Feature Request Template
```markdown
## Feature Description
A clear and concise description of what the feature is.

## Use Case
Describe the user story or use case for this feature.

## Proposed Solution
If you have a solution in mind, describe it here.

## Alternatives Considered
Describe any alternative solutions or features you've considered.

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2
- [ ] Criteria 3

## Additional Context
Add any other context about the feature request here.
```

### Documentation Template
```markdown
## Documentation Type
- [ ] API Documentation
- [ ] User Guide
- [ ] Developer Guide
- [ ] README Update
- [ ] Code Comments

## Description
A clear and concise description of what documentation needs to be added or updated.

## Target Audience
Who is this documentation for?

## Key Points to Cover
- Point 1
- Point 2
- Point 3

## Additional Context
Add any other context about the documentation request here.
```

## Issue Title Conventions

### Format
- Use conventional commit style prefixes
- Keep titles under 72 characters
- Be specific and descriptive

### Common Prefixes
- `Fix:` - Bug fixes
- `Feat:` - New features
- `Docs:` - Documentation changes
- `Style:` - Code style changes (formatting, etc.)
- `Refactor:` - Code refactoring
- `Test:` - Adding or updating tests
- `Chore:` - Maintenance tasks
- `Perf:` - Performance improvements
- `CI:` - Continuous integration changes

### Examples
```
Fix: Login fails with invalid credentials
Feat: Add user profile image upload
Docs: Update API authentication guide
Refactor: Extract user service from controller
```

## Label Guidelines

### Type Labels
- `bug` - Software bugs
- `feature` - New features
- `documentation` - Documentation changes
- `enhancement` - Feature enhancements
- `question` - User questions
- `wontfix` - Issues that won't be fixed
- `duplicate` - Duplicate issues

### Priority Labels
- `priority: critical` - Blocks release/critical functionality
- `priority: high` - Important for next release
- `priority: medium` - Should be included when time permits
- `priority: low` - Nice to have, can be deferred

### Status Labels
- `status: new` - Newly created
- `status: in-progress` - Currently being worked on
- `status: review-needed` - Awaiting review
- `status: testing` - In testing phase
- `status: done` - Completed

### Area Labels
- `area: frontend` - Frontend related
- `area: backend` - Backend related
- `area: api` - API related
- `area: ui` - UI/UX related
- `area: database` - Database related
- `area: devops` - DevOps/Infrastructure related

## Issue Quality Checklist

### Title Quality
- [ ] Uses conventional prefix
- [ ] Descriptive and specific
- [ ] Under 72 characters
- [ ] No unnecessary technical jargon

### Body Quality
- [ ] Clear problem description
- [ ] Steps to reproduce (for bugs)
- [ ] Expected vs actual behavior (for bugs)
- [ ] Acceptance criteria (for features)
- [ ] Environment information (when relevant)
- [ ] Screenshots/examples (when helpful)

### Structure
- [ ] Uses proper Markdown formatting
- [ ] Has clear section headings
- [ ] Uses bullet points or numbered lists appropriately
- [ ] Code blocks formatted correctly

### Labels
- [ ] Appropriate type label
- [ ] Appropriate priority label
- [ ] Relevant area labels
- [ ] Not over-labeled (3-5 labels max)

## Common Anti-Patterns to Avoid

### Vague Titles
- ❌ "Problem with login"
- ❌ "Something is broken"
- ❌ "Issue with feature"
- ✅ "Fix: Login fails with special characters in password"

### Missing Context
- ❌ "This doesn't work"
- ❌ "Fix it"
- ❌ "Add the thing"
- ✅ "API endpoint /users returns 500 error when user email contains + symbol"

### Incomplete Information
- ❌ Bug reports without reproduction steps
- ❌ Feature requests without use cases
- ❌ Issues without environment details
- ✅ Complete descriptions with all relevant context