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
This is an automatic script for checking source url of package
"""

import os
import re
import sys
import math
import subprocess
import threading
import argparse
import yaml
from pyrpm.spec import Spec, replace_macros

from advisors import gitee


BODY_SOURCE = """Dear Maintainer:
              Due to source url problem checked by openEuler-Advisor, please solve it as soon as
              possible and check other branch too.
              If any problem, please create issue in https://gitee.com/openeuler/openEuler-Advisor.
              Thanks.
              Yours openEuler-Advisor"""
BODY_SPEC = """Dear Maintainer:
            Due to spec can't be found by openEuler-Advisor, please add it as soon as possible 
            and check other branch too.
            If any problem, please create issue in https://gitee.com/openeuler/openEuler-Advisor.
            Thanks.
            Yours openEuler-Advisor"""


def check_repo(repo, branch, batch_num):
    """
    Check source url of multi-packages in repo like src-openeuler.
    batch_num is batch num of one thread
    """
    try:
        user_gitee = gitee.Gitee()
    except NameError:
        sys.exit(1)
    repo_info = user_gitee.get_community(repo)
    if not repo_info:
        print("WARNING: {repo}.yaml can't be found in community.".format(repo=repo))
        sys.exit(1)
    repo_yaml = yaml.load(repo_info, Loader=yaml.Loader)
    repo_list = repo_yaml.get("repositories")
    thread_num = math.ceil(len(repo_list)/batch_num)
    threads = []
    lock = threading.Lock()
    for number in range(thread_num):
        thread = threading.Thread(target=check_batch, args=(repo_list,
                                                            branch,
                                                            number,
                                                            batch_num,
                                                            lock))
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    print("Ending check.")


def create_issue(user_gitee, repo, title, body):
    """
    Create issue for repo
    """
    created_issue = False
    issues = user_gitee.get_issues(repo)
    for issue in issues:
        if issue["title"] == title:
            created_issue = True
            break
    if not created_issue:
        user_gitee.post_issue(repo, title, body)


def check_batch(repo_list, branch, number, batch_num, lock):
    """
    Check source url in one batch
    """
    file_str = "result_" + "{num}.log".format(num=number)
    batch_file = open(file_str, "w+")
    for batch_index in range(batch_num):
        index = number * batch_num + batch_index
        if index < len(repo_list):
            repo_name = repo_list[index].get("name")
        else:
            break

        check_pkg(repo_name, branch, batch_file, lock)


def check_pkg(pkg, branch, check_file, lock):
    """
    Check source url of single package
    """
    try:
        user_gitee = gitee.Gitee()
    except NameError:
        sys.exit(1)
    check_file.writelines("\n-----------------------Checking {}-----------------------".format(
        pkg))
    lock.acquire()
    spec_str = user_gitee.get_spec(pkg, branch)
    lock.acquire()
    if not spec_str:
        check_file.writelines("WARNING: Spec of {repo} can't be found on {br}".format(repo=pkg,
                                                                                      br=branch))
        return False

    repo_spec = Spec.from_string(spec_str)
    if repo_spec.sources_dict:
        source = replace_macros(repo_spec.sources[0], repo_spec)
    else:
        title = "Source url can't be found in spec on {br}".format(br=branch)
        check_file.writelines("WARNING: {content}".format(content=title))
        create_issue(user_gitee, pkg, title, BODY_SOURCE)
        return False

    if re.search(r"%{.*?}", source):
        title = "Source url can't be parsed with extra macros in spec on {}.".format(branch)
        check_file.writelines("WARNING: {content}".format(content=title))
        create_issue(user_gitee, pkg, title, BODY_SOURCE)
        return False

    if source.startswith("http") or source.startswith("ftp"):
        file_name = os.path.basename(source)
        down_cnt = 0
        lock.acquire()
        while down_cnt < 2:
            down_cnt += 1
            if not subprocess.call(["timeout 15m wget -c {url} -O {name}".format(url=source,
                                                                                 name=file_name)],
                                   shell=True):
                break
        lock.release()

        title = "Source url may be wrong in spec on {br}.".format(br=branch)
        if os.path.exists(file_name):
            if subprocess.call(["tar -tvf {} &>/dev/null".format(file_name)], shell=True):
                check_file.writelines("WARNING: {content}".format(content=title))
                create_issue(user_gitee, pkg, title, BODY_SOURCE)
                result = False
            else:
                check_file.writelines("Check successfully.")
                result = True
            subprocess.call(["rm -rf {}".format(file_name)], shell=True)
        else:
            check_file.writelines("WARNING: {content}".format(content=title))
            create_issue(user_gitee, pkg, title, BODY_SOURCE)
            result = False
        return result

    title = "Source url is invalid in spec on {br}.".format(br=branch)
    check_file.writelines("WARNING: {content}".format(content=title))
    create_issue(user_gitee, pkg, title, BODY_SOURCE)
    return False


def main():
    """
    Main entrance for command line
    """
    pars = argparse.ArgumentParser()
    pars.add_argument("-r", "--repo", type=str, help="The repository to be check.")
    pars.add_argument("-p", "--pkg", type=str, help="The package to be check.")
    pars.add_argument("-b", "--batch_num", type=int, default=100, help="The batch num of one task.")
    pars.add_argument("branch", type=str, help="The branch to be check.")
    args = pars.parse_args()

    if args.repo:
        check_repo(args.repo, args.branch, args.batch_num)
    elif args.pkg:
        check_file = open("check_repo.log", "w")
        lock = threading.Lock()
        check_pkg(args.pkg, args.branch, check_file, lock)
    else:
        print("WARNING: Please specify what to be checkd.")
        sys.exit(1)


if __name__ == "__main__":
    main()
