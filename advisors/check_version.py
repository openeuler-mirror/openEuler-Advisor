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
This is an automatic script for checking source url of package
"""
import os
import argparse
from advisors import gitee
from advisors.oa_upgradable import main_process


def get_repos_by_sig(sig):
    """
    Get repos by sig
    """
    user_gitee = gitee.Gitee()
    yaml_data = user_gitee.get_sigs()

    repo_list = []
    for sigs in yaml_data['sigs']:
        if sig not in (sigs['name'], 'all'):
            continue
        repo_name = sigs['repositories']
        repo_list.append(repo_name)
    repo_list = [i for item in repo_list for i in item]
    return repo_list


def main():
    """
    Main process of the functionality
    """
    parameters = argparse.ArgumentParser()
    parameters.add_argument("-p", "--push", action="store_true",
                            help="Push the version bump as an issue to src-openeuler repository")

    parameters.add_argument("-d", "--default", type=str, default=os.getcwd(),
                            help="The fallback place to look for YAML information")

    parameters.add_argument("-s", "--sig",
                            help="Check yaml by Sig")

    args = parameters.parse_args()
    if args.sig:
        sig = args.sig
    else:
        sig = 'all'

    repos = get_repos_by_sig(sig)

    for repo in repos:
        url = repo.split('/')[0]
        if url == 'openeuler':
            continue
        try:
            main_process(args.push, args.default, repo.split('/')[1])
        except Exception as error:
            print("ERROR: Command execution error", error)


if __name__ == "__main__":
    main()
