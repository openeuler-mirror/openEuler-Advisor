#!/usr/bin/python3
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

from advisors import gitee

CHK_TABLE_HEADER = """
**以下为 openEuler-Advisor 的 review_tool 生成审视要求清单**
如果您是第一次给 openEuler 提交 PR，建议您花一点时间阅读 [Gitee工作流说明](https://gitee.com/openeuler/community/blob/master/zh/contributors/Gitee-workflow.md)

**{go}** 审视者确认符合要求 | **{nogo}** 审视者认为不符合要求 | **{na}** 审视者认为与本PR无关 | **{question}** 审视者无法确认是否符合要求 | **{ongoing}** 审视过程中
**NOTE:** Comment "/review status[go/nogo/na/question/ongoing]:number_list[0,1,2 ...] ..." to update the status.
Example: "/review go:0,1,2 nogo:3,4,5" or "/review go:0-2 nogo:3-5".
Comment "/review status[go/nogo/na/question/ongoing]:999" if you want to update the status of all items at a time.
|审视项编号|审视类别|审视要求|审视要求说明|审视结果|
|:--:|:--:|:--|:--|:--:|
"""

CHECKLIST = "helper/reviewer_checklist.yaml"

categorizer = {'PRSubmissionSPEC': 'PR提交规范',
               'CleanCode': 'Clean Code',
               'OpenSourceCompliance': '开源合规性',
               'SecurityPrivacy': '安全及隐私',
               'Compatibility': '兼容性',
               'PackageSubmission': '制品仓要求',
               'customization': '定制项'}
SIGS_URL = "https://gitee.com/openeuler/community/raw/master/sig/sigs.yaml"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW 64; rv:23.0) Gecko/20100101 Firefox/23.0'}
__NUMBER = 0

RRVIEW_STATUS = {
    'go': '[&#x1F7E2;]',
    'nogo': '[&#x1F534;]',
    'na': '[&#x25EF;]',
    'question': '[&#x1F7E1;]',
    'ongoing': '[&#x1F535;]'
}

FLAG_EDIT_ALL = 999

PR_CONFLICT_COMMENT = "Conflict exists in PR.Please resolve conflict before review.@{owner}"
FAILURE_COMMENT = """
Failed to create review list.You can try to rebuild using "/review retrigger".:confused:"""


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


def check_spec_change(branch, keyword):
    """
    check if value of keyword changed in spec
    """
    modify_files = subprocess.getoutput(
        "git diff --name-only --diff-filter=M remotes/origin/{}..".format(branch))
    for item in modify_files.splitlines():
        if item.endswith(".spec"):
            lines = subprocess.getoutput(
                "git diff remotes/origin/{0}.. {1} \
                | grep '^[+-]{2}:'".format(branch, item, keyword))
            lines_list = lines.splitlines()
            if len(lines_list) != 2:
                break
            cur_value = ""
            new_value = ""
            for line in lines_list:
                if line.startswith("+{}:".format(keyword)):
                    cur_value = line.split(":")[1].strip()
                elif line.startswith("-{}:".format(keyword)):
                    new_value = line.split(":")[1].strip()
            if cur_value != new_value:
                return True
    return False


def load_checklist(local, user_gitee):
    """
    @Desc: load checklist
    @Notice: this function must be called before prepare_env(),
    because prepare_env() changed work directory.
    """
    if not local:
        return user_gitee.get_reviewer_checklist()
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    chklist_path = os.path.join(cur_dir, CHECKLIST)
    try:
        with open(chklist_path, 'r', encoding='utf-8') as file_descriptor:
            return yaml.load(file_descriptor.read(), Loader=yaml.Loader)
    except OSError as reason:
        print("Load yaml failed!" + str(reason))
        return None


def join_check_item(category, claim, explain):
    """
    join check item as a table row
    """
    global __NUMBER
    item_template = "|{}|{}|{}|{}|{}|\n"
    res = item_template.format(__NUMBER, category, claim, explain, RRVIEW_STATUS['ongoing'])
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
        try:
            file_descriptor = open(sigs_file, 'r', encoding='utf-8')
        except IOError as error:
            print("Error: open file {} failed", sigs_file, error)
            return None
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
        try:
            file_descriptor = open(repos_file, 'r', encoding='utf-8')
        except IOError as error:
            print("Error: open file {} failed", repos_file, error)
            return None
        repos = yaml.load(file_descriptor.read(), Loader=yaml.Loader)
        return repos['repositories']
    return None


def is_exist_protected_branch_exclude_master(repo_name, repos):
    """
    check there exist other protected branches exclude master
    """
    for repo in repos:
        if repo_name == repo['name']:
            if len(repo['branches']) == 1:
                return False
            return True
    return False


def load_sig_owners(sig_name):
    """
    Load owners specified sig
    """
    owners = []
    owners_file = "sig/{}/OWNERS".format(sig_name)
    try:
        with open(owners_file, 'r') as file_descriptor:
            lines = file_descriptor.readlines()
            for line in lines:
                if line.strip().startswith('-'):
                    owner = line.replace('- ', '@').strip()
                    owners.append(owner)
    except IOError as error:
        print("Error: 没有找到文件或读取文件失败 {}.", owners_file, error)
        return None
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
        repos_need_lgtm = []
        if sig_changes[1] == 'sig-recycle':
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
        status, item = line.split(maxsplit=1)
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
        status, item = line.split(maxsplit=1)
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
                if not check_spec_change(branch, "License"):
                    continue
            elif value2['condition'] == 'version-change':
                if branch == "master" or not check_spec_change(branch, "Version"):
                    continue
            item = join_check_item(categorizer[key1],
                                   value2['claim'], value2['explain'])
            review_body += item
    return review_body

def src_openeuler_review(cklist, branch):
    """
    Review items for src-openeuler repos
    """
    review_body = ""
    for key1, value1 in cklist['src-openeuler'].items():
        for value2 in value1:
            if value2['name'] == 'PR-latest-version' and branch == 'master':
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


def review(checklist, pull_request, repo_name, branch, group):
    """
    Return check list of this PR
    """
    if not pull_request["mergeable"]:
        return PR_CONFLICT_COMMENT.format(owner=pull_request['user']['login'])

    review_body = CHK_TABLE_HEADER.format(go=RRVIEW_STATUS['go'],
                                          nogo=RRVIEW_STATUS['nogo'],
                                          na=RRVIEW_STATUS['na'],
                                          question=RRVIEW_STATUS['question'],
                                          ongoing=RRVIEW_STATUS['ongoing'])
    review_body += basic_review(checklist, branch)

    if group == "src-openeuler":
        review_body += src_openeuler_review(checklist, branch)

    custom_items = checklist['customization'].get(repo_name, None)
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


def args_parser():
    """
    arguments parser
    """
    pars = argparse.ArgumentParser()
    pars.add_argument("-q", "--quiet", action='store_true', default=False, \
                      help="No log print")
    pars.add_argument("-n", "--repo", type=str, help="Repository name that include group")
    pars.add_argument("-p", "--pull", type=str, help="Number ID of Pull Request")
    pars.add_argument("-u", "--url", type=str, help="URL of Pull Request")
    pars.add_argument("-r", "--reuse", help="Reuse current local git dirctory", action="store_true")
    pars.add_argument("-w", "--workdir", type=str, default=os.getcwd(),
                      help="Work directory.Default is current directory.")
    pars.add_argument("-e", "--edit", type=str,
                      help="Edit items format.Format: status1:number_list1 status2:number_list2 ...")
    pars.add_argument("-c", "--clean", help="Clean environment", action="store_true")
    pars.add_argument("-l", "--local", help="Using local checklist", action="store_true")

    return pars.parse_args()


def local_repo_name(group, repo_name, pull_id):
    """
    combine name to avoid name conflit
    """
    return "{}_{}_{}".format(group, repo_name, pull_id)


def exec_cmd(cmd, retry_times=0):
    """
    wrapper for Popen
    @cmd: argument list of command
    @retry_times: retry times if cmd execute failed
    """
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


def prepare_env(work_dir, reuse, pr_tuple, branch):
    """
    prepare local reposity base and PR branch
    Notice: this will change work directory,
    action related to obtain path need do before this.
    """
    group = pr_tuple[0]
    repo_name = pr_tuple[1]
    pull_id = pr_tuple[2]
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    repo = group + "/" + repo_name
    gitee_url = "https://gitee.com/{repo}.git".format(repo=repo)
    local_path = os.path.join(work_dir, local_repo_name(group, repo_name, pull_id))
    if os.path.exists(local_path) and not reuse:
        print("WARNING: %s already exist, delete it." % local_path)
        shutil.rmtree(local_path)
    if not os.path.exists(local_path):
        if exec_cmd(["git", "clone", gitee_url, local_path]) != 0:
            print("Failed to git clone {}".format(gitee_url))
            return 1
    os.chdir(local_path)
    if exec_cmd(["git", "checkout", branch]) != 0:
        print("Failed to checkout %s branch" % branch)
        return 1
    if exec_cmd(["git", "pull"]) != 0:
        print("Failed to update to latest commit in %s branch" % branch)
        return 1
    lines = subprocess.getoutput("git branch | grep pr_{n}".format(n=pull_id))
    for br_name in lines.splitlines():
        exec_cmd(["git", "branch", "-D", br_name.strip()])
    if exec_cmd(["git", "fetch", gitee_url, "pull/{n}/head:pr_{n}".format(n=pull_id)]) != 0:
        print("Failed to fetch PR:{n}".format(n=pull_id))
        return 1
    if exec_cmd(["git", "checkout", "-b", "working_pr_{n}".format(n=pull_id)]) != 0:
        print("Failed to create working branch working_pr_{n}".format(n=pull_id))
        return 1
    if exec_cmd(["git", "merge", "--no-edit", "pr_{n}".format(n=pull_id)], 3) != 0:
        print("Failed to merge PR:{n} to branch:{base}".format(n=pull_id, base=branch))
        return 1
    return 0


def cleanup_env(work_dir, group, repo_name, pull_id):
    """
    Clean up environment, e.g. temporary directory
    """
    shutil.rmtree(os.path.join(work_dir, local_repo_name(group, repo_name, pull_id)))


def find_review_comment(user_gitee, group, repo_name, pull_id):
    """
    Find the review comment for PR
    """
    review_key = "以下为 openEuler-Advisor 的 review_tool 生成审视要求清单"
    data = user_gitee.get_pr_comments_all(group, repo_name, pull_id)
    for comment in data[::-1]:
        if review_key in comment['body']:
            return comment
    return None


def edit_review_status(edit, user_gitee, group, repo_name, pull_id):
    """
    Edit review status
    """
    status_num_dicts = decode_edit_content(edit)
    if not status_num_dicts:
        return 1
    comment = find_review_comment(user_gitee, group, repo_name, pull_id)
    if not comment:
        print("ERROR: can not find review list")
        return 1
    items = comment['body'].splitlines(True)
    need_edit = False
    head_len = len(CHK_TABLE_HEADER.splitlines())
    match_str = r"\[&#x[0-9A-F]+;\]"
    if len(status_num_dicts) == 1 and FLAG_EDIT_ALL in status_num_dicts.keys():
        need_edit = True
        for num in range(len(items[head_len:])):
            items[head_len + num] = re.sub(match_str,
                                           RRVIEW_STATUS[status_num_dicts[FLAG_EDIT_ALL]],
                                           items[head_len + num])
    else:
        for num, status in status_num_dicts.items():
            if int(num) >= 0 and int(num) < len(items[head_len:]):
                items[head_len + num] = re.sub(match_str,
                                               RRVIEW_STATUS[status],
                                               items[head_len + num])
                need_edit = True
    if need_edit:
        new_body = "".join(items)
        user_gitee.edit_pr_comment(group, repo_name, comment['id'], new_body)
    return 0


def decode_edit_content(edit):
    """
    @desc: decode input string
    @edit: input string
    @dicts: dict {num: status}
    """
    dicts = {}
    for sect in edit.split():
        status = sect.split(":")[0]
        if status not in RRVIEW_STATUS.keys():
            print("ERROR: review item status \'%s\' undefined." % status)
            return {}
        nums = sect.split(":")[1]
        for num in nums.split(","):
            if not num.isdigit():
                res = re.match("^([0-9]{1,3})-([0-9]{0,3})$", num)
                if res:
                    start = int(res.group(1))
                    end = FLAG_EDIT_ALL
                    if res.group(2):
                        end = int(res.group(2))
                    if start >= end:
                        print("ERROR: input format error,start number must greater than end.")
                        return {}
                    for i in range(start, end + 1):
                        dicts[i] = status
                else:
                    print("ERROR: input format error or contain invalid character.")
                    return {}
            else:
                dicts[int(num)] = status
    return dicts


def main():
    """
    Main entrance of the functionality
    """
    args = args_parser()
    if args.quiet:
        sys.stdout = open('/dev/null', 'w')
        sys.stderr = sys.stdout
    work_dir = os.path.realpath(args.workdir)
    params = extract_params(args)
    if not params:
        return 1
    group = params[0]
    repo_name = params[1]
    pull_id = params[2]
    try:
        user_gitee = gitee.Gitee()
    except NameError:
        sys.exit(1)
    pull_request = user_gitee.get_pr(repo_name, pull_id, group)
    if not pull_request:
        print("Failed to get PR:%s of repository:%s/%s, make sure the PR is exist." \
              % (pull_id, group, repo_name))
        return 1
    if args.edit:
        if edit_review_status(args.edit, user_gitee, group, repo_name, pull_id) != 0:
            return 1
    else:
        checklist = load_checklist(args.local, user_gitee)
        if not checklist:
            return 1
        branch = pull_request['base']['label']
        ret = prepare_env(work_dir, args.reuse, params, branch)
        if ret != 0:
            user_gitee.create_pr_comment(repo_name, pull_id, FAILURE_COMMENT, group)
            return 1
        review_comment = review(checklist, pull_request, repo_name, branch, group)
        user_gitee.create_pr_comment(repo_name, pull_id, review_comment, group)
        if args.clean:
            cleanup_env(work_dir, group, repo_name, pull_id)
        print("push review list finish.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
