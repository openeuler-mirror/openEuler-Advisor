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
import openai
import chromadb

from advisors import gitee


GLOBAL_MAX_RETRY = 60 * 24 * 3
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

# define data structure to contain AI model information
class oe_review_ai_model:
    def __init__(self, type):
        if type == "local":
            self._type = type
            self._base_url = "http://localhost:11434/api"
            self._model_name = "llama3.1:8b"
            self._method = "ollama"
        elif type == "deepseek":
            self._type = "deepseek"
            self._base_url = "https://api.deepseek.com"
            self._model_name = "deepseek-chat"
            self._api_key = ""
            self._method = "openai"
        elif type == "bailian":
            self._type = "bailian"
            self._base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            self._model_name = "deepseek-v3"
            self._api_key = ""
            self._method = "openai"
        elif type == "siliconflow":
            self._type = "siliconflow"
            self._base_url = "https://api.siliconflow.cn/v1/chat/completions"
            self._model_name = "deepseek-r1"
            self._api_key = ""
            self._method = "openai"
        elif type == "no":
            self._type = "no"
        else:
            self._type = type

    @property
    def type(self):
        return self._type
    @type.setter
    def type(self, new_value):
        self._type = new_value

    @property
    def base_url(self):
        return self._base_url
    @base_url.setter
    def base_url(self, new_value):
        self._base_url = new_value

    @property
    def model_name(self):
        return self._model_name
    @model_name.setter
    def model_name(self, new_value):
        self._model_name = new_value

    @property
    def api_key(self):
        if self._type != "local" and self.type != "no":
            return self._api_key
        else:
            return ""
    @api_key.setter
    def api_key(self, new_value):
        if self._type != "local" and self.type != "no":
            self._api_key = new_value
        else:
            pass # we dont need api_key for local or no

    @property
    def method(self):
        return self._method
    @method.setter
    def method(self, new_value):
        self._method = new_value

def print_verbose(msg):
    global GLOBAL_VERBOSE
    if GLOBAL_VERBOSE:
        print(msg)

# 建四个队列，一个是待处理PR队列，一个是经过预处理的PR队列，一个是待人工审核的PR队列，一个是待提交PR队列
# 批处理，首先关闭所有可以关闭的PR，直接合并sync且没有ci_failed的PR
# 然后对所有其他的PR再进行review
# define 4 queues to be shared across threads
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
def generate_review_from_ollama(pr_content, prompt, ai_model):
    base_url = "http://localhost:11434/api"
    json_resp = []
    resp = None
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW 64; rv:50.0) '\
                        'Gecko/20100101 Firefox/50.0'}
    headers["Content-Type"] = "application/json;charset=UTF-8"
    
    url = f"{base_url}/generate"
    num_ctx = math.ceil((len(pr_content) + len(prompt)) / 2048) * 2048
    values = {}
    model = ai_model.model_name
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

def generate_review_from_request(pr_content, prompt, model):
    """Send review request to API endpoint and return response"""
    messages = [
        {"role": "user", "content": urllib.parse.quote(pr_content)},
        {"role": "system", "content": urllib.parse.quote(prompt)}
    ]
    
    payload = {
        "model": model.model_name,
        "messages": messages,
        "stream": False
    }
    
    headers = {
        "Authorization": f"Bearer {model.api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(model.base_url, json=payload, headers=headers)
    return response.text

def generate_review_from_openai(pr_content, prompt, model):
    #Get URL and API Key from config file
    print_verbose("api_key: " + model.api_key)
    print_verbose("base_url: " + model.base_url)
    print_verbose("model_name: " + model.model_name)
    client = OpenAI(api_key=model.api_key, base_url=model.base_url)
    try:
        response = client.chat.completions.create(
            model = model.model_name,
            messages = [
                {'role': 'system', 'content': urllib.parse.quote(prompt)},
                {'role': 'user', 'content': urllib.parse.quote(pr_content)},
            ],
            stream = False
        )
        print_verbose(f"response is {response.model_dump_json()}")
        return (response.choices[0].message.content)
    except openai.APIError as e:
        print(f"API Error: {e.status_code} - {e.message}")
    except openai.APIConnectionError as e:
        print(f"Connection error: {e}")
    except openai.RateLimitError as e:
        print(f"Rate limit exceeded: {e}")
    except openai.AuthenticationError as e:
        print(f"Authentication failed: {e}")
    except openai.BadRequestError as e:
        print(f"Invalid request: {e}")
    except openai.OpenAIError as e:
        print(f"OpenAI error: {e}")    
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}, {str(e)}")

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
            return (res.group(3), res.group(4), res.group(5))
        print("ERROR: URL is wrong, please check!")
        return ()
        
    if args.repo and args.pull:
        group, repo_name = args.repo.split('/')
        return (group, repo_name, args.pull)

    print("WARNING: please specify the URL of PR or repository name and PR's ID.\nDetails use -h/--help option.")
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
    pars.add_argument("-i", "--intelligent", type=str, help="Select Intelligent from local/deepseek/no")
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
    """
    Edit content using the specified editor.
    
    Args:
        text (str): The text content to edit
        editor (dict): Dictionary containing editor and editor options
    
    Returns:
        str: The edited text content
    """
    print_verbose("starting edit_content")
    
    # Create temporary file
    fd, temp_path = tempfile.mkstemp(suffix=".tmp", prefix="oe_review")
    
    # Write content to temp file
    with os.fdopen(fd, 'w') as temp_file:
        temp_file.write(text)
        temp_file.flush()

    print_verbose(editor["editor-option"])
    
    # Launch editor based on options
    if editor["editor-option"] == '""':
        # Simple editor launch
        editor_process = subprocess.Popen([editor["editor"], temp_path])
        editor_process.wait()
    else:
        # Launch with additional options
        result = subprocess.run([editor["editor"], editor["editor-option"], temp_path])
        print_verbose(result.stdout)
        print_verbose(result.stderr)

    # Read and return edited content
    with open(temp_path) as edited_file:
        return edited_file.read()

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
    comments = user_gitee.get_pr_comments_all(owner, repo, number)
    
    return {
        'target_branch': pull_request["base"]["ref"],
        'advisor_comment': next((c['body'] for c in comments 
                               if c['user']['name'] == "openeuler-ci-bot" 
                               and c['body'].startswith("\n**以下为 openEuler-Advisor")), ""),
        'sync_comment': ''.join(c['body'] + '\n' for c in comments 
                              if c['user']['name'] == "openeuler-sync-bot"),
        'history_comment': ''.join(f"{c['user']['name']}:\n{c['body']}\n" for c in comments
                                 if c['user']['name'] not in ["openeuler-ci-bot", "openeuler-sync-bot"])
    }

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

def ai_review_impl(user_gitee, repo, pull_id, group, ai_model, review_comment, pull_request):
    global g_chromadb_client
    global g_chromadb_collection

    print_verbose("start getting diff")
    pr_diff = user_gitee.get_diff(repo, pull_id, group)
    if not pr_diff:
        print("Failed to get PR:%s of repository:%s/%s, make sure the PR is exist." % (pull_id, group, repo))
        return "", "", ""
    else:
        print_verbose(f"pr_diff is {pr_diff}")

    if ai_model.type == "no":
        return pr_diff, "", ""

    print_verbose("initialize chromadb instance")
    if g_chromadb_client is None:
        g_chromadb_client = chromadb.PersistentClient(path=CHROMADB_DB_PATH)
        g_chromadb_collection = g_chromadb_client.get_or_create_collection(CHROMADB_COLLECTION_NAME)

    print_verbose(f"start querying chromadb")
    chomadb_query_text = pr_diff
    chromadb_result = g_chromadb_collection.query(
        query_texts=[chomadb_query_text],
        n_results=2,
        include=["documents"]
    )

    print_verbose(f"chromadb search result: {chromadb_result['documents']}")

    if len(chromadb_result["documents"][0]) == 0:
        review_example = chromadb_result["documents"][0]
    else:
        review_example = chromadb_result["documents"][0][0]

    print_verbose(f"review example is {review_example}")

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

    print_verbose(f"review_prompt is: {review_prompt}")

    if ai_model.method == "ollama":
        review = generate_review_from_ollama(review_content, review_prompt, ai_model)
        review_rating = generate_review_from_ollama(pr_diff, OE_REVIEW_RATING_PROMPT, ai_model)
    elif ai_model.method == "openai":
        review = generate_review_from_openai(review_content, review_prompt, ai_model)
        review_rating = generate_review_from_openai(pr_diff, OE_REVIEW_RATING_PROMPT, ai_model)
    elif ai_model.method == "requests":
        review = generate_review_from_request(review_content, review_prompt, ai_model)
        review_rating = generate_review_from_request(pr_diff, OE_REVIEW_RATING_PROMPT, ai_model)
    return pr_diff, review, review_rating

def ai_review(user_gitee, ai_model):
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
                                                        ai_model, review_item['review_comment'], review_item['pull_request'])
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

    if review is None:
        review = ""
    if review_rating is None:
        review_rating = ""
    #review_comment_raw = edit_content(review_content + '\n\n# ReviewBot\n\n' + review + '\n\n# ReviewRating\n\n' + review_rating + '\n\n' + pr_diff, editor)
    review_comment_raw = edit_content('# ReviewBot\n\n' + review + '\n\n# ReviewRating\n\n' + review_rating + '\n\n' + review_content + '\n\n' + pr_diff, editor)

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

def review_pr(user_gitee, repo_name, pull_id, group, editor, ai_model, filter):
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
    print_verbose(f"suggest_action: {suggest_action}")
    review_history_comment = review_history(user_gitee, group, repo_name, pull_id, pull_request)
    print_verbose(f"review_history: {review_history_comment}")
    pr_diff, review, review_rating = ai_review_impl(user_gitee, repo_name, pull_id, group, ai_model, review_history_comment, pull_request)
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
    print_verbose("start generate list of pending pr.")
    
    repos = {
        'src-openeuler': user_gitee.get_repos_by_sig(sig),
        'openeuler': user_gitee.get_openeuler_repos_by_sig(sig)
    }
    
    total = sum(len(r) for r in repos.values())
    for owner, repo_list in repos.items():
        for i, repo in enumerate(repo_list, 1):
            if print_progress(i, total, (i/total)*100):
                review_repo(user_gitee, owner, repo)

    PENDING_PRS.put(None)
    print_verbose("generate_pending_pr finished")
    PENDING_PRS.join() 
    print_verbose("PENDING_PRS join finished")
    return 0

def get_responsible_sigs(user_gitee, filter):
    """
    Get responsible sigs from config file
    """
    sigs = user_gitee.get_sigs()
    result = []
    for sig in sigs:
        if sig == "sig-minzuchess" or sig == "README.md":
            continue
        if sig in filter["sigs"]:
            print_verbose(f"sig {sig} is filtered".format(sig=sig))
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
        results = []
        total = 0

        def process_response(json_resp):
            if not json_resp or not json_resp.get("data"):
                return False
            for d in json_resp["data"]:
                repo_parts = d["repo"].split("/")
                results.append({
                    'owner': repo_parts[0],
                    'repo': repo_parts[1],
                    'number': d["link"].split("/")[-1]
                })
            return True

        # Get first page
        query_url = f"{quickissue_base_url}?sig={sig}&page=1&per_page=100&sort=created_at&state=open"
        json_resp = get_quickissue(query_url)
        if not process_response(json_resp):
            return results, total

        total = json_resp["total"]
        pages = math.ceil(total / json_resp["per_page"])

        # Get remaining pages
        for page in range(2, pages + 1):
            query_url = f"{quickissue_base_url}?sig={sig}&page={page}&per_page=100&sort=created_at&state=open"
            process_response(get_quickissue(query_url))

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

def review_sig(user_gitee, sig, editor, ai_model, filter):
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
    ai_review_thread = threading.Thread(target=ai_review, args=(user_gitee, ai_model))
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

    my_model = None
    no_ai = False

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

    print_verbose(f"editor option is: {editor['editor-option']}")

    if args.intelligent == "no":
        my_model = oe_review_ai_model("no")
    else:
        if not cf.has_section(args.intelligent):
            print("Section of config not found in config file.")
            return 1
        else:
            try:
                my_model = oe_review_ai_model(args.intelligent)
                my_model.model_name = cf.get(args.intelligent, 'model')
                my_model.api_key = cf.get(args.intelligent, 'api_key')
                my_model.base_url = cf.get(args.intelligent, 'base_url')
                my_model.method = cf.get(args.intelligent, 'method')
            except configparser.NoOptionError as e:
                print(f"Config option is missing: {e}")
                return 1

    if args.model:
        print_verbose(f"command line model is overriding config file")
        my_model.model_name = args.model

    filter = {}
    filter['labels'] = set(cf.get('filter', 'labels').split())
    filter['submitters'] = set(cf.get('filter', 'submitters').split())
    filter['repos'] = set(cf.get('filter', 'repos').split())
    filter['sigs'] = set(cf.get('filter', 'sigs').split())

    global g_chromadb_client
    global g_chromadb_collection
    g_chromadb_client = chromadb.PersistentClient(path=CHROMADB_DB_PATH)
    g_chromadb_collection = g_chromadb_client.get_or_create_collection(CHROMADB_COLLECTION_NAME)

    if args.active_user:
        if args.sig == "":
            sigs = get_responsible_sigs(user_gitee, filter)
            for sig in sigs:
                review_sig(user_gitee, sig, editor, my_model, filter)
        else:
            review_sig(user_gitee, args.sig, editor, my_model, filter)
    else:
        params = extract_params(args)
        if not params:
            return 1 
        group = params[0]
        repo_name = params[1]
        pull_id = params[2]
        review_pr(user_gitee, repo_name, pull_id, group, editor, my_model, filter)

    return 0

if __name__ == "__main__":
    sys.exit(main())

