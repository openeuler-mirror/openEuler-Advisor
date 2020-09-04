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

from pyrpm.spec import Spec, replace_macros
import argparse
import gitee
import os
import re
import sys
import yaml
import subprocess
import threading
import math


def check_repo(repo, branch, batch_num):
    """
    Check source url of multi-packages in repo like src-openeuler.
    batch_num is batch num of one thread
    """
    gt = gitee.Gitee()
    repo_info = gt.get_community(repo)
    if not repo_info:
        print("WARNING: {repo}.yaml can't be found in community.".format(repo=repo))
        sys.exit(1)
    repo_yaml = yaml.load(repo_info, Loader=yaml.Loader)
    repo_list = repo_yaml.get("repositories")
    thread_num = math.ceil(len(repo_list)/batch_num)
    threads = []
    lock = threading.Lock()
    for number in range(thread_num):
        thread= threading.Thread(target=check_batch, args=(repo_list, branch, number, batch_num, lock))
        threads.append(thread)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("Ending check.")


def create_issue(repo, title, body):
    """
    Create issue for repo
    """
    gt = gitee.Gitee()
    created_issue = False
    issues = gt.get_issues(repo)
    for issue in issues:
        if issue["title"] == title:
            created_issue = True
            break
    if not created_issue:
        gt.post_issue(repo, title, body)


def check_batch(repo_list, branch, number, batch_num, lock):
    """
    Check source url in one batch
    """
    gt = gitee.Gitee()
    body_source = """Dear Maintainer:
                  Due to source url problem checked by openEuler-Advisor, please solve it as soon as
                  possible and check other branch too.
                  If any problem, please create issue in https://gitee.com/openeuler/openEuler-Advisor.
                  Thanks.
                  Yours openEuler-Advisor"""
    body_spec = """Dear Maintainer:
                Due to spec can't be found by openEuler-Advisor, please add it as soon as possible 
                and check other branch too.
                If any problem, please create issue in https://gitee.com/openeuler/openEuler-Advisor.
                Thanks.
                Yours openEuler-Advisor"""
    file_str = "result_" + "{num}.log".format(num=number)
    file_name = open(file_str, "w+")
    for n in range(batch_num):
        index = number * batch_num + n
        if index < len(repo_list):
            repo_name = repo_list[index].get("name")
        else:
            break
        file_name.writelines("\n-----------------------Checking {repo}-----------------------".format(repo=repo_name))
        lock.acquire()
        spec_str = gt.get_spec(repo_name, branch)
        lock.release()
        if not spec_str:
            file_name.writelines("WARNING: {repo}.spec can't be found on {br}".format(repo=repo_name, br=branch))
            title = "Submit spec file into this repository"
            ####create_issue(repo_name, title, body_spec) 
            continue

        repo_spec = Spec.from_string(spec_str)
        if repo_spec.sources_dict:
            source = replace_macros(repo_spec.sources[0], repo_spec)
        else:
            title = "Source url can't be found in spec on {br}".format(br=branch)
            file_name.writelines("WARNING: {content}".format(content=title))
            create_issue(repo_name, title, body_source)
            continue
        
        if re.search(r"%{.*?}", source):
            title = "Source url can't be parsed with extra macros in spec on {br}.".format(br=branch)
            file_name.writelines("WARNING: {content}".format(content=title))
            create_issue(repo_name, title, body_source)
            continue
        elif source.startswith("http") or source.startswith("ftp"):
            fn = os.path.basename(source)
            n = 0
            lock.acquire()
            while n < 2:
                n += 1
                if subprocess.call(["curl -m 600 -L {url} -o {name}".format(url=source, name=fn)], shell=True):
                    continue
                else:
                    break
            lock.release()
            title = "Source url may be wrong in spec on {br}.".format(br=branch)
            if os.path.exists(fn):
                if subprocess.call(["tar -tvf {file_name} &>/dev/null".format(file_name=fn)], shell=True):
                    file_name.writelines("WARNING: {content}".format(content=title))
                    create_issue(repo_name, title, body_source)
                else:
                    file_name.writelines("Check successfully.")
                subprocess.call(["rm -rf {file_name}".format(file_name=fn)], shell=True)
            else:
                file_name.writelines("WARNING: {content}".format(content=title))
                create_issue(repo_name, title, body_source)
        else:
            title = "Source url is invalid in spec on {br}.".format(br=branch)
            file_name.writelines("WARNING: {content}".format(content=title))
            create_issue(repo_name, title, body_source)
            continue


def check_pkg(pkg, branch):
    """
    Check source url of single package
    """
    gt = gitee.Gitee()
    print("\n-----------------------Checking {repo}-----------------------".format(repo=pkg))
    spec_str = gt.get_spec(pkg, branch)
    if not spec_str:
        print("WARNING: {repo}.spec can't be found on {branch}".format(repo=pkg, branch=branch))
        created_issue = False
        issues = gt.get_issues(pkg)
        for issue in issues:
            if issue["title"] == "Submit spec file into this repository":
                created_issue = True
                break
            if not created_issue:
                title = "Submit spec file into this repository"
                print(title)
        sys.exit(1)
    repo_spec = Spec.from_string(spec_str)
    if repo_spec.sources_dict:
        source = replace_macros(repo_spec.sources[0], repo_spec)
    else:
        print("No source url")
        sys.exit(1)
    if re.search(r"%{.*?}", source):
        print("WARNING: Extra macros in source url which failed to be expanded.")
        sys.exit(1)
    elif source.startswith("http") or source.startswith("ftp"):
        fn = os.path.basename(source)
        n = 0
        while n < 2:
            n += 1
            if subprocess.call(["curl -m 600 -L {url} -o {name}".format(url=source, name=fn)], shell=True):
                continue
            else:
                break

        if os.path.exists(fn):
            if subprocess.call(["tar -tvf {file_name} &>/dev/null".format(file_name=fn)], shell=True):
                print("WARNING: source url of {repo} may be wrong.".format(repo=pkg))
            else:
                print("Check successfully.")
        else:
            print("WARNING: source url of {repo} may be wrong.".format(repo=pkg))
    else:
        print("WARNING: Not valid URL for Source code.")
        sys.exit(1)


if __name__ == "__main__":
    pars = argparse.ArgumentParser()
    pars.add_argument("-r", "--repo", type=str, help="The repository to be check.")
    pars.add_argument("-p", "--pkg", type=str, help="The package to be check.")
    pars.add_argument("-b", "--batch_num", type=int, default=100, help="The batch num of one task.")
    pars.add_argument("branch", type=str, help="The branch to be check.")
    args = pars.parse_args()

    if args.repo:
        check_repo(args.repo, args.branch, args.batch_num)
    elif args.pkg:
        check_pkg(args.pkg, args.branch)
    else:
        print("WARNING: Please specify what to be checkd.")
        sys.exit(1)
