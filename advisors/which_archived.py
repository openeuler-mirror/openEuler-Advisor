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
"""
import sys
import json
import logging
import argparse
import signal
import re
import urllib.request
import urllib.error
import requests
import yaml
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()


GET_METHOD_PEOJECTS = "/projects"
SIGS_URL = "https://gitee.com/openeuler/community/raw/master/sig/sigs.yaml"
YAML_URL_TEMPLATE = "https://gitee.com/src-openeuler/{0}/raw/master/{0}.yaml"
YAML_FILE = "helper/community_archived.yaml"
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW 64; rv:23.0) Gecko/20100101 Firefox/23.0'}
gitlab_li = ['gnome', 'freedesktop']
vc_map = {
    'gnome':'gitlab.gnome',
    'freedesktop':'gitlab.freedesktop',
    'gnu':'gnu.org'}



class GitlabQuerier:
    """
    This is a querier class for gitlab
    """
    __urlbase = ""
    __token = ""

    def __init__(self, url, token):
        self.__urlbase = url
        self.__token = token

    def get(self, query_url, params=None):
        """
        Get method
        """
        try:
            header_token = {'Private-Token': self.__token}
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
        except requests.RequestException as e:
            logging.debug("request failed, reason=%s", e)
            return None

    def list_project(self, params, group_path=""):
        """
        get project list from gitlab
        """
        if group_path == "":
            query_url = self.__urlbase + GET_METHOD_PEOJECTS
        else:
            query_url = self.__urlbase + "/groups/" + \
                    group_path.replace("/", "%2F") + GET_METHOD_PEOJECTS
        return self.get(query_url, params)


def get_sigs():
    """
    get sigs from oe
    """
    req = urllib.request.Request(url=SIGS_URL, headers=headers)
    res = urllib.request.urlopen(req)
    sigs = yaml.load(res.read().decode("utf-8"), Loader=yaml.Loader)
    return sigs['sigs']


def get_version_control(repo_name):
    """
    get yaml from repo in oe
    """
    try:
        yaml_url = YAML_URL_TEMPLATE.format(repo_name)
        req = urllib.request.Request(url=yaml_url, headers=headers)
        res = urllib.request.urlopen(req)
        content = yaml.load(res.read().decode("utf-8"), Loader=yaml.Loader)
        return content
    except urllib.error.URLError as e:
        logging.debug("get %s yaml failed, reason=%s", repo_name, e.reason)
        return None


def get_oe_repolist():
    """
    get oe repo list from sigs.yaml
    """
    data = get_sigs()
    oe_repos = []
    for repos in data:
        for repo in repos['repositories']:
            if repo.startswith('src-openeuler/'):
                name = repo.replace('src-openeuler/', '')
                oe_repos.append(name)
    logging.debug("total %d repositories in src-openeuler", len(oe_repos))
    return oe_repos


def load_yaml():
    """
    load yaml config
    """
    try:
        with open(YAML_FILE, 'r', encoding =  'utf-8') as f:
            return yaml.load(f.read(), Loader = yaml.Loader)
    except OSError as reason:
        print("Load yaml failed!" + str(reason))
        return None


def sigint_handler(signum, _frame):
    """
    interrupt signals handler
    """
    print("Receive interrupt signal: %d. Exit!!!" % signum)
    sys.exit(0)


def arg_parser():
    """
    parse arguments
    """
    parser = argparse.ArgumentParser(description = "check archived \
            projects in upstream.")
    parser.add_argument('-d', '--debug', action = 'store_true', \
            default = False, help = 'print debug log.')
    parser.add_argument('-n', '--name', type = str, choices = \
            ['gnome', 'freedesktop', 'gnu'], default = "", help = "community name.")
    parser.set_defaults(func=cmd_check)
    sub_parser = parser.add_subparsers(title="sub-command list")
    parser_list = sub_parser.add_parser("list", help="list archived projects in upstream.")
    parser_list.set_defaults(func=cmd_list)
    args = parser.parse_args()
    return args


def __query_gitlab(vals, dicts):
    repos = []
    querier = GitlabQuerier(vals['restapi'], vals['token'])
    for i in range(1, 100):
        params = vals['params']
        params['page'] = i
        data = querier.list_project(params, vals['group'])
        if data is None or len(data) == 0:
            break
        for entry in data:
            repos.append(entry['name'])
    dicts[vals['name']] = repos.copy()
    return len(repos)


def parse_gnu_html(url, dicts):
    """
    parse gnu mainpage to get archived project
    """
    logging.debug("Parse gnu html: %s", url)
    vals = []
    file = urllib.request.urlopen(url, timeout=5)
    data = file.read()
    soup = BeautifulSoup(data.decode('utf-8'), 'html.parser')
    tag = soup.find(text=re.compile("decommissioned"))
    while tag is not None and getattr(tag, 'name', None) != 'p':
        if getattr(tag, 'name', None) == 'a':
            vals.append(tag.string)
        tag = tag.nextSibling
    # delete first element useless string '<maintainers@gnu.org>'
    del vals[0]
    dicts['gnu'] = vals.copy()
    return len(vals)


def get_upsteam_project(name=""):
    """
    get all archived project from upstream
    """
    dicts = {}
    total = 0

    data = load_yaml()
    if data is None or len(data) == 0:
        print("Load \'%s\' failed, please check!" % YAML_FILE)
        sys.exit(1)
    if name == "":
        for entry in data.values():
            if entry['type'] == 'REST':
                total += __query_gitlab(entry, dicts)
            elif entry['type'] == 'HTML':
                total += parse_gnu_html(entry['url'], dicts)
            #here handle other type
        logging.debug("Total %d archived projects", total)
    else:
        entry = data[name]
        if name == "gnu":
            total = parse_gnu_html(entry['url'], dicts)
        elif name in gitlab_li:
            total =  __query_gitlab(entry, dicts)
        else:
            pass
        logging.debug("%s: total %d archived projects", name, total)
    return dicts


def cmd_list(args):
    """
    cmd list handler
    """
    dicts = get_upsteam_project(args.name)
    repos = dicts[args.name]
    for repo in repos:
        print(repo)
    print("Total %d projects" % len(repos))
    return 0


def cmd_check(args):
    """
    cmd check handler
    """
    vals=[]
    dicts={}
    success_list = []
    failed_list = []
    oe_repos = get_oe_repolist()
    upstream_repos = get_upsteam_project(args.name)
    for key, value in upstream_repos.items():
        for repo in value:
            if repo in oe_repos:
                vals.append(repo)
        dicts[key] = vals.copy()
        vals.clear()
    for key, value in dicts.items():
        mstr = vc_map[key]
        for repo in value:
            vc_dict = get_version_control(repo)
            if vc_dict is None:
                failed_list.append(repo)
                continue
            version_control = vc_dict['version_control']
            src_repo = vc_dict['src_repo']
            if vc_map[key] == version_control or mstr in src_repo:
                success_list.append(repo)
    print("\033[31m")
    print("Archived projects in upstream:")
    for repo in success_list:
        print(repo)
    print('\033[33m')
    print("Project need to confirm manually: ")
    for repo in failed_list:
        print(repo)
    print('\033[0m')
    return 0


def main():
    """
    entry function
    """
    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGHUP, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)
    args = arg_parser()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(message)s')
    else:
        logging.basicConfig(level=logging.INFO,
                            format='%(message)s')
    if args.__contains__("func"):
        return args.func(args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
