#!/usr/bin/env python3
"""
GitHub Data Fetcher for touchHLE

Fetches issues, PRs, and related data from the touchHLE repository
and its forks for analysis by the automation framework.

Usage:
    python fetch_github_data.py --all           # Fetch everything
    python fetch_github_data.py --upstream      # Fetch upstream only
    python fetch_github_data.py --forks         # Fetch all forks
    python fetch_github_data.py --search "term" # Search for keyword
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def get_utc_now() -> str:
    """Get current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

# Configuration
UPSTREAM_REPO = "touchHLE/touchHLE"
BASE_DIR = Path(__file__).parent
UPSTREAM_DIR = BASE_DIR / "upstream"
FORKS_DIR = BASE_DIR / "forks"
CACHE_DIR = BASE_DIR / "cache"

# GitHub API
GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Rate limiting
REQUEST_DELAY = 1.0  # seconds between requests (unauthenticated)
AUTH_REQUEST_DELAY = 0.2  # seconds between requests (authenticated)


def get_headers() -> Dict[str, str]:
    """Get headers for GitHub API requests."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "touchHLE-automation-fetcher"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


def make_request(url: str, max_retries: int = 3) -> Optional[Dict]:
    """Make a GitHub API request with retry logic."""
    delay = AUTH_REQUEST_DELAY if GITHUB_TOKEN else REQUEST_DELAY

    for attempt in range(max_retries):
        try:
            req = Request(url, headers=get_headers())
            with urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode())
                time.sleep(delay)
                return data
        except HTTPError as e:
            if e.code == 403:
                # Rate limited
                reset_time = e.headers.get("X-RateLimit-Reset")
                if reset_time:
                    wait_time = int(reset_time) - int(time.time()) + 5
                    print(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(max(wait_time, 60))
                    continue
            elif e.code == 404:
                print(f"Not found: {url}")
                return None
            else:
                print(f"HTTP Error {e.code}: {url}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                return None
        except URLError as e:
            print(f"URL Error: {e.reason}")
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            return None
        except Exception as e:
            print(f"Error: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            return None

    return None


def get_rate_limit() -> Dict:
    """Check current rate limit status."""
    data = make_request(f"{GITHUB_API}/rate_limit")
    if data:
        return data.get("rate", {})
    return {}


def fetch_paginated(url: str, max_pages: int = 10) -> List[Dict]:
    """Fetch paginated results from GitHub API."""
    results = []
    page = 1

    while page <= max_pages:
        page_url = f"{url}{'&' if '?' in url else '?'}page={page}&per_page=100"
        data = make_request(page_url)

        if not data or len(data) == 0:
            break

        results.extend(data)
        print(f"  Fetched page {page} ({len(data)} items)")
        page += 1

    return results


def fetch_issue_comments(repo: str, issue_number: int) -> List[Dict]:
    """Fetch comments for an issue."""
    url = f"{GITHUB_API}/repos/{repo}/issues/{issue_number}/comments"
    comments = make_request(url)

    if not comments:
        return []

    return [
        {
            "author": c.get("user", {}).get("login", "unknown"),
            "body": c.get("body", ""),
            "created_at": c.get("created_at", "")
        }
        for c in comments
    ]


def fetch_issues(repo: str, output_dir: Path, state: str = "all") -> int:
    """Fetch all issues from a repository."""
    issues_dir = output_dir / "issues"
    issues_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching issues from {repo}...")
    url = f"{GITHUB_API}/repos/{repo}/issues?state={state}&sort=updated"
    issues = fetch_paginated(url)

    count = 0
    for issue in issues:
        # Skip pull requests (they appear in issues endpoint too)
        if "pull_request" in issue:
            continue

        issue_num = issue["number"]
        print(f"  Processing issue #{issue_num}: {issue['title'][:50]}...")

        # Fetch comments
        comments = fetch_issue_comments(repo, issue_num)

        issue_data = {
            "number": issue_num,
            "title": issue["title"],
            "state": issue["state"],
            "created_at": issue["created_at"],
            "updated_at": issue["updated_at"],
            "closed_at": issue.get("closed_at"),
            "labels": [l["name"] for l in issue.get("labels", [])],
            "author": issue.get("user", {}).get("login", "unknown"),
            "body": issue.get("body", ""),
            "comments": comments,
            "comments_count": len(comments),
            "url": issue["html_url"],
            "fetched_at": get_utc_now()
        }

        # Save to file
        issue_file = issues_dir / f"issue_{issue_num:04d}.json"
        with open(issue_file, "w", encoding="utf-8") as f:
            json.dump(issue_data, f, indent=2, ensure_ascii=False)

        count += 1

    print(f"Saved {count} issues to {issues_dir}")
    return count


def fetch_pull_requests(repo: str, output_dir: Path, state: str = "all") -> int:
    """Fetch all pull requests from a repository."""
    pulls_dir = output_dir / "pulls"
    pulls_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching pull requests from {repo}...")
    url = f"{GITHUB_API}/repos/{repo}/pulls?state={state}&sort=updated"
    pulls = fetch_paginated(url)

    count = 0
    for pr in pulls:
        pr_num = pr["number"]
        print(f"  Processing PR #{pr_num}: {pr['title'][:50]}...")

        # Fetch comments
        comments = fetch_issue_comments(repo, pr_num)

        pr_data = {
            "number": pr_num,
            "title": pr["title"],
            "state": pr["state"],
            "created_at": pr["created_at"],
            "updated_at": pr["updated_at"],
            "closed_at": pr.get("closed_at"),
            "merged_at": pr.get("merged_at"),
            "labels": [l["name"] for l in pr.get("labels", [])],
            "author": pr.get("user", {}).get("login", "unknown"),
            "body": pr.get("body", ""),
            "comments": comments,
            "comments_count": len(comments),
            "base_branch": pr.get("base", {}).get("ref", "unknown"),
            "head_branch": pr.get("head", {}).get("ref", "unknown"),
            "url": pr["html_url"],
            "diff_url": pr.get("diff_url", ""),
            "fetched_at": get_utc_now()
        }

        # Save to file
        pr_file = pulls_dir / f"pr_{pr_num:04d}.json"
        with open(pr_file, "w", encoding="utf-8") as f:
            json.dump(pr_data, f, indent=2, ensure_ascii=False)

        count += 1

    print(f"Saved {count} pull requests to {pulls_dir}")
    return count


def fetch_commits(repo: str, output_dir: Path, max_commits: int = 100) -> int:
    """Fetch recent commits from a repository."""
    commits_dir = output_dir / "commits"
    commits_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching commits from {repo}...")
    url = f"{GITHUB_API}/repos/{repo}/commits?per_page={min(max_commits, 100)}"
    commits = make_request(url)

    if not commits:
        return 0

    commits_data = []
    for commit in commits[:max_commits]:
        commit_data = {
            "sha": commit["sha"],
            "message": commit["commit"]["message"],
            "author": commit["commit"]["author"]["name"],
            "date": commit["commit"]["author"]["date"],
            "url": commit["html_url"]
        }
        commits_data.append(commit_data)

    # Save all commits to a single file
    commits_file = commits_dir / "recent_commits.json"
    with open(commits_file, "w", encoding="utf-8") as f:
        json.dump({
            "repo": repo,
            "fetched_at": get_utc_now(),
            "commits": commits_data
        }, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(commits_data)} commits to {commits_file}")
    return len(commits_data)


def fetch_forks(repo: str) -> List[Dict]:
    """Fetch list of forks for a repository."""
    print(f"Fetching forks of {repo}...")
    url = f"{GITHUB_API}/repos/{repo}/forks?sort=updated"
    forks = fetch_paginated(url, max_pages=5)

    fork_list = []
    for fork in forks:
        fork_list.append({
            "full_name": fork["full_name"],
            "owner": fork["owner"]["login"],
            "name": fork["name"],
            "description": fork.get("description", ""),
            "updated_at": fork["updated_at"],
            "stargazers_count": fork.get("stargazers_count", 0),
            "open_issues_count": fork.get("open_issues_count", 0),
            "url": fork["html_url"]
        })

    # Save fork list
    forks_file = FORKS_DIR / "fork_list.json"
    with open(forks_file, "w", encoding="utf-8") as f:
        json.dump({
            "upstream": repo,
            "fetched_at": get_utc_now(),
            "forks": fork_list
        }, f, indent=2, ensure_ascii=False)

    print(f"Found {len(fork_list)} forks")
    return fork_list


def search_issues(query: str, repo: Optional[str] = None) -> List[Dict]:
    """Search for issues matching a query."""
    search_query = f"{query}"
    if repo:
        search_query += f" repo:{repo}"
    else:
        search_query += f" repo:{UPSTREAM_REPO}"

    print(f"Searching for: {search_query}")
    url = f"{GITHUB_API}/search/issues?q={search_query.replace(' ', '+')}&sort=updated"
    data = make_request(url)

    if not data:
        return []

    results = []
    for item in data.get("items", []):
        results.append({
            "number": item["number"],
            "title": item["title"],
            "state": item["state"],
            "is_pr": "pull_request" in item,
            "url": item["html_url"],
            "body_preview": (item.get("body", "") or "")[:200]
        })

    # Save search results
    search_dir = BASE_DIR / "searches"
    search_dir.mkdir(exist_ok=True)

    safe_query = "".join(c if c.isalnum() else "_" for c in query)[:50]
    search_file = search_dir / f"search_{safe_query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(search_file, "w", encoding="utf-8") as f:
        json.dump({
            "query": query,
            "repo": repo or UPSTREAM_REPO,
            "fetched_at": get_utc_now(),
            "total_count": data.get("total_count", 0),
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"Found {len(results)} results, saved to {search_file}")
    return results


def fetch_upstream():
    """Fetch all data from upstream repository."""
    print("=" * 60)
    print(f"Fetching upstream repository: {UPSTREAM_REPO}")
    print("=" * 60)

    UPSTREAM_DIR.mkdir(parents=True, exist_ok=True)

    fetch_issues(UPSTREAM_REPO, UPSTREAM_DIR)
    fetch_pull_requests(UPSTREAM_REPO, UPSTREAM_DIR)
    fetch_commits(UPSTREAM_REPO, UPSTREAM_DIR)

    # Save metadata
    meta_file = UPSTREAM_DIR / "metadata.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump({
            "repo": UPSTREAM_REPO,
            "fetched_at": get_utc_now(),
            "url": f"https://github.com/{UPSTREAM_REPO}"
        }, f, indent=2)


def fetch_all_forks():
    """Fetch data from all active forks."""
    print("=" * 60)
    print("Fetching fork data")
    print("=" * 60)

    forks = fetch_forks(UPSTREAM_REPO)

    # Only fetch from forks with recent activity or issues
    active_forks = [
        f for f in forks
        if f.get("open_issues_count", 0) > 0
    ]

    print(f"Found {len(active_forks)} forks with open issues")

    for fork in active_forks[:10]:  # Limit to 10 most active forks
        fork_name = fork["full_name"]
        fork_dir = FORKS_DIR / fork["owner"]
        fork_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nFetching from fork: {fork_name}")
        fetch_issues(fork_name, fork_dir)
        fetch_pull_requests(fork_name, fork_dir)


def create_summary():
    """Create a summary of all collected data."""
    summary = {
        "generated_at": get_utc_now(),
        "upstream": {},
        "forks": {},
        "searches": []
    }

    # Count upstream data
    issues_dir = UPSTREAM_DIR / "issues"
    pulls_dir = UPSTREAM_DIR / "pulls"

    if issues_dir.exists():
        summary["upstream"]["issues_count"] = len(list(issues_dir.glob("*.json")))
    if pulls_dir.exists():
        summary["upstream"]["pulls_count"] = len(list(pulls_dir.glob("*.json")))

    # Count fork data
    if FORKS_DIR.exists():
        for fork_owner in FORKS_DIR.iterdir():
            if fork_owner.is_dir() and fork_owner.name != "fork_list.json":
                fork_issues = fork_owner / "issues"
                fork_pulls = fork_owner / "pulls"
                summary["forks"][fork_owner.name] = {
                    "issues_count": len(list(fork_issues.glob("*.json"))) if fork_issues.exists() else 0,
                    "pulls_count": len(list(fork_pulls.glob("*.json"))) if fork_pulls.exists() else 0
                }

    # List searches
    searches_dir = BASE_DIR / "searches"
    if searches_dir.exists():
        summary["searches"] = [f.name for f in searches_dir.glob("*.json")]

    # Save summary
    summary_file = BASE_DIR / "summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary saved to {summary_file}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub data for touchHLE")
    parser.add_argument("--all", action="store_true", help="Fetch everything")
    parser.add_argument("--upstream", action="store_true", help="Fetch upstream only")
    parser.add_argument("--forks", action="store_true", help="Fetch all forks")
    parser.add_argument("--fork", type=str, help="Fetch specific fork (owner/repo)")
    parser.add_argument("--search", type=str, help="Search for keyword")
    parser.add_argument("--rate-limit", action="store_true", help="Check rate limit")

    args = parser.parse_args()

    # Create directories
    UPSTREAM_DIR.mkdir(parents=True, exist_ok=True)
    FORKS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if args.rate_limit:
        rate = get_rate_limit()
        print(f"Rate limit: {rate.get('remaining', '?')}/{rate.get('limit', '?')}")
        reset = rate.get('reset')
        if reset:
            reset_time = datetime.fromtimestamp(reset)
            print(f"Resets at: {reset_time}")
        return

    if args.search:
        search_issues(args.search)
        return

    if args.upstream or args.all:
        fetch_upstream()

    if args.forks or args.all:
        fetch_all_forks()

    if args.fork:
        fork_dir = FORKS_DIR / args.fork.split("/")[0]
        fork_dir.mkdir(parents=True, exist_ok=True)
        fetch_issues(args.fork, fork_dir)
        fetch_pull_requests(args.fork, fork_dir)

    # Create summary
    summary = create_summary()

    print("\n" + "=" * 60)
    print("Fetch complete!")
    print("=" * 60)
    print(f"Upstream issues: {summary['upstream'].get('issues_count', 0)}")
    print(f"Upstream PRs: {summary['upstream'].get('pulls_count', 0)}")
    print(f"Forks with data: {len(summary['forks'])}")
    print(f"Searches: {len(summary['searches'])}")


if __name__ == "__main__":
    main()
