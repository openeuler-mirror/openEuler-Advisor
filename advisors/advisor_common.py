#!/usr/bin/python3
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2023. All rights reserved.
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
Common functions for openEuler-Advisor tools
"""
import os
import re
import sys
import argparse
import subprocess
import shutil
import urllib
import yaml

from advisors import gitee

def exec_cmd(cmd, retry_times=0):
    subp = subprocess.run(cmd,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          encoding="utf-8",
                          check=False)
    if subp.returncode != 0 and retry_times > 0:
        for i in range(1, retry_times + 1):
            print("cmd:%s execute failed,retry:%d" % (cmd, i))
            subp = subprocess.run(cmd,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                  encoding="utf-8",
                                  check=False)
            if subp.returncode == 0:
                break
    print(subp.stdout)
    return subp.returncode

def prepare_gitee_repo(work_dir, reuse, group, repo_name, branch):
    """
    prepare local repository
    """
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)

    repo = group + "/" + repo_name

    gitee_url = "https://gitee.com/{repo}.git".format(repo=repo)

    local_path = os.path.join(work_dir, "{}_{}".format(group, repo_name))

    if os.path.exists(local_path) and not reuse:
        print("%s already exist, delete as we dont reuse" % local_path)
        shutil.rmtree(local_path)

    if not os.path.exists(local_path):
        if exec_cmd(["git", "clone", gitee_url, local_path]) != 0:
            print("ERROR: failed to git clone {}".format(gitee_url))
            return None

    previous_dir = os.getcwd()
    os.chdir(local_path)

    if exec_cmd(["git", "checkout", branch]) != 0:
        print("ERROR: failed to git checkout %s branch " % branch)
        os.chdir(previous_dir)
        return None
    if exec_cmd(["git", "pull"]) != 0:
        print("ERROR: failed to update to latest commit in %s branch" % branch)
        os.chdir(previous_dir)
        return None

    os.chdir(previous_dir)
    return local_path


def get_openeuler_sigs():
    """
    return a list of openeuler sigs
    """

    exception_list = ["README.md", "create_sig_info_template.py", "sig-template"]
    exp_set = set(exception_list)
    ipath = prepare_gitee_repo(".", True, "openeuler", "community", "master")
    if ipath == None:
        return None

    sigs = []
    spath = os.path.join(ipath, "sig")
    for f in os.listdir(spath):
        if f in exp_set:
            continue
        sigs.append(f) 

    return sigs

def get_repos_by_openeuler_sig(sig):
    """
    return a list of repos maintained by given openeuler sig
    """
    ipath = prepare_gitee_repo(".", True, "openeuler", "community", "master")
    if ipath == None:
        return None

    repos = []
    spath = os.path.join(ipath, "sig", sig)

    spath_openeuler = os.path.join(spath, "openeuler")
    for r, d, f in os.walk(spath_openeuler):
        for file in f:
            if file.endswith(".yaml"):
                repos.append("openeuler/"+file[:-5])

    spath_srcopeneuler = os.path.join(spath, "src-openeuler")
    for r, d, f in os.walk(spath_srcopeneuler):
        for file in f:
            if file.endswith(".yaml"):
                repos.append("src-openeuler/"+file[:-5])

    return repos


if __name__ == "__main__":
    print(get_openeuler_sigs())
    print(get_repos_by_openeuler_sig('sig-rfo'))
    print(get_repos_by_openeuler_sig('sig-sw-arch'))
