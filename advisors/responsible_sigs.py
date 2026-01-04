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
Responsible SIGs module for openEuler-Advisor.
This module provides functions to get responsible SIGs for the current user.
It can be used as a standalone tool or imported by oe_review.
"""
import json
import yaml
from typing import List, Tuple, Dict, Any, Optional, Callable


def get_responsible_sigs(user_git, filter_dict: Dict[str, Any], api: str = "gitcode",
                         verbose_func: Callable[[str, int], None] = None) -> List[str]:
    """
    Get responsible SIGs for the current user.

    Args:
        user_git: Gitee or Gitcode API instance
        filter_dict: Filter configuration dictionary with 'sigs' key
        api: API platform, either "gitcode" or "gitee" (default: "gitcode")
        verbose_func: Function for verbose logging (default: None)

    Returns:
        List of SIG names that the current user is responsible for
    """
    def verbose(msg: str, level: int = 2):
        if verbose_func:
            verbose_func(msg, level)
        elif level <= 1:  # Always print errors if no verbose_func
            print(msg)

    sigs = user_git.get_sigs()
    result = []
    for sig in sigs:
        if sig == "sig-minzuchess" or sig == "README.md":
            continue
        if sig in filter_dict.get("sigs", []):
            verbose(f"sig {sig} is filtered", 2)
            continue
        sig_info_str = user_git.get_sig_info(sig)
        if sig_info_str is None:
            continue
        sig_info = yaml.load(sig_info_str, Loader=yaml.FullLoader)
        for maintainer in sig_info["maintainers"]:
            git_id = ""
            if api == "gitcode":
                git_id = maintainer.get("atomgit_id", "").lower()
            elif api == "gitee":
                git_id = maintainer.get("gitee_id", "").lower()
            else:
                git_id = ""
            if git_id == user_git.token['user'].lower():
                result.append(sig_info["name"])
    return result


# Standalone tool entry point
if __name__ == "__main__":
    import argparse
    import sys
    import os

    parser = argparse.ArgumentParser(description="Get responsible SIGs for the current user")
    parser.add_argument("--api", type=str, default="gitcode", choices=["gitcode", "gitee"],
                        help="Select API platform: gitcode or gitee (default: gitcode)")
    parser.add_argument("--filter-sigs", type=str, default="",
                        help="Comma-separated list of SIGs to filter out")
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

    # Parse filter SIGs
    filter_sigs = set()
    if args.filter_sigs:
        filter_sigs = set(sig.strip() for sig in args.filter_sigs.split(",") if sig.strip())

    filter_dict = {"sigs": filter_sigs}

    simple_verbose(f"Getting responsible SIGs for user: {api_instance.token['user']}", 1)
    simple_verbose(f"Filtering SIGs: {filter_sigs}", 2)

    try:
        sigs = get_responsible_sigs(api_instance, filter_dict, args.api, simple_verbose)

        if args.json:
            output = {
                "user": api_instance.token['user'],
                "api_platform": args.api,
                "responsible_sigs": sigs,
                "count": len(sigs)
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            if sigs:
                print(f"Responsible SIGs for {api_instance.token['user']} ({args.api}):")
                for sig in sorted(sigs):
                    print(f"  - {sig}")
                print(f"\nTotal: {len(sigs)} SIG(s)")
            else:
                print(f"No responsible SIGs found for {api_instance.token['user']}")

    except Exception as e:
        print(f"ERROR: Failed to get responsible SIGs: {e}")
        sys.exit(1)