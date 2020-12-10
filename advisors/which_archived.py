#!/usr/bin/python3
#encoding: utf-8
#******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EI
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FO
# PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************/
"""
@author: smileknife
@desc: check archived project in upstream community
@date: 2020/10/1
@notice: this tool check websites in 'helper/community_archived.yaml',
user needs to configure first before running.
step1: copy helper/community_archived.yaml to ~/.community_archived.yaml
step2: edit ~/.community_archived.yaml
"""
import sys
import os
import json
import logging
import argparse
import signal
import urllib.request
import urllib.error
import requests
import yaml
import bs4
import urllib3

from advisors import gitee
from advisors import yaml2url


urllib3.disable_warnings()

GET_METHOD_PEOJECTS = "/projects"
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW 64; rv:23.0) Gecko/20100101 Firefox/23.0'}
gitlab_list = ['gnome', 'freedesktop']
RECORDER_YAML = ".query_result_lasttime"
GNU_SOFTWARE_PAGE = "https://www.gnu.org/software/"


def __gitlab_get_method(query_url, token, params=None):
    """
    Get method
    """
    try:
        header_token = {'Private-Token': token}
        res = requests.get(query_url, headers = header_token, \
                params=params, verify = False)
        logging.debug("status_code: %d", res.status_code)
        content = res.content.decode('utf-8')
        if res.status_code != 200:
            logging.debug(content)
            return None
        if content != "":
            data = json.loads(content)
            return data
        return None
    except requests.RequestException as excpt:
        logging.error("request failed, reason=%s", excpt)
        return None


def gitlab_list_project(urlbase, token, params, group_path=""):
    """
    get project list from gitlab
    """
    if group_path == "":
        query_url = urlbase + GET_METHOD_PEOJECTS
    else:
        query_url = urlbase + "/groups/" + \
                group_path.replace("/", "%2F") + GET_METHOD_PEOJECTS
    return __gitlab_get_method(query_url, token, params)


def record_pkginfo(py_object):
    """
    record package info for running quickly next time
    """
    with open(RECORDER_YAML, 'w', encoding='utf-8') as record_file:
        yaml.dump(py_object, record_file)
        record_file.close()


def read_pkginfo_lasttime():
    """
    read package info record last time
    """
    file_name = os.path.join(os.getcwd(), RECORDER_YAML)
    try:
        with open(file_name, 'r', encoding='utf-8') as record_file:
            return  yaml.load(record_file.read(), Loader = yaml.Loader)
    except FileNotFoundError:
        return {}


def get_oe_repo_dict(cwd_path, use_cache):
    """
    get oe repo list from sigs.yaml
    """
    logging.debug("begin to query oe.")
    oe_repo_dict = {}
    last_record_dict = {}
    my_gitee = gitee.Gitee()
    data = my_gitee.get_sigs()['sigs']
    if use_cache:
        last_record_dict = read_pkginfo_lasttime()
        if len(last_record_dict) == 0:
            logging.info("last recorder not exist.")
    for repos in data:
        for repo in repos['repositories']:
            if repo.startswith('src-openeuler/'):
                name = repo.split('/')[1]
                repo_url = last_record_dict.get(name, None)
                if repo_url:
                    logging.info("%s has record.", name)
                else:
                    pkginfo = get_pkg_info(my_gitee, name, cwd_path)
                    if pkginfo:
                        repo_url = yaml2url.yaml2url(pkginfo)
                if not repo_url:
                    repo_url = 'none'
                oe_repo_dict.update({name: repo_url})
    logging.info("total %d repositories in src-openeuler", len(oe_repo_dict))
    record_pkginfo(oe_repo_dict)
    return oe_repo_dict


def load_config():
    """
    load configuration
    """
    try:
        config = os.path.expanduser("~/.community_archived.yaml")
        with open(config, 'r', encoding = 'utf-8') as archived_file:
            return yaml.load(archived_file.read(), Loader = yaml.Loader)
    except OSError as reason:
        print("Load yaml failed!" + str(reason))
        return None


def get_pkg_info(my_gitee, repo, cwd_path):
    """
    Get package info from yaml specified
    """
    if cwd_path:
        try:
            repo_yaml = open(os.path.join(cwd_path, "{pkg}.yaml".format(pkg=repo)))
        except FileNotFoundError:
            print("WARNING: {pkg}.yaml can't be found in local path: {path}.".format(pkg=repo,
                                                                                     path=cwd_path))
            repo_yaml = my_gitee.get_yaml(repo)
    else:
        repo_yaml = my_gitee.get_yaml(repo)

    if repo_yaml:
        return yaml.load(repo_yaml, Loader=yaml.Loader)
    return None


def sigint_handler(signum, frame):
    """
    interrupt signals handler
    """
    del frame
    print("Receive interrupt signal: %d. Exit!!!" % signum)
    sys.exit(0)


def arg_parser():
    """
    parse arguments
    """
    parser = argparse.ArgumentParser(description = "check archived \
            projects in upstream.")
    parser.add_argument('-v', '--verbose', action = 'store_true', \
            default = False, help = 'print debug log.')
    parser.add_argument('-n', '--name', type = str, choices = \
            ['gnome', 'freedesktop', 'gnu'], default = "", help = "community name.")
    parser.add_argument('-d', '--default', type = str, default = os.getcwd(),
            help="The fallback place to look for YAML information")
    parser.add_argument('-x', '--cached', action = 'store_true', \
            default = False, help = 'use result of last query')
    parser.set_defaults(func=cmd_check)
    sub_parser = parser.add_subparsers(title="sub-command list")
    parser_list = sub_parser.add_parser("list", help="list archived projects in upstream.")
    parser_list.set_defaults(func=cmd_list)
    args = parser.parse_args()
    return args


def __query_gitlab(vals, repo_url_list):
    for i in range(1, 100):
        params = vals['params']
        params['page'] = i
        data = gitlab_list_project(vals['restapi'], vals['token'], params, vals['group'])
        if data is None or len(data) == 0:
            break
        for entry in data:
            repo_url_list.append(entry['http_url_to_repo'])


def parse_gnu_html(url, repo_url_list):
    """
    parse gnu mainpage to get archived project
    """
    logging.debug("Parse gnu html: %s", url)
    file = urllib.request.urlopen(url, timeout=5)
    data = file.read()
    soup = bs4.BeautifulSoup(data.decode('utf-8'), 'html.parser')
    res = soup.find_all(class_="package-list emph-box")
    tags = res[-1].children
    for tag in tags:
        if getattr(tag, 'name', None) == 'a':
            repo_url_list.append(GNU_SOFTWARE_PAGE + tag.string)


def get_upstream_repo_url_list(name=""):
    """
    get all archived repo url list from upstream
    """
    url_list = []

    data = load_config()
    if data is None or len(data) == 0:
        return []
    if name == "":
        for entry in data.values():
            if entry['type'] == 'REST':
                __query_gitlab(entry, url_list)
            elif entry['type'] == 'HTML':
                parse_gnu_html(entry['url'], url_list)
            #here handle other type
        logging.info("Total %d archived projects", len(url_list))
    else:
        entry = data[name]
        if name == "gnu":
            parse_gnu_html(entry['url'], url_list)
        elif name in gitlab_list:
            __query_gitlab(entry, url_list)
        else:
            pass
        logging.info("%s: total %d archived projects", name, len(url_list))
    return url_list


def cmd_list(args):
    """
    cmd list handler
    """
    url_list = get_upstream_repo_url_list(args.name)
    if not url_list:
        return 1
    for repo_url in url_list:
        print(repo_url)
    print("Total %d projects" % len(url_list))
    return 0


def cmd_check(args):
    """
    cmd check handler
    """
    result = {}
    oe_repo_dict = get_oe_repo_dict(args.default, args.cached)
    url_list = get_upstream_repo_url_list(args.name)
    if not url_list:
        return 1
    for key1, value1 in oe_repo_dict.items():
        if value1 in url_list:
            result.update({key1:value1})
    print("\033[31m")
    print("Total %d archived projects in upstream:" % len(result))
    for repo_id, repo_url in result.items():
        print(str(repo_id) + '|' + repo_url)
    print("\033[0m")
    return 0


def main():
    """
    entry function
    """
    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGHUP, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)
    args = arg_parser()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,
                format='%(levelname)s: %(message)s')
    if args.__contains__("func"):
        return args.func(args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
