#!/usr/bin/env python3
"""
command line of creating tracking item
"""
import argparse
import sys
import os
import requests
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

USAGE = """
        patch-tracking-cli --help
        patch-tracking-cli --server SERVER --version_control github --scm_repo SCM_REPO --scm_branch SCM_BRANCH \\
                           --repo REPO --branch BRANCH --enabled True --user USER --password PWD
        patch-tracking-cli --server SERVER --file FILE --user USER --password PWD
        patch-tracking-cli --server SERVER --dir DIR --user USER --password PWD
"""

parser = argparse.ArgumentParser(
    usage=USAGE, allow_abbrev=False, description="command line to create/update patch tracking item"
)

parser.add_argument("--server", help="patch tracking daemon server")

parser.add_argument("--version_control", choices=['github'], help="upstream version control system")
parser.add_argument("--scm_repo", help="upstream scm repository")
parser.add_argument("--scm_branch", help="upstream scm branch")
parser.add_argument("--repo", help="source package repository")
parser.add_argument("--branch", help="source package branch")
parser.add_argument("--enabled", choices=["True", "true", "False", "false"], help="whether tracing is enabled")

parser.add_argument('--file', help='import patch tracking from file')

parser.add_argument('--dir', help='import patch tracking from files in directory')
parser.add_argument('--user', help='Authentication username')
parser.add_argument('--password', help='Authentication password')

args = parser.parse_args()

style1 = args.version_control or args.repo or args.branch or args.scm_repo or args.scm_branch or args.enabled
style2 = bool(args.file)
style3 = bool(args.dir)

if str([style1, style2, style3]).count('True') >= 2:
    print("mix different usage style")
    parser.print_usage()
    sys.exit(-1)


def single_input_track(params, file_path=None):
    """
    load tracking from ommand lcine arguments
    """
    if param_check(params, file_path) == 'error':
        return 'error', 'Check input params error.'
    if param_check_url(params, file_path) == 'error':
        return 'error', 'Check input params error.'

    repo = params['repo']
    branch = params['branch']
    scm_repo = params['scm_repo']
    scm_branch = params['scm_branch']
    version_control = params['version_control'].lower()
    enabled = params['enabled'].lower()
    server = params['server']
    user = params['user']
    password = params['password']

    enabled = bool(enabled == 'true')

    url = '/'.join(['https:/', server, 'tracking'])
    data = {
        'version_control': version_control,
        'scm_repo': scm_repo,
        'scm_branch': scm_branch,
        'repo': repo,
        'branch': branch,
        'enabled': enabled
    }
    try:
        ret = requests.post(url, json=data, verify=False, auth=HTTPBasicAuth(user, password))
    except Exception as exception:
        return 'error', 'Connect server error: ' + str(exception)
    if ret.status_code == 401 or ret.status_code == 403:
        return 'error', 'Authenticate Error. Please make sure user and password are correct.'
    if ret.status_code == 200 and ret.json()['code'] == '2001':
        return 'success', 'created'
    else:
        print("status_code: {}, return text: {}".format(ret.status_code, ret.text))
        return 'error', 'Unexpected Error.'


def file_input_track(file_path):
    """
    load tracking from file
    """
    if os.path.exists(file_path) and os.path.isfile(file_path):
        if os.path.splitext(file_path)[-1] != ".yaml":
            print('Please input yaml file. Error in {}'.format(file_path))
            return None
        with open(file_path) as file:
            content = file.readlines()
            params = dict()
            for item in content:
                if ":" in item:
                    k = item.split(':')[0]
                    value = item.split(':')[1].strip(' ').strip('\n')
                    params.update({k: value})
            params.update({'server': args.server, 'user': args.user, 'password': args.password})
            ret = single_input_track(params, file_path)
            if ret[0] == 'success':
                print('Tracking successfully {} for {}'.format(ret[1], file_path))
            else:
                print('Tracking failed for {}: {}'.format(file_path, ret[1]))
    else:
        print('yaml path error. Params error in {}'.format(file_path))


def dir_input_track(dir_path):
    """
    load tracking from dir
    """
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        for root, _, files in os.walk(dir_path):
            if not files:
                print('error: dir path empty')
                return None
            for file in files:
                if os.path.splitext(file)[-1] == ".yaml":
                    file_path = os.path.join(root, file)
                    file_input_track(file_path)
                else:
                    print('Please input yaml file. Error in {}'.format(file))
    else:
        print('error: dir path error. Params error in {}'.format(dir_path))


def patch_tracking_server_check(url):
    """
    check if patch_tracking server start
    """
    try:
        ret = requests.head(url=url, verify=False)
    except Exception as exception:
        print(f"Error: Cannot connect to {url}, please make sure patch-tracking service is running.")
        return 'error', exception
    if ret.status_code == 200 or ret.status_code == 404:
        return 'success', ret

    print(f"Unexpected Error: {ret.text}")
    return 'error', ret.text


def repo_branch_check(url):
    """
    check if repo/branch exist
    """
    headers = {
        "User-Agent":
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) " +
        "Ubuntu Chromium/83.0.4103.61 Chrome/83.0.4103.61 Safari/537.36"
    }
    try:
        ret = requests.get(url=url, headers=headers)
    except Exception as exception:
        return 'error', exception
    if ret.status_code == 404:
        return 'error', f'{url} not exist.'
    if ret.status_code == 200:
        return 'success', ret

    return 'error', ret.text


def command_default_param_check():
    flag = 0
    if not args.server:
        print("Error: --server not configure.")
        flag = 1
    if not args.user:
        print("Error: --user not configure.")
        flag = 1
    if not args.password:
        print("Error: --password not configure.")
        flag = 1
    if flag == 1:
        return 'error'
    else:
        return 'success'


def param_check(params, file_path=None):
    """
    check if param is valid
    """
    flag = 0
    required_param = ['version_control', 'scm_repo', 'scm_branch', 'repo', 'branch', 'enabled', 'user', 'password']
    for req in required_param:
        if req not in params:
            if file_path:
                print(f'param: --{req} must be configured. Error in {file_path}')
            else:
                print(f'param: --{req} must be configured.')
            flag = 1
    for k, value in params.items():
        if not value:
            if file_path:
                print(f'param: --{k} must be configured. Error in {file_path}')
            else:
                print(f'param: --{k} cannot be empty.')
            flag = 1
    if flag:
        return 'error'
    return None


def param_check_url(params, file_path=None):
    """
    check url
    """
    scm_url = f"https://github.com/{params['scm_repo']}/tree/{params['scm_branch']}"
    url = f"https://gitee.com/{params['repo']}/tree/{params['branch']}"
    patch_tracking_url = f"https://{params['server']}"
    server_ret = patch_tracking_server_check(patch_tracking_url)
    if server_ret[0] != 'success':
        return 'error'

    scm_ret = repo_branch_check(scm_url)
    if scm_ret[0] != 'success':
        if file_path:
            print(
                f"scm_repo: {params['scm_repo']} and scm_branch: {params['scm_branch']} check failed. \n"
                f"Error in {file_path}. {scm_ret[1]}"
            )
        else:
            print(f"scm_repo: {params['scm_repo']} and scm_branch: {params['scm_branch']} check failed. {scm_ret[1]}")
        return 'error'
    ret = repo_branch_check(url)
    if ret[0] != 'success':
        if file_path:
            print(f"repo: {params['repo']} and branch: {params['branch']} check failed. {ret[1]}. Error in {file_path}")
        else:
            print(f"repo: {params['repo']} and branch: {params['branch']} check failed. {ret[1]}.")
        return 'error'
    return None


def main():
    """
    main
    """

    if command_default_param_check() == 'error':
        return None

    if style2:
        file_input_track(args.file)
    elif style3:
        dir_input_track(args.dir)
    else:
        params = {
            'repo': args.repo,
            'branch': args.branch,
            'scm_repo': args.scm_repo,
            'scm_branch': args.scm_branch,
            'version_control': args.version_control,
            'enabled': args.enabled,
            'server': args.server,
            'user': args.user,
            'password': args.password
        }
        ret = single_input_track(params)
        if ret[0] == 'success':
            print('Tracking successfully.')
        else:
            print(ret[1])


if __name__ == '__main__':
    main()
