#!/usr/bin/env python3
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2026. All rights reserved.
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
Delete personal fork repository on atomgit.com
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.error


def delete_repo(owner: str, repo: str, token: str) -> bool:
    """
    Delete a repository on atomgit

    Args:
        owner: Repository owner (username)
        repo: Repository name
        token: Personal access token

    Returns:
        True if successful, False otherwise
    """
    url = f"https://api.atomgit.com/api/v5/repos/{owner}/{repo}"

    # Add access token to URL
    if '?' in url:
        url += "&"
    else:
        url += "?"
    url += f"access_token={token}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW 64; rv:50.0) Gecko/20100101 Firefox/50.0'
    }

    req = urllib.request.Request(url=url, headers=headers, method="DELETE")

    try:
        result = urllib.request.urlopen(req)
        response = result.read().decode("utf-8")
        print(f"Successfully deleted repository: {owner}/{repo}")
        return True
    except urllib.error.HTTPError as err:
        print(f"ERROR: Failed to delete repository {owner}/{repo}")
        print(f"HTTP Error {err.code}: {err.reason}")
        print(f"Headers: {err.headers}")
        return False
    except urllib.error.URLError as err:
        print(f"ERROR: Failed to delete repository {owner}/{repo}")
        print(f"URL Error: {err.reason}")
        return False


def load_token() -> dict:
    """
    Load personal access token from config file

    Returns:
        Dictionary containing access token and user info
    """
    token_file = os.path.expanduser("~/.atomgit_personal_token.json")

    if not os.path.exists(token_file):
        print(f"ERROR: Token file not found: {token_file}")
        print("Please create the file with your atomgit personal access token.")
        sys.exit(1)

    try:
        with open(token_file, "r") as f:
            token_data = json.load(f)
            return token_data
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in token file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read token file: {e}")
        sys.exit(1)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Delete personal fork repository on atomgit.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Delete a specific repository
  python delete_personal_repo.py my-repo

  # Delete repository with explicit owner
  python delete_personal_repo.py --owner username my-repo

  # Delete multiple repositories
  python delete_personal_repo.py repo1 repo2 repo3
        """
    )

    parser.add_argument(
        "repos",
        nargs="+",
        help="Repository name(s) to delete (can specify multiple)"
    )

    parser.add_argument(
        "--owner",
        help="Repository owner (default: use username from token file)",
        default=None
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )

    parser.add_argument(
        "--token-file",
        help="Path to token file (default: ~/.atomgit_personal_token.json)",
        default=None
    )

    args = parser.parse_args()

    # Load token
    if args.token_file:
        token_path = os.path.expanduser(args.token_file)
        if not os.path.exists(token_path):
            print(f"ERROR: Token file not found: {token_path}")
            sys.exit(1)
        try:
            with open(token_path, "r") as f:
                token_data = json.load(f)
        except Exception as e:
            print(f"ERROR: Failed to read token file: {e}")
            sys.exit(1)
    else:
        token_data = load_token()

    access_token = token_data.get("access_token")
    if not access_token:
        print("ERROR: access_token not found in token file")
        sys.exit(1)

    # Determine owner
    owner = args.owner
    if not owner:
        owner = token_data.get("user")
        if not owner:
            print("ERROR: No owner specified and 'user' not found in token file")
            print("Please specify --owner or add 'user' field to token file")
            sys.exit(1)

    # Delete repositories
    success_count = 0
    fail_count = 0

    for repo in args.repos:
        print(f"\n{'='*60}")
        if args.dry_run:
            print(f"[DRY RUN] Would delete: {owner}/{repo}")
        else:
            print(f"Deleting: {owner}/{repo}")
            if delete_repo(owner, repo, access_token):
                success_count += 1
            else:
                fail_count += 1

    # Summary
    print(f"\n{'='*60}")
    if args.dry_run:
        print(f"DRY RUN: Would delete {len(args.repos)} repository(ies)")
    else:
        print(f"Summary: {success_count} succeeded, {fail_count} failed")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
