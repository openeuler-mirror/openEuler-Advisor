#!/usr/bin/env python3
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
This modules containers methods to check upstream version info
"""
import re
import sys
import json
import subprocess
from datetime import datetime
from urllib.parse import urljoin
import requests

from advisors import yaml2url

TIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def eprint(*args, **kwargs):
    """Helper for debug print"""
    print("DEBUG: ", *args, file=sys.stderr, **kwargs)


def load_last_query_result(info, force_reload=False):
    """
    If there's last_query stored in yaml, load it
    """
    if force_reload:
        last_query = info.pop("last_query")
        eprint("{repo} > Force reload".format(repo=info["src_repo"]))
        return ""

    if "last_query" in info.keys():
        last_query = info.pop("last_query")
        #age = datetime.now() - datetime.strptime(last_query["time_stamp"], TIME_FORMAT)
        age = datetime.now() - last_query["time_stamp"].replace(tzinfo=None)
        if age.days < 7:
            eprint("{repo} > Reuse Last Query".format(repo=info["src_repo"]))
            return last_query["raw_data"]

        eprint("{repo} > Last Query Too Old.".format(repo=info["src_repo"]))
        return ""

    return ""


def clean_tags(tags, info):
    """
    Clean up tags according to setting
    """
    if info.get("tag_pattern", "") != "" and info.get("tag_pattern", "") is not None:
        pattern_regex = re.compile(info["tag_pattern"])
        result_list = [pattern_regex.sub("\\1", x) for x in tags]
    elif info.get("tag_reorder", "") != "" and info.get("tag_reorder", "") is not None:
        pattern_regex = re.compile(info["tag_reorder"])
        result_list = [pattern_regex.sub(info["tag_neworder"], x) for x in tags]
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

    result_list = [x for x in result_list if x and x[0].isdigit()]

    return result_list


def dirty_redirect_tricks(url, resp):
    """
    Helper on redict tricks of some site
    """
    cookie = set()
    href = ""
    need_trick = False
    for line in resp.splitlines():
        line = line.strip()
        if line.startswith("Redirecting"):
            eprint("Redirecting with document.cookie")
            need_trick = True
        search_result = re.search(r"document\.cookie=\"(.*)\";", line)
        if search_result:
            cookie = cookie | set(search_result.group(1).split(';'))
        search_result = re.search(r"document\.location\.href=\"(.*)\";", line)
        if search_result:
            href = search_result.group(1)
    new_url = urljoin(url, href)
    if "" in cookie:
        cookie.remove("")
    return need_trick, new_url, list(cookie)


def check_hg_raw(info, clean_tag=True):
    """
    Check hg version info via raw-tags
    """
    eprint("{repo} > Using hg raw-tags".format(repo=info["src_repo"]+"/raw-tags"))
    resp = load_last_query_result(info)
    if resp == "":
        headers = {
            'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64)'
            }
        url = yaml2url.yaml2url(info)
        resp = requests.get(url, headers=headers)
        resp = resp.text
        need_trick, url, cookies = dirty_redirect_tricks(url, resp)
        if need_trick:
            # I dont want to introduce another dependency on requests
            # but urllib handling cookie is outragely complex
            c_dict = {}
            for cookie in cookies:
                key, value = cookie.split('=')
                c_dict[key] = value
            resp = requests.get(url, headers=headers, cookies=c_dict)
            resp = resp.text

    last_query = {}
    last_query["time_stamp"] = datetime.now()
    last_query["raw_data"] = resp
    info["last_query"] = last_query
    tags = []
    for line in resp.splitlines():
        tags.append(line.split()[0])
    if clean_tag:
        tags = clean_tags(tags, info)
    return tags


def check_hg(info, clean_tag=True):
    """
    Check hg version info via json
    """
    eprint("{repo} > Using hg json-tags".format(repo=info["src_repo"]+"/json-tags"))
    resp = load_last_query_result(info)
    if resp == "":
        headers = {
            'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64)'
            }
        url = yaml2url.yaml2url(info)
        resp = requests.get(url, headers=headers)
        resp = resp.text
        need_trick, url, cookies = dirty_redirect_tricks(url, resp)
        if need_trick:
            # I dont want to introduce another dependency on requests
            # but urllib handling cookie is outragely complex
            c_dict = {}
            for cookie in cookies:
                key, value = cookie.split('=')
                c_dict[key] = value
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
    if clean_tag:
        result_list = clean_tags(result_list, info)
    return result_list


def check_metacpan(info, clean_tag=True):
    """
    Check perl module version info via metacpan api
    """
    resp = load_last_query_result(info)
    if resp == "":
        headers = {
            'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64)'
            }
        url = yaml2url.yaml2url(info)
        resp = requests.get(url, headers=headers)
        resp = resp.text

    tags = []
    tag_list = resp.splitlines()
    condition = "value=\"/release"

    len_tag_list = len(tag_list) - 1
    for index in range(len_tag_list):
        if condition in tag_list[index]:
            tag = tag_list[index + 1]
            index = index + 1
            if 'DEV' in tag:
                continue
            tag = tag.lstrip()
            tag = tag.rstrip()
            tags.append(tag)

    if not tags:
        eprint("{repo} found unsorted on cpan.metacpan.org".format(repo=info["src_repo"]))
        sys.exit(1)
    last_query = {}
    last_query["time_stamp"] = datetime.now()
    last_query["raw_data"] = resp
    info["last_query"] = last_query
    if clean_tag:
        tags = clean_tags(tags, info)
    return tags


def check_pypi(info, clean_tag=True):
    """
    Check python module version info via pypi api
    """
    resp = load_last_query_result(info)
    tags = []
    if resp == "":
        headers = {
            'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64)'
            }
        url = yaml2url.yaml2url(info)
        resp = requests.get(url, headers=headers)

    data = resp.json()
    for key in data["releases"].keys():
        tags.append(key)
    if not tags:
        eprint("{repo} > No Response or JSON parse failed".format(repo=info["src_repo"]))
        sys.exit(1)
    if clean_tag:
        tags = clean_tags(tags, info)
    return tags


def check_rubygem(info, clean_tag=True):
    """
    Check ruby module version info via rubygem api
    """
    resp = load_last_query_result(info)
    tags = []
    if resp == "":
        headers = {
            'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64)'
            }
        url = yaml2url.yaml2url(info)
        resp = requests.get(url, headers=headers)

    data = resp.json()
    for release in data:
        tags.append(release["number"])
    if not tags:
        eprint("{repo} > No Response or JSON parse failed".format(repo=info["src_repo"]))
        sys.exit(1)
    if clean_tag:
        tags = clean_tags(tags, info)
    return tags


def __check_subprocess(cmd_list):
    """
    Helper to start and check subprocess result
    """
    subp = subprocess.Popen(cmd_list, stdout=subprocess.PIPE)
    resp = subp.stdout.read().decode("utf-8")
    if subp.wait() != 0:
        eprint("{cmd} > encount errors".format(cmd=" ".join(cmd_list)))
    return resp


def __check_svn_helper(repo_url):
    """
    Helper to start svn command
    """
    eprint("{repo} > Using svn ls".format(repo=repo_url))
    cmd_list = ["/usr/bin/svn", "ls", "-v", repo_url]
    return __check_subprocess(cmd_list)


def __check_git_helper(repo_url):
    """
    Helper to start git command
    """
    eprint("{repo} > Using git ls-remote".format(repo=repo_url))
    cmd_list = ["git", "ls-remote", "--tags", repo_url]
    return __check_subprocess(cmd_list)


def __svn_resp_to_tags(resp):
    """
    Helper to convert svn response to tags
    """
    tags = []
    for line in resp.splitlines():
        items = line.split()
        for item in items:
            if item[-1] == "/":
                tags.append(item[:-1])
                break
    return tags


def __git_resp_to_tags(resp):
    """
    Helpers to convert git response to tags
    """
    tags = []
    pattern = re.compile(r"^([^ \t]*)[ \t]*refs\/tags\/([^ \t]*)")
    for line in resp.splitlines():
        match_result = pattern.match(line)
        if match_result:
            tag = match_result.group(2)
            if not tag.endswith("^{}"):
                tags.append(tag)
    return tags


def check_git(info, clean_tag=True):
    """
    Check version info via git command
    """
    resp = load_last_query_result(info)
    if resp == "":
        url = yaml2url.yaml2url(info)
        resp = __check_git_helper(url)
        last_query = {}
        last_query["time_stamp"] = datetime.now()
        last_query["raw_data"] = resp
        info["last_query"] = last_query

    tags = __git_resp_to_tags(resp)
    if clean_tag:
        tags = clean_tags(tags, info)
    return tags


def check_github(info, clean_tag=True):
    """
    Check version info via github api
    """
    resp = load_last_query_result(info)
    if info.get("query_type", "git-ls") != "git-ls":
        resp = ""

    repo_url = yaml2url.yaml2url(info)

    if resp == "":
        resp = __check_git_helper(repo_url)
        last_query = {}
        last_query["time_stamp"] = datetime.now()
        last_query["raw_data"] = resp
        info["last_query"] = last_query
        info["query_type"] = "git-ls"

    tags = __git_resp_to_tags(resp)
    if clean_tag:
        tags = clean_tags(tags, info)
    return tags


def check_gnu_ftp(info, clean_tag=True):
    """
    Check version info via compare ftp release tar file for gnu
    """
    headers = {
        'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64)'
        }
    url = yaml2url.yaml2url(info)
    eprint("{repo} > List ftp directory".format(repo=url))
    resp = requests.get(url, headers=headers)
    resp = resp.text
    re_pattern = re.compile("href=\"(.*)\">(\\1)</a>")
    tags = []
    for line in resp.splitlines():
        result = re_pattern.search(line)
        if result:
            tags.append(result[1])
    if clean_tag:
        tags = clean_tags(tags, info)
    return tags


def check_ftp(info, clean_tag=True):
    """
    Check version info via compare ftp release tar file
    """
    headers = {
        'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64)'
        }
    url = yaml2url.yaml2url(info)
    eprint("{repo} > List ftp directory".format(repo=url))
    resp = requests.get(url, headers=headers)
    resp = resp.text
    re_pattern = re.compile("href=\"(.*)\">(.*)</a>")
    tags = []
    for line in resp.splitlines():
        result = re_pattern.search(line)
        if result:
            tags.append(result[1])
    if clean_tag:
        tags = clean_tags(tags, info)
    return tags


def check_gnome(info, clean_tag=True):
    """
    Check version info via gitlab.gnome.org api
    """
    resp = load_last_query_result(info)
    repo_url = yaml2url.yaml2url(info)

    if resp == "":
        resp = __check_git_helper(repo_url)
        last_query = {}
        last_query["time_stamp"] = datetime.now()
        last_query["raw_data"] = resp
        info["last_query"] = last_query

    tags = __git_resp_to_tags(resp)
    if clean_tag:
        tags = clean_tags(tags, info)
    return tags


def check_gitee(info, clean_tag=True):
    """
    Check version info via gitee
    """
    resp = load_last_query_result(info)
    repo_url = yaml2url.yaml2url(info)
    if resp == "":
        resp = __check_git_helper(repo_url)
        last_query = {}
        last_query["time_stamp"] = datetime.now()
        last_query["raw_data"] = resp
        info["last_query"] = last_query

    tags = __git_resp_to_tags(resp)
    if clean_tag:
        tags = clean_tags(tags, info)
    return tags


def check_svn(info, clean_tag=True):
    """
    Check version info via svn
    """
    resp = load_last_query_result(info)
    repo_url = yaml2url.yaml2url(info)
    if resp == "":
        resp = __check_svn_helper(repo_url)
        last_query = {}
        last_query["time_stamp"] = datetime.now()
        last_query["raw_data"] = resp
        info["last_query"] = last_query

    tags = __svn_resp_to_tags(resp)
    if clean_tag:
        tags = clean_tags(tags, info)
    return tags


def check_sourceforge(info, clean_tag=True):
    """
    Check python module version info via sourceforge url
    """
    resp = load_last_query_result(info)
    tags = []
    if resp == "":
        headers = {
            'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64)'
        }
        url = yaml2url.yaml2url(info)
        print("check_sourceforge, url = " + url)
        try:
            resp = requests.get(url, headers=headers)
        except ConnectionError as err:
            print("ERROR: connect {} error.".format(url), err)
            return ''

    data = resp.text
    lines = data.splitlines()
    filter_condition = "\"download_url\": \"" + url
    for line in lines:
        if filter_condition in line:
            tag_infos = line.split(',')
            for tag_info in tag_infos:
                if filter_condition in tag_info:
                    tag = tag_info.strip()
                    tag = tag.replace(filter_condition, "")
                    tag = tag.strip("/download\"")
                    tags.append(tag)
    if clean_tag:
        tags = clean_tags(tags, info)
    return tags


if __name__ == "__main__":
    pass
