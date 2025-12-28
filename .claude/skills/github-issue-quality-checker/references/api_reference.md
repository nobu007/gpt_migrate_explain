# GitHub Issue Quality Checker API Reference

## Quick Reference

### Environment Variables
- `GITHUB_TOKEN`: GitHub Personal Access Token (required)
- `GITHUB_REPOSITORY`: Target repository in "owner/repo" format (required)

### Command Line Usage
```bash
python scripts/main.py [--repository owner/repo] [--token TOKEN] [--output-format text|json]
```

### Output Formats

#### Text Format (default)
Human-readable report with issue details and quality assessment.

#### JSON Format
```json
{
  "issue_number": 123,
  "title": "Issue title",
  "score": 25.5,
  "reasons": ["タイトルが短い", "本文が空"],
  "url": "https://github.com/owner/repo/issues/123"
}
```

## Quality Scoring Algorithm

See `references/quality_criteria.md` for detailed scoring methodology.

## GitHub API Integration

See `references/github_api_usage.md` for GitHub API usage details and authentication requirements.
