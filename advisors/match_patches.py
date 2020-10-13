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
This module supply the function for patch matching
"""

import os
import re
import shutil
import argparse
import subprocess
import yaml

import gitee
import yaml2url
import oa_upgradable
import simple_update_robot


def _clone_repo(pkg_info):
    """
    Clone repo to local
    """
    repo_url = yaml2url.yaml2url(pkg_info)
    if not (repo_url and pkg_info["version_control"].startswith("git")):
        print("WARNING: Patch matching only support for git repo.")
        return None

    dir_pkg = os.path.basename(repo_url).split(".")[0]
    if os.path.exists(dir_pkg):
        shutil.rmtree(dir_pkg, ignore_errors=True)

    print("git clone {url}".format(url=repo_url))
    subprocess.call(["git clone {url}".format(url=repo_url)], shell=True)
    if os.path.exists(dir_pkg):
        return dir_pkg

    print("WARING: Clone failed, {} not exist.".format(dir_pkg))
    return None


def _get_commits_info(gt_api, pkg, c_ver, u_ver):
    """
    Get commits info of package within two version release
    """
    pkg_info = gt_api.get_yaml(pkg)
    if not pkg_info:
        return None

    pkg_yaml = yaml.load(pkg_info, Loader=yaml.Loader)
    separa = pkg_yaml.get("separator")
    if not separa:
        print("WARNING: Keyword of separator can't be found in {}.yaml".format(pkg))
        return None

    pkg_tags = oa_upgradable.get_ver_tags(gt_api, pkg, clean_tag=False)

    c_tag = ""
    u_tag = ""
    for tag in pkg_tags:
        if re.search(r"\d[a-z]\d*|rc\d*$|dev\d*$|beta\d*$|"\
                r"alpha.*$|pl\d*$|pre\d*$|bp\d*$", tag, re.I):
            continue
        if c_ver in tag or c_ver.replace(".", separa) in tag:
            c_tag = tag
        elif u_ver in tag or u_ver.replace(".", separa) in tag:
            u_tag = tag

    if not c_tag or not u_tag:
        print("WARNING: current version tag or upgrade version tag can't be found in repository.")
        return None

    dir_pkg = _clone_repo(pkg_yaml)
    if dir_pkg:
        os.chdir(dir_pkg)
        print("git log -p {t1}...{t2}".format(t1=u_tag, t2=c_tag))
        commit_str = subprocess.check_output(["git log -p {t1}...{t2}".format(
            t1=u_tag, t2=c_tag)], shell=True).decode('ISO-8859-1').strip('\n')
        os.chdir(os.pardir)
        shutil.rmtree(dir_pkg, ignore_errors=True)
    else:
        return None

    if not commit_str:
        print("WARNING: No commits between {t1} and {t2}.".format(t1=u_tag, t2=c_tag))
    return commit_str


def patches_match(gt_api, pkg, c_ver, u_ver):
    """
    Patches match function for pkg on src-openeuler
    when patch all matched, then return 'patch_name': all
    when patch part matched, then return 'patch_name': matched index number
    """
    commit_str = _get_commits_info(gt_api, pkg, c_ver, u_ver)
    if not commit_str:
        return None

    patch_match = {}
    for file_name in os.listdir("./"):
        if not file_name.endswith(".patch"):
            continue
        patch_file = open("./{fn}".format(fn=file_name), "r")
        index_match = []
        part_matched = False
        for line in patch_file.readlines():
            if re.match("index", line):
                index_head = line[0:13]
                index_tail = re.findall(r'\.\..{7}', line)[0]
                if index_head and index_tail in commit_str:
                    index_match.append(line.strip('\n'))
                else:
                    part_matched = True

        if len(index_match) > 0:
            if part_matched:
                patch_match[file_name] = index_match
            else:
                patch_match[file_name] = "all"
    print(patch_match)
    return patch_match


if __name__ == "__main__":
    pars = argparse.ArgumentParser()
    pars.add_argument("pkg", type=str, help="The package to be matched.")
    pars.add_argument("branch", type=str, help="Branch to be matched.")
    pars.add_argument("cur_ver", type=str, help="Current version of package.")
    pars.add_argument("up_ver", type=str, help="Upgrade version of package.")
    args = pars.parse_args()

    user_gitee = gitee.Gitee()
    simple_update_robot.fork_clone_repo(user_gitee, args.pkg, args.branch)
    os.chdir(args.pkg)
    patches_match(user_gitee, args.pkg, args.cur_ver, args.up_ver)
    os.chdir(os.pardir)
