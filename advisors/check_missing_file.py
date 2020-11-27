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
This is a simple script to check if files already been submit into repository.
If not, it can be used to push an issue to remind the developer.
"""

import sys
import argparse
from datetime import datetime

from advisors import gitee


NEW_SPEC_ISSUE_BODY = """Dear {repo} maintainer:
亲爱的 {repo} 维护者：

We found there is no spec file in this repository's master branch yet.
我们发现这个代码仓 master branch 中没有 spec 文件。

Missing spec file implies that this components will not be integtaed into latest openEuler release, and your hardworking cannot help others.
缺少 spec 文件意味着这个项目还不能被集成到 openEuler 项目中，而您的贡献还不能帮助到社区中的其他人。

We courage you submit your spec file into this repository as soon as possible.
我们鼓励您尽快提交 spec 文件到这个代码仓中.

This is a automatic advise from openEuler-Advisor. If you think the advise is not correct, please fill an issue at https://gitee.com/openeuler/openEuler-Advisor to help us improve.
这是一条由 openEuler-Advisor 自动生成的建议。如果您认为这个建议不对，请访问 https://gitee.com/openeuler/openEuler-Advisor 来帮助我们改进。

Yours openEuler Advisor.
"""

NEW_YMAL_ISSUE_BODY = """Dear {repo} maintainer:
亲爱的 {repo} 维护者：

We found there is no yaml file in this repository's master branch yet.
我们发现这个代码仓 master branch 中没有 yaml 文件。

Missing yaml file implies that this components will not upgrade automatic.
缺少 yaml 文件意味着这个项目还不能自动升级。

We courage you submit your yaml file into this repository as soon as possible.
我们鼓励您尽快提交 yaml 文件到这个代码仓中.

This is a automatic advise from openEuler-Advisor. If you think the advise is not correct, please fill an issue at https://gitee.com/openeuler/openEuler-Advisor to help us improve.
这是一条由 openEuler-Advisor 自动生成的建议。如果您认为这个建议不对，请访问 https://gitee.com/openeuler/openEuler-Advisor 来帮助我们改进。

Yours openEuler Advisor.
"""

NEW_COMMENT = """Dear {repo} maintainer:

We found this issue has been open for {days} days.

If you have any problems to implement it, please let the community known.

We'll try to help.

This is a automatic advise from openEuler-Advisor. If you think the advise is not correct, please fill an issue at https://gitee.com/openeuler/openEuler-Advisor to help us imporove.

Yours openEuler Advisor.
"""

def get_repos_by_sig(sig):
    """
    Get repos by sig
    """
    try:
        user_gitee = gitee.Gitee()
    except NameError:
        sys.exit(1)
    yaml_data = user_gitee.get_sigs()

    repo_list = []
    for sigs in yaml_data['sigs']:
        if sig not in (sigs['name'], 'all'):
            continue
        repo_name = sigs['repositories']
        repo_list.append(repo_name)
    repo_list = [i for item in repo_list for i in item]
    return repo_list

def main_process(repo, push, check_file):
    """
    Main process for command line
    """
    try:
        my_gitee = gitee.Gitee()
    except NameError:
        sys.exit(1)
    if check_file == 'yaml':
        file = my_gitee.get_yaml(repo)
    elif check_file == 'spec':
        file = my_gitee.get_spec(repo)
    else:
        print("ERROR: Not support {file} check".format(file=check_file))
        return 'NOK'

    if not file:
        print("no {file} file found for {repo} project".format(file=check_file, repo=repo))
        if push:
            issues = my_gitee.get_issues(repo)
            for issue in issues:
                if issue["title"] == "Submit {file} file into this repository".format(
                        file=check_file):
                    ages = datetime.now() - my_gitee.get_gitee_datetime(issue["created_at"])
                    if ages.days <= 10:
                        print("Advise has been issues only %d days ago" % ages.days)
                        print("Give developers more time to handle it.")
                        break
                    my_gitee.post_issue_comment(repo, issue["number"], NEW_COMMENT.format(
                                                repo=repo,
                        days=ages.days))
                    break
            else:
                if check_file == 'spec':
                    my_gitee.post_issue(repo,
                                        "Submit {file} file into this repository".format(
                                            file=check_file),
                                        NEW_SPEC_ISSUE_BODY.format(repo=repo,
                                                                   file=check_file))
                else:
                    my_gitee.post_issue(repo,
                                        "Submit {file} file into this repository".format(
                                            file=check_file),
                                        NEW_YMAL_ISSUE_BODY.format(repo=repo,
                                                                   file=check_file))
        return 'NOK'
    return 'OK'


def main():
    """
    Main process for command line
    """
    pars = argparse.ArgumentParser()
    pars.add_argument("-s", "--sig", type=str, default='all', help="Sig name")
    pars.add_argument("-p", "--push",
                      help="Push the advise to gitee.com/src-openeuler",
                      action="store_true")
    pars.add_argument("-f", "--file", type=str, default='spec',
                      help="File name want to check, spec or yaml?")
    args = pars.parse_args()

    if args.file not in ('spec', 'yaml'):
        print("ERROR: Not support {file} check".format(file=args.file))
        return

    repos = get_repos_by_sig(args.sig)
    if not repos:
        print("ERROR: no repos find is {sig} sig, please check the sig name.".format(
            sig=args.sig))
        return
    fail_list = []

    total = len(repos)
    index = 0
    for repo in repos:
        index = index + 1
        url = repo.split('/')[0]
        if url == 'openeuler':
            continue
        check_repo = repo.split('/')[1]
        result = main_process(check_repo, args.push, args.file)
        if result != 'OK':
            fail_list.append(check_repo)

        print("INFO: {index} in {total} check {repo} {file} {result}".format(index=index,
                                                                             total=total,
                                                                             repo=check_repo,
                                                                             file=args.file,
                                                                             result=result))
    if fail_list:
        print('The repos listed below check {file} failed:'.format(file=args.file))
        for repo in fail_list:
            print(repo)

if __name__ == "__main__":
    main()
