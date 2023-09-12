#!/usr/bin/env python3
# ******************************************************************************
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
import sys
import argparse
import time
from advisors import gitee
from advisors.oa_upgradable import main_process
from advisors import advisor_common
import time


def main():
    """
    Main process of the functionality
    """
    parameters = argparse.ArgumentParser()
    parameters.add_argument("-p", "--push", action="store_true",
                            help="Push the version bump as an issue to src-openeuler repository")

    parameters.add_argument("-d", "--default", type=str, default=os.getcwd(),
                            help="The fallback place to look for YAML information")

    parameters.add_argument("-s", "--sig", type=str, default="sig-recycle",
                            help="Check yaml by Sig")

    args = parameters.parse_args()
    if args.sig:
        sig = args.sig
    else:
        sig = 'sig-recycle'

    repos = advisor_common.get_repos_by_openeuler_sig(sig)

    total = len(repos)
    index = 0
    upgrade_list = []
    for repo in repos:
        if repo.startswith('openeuler/'):
            continue
        check_repo = repo[len('src-openeuler/'):]
        index = index + 1
        result = main_process(args.push, args.default, check_repo)
        if result:
            if result[1] != result[2]:
                print('''INFO: {index} in {total} check {repo} need upgrade \
from {current} to {latest}'''.format(index=index,
                                     total=total,
                                     repo=result[0],
                                     current=result[1],
                                     latest=result[2]))
                result.append('Y')
                upgrade_list.append(result)
            else:
                result.append('N')
                upgrade_list.append(result)
                print('''INFO: {index} in {total} check {repo} not need \
upgrade'''.format(index=index,
                  total=total,
                  repo=check_repo))
        else:
            upgrade_list.append([check_repo, '-', '-', '-'])
            print('''INFO: {index} in {total} check {repo} \
latest version failed.'''.format(index=index,
                                 total=total,
                                 repo=check_repo))

    if upgrade_list:
        print("Repo upgrade check result:")
        for upgrade_repo in upgrade_list:
            print("{repo}   {current}   {latest}    {upgrade}".format(repo=upgrade_repo[0],
                                                                      current=upgrade_repo[1],
                                                                      latest=upgrade_repo[2],
                                                                      upgrade=upgrade_repo[3]))


if __name__ == "__main__":
    main()
