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
# ******************************************************************************/
"""
Responsible repositories module for openEuler-Advisor.
This module provides functions to get repositories that the current user is a committer for.
It can be used as a standalone tool or imported by oe_review.
"""
import json
import yaml
from typing import List, Tuple, Dict, Any, Optional, Callable


def get_responsible_repos(user_git, filter_dict: Dict[str, Any], api: str = "gitcode",
                          verbose_func: Callable[[str, int], None] = None) -> List[str]:
    """
    Get repositories that the current user is a committer for.

    Args:
        user_git: Gitee or Gitcode API instance
        filter_dict: Filter configuration dictionary with 'sigs' and 'repos' keys
        api: API platform, either "gitcode" or "gitee" (default: "gitcode")
        verbose_func: Function for verbose logging (default: None)

    Returns:
        List of repository names (format: "owner/repo" or "group/repo") that the current user is a committer for
    """
    def verbose(msg: str, level: int = 2):
        if verbose_func:
            verbose_func(msg, level)
        elif level <= 1:  # Always print errors if no verbose_func
            print(msg)

    current_user = user_git.token['user'].lower()
    result = []

    # Get all SIGs
    sigs = user_git.get_sigs()
    verbose(f"Found {len(sigs)} SIGs", 2)

    for sig_name in sigs:
        # Skip filtered SIGs
        if sig_name in filter_dict.get("sigs", []):
            verbose(f"SIG {sig_name} is filtered", 3)
            continue

        # Skip special entries
        if sig_name == "sig-minzuchess" or sig_name == "README.md":
            continue

        # Get SIG info
        sig_info_str = user_git.get_sig_info(sig_name)
        if sig_info_str is None:
            verbose(f"Failed to get sig-info.yaml for {sig_name}", 2)
            continue

        try:
            sig_info = yaml.load(sig_info_str, Loader=yaml.FullLoader)
        except yaml.YAMLError as e:
            verbose(f"Failed to parse sig-info.yaml for {sig_name}: {e}", 2)
            continue

        # Check if SIG has repositories field
        if "repositories" not in sig_info:
            verbose(f"SIG {sig_name} has no repositories field", 3)
            continue

        repositories_data = sig_info["repositories"]
        if not repositories_data:
            verbose(f"SIG {sig_name} has empty repositories", 3)
            continue

        # Process repositories
        repo_count = 0
        for repo_entry in repositories_data:
            # repo_entry might be a YAML string or a dict
            if isinstance(repo_entry, str):
                try:
                    repo_data = yaml.load(repo_entry, Loader=yaml.FullLoader)
                except yaml.YAMLError as e:
                    verbose(f"Failed to parse repository YAML in {sig_name}: {e}", 2)
                    continue
            else:
                repo_data = repo_entry

            # Check for repo field (list of repositories)
            if "repo" not in repo_data:
                verbose(f"No 'repo' field in repository entry for {sig_name}", 3)
                continue

            repo_list = repo_data["repo"]
            if not repo_list:
                continue

            # Check committers
            committers = repo_data.get("committers", [])

            # Check if current user is a committer
            user_is_committer = False
            for committer in committers:
                if isinstance(committer, str):
                    # committer is a string (username)
                    if committer.lower() == current_user:
                        user_is_committer = True
                        break
                elif isinstance(committer, dict):
                    # committer is a dict with gitee_id/atomgit_id fields
                    git_id = ""
                    if api == "gitcode":
                        git_id = committer.get("atomgit_id", "").lower()
                    elif api == "gitee":
                        git_id = committer.get("gitee_id", "").lower()

                    if git_id == current_user:
                        user_is_committer = True
                        break

            if user_is_committer:
                result.append(repo_list)
                repo_count += len(repo_list)

        if repo_count > 0:
            verbose(f"Found {repo_count} repositories in SIG {sig_name} where user is committer", 2)

    verbose(f"Total repositories where user is committer: {len(result)}", 1)
    return result


# Standalone tool entry point
if __name__ == "__main__":
    import argparse
    import sys
    import os

    parser = argparse.ArgumentParser(description="Get repositories that the current user is a committer for")
    parser.add_argument("--api", type=str, default="gitcode", choices=["gitcode", "gitee"],
                        help="Select API platform: gitcode or gitee (default: gitcode)")
    parser.add_argument("--filter-sigs", type=str, default="",
                        help="Comma-separated list of SIGs to filter out")
    parser.add_argument("--filter-repos", type=str, default="",
                        help="Comma-separated list of repositories to filter out (format: owner/repo)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    # Simple verbose function for standalone use
    def simple_verbose(msg: str, level: int = 2):
        if args.verbose or level <= 1:
            print(msg)

    # Add parent directory to path to import advisors module
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    try:
        # Import the appropriate API module
        if args.api == "gitcode":
            from advisors import gitcode
            api_instance = gitcode.Gitcode()
        else:  # args.api == "gitee"
            from advisors import gitee
            api_instance = gitee.Gitee()
    except Exception as e:
        print(f"ERROR: Failed to initialize {args.api} API: {e}")
        print("Make sure you have the appropriate token file:")
        if args.api == "gitcode":
            print("  ~/.atomgit_personal_token.json")
        else:
            print("  ~/.gitee_personal_token.json")
        sys.exit(1)

    # Parse filter SIGs and repos
    filter_sigs = set()
    if args.filter_sigs:
        filter_sigs = set(sig.strip() for sig in args.filter_sigs.split(",") if sig.strip())

    filter_repos = set()
    if args.filter_repos:
        filter_repos = set(repo.strip() for repo in args.filter_repos.split(",") if repo.strip())

    filter_dict = {
        "sigs": filter_sigs,
        "repos": filter_repos
    }

    simple_verbose(f"Getting responsible repos for user: {api_instance.token['user']}", 1)
    simple_verbose(f"Filtering SIGs: {filter_sigs}", 2)
    simple_verbose(f"Filtering repos: {filter_repos}", 2)

    try:
        repos = get_responsible_repos(api_instance, filter_dict, args.api, simple_verbose)

        if args.json:
            output = {
                "user": api_instance.token['user'],
                "api_platform": args.api,
                "responsible_repos": repos,
                "count": len(repos)
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            if repos:
                print(f"Repositories where {api_instance.token['user']} is a committer ({args.api}):")
                for repo in sorted(repos):
                    print(f"  - {repo}")
                print(f"\nTotal: {len(repos)} repository(ies)")
            else:
                print(f"No repositories found where {api_instance.token['user']} is a committer")

    except Exception as e:
        print(f"ERROR: Failed to get responsible repositories: {e}")
        sys.exit(1)
