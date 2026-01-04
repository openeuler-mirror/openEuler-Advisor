#!/usr/bin/env python3
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2024. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************
"""
Standalone tool to fetch pending pull requests from openEuler repositories.
This tool can fetch PRs either by SIG name or by repository, with various output formats.
"""

import argparse
import json
import math
import queue
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import List, Tuple, Dict, Any, Optional, Callable


def get_quickissue(url: str, verbose: bool = False) -> Optional[Dict[str, Any]]:
    """
    Fetch quickissue data from URL.

    Args:
        url: The URL to fetch
        verbose: Enable verbose logging

    Returns:
        JSON response as dict, or None on error
    """
    try:
        result = urllib.request.urlopen(url)
        json_resp = json.loads(result.read().decode("utf-8"))
        return json_resp
    except urllib.error.HTTPError as error:
        if verbose:
            print(f"get_quickissue failed to access: {url}", file=sys.stderr)
            print(f"get_quickissue failed: {error.code}, {error.reason}", file=sys.stderr)
        return None


def get_quickissue_pulls_by_sig(sig: str, verbose: bool = False) -> Tuple[List[Dict[str, Any]], int]:
    """
    Get pull requests for a SIG from quickissue API.

    Args:
        sig: SIG name
        verbose: Enable verbose logging

    Returns:
        Tuple of (list of PR dicts, total count)
    """
    quickissue_base_url = "https://quickissue.openeuler.openatom.cn/api-issues/pulls"
    results = []
    total = 0

    def process_response(json_resp: Optional[Dict[str, Any]]) -> bool:
        if not json_resp or not json_resp.get("data"):
            return False
        for d in json_resp["data"]:
            repo_parts = d["repo"].split("/")
            results.append({
                'owner': repo_parts[0],
                'repo': repo_parts[1],
                'number': d["link"].split("/")[-1],
                'title': d.get("title", ""),
                'author': d.get("author", ""),
                'created_at': d.get("created_at", ""),
                'updated_at': d.get("updated_at", ""),
                'url': d.get("link", ""),
                'state': d.get("state", "open")
            })
        return True

    # Get first page
    query_url = f"{quickissue_base_url}?sig={sig}&page=1&per_page=100&sort=created_at&state=open"
    json_resp = get_quickissue(query_url, verbose)
    if not process_response(json_resp):
        return results, total

    total = json_resp["total"]
    pages = math.ceil(total / json_resp["per_page"])

    # Get remaining pages
    for page in range(2, pages + 1):
        query_url = f"{quickissue_base_url}?sig={sig}&page={page}&per_page=100&sort=created_at&state=open"
        process_response(get_quickissue(query_url, verbose))

    return results, total


def get_quickissue_pulls_by_repo(owner: str, repo: str, verbose: bool = False) -> Tuple[List[Dict[str, Any]], int]:
    """
    Get pull requests for a specific repository from quickissue API.

    The API uses filters to match repository by the full path (org/repo format).

    Args:
        owner: Repository owner/organization
        repo: Repository name
        verbose: Enable verbose logging

    Returns:
        Tuple of (list of PR dicts, total count)
    """
    quickissue_base_url = "https://quickissue.openeuler.openatom.cn/api-issues/pulls"
    results = []
    total = 0
    repo_full_name = f"{owner}/{repo}"

    def process_response(json_resp: Optional[Dict[str, Any]]) -> bool:
        if not json_resp or not json_resp.get("data"):
            return False
        for d in json_resp["data"]:
            # Filter by repository - match the full repo path
            if d.get("repo", "") != repo_full_name:
                continue

            # Extract MR/PR number from URL (atomgit uses merge_requests)
            url_parts = d.get("link", "").split("/")
            number = url_parts[-1] if url_parts else ""

            results.append({
                'owner': owner,
                'repo': repo,
                'number': number,
                'title': d.get("title", ""),
                'author': d.get("author", ""),
                'created_at': d.get("created_at", ""),
                'updated_at': d.get("updated_at", ""),
                'url': d.get("link", ""),
                'state': d.get("state", "open"),
                'description': d.get("description", ""),
                'assignees': d.get("assignees", "").split(",") if d.get("assignees") else [],
                'labels': d.get("labels", "").split(",") if d.get("labels") else [],
                'milestone': d.get("milestone", ""),
                'draft': d.get("draft", False),
                'mergeable': d.get("mergeable", False),
                'merged': d.get("merged", False),
                'org': d.get("org", ""),
                'branch': d.get("ref", ""),
                'sig': d.get("sig", ""),
                'last_comment_at': d.get("updated_at", d.get("created_at", ""))
            })
        return True

    # Query all open PRs and filter by repository
    # Note: The API doesn't seem to support repository filter directly, so we fetch all and filter
    query_url = f"{quickissue_base_url}?page=1&per_page=100&sort=created_at&direction=desc&state=open"
    if verbose:
        print(f"Fetching PRs from: {query_url}", file=sys.stderr)
        print(f"Filtering for repository: {repo_full_name}", file=sys.stderr)

    json_resp = get_quickissue(query_url, verbose)
    if not process_response(json_resp):
        if verbose:
            print(f"Failed to get response from API", file=sys.stderr)
        return results, total

    total_all = json_resp.get("total", 0)
    per_page = json_resp.get("per_page", 100)

    # Filter results from first page
    results_per_page = len(results)
    total = results_per_page

    if verbose:
        print(f"Found {results_per_page} PRs for {repo_full_name} on page 1", file=sys.stderr)

    # If we results and there might be more pages, fetch remaining pages
    if results_per_page > 0 and total_all > per_page:
        pages = math.ceil(total_all / per_page)
        for page in range(2, pages + 1):
            query_url = f"{quickissue_base_url}?page={page}&per_page={per_page}&sort=created_at&direction=desc&state=open"
            json_resp = get_quickissue(query_url, verbose)
            if json_resp:
                page_results_size = len(results)
                process_response(json_resp)
                new_results = len(results) - page_results_size
                total += new_results
                if verbose and new_results > 0:
                    print(f"Found {new_results} more PRs for {repo_full_name} on page {page}", file=sys.stderr)
                if new_results == 0:
                    # No more results for this repo, we can stop
                    break

    return results, total


def format_output(prs: List[Dict[str, Any]], format_type: str = "text",
                  fields: List[str] = None) -> str:
    """
    Format PRs output according to specified format.

    Args:
        prs: List of PR dictionaries
        format_type: Output format ('text', 'json', 'csv')
        fields: List of fields to include (None for all)

    Returns:
        Formatted string
    """
    if fields is None:
        fields = ['owner', 'repo', 'number', 'title', 'author', 'created_at', 'url']

    if format_type == "json":
        filtered_prs = []
        for pr in prs:
            filtered_pr = {}
            for field in fields:
                value = pr.get(field, "")
                # Convert arrays to strings for JSON output
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                filtered_pr[field] = value
            filtered_prs.append(filtered_pr)
        return json.dumps(filtered_prs, indent=2, ensure_ascii=False)

    elif format_type == "csv":
        import csv
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for pr in prs:
            row = {}
            for field in fields:
                value = pr.get(field, "")
                # Convert arrays to strings for CSV output
                if isinstance(value, list):
                    value = "; ".join(str(v) for v in value)
                elif value is None:
                    value = ""
                row[field] = value
            writer.writerow(row)
        return output.getvalue()

    else:  # text format
        lines = []
        for pr in prs:
            if 'owner' in fields and 'repo' in fields and 'number' in fields:
                line = f"{pr['owner']}/{pr['repo']}#{pr['number']}"
            else:
                line = ""

            if 'title' in fields and pr.get('title'):
                line += f" - {pr['title']}"

            if 'author' in fields and pr.get('author'):
                line += f" by {pr['author']}"

            # Add additional fields for text format
            if 'state' in fields:
                line += f" [{pr.get('state', 'open')}]"

            if 'created_at' in fields and pr.get('created_at'):
                line += f" (created: {pr['created_at']})"

            lines.append(line)

        return "\n".join(lines)


def filter_prs(prs: List[Dict[str, Any]], author: str = None,
                title_contains: str = None, repo: str = None) -> List[Dict[str, Any]]:
    """
    Filter PRs based on criteria.

    Args:
        prs: List of PR dictionaries
        author: Filter by author name (case insensitive)
        title_contains: Filter by title containing text (case insensitive)
        repo: Filter by repository name (case insensitive)

    Returns:
        Filtered list of PRs
    """
    filtered = prs

    if author:
        filtered = [pr for pr in filtered
                   if pr.get('author', '').lower() == author.lower()]

    if title_contains:
        filtered = [pr for pr in filtered
                   if title_contains.lower() in pr.get('title', '').lower()]

    if repo:
        filtered = [pr for pr in filtered
                   if repo.lower() in pr.get('repo', '').lower()]

    return filtered


def generate_pending_prs(user_gitee, sig: str, pending_prs_queue: queue.Queue,
                         verbose_func: Callable[[str, int], None] = None) -> int:
    """
    Generate pending PRs via quickissue API (compatibility function).

    This function maintains compatibility with the original interface used by oe_review.py.

    Args:
        user_gitee: Gitee API instance (unused in this implementation but kept for compatibility)
        sig: SIG name
        pending_prs_queue: Queue to put pending PRs into
        verbose_func: Function for verbose logging (default: None)

    Returns:
        0 on success
    """
    verbose = bool(verbose_func)
    results, total = get_quickissue_pulls_by_sig(sig, verbose)

    if verbose_func:
        verbose_func(f"start generate list of pending pr.", 2)
        verbose_func(f"Pending PRs of {sig}: {results}", 2)

    for result in results:
        pending_prs_queue.put(result)

    pending_prs_queue.put(None)
    if verbose_func:
        verbose_func("generate_pending_pr finished", 2)
    pending_prs_queue.join()
    if verbose_func:
        verbose_func("PENDING_PRS join finished", 2)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Fetch pending pull requests from openEuler repositories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --sig devkit
  %(prog)s --sig sig-high-availability --format json
  %(prog)s --repo src-openeuler/yum --fields owner,repo,number,title
  %(prog)s --sig infra --author john --format csv
  %(prog)s --sig devkit --title_contains "fix bug"
        """
    )

    # Query options
    query_group = parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument("-s", "--sig", help="SIG name")
    query_group.add_argument("-r", "--repo", nargs=2, metavar=('OWNER', 'REPO'),
                           help="Repository owner and name")

    # Output options
    parser.add_argument("-f", "--format", choices=["text", "json", "csv"],
                       default="text", help="Output format (default: text)")
    parser.add_argument("--fields", nargs="+",
                       choices=["owner", "repo", "number", "title", "author",
                               "created_at", "updated_at", "url", "state",
                               "description", "assignees", "labels", "milestone",
                               "mergeable", "merged", "head_branch", "head_sha",
                               "base_branch", "changes_count", "additions", "deletions",
                               "commits_count", "comments_count", "review_comments_count",
                               "last_comment_at"],
                       help="Fields to include in output")
    parser.add_argument("-o", "--output", metavar="FILE",
                       help="Write output to file (default: stdout)")

    # Filter options
    parser.add_argument("--author", help="Filter by author name")
    parser.add_argument("--title_contains", help="Filter by title containing text")
    parser.add_argument("--repo_filter", metavar="REPO_NAME",
                       help="Filter by repository name (when using --sig)")

    # Other options
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose output")

    args = parser.parse_args()

    # Fetch PRs
    if args.sig:
        prs, total = get_quickissue_pulls_by_sig(args.sig, args.verbose)
    else:  # repo
        owner, repo = args.repo
        prs, total = get_quickissue_pulls_by_repo(owner, repo, args.verbose)

    if args.verbose:
        print(f"Fetched {len(prs)} PRs (total: {total})", file=sys.stderr)

    # Apply filters
    if args.repo_filter:
        prs = filter_prs(prs, repo=args.repo_filter)
    if args.author:
        prs = filter_prs(prs, author=args.author)
    if args.title_contains:
        prs = filter_prs(prs, title_contains=args.title_contains)

    if args.verbose:
        print(f"After filtering: {len(prs)} PRs", file=sys.stderr)

    # Format and output
    output = format_output(prs, args.format, args.fields)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        if args.verbose:
            print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()