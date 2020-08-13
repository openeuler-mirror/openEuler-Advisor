#!/usr/bin/python3

import http.cookiejar
import urllib.request
import re
import yaml
import json
import sys
import subprocess
import requests

from urllib.parse import urljoin
from datetime import datetime

time_format = "%Y-%m-%dT%H:%M:%S%z"

def eprint(*args, **kwargs):
    print("DEBUG: ", *args, file=sys.stderr, **kwargs)

def load_last_query_result(info, force_reload=False):
    if force_reload:
        last_query = info.pop("last_query")
        eprint("{repo} > Force reload".format(repo=info["src_repo"]))
        return ""
    else:
        if "last_query" in info.keys():
            last_query = info.pop("last_query")
            #age = datetime.now() - datetime.strptime(last_query["time_stamp"], time_format)
            age = datetime.now() - last_query["time_stamp"].replace(tzinfo=None)
            if age.days < 7:
                eprint("{repo} > Reuse Last Query".format(repo=info["src_repo"]))
                return last_query["raw_data"]
            else:
                eprint("{repo} > Last Query Too Old.".format(repo=info["src_repo"]))
                return ""
        else:
            return ""


def clean_tags(tags, info):
    if info.get("tag_pattern", "") != "" and info.get("tag_pattern", "") is not None:
        pattern_regex = re.compile(info["tag_pattern"])
        result_list = [pattern_regex.sub("\\1", x) for x in tags]
    elif info.get("tag_prefix", "") != "" and info.get("tag_prefix", "") is not None:
        prefix_regex = re.compile(info["tag_prefix"])
        result_list = [prefix_regex.sub("", x) for x in tags]
    else:
        result_list = tags

    if info.get("separator", ".") != "." and info.get("separator", ".") is not None:
        separator_regex = re.compile(info["separator"])
        result_list = [separator_regex.sub(".", x) for x in result_list]
    
    # Xinwei used to mis-spell 'separator'. 
    # Followings are kept for compatability until all yaml files are fixed.
    if info.get("seperator", ".") != "." and info.get("seperator", ".") is not None:
        separator_regex = re.compile(info["seperator"])
        result_list = [separator_regex.sub(".", x) for x in result_list]

    result_list = [x for x in result_list if x[0].isdigit()]
    
    return result_list


def dirty_redirect_tricks(url, resp):
    cookie = set()
    href = ""
    need_trick = False
    for line in resp.splitlines():
        line = line.strip()
        if line.startswith("Redirecting"):
            eprint("Redirecting with document.cookie")
            need_trick = True
        m = re.search(r"document\.cookie=\"(.*)\";", line)
        if m:
            cookie = cookie | set(m.group(1).split(';'))
        m = re.search(r"document\.location\.href=\"(.*)\";", line)
        if m:
            href = m.group(1)
    new_url = urljoin(url, href)
    if "" in cookie: cookie.remove("") 
    return need_trick, new_url, list(cookie)


def check_hg(info):
    resp = load_last_query_result(info)
    if resp == "":
        headers = {
                'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64)'
                }
        url = urljoin(info["src_repo"] + "/", "json-tags")
        resp = requests.get(url, headers=headers)
        resp = resp.text
        need_trick, url, cookie = dirty_redirect_tricks(url, resp)
        if need_trick:
            # I dont want to introduce another dependency on requests
            # but urllib handling cookie is outragely complex
            c_dict = {}
            for c in cookie:
                k, v = c.split('=')
                c_dict[k] = v
            resp = requests.get(url, headers=headers, cookies=c_dict)
            resp = resp.text

    last_query = {}
    last_query["time_stamp"] = datetime.now()
    last_query["raw_data"] = resp
    info["last_query"] = last_query
    # try and except ?
    tags_json = json.loads(resp)
    sort_tags = tags_json["tags"]
    sort_tags.sort(reverse=True, key=lambda x: x['date'][0])
    result_list = [tag['tag'] for tag in sort_tags]
    result_list = clean_tags(result_list, info)
    return result_list

def check_metacpan(info):
    resp = load_last_query_result(info)
    if resp == "":
        headers = {
                'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64)'
                }
        url = urljoin("https://fastapi.metacpan.org/release/", info["src_repo"])
        resp = requests.get(url, headers=headers)
        resp = resp.text

    tags = []
    result_json = json.loads(resp)
    if result_json != {}:
        if "version" not in result_json.keys():
            eprint("{repo} > ERROR FOUND".format(repo=info["src_repo"]))
            sys.exit(1)
        else:
            tags.append(result_json["version"])
    else:
        eprint("{repo} found unsorted on cpan.metacpan.org".format(repo=info["src_repo"]))
        sys.exit(1)

    last_query = {}
    last_query["time_stamp"] = datetime.now()
    last_query["raw_data"] = resp
    info["last_query"] = last_query
    tags = clean_tags(tags, info)
    return tags

def check_pypi(info):
    resp = load_last_query_result(info)
    tags = []
    if resp == "":
        headers = {
                'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64)'
                }
        url = urljoin("https://pypi.org/pypi/", info["src_repo"] + "/json")
        resp = requests.get(url, headers=headers)
        resp = resp.text

    result_json = json.loads(resp)
    if result_json != {}:
        tags.append(result_json["info"]["version"])
    else:
        eprint("{repo} > No Response or JSON parse failed".format(repo=info["src_repo"]))
        sys.exit(1)
    return tags

def __check_subprocess(cmd_list):
    subp = subprocess.Popen(cmd_list, stdout=subprocess.PIPE)
    resp = subp.stdout.read().decode("utf-8")
    if subp.wait() != 0:
        eprint("{cmd} > encount errors".format(cmd=" ".join(cmd_list)))
        sys.exit(1)
    return resp

def __check_svn_helper(repo_url):
    eprint("{repo} > Using svn ls".format(repo=repo_url))
    cmd_list = ["/usr/bin/svn", "ls", "-v", repo_url]
    return __check_subprocess(cmd_list)

def __check_git_helper(repo_url):
    eprint("{repo} > Using git ls-remote".format(repo=repo_url))
    cmd_list = ["git", "ls-remote", "--tags", repo_url]
    return __check_subprocess(cmd_list)

def __svn_resp_to_tags(resp):
    tags = []
    for line in resp.splitlines():
        items = line.split()
        for item in items:
            if item[-1] == "/":
                tags.append(item[:-1])
                break
    return tags

def __git_resp_to_tags(resp):
    tags = []
    pattern = re.compile(r"^([^ \t]*)[ \t]*refs\/tags\/([^ \t]*)")
    for line in resp.splitlines():
        m = pattern.match(line)
        if m:
            tag = m.group(2)
            if not tag.endswith("^{}"):
                tags.append(tag)
    return tags

def check_git (info):
    resp = load_last_query_result(info)
    if resp == "":
        resp = __check_git_helper(info["src_repo"])
        last_query={}
        last_query["time_stamp"] = datetime.now()
        last_query["raw_data"] = resp
        info["last_query"] = last_query

    tags = __git_resp_to_tags(resp)
    tags = clean_tags(tags, info)

    return tags

def check_github(info):
    resp = load_last_query_result(info)
    if info.get("query_type", "git-ls") != "git-ls":
        resp = ""

    repo_url = "https://github.com/" + info["src_repo"] + ".git"

    if resp == "":
        resp = __check_git_helper(repo_url)
        last_query = {}
        last_query["time_stamp"] = datetime.now()
        last_query["raw_data"] = resp
        info["last_query"] = last_query
        info["query_type"] = "git-ls"

    tags = __git_resp_to_tags(resp)
    tags = clean_tags(tags, info)
    return tags

def check_gnome(info):
    resp = load_last_query_result(info)
    src_repos = info["src_repo"].split("/")
    if len(src_repos) == 1:
        repo_url = "https://gitlab.gnome.org/GNOME/" + info["src_repo"] + ".git"
    else:
        repo_url = "https://gitlab.gnome.org/" + info["src_repo"] + ".git"

    if resp == "":
        resp = __check_git_helper(repo_url)
        last_query={}
        last_query["time_stamp"] = datetime.now()
        last_query["raw_data"] = resp
        info["last_query"] = last_query

    tags = __git_resp_to_tags(resp)
    tags = clean_tags(tags, info)
    return tags

def check_gitee(info):
    resp = load_last_query_result(info)
    repo_url = "https://gitee.com/" + info["src_repo"]
    if resp == "":
        resp = __check_git_helper(repo_url)
        last_query = {}
        last_query["time_stamp"] = datetime.now()
        last_query["raw_data"] = resp
        info["last_query"] = last_query

    tags = __git_resp_to_tags(resp)
    tags = clean_tags(tags, info)
    return tags

def check_svn(info):
    resp = load_last_query_result(info)
    repo_url = info["src_repo"] + "/tags"
    if resp == "":
        resp = __check_svn_helper(repo_url)
        last_query = {}
        last_query["time_stamp"] = datetime.now()
        last_query["raw_data"] = resp
        info["last_query"] = last_query

    tags = __svn_resp_to_tags(resp)
    tags = clean_tags(tags, info)
    return tags


if __name__ == "__main__":
    pass

