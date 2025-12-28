# GitHub API Reference for Issue Management

## Authentication

The GitHub Issue Improver uses Personal Access Tokens (PAT) for authentication.

### Required Environment Variable
```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

### Token Permissions
The PAT requires the following scopes:
- `repo` - Full control of private repositories
- `public_repo` - Access public repositories (if only working with public repos)
- `issues:write` - Read and write issues

## Core API Endpoints

### Get Issue
```http
GET /repos/{owner}/{repo}/issues/{issue_number}
```

**Response Fields:**
- `id` - Issue ID
- `number` - Issue number
- `title` - Issue title
- `body` - Issue body (Markdown)
- `state` - `open` or `closed`
- `labels` - Array of label objects
- `assignees` - Array of assignee objects
- `html_url` - URL to view issue in browser
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

**Example Response:**
```json
{
  "id": 1,
  "number": 1347,
  "title": "Found a bug",
  "body": "I'm having a problem with this.",
  "state": "open",
  "labels": [
    {
      "id": 208045946,
      "node_id": "MDU6TGFiZWwyMDgwNDU5NDY=",
      "url": "https://api.github.com/repos/octocat/Hello-World/labels/bug",
      "name": "bug",
      "color": "f29513",
      "default": true
    }
  ],
  "assignees": [],
  "html_url": "https://github.com/octocat/Hello-World/issues/1347"
}
```

### Update Issue
```http
PATCH /repos/{owner}/{repo}/issues/{issue_number}
```

**Request Body:**
```json
{
  "title": "New title",
  "body": "New body text",
  "labels": ["bug", "enhancement"],
  "assignees": ["octocat", "hubot"]
}
```

**Fields:**
- `title` (optional) - Issue title
- `body` (optional) - Issue body text
- `labels` (optional) - Array of label names
- `assignees` (optional) - Array of assignee usernames

### Create Issue Comment
```http
POST /repos/{owner}/{repo}/issues/{issue_number}/comments
```

**Request Body:**
```json
{
  "body": "Me too"
}
```

**Response:**
```json
{
  "id": 1,
  "html_url": "https://github.com/octocat/Hello-World/issues/1347#issuecomment-1",
  "body": "Me too",
  "user": {
    "login": "octocat",
    "id": 1
  },
  "created_at": "2011-04-14T16:00:49Z"
}
```

### Get Repository Labels
```http
GET /repos/{owner}/{repo}/labels
```

**Response:**
```json
[
  {
    "id": 208045946,
    "node_id": "MDU6TGFiZWwyMDgwNDU5NDY=",
    "url": "https://api.github.com/repos/octocat/Hello-World/labels/bug",
    "name": "bug",
    "description": "Something isn't working",
    "color": "f29513",
    "default": true
  }
]
```

## Rate Limits

GitHub API has rate limits:
- **Authenticated requests:** 5,000 requests per hour
- **Unauthenticated requests:** 60 requests per hour

Rate limit headers are included in responses:
- `X-RateLimit-Limit` - Maximum requests per hour
- `X-RateLimit-Remaining` - Remaining requests in current window
- `X-RateLimit-Reset` - Unix timestamp when rate limit resets

## Error Handling

### Common HTTP Status Codes

#### 401 Unauthorized
```json
{
  "message": "Requires authentication",
  "documentation_url": "https://docs.github.com/rest/reference/issues"
}
```
**Solution:** Check that `GITHUB_TOKEN` is valid and has required scopes.

#### 403 Forbidden
```json
{
  "message": "Rate limit exceeded",
  "documentation_url": "https://docs.github.com/rest/overview/rate-limits-for-the-rest-api"
}
```
**Solution:** Wait for rate limit reset or implement exponential backoff.

#### 404 Not Found
```json
{
  "message": "Not Found"
}
```
**Solution:** Verify repository exists and issue number is correct.

#### 422 Unprocessable Entity
```json
{
  "message": "Validation Failed",
  "errors": [
    {
      "resource": "Issue",
      "field": "title",
      "code": "missing_field"
    }
  ]
}
```
**Solution:** Check request body format and required fields.

## Pagination

List endpoints return paginated results. Response includes:
- `Link` header with pagination URLs
- Page info in response body for some endpoints

**Example Link Header:**
```
Link: <https://api.github.com/repositories/1234/issues?page=2>; rel="next",
      <https://api.github.com/repositories/1234/issues?page=5>; rel="last"
```

## Conditional Requests

Use conditional requests to avoid rate limits:
- `If-None-Match` header with ETag
- `If-Modified-Since` header with timestamp

**Example:**
```http
GET /repos/{owner}/{repo}/issues/{issue_number}
If-None-Match: "some-etag-value"
```

Returns `304 Not Modified` if data hasn't changed.

## Best Practices

### 1. Use Appropriate Scopes
Only request the minimum necessary permissions for your PAT.

### 2. Handle Rate Limits Gracefully
- Check rate limit headers
- Implement exponential backoff
- Cache responses when possible

### 3. Use Conditional Requests
- Include `If-None-Match` for GET requests
- Store and reuse ETags

### 4. Validate Input
- Validate repository format (owner/repo)
- Check issue numbers are positive integers
- Sanitize user input for issue bodies

### 5. Error Handling
- Always check response status codes
- Provide meaningful error messages
- Implement retry logic for transient failures

## SDK Libraries

While this skill uses direct HTTP requests, you could also use:

### Python
- `PyGithub` - Official-ish Python GitHub library
- `github3.py` - Another popular Python library

### JavaScript
- `@octokit/rest` - Official GitHub REST client
- `simple-git` - Simplified Git operations

These libraries handle many edge cases and provide better abstractions.