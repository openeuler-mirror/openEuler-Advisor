#!/usr/bin/env python3
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
import collections
import queue
import tempfile
import urllib
import urllib.error
import urllib.request
import urllib.parse
import http.client
import yaml
import json
import requests
import configparser
import math

from openai import OpenAI
import chromadb

from advisors import gitee


GLOBAL_MAX_RETRY = 1000
GLOBAL_TIMEOUT = 60
GLOBAL_VERBOSE = False

OE_REVIEW_PR_PROMPT="""
You are a code reviewer of a openEuler Pull Request, providing feedback on the code changes below.
      As a code reviewer, your task is:
      - Review the code changes (diffs) in the patch and provide feedback.
      - If changelog is updated, it should describe visible changes to end-users or developers, not simply say "upgrade to blahblah".
      - If there are any bugs, highlight them.
      - Does the code do what it says in the commit messages?
      - Do not highlight minor issues and nitpicks.
      - Use bullet points if you have multiple comments.
      - If no suggestions are provided, please give good feedback.
      - please use chinese to give feedback.
      - Based on the feedback all above, if the Pull Request is good, you need to decide merge the Pull Request by respones "/lgtm /approve".
      - If the Pull Request is not good, you need to reject it by response "/close".
      - Give this decision in the first line.
Following is a previous example of Pull Request review, You can use it as a reference. 
{example}
Now you are provided with the pull request changes in complete format.
It includes the repository name, target branch, pull request title, pull request body,
Patch of the Pull Request and Review History of the Pull Request.
"""

OE_REVIEW_PR_PROMPT_OLD="""
You are a code reviewer of a openEuler Pull Request, providing feedback on the code changes below.
      As a code reviewer, your task is:
      - Above all, you need to decide "/close" the PR, or "/lgtm" and "/approve" the PR.
      - Review the code changes (diffs) in the patch and provide feedback.
      - If changelog is updated, it should describe visible changes to end-users or developers, not simply say "upgrade to blahblah".
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

CHROMADB_DB_PATH = os.path.expanduser("~/.config/openEuler-Advisor/chromadb")
CHROMADB_COLLECTION_NAME = "oe_review"

g_chromadb_client = None
g_chromadb_collection = None

# define data structure that contains queue and mutex lock for thread sharing
import threading
import time

def print_verbose(msg):
    global GLOBAL_VERBOSE
    if GLOBAL_VERBOSE:
        print(msg)

class ThreadSafeQueueSimple:
    def __init__(self):
        self.queue = []  # Your data structure (list) can be replaced with any other like deque from collections
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

    def put(self, item):
        with self.condition:
            self.queue.append(item)
            self.condition.notify_all()  # Notify all waiting threads that new item is added

    def get(self):
        with self.condition:
            while len(self.queue) == 0:
                self.condition.wait()  # Wait until there are items in the queue
            item = self.queue.pop(0)
            return item

    def qsize(self):
        with self.lock:
            return len(self.queue)

class ThreadSafeQueueComplex:
    def __init__(self, maxsize=0):
        self.queue = collections.deque()  # 使用deque替代list
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.maxsize = maxsize  # 添加最大容量限制
    
    def put(self, item, block=True, timeout=None):
        with self.condition:
            while self.maxsize > 0 and len(self.queue) >= self.maxsize:
                if not block:
                    raise self.queue.Full
                if timeout is not None:
                    if not self.condition.wait(timeout):
                        raise self.queue.Full
                else:
                    self.condition.wait()
            self.queue.append(item)
            self.condition.notify()
    
    def get(self, block=True, timeout=None):
        with self.condition:
            while len(self.queue) == 0:
                if not block:
                    raise queue.Empty
                if timeout is not None:
                    if not self.condition.wait(timeout):
                        raise queue.Empty
                else:
                    self.condition.wait()
            item = self.queue.popleft()  # 使用popleft()而不是pop(0)
            self.condition.notify()
            return item

# 建三个队列，一个是待处理PR列表，一个是经过预处理的PR列表，一个是待提交PR列表
# 批处理，首先关闭所有可以关闭的PR，直接合并sync且没有ci_failed的PR
# 然后对所有其他的PR再进行review
# define 3 queues to be shared across threads
# List of PRs to be reviewed, by review_repos()
PENDING_PRS = queue.Queue()
# sort_pr() get pr from PENDING_PRS, if can be obviously handled, put comment into submitting_prs, otherwise, move to NEED_REVIEW_PRS
# that are being preprocessed for review
NEED_REVIEW_PRS = queue.Queue()
# manually_review() get pr from NEED_REVIEW_PRS, and edit comment
MANUAL_REVIEW_PRS = queue.Queue()
# PRs that are being submitted 
SUBMITTING_PRS = queue.Queue()

#def generate_review_from_ollama(pr_content, prompt, model="llama3.1:8b"):
def generate_review_from_ollama(pr_content, prompt, model):
    base_url = "http://localhost:11434/api"
    json_resp = []
    resp = None
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW 64; rv:50.0) '\
                        'Gecko/20100101 Firefox/50.0'}
    headers["Content-Type"] = "application/json;charset=UTF-8"
    
    url = f"{base_url}/generate"
    num_ctx = math.ceil((len(pr_content) + len(prompt)) / 2048) * 2048
    values = {}
    values["model"] = model
    values['prompt'] = pr_content
    values['system'] = prompt
    values['stream'] = False
    values['options'] = {"num_ctx": num_ctx}
    print_verbose("ollama request model: "+model)
    print_verbose("ollama request prompt: "+prompt)
    print_verbose("ollama request content: "+pr_content)
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
    pars.add_argument("-q", "--quite", action='store_true', default=False, help="Disable all log print")
    pars.add_argument("-v", "--verbose", action='store_true', default=False, help="Print Verbose Log")
    pars.add_argument("-a", "--active_user", action='store_true', default=False, help="Review all PRs in repositories as maintainer or committer")
    pars.add_argument("-n", "--repo", type=str, help="Repository name that include group")
    pars.add_argument("-p", "--pull", type=str, help="Number ID of Pull Request")
    pars.add_argument("-u", "--url", type=str, help="URL of Pull Request")
    pars.add_argument("-s", "--sig", type=str, default="", help="When active_user is set, review all PRs in specified SIG")
    pars.add_argument("-m", "--model", type=str, help="Model of selection to generate review")
    pars.add_argument("-e", "--editor", type=str, help="Editor of choice to edit content, default to nvim")
    pars.add_argument("-b", "--no_ai", action='store_true', default=False, help="No AI to generate review")
    pars.add_argument("-o", "--editor-option", type=str, help="Commandline option for editor")
    return pars.parse_args()

def load_config():
    """
    Load config from config file
    """
    cf = configparser.ConfigParser()
    cf_path = os.path.expanduser("~/.config/openEuler-Advisor/config.ini")
    if os.path.exists(cf_path):
        cf.read(cf_path)
        return cf
    else:
        print("ERROR: miss config file:"+cf_path)
        return None

def edit_content(text, editor):
    fd, path = tempfile.mkstemp(suffix=".tmp", prefix="oe_review")
    with os.fdopen(fd, 'w') as tmp:
        tmp.write(text)
        tmp.flush()

        result = subprocess.run([editor["editor"], editor["editor-option"], path], capture_output=True, text=True)
        print_verbose(result.stdout)
        print_verbose(result.stderr)

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

def review_history(user_gitee, owner, repo, number, pull_request):
    review_comment = {}
    review_comment['target_branch'] = pull_request["base"]["ref"]
    history_comment = ""
    sync_comment = ""
    advisor_comment = ""
    comments = user_gitee.get_pr_comments_all(owner, repo, number)
    for comment in comments:
        if comment['user']['name'] == "openeuler-ci-bot":
            if comment['body'].startswith("\n**以下为 openEuler-Advisor"):
                advisor_comment = comment['body']
        elif comment['user']['name'] == "openeuler-sync-bot":
            sync_comment += comment["body"] + "\n"
        else:
            history_comment += comment["user"]["name"] + ":\n"
            history_comment += comment["body"] + "\n"
    review_comment['history_comment'] = history_comment
    review_comment['sync_comment'] = sync_comment
    review_comment['advisor_comment'] = advisor_comment
    return review_comment

def filter_pr(pull_request, filter):
    print_verbose("filter is: "+str(filter))
    for label in pull_request["labels"]:
        if label["name"] in filter["labels"]:
            return True
    if pull_request["user"]["login"] in filter["submitters"]:
        return True
    for filter_repo in filter["repos"]:
        if re.match(filter_repo, pull_request["head"]["repo"]["path"]):
            return True
    return False

def sort_pr(user_gitee, filter):
    wait_error = 0
    while True:
        try:
            review_item = PENDING_PRS.get(timeout=GLOBAL_TIMEOUT)
        except queue.Empty as e:
            print("PENDING_PRS queue is empty for a while.")
            if wait_error >= GLOBAL_MAX_RETRY:
                break
            else:
                wait_error = wait_error + 1 
                continue
        if not review_item:
            PENDING_PRS.task_done()
            break
        #print(f"Got {item} from queue")

        pull_request = user_gitee.get_pr(review_item["repo"], review_item["number"], review_item["owner"])
        PENDING_PRS.task_done()

        if filter_pr(pull_request, filter):
            continue

        suggest_action, suggest_reason = easy_classify(pull_request)

        review_comment = review_history(user_gitee, review_item['owner'], review_item['repo'], review_item['number'], pull_request)
        review_item['review_comment'] = review_comment

        if suggest_action == "":
            review_item['pull_request'] = pull_request
            NEED_REVIEW_PRS.put(review_item)
        else:
            review_comment_raw = suggest_action + "\n" + suggest_reason
            review_item['review_comment'] = review_comment_raw
            review_item['pull_request'] = pull_request
            review_item['suggest_action'] = suggest_action
            review_item['suggest_reason'] = suggest_reason
            SUBMITTING_PRS.put(review_item)

    NEED_REVIEW_PRS.put(None)
    print_verbose("sort pr finished")
    NEED_REVIEW_PRS.join()
    print_verbose("NEED_REVIEW_PRS join finished")

def ai_review_impl(user_gitee, repo, pull_id, group, ai_flag, ai_model, review_comment, pull_request):
    global g_chromadb_client
    global g_chromadb_collection

    pr_diff = user_gitee.get_diff(repo, pull_id, group)
    if not pr_diff:
        print("Failed to get PR:%s of repository:%s/%s, make sure the PR is exist." % (pull_id, group, repo))
        return "", "", ""
    if not ai_flag:
        return pr_diff, "", ""

    if g_chromadb_client is None:
        g_chromadb_client = chromadb.PersistentClient(path=CHROMADB_DB_PATH)
        g_chromadb_collection = g_chromadb_client.get_or_create_collection(CHROMADB_COLLECTION_NAME)

    chomadb_query_text = pr_diff
    chromadb_result = g_chromadb_collection.query(
        query_texts=[chomadb_query_text],
        n_results=2,
        include=["documents"]
    )

    print_verbose(chromadb_result["documents"])

    if len(chromadb_result["documents"][0]) == 0:
        review_example = chromadb_result["documents"][0]
    else:
        review_example = chromadb_result["documents"][0][0]

    review_content = """
    Pull Request to {owner}/{repo}:{target_branch}
    Pull Request Title: {title}
    Pull Request Body: {body}
    Patch of the Pull Request:
    {pr_diff}
    Review History of the Pull Request: 
    {history_comment}
    """.format(owner=group, repo=repo, target_branch=pull_request["base"]["ref"],
               title=pull_request["title"], body=pull_request["body"],
               pr_diff=pr_diff, history_comment=review_comment["history_comment"])
    review_prompt = OE_REVIEW_PR_PROMPT.format(example=review_example)

    #review = generate_review_from_ollama(pr_diff, OE_REVIEW_PR_PROMPT, ai_model)
    review = generate_review_from_ollama(review_content, review_prompt, ai_model)
    review_rating = generate_review_from_ollama(pr_diff, OE_REVIEW_RATING_PROMPT, ai_model)   
    return pr_diff, review, review_rating

def ai_review(user_gitee, ai_flag, ai_model):
    wait_error = 0
    while True:
        try:
            review_item = NEED_REVIEW_PRS.get(timeout=GLOBAL_TIMEOUT)
        except queue.Empty as e:
            print_verbose("NEED_REVIEW_PRS queue is empty for a while.")
            if wait_error > GLOBAL_MAX_RETRY:
                break
            else:
                wait_error = wait_error + 1
                continue
        if not review_item:
            NEED_REVIEW_PRS.task_done()
            break

        pr_diff, review, review_rating = ai_review_impl(user_gitee, review_item['repo'], review_item['number'], review_item['owner'], 
                                                        ai_flag, ai_model, review_item['review_comment'], review_item['pull_request'])
        NEED_REVIEW_PRS.task_done()
    
        if pr_diff == "":
            continue

        review_item['pr_diff'] = pr_diff
        review_item['review'] = review
        review_item['review_rating'] = review_rating
        MANUAL_REVIEW_PRS.put(review_item)
    MANUAL_REVIEW_PRS.put(None)
    print_verbose("ai review finished")
    MANUAL_REVIEW_PRS.join()
    print_verbose("MANUAL_REVIEW_PRS join finished")

def clean_advisor_comment(comment):
    """
    replace icon in advisor comment
    """
    comment = comment.replace('[&#x1F535;]', 'ongoing').replace('[&#x1F7E1;]', 'question')
    comment = comment.replace('[&#x25EF;]', 'NA').replace('[&#x1F534;]', 'nogo').replace('[&#x1F7E2;]', 'GO')
    comment = comment.replace('[&#x1F600;]', 'smile').replace('[:white_check_mark:]', 'GO')
    return comment

def manually_review_impl(user_gitee, pr_info, pull_request, review, review_rating, pr_diff, editor):
    review_content = ""
    review_content += "!{number}: {title}\n# {body}\n".format(number=pull_request["number"], title=pull_request["title"], body=pull_request["body"])
    review_content += "This PR has following labels:\n"
    for label in pull_request["labels"]:
        review_content += f"{label['name']}  "
    target_branch = pull_request["base"]["ref"]
    review_content += "\nThis PR is submitted to {branch}\n".format(branch=target_branch)
    history_comment = ""
    sync_comment = ""
    advisor_comment = ""
    comments = user_gitee.get_pr_comments_all(pr_info['owner'], pr_info['repo'], pr_info['number'])
    for comment in comments:
        if comment['user']['name'] == "openeuler-ci-bot":
            if comment['body'].startswith("\n**以下为 openEuler-Advisor"):
                advisor_comment = comment['body']
        elif comment['user']['name'] == "openeuler-sync-bot":
            sync_comment += comment["body"] + "\n"
        else:
            history_comment += comment["user"]["name"] + ":\n"
            history_comment += comment["body"] + "\n"

    review_content += "\n# Branch Status\n" + sync_comment
    review_content += "\n# History\n" + history_comment
    review_content += "\n# Advisor\n" + clean_advisor_comment(advisor_comment)
    review_comment_raw = edit_content(review_content + '\n\n# ReviewBot\n\n' + review + '\n\n# ReviewRating\n\n' + review_rating + '\n\n' + pr_diff, editor)

    global g_chromadb_client
    global g_chromadb_collection
    # save review_comment_raw to chromadb
    if g_chromadb_client is None:
        g_chromadb_client = chromadb.PersistentClient(path=CHROMADB_DB_PATH)
        g_chromadb_collection = g_chromadb_client.get_or_create_collection(CHROMADB_COLLECTION_NAME)

    chromadb_document = """
    Pull Request to {owner}/{repo}:{target_branch}
    Pull Request Title: {title}
    Pull Request Body: {body}
    Patch of the Pull Request:
    {pr_diff}
    Review History of the Pull Request: 
    {history_comment}
    My Review Comment:
    {review_comment}
    """.format(owner=pr_info["owner"], repo=pr_info["repo"], target_branch=target_branch,
               title=pull_request["title"], body=pull_request["body"], 
               pr_diff=pr_diff, history_comment=history_comment, 
               review_comment=review_comment_raw)
    
    g_chromadb_collection.upsert(
        documents=[chromadb_document],
        metadatas=[{"owner": pr_info["owner"], "repo": pr_info["repo"]}],
        ids=[str(pr_info["owner"]) + "/" + str(pr_info["repo"]) + "/" + str(pr_info["number"])]
    )
    return review_comment_raw

def manually_review(user_gitee, editor):
    wait_error = 0
    while True:
        try:
            review_item  = MANUAL_REVIEW_PRS.get(timeout=GLOBAL_TIMEOUT)
        except queue.Empty as e:
            print_verbose("MANUAL_REVIEW_PRS queue is empty for a while.")
            if wait_error >= GLOBAL_MAX_RETRY:
                break
            else:
                wait_error = wait_error + 1
                continue

        if not review_item:
            MANUAL_REVIEW_PRS.task_done()
            break

        pr_info = {}
        pr_info["owner"] = review_item['owner']
        pr_info["repo"] = review_item["repo"]
        pr_info["number"] = review_item["number"]

        review_comment_raw = manually_review_impl(user_gitee, pr_info, 
                                                  review_item['pull_request'], 
                                                  review_item['review'], 
                                                  review_item['review_rating'], 
                                                  review_item['pr_diff'], 
                                                  editor)

        review_item['review_comment'] = review_comment_raw
        MANUAL_REVIEW_PRS.task_done()
        SUBMITTING_PRS.put(review_item)

    SUBMITTING_PRS.put(None)
    print_verbose("manually review finished")
    SUBMITTING_PRS.join()
    print_verbose("SUBMITTING_PRS join finished")

def submit_review_impl(user_gitee, pr_info, pull_request, review_comment, suggest_action="", suggest_reason=""):
    result = " is handled and review is published."
    print("{owner}/{repo}!{number}: {title}".format(owner=pr_info["owner"], repo=pr_info["repo"], number=pr_info["number"], title=pull_request["title"]))

    if review_comment == "":
        print(" - review comment is ignored due to empty content")
        return
    
    last_comment = user_gitee.get_pr_comments_all(pr_info['owner'], pr_info['repo'], pr_info['number'])

    review_to_submit = ""
    for line in review_comment.split("\n"):
        if line == "====":
            if review_to_submit == "":
                continue
            if last_comment[-1]['body'] == review_to_submit:
                print(" - review comment is ignored due to duplication with last comment")
                continue
            try:
                user_gitee.create_pr_comment(pr_info['repo'], pr_info['number'], review_to_submit, pr_info['owner'])
            except http.client.RemoteDisconnected as e:
                print("Failed to sumit review comment: {error}".format(error=e))
            review_to_submit = ""
        else:
            review_to_submit += line + "\n"
    else:
        if review_to_submit == last_comment[-1]['body']:
            print(" - review comment is ignored due to duplication with last comment")
        else:
            try:
                user_gitee.create_pr_comment(pr_info['repo'], pr_info['number'], review_to_submit, pr_info['owner'])
            except http.client.RemoteDisconnected as e:
                print("Failed to sumit review comment: {error}".format(error=e))


    if suggest_action == "/close":
        result = " is closed due to {reason}.".format(reason=suggest_reason)
    elif suggest_action == "暂不处理":
        result = " is skipped due to {reason}.".format(reason=suggest_reason)
    elif suggest_action == "/lgtm\n/approve":
        result = " is approved due to {reason}.".format(reason=suggest_reason)
    else:
        pass
    print(" - PR{res}".format(res=result))

def submmit_review(user_gitee):
    wait_error = 0
    while True:
        try:
            review_item = SUBMITTING_PRS.get(timeout=GLOBAL_TIMEOUT)
        except queue.Empty as e:
            print("SUBMITTING_PRS queue is empty for a while.")
            if wait_error >= GLOBAL_MAX_RETRY:
                break
            else:
                wait_error = wait_error + 1
                continue
        #print("submit review works")
        #print(item)
        if not review_item:
            SUBMITTING_PRS.task_done()
            break
        
        pr_info = {}
        pr_info['owner'] = review_item['owner']
        pr_info['repo'] = review_item['repo']
        pr_info['number'] = review_item['number']
        
        suggest_action = review_item.get('suggest_action', "")
        suggest_reason = review_item.get('suggest_reason', "")

        submit_review_impl(user_gitee, pr_info, 
                           review_item['pull_request'], 
                           review_item['review_comment'], 
                           suggest_action, suggest_reason)
        SUBMITTING_PRS.task_done()
    print_verbose("submit review finish")

def review_pr(user_gitee, repo_name, pull_id, group, editor, ai_flag, ai_model, filter):
    """
    New Implementation of Review Pull Request, reuse code from threading implementation
    """
    pr_info = {}
    pr_info["repo"] = repo_name
    pr_info['number'] = pull_id
    pr_info['owner'] = group

    pull_request = user_gitee.get_pr(repo_name, pull_id, group)

    if filter_pr(pull_request, filter):
        print("PR has been filtered, do not review")
        return
    print_verbose("Doing review")
    suggest_action, suggest_reason = easy_classify(pull_request)
    review_history_comment = review_history(user_gitee, group, repo_name, pull_id, pull_request)
    pr_diff, review, review_rating = ai_review_impl(user_gitee, repo_name, pull_id, group, ai_flag, ai_model, review_history_comment, pull_request)
    review_comment = manually_review_impl(user_gitee, pr_info, pull_request, review, review_rating, pr_diff, editor)
    submit_review_impl(user_gitee, pr_info, pull_request, review_comment, suggest_action, suggest_reason)

    print_verbose("Finish Review")

def review_repo(user_gitee, owner, repo):
    """"
    Get PRs in give repo, or doing nothing if no PR
    """
    result = f'{owner}/{repo}'.format(owner=owner, repo=repo)
    try:
        PRs = user_gitee.list_pr(repo, owner)
    except urllib.error.URLError as e:
        print(e)
        print(f'Failed to get PRs in {owner}/{repo}'.format(owner=owner, repo=repo))
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

def print_progress(current, total, percentage):
    #print current progress when cur is 10%, 20% ... till 100%
    #keep silent otherwise
    if (current / total) * 100 > percentage: 
        print(f'generate_pending_prs in {percentage}%')
        return True
    else:
        return False

def generate_pending_prs_old(user_gitee, sig):
    """
    Generate pending PRs
    """
    src_oe_repos = user_gitee.get_repos_by_sig(sig)
    oe_repos = user_gitee.get_openeuler_repos_by_sig(sig)
    
    total_len = len(src_oe_repos) + len(oe_repos)
    current_percentage = 10
    counter = 0

    print_verbose(f"start generate list of pending pr.")
    for repo in src_oe_repos:
        counter = counter + 1
        if print_progress(counter, total_len, current_percentage):
            current_percentage = current_percentage + 10
        review_repo(user_gitee, 'src-openeuler', repo)

    for repo in oe_repos:
        counter = counter + 1
        if print_progress(counter, total_len, current_percentage):
            current_percentage = current_percentage + 10
        review_repo(user_gitee, 'openeuler', repo)

    PENDING_PRS.put(None)
    print_verbose("generate_pending_pr finished")
    PENDING_PRS.join()
    print_verbose("PENDING_PRS join finished")
    return 0

def get_responsible_sigs(user_gitee):
    """
    Get responsible sigs from config file
    """
    sigs = user_gitee.get_sigs()
    result = []
    for sig in sigs:
        if sig == "sig-minzuchess" or sig == "README.md":
            continue
        sig_info_str = user_gitee.get_sig_info(sig)
        if sig_info_str == None:
            continue
        sig_info = yaml.load(sig_info_str, Loader=yaml.FullLoader)
        for maintainer in sig_info["maintainers"]:
            if maintainer["gitee_id"].lower() == user_gitee.token['user'].lower():
                result.append((sig_info["name"]))
    return result

def get_quickissue(url):
    try:
        result = urllib.request.urlopen(url)
        json_resp = json.loads(result.read().decode("utf-8"))
        return json_resp
    except urllib.error.HTTPError as error:
        print("get_quickissue failed to access: %s" % (url))
        print("get_quickissue failed: %d, %s" % (error.code, error.reason))
        return None

def get_quickissue_pulls_by_sig(sig):
        """
        GET from quckissue api
        """
        quickissue_base_url = "https://quickissue.openeuler.org/api-issues/pulls"

        query_url = quickissue_base_url + "?sig=" + sig + "&page=1&per_page=100&sort=created_at&state=open"
        results = []
        total = 0
        pages = 1
        json_resp = get_quickissue(query_url)
        if json_resp == None:
            return results, total
        elif json_resp["data"] == None:
            return results, total
        
        total = json_resp["total"]
        
        for d in json_resp["data"]:
            res = {}
            res['owner'] = d["repo"].split("/")[0]
            res['repo'] = d["repo"].split("/")[1]
            res['number'] = d["link"].split("/")[-1]
            results.append(res)

        pages = math.ceil(json_resp["total"] / json_resp["per_page"])

        for page in range(2, pages + 1):
            query_url = quickissue_base_url + "?sig=" + sig + "&page=" + str(page) + "&per_page=100&sort=created_at&state=open"
            json_resp = get_quickissue(query_url)
            if json_resp == None:
                return results, total
            elif json_resp["data"] == None:
                return results, total
            for d in json_resp["data"]:
                res = {}
                res['owner'] = d["repo"].split("/")[0]
                res['repo'] = d["repo"].split("/")[1]
                res['number'] = d["link"].split("/")[-1]
                results.append(res)
        return results, total

def generate_pending_prs(user_gitee, sig):
    """
    Generating pending PR via quickissue
    """
    results, total = get_quickissue_pulls_by_sig(sig)

    print_verbose(f"start generate list of pending pr.")

    print_verbose("Pending PRs of {sig}: {results}".format(sig=sig, results=results))
    for result in results:
        PENDING_PRS.put(result)

    PENDING_PRS.put(None)
    print_verbose("generate_pending_pr finished")
    PENDING_PRS.join()
    print_verbose("PENDING_PRS join finished")
    return 0

def review_sig(user_gitee, sig, editor, ai_flag, ai_model, filter):
    """
    Review sig
    1. Generate pending PRs for sig
    2. Close or accept PR for easy ones
    3. Generate AI Comments for sophisitcated PR
    4. Manually edit comment
    5. Submit PR review
    """

    print("Reviewing sig: {}".format(sig))
    generate_pending_prs_thread = threading.Thread(target=generate_pending_prs, args=(user_gitee, sig))
    sort_pr_thread = threading.Thread(target=sort_pr, args=(user_gitee, filter))
    ai_review_thread = threading.Thread(target=ai_review, args=(user_gitee, ai_flag, ai_model))
    manually_review_thread = threading.Thread(target=manually_review, args=(user_gitee, editor))
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

def main():
    """
    Main entrance of the functionality
    """
    args = args_parser()
    cf = load_config()

    if args.verbose:
        global GLOBAL_VERBOSE
        GLOBAL_VERBOSE = True
    
    if args.quite:
        sys.stdout = open('/dev/null', 'w')
        sys.stderr = sys.stdout

    try:
        user_gitee = gitee.Gitee()
    except NameError:
        sys.exit(1)

    
    editor = {}
    # command line overrides config file
    editor["editor"] = cf.get('editor', 'command')
    if args.editor:
        editor["editor"] = args.editor
    editor["editor-option"] = cf.get('editor', 'option')
    if args.editor_option:
        editor["editor-option"] = args.editor_option

    ai_model = cf.get('model', 'name')
    if args.model:
        ai_model = args.model

    filter = {}
    filter['labels'] = set(cf.get('filter', 'labels').split())
    filter['submitters'] = set(cf.get('filter', 'submitters').split())
    filter['repos'] = set(cf.get('filter', 'repos').split())

    global g_chromadb_client
    global g_chromadb_collection
    g_chromadb_client = chromadb.PersistentClient(path=CHROMADB_DB_PATH)
    g_chromadb_collection = g_chromadb_client.get_or_create_collection(CHROMADB_COLLECTION_NAME)

    if args.active_user:
        if args.sig == "":
            sigs = get_responsible_sigs(user_gitee)
            for sig in sigs:
                review_sig(user_gitee, sig, editor, not args.no_ai, ai_model, filter)
        else:
            review_sig(user_gitee, args.sig, editor, not args.no_ai, ai_model, filter)
    else:
        params = extract_params(args)
        if not params:
            return 1
        group = params[0]
        repo_name = params[1]
        pull_id = params[2]
        review_pr(user_gitee, repo_name, pull_id, group, editor, not args.no_ai, ai_model, filter)

    return 0


if __name__ == "__main__":
    sys.exit(main())

