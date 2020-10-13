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
# ******************************************************************************/
"""
Review tool for openEuler submission
"""
import os
import re
import sys
import argparse
import subprocess
import shutil
import yaml
import gitee

CHK_TABLE_HEADER = """
**以下为 openEuler-Advisor 的 review_tool 生成审视要求清单**
**[Y]** 审视者确认符合要求 | **[N]** 审视者认为不符合要求 | **[NA]** 审视者认为与本PR无关 | **[?]** 审视者无法确认是否符合要求 | **[ ]** 审视过程中
|审视项编号|审视类别|审视要求|审视要求说明|审视结果|
|:--:|:--|:--|:--|:--:|
"""

SANITY_CHK_CMD = "python3 zh/technical-committee/governance/sanity_check.py ."

CHECKLIST = "helper/reviewer_checklist.yaml"

categorizer = {'PRSubmissionSPEC':'PR提交规范',
            'CleanCode':'Clean Code',
            'OpenSourceCompliance':'开源合规性',
            'SecurityPrivacy':'安全及隐私',
            'customization':'定制项'}

__NUMBER = 0


def check_new_code():
    """
    Check if new code file has been introduced
    """
    lst_files = subprocess.getoutput("git diff --name-only --diff-filter=A remotes/origin/master..")
    return bool(lst_files.splitlines())


def check_code_lang():
    """
    Check this PR code programming language
    """
    langs = []
    checkers = []
    lst_files = subprocess.getoutput("git diff --name-only remotes/origin/master..")
    for item in lst_files.splitlines():
        if item.endswith(".py") and "Python" not in langs:
            langs.append("Python")
            checkers.append("pylint-3")
        elif item.endswith(".go") and "GO" not in langs:
            langs.append("GO")
            checkers.append("golint")
        elif item.endswith(".c") and "C/C++" not in langs:
            langs.append("C/C++")
            checkers.append("pclint")
        elif item.endswith(".cpp") and "C/C++" not in langs:
            langs.append("C/C++")
            checkers.append("pclint")
        elif item.endswith(".h") and "C/C++" not in langs:
            langs.append("C/C++")
            checkers.append("pclint")
    return langs, checkers


def load_checklist(chklist_path):
    """
    load configuration
    """
    try:
        with open(chklist_path, 'r', encoding = 'utf-8') as f:
            return yaml.load(f.read(), Loader = yaml.Loader)
    except OSError as reason:
        print("Load yaml failed!" + str(reason))
        return None


def join_check_item(category, claim, explain):
    """
    join check item as a table row
    """
    global __NUMBER
    res = "|" + str(__NUMBER) + "|" + category + "|" + claim + "|" + explain + "|[ ]|\n"
    __NUMBER += 1
    return res


def check_repository_changes():
    """
    check if src-openeuler.yaml has been changed
    """
    lst_files = subprocess.getoutput("git diff --name-only remotes/origin/master..")
    for item in lst_files.splitlines():
        if item.startswith("repository/src-openeuler.yaml"):
            return True
    return False

def check_repository_mgmt_changes(sigs, info):
    """
    Return additional checking item if management of repository has been changed
    """
    review_body = ""
    need_additional_review = False
    ret_code, lst_files = subprocess.getstatusoutput(info['cmd'])
    if ret_code != 0:
        chk = join_check_item(categorizer['customization'],
                info['failed']['claim'], info['failed']['explain'])
        return chk
    for item in lst_files.splitlines():
        if item.startswith("SUGGESTION: This PR needs to be reviewed"):
            need_additional_review = True
            continue
        if need_additional_review:
            result = re.match("([^:]*): (.*)", item)
            if result:
                sig = result.group(1)
                owners = result.group(2)
                if sig not in sigs:
                    chk = join_check_item(categorizer['customization'],
                            info['lgtm-chk']['claim'], info['lgtm-chk']['explain'])
                    review_body += chk.format(sig=sig, owners=owners)
        else:
            result = re.match("WARNING! deleting (.*)", item)
            if result:
                chk = join_check_item(categorizer['customization'],
                        info['dlt-chk']['claim'], info['dlt-chk']['explain'])
                review_body += chk.format(repo=result.group(1))
    if need_additional_review:
        review_body += join_check_item(categorizer['customization'],
                info['success']['claim'], info['success']['explain'])
    return review_body


def check_maintainer_changes():
    """
    return all SIGs with changed maintainer
    """
    sigs = {}
    lst_files = subprocess.getoutput("git diff --name-status remotes/origin/master..")
    for line in lst_files.splitlines():
        status, item = line.split()
        if status != "M":
            continue
        if item.startswith("sig/") and item.endswith("/OWNERS"):
            sig = item.split("/")[1]
            owners = []
            owner_file = subprocess.getoutput("git show remotes/origin/master:" + item)
            for f_line in owner_file.splitlines():
                if f_line.strip().startswith("-"):
                    owner = f_line.replace("- ", "@").strip()
                    owners.append(owner)
            sigs[sig] = " ".join(owners)
    return sigs


def check_sig_information_changes():
    """
    return all SIGs with changed information
    """
    sigs = {}
    lst_files = subprocess.getoutput("git diff --name-status remotes/origin/master..")
    for line in lst_files.splitlines():
        status, item = line.split()
        if status != "M":
            continue
        if item == "sig/sigs.yaml":
            continue
        if item.startswith("sig/") and not item.endswith("/OWNERS"):
            sig = item.split("/")[1]
            owners = []
            owner_fn = item.split("/")[:2]
            owner_fn.append("OWNERS")
            cmd_line = "git show remotes/origin/master:" + "/".join(owner_fn)
            owner_file = subprocess.getoutput(cmd_line)
            for f_line in owner_file.splitlines():
                if f_line.strip().startswith("-"):
                    owner = f_line.replace("- ", "@").strip()
                    owners.append(owner)
            sigs[sig] = " ".join(owners)
    return sigs


def basic_review(cklist):
    """
    basic review body
    """
    review_body = ""
    for key1, value1 in cklist['basic'].items():
        for value2 in value1:
            if value2["condition"] == "code-modified":
                if value2["name"] == "static-check":
                    langs, checkers = check_code_lang()
                    if not langs:
                        continue
                    item = join_check_item(categorizer[key1],
                            value2['claim'], value2['explain'])
                    item = item.format(lang="/".join(langs), checker="/".join(checkers))
                    review_body += item
            elif value2["condition"] == "new-file-add":
                if not check_new_code():
                    continue
                item = join_check_item(categorizer[key1],
                            value2['claim'], value2['explain'])
                review_body += item
            else:
                item = join_check_item(categorizer[key1],
                        value2['claim'], value2['explain'])
                review_body += item
    return review_body


def community_maintainer_change_review(cstm_item, sigs):
    """
    maintainer changed review body
    """
    review_body = ""
    if cstm_item['name'] == "maintainer-add-explain":
        item = join_check_item(categorizer['customization'],
                cstm_item['claim'], cstm_item['explain'])
        review_body += item
    elif cstm_item['name'] == "maintainer-change-lgtm":
        for sig in sigs:
            item = join_check_item(categorizer['customization'],
                    cstm_item['claim'], cstm_item['explain'])
            review_body += item.format(sig=sig, owners=sigs[sig])
    return review_body


def community_review(custom_items):
    """
    generate repository 'community' review body
    """
    review_body = ""
    sigs = check_maintainer_changes()
    info_sigs = check_sig_information_changes()
    repo_change = check_repository_changes()
    for cstm_item in custom_items:
        if cstm_item['condition'] == "maintainer-change":
            if not sigs:
                continue
            review_body += community_maintainer_change_review(cstm_item, sigs)
        elif cstm_item['condition'] == "sig-update":
            if not info_sigs:
                continue
            for sig in info_sigs:
                if sig in sigs:
                    continue
                item = join_check_item(categorizer['customization'],
                        cstm_item['claim'], cstm_item['explain'])
                review_body += item.format(sig=sig, owners=info_sigs[sig])
        elif cstm_item['condition'] == 'repo-introduce':
            if not repo_change:
                continue
            item = join_check_item(categorizer['customization'],
                    cstm_item['claim'], cstm_item['explain'])
            review_body += item
        elif cstm_item['condition'] == 'sanity_check':
            add_review = check_repository_mgmt_changes(info_sigs, cstm_item)
            review_body += add_review
    return review_body


def review(pull_request, repo_name, chklist_path):
    """
    Return check list of this PR
    """

    if not pull_request["mergeable"]:
        return "PR中存在冲突，无法自动合并。需要先解决冲突，才可以开展评审。"

    review_body = CHK_TABLE_HEADER
    cklist = load_checklist(chklist_path)
    review_body += basic_review(cklist)
    custom_items = cklist['customization'].get(repo_name, None)
    if custom_items:
        if repo_name == "community":
            review_body += community_review(custom_items)
        else:
            for cstm_item in custom_items:
                item = join_check_item(categorizer['customization'],
                                cstm_item['claim'], cstm_item['explain'])
                review_body += item
    return review_body


def main():
    """
    Main entrance of the functionality
    """
    cur_path = os.path.dirname(os.path.abspath(sys.argv[0]))

    pars = argparse.ArgumentParser()
    pars.add_argument("-n", "--repo", type=str, help="Repository name that include group",
                    required=True, default=False)
    pars.add_argument("-p", "--pull", type=str, help="Number ID of Pull Request", required=True)
    pars.add_argument("-r", "--reuse", help="Reuse current local git dirctory", action="store_true")
    pars.add_argument("-w", "--workdir", type=str, help="Work directory", default=cur_path)

    args = pars.parse_args()

    user_gitee = gitee.Gitee()
    chklist_path = os.path.join(cur_path, CHECKLIST)
    work_dir = os.path.realpath(args.workdir)
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    gitee_url = "git@gitee.com:{repo}".format(repo=args.repo)
    group = args.repo.split('/')[0]
    repo_name = args.repo.split('/')[1]
    local_path = os.path.join(work_dir, repo_name)
    if not args.reuse:
        if os.path.exists(local_path):
            shutil.rmtree(local_path)
        subprocess.call(["git", "clone", gitee_url, local_path])
    if not os.path.exists(local_path):
        print("%s not exist, can not use option -r" % local_path)
        sys.exit(1)
    os.chdir(local_path)

    ret_code = subprocess.call(["git", "checkout", "master"])
    if ret_code != 0:
        print("Failed to checkout master branch")
        sys.exit(1)

    subprocess.call(["git", "branch", "-D", "pr_{n}".format(n=args.pull)])
    # It's OK to ignore the result

    ret_code = subprocess.call(["git", "pull"])
    if ret_code != 0:
        print("Failed to update to latest commit in master branch")
        sys.exit(1)

    ret_code = subprocess.call(["git", "fetch", gitee_url,
                                "pull/{n}/head:pr_{n}".format(n=args.pull)])
    if ret_code != 0:
        print("Failed to fetch PR")
        sys.exit(1)

    print("You are reviewing pull {n}".format(n=args.pull))

    subprocess.call(["git", "checkout", "pr_{n}".format(n=args.pull)])

    subprocess.call(["git", "merge", "--no-edit", "remotes/origin/master"])

    pull_request = user_gitee.get_pr(repo_name, args.pull, group)
    review_comment = review(pull_request, repo_name, chklist_path)

    user_gitee.create_pr_comment(repo_name, args.pull, review_comment, group)

if __name__ == "__main__":
    main()
