# GitHub Data Collection

This folder stores issues, PRs, and discussions from the touchHLE repository and its forks.

## Folder Structure

```
github_data/
├── README.md              # This file
├── fetch_github_data.py   # Main fetcher script
├── upstream/              # Data from touchHLE/touchHLE (official)
│   ├── issues/            # Issue JSON files
│   ├── pulls/             # PR JSON files
│   ├── discussions/       # Discussion JSON files (if available)
│   └── commits/           # Recent commit info
├── forks/                 # Data from known forks
│   └── {owner}/           # Each fork gets its own folder
│       ├── issues/
│       └── pulls/
└── cache/                 # Cached API responses
    └── rate_limit.json    # Rate limit tracking
```

## Usage

### Fetch all data
```bash
python fetch_github_data.py --all
```

### Fetch only upstream
```bash
python fetch_github_data.py --upstream
```

### Fetch specific fork
```bash
python fetch_github_data.py --fork owner/repo
```

### Search for keywords
```bash
python fetch_github_data.py --search "black screen"
python fetch_github_data.py --search "glMaterial"
python fetch_github_data.py --search "rendering"
```

## Data Format

Each issue/PR is stored as a JSON file:

```json
{
  "number": 123,
  "title": "Issue title",
  "state": "open|closed",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T00:00:00Z",
  "labels": ["bug", "rendering"],
  "body": "Issue description...",
  "comments": [
    {"author": "user", "body": "Comment text", "created_at": "..."}
  ],
  "url": "https://github.com/touchHLE/touchHLE/issues/123"
}
```

## Known Repositories

### Upstream
- `touchHLE/touchHLE` - Official repository

### Notable Forks
Forks are discovered automatically via the GitHub API.

## Rate Limiting

GitHub API has rate limits:
- Unauthenticated: 60 requests/hour
- Authenticated: 5000 requests/hour

Set `GITHUB_TOKEN` environment variable for higher limits:
```bash
export GITHUB_TOKEN=ghp_your_token_here
python fetch_github_data.py --all
```

## Useful Searches for Black Screen Bug

- "black screen" - General black screen issues
- "rendering" - Rendering problems
- "glMaterial" - Material lighting issues
- "viewport" - Viewport configuration
- "texture" - Texture loading issues
- "OpenGL ES" - GL translation issues
- "Avatar of War" - This specific game
