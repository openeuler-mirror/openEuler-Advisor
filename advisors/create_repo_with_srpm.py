#!/usr/bin/python3
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

from os import path
import sys
import argparse
import subprocess
import yaml


def get_info(pkg):
    """
    Get package rpm information
    """
    pkg_info = {}
    proc = subprocess.Popen(["rpm", "-qpi", pkg], stdout=subprocess.PIPE)
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        info = str(line.strip().decode()).split(':')
        if len(info) < 2:
            continue
        info[0] = info[0].strip()
        info[1] = info[1].strip()
        if info[0] == "Name":
            pkg_info["name"] = info[1]
        elif info[0] == "Summary":
            pkg_info["description"] = info[1]
        elif info[0] == "URL":
            if len(info) >= 3:
                pkg_info["upstream"] = info[1] + ":" + info[2]
            else:
                pkg_info["upstream"] = info[1]

    proc.stdout.close()
    proc.wait()
    return pkg_info


def check_repo(repo):
    """
    Check the condition for repo create
    """
    if path.exists(repo) and path.isfile(repo):
        pkg_info = get_info(repo)
        if len(pkg_info) < 3:
            print("Failed to parse the output of rpm -qpi {pkg}".format(pkg=repo))
            sys.exit(1)
    else:
        print("%s does not exist\n" & repo)
        sys.exit(1)


def main():
    """
    Main entrance for command line
    """
    par = argparse.ArgumentParser()
    par.add_argument("-r", "--repo", help="YAML file for repositories", type=str, required=True)
    par.add_argument("-i", "--sigs", help="YAML file for sigs", type=str, required=True)
    par.add_argument("-s", "--sig", help="The SIG which contains the package",
                     type=str, required=True)
    par.add_argument("-p", "--pkg", help="Package for upoad", type=str, required=True)
    args = par.parse_args()

    pkg_info = {}

    check_repo(args.pkg)

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

    pkg_info["protected_branches"] = ["master"]
    pkg_info["type"] = "public"

    exist = [x for x in repo["repositories"] if x["name"] == pkg_info["name"]]
    if exist != []:
        print("Repo already exist")
        sys.exit(1)

    if repo["community"] == "openeuler":
        del pkg_info["upstream"]
        repo["repositories"].append(pkg_info)
    elif repo["community"] == "src-openeuler":
        repo["repositories"].append(pkg_info)

    repo["repositories"].sort(key=lambda r: r["name"])

    valid_sig = False
    for sig in sigs["sigs"]:
        if sig["name"] == args.sig:
            sig["repositories"].append(repo["community"] + "/" + pkg_info["name"])
            sig["repositories"].sort()
            valid_sig = True
            continue

    if valid_sig:
        with open(args.repo, "w") as repo_file:
            yaml.dump(repo, repo_file, sort_keys=False)
        with open(args.sigs, "w") as sigs_file:
            yaml.dump(sigs, sigs_file, sort_keys=False)
    else:
        print("SIG name is not valid")
        sys.exit(1)

    print("create repo %s successfully\n" % pkg_info["name"])
    sys.exit(0)


if __name__ == "__main__":
    main()
