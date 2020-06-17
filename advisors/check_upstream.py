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

    if info.get("tag_pattern", "") != "":
        pattern_regex = re.compile(info["tag_pattern"])
        result_list = [pattern_regex.sub("\\1", x) for x in tags]
    elif info.get("tag_prefix", "") != "":
        prefix_regex = re.compile(info["tag_prefix"])
        result_list = [prefix_regex.sub("", x) for x in tags]
    else:
        result_list = tags

    if info.get("seperator", ".") != ".":
        seperator_regex = re.compile(info["seperator"])
        result_list = [seperator_regex.sub(".", x) for x in result_list]

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
        m = re.search("document\.cookie=\"(.*)\";", line)
        if m:
            cookie = cookie | set(m.group(1).split(';'))
        m = re.search("document\.location\.href=\"(.*)\";", line)
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
        need_trick, url, cookie = dirty_redirect_tricks(url, resp.text)
        if need_trick:
            # I dont want to introduce another dependency on requests
            # but urllib handling cookie is outragely complex
            c_dict = {}
            for c in cookie:
                k, v = c.split('=')
                c_dict[k] = v
            resp = requests.get(url, headers=headers, cookies=c_dict)

    last_query = {}
    last_query["time_stamp"] = datetime.now()
    last_query["raw_data"] = resp.text
    info["last_query"] = last_query
    # try and except ?
    tags_json = json.loads(resp.text)
    sort_tags = tags_json["tags"]
    sort_tags.sort(reverse=True, key=lambda x: x['date'][0])
    result_list = [tag['tag'] for tag in sort_tags]
    result_list = clean_tags(result_list, info)
    return result_list

def check_github(info):
    resp = load_last_query_result(info)
    if info.get("query_type", "git-ls") != "git-ls":
        resp = ""
    cmd_list = ["git", "ls-remote", "--tags", "https://github.com/" + info["src_repo"] + ".git"]
    if resp == "":
        eprint("{repo} > Using git ls-remote".format(repo=info["src_repo"]))
        subp = subprocess.Popen(cmd_list, stdout=subprocess.PIPE)
        resp = subp.stdout.read().decode("utf-8")
        if subp.wait() != 0:
            eprint("{repo} > git ls-remote encount errors".format(repo=info["src_repo"]))
            sys.exit(1)

        last_query = {}
        last_query["time_stamp"] = datetime.now()
        last_query["raw_data"] = resp
        info["last_query"] = last_query
        info["query_type"] = "git-ls"

    tags = []
    pattern = re.compile("^([^ \t]*)[ \t]*refs\/tags\/([^ \t]*)")
    for line in resp.splitlines():
        m = pattern.match(line)
        if m:
            tags.append(m.group(2))
    tags = clean_tags(tags, info)
    return tags

if __name__ == "__main__":
    pass
"""
def compare_tags (a, b)
	arr_a = a.split(".")
	arr_b = b.split(".")
	len = [arr_a.length, arr_b.length].min
	idx = 0
	while idx < len do
		res1 = arr_a[idx].to_i <=> arr_b[idx].to_i
		return res1 if res1 != 0
		res2 = arr_a[idx].length <=> arr_b[idx].length
		return -res2 if res2 != 0
		res3 = arr_a[idx][-1].to_i <=> arr_b[idx][-1].to_i
		return res3 if res3 != 0
		idx = idx + 1
	end
	return arr_a.length <=> arr_b.length
end

def sort_tags (tags)
	tags.sort! { |a, b|
		compare_tags(a,b)
	}
	return tags
end


"""
