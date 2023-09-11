#!/usr/bin/env python3
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
#
# ******************************************************************************/
"""
This modules containers methods to check upstream version info
"""
import os
import re
import shutil
import sys
import json
import subprocess
import time
from datetime import datetime
from urllib.parse import urljoin
import requests
from advisors import yaml2url

TIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def eprint(*args, **kwargs):
    """Helper for debug print"""
    print("DEBUG: ", *args, file=sys.stderr, **kwargs)


def get_resp(url, **kwargs):
    r"""Sends a GET request.

    :param url: URL for the new :class:`Request` object.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """
    try:
        resp = requests.get(url, **kwargs)
    except requests.RequestException as e:
        eprint("{url} > requests.get return error: {error}.".format(url=url, error=e))
        return ""

    return resp


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
        # age = datetime.now() - datetime.strptime(last_query["time_stamp"], TIME_FORMAT)
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
    result_list = {}
    if info.get("tag_pattern", "") != "" and info.get("tag_pattern", "") is not None:
        pattern_regex = re.compile(info["tag_pattern"])
        for tag in tags.keys():
            if pattern_regex.match(tag):
                new_tag = pattern_regex.sub("\\1", tag)
                result_list[new_tag] = tags[tag]

    elif info.get("tag_reorder", "") != "" and info.get("tag_reorder", "") is not None:
        pattern_regex = re.compile(info["tag_reorder"])
        for tag in tags.keys():
            if pattern_regex.match(tag):
                new_tag = pattern_regex.sub(info["tag_neworder"], tag)
                result_list[new_tag] = tags[tag]

    elif info.get("tag_prefix", "") != "" and info.get("tag_prefix", "") is not None:
        prefix_regex = re.compile(info["tag_prefix"])
        for tag in tags.keys():
            if prefix_regex.match(tag):
                new_tag = prefix_regex.sub("", tag)
                result_list[new_tag] = tags[tag]
    else:
        result_list = tags

    result = {}
    if info.get("separator", ".") != "." and info.get("separator", "."):
        separator_regex = re.compile(info["separator"])
        for tag in result_list.keys():
            result[separator_regex.sub(".", tag)] = result_list[tag]
    # Xinwei used to mis-spell 'separator'.
    # Followings are kept for compatability until all yaml files are fixed.
    elif info.get("seperator", ".") != "." and info.get("seperator", "."):
        separator_regex = re.compile(info["seperator"])
        for tag in result_list.keys():
            result[separator_regex.sub(".", tag)] = result_list[tag]
    else:
        result = result_list
    return result


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
    tags = {}
    eprint("{repo} > Using hg raw-tags".format(repo=info["src_repo"] + "/raw-tags"))
    resp = load_last_query_result(info)
    if resp == "":
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'
        }
        url = yaml2url.yaml2url(info)
        resp = get_resp(url, headers=headers)
        if not resp:
            return tags

        resp = resp.text
        need_trick, url, cookies = dirty_redirect_tricks(url, resp)
        if need_trick:
            # I dont want to introduce another dependency on requests
            # but urllib handling cookie is outragely complex
            c_dict = {}
            for cookie in cookies:
                key, value = cookie.split('=')
                c_dict[key] = value

            resp = get_resp(url, headers=headers, cookies=c_dict)
            if not resp:
                return tags

            resp = resp.text
    last_query = {"time_stamp": datetime.now(), "raw_data": resp}
    info["last_query"] = last_query

    for line in resp.splitlines():
        tags[line.split()[0]] = None
    if clean_tag:
        tags = clean_tags(tags, info)
    return tags


def check_hg(info, clean_tag=True):
    """
    Check hg version info via json
    """
    result_list = {}
    eprint("{repo} > Using hg json-tags".format(repo=info["src_repo"] + "/json-tags"))
    resp = load_last_query_result(info)
    if resp == "":
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'
        }
        url = yaml2url.yaml2url(info)
        resp = get_resp(url, headers=headers)
        if not resp:
            return result_list

        resp = resp.text
        need_trick, url, cookies = dirty_redirect_tricks(url, resp)
        if need_trick:
            # I dont want to introduce another dependency on requests
            # but urllib handling cookie is outragely complex
            c_dict = {}
            for cookie in cookies:
                key, value = cookie.split('=')
                c_dict[key] = value

            resp = get_resp(url, headers=headers, cookies=c_dict)
            if not resp:
                return result_list

            resp = resp.text
    last_query = {"time_stamp": datetime.now(), "raw_data": resp}
    info["last_query"] = last_query
    # try and except ?
    tags_json = json.loads(resp)
    sort_tags = tags_json["tags"]

    sort_tags.sort(reverse=True, key=lambda x: x['date'][0])
    for tag in sort_tags:
        tag_date = datetime.fromtimestamp(tag['date'][0])
        result_list[tag['tag']] = tag_date

    if clean_tag:
        result_list = clean_tags(result_list, info)
    return result_list


def check_metacpan(info, clean_tag=True):
    """
    Check perl module version info via metacpan api
    """
    tags = {}
    resp = load_last_query_result(info)
    if resp == "":
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'
        }
        url = yaml2url.yaml2url(info)
        eprint(url)
        resp = get_resp(url, headers=headers)
        if not resp:
            return tags

        resp = resp.text

    last_query = {"time_stamp": datetime.now(), "raw_data": resp}
    info["last_query"] = last_query

    tags = []
    tag = None
    tags_json = json.loads(resp)
    if "version" in tags_json:
        tag = tags_json["version"]
    elif "version" in tags.json["metadata"]:
        tag = tags_json["metadata"]["version"]
    elif "version_numified" in tags_json:
        tag = str(tags_json["version_numified"])
    if tag:
        tag = tag.lstrip('0').rstrip('0')
        tags.append(tag)

    if clean_tag:
        tags = clean_tags(tags, info)
    return tags


def check_pypi(info, clean_tag=True):
    """
    Check python module version info via pypi api
    """
    resp = load_last_query_result(info)
    tags = {}
    if resp == "":
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'
        }
        url = yaml2url.yaml2url(info)
        resp = get_resp(url, headers=headers)
        if not resp:
            return tags

    data = resp.json()
    release_date = data["releases"]
    for tag, value in release_date.items():
        if value:
            upload_time = value[0].get('upload_time')
            upload_time = upload_time.split('T')[0]
            tags[tag] = datetime.strptime(upload_time, "%Y-%m-%d")
        else:
            tags[tag] = None
    if not tags:
        eprint("{repo} > No Response or JSON parse failed".format(repo=info["src_repo"]))
        return tags
    if clean_tag:
        tags = clean_tags(tags, info)
    return tags


def check_rubygem(info, clean_tag=True):
    """
    Check ruby module version info via rubygem api
    """
    resp = load_last_query_result(info)
    tags = {}
    if resp == "":
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'
        }
        url = yaml2url.yaml2url(info)
        resp = get_resp(url, headers=headers)
        if not resp:
            return tags

    data = resp.json()
    for release in data:
        built_at = release["built_at"]
        built_at = built_at.split('T')[0]
        tag = release["number"]
        tags[tag] = datetime.strptime(built_at, "%Y-%m-%d")
    if not tags:
        eprint("{repo} > No Response or JSON parse failed".format(repo=info["src_repo"]))
        return ""
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


def __get_git_tag_list(git_repo):
    """
    Get tag list
    """
    tag_date = {}
    cmd_list = ["git", "tag", '-l']
    resp = __check_subprocess(cmd_list)
    for version in resp.splitlines():
        if version == '-' or version == 'CHANGES':
            continue
        cmd_list = ['git', 'log', '-1', '--format=%ai', version]
        date_resp = __check_subprocess(cmd_list)
        if not date_resp:
            tag_date[version] = None
        else:
            date = datetime.strptime(date_resp.split(" ")[0], "%Y-%m-%d")
            tag_date[version] = date
    return tag_date


def __check_git_helper(repo_url):
    """
    Helper to start git command
    """
    tags = {}
    if os.path.isdir("git"):
        os.chdir("git")
    else:
        os.mkdir("git")
        os.chdir("git")
    if repo_url[-1] == '/':
        repo_url = repo_url[0:-1]
    if repo_url.endswith(".git"):
        git_repo_list = os.path.basename(repo_url).split('.')[0:-1]
        git_repo = ".".join(git_repo_list)
    else:
        git_repo_list = os.path.basename(repo_url)
        git_repo = git_repo_list

    zip_file = git_repo + ".zip"
    if os.path.isfile(zip_file):
        shutil.unpack_archive(zip_file, git_repo)
        os.remove(zip_file)
    if os.path.isdir(git_repo):
        os.chdir(git_repo)
        eprint("INFO:start to git pull", repo_url)
        cmd_list = ["git", "pull", repo_url]
        __check_subprocess(cmd_list)
        os.chdir("..")
    else:
        cnt = 0
        while True:
            eprint("INFO:start to git clone", repo_url)
            cmd_list = ["git", "clone", repo_url]
            __check_subprocess(cmd_list)
            if os.path.isdir(git_repo):
                break
            elif cnt < 10:
                time.sleep(1)
                cnt = cnt + 1
                eprint("INFO:try to git clone repo {} cnt = {}".format(repo_url, cnt))
                continue
            else:
                eprint("ERROR:git clone {} failed".format(repo_url))
                break
    try:
        os.chdir(git_repo)
    except FileNotFoundError as e:
        eprint("ERROR: dir not find", e)
        os.chdir("..")
        return tags
    tags = __get_git_tag_list(git_repo)
    os.chdir("..")
    shutil.make_archive(git_repo, 'zip', git_repo)
    shutil.rmtree(git_repo)
    os.chdir("..")
    return tags


def __svn_resp_to_tags(resp):
    """
    Helper to convert svn response to tags
    """
    tags = {}
    for line in resp.splitlines():
        if 'Redirecting' in line:
            continue
        items = line.split()
        create_date = items[2:5]
        tag = items[5]
        tag = tag[:-1]
        try:
            date = datetime.strptime(",".join(create_date), "%b,%d,%Y")
            tags[tag] = date
        except ValueError:
            tags[tag]=None

    return tags


def __git_resp_to_tags(tags):
    """
    Helpers to convert git response to tags
    """
    return tags


def check_git(info, clean_tag=True):
    """
    Check version info via git command
    """
    resp = load_last_query_result(info)
    if resp == "":
        url = yaml2url.yaml2url(info)
        tag_data = __check_git_helper(url)
        last_query = {"time_stamp": datetime.now(), "raw_data": tag_data}
        info["last_query"] = last_query
    if tag_data:
        tags = clean_tags(tag_data, info)
        return tags
    else:
        return None


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
        last_query = {"time_stamp": datetime.now(), "raw_data": resp}
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
    tags = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'
    }
    url = yaml2url.yaml2url(info)
    eprint("{repo} > List ftp directory".format(repo=url))
    resp = get_resp(url, headers=headers)
    if not resp:
        return tags
    resp = resp.text
    re_pattern = re.compile("href=\"(.*)\">(\\1)</a>")

    for line in resp.splitlines():
        result = re_pattern.search(line)
        if result:
            tags[result[1]] = None
    if clean_tag:
        tags = clean_tags(tags, info)
    return tags


def check_ftp(info, clean_tag=True):
    """
    Check version info via compare ftp release tar file
    """
    tags = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'
    }
    url = yaml2url.yaml2url(info)
    eprint("{repo} > List ftp directory".format(repo=url))

    resp = get_resp(url, headers=headers)
    if not resp:
        return tags

    resp = resp.text

    re_pattern = re.compile("href=\"(.*)\">(.*)</a>")

    for line in resp.splitlines():
        result = re_pattern.search(line)
        if result:
            tags[result[1]] = None
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
        last_query = {"time_stamp": datetime.now(), "raw_data": resp}
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
        last_query = {"time_stamp": datetime.now(), "raw_data": resp}
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
    tags = {}
    if resp == "":
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'
        }
        url = yaml2url.yaml2url(info)
        eprint("check_sourceforge, url = " + url)
        resp = get_resp(url, headers=headers)
        if not resp:
            return tags

    data = resp.text
    lines = data.splitlines()
    re_pattern = re.compile("<tr title=\"(.*)\" class=\"folder \">")
    for line in lines:
        result = re_pattern.search(line)
        if result:
            tags[result[1]] = None
    if clean_tag:
        tags = clean_tags(tags, info)
    return tags


if __name__ == "__main__":
    pass
