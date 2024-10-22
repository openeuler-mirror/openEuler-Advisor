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

def generate_review_from_ollama(pr_content, prompt, model="llama3.1:70b"):
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
    pars.add_argument("-n", "--repo", type=str, help="Repository name that include group")
    pars.add_argument("-p", "--pull", type=str, help="Number ID of Pull Request")
    pars.add_argument("-u", "--url", type=str, help="URL of Pull Request")
    pars.add_argument("-m", "--model", type=str, help="Model of selection to generate review")
    pars.add_argument("-w", "--workdir", type=str, default=os.getcwd(),
                      help="Work directory.Default is current directory.")
    pars.add_argument("-e", "--editor", type=str, default="/opt/homebrew/bin/nvim",
                      help="Editor of choice to edit content, default to nvim")
    pars.add_argument("-c", "--clean", help="Clean environment", action="store_true")
    pars.add_argument("-l", "--local", help="Using local checklist", action="store_true")

    return pars.parse_args()
    
def edit_content(text, editor):
    fd, path = tempfile.mkstemp(suffix=".tmp", prefix="oe_review")
    with os.fdopen(fd, 'w') as tmp:
        tmp.write(text)
        tmp.flush()
        subprocess.call([editor, path])
        text_new = open(path).read()
        return text_new
    
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
    pr_diff = user_gitee.get_diff(repo_name, pull_id, group)
    if not pr_diff:
        print("Failed to get PR:%s of repository:%s/%s, make sure the PR is exist." % (pull_id, group, repo_name))
        return 1

    review = generate_review_from_ollama(pr_diff, OE_REVIEW_PR_PROMPT)
    review_comment = edit_content(review + '\n\n' + pr_diff, args.editor)

    user_gitee.create_pr_comment(repo_name, pull_id, review_comment, group)

    print("push review list finish.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

