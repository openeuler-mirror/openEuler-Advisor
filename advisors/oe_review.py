#!/usr/bin/python3
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2024. All rights reserved.
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
import tempfile
import urllib
import urllib.request
import urllib.parse
import yaml
import json
import requests

from openai import OpenAI
from advisors import gitee

OE_REVIEW_PR_PROMPT="""
You are a code reviewer of a openEuler Pull Request, providing feedback on the code changes below.
      As a code reviewer, your task is:
      - Review the code changes (diffs) in the patch and provide feedback.
      - If there are any bugs, highlight them.
      - Does the code do what it says in the commit messages?
      - Do not highlight minor issues and nitpicks.
      - Use bullet points if you have multiple comments.
      - If no suggestions are provided, please give good feedback.
      - please use chinese to give feedback.

      You are provided with the merge request changes in a diff format.
      The diff to be reviewed, which is get from the Gitee source code repo, as following:
"""

OE_REVIEW_RATING_PROMPT="""
Assume you are managing a software project and need sort out important patches from careless ones,
quality patches from careless patches, relevant/impactful patches from trivial patches, difficult
patches from easy patches, core changes from leaf changes. Please evaluate the below patch and give
a rating number in range 1-100.
"""

# define data structure that contains queue and mutex lock for thread sharing
import threading
import time

class ThreadSafeQueue:
    def __init__(self):
        self.queue = []  # Your data structure (list) can be replaced with any other like deque from collections
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

    def put(self, item):
        with self.lock:
            self.queue.append(item)
            self.condition.notify_all()  # Notify all waiting threads that new item is added

    def get(self):
        with self.lock:
            while len(self.queue) == 0:
                self.condition.wait()  # Wait until there are items in the queue
            item = self.queue.pop(0)
            return item

    def qsize(self):
        with self.lock:
            return len(self.queue)


# 建三个队列，一个是待处理PR列表，一个是经过预处理的PR列表，一个是待提交PR列表
# 批处理，首先关闭所有可以关闭的PR，直接合并sync且没有ci_failed的PR
# 然后对所有其他的PR再进行review
# define 3 queues to be shared across threads
# List of PRs to be reviewed, by review_repos()
PENDING_PRS = ThreadSafeQueue()
# review_pr() get pr from PENDING_PRS, if can be obviously handled, put comment into submitting_prs, otherwise, move to NEED_REVIEW_PRS
# that are being preprocessed for review
NEED_REVIEW_PRS = ThreadSafeQueue()
MANUAL_REVIEW_PRS = ThreadSafeQueue()
# PRs that are being submitted 
SUBMITTING_PRS = ThreadSafeQueue()

def generate_review_from_ollama(pr_content, prompt, model="llama3.1:8b"):
    base_url = "http://localhost:11434/api"
    json_resp = []
    resp = None
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW 64; rv:50.0) '\
                        'Gecko/20100101 Firefox/50.0'}
    headers["Content-Type"] = "application/json;charset=UTF-8"
    
    url = f"{base_url}/generate"

    values = {}
    values["model"] = model
    values['prompt'] = pr_content
    values['system'] = prompt
    values['stream'] = False
    response = requests.post(url, headers=headers, json=values)
    return response.json().get('response', '')

def check_pr_url(url):
    """
    check whether the URL of Pull Request is valid
    """
    if url:
        pattern = re.compile(r'https://(e.)?gitee.com/(open_euler/repos/)?'
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
            group = res.group(3)
            repo_name = res.group(4)
            pull_id = res.group(5)
            return (group, repo_name, pull_id)
        print("ERROR: URL is wrong, please check!")
        return ()
    if args.repo and args.pull and len(args.repo) > 0 and len(args.pull) > 0:
        group = args.repo.split('/')[0]
        repo_name = args.repo.split('/')[1]
        pull_id = args.pull
        return group, repo_name, pull_id
    print("WARNING: please specify the URL of PR or repository name and  PR's ID.\
            \nDetails use -h/--help option.")
    return ()

def args_parser():
    """
    arguments parser
    """
    pars = argparse.ArgumentParser()
    pars.add_argument("-q", "--quiet", action='store_true', default=False, help="No log print")
    pars.add_argument("-a", "--active_user", action='store_true', default=False, help="Review all PRs in repositories as maintainer or committer")
    pars.add_argument("-n", "--repo", type=str, help="Repository name that include group")
    pars.add_argument("-p", "--pull", type=str, help="Number ID of Pull Request")
    pars.add_argument("-u", "--url", type=str, help="URL of Pull Request")
    pars.add_argument("-s", "--sig", type=str, default="TC", help="When active_user is set, review all PRs in specified SIG")
    pars.add_argument("-m", "--model", type=str, help="Model of selection to generate review")
    pars.add_argument("-e", "--editor", type=str, default="nvim",
                      help="Editor of choice to edit content, default to nvim")

    return pars.parse_args()
    
def edit_content(text, editor):
    fd, path = tempfile.mkstemp(suffix=".tmp", prefix="oe_review")
    with os.fdopen(fd, 'w') as tmp:
        tmp.write(text)
        tmp.flush()
        subprocess.call([editor, path])
        text_new = open(path).read()
        return text_new

def easy_classify(pull_request):
    suggest_action = ""
    suggest_reason = ""
    sync_pr = False
    
    if not pull_request["mergeable"]:
        suggest_action = "/close"
        suggest_reason = "存在冲突"

    if pull_request["title"].startswith("[sync] PR-") and pull_request["user"]["login"]=="openeuler-sync-bot":
        sync_pr = True

    for label in pull_request["labels"]:
        if label['name'] == "ci_failed":
            suggest_action = "/close"
            suggest_reason = "CI 失败"
        elif label['name'] == 'openeuler-cla/no':
            suggest_action = "/check-cla"
            suggest_reason = "CLA 未签署"
        elif label['name'] == 'ci_processing':
            suggest_action = "暂不处理"
            suggest_reason = "等待 CI 处理结果"
        elif label['name'] == 'kind/wait_for_update':
            suggest_action = "暂不处理"
            suggest_reason = "等待提交人更新"
        elif label['name'] == 'wait_confirm':
            suggest_action = "暂不处理"
            suggest_reason = "等待相关开发者确认"
        elif label['name'] == 'ci_successful':
            if sync_pr == True:
                suggest_action = "/lgtm\n/approve"
                suggest_reason = "分支同步 PR，构建成功，默认合入。"
        else:
            pass
    return suggest_action, suggest_reason

def sort_pr(user_gitee):
    while True:
        item = PENDING_PRS.get()
        if not item:
            break
        print(f"Got {item} from queue")

        pull_request = user_gitee.get_pr(item["repo"], item["number"], item["owner"])

        suggest_action, suggest_reason = easy_classify(pull_request)

        if suggest_action == "":
            need_review_pr = {}
            need_review_pr['pull_request'] = pull_request
            need_review_pr['pr_info'] = item
            NEED_REVIEW_PRS.put(need_review_pr)
        else:
            review_comment_raw = suggest_action + "\n" + suggest_reason
            submitting_pr = {}
            submitting_pr['review_comment'] = review_comment_raw
            submitting_pr['pr_info'] = item
            submitting_pr['suggest_action'] = suggest_action
            submitting_pr['suggest_reason'] = suggest_reason
            SUBMITTING_PRS.put(submitting_pr)

    NEED_REVIEW_PRS.put(None)

def ai_review(user_gitee):
    while True:
        item = NEED_REVIEW_PRS.get()
        if not item:
            break
        pr_info = item["pr_info"]
        pr_diff = user_gitee.get_diff(pr_info['repo'], pr_info['number'], pr_info['owner'])
        if not pr_diff:
            print("Failed to get PR:%s of repository:%s/%s, make sure the PR is exist." % (pr_info['number'], pr_info['owner'], pr_info['repo']))
            continue
        review = generate_review_from_ollama(pr_diff, OE_REVIEW_PR_PROMPT)
        review_rating = generate_review_from_ollama(pr_diff, OE_REVIEW_RATING_PROMPT)
    
        manual_review_pr = {}
        manual_review_pr['pr_info'] = pr_info
        manual_review_pr['pull_request'] = item['pull_request']
        manual_review_pr['pr_diff'] = pr_diff
        manual_review_pr['review'] = review
        manual_review_pr['review_rating'] = review_rating
        MANUAL_REVIEW_PRS.put(manual_review_pr)
    MANUAL_REVIEW_PRS.put(None)

def manually_review(user_gitee, editor):
    while True:
        item  = MANUAL_REVIEW_PRS.get()
        if not item:
            break
        review_content = ""
        pull_request = item['pull_request']
        pr_info = item["pr_info"]
        review = item['review']
        review_rating = item['review_rating']
        pr_diff = item['pr_diff']

        review_content += "!{number}: {title}\n# {body}\n".format(number=pull_request["number"], title=pull_request["title"], body=pull_request["body"])

        review_content += "This PR has following labels:\n"
        for label in pull_request["labels"]:
            review_content += f"{label['name']}  "
            
        review_comment_raw = edit_content(review_content + '\n\n' + review + '\n\n' + review_rating + '\n\n' + pr_diff, editor)

        submitting_pr = {}
        submitting_pr['review_comment'] = review_comment_raw
        submitting_pr['pr_info'] = item['pr_info']
        submitting_pr['pull_request'] = pull_request
        SUBMITTING_PRS.put(submitting_pr)

    SUBMITTING_PRS.put(None)

def submit_review_impl(user_gitee, pr_info, pull_request, review_comment, suggest_action="", suggest_reason=""):
    result = " is handled and review is published."

    user_gitee.create_pr_comment(pr_info['repo'], pr_info['number'], review_comment, pr_info['owner'])

    if suggest_action == "/close":
        result = " is closed due to {reason}.".format(reason=suggest_reason)
    elif suggest_action == "暂不处理":
        result = " is skipped due to {reason}.".format(reason=suggest_reason)
    elif suggest_action == "/lgtm\n/approve":
        result = " is approved due to {reason}.".format(reason=suggest_reason)
    else:
        pass
    print("!{number}: {title}{res}".format(number=pr_info["number"], title=pull_request["title"], res=result))

def submmit_review(user_gitee):
    while True:
        item = SUBMITTING_PRS.get()
        print(item)
        if not item:
            break
        review_comment = item['review_comment']
        pr_info = item['pr_info']
        pull_request = item['pull_request']
        suggest_action = item.get('suggest_action', "")
        suggest_reason = item.get('suggest_reason', "")

        submit_review_impl(user_gitee, pr_info, pull_request, review_comment, suggest_action, suggest_reason)


def review_pr(user_gitee, repo_name, pull_id, group, editor):
    """
     Review Pull Request
     """
    review_content = ""
    pull_request = user_gitee.get_pr(repo_name, pull_id, group)

    suggest_action = ""

    result = ""

    review_content += "!{number}: {title}\n# {body}\n".format(number=pull_request["number"], title=pull_request["title"], body=pull_request["body"])
    if not pull_request["mergeable"]:
        review_content += "This PR is not mergeable!\n"
        suggest_action = "/close"
        suggest_reason = "存在冲突"

    if pull_request["title"].startswith("[sync] PR-") and pull_request["user"]["login"]=="openeuler-sync-bot":
        sync_pr = True

    review_content += "This PR has following labels:\n"
    for label in pull_request["labels"]:
        if label['name'] == "ci_failed":
            suggest_action = "/close"
            suggest_reason = "CI 失败"
        elif label['name'] == 'openeuler-cla/no':
            suggest_action = "/check-cla"
            suggest_reason = "CLA 未签署"
        elif label['name'] == 'ci_processing':
            suggest_action = "暂不处理"
            suggest_reason = "等待 CI 处理结果"
        elif label['name'] == 'kind/wait_for_update':
            suggest_action = "暂不处理"
            suggest_reason = "等待提交人更新"
        elif label['name'] == 'wait_confirm':
            suggest_action = "暂不处理"
            suggest_reason = "等待相关开发者确认"
        elif label['name'] == 'ci_successful':
            if sync_pr == True:
                suggest_action = "/lgtm\n/approve"
                suggest_reason = "分支同步 PR，构建成功，默认合入。"
        else:
            pass
        review_content += f"{label['name']}  "
    review_content += "\n\n"

    pr_diff = user_gitee.get_diff(repo_name, pull_id, group)
    if not pr_diff:
        print("Failed to get PR:%s of repository:%s/%s, make sure the PR is exist." % (pull_id, group, repo_name))
        return 1

    if suggest_action == "/close":
        review = "/close"
        review_comment_raw = review + "\n" + suggest_reason
    elif suggest_action == "/check-cla":
        review = "/check-cla"
        review_comment_raw = review + "\n" + suggest_reason
    elif suggest_action == "暂不处理":
        review = "暂不处理"
        review_comment_raw = review + "\n" + suggest_reason
    elif suggest_action == "/lgtm\n/approve":
        review = "/lgtm\n/approve"
        review_comment_raw = review + "\n" + suggest_reason
    else:
        review = generate_review_from_ollama(pr_diff, OE_REVIEW_PR_PROMPT)
        review_rating = generate_review_from_ollama(pr_diff, OE_REVIEW_RATING_PROMPT)
        review_comment_raw = edit_content(review_content + '\n\n' + review + '\n\n' + review_rating + '\n\n' + pr_diff, editor)

    review_comment = ""
    # remove lines start with hash
    for l in review_comment_raw:
        if l.startswith("#"):
            continue
        else:
            review_comment += l

    user_gitee.create_pr_comment(repo_name, pull_id, review_comment, group)
    if suggest_action == "/close":
        result = " is closed due to {reason}.".format(reason=suggest_reason)
    elif suggest_action == "暂不处理":
        result = " is skipped due to {reason}.".format(reason=suggest_reason)
    elif suggest_action == "/lgtm\n/approve":
        result = " is approved due to {reason}.".format(reason=suggest_reason)
    else:
        result = " is handled and review is published."
    return result

def review_repo(user_gitee, owner, repo):
    """"
    Get PRs in give repo, or doing nothing if no PR
    """
    result = f'{owner}/{repo}'.format(owner=owner, repo=repo)
    PRs = user_gitee.list_pr(repo, owner)
    if not PRs:
        return
    else:
        for pr in PRs:
            pending_pr = {}
            pending_pr['repo'] = repo
            pending_pr['number'] = pr["number"]
            pending_pr['owner'] = owner
            #print(pending_pr)
            PENDING_PRS.put(pending_pr)

def generate_pending_prs(user_gitee, sig):
    """
    Generate pending PRs
    """
    src_oe_repos = user_gitee.get_repos_by_sig(sig)
    for repo in src_oe_repos:
        review_repo(user_gitee, 'src-openeuler', repo)

    oe_repos = user_gitee.get_openeuler_repos_by_sig(sig)
    for repo in oe_repos:
        review_repo(user_gitee, 'openeuler', repo)

    PENDING_PRS.put(None)
    print("DONE PENDING GENERATE")
    return 0


def main():
    """
    Main entrance of the functionality
    """
    args = args_parser()
    if args.quiet:
        sys.stdout = open('/dev/null', 'w')
        sys.stderr = sys.stdout

    try:
        user_gitee = gitee.Gitee()
    except NameError:
        sys.exit(1)

    if args.active_user:
        generate_pending_prs_thread = threading.Thread(target=generate_pending_prs, args=(user_gitee, args.sig))
        sort_pr_thread = threading.Thread(target=sort_pr, args=(user_gitee,))
        ai_review_thread = threading.Thread(target=ai_review, args=(user_gitee,))
        manually_review_thread = threading.Thread(target=manually_review, args=(user_gitee, args.editor))
        submmit_review_thread = threading.Thread(target=submmit_review, args=(user_gitee,))

        generate_pending_prs_thread.start()
        sort_pr_thread.start()
        ai_review_thread.start()
        manually_review_thread.start()
        submmit_review_thread.start()

        generate_pending_prs_thread.join()
        sort_pr_thread.join()
        ai_review_thread.join()
        manually_review_thread.join()
        submmit_review_thread.join()

        # 获取当前用户所有担任 maintainer 的 sig，以及所有担任 committer 的 代码仓
        # 此处应考虑建立本地缓存，保留PR的标签，最近更新，如果和本地缓存相比没有更新就忽略，否则更新 review
        # 然后根据不同的模型生成 review
    else:
        params = extract_params(args)
        if not params:
            return 1
        group = params[0]
        repo_name = params[1]
        pull_id = params[2]
        review_pr(user_gitee, repo_name, pull_id, group, args.editor)

    return 0


if __name__ == "__main__":
    sys.exit(main())

