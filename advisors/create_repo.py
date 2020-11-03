#!/usr/bin/env python3
#******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
#
# ******************************************************************************/
"""
This is a command line tool for adding new repo
"""

import sys
import argparse
import yaml


def main():
    """
    Main entrance for command line
    """
    par = argparse.ArgumentParser()
    par.add_argument("-r", "--repo", help="YAML file for repositories", type=str, required=True)
    par.add_argument("-i", "--sigs", help="YAML file for sigs", type=str, required=True)
    par.add_argument("-s", "--sig", help="Sig manage this repo", type=str, required=True)
    par.add_argument("-n", "--name", help="Name for new repo", type=str, required=True)
    par.add_argument("-d", "--desc", help="Description for new repo", type=str, required=True)
    par.add_argument("-u", "--upstream", help="Upstream for new repo", type=str, required=True)

    args = par.parse_args()

    with open(args.sigs) as sigs_file:
        sigs = yaml.load(sigs_file.read(), Loader=yaml.Loader)
        if not sigs:
            print("Failed to load {file}".format(file=args.sigs))
            sys.exit(1)

    with open(args.repo) as repo_file:
        repo = yaml.load(repo_file.read(), Loader=yaml.Loader)
        if not repo:
            print("Failed to load {file}".format(file=args.repo))
            sys.exit(1)

    repo_info = {}
    repo_info["name"] = args.name
    repo_info["description"] = args.desc
    repo_info["upstream"] = args.upstream
    repo_info["protected_branches"] = ["master"]
    repo_info["type"] = "public"

    exist = [x for x in repo["repositories"] if x["name"] == args.name]
    if exist != []:
        print("Repo already exist")
        sys.exit(1)

    if repo["community"] == "openeuler":
        repo["repositories"].append(repo_info)
    elif repo["community"] == "src-openeuler":
        repo_info["upstream"] = args.upstream
        repo["repositories"].append(repo_info)

    repo["repositories"].sort(key=lambda r: r["name"])

    valid_sig = False
    for sig in sigs["sigs"]:
        if sig["name"] == args.sig:
            sig["repositories"].append(repo["community"] + "/" + args.name)
            sig["repositories"].sort()
            valid_sig = True
            continue

    if valid_sig:
        with open(args.repo, "w") as repo_file:
            yaml.dump(repo, repo_file)
        with open(args.sigs, "w") as sigs_file:
            yaml.dump(sigs, sigs_file)
    else:
        print("SIG name is not valid")
        sys.exit(1)


if __name__ == "__main__":
    main()
