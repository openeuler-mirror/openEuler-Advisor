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
import urllib
import yaml
import gitee

CHK_TABLE_HEADER = """
**以下为 openEuler-Advisor 的 review_tool 生成审视要求清单**
如果您是第一次给 openEuler 提交 PR，建议您花一点时间阅读 [Gitee工作流说明](https://gitee.com/openeuler/community/blob/master/zh/contributors/Gitee-workflow.md)

**[Y]** 审视者确认符合要求 | **[N]** 审视者认为不符合要求 | **[NA]** 审视者认为与本PR无关 | **[?]** 审视者无法确认是否符合要求 | **[ ]** 审视过程中
|审视项编号|审视类别|审视要求|审视要求说明|审视结果|
|:--:|:--:|:--|:--|:--:|
"""

SANITY_CHK_CMD = "python3 zh/technical-committee/governance/sanity_check.py ."

CHECKLIST = "helper/reviewer_checklist.yaml"

categorizer = {'PRSubmissionSPEC':'PR提交规范',
            'CleanCode':'Clean Code',
            'OpenSourceCompliance':'开源合规性',
            'SecurityPrivacy':'安全及隐私',
            'customization':'定制项'}
SIGS_URL = "https://gitee.com/openeuler/community/raw/master/sig/sigs.yaml"
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW 64; rv:23.0) Gecko/20100101 Firefox/23.0'}
__NUMBER = 0


def check_new_code(branch):
    """
    Check if new code file has been introduced
    """
    lst_files = subprocess.getoutput(
            "git diff --name-only --diff-filter=A remotes/origin/{}..".format(branch))
    return bool(lst_files.splitlines())


def check_code_lang(branch):
    """
    Check this PR code programming language
    """
    langs = []
    checkers = []
    lst_files = subprocess.getoutput("git diff --name-only remotes/origin/{}..".format(branch))
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


def check_license_change(branch):
    """
    check if spec be modified
    """
    lst_files = subprocess.getoutput(
            "git diff --name-only --diff-filter=M remotes/origin/{}..".format(branch))
    for item in lst_files.splitlines():
        if item.endswith(".spec"):
            lst_lines = subprocess.getoutput(
                    "git diff remotes/origin/{}.. ".format(branch) + item + " | grep '^+License'")
            return bool(lst_lines.splitlines())
    return False


def load_checklist(chklist_path):
    """
    load configuration
    """
    try:
        with open(chklist_path, 'r', encoding = 'utf-8') as file_descriptor:
            return yaml.load(file_descriptor.read(), Loader = yaml.Loader)
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
    lst_files = subprocess.getoutput("git diff remotes/origin/master.. \
            repository/src-openeuler.yaml | grep '^+- name' | awk '{print $NF}'")
    return bool(lst_files.splitlines())


def load_sigs(sigs_file=""):
    """
    Load sigs yaml
    """
    if sigs_file:
        file_descriptor = open(sigs_file, 'r', encoding = 'utf-8')
        sigs = yaml.load(file_descriptor.read(), Loader=yaml.Loader)
    else:
        req = urllib.request.Request(url=SIGS_URL, headers=headers)
        res = urllib.request.urlopen(req)
        sigs = yaml.load(res.read().decode("utf-8"), Loader=yaml.Loader)
    return sigs['sigs']


def get_repo_sig_ownership(repo, sigs):
    """
    Get repository ownership
    """
    for sig in sigs:
        if repo in sig['repositories']:
            return sig['name']
    return ""


def load_repositories(repos_file):
    """
    Load repository yaml
    """
    if repos_file:
        file_descriptor = open(repos_file, 'r', encoding = 'utf-8')
        repos = yaml.load(file_descriptor.read(), Loader=yaml.Loader)
        return repos['repositories']
    return None


def is_exist_protected_branch_exclude_master(repo_name, repos):
    """
    check there exist other protected branches exclude master
    """
    for repo in repos:
        if repo_name == repo['name']:
            if len(repo['protected_branches']) == 1:
                return False
            return True
    return False


def load_sig_owners(sig_name):
    """
    Load owners specified sig
    """
    owners = []
    owners_file = "sig/{}/OWNERS".format(sig_name)
    with open(owners_file, 'r') as file_descriptor:
        lines = file_descriptor.readlines()
        for line in lines:
            if line.strip().startswith('-'):
                owner = line.replace('- ', '@').strip()
                owners.append(owner)
    return owners


def get_repo_changes():
    """
    find repositories that ownership changes
    """
    dlt_repos = []
    add_repos = []

    dlt_lines = subprocess.getoutput(
            "git diff remotes/origin/master.. sig/sigs.yaml | grep '^-[ ][ ]-' | awk '{print $NF}'")
    for dlt_line in dlt_lines.splitlines():
        if dlt_line.startswith("openeuler") or dlt_line.startswith("src-openeuler"):
            dlt_repos.append(dlt_line.strip())

    add_lines = subprocess.getoutput(
            "git diff remotes/origin/master.. sig/sigs.yaml | grep '^+[ ][ ]-' | awk '{print $NF}'")
    for add_line in add_lines.splitlines():
        if add_line.startswith("openeuler") or add_line.startswith("src-openeuler"):
            add_repos.append(add_line.strip())

    repo_changes = {}
    cur_sigs = load_sigs()
    tobe_sigs = load_sigs("sig/sigs.yaml")
    for dlt_repo in dlt_repos:
        if dlt_repo in add_repos:
            cur_sig = get_repo_sig_ownership(dlt_repo, cur_sigs)
            tobe_sig = get_repo_sig_ownership(dlt_repo, tobe_sigs)
            if cur_sig != tobe_sig:
                repo = dlt_repo
                chg_tuple = (cur_sig, tobe_sig)
                res = repo_changes.get(chg_tuple, None)
                if res:
                    repo_changes[chg_tuple].append(repo)
                else:
                    repo_changes[chg_tuple] = [repo]
    return repo_changes


def check_repository_ownership_changes(info):
    """
    Check if repository ownership changes.Example, from sigA to sigB
    """
    review_body = ""

    rls_mgmt_owners = load_sig_owners("sig-release-management")
    oe_mgmt_repos = load_repositories("repository/openeuler.yaml")
    src_oe_mgmt_repos = load_repositories("repository/src-openeuler.yaml")
    repo_changes = get_repo_changes()
    for sig_changes, repos in repo_changes.items():
        sig1_owners = load_sig_owners(sig_changes[0])
        sig2_owners = load_sig_owners(sig_changes[1])
        if sig_changes[1] == 'sig-recycle':
            repos_need_lgtm = []
            for repo in repos:
                if repo.startswith('openeuler/'):
                    mgmt_repos = oe_mgmt_repos
                elif repo.startswith('src-openeuler/'):
                    mgmt_repos = src_oe_mgmt_repos
                else:
                    print("ERROR: repo:%s error" % repo)
                    mgmt_repos = None
                repo_name = repo.split('/')[1]
                if is_exist_protected_branch_exclude_master(repo_name, mgmt_repos):
                    repos_need_lgtm.append(repo)

        item = join_check_item(categorizer['customization'],
                info['claim'], info['explain'])
        review_body += item.format(repos=" ".join(repos), sig1=sig_changes[0], sig2=sig_changes[1],
                                owners1=" ".join(sig1_owners), owners2=" ".join(sig2_owners))
        if repos_need_lgtm:
            item = join_check_item(categorizer['customization'],
                    info['to_recycle']['claim'], info['to_recycle']['explain'])
            review_body += item.format(repos=" ".join(repos_need_lgtm), sig1=sig_changes[0],
                                    sig2=sig_changes[1], owners=" ".join(rls_mgmt_owners))
            repos_need_lgtm.clear()
    return review_body


def check_branch_add(info):
    """
    check if new branch add in repo
    """
    review_body = ""
    need_mgmt_lgtm = False

    add_lines = subprocess.getoutput(
            "git diff remotes/origin/master.. \
            repository/src-openeuler.yaml | grep '^+[ ][ ]-' | awk '{print $NF}'")
    for add_line in add_lines.splitlines():
        if add_line.strip() != "master":
            need_mgmt_lgtm = True
            break
    if need_mgmt_lgtm:
        owners = load_sig_owners("sig-release-management")
        item = join_check_item(categorizer['customization'], info['claim'], info['explain'])
        review_body += item.format(owners=" ".join(owners))
    return review_body


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


def basic_review(cklist, branch):
    """
    basic review body
    """
    review_body = ""
    for key1, value1 in cklist['basic'].items():
        for value2 in value1:
            if value2["condition"] == "code-modified":
                if value2["name"] == "static-check":
                    langs, checkers = check_code_lang(branch)
                    if not langs:
                        continue
                    item = join_check_item(categorizer[key1],
                            value2['claim'], value2['explain'])
                    item = item.format(lang="/".join(langs), checker="/".join(checkers))
                    review_body += item
                    continue
            elif value2["condition"] == "new-file-add":
                if not check_new_code(branch):
                    continue
            elif value2['condition'] == 'license-change':
                if not check_license_change(branch):
                    continue
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
        elif cstm_item['condition'] == 'repo-ownership-change':
            review_body += check_repository_ownership_changes(cstm_item)
        elif cstm_item['condition'] == 'new-branch-add':
            review_body += check_branch_add(cstm_item)

    return review_body


def review(pull_request, repo_name, chklist_path, branch):
    """
    Return check list of this PR
    """

    if not pull_request["mergeable"]:
        return "PR中存在冲突，无法自动合并。需要先解决冲突，才可以开展评审。"

    review_body = CHK_TABLE_HEADER
    cklist = load_checklist(chklist_path)
    review_body += basic_review(cklist, branch)
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


def check_pr_url(url):
    """
    check whether the URL of Pull Request is valid
    """
    if url:
        pattern = re.compile(r'https://gitee.com/(open_euler/dashboard/projects/)?'
                + r'(openeuler|src-openeuler)/([A-Za-z0-9-_]*)/pulls/(\d+$)')
        return pattern.match(url)
    return None


def extract_params(args):
    """
    check and extract parameters we need
    """
    if args.url and len(args.url) > 0:
        res = check_pr_url(args.url)
        if res:
            group = res.group(2)
            repo_name = res.group(3)
            pull_id = res.group(4)
            return (group, repo_name, pull_id)
        print("ERROR: URL is wrong, please check!")
        return ()
    if args.repo and args.pull and len(args.repo) > 0 and len(args.pull) > 0:
        group = args.repo.split('/')[0]
        repo_name = args.repo.split('/')[1]
        pull_id = args.pull
        return (group, repo_name, pull_id)
    print("WARNING: please specify the URL of PR or repository name and  PR's ID.\
            \nDetails use -h/--help option.")
    return ()


def args_parser(cur_path):
    """
    arguments parser
    """
    pars = argparse.ArgumentParser()
    pars.add_argument("-n", "--repo", type=str, help="Repository name that include group")
    pars.add_argument("-p", "--pull", type=str, help="Number ID of Pull Request")
    pars.add_argument("-u", "--url", type=str, help="URL of Pull Request")
    pars.add_argument("-r", "--reuse", help="Reuse current local git dirctory", action="store_true")
    pars.add_argument("-w", "--workdir", type=str,
            help="Work directory.Default is current directory.", default=cur_path)

    return pars.parse_args()


def prepare(args, group, repo_name, pull_id, branch):
    """
    prepare local reposity base and PR branch
    """
    work_dir = os.path.realpath(args.workdir)
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    repo = group + "/" + repo_name
    gitee_url = "git@gitee.com:{repo}".format(repo=repo)
    local_path = os.path.join(work_dir, repo_name)
    if not args.reuse:
        if os.path.exists(local_path):
            shutil.rmtree(local_path)
        ret_code = subprocess.call(["git", "clone", gitee_url, local_path])
        if ret_code != 0:
            sys.exit(1)
    if not os.path.exists(local_path):
        print("%s not exist, can not use option -r" % local_path)
        sys.exit(1)
    os.chdir(local_path)

    ret_code = subprocess.call(["git", "checkout", branch])
    if ret_code != 0:
        print("Failed to checkout %s branch" % branch)
        sys.exit(1)

    subprocess.call(["git", "branch", "-D", "pr_{n}".format(n=pull_id)])
    # It's OK to ignore the result

    ret_code = subprocess.call(["git", "pull"])
    if ret_code != 0:
        print("Failed to update to latest commit in %s branch" % branch)
        sys.exit(1)

    ret_code = subprocess.call(["git", "fetch", gitee_url,
                                "pull/{n}/head:pr_{n}".format(n=pull_id)])
    if ret_code != 0:
        print("Failed to fetch PR")
        sys.exit(1)

    print("You are reviewing PR:{n}".format(n=pull_id))

    subprocess.call(["git", "checkout", "pr_{n}".format(n=pull_id)])

    subprocess.call(["git", "merge", "--no-edit", "remotes/origin/" + branch])


def main():
    """
    Main entrance of the functionality
    """
    cur_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    args = args_parser(cur_path)
    params = extract_params(args)
    if not params:
        sys.exit(1)
    group = params[0]
    repo_name = params[1]
    pull_id = params[2]

    user_gitee = gitee.Gitee()
    pull_request = user_gitee.get_pr(repo_name, pull_id, group)
    if not pull_request:
        print("Failed to get PR:%s of repository:%s, make sure the PR is exist."\
                % (pull_id, repo_name))
        sys.exit(1)
    branch = pull_request['base']['label']

    prepare(args, group, repo_name, pull_id, branch)

    chklist_path = os.path.join(cur_path, CHECKLIST)
    review_comment = review(pull_request, repo_name, chklist_path, branch)

    user_gitee.create_pr_comment(repo_name, pull_id, review_comment, group)

if __name__ == "__main__":
    main()
